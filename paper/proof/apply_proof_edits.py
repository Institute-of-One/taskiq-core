"""Answer the J. Imaging proof by editing only the text, never the markup around it.

Word's own find-and-replace deletes any editorial comment whose anchor lies inside the
range it replaces. Four attempts at this proof lost between four and seven of the
twenty-five comments that way, and the editorial office's first instruction is not to
delete them. So the edits are made here instead, in the document's XML, by rewriting the
contents of `<w:t>` elements and touching nothing else: comment anchors, bookmarks,
equations and run properties are all elements, not text, and are left exactly where they
were.

It also reorders the reference list, which MDPI asks to run in order of first citation,
and replaces the two figures whose images in the proof were older than the ones the
public code produces.

Run it against the file the editorial office sent; it writes a new file and checks its
own work.

    python paper/proof/apply_proof_edits.py
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
SOURCE = HERE / "jimaging-4539482-for proof.docx"
TARGET = HERE / "jimaging-4539482-answered.docx"
FIGURE4 = PAPER / "figures" / "fig4_injection.png"
FIGURE5 = Path("D:/DevGit/ldct-io/results/acr_atlas.png")

PARA = re.compile(r"<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>", re.S)
TEXT = re.compile(r"<w:t(?: [^>]*)?>([^<]*)</w:t>")

ACCESSED = "(accessed on 12 September 2026)"

#: (what to find, what to put there, how many times it must occur)
EDITS: list[tuple[str, str, int]] = [
    # Abbreviations, at first use in the abstract and in the main text, as the English
    # Editor's note requires. CT was the one that mattered: it was used before
    # "computed tomography" was ever written out.
    (
        "the noise power spectrum, the noise-equivalent quanta",
        "the noise power spectrum (NPS), the noise-equivalent quanta",
        1,
    ),
    (
        "measured ACR phantom projections across seven",
        "measured American College of Radiology (ACR) phantom projections across seven",
        1,
    ),
    (
        "formalised in ISO 12233",
        "formalised by the International Organization for Standardization (ISO) in ISO 12233",
        1,
    ),
    (
        "standardised for digital X-ray detectors in IEC 62220-1",
        "standardised for digital X-ray detectors by the International Electrotechnical "
        "Commission (IEC) in IEC 62220-1",
        1,
    ),
    (
        "reviewed for CT [12], and its use in computed tomography has been consolidated in "
        "AAPM Task Group 233",
        "reviewed for computed tomography (CT) [12], and its use in CT has been consolidated "
        "in American Association of Physicists in Medicine (AAPM) Task Group 233",
        1,
    ),
    (
        "the area under the ROC curve",
        "the area under the receiver operating characteristic (ROC) curve",
        1,
    ),
    (
        "Subtracting the mean from each region of interest sets",
        "Subtracting the mean from each region of interest (ROI) sets",
        1,
    ),
    ("excludes the DC bin", "excludes the zero-frequency (DC) bin", 1),
    (
        "run on measured ACR phantom projections from",
        "run on measured American College of Radiology (ACR) phantom projections from",
        1,
    ),
    (
        "It contains no DICOM handling",
        "It contains no Digital Imaging and Communications in Medicine (DICOM) handling",
        1,
    ),
    ("Use of Generative AI", "Use of Generative Artificial Intelligence (AI)", 1),
    # The manufacturer, with its city and country, where the measured data is introduced.
    (
        "projections from LDCT-and-Projection-data [10].",
        "projections from LDCT-and-Projection-data [10], acquired on a Siemens CT scanner "
        "(Siemens Healthineers, Forchheim, Germany).",
        1,
    ),
    # Software versions, asked for twice.
    (
        "one pure-Python implementation of the chain (taskiq-core), which computes",
        "one pure-Python implementation of the chain (taskiq-core v0.4.0), which computes",
        1,
    ),
    (
        "depending only on NumPy and SciPy, with Matplotlib for figures",
        "depending only on NumPy and SciPy, with Matplotlib for figures; the results reported "
        "here were produced with Python 3.14.3, NumPy 2.5.1, SciPy 1.17.1 and "
        "Matplotlib 3.10.8",
        1,
    ),
    ("(Claude, Anthropic)", "(Claude Opus 5, Anthropic)", 2),
    # Access dates for the two repositories.
    ("taskiq-core> under the MIT licence", f"taskiq-core> {ACCESSED} under the MIT licence", 1),
    ("ldct-io>, MIT)", f"ldct-io> {ACCESSED}, MIT)", 1),
    # A section that does not exist. All four citations mean Section 3.6.
    ("Section 4.6", "Section 3.6", 3),
    ("(Sections 3.8 and 4.6)", "(Sections 3.6 and 3.8)", 1),
    # The defect is called disk in the released code; production made it disc everywhere,
    # which is right for the shape and wrong for the name.
    ("disc\u2014the signal built", "disk\u2014the signal built", 1),
    ("nps_area (Parseval), disc", "nps_area (Parseval), disk", 1),
    # The Acknowledgments label came back empty; MDPI asks for its own GenAI wording.
    (
        "Acknowledgments:",
        "Acknowledgments: During the preparation of this manuscript, the author used Claude "
        "Opus 5 (Anthropic) for the purposes of code scaffolding, test drafting, figure and "
        "script generation, and drafting and editing manuscript text. The author has reviewed "
        "and edited the output and takes full responsibility for the content of this "
        "publication. Section 2.8 sets out this use in full, including what the model was not "
        "used for.",
        1,
    ),
]

#: Citations, renumbered so the list runs in order of first appearance. Written through a
#: placeholder because the mapping has a cycle: 6 becomes 17 and 17 becomes 21.
CITATIONS: list[tuple[str, str]] = [
    ("[6]", "17"),
    ("[8]", "7"),
    ("[9]", "10"),
    ("[10]", "18"),
    ("[11]", "8"),
    ("[12]", "9"),
    ("[13]", "11"),
    ("[16]", "19"),
    ("[17]", "21"),
    ("[18]", "14"),
    ("[19]", "15"),
    ("[20]", "16"),
    ("[21]", "20"),
    ("[14,15]", "12,13"),
    ("[1,5,7,8]", "1,5,6,7"),
]
#: New order of the reference list: position k holds the entry numbered ORDER[k-1] before.
ORDER = [1, 2, 3, 4, 5, 7, 8, 11, 12, 9, 13, 14, 15, 18, 19, 20, 6, 10, 16, 21, 17]


def replace_in_paragraph(block: str, find: str, repl: str) -> tuple[str, int]:
    """Replace text inside a paragraph without disturbing any element around it.

    The visible text of a paragraph is spread over several `<w:t>` elements, and a phrase
    can straddle them. The replacement is written into the first element the phrase
    touches and the remainder of the phrase is cut from the ones after it, so the count
    and order of every other element -- comment anchors included -- is unchanged.
    """
    runs = list(TEXT.finditer(block))
    if not runs:
        return block, 0
    text = "".join(m.group(1) for m in runs)
    if find not in text:
        return block, 0

    # Which run each character of the concatenated text belongs to.
    owner: list[tuple[int, int]] = []
    for index, match in enumerate(runs):
        for offset in range(len(match.group(1))):
            owner.append((index, offset))

    pieces = [list(m.group(1)) for m in runs]
    count = 0
    position = text.find(find)
    while position != -1:
        count += 1
        first_run, first_offset = owner[position]
        # Blank every character the phrase covers, then write the replacement into the
        # first run's own characters.
        for k in range(position, position + len(find)):
            run, offset = owner[k]
            pieces[run][offset] = ""
        pieces[first_run][first_offset] = repl
        position = text.find(find, position + len(find))

    out, last = [], 0
    for index, match in enumerate(runs):
        out.append(block[last : match.start(1)])
        out.append("".join(pieces[index]))
        last = match.end(1)
    out.append(block[last:])
    rebuilt = "".join(out)
    # A run that now begins or ends with a space needs to say so, or Word eats it.
    rebuilt = re.sub(r"<w:t>(?=[^<]*(?:^ | $))", '<w:t xml:space="preserve">', rebuilt)
    rebuilt = rebuilt.replace("<w:t>", '<w:t xml:space="preserve">')
    return rebuilt, count


def escape(text: str) -> str:
    """The text as it is written inside the XML, where < and > are entities."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def apply(document: str, find: str, repl: str) -> tuple[str, int]:
    find, repl = escape(find), escape(repl)
    out, last, total = [], 0, 0
    for match in PARA.finditer(document):
        out.append(document[last : match.start()])
        block, n = replace_in_paragraph(match.group(0), find, repl)
        out.append(block)
        total += n
        last = match.end()
    out.append(document[last:])
    return "".join(out), total


