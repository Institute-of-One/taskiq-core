"""Stop tables breaking in the middle of a row, and repeat the header when they do break.

Pandoc emits tables that Word is free to split anywhere, and it split Table 2 through the
middle of a cell: "NPS closed form" became "NPS closed" on one page and "form" alone at the
top of the next, with no header row above it to say what the columns were. A table crossing
a page is ordinary; a row cut in half is a defect, and a continuation without a header is
unreadable.

Two settings fix it, and both live in the row properties:

* ``cantSplit`` on every row — a row moves to the next page whole rather than being cut;
* ``tblHeader`` on the first row — Word repeats it at the top of each continuation.

The `_set_property` helper is ported from ct_dosemc_core, where the same problem was solved
for another manuscript. Its comment there is worth keeping: a properties element occurs in
three forms -- present with children, present and self-closing, and absent -- and handling
only the first two appends a *second* properties element, which the schema forbids and Word
silently ignores, so the setting reads as applied and does nothing.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

DOCUMENT = "word/document.xml"


def _set_property(fragment: str, container: str, element: str, prop: str) -> str:
    """Add ``prop`` to every ``container``'s properties, whatever form they take."""
    opened = f"<{element}>"
    fragment = re.sub(re.escape(opened), f"{opened}{prop}", fragment)
    fragment = re.sub(rf"<{re.escape(element)}\s*/>", f"{opened}{prop}</{element}>", fragment)
    return re.sub(
        rf"(<{re.escape(container)}\b[^>]*>)(?<!/>)(?!<{re.escape(element)})",
        rf"\1{opened}{prop}</{element}>",
        fragment,
    )


def _repeat_header_rows(document: str) -> tuple[str, int]:
    """Mark the first row of each table as a header, so Word repeats it after a break."""
    count = 0

    def mark(match: re.Match) -> str:
        nonlocal count
        table = match.group(0)
        first = re.search(r"<w:tr\b.*?</w:tr>", table, re.S)
        if first is None:
            return table
        count += 1
        headed = _set_property(first.group(0), "w:tr", "w:trPr", "<w:tblHeader/>")
        return table.replace(first.group(0), headed, 1)

    return re.sub(r"<w:tbl>.*?</w:tbl>", mark, document, flags=re.S), count


def keep_rows_whole(path: Path) -> tuple[int, int]:
    """Apply both settings in place. Returns (rows protected, tables given headers)."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        contents = {name: archive.read(name) for name in names}

    document = contents[DOCUMENT].decode("utf-8")
    rows = len(re.findall(r"<w:tr\b", document))
    document = _set_property(document, "w:tr", "w:trPr", "<w:cantSplit/>")
    document, tables = _repeat_header_rows(document)
    contents[DOCUMENT] = document.encode("utf-8")

    temporary = path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.writestr(name, contents[name])
    shutil.move(str(temporary), str(path))
    return rows, tables


def verify(path: Path) -> dict:
    """Read the setting back out of the written file rather than trusting the call."""
    with zipfile.ZipFile(path) as archive:
        document = archive.read(DOCUMENT).decode("utf-8")
    return {
        "rows": len(re.findall(r"<w:tr\b", document)),
        "rows_protected": document.count("<w:cantSplit/>"),
        "tables": len(re.findall(r"<w:tbl>", document)),
        "headers_repeated": document.count("<w:tblHeader/>"),
        # a second properties element is the failure this helper exists to avoid
        "double_trPr": len(re.findall(r"<w:trPr>.*?</w:trPr>\s*<w:trPr>", document, re.S)),
    }
