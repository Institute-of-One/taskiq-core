"""Final proofread of the answered J. Imaging proof, before the file goes back.

Six things were checked. The first four were checked against the released code and
against `paper/figures/injection.json`, which the study script writes and which is the
only authority for the numbers in Table 2:

  1. Which checks caught which defects. The prose said each family caught three of six.
     The data says internal identities caught three (nps_area, disk, no_floor) and
     closed-form references caught five (sinc, jitter, detrend, and nps_area and
     no_floor as well). It also said no single check caught more than two defects; the
     NPS closed-form reference caught three.
  2. "Detection precedes materiality" is stronger than the grid supports: for nps_area
     and no_floor detection and materiality fall on the same grid point.
  3. ISO 12233 is issued by ISO, not by the IEC.
  4. `disk` is the defect's name in the released code; Table 2 still called it `disc`.

The last two were checked against the repository and the English Editor's note:

  5. The Data Availability Statement called the Zenodo record for v0.4.0 the archived
     snapshot behind every synthetic number, but that tag predates the study scripts. It
     now separates the archived library from the scripts on GitHub, pins the revision the
     results were verified against, and no longer claims that text and figure cannot
     diverge. The version and both DOIs are unchanged.
  6. NEQ is defined at its first use in the main text.

Nothing in the data was changed, no figure was regenerated and no study was re-run for
this pass; only the sentences that misreport the data are edited. As in
`apply_proof_edits.py`, only the contents of `<w:t>` elements are rewritten, so every
comment anchor, bookmark, equation and run property stays exactly where the editorial
office put it.

    python paper/proof/apply_final_proofread.py
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from apply_proof_edits import PARA, apply, escape, replace_in_paragraph

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "jimaging-4539482-answered.docx"
TARGET = HERE / "jimaging-4539482-final.docx"

#: (what to find, what to put there, how many times it must occur)
EDITS: list[tuple[str, str, int]] = [
    # -- 1. The two families did not catch three each. -----------------------------
    # Abstract.
    (
        "Neither family sufficed alone: each detected three of six,",
        "Neither family sufficed alone: the internal identities detected three of the six "
        "and the closed-form references five,",
        1,
    ),
    # Section 3.4, the sentence that lists them.
    (
        "Closed-form references caught sinc, jitter and detrend—3 of 6.",
        "Closed-form references caught sinc, jitter and detrend, and also nps_area and "
        "no_floor—5 of 6.",
        1,
    ),
    # The two families overlap on nps_area and no_floor, so they do not split cleanly.
    (
        "The two families split the defects cleanly:",
        "The two families overlap, and neither covers the whole set:",
        1,
    ),
    (
        "No defect was caught only by a check outside its family, and no single check "
        "caught more than two defects.",
        "Two defects, nps_area and no_floor, were caught by both families; disk was caught "
        "by an identity alone, and sinc, jitter and detrend by a closed-form reference "
        "alone. No single check caught more than three defects, and only the NPS "
        "closed-form reference caught that many.",
        1,
    ),
    # -- 2. Detection is at or before materiality, not strictly before. -------------
    (
        "The claim made here is therefore that detection precedes materiality, which the "
        "grid does resolve,",
        "The claim made here is therefore that detection occurs at or before materiality"
        "—for nps_area and no_floor the two fall on the same grid point—which the "
        "grid does resolve,",
        1,
    ),
    # Three defects never became material at any severity tried; neither the abstract nor
    # the conclusions should be readable as saying that all six did.
    (
        "became wrong by more than 5%. Neither family sufficed alone",
        "became wrong by more than 5%—an error that three of the six never produced. "
        "Neither family sufficed alone",
        1,
    ),
    (
        "at or before the point where the reported detectability became materially wrong.",
        "at or before the point where the reported detectability became materially "
        "wrong—which, for three of the six, it never did.",
        1,
    ),
    # -- 3. ISO 12233 is an ISO standard. The edition is unchanged. -----------------
    (
        "International Electrotechnical Commission (ISO): Geneva, Switzerland, 2017.",
        "International Organization for Standardization (ISO): Geneva, Switzerland, 2017.",
        1,
    ),
    # -- 5. What the Zenodo archive actually holds. --------------------------------
    # `git ls-tree -r v0.4.0 -- paper/` returns paper.bib and paper.md and nothing
    # else: the tag is commit c7493c1 of 18 July 2026 and the study scripts were added
    # on 16 August. The archive holds the library and its unit tests; the scripts, their
    # outputs and the tests that check them are on GitHub only. taskiq_core/ is
    # byte-identical between v0.4.0 and the revision cited, so the version and both DOIs
    # stand as printed and no new release is cut.
    #
    # The two replacements below leave the stretch of text that carries comment anchors
    # 38 and 39 -- the repository URL, its access date and the licence -- untouched.
    (
        "The synthetic arm—the phantom generators, the physical and observer "
        "estimators, the injection study (paper/make_injection_study.py) and the test "
        "suite—is openly available at ",
        "The estimator library behind every synthetic number here—the phantom "
        "generators and the physical and observer estimators, with their unit tests—"
        "is taskiq-core v0.4.0, archived on Zenodo (version DOI 10.5281/zenodo.21422924; "
        "concept DOI 10.5281/zenodo.21422923 resolves to the latest version). The scripts "
        "that run the studies reported here (paper/make_injection_study.py and "
        "paper/make_figures.py), their outputs, and the tests that check them were added "
        "to the repository after that release was tagged and are therefore not part of "
        "the Zenodo archive; they are openly available at ",
        1,
    ),
    (
        " and archived on Zenodo (version DOI 10.5281/zenodo.21422924 for v0.4.0, the "
        "archived snapshot behind every synthetic number here; concept DOI "
        "10.5281/zenodo.21422923 resolves to the latest version).",
        ". The revision the results reported here were verified against is "
        "4c238362cd8720a7c6a2eddc98347dd400106bbd "
        "(<https://github.com/Institute-of-One/taskiq-core/tree/"
        "4c238362cd8720a7c6a2eddc98347dd400106bbd> (accessed on 12 September 2026)).",
        1,
    ),
    # What injection.json covers, and how its numbers reach the page. The script writes
    # one figure and one JSON file, for the injection study alone; Figures 1 to 3 come
    # from a different script, and the values in the text were transcribed by hand.
    (
        "Every number in that arm is written to paper/figures/injection.json by the "
        "script that produces Figure 4, so the text and the figure cannot diverge.",
        "The injection study reported in Table 2 and Figure 4 is run by "
        "paper/make_injection_study.py, which writes both paper/figures/fig4_injection.png "
        "and paper/figures/injection.json; the values quoted for that study in Table 2 and "
        "in the text were transcribed from that file. Figures 1 to 3 are produced by "
        "paper/make_figures.py, which writes paper/figures/results.json.",
        1,
    ),
    # -- 6. NEQ, defined at its first use in the main text. -------------------------
    (
        "to the task is the noise-equivalent quanta,",
        "to the task is the noise-equivalent quanta (NEQ),",
        1,
    ),
]

#: Paragraphs whose whole text is replaced, for table cells too short to match on.
#: `disk` is the name the released code and injection.json give the defect, and the name
#: Sections 3.3 and 3.4 now use; only the Table 2 cell still said `disc`.
WHOLE: list[tuple[str, str, int]] = [("disc", "disk", 1)]


def apply_whole(document: str, find: str, repl: str) -> tuple[str, int]:
    out, last, total = [], 0, 0
    for match in PARA.finditer(document):
        out.append(document[last : match.start()])
        block = match.group(0)
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block))
        if text.strip() == find:
            block, n = replace_in_paragraph(block, escape(find), escape(repl))
            total += n
        out.append(block)
        last = match.end()
    out.append(document[last:])
    return "".join(out), total


def comment_ids(data: bytes) -> list[str]:
    return re.findall(r'<w:comment [^>]*w:id="(\d+)"', data.decode("utf-8"))


def main() -> int:
    with zipfile.ZipFile(SOURCE) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        items = [(item, archive.read(item.filename)) for item in archive.infolist()]
    before = comment_ids(dict((i.filename, d) for i, d in items)["word/comments.xml"])

    print("edits")
    for find, repl, expected in EDITS:
        document, n = apply(document, find, repl)
        print(f"  {'ok  ' if n == expected else 'WRONG'} {n} of {expected}   {find[:58]}")
        if n != expected:
            raise SystemExit(f"expected {expected} occurrence(s) of {find!r}, found {n}")
    for find, repl, expected in WHOLE:
        document, n = apply_whole(document, find, repl)
        print(f"  {'ok  ' if n == expected else 'WRONG'} {n} of {expected}   (whole) {find}")
        if n != expected:
            raise SystemExit(f"expected {expected} paragraph(s) reading {find!r}, found {n}")

    ElementTree.fromstring(document)
    temporary = TARGET.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as out:
        for item, data in items:
            out.writestr(
                item, document.encode("utf-8") if item.filename == "word/document.xml" else data
            )
    shutil.move(temporary, TARGET)

    with zipfile.ZipFile(TARGET) as archive:
        after = comment_ids(archive.read("word/comments.xml"))
    print(f"\ncomments: {len(before)} -> {len(after)}")
    if after != before:
        raise SystemExit("comments were lost or renumbered")
    print(f"written: {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