def reorder_references(document: str) -> str:
    spans = [(m.start(), m.end(), m.group(0)) for m in PARA.finditer(document)]
    index = [i for i, (_, _, b) in enumerate(spans) if 'w:pStyle w:val="MDPI81references"' in b]
    if index != list(range(index[0], index[0] + len(ORDER))):
        raise SystemExit("the reference paragraphs are not contiguous; not reordering")
    entries = [spans[i][2] for i in index]
    return (
        document[: spans[index[0]][0]]
        + "".join(entries[o - 1] for o in ORDER)
        + document[spans[index[-1]][1] :]
    )


def main() -> int:
    with zipfile.ZipFile(SOURCE) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        items = [(item, archive.read(item.filename)) for item in archive.infolist()]
    comments_before = len(
        re.findall(
            r"<w:comment w:id=",
            dict((i.filename, d) for i, d in items)["word/comments.xml"].decode("utf-8"),
        )
    )

    print("edits")
    for find, repl, expected in EDITS:
        document, n = apply(document, find, repl)
        mark = "ok  " if n == expected else "WRONG"
        print(f"  {mark} {n} of {expected}   {find[:56]}")
        if n != expected:
            raise SystemExit(f"expected {expected} occurrences of {find!r}, found {n}")

    print("\ncitations")
    open_mark, close_mark = "\u00ab", "\u00bb"
    for old, new in CITATIONS:
        document, n = apply(document, old, f"{open_mark}{new}{close_mark}")
        print(f"  {old:12} -> [{new}]   {n} occurrence(s)")
    document, a = apply(document, open_mark, "[")
    document, b = apply(document, close_mark, "]")
    print(f"  placeholders restored: {a} / {b}")

    document = reorder_references(document)
    print("\nreference list reordered")

    ElementTree.fromstring(document)
    swapped = {
        "word/media/image4.png": FIGURE4.read_bytes(),
        "word/media/image5.png": FIGURE5.read_bytes(),
    }
    temporary = TARGET.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as out:
        for item, data in items:
            if item.filename == "word/document.xml":
                data = document.encode("utf-8")
            elif item.filename in swapped:
                data = swapped[item.filename]
            out.writestr(item, data)
    shutil.move(temporary, TARGET)

    with zipfile.ZipFile(TARGET) as archive:
        comments_after = len(
            re.findall(r"<w:comment w:id=", archive.read("word/comments.xml").decode("utf-8"))
        )
    print(f"\ncomments: {comments_before} -> {comments_after}")
    if comments_after != comments_before:
        raise SystemExit("comments were lost")
    print(f"written: {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
