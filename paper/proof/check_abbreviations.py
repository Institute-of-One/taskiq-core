"""Check each abbreviation is defined at first use in the three places MDPI counts.

The English Editor's note on this proof says, as it did on Tomography: abbreviations must be
defined the first time they appear in each of three sections -- the abstract, the main
text, and the first figure or table. Each section is read on its own, as a reader who
starts there would, so an acronym defined in the Introduction is still undefined in the
abstract. On Tomography this note found CT, CTDIvol and ICRP undefined everywhere.

A definition is taken to be the acronym in parentheses after words ("noise power spectrum
(NPS)") or words in parentheses after the acronym ("NPS (noise power spectrum)").

    python paper/proof/check_abbreviations.py manuscript.docx
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

PARA = re.compile(r"<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>", re.S)
TBL = re.compile(r"<w:tbl>.*?</w:tbl>", re.S)
ACRONYM = re.compile(r"(?<![A-Za-z])([A-Z][A-Z0-9]{1,}(?:-[A-Z0-9]+)?)(?![a-z])")

# Tokens that look like acronyms and are not: units, roman numerals, labels, names.
NOT_ACRONYMS = {
    "II",
    "III",
    "IV",
    "MIT",
    "USA",
    "UK",
    "JP",
    "PDF",
    "URL",
    "DOI",
    "ORCID",
    "CC",
    "BY",
    "A1",
    "A2",
    "A3",
    "A4",
    "B1",
    "B2",
    "SY",
    "OU",
    "HH",
    "KJ",
    "NJ",
    "MD",
    "CA",
    "LISIT",
}


def text_of(block: str) -> str:
    return re.sub(r"\s+", " ", "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", block))).strip()


def sections(document: str) -> dict[str, str]:
    tables = TBL.findall(document)
    body = TBL.sub(" ", document)
    paras = [text_of(p) for p in PARA.findall(body)]
    paras = [p for p in paras if p]

    start_abs = next(i for i, p in enumerate(paras) if p.lower().startswith("abstract"))
    start_kw = next(i for i, p in enumerate(paras) if p.lower().startswith("keywords"))
    start_intro = next(i for i, p in enumerate(paras) if re.match(r"1\.\s+Introduction", p))
    end_body = next(
        (
            i
            for i, p in enumerate(paras)
            if re.match(r"(Funding|Author Contributions|Institutional Review|Data Availability)", p)
        ),
        len(paras),
    )
    abstract = " ".join(paras[start_abs:start_kw])
    main = " ".join(
        p for p in paras[start_intro:end_body] if not re.match(r"(Figure|Table) \d+\.", p)
    )

    captions = [p for p in paras if re.match(r"(Figure|Table) \d+\.", p)]
    first_caption = captions[0] if captions else ""
    first_is_table = first_caption.startswith("Table")
    first_item = first_caption
    if first_is_table and tables:
        first_item += " " + text_of(tables[0])
    return {
        "abstract": abstract,
        "main text": main,
        f"first figure or table ({first_caption[:9]})": first_item,
    }


def defined_at(text: str, acronym: str) -> tuple[bool, str]:
    m = re.search(rf"(?<![A-Za-z]){re.escape(acronym)}(?![a-z])", text)
    if not m:
        return True, ""
    window = text[max(0, m.start() - 90) : m.end() + 60]
    after_words = re.search(rf"[a-z][a-z\- ]{{3,}}\(\s*{re.escape(acronym)}\s*[;,)]", window)
    words_after = re.search(rf"{re.escape(acronym)}\s*\(\s*[a-z]", window)
    return bool(after_words or words_after), window.strip()


def main() -> int:
    path = Path(sys.argv[1])
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    parts = sections(document)
    problems = 0
    for name, text in parts.items():
        found = []
        for m in ACRONYM.finditer(text):
            token = m.group(1)
            if token in NOT_ACRONYMS or token.isdigit() or token not in found:
                if token not in NOT_ACRONYMS and not token.isdigit() and token not in found:
                    found.append(token)
        print(f"=== {name}: {len(found)} abbreviations")
        for token in found:
            ok, where = defined_at(text, token)
            if not ok:
                problems += 1
                print(f"   UNDEFINED  {token:9} ...{where[:130]}...")
            else:
                print(f"   ok         {token}")
        print()
    print(f"{problems} undefined at first use")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
