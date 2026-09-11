"""Check the MDPI proof against the accepted manuscript before anything is changed in it.

The proof is where production has had the file. Two things in it were already known to be
wrong upstream when the paper was accepted -- the abstract stored in the submission system
was still the August text, and the author record carried a malformed affiliation -- so
those are checked first, against exact strings rather than by reading. Then everything the
revision changed is checked for survival, and every tracked change and comment production
left is listed, because a proof is answered by accepting, replying to, or editing each of
them, and one missed is one answered wrongly.

Text is read in the "all changes accepted" view: inserted runs count, deleted runs do not.
That is the text that will be published if the tracked changes are accepted.

    python paper/proof/check_proof.py [proof.docx]
"""

from __future__ import annotations

import difflib
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
ACCEPTED = PAPER / "revision_r1" / "jimaging-4539482-revised-highlighted.docx"
REPORT = HERE / "PROOF_REPORT.md"

PARA = re.compile(r"<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>", re.S)
TEXT = re.compile(r"<w:t(?: [^>]*)?>([^<]*)</w:t>")
DELTEXT = re.compile(r"<w:delText(?: [^>]*)?>([^<]*)</w:delText>")
MATH = re.compile(r"<m:oMathPara>.*?</m:oMathPara>|<m:oMath>.*?</m:oMath>", re.S)
SYMBOL = re.compile(r"<m:t(?: [^>]*)?>([^<]*)</m:t>")

AFFILIATION = "Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan"

# The two sentences the revision corrected, and what replaced them.
MUST_BE_PRESENT = {
    "abstract: the three identities, not all four": (
        "the three identities that can be evaluated without ground truth"
    ),
    "abstract: return no value, not refuse": (
        "should return no value at all rather than a computed one"
    ),
    "affiliation, exactly": AFFILIATION,
    "funding statement": "This research received no external funding",
    "generative AI declared": "Claude",
    "ldct-io named": "ldct-io",
    "taskiq-core named": "taskiq-core",
    "checklist relabelled A1": "A1.",
    "checklist relabelled B2": "B2.",
    "section 2.7 Implementation": "Implementation",
    "section 2.8 generative AI": "Use of Generative Artificial Intelligence",
}
MUST_BE_ABSENT = {
    "abstract overclaim": "the identities transferred intact",
    "unclear 'refuse' wording": "must refuse to answer",
    "lower-case affiliation": "Institute of one",
    "affiliation's extra comma": "LISIT, Co.",
}


