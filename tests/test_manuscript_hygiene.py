"""Defects the manuscript can acquire silently, asserted rather than hoped for.

Each check here corresponds to something that actually happened to this file, not to a
hypothetical. A manuscript is edited by hand and by script over weeks, and the failures
that matter are the ones that leave the text looking almost right.

    python -m pytest tests/test_manuscript_hygiene.py -q
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANUSCRIPT = REPO / "paper" / "manuscript.md"

#: The affiliation Crossref carries for this author, identical in IORN-002 (this journal)
#: and IORN-006 (Tomography). The ROR application rests on the three agreeing, so a
#: departure here is not a typographical matter.
AFFILIATION = "Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan"


def _text() -> str:
    return MANUSCRIPT.read_text(encoding="utf-8")


def test_no_control_characters_survive_an_edit():
    r"""A heredoc turned `\alpha` into a bell character and left `$<BEL>lpha` in the text.

    It renders as `$lpha`, which reads as a typo rather than as a control character, and
    it reached the file during this very revision. Tabs and newlines are the only
    non-printing characters a manuscript has any business containing.
    """
    stray = sorted({hex(ord(c)) for c in _text() if ord(c) < 32 and c not in "\n\t"})
    assert not stray, f"control characters in the manuscript: {stray}"


def test_no_latex_command_lost_its_backslash():
    r"""The same accident, caught from the other side.

    `\alpha`, `\times` and `\mathrm` are the commands this manuscript uses most; if a
    backslash is eaten, the command name survives as a bare word next to a dollar sign.
    """
    text = _text()
    for command in ("alpha", "times", "mathrm", "sigma", "int"):
        broken = re.findall(rf"\$[^$\n]*(?<![\\A-Za-z]){command}\b", text)
        assert not broken, (
            f"'{command}' appears inside math without its backslash: {broken[:3]}"
        )


def test_the_affiliation_is_the_one_crossref_carries():
    """Two published papers already carry this string; the third must match, exactly.

    It was submitted without the postcode, and the copy typed into the portal also lost
    the capital in "One" and gained a comma in "LISIT, Co., Ltd.". A ROR application
    argues that an organisation is used consistently as an affiliation, and three
    spellings across three papers is the argument's opposite.
    """
    text = _text()
    assert AFFILIATION in text, f"the manuscript does not carry: {AFFILIATION}"
    for wrong in ("Institute of one", "LISIT, Co.", "Tokyo, Japan;"):
        assert wrong not in text, f"an older affiliation spelling survives: {wrong!r}"


def test_every_figure_referenced_is_present():
    """A figure the text names and the repository lacks is a hole a reader falls into."""
    text = _text()
    missing = [
        name for name in re.findall(r"!\[\]\(figures/([^)]+)\)", text)
        if not (REPO / "paper" / "figures" / name).is_file()
    ]
    assert not missing, f"referenced but absent: {missing}"


#: Figures produced outside this repository, and the repository the manuscript must cite
#: for each. The real-scanner arm needs reconstruction code that has no business living in
#: a package deliberately free of DICOM, so it lives in ldct-io and the paper says so.
EXTERNAL_FIGURES = {"fig5_acr_atlas.png": "ldct-io"}


def test_no_figure_is_orphaned_from_its_generator():
    """A figure no script writes cannot be regenerated, whatever the paper says about it.

    This paper argues that a result you cannot re-derive is a result you cannot check, so
    a figure of unknown provenance contradicts its own thesis. Figure 5 was exactly that
    until its generator was published: it came from a script in ldct-io that the manuscript
    did not cite and nobody could obtain.

    A figure generated elsewhere is allowed. A figure generated elsewhere without the
    manuscript saying where is not, which is what this asserts.
    """
    text = _text()
    referenced = set(re.findall(r"!\[\]\(figures/([^)]+)\)", text))
    written = set()
    for script in (REPO / "paper").glob("*.py"):
        for name in re.findall(r'"(fig[^"]+\.png)"', script.read_text(encoding="utf-8")):
            written.add(name)

    for name in sorted(referenced - written):
        source = EXTERNAL_FIGURES.get(name)
        assert source is not None, (
            f"{name} is referenced by the manuscript, written by no script in paper/, and "
            f"not declared as coming from anywhere else"
        )
        assert source in text, (
            f"{name} comes from {source}, which the manuscript never cites; a reader "
            f"cannot regenerate it and this paper's whole argument is that they should be "
            f"able to"
        )
