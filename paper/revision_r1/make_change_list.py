"""Produce an exact, ordered list of edits to apply to the journal's formatted manuscript.

The editorial office had already applied the journal template during peer review, and
rebuilding the document from markdown discarded it. Their file has to be the base.

It cannot be patched programmatically. It carries 162 native Word equations and 39
MDPI-specific paragraph styles, and replacing a paragraph's text destroys both -- the fix
would cost more than the fault. So this produces a change list precise enough to apply by
hand without judgement: for each changed paragraph, enough of the old text to find it, and
the whole of the new text to replace it with.

    python paper/revision_r1/make_change_list.py
"""

from __future__ import annotations

import difflib
import re
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MANUSCRIPT = REPO / "paper" / "manuscript.md"
FORMATTED = HERE / "jimaging-4539482- peer review.docx"
OUTPUT = HERE / "CHANGES_TO_APPLY.md"

SUBMISSION_DATE = "2026-08-18"


def submitted_markdown() -> str:
    commit = subprocess.run(
        ["git", "rev-list", "-1", f"--before={SUBMISSION_DATE} 23:59", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    ).stdout.strip()
    return subprocess.run(
        ["git", "show", f"{commit}:paper/manuscript.md"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    ).stdout


def plain(markdown: str) -> str:
    """Strip the markup so a paragraph can be matched against Word's plain text."""
    text = re.sub(r"`([^`]*)`", r"\1", markdown)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(markdown: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", markdown) if block.strip()]


def word_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    out = []
    for block in re.findall(r"<w:p[ >].*?</w:p>", document, re.S):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block))
        if text.strip():
            out.append(re.sub(r"\s+", " ", text).strip())
    return out


def locate(needle: str, haystack: list[str]) -> int | None:
    """Which paragraph of the formatted document a changed paragraph corresponds to."""
    if not needle:
        return None
    best, score = None, 0.0
    opening = needle[:70]
    for index, candidate in enumerate(haystack):
        ratio = difflib.SequenceMatcher(None, opening, candidate[:70]).ratio()
        if ratio > score:
            best, score = index, ratio
    return best if score >= 0.6 else None


def main() -> int:
    before = paragraphs(submitted_markdown())
    after = paragraphs(MANUSCRIPT.read_text(encoding="utf-8"))
    formatted = word_paragraphs(FORMATTED)

    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    edits: list[dict] = []

    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        for offset, block in enumerate(after[new_start:new_end]):
            if block.startswith(("|", "!", "$$")):
                continue  # tables, figures and display equations are handled separately
            old_block = before[old_start + offset] if old_start + offset < old_end else ""
            # An insertion has no old text to search for, so it is anchored to the last
            # unchanged paragraph before it. That is what someone applying the edit needs:
            # not "insert this somewhere" but "insert it after this".
            anchor = ""
            if not old_block:
                for previous in reversed(after[: new_start + offset]):
                    if previous in before and not previous.startswith(("|", "!", "$$", "#")):
                        anchor = plain(previous)
                        break
            edits.append(
                {
                    "kind": "replace" if old_block else "insert",
                    "old": plain(old_block),
                    "new": block,
                    "anchor": anchor,
                    "at": locate(plain(old_block) or anchor, formatted),
                }
            )

    lines = [
        "# Changes to apply to the journal-formatted manuscript",
        "",
        f"Base file: `{FORMATTED.name}` (the preliminarily formatted version sent by the",
        "editorial office). Apply these edits **in that file**, in Word, and keep its styles.",
        "",
        "**Do not rebuild the document.** It carries 162 native Word equations and 39",
        "MDPI paragraph styles; replacing paragraphs wholesale destroys both.",
        "",
        f"{len(edits)} edits. Each gives the text to find and the text to put in its place.",
        "Highlight each replacement in yellow so the reviewers can see what changed.",
        "",
        "---",
        "",
    ]

    for number, edit in enumerate(edits, start=1):
        where = (
            f"near paragraph {edit['at'] + 1}"
            if edit["at"] is not None
            else "location not found automatically"
        )
        lines.append(f"## {number}. {edit['kind'].upper()} — {where}")
        lines.append("")
        if edit["old"]:
            lines.append("**Find this paragraph:**")
            lines.append("")
            lines.append("> " + edit["old"])
            lines.append("")
            lines.append("**Replace the whole of it with:**")
        elif edit["anchor"]:
            lines.append("**Find this paragraph:**")
            lines.append("")
            lines.append("> " + edit["anchor"])
            lines.append("")
            lines.append("**Insert the following immediately after it, as a new paragraph:**")
        else:
            lines.append("**Insert this as a new paragraph:**")
        lines.append("")
        lines.append("> " + plain(edit["new"]).replace("\n", "\n> "))
        lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    located = sum(1 for edit in edits if edit["at"] is not None)
    print(f"formatted document: {len(formatted)} paragraphs with text")
    print(f"{len(edits)} edits, {located} located automatically, {len(edits) - located} not")
    print(f"written: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