def read(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        return {
            name: archive.read(name).decode("utf-8", errors="replace")
            for name in archive.namelist()
            if name.endswith(".xml") or name.endswith(".rels")
        }


def paragraph_texts(document: str) -> list[str]:
    out = []
    for block in PARA.findall(document):
        text = re.sub(r"\s+", " ", "".join(TEXT.findall(block))).strip()
        if text:
            out.append(text)
    return out


def flat(document: str) -> str:
    return " ".join(paragraph_texts(document))


def main() -> int:
    proof_path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(HERE.glob("*.docx"))[-1]
    proof = read(proof_path)
    accepted = read(ACCEPTED)
    doc_p, doc_a = proof["word/document.xml"], accepted["word/document.xml"]
    text_p = flat(doc_p)

    lines: list[str] = [f"# Proof check: `{proof_path.name}`", ""]
    problems: list[str] = []

    # --- what production did to the file ---------------------------------------------
    ins = re.findall(r'<w:ins w:id="[^"]*" w:author="([^"]*)"', doc_p)
    dels = re.findall(r'<w:del w:id="[^"]*" w:author="([^"]*)"', doc_p)
    fmt = len(re.findall(r"<w:rPrChange|<w:pPrChange", doc_p))
    comments_xml = proof.get("word/comments.xml", "")
    comments = re.findall(
        r'<w:comment w:id="(\d+)" w:author="([^"]*)"[^>]*>(.*?)</w:comment>', comments_xml, re.S
    )
    lines += [
        "## What production left in the file",
        "",
        f"- tracked insertions: **{len(ins)}**  (authors: {sorted(set(ins)) or '-'})",
        f"- tracked deletions: **{len(dels)}**  (authors: {sorted(set(dels)) or '-'})",
        f"- formatting changes: **{fmt}**",
        f"- comments: **{len(comments)}**",
        "",
    ]

    # --- the strings that must and must not be there ----------------------------------
    lines += ["## Strings that decide the proof", ""]
    for label, needle in MUST_BE_PRESENT.items():
        ok = needle in text_p
        lines.append(f"- {'ok  ' if ok else '**MISSING**'}  {label}")
        if not ok:
            problems.append(f"missing: {label}")
    for label, needle in MUST_BE_ABSENT.items():
        present = needle in text_p
        lines.append(f"- {'**STILL THERE**' if present else 'ok  '}  {label}")
        if present:
            problems.append(f"still there: {label}")
    lines.append("")

    # --- structure, against the accepted file -----------------------------------------
    lines += ["## Structure, accepted -> proof", ""]
    for label, pattern in (
        ("equations", r"<m:oMath[ >]"),
        ("display equations", r"<m:oMathPara>"),
        ("tables", r"<w:tbl>"),
        ("images", r"<w:drawing>"),
    ):
        a, p = len(re.findall(pattern, doc_a)), len(re.findall(pattern, doc_p))
        mark = "ok  " if p >= a else "**FEWER**"
        lines.append(f"- {mark}  {label}: {a} -> {p}")
        if p < a:
            problems.append(f"{label}: {a} -> {p}")
    refs_a = len(re.findall(r'<w:numId w:val="8"/>', doc_a))
    refs_p = len(re.findall(r'<w:numId w:val="8"/>', doc_p))
    lines.append(f"- reference-list paragraphs (numId 8): {refs_a} -> {refs_p}")
    lines.append("")

    # --- comments, in full --------------------------------------------------------------
    if comments:
        lines += ["## Comments from production", ""]
        anchors = {}
        for cid in [c[0] for c in comments]:
            m = re.search(
                rf'<w:commentRangeStart w:id="{cid}"/>(.*?)<w:commentRangeEnd w:id="{cid}"/>',
                doc_p,
                re.S,
            )
            anchors[cid] = (
                re.sub(r"\s+", " ", "".join(TEXT.findall(m.group(1)))).strip() if m else ""
            )
        for cid, author, body in comments:
            text = re.sub(r"\s+", " ", " ".join(TEXT.findall(body))).strip()
            lines += [
                f"### Comment {cid} — {author}",
                "",
                f"> {text}",
                "",
                f"Anchored on: *{anchors.get(cid, '')[:200] or '(point)'}*",
                "",
            ]

    # --- tracked changes, with context --------------------------------------------------
    if ins or dels:
        lines += ["## Tracked changes, paragraph by paragraph", ""]
        for block in PARA.findall(doc_p):
            if "<w:ins " not in block and "<w:del " not in block:
                continue
            inserted = " | ".join(
                re.sub(r"\s+", " ", "".join(TEXT.findall(m))).strip()
                for m in re.findall(r"<w:ins [^>]*>(.*?)</w:ins>", block, re.S)
            )
            deleted = " | ".join(
                re.sub(r"\s+", " ", "".join(DELTEXT.findall(m))).strip()
                for m in re.findall(r"<w:del [^>]*>(.*?)</w:del>", block, re.S)
            )
            now = re.sub(r"\s+", " ", "".join(TEXT.findall(block))).strip()
            lines += [f"- **in:** `{now[:110]}`"]
            if deleted:
                lines.append(f"  - deleted: `{deleted[:160]}`")
            if inserted:
                lines.append(f"  - inserted: `{inserted[:160]}`")
        lines.append("")

    # --- everything else production changed, as prose ----------------------------------
    pa, pp = paragraph_texts(doc_a), paragraph_texts(doc_p)
    matcher = difflib.SequenceMatcher(None, pa, pp, autojunk=False)
    changed = [op for op in matcher.get_opcodes() if op[0] != "equal"]
    lines += [f"## Paragraphs that differ from the accepted file: {len(changed)} runs", ""]
    for tag, i1, i2, j1, j2 in changed:
        old = " / ".join(pa[i1:i2])
        new = " / ".join(pp[j1:j2])
        words = difflib.ndiff(old.split(), new.split())
        diff = " ".join(
            f"[-{w[2:]}-]"
            if w.startswith("- ")
            else f"{{+{w[2:]}+}}"
            if w.startswith("+ ")
            else w[2:]
            for w in words
            if not w.startswith("? ")
        )
        lines += [f"- *{tag}* — {diff[:600]}", ""]

    lines += ["## Verdict", ""]
    lines += [f"- {p}" for p in problems] or [
        "- no problems in the decisive strings or the structure"
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    print(f"proof: {proof_path.name}")
    print(f"  tracked ins/del/format: {len(ins)}/{len(dels)}/{fmt}   comments: {len(comments)}")
    print(f"  paragraph runs differing from the accepted file: {len(changed)}")
    print(f"  problems: {len(problems)}")
    for p in problems:
        print(f"    - {p}")
    print(f"report: {REPORT}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
