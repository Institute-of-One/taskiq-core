"""Build the revised submission: a clean .docx and one with every change highlighted.

MDPI asks that revisions be highlighted so editors and reviewers can see what changed
(checklist item II). Producing that by hand invites the failure this whole paper is about:
a document that looks revised without being the revision.

So the highlighted version is derived, not written. The submitted manuscript is recovered
from git at the commit that was sent, compared with the current one paragraph by paragraph,
and every paragraph that differs is marked in the output. Nothing is highlighted by
judgement, and nothing that changed can be missed.

    python paper/build_revision.py
"""

from __future__ import annotations

import difflib
import re
import subprocess
from pathlib import Path

import pypandoc

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
MANUSCRIPT = HERE / "manuscript.md"
OUT = HERE / "revision_r1"

#: The state that was sent to the journal. Recovered from git rather than from a copy on
#: disk, because a copy on disk is a claim about what was sent and git is a record of it.
SUBMITTED_TAG_CANDIDATES = ("submitted-jimaging", "jimaging-submitted")
SUBMISSION_DATE = "2026-08-18"


def submitted_manuscript() -> tuple[str, str]:
    """The manuscript as submitted, and how it was identified."""
    for tag in SUBMITTED_TAG_CANDIDATES:
        result = subprocess.run(
            ["git", "show", f"{tag}:paper/manuscript.md"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=REPO,
        )
        if result.returncode == 0:
            return result.stdout, f"tag {tag}"

    # No tag was cut, so fall back to the last commit on or before the submission date.
    result = subprocess.run(
        ["git", "rev-list", "-1", f"--before={SUBMISSION_DATE} 23:59", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    )
    commit = result.stdout.strip()
    if not commit:
        raise SystemExit("cannot identify the submitted state; no tag and no dated commit")
    shown = subprocess.run(
        ["git", "show", f"{commit}:paper/manuscript.md"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    )
    if shown.returncode != 0:
        raise SystemExit(f"commit {commit[:8]} has no paper/manuscript.md")
    return shown.stdout, f"commit {commit[:8]} (last on or before {SUBMISSION_DATE})"


def paragraphs(text: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def highlight_changes(before: str, after: str) -> tuple[str, int, int]:
    """Mark every paragraph of `after` that is new or altered.

    Pandoc renders `[text]{.mark}` as highlighted text in Word, so the marking survives
    the conversion rather than being a colour applied afterwards.
    """
    old, new = paragraphs(before), paragraphs(after)
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    out, changed = [], 0

    for tag, _, _, new_start, new_end in matcher.get_opcodes():
        for block in new[new_start:new_end]:
            if tag == "equal":
                out.append(block)
                continue
            changed += 1
            # Tables and figure includes must not be wrapped: pandoc would take the
            # markup as literal text and the table would stop being a table.
            if block.startswith(("|", "!", "$$")) or block.startswith("#"):
                out.append(block)
            else:
                out.append(f"[{block}]{{.mark}}")

    return "\n\n".join(out), changed, len(new)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    before, source = submitted_manuscript()
    after = MANUSCRIPT.read_text(encoding="utf-8")
    print(f"submitted state taken from {source}")

    marked, changed, total = highlight_changes(before, after)
    print(f"{changed} of {total} paragraphs changed or added")

    clean_docx = OUT / "manuscript_revised.docx"
    marked_docx = OUT / "manuscript_revised_highlighted.docx"

    for text, destination, label in (
        (after, clean_docx, "clean"),
        (marked, marked_docx, "highlighted"),
    ):
        pypandoc.convert_text(
            text,
            to="docx",
            format="markdown",
            outputfile=str(destination),
            extra_args=["--resource-path", str(HERE), "--wrap=none"],
        )
        size = destination.stat().st_size / 1000
        print(f"  {label:12} {destination.name}  ({size:.0f} kB)")

    # The response letter goes as its own document.
    letter = OUT / "response_to_reviewers.md"
    if letter.is_file():
        pypandoc.convert_text(
            letter.read_text(encoding="utf-8"),
            to="docx",
            format="markdown",
            outputfile=str(OUT / "response_to_reviewers.docx"),
            extra_args=["--wrap=none"],
        )
        print(f"  {'letter':12} response_to_reviewers.docx")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
