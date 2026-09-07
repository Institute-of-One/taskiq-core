"""Give the paragraphs added in Word the indentation the rest of the manuscript has.

The peer-review template indents body text with direct formatting on each paragraph --
`<w:ind w:left="2608" w:firstLine="425"/>` -- and not through the paragraph style. A new
paragraph given the right style therefore still comes out flush left, four and a half
centimetres to the left of the text above it, and the five paragraphs typed into Word did.

The checklist has the same fault from the other direction. Its items used to be a numbered
list, and the indent came from the numbering definition, which supplies
`left="3033" hanging="425"`. Turning the numbering off to make room for the A1-B2 labels
took the indent with it, and the placeholder written in its place was the reference list's
indent, which is a different and much smaller one.

Both are corrected here against the file the editorial office sent, rather than against
anything remembered: the body indent is read from the paragraphs that were never touched,
and the list indent from the numbering definition itself.

    python paper/revision_r1/fix_indentation.py
"""

from __future__ import annotations

import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
FORMATTED = HERE / "jimaging-4539482- peer review.docx"
TARGET = HERE / "jimaging-4539482-revised-highlighted.docx"

PARAGRAPH = re.compile(r"<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>", re.S)
PPR = re.compile(r"<w:pPr>.*?</w:pPr>", re.S)
IND = re.compile(r"<w:ind [^>]*/>")
ELEMENT = re.compile(r"<(w14?:[A-Za-z]+)(?: [^>]*?)?(?:/>|>.*?</\1>)", re.S)

# Paragraph properties are an ordered sequence; an indent in the wrong place is not a
# misplaced indent but an invalid document.
PPR_ORDER = [
    "w:pStyle",
    "w:keepNext",
    "w:keepLines",
    "w:pageBreakBefore",
    "w:framePr",
    "w:widowControl",
    "w:numPr",
    "w:suppressLineNumbers",
    "w:pBdr",
    "w:shd",
    "w:tabs",
    "w:suppressAutoHyphens",
    "w:kinsoku",
    "w:wordWrap",
    "w:overflowPunct",
    "w:topLinePunct",
    "w:autoSpaceDE",
    "w:autoSpaceDN",
    "w:bidi",
    "w:adjustRightInd",
    "w:snapToGrid",
    "w:spacing",
    "w:ind",
    "w:contextualSpacing",
    "w:mirrorIndents",
    "w:suppressOverlap",
    "w:jc",
    "w:textDirection",
    "w:textAlignment",
    "w:textboxTightWrap",
    "w:outlineLvl",
    "w:divId",
    "w:cnfStyle",
    "w:rPr",
    "w:sectPr",
    "w:pPrChange",
]

BODY_STYLES = {"a0", "afe", "BodyText", "FirstParagraph"}


def text_of(block: str) -> str:
    return re.sub(r"\s+", " ", "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block))).strip()


def style_of(block: str) -> str:
    found = re.search(r'<w:pStyle w:val="([^"]+)"', block)
    return found.group(1) if found else ""


def numbering_of(block: str) -> str:
    found = re.search(r'<w:numPr>.*?<w:numId w:val="(\d+)"/>', block, re.S)
    return found.group(1) if found else ""


def body_indent() -> str:
    """The indentation the untouched body paragraphs carry, taken from the original."""
    with zipfile.ZipFile(FORMATTED) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    seen: Counter[str] = Counter()
    for match in PARAGRAPH.finditer(document):
        block = match.group(0)
        if style_of(block) in BODY_STYLES:
            found = IND.search(block)
            if found:
                seen[found.group(0)] += 1
    return seen.most_common(1)[0][0]


def list_indent(num_id: str) -> str:
    """The indentation the numbering definition used to supply for a list."""
    with zipfile.ZipFile(FORMATTED) as archive:
        numbering = archive.read("word/numbering.xml").decode("utf-8")
    num = re.search(rf'<w:num w:numId="{num_id}"[^>]*>.*?</w:num>', numbering, re.S)
    abstract = re.search(r'<w:abstractNumId w:val="(\d+)"/>', num.group(0)).group(1)
    block = re.search(
        rf'<w:abstractNum w:abstractNumId="{abstract}"[^>]*>.*?</w:abstractNum>',
        numbering,
        re.S,
    ).group(0)
    level = re.search(r'<w:lvl w:ilvl="0"[^>]*>.*?</w:lvl>', block, re.S).group(0)
    return IND.search(level).group(0)


def set_indent(ppr: str, indent: str) -> str:
    """Replace the paragraph's indentation, keeping the properties in their required order."""
    inner = re.sub(r"^<w:pPr>|</w:pPr>$", "", ppr)
    children = [
        (match.group(1), match.group(0))
        for match in ELEMENT.finditer(inner)
        if match.group(1) != "w:ind"
    ]
    children.append(("w:ind", indent))
    children.sort(key=lambda item: PPR_ORDER.index(item[0]) if item[0] in PPR_ORDER else 999)
    return "<w:pPr>" + "".join(xml for _, xml in children) + "</w:pPr>"


def main() -> int:
    body = body_indent()
    checklist = list_indent("7")
    centred = re.sub(r' w:(firstLine|hanging)="\d+"', "", body)
    print(f"body paragraphs   : {body}")
    print(f"checklist items   : {checklist}")
    print(f"centred equation  : {centred}\n")

    with zipfile.ZipFile(TARGET) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        items = [(item, archive.read(item.filename)) for item in archive.infolist()]

    out, position, index, fixed = [], 0, 0, 0
    for match in PARAGRAPH.finditer(document):
        block = match.group(0)
        index += 1
        out.append(document[position : match.start()])
        position = match.end()

        wanted = None
        if style_of(block) == "MDPI37itemize" and numbering_of(block) == "0":
            wanted = checklist  # a checklist item, its numbering turned off for the labels
        elif style_of(block) in BODY_STYLES and not IND.search(block):
            if index <= 5:
                out.append(block)  # the title block is flush left by design
                continue
            wanted = centred if not text_of(block) else body

        if wanted is None or (IND.search(block) or [None]) and wanted in block:
            out.append(block)
            continue

        ppr = PPR.search(block)
        if not ppr:
            out.append(block)
            continue
        out.append(block.replace(ppr.group(0), set_indent(ppr.group(0), wanted), 1))
        fixed += 1
        print(f"  paragraph {index:4}: {wanted}  {(text_of(block) or '(the equation)')[:52]!r}")
    out.append(document[position:])

    patched = "".join(out)
    ElementTree.fromstring(patched)

    shutil.copy(TARGET, TARGET.with_suffix(".before-indent.docx"))
    with zipfile.ZipFile(TARGET, "w", zipfile.ZIP_DEFLATED) as target:
        for item, data in items:
            target.writestr(
                item, patched.encode("utf-8") if item.filename == "word/document.xml" else data
            )
    print(f"\n{fixed} paragraphs given the indentation of the text around them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
