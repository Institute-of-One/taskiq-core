"""Check the hand-edited journal file before it is emailed back.

Thirty-nine edits applied by hand into a Word document will not all land. Some will be
missed, some mistyped, and a stray keystroke can delete an equation without anyone
noticing until the proof. This checks the finished file against the manuscript source and
against the file it started from, so what goes to the editorial office has been verified
rather than believed.

    python paper/revision_r1/verify_formatted.py edited.docx
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MANUSCRIPT = REPO / "paper" / "manuscript.md"
ORIGINAL = HERE / "jimaging-4539482- peer review.docx"
SUBMISSION_DATE = "2026-08-18"

AFFILIATION = "Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan"


def _document(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def _paragraph_texts(document: str) -> list[str]:
    out = []
    for block in re.findall(r"<w:p[ >].*?</w:p>", document, re.S):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block))
        if text.strip():
            out.append(re.sub(r"\s+", " ", text).strip())
    return out


def plain(markdown: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", markdown)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\$[^$]*\$", " ", text)  # maths is OMML in Word; compare the prose only
    return re.sub(r"\s+", " ", text).strip()


def submitted_blocks() -> list[str]:
    commit = subprocess.run(
        ["git", "rev-list", "-1", f"--before={SUBMISSION_DATE} 23:59", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    ).stdout.strip()
    text = subprocess.run(
        ["git", "show", f"{commit}:paper/manuscript.md"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    ).stdout
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def revised_blocks() -> list[str]:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def contains(needle: str, haystack: list[str], threshold: float = 0.82) -> bool:
    """Whether the paragraph is present, allowing for maths rendered as objects, not text."""
    if not needle:
        return True
    for candidate in haystack:
        if needle in candidate or candidate in needle:
            return True
        if difflib.SequenceMatcher(None, needle, candidate).ratio() >= threshold:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edited", type=Path, help="the hand-edited .docx to check")
    edited_path = parser.parse_args().edited

    edited = _document(edited_path)
    original = _document(ORIGINAL)
    texts = _paragraph_texts(edited)

    print(f"checking {edited_path.name}\n")
    failures: list[str] = []

    # --- 1. nothing structural was lost -------------------------------------------------
    print("=== structure, against the file the editorial office sent")
    for label, pattern in (
        ("equations", r"<m:oMath"),
        ("tables", r"<w:tbl>"),
        ("images", r"<w:drawing>"),
        ("MDPI styles", r'w:val="MDPI'),
    ):
        was, now = len(re.findall(pattern, original)), len(re.findall(pattern, edited))
        ok = now >= was
        print(f"  {'ok  ' if ok else 'LOST'}  {label:14} {was} -> {now}")
        if not ok:
            failures.append(f"{was - now} {label} lost")

    # --- 2. every changed paragraph arrived ---------------------------------------------
    print("\n=== the revision's changed paragraphs")
    before, after = submitted_blocks(), revised_blocks()
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    expected, missing = 0, []
    for tag, _, _, n0, n1 in matcher.get_opcodes():
        if tag == "equal":
            continue
        for block in after[n0:n1]:
            if block.startswith(("|", "!", "$$", "#")):
                continue
            needle = plain(block)
            if len(needle.split()) < 4:
                continue
            expected += 1
            if not contains(needle, texts):
                missing.append(needle[:90])
    print(f"  {expected - len(missing)} of {expected} present")
    for item in missing:
        print(f"  MISSING  {item}...")
        failures.append(f"missing paragraph: {item[:50]}")

    # --- 3. nothing the revision removed is still there ---------------------------------
    print("\n=== text the revision removed")
    stale = [
        ("the identities transferred intact", "the abstract's overclaim"),
        ("must refuse to answer", "the unclear 'refused' wording"),
        ("Institute of one", "the lower-case affiliation"),
        ("LISIT, Co.", "the affiliation's extra comma"),
    ]
    for needle, description in stale:
        present = any(needle in text for text in texts)
        print(f"  {'STILL THERE' if present else 'ok         '}  {description}")
        if present:
            failures.append(f"stale text remains: {description}")

    # --- 4. the things that must be exactly right ---------------------------------------
    print("\n=== exact strings")
    for needle, description in (
        (AFFILIATION, "affiliation with postcode"),
        ("ldct-io", "the second package cited"),
        ("A1.", "checklist relabelled"),
        ("B2.", "checklist relabelled"),
    ):
        present = any(needle in text for text in texts)
        print(f"  {'ok  ' if present else 'FAIL'}  {description}")
        if not present:
            failures.append(f"absent: {description}")

    # --- 5. highlighting, which the journal asked for ------------------------------------
    marks = len(re.findall(r"<w:highlight", edited))
    print(f"\n=== highlighting\n  {marks} highlighted runs")
    if marks == 0:
        failures.append("no highlighting; the journal asked for changes to be marked")

    print(f"\n{len(failures)} problems" if failures else "\nno problems found")
    for problem in failures:
        print(f"  - {problem}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
