"""Apply the revision into the journal's own formatted file, and say what is left.

The editorial office returned the revision because it had been rebuilt from markdown and
had lost their template. Their file has to be the base, which leaves two ways to get the
revision into it: retype thirty-nine edits by hand, or change the text of the affected
paragraphs in place and leave the document otherwise untouched. This does the second for
every edit it can do safely, and writes the rest out as a much shorter list to apply in
Word.

Safely means: the paragraph is found, it carries no display equation, its inline equations
are matched one-for-one by the replacement's maths so they can be moved across rather than
retyped, and it is not a markdown list that would collapse several Word paragraphs into
one. Anything else is refused and reported. A refusal costs a hand edit; a wrong guess
costs a second rejection.

Three things the diff cannot work out are told to it here.

Two passages are restructured rather than edited -- Section 4.2, where six checks become
two labelled families, and Sections 2.7 and 2.8, where an implementation section is
inserted ahead of the one on generative AI. In both, matching revised paragraphs to
submitted ones by resemblance puts the right text in the wrong paragraph: it wrote
checklist item A3 into the paragraph belonging to the closing remark, and it left the old
generative-AI paragraph stranded at the end of the section that replaced it. Both are
therefore laid out here paragraph by paragraph instead of inferred.

And the numbered lists are numbered by Word, not in their text. A replacement carrying its
own "1." would print the label twice, so the references keep Word's numbering and lose the
typed one; the checklist, whose new A1-A4 and B1-B2 labels Word's automatic numbering
cannot produce, loses Word's numbering and keeps the typed labels, with the indent the
numbering used to supply written back explicitly.

    python paper/revision_r1/apply_changes.py
"""

from __future__ import annotations

import difflib
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import docx_edit as edit

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MANUSCRIPT = REPO / "paper" / "manuscript.md"
FORMATTED = HERE / "jimaging-4539482- peer review.docx"
OUTPUT = HERE / "jimaging-4539482-revised-highlighted.docx"
REMAINING = HERE / "CHANGES_TO_APPLY.md"
SUBMISSION_DATE = "2026-08-18"

CHECKLIST_NUMBERING = "7"  # the numId of the list in Section 4.2
REFERENCE_NUMBERING = "8"  # the numId of the reference list
CHECKLIST_INDENT = '<w:ind w:left="425" w:hanging="425"/>'
NO_NUMBERING = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'

SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to"}

# The two restructured passages, laid out against the formatted file's own paragraph
# numbers. `at` is a paragraph of that file, counting from one; `starts` identifies the
# revised paragraph that belongs there. Everything else in the revision is worked out from
# the diff.
REGIONS: list[dict] = [
    # Section 2.7 becomes Implementation; what was 2.7 becomes 2.8 and is rewritten.
    {"op": "replace", "at": 86, "starts": "### 2.7 Implementation"},
    {"op": "replace", "at": 87, "starts": "The estimators, the phantoms and the observers"},
    {"op": "insert", "at": 87, "starts": "### 2.8 Use of generative AI"},
    {"op": "insert", "at": 87, "starts": "A large language model (Claude, Anthropic)"},
    {"op": "insert", "at": 87, "starts": "The relationship between that assistance"},
    # Section 4.2: six checks in one numbered list become two labelled families.
    {"op": "replace", "at": 264, "starts": "Six checks, in two families."},
    {"op": "insert", "at": 264, "starts": "**Family A", "style": "BodyText"},
    {"op": "replace", "at": 265, "starts": "**A1.**", "delist": True},
    {"op": "replace", "at": 266, "starts": "**A2.**", "delist": True},
    {"op": "replace", "at": 267, "starts": "**A3.**", "delist": True},
    {"op": "replace", "at": 268, "starts": "**A4.**", "delist": True},
    {"op": "replace", "at": 269, "starts": "**Family B", "delist": True, "style": "BodyText"},
    {"op": "replace", "at": 270, "starts": "**B1.**", "delist": True},
    {"op": "replace", "at": 271, "starts": "**B2.**", "delist": True},
    {"op": "replace", "at": 272, "starts": "The injection study adds two methodological"},
    # Figure captions sit next to the image they belong to, which is a paragraph with no
    # text; the aligner has nothing to match on there and loses its place, so both captions
    # are named rather than searched for.
    {"op": "replace", "at": 101, "starts": "**Figure 4.**"},
    {"op": "replace", "at": 217, "starts": "**Figure 5.**"},
    # Reworded rather than edited, and too different from its earlier self to be recognised
    # as the same paragraph: left to the diff it would be inserted beside the paragraph it
    # replaces, leaving the superseded claim about all four identities in the document.
    {"op": "replace", "at": 221, "starts": "Three of the four internal identities"},
    {"op": "replace", "at": 69, "starts": "Two points deserve emphasis"},
    # One markdown bullet list is three Word paragraphs. Only the second item changed, but
    # the list is one block to the diff, so the block is split here and its items laid
    # against the three paragraphs they became.
    {"op": "list", "at": 16, "starts": "* A slanted-edge MTF routine"},
]


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


def blocks(markdown: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", markdown) if block.strip()]


def plain(markdown: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", markdown)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\$[^$]*\$", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def align(before: list[str], word_texts: list[str]) -> list[int | None]:
    """Map each submitted paragraph to the formatted document's paragraph of the same text.

    The formatted file is the submitted manuscript, so the two sequences run in step; the
    match is constrained to move forwards so that a paragraph repeated in the text cannot
    pull the alignment backwards. A markdown block that becomes several Word paragraphs --
    a table, a bullet list -- matches none of them well and is left unmapped.
    """
    mapping: list[int | None] = []
    position = 0
    for block in before:
        needle = plain(block)[:120]
        best, score = None, 0.0
        for index in range(position, min(position + 60, len(word_texts))):
            ratio = difflib.SequenceMatcher(None, needle, word_texts[index][:120]).ratio()
            if ratio > score:
                best, score = index, ratio
        if best is not None and score >= 0.6:
            mapping.append(best)
            position = best + 1
        else:
            mapping.append(None)
    return mapping


def pair(old: list[str], new: list[str], threshold: float = 0.5) -> list[int | None]:
    """Which submitted paragraph each revised paragraph is a revision of, if any.

    Pairing them off in order is wrong wherever the revision inserts a paragraph in the
    middle of a rewritten passage: every paragraph after the insertion shifts by one. So
    each revised paragraph is matched to the submitted paragraph it most resembles, still
    moving forwards, and one resembling none of them is an insertion, not a replacement.
    """
    matched: list[int | None] = []
    position = 0
    for block in new:
        needle = plain(block)
        best, score = None, 0.0
        for index in range(position, len(old)):
            ratio = difflib.SequenceMatcher(None, needle, plain(old[index])).ratio()
            if ratio > score:
                best, score = index, ratio
        if best is not None and score >= threshold:
            matched.append(best)
            position = best + 1
        else:
            matched.append(None)

    # A paragraph reworded rather than edited resembles its own earlier self too little to
    # be matched, and would be inserted beside the paragraph it was meant to replace,
    # leaving both in the document. But if one submitted paragraph and one revised
    # paragraph are left over between the same two matched neighbours, there is nothing
    # else either could be, and the pair is taken.
    taken = {index for index in matched if index is not None}
    for position, index in enumerate(matched):
        if index is not None:
            continue
        lower = max((matched[j] for j in range(position) if matched[j] is not None), default=-1)
        upper = min(
            (matched[j] for j in range(position + 1, len(matched)) if matched[j] is not None),
            default=len(old),
        )
        gap = [k for k in range(lower + 1, upper) if k not in taken]
        if len(gap) == 1:
            candidate = gap[0]
            if (
                difflib.SequenceMatcher(None, plain(new[position]), plain(old[candidate])).ratio()
                >= 0.25
            ):
                matched[position] = candidate
                taken.add(candidate)
    return matched


def title_case(title: str) -> str:
    words = title.split()
    return " ".join(
        word if index and word.lower() in SMALL_WORDS else word[:1].upper() + word[1:]
        for index, word in enumerate(words)
    )


def heading_text(block: str) -> str:
    """A heading as the journal writes them: the number, a full stop, then the title."""
    body = block.lstrip("#").strip()
    numbered = re.match(r"([\d.]+)\s+(.*)", body)
    if not numbered:
        return title_case(body)
    return f"{numbered.group(1).rstrip('.')}. {title_case(numbered.group(2))}"


def numbering_of(paragraph: str) -> str | None:
    found = re.search(r'<w:numPr>.*?<w:numId w:val="(\d+)"/>', paragraph, re.S)
    return found.group(1) if found else None


def denumber(ppr: str) -> str:
    """Turn Word's automatic numbering off, and write back the indent it was providing.

    Deleting the paragraph's own numbering is not enough, because the MDPI itemize style
    defines numbering too, and the paragraph then falls back to it: the checklist printed
    "4. A1." and "9. B2.", Word's label beside the one the revision added. Numbering has to
    be overridden rather than removed, which in Word means numbering identifier zero.
    """
    without = re.sub(r"<w:numPr>.*?</w:numPr>", NO_NUMBERING, ppr, count=1, flags=re.S)
    if NO_NUMBERING not in without:
        after_style = re.search(r"<w:pStyle [^>]*/>", without)
        cut = after_style.end() if after_style else without.index(">") + 1
        without = without[:cut] + NO_NUMBERING + without[cut:]
    if "<w:ind " not in without:
        # Paragraph properties are an ordered sequence, and the indent belongs before the
        # paragraph mark's run properties, not appended at the end.
        mark = without.find("<w:rPr>")
        cut = mark if mark != -1 else without.rindex("</w:pPr>")
        without = without[:cut] + CHECKLIST_INDENT + without[cut:]
    return without


def restyle(ppr: str, style: str) -> str:
    return re.sub(r'<w:pStyle w:val="[^"]+"/>', f'<w:pStyle w:val="{style}"/>', ppr)


def is_multi_item_list(block: str) -> bool:
    return sum(1 for line in block.splitlines() if re.match(r"\s*([-*+]|\d+\.)\s", line)) > 1


def only_block(after: list[str], prefix: str) -> str:
    found = [block for block in after if block.startswith(prefix)]
    if len(found) != 1:
        raise SystemExit(f"{len(found)} revised paragraphs start with {prefix!r}; expected one")
    return found[0]


def reference_items(markdown: str) -> list[str]:
    section = markdown.split("## References", 1)[1]
    return [line.strip() for line in section.splitlines() if re.match(r"\s*\d+\.\s", line)]


class Edits:
    """The edits accumulated against the formatted document, and what could not be made."""

    def __init__(self, paragraphs: list[str], pool: dict[str, str]) -> None:
        """Take the document's paragraphs, and the equations available to be moved."""
        self.paragraphs = paragraphs
        self.pool = pool
        self.replacements: dict[int, str] = {}
        self.insertions: dict[int, list[str]] = {}
        self.applied: list[str] = []
        self.deferred: list[dict] = []
        self.record: list[tuple[str, int, str, str]] = []

    def replace(self, index: int, xml: str, note: str) -> None:
        """Put new text in a paragraph. Two edits claiming one paragraph is a mistake."""
        if index in self.replacements:
            raise SystemExit(f"two edits both replace paragraph {index + 1}")
        self.replacements[index] = xml
        self.applied.append(f"replaced paragraph {index + 1}: {note}")
        self.record.append(("replace", index, edit.text_of(self.paragraphs[index]), xml))

    def insert(self, index: int, xml: str, note: str) -> None:
        """Add a paragraph after the given one, keeping the order they were added in."""
        self.insertions.setdefault(index, []).append(xml)
        self.applied.append(f"inserted after paragraph {index + 1}: {note}")
        self.record.append(("insert", index, edit.text_of(self.paragraphs[index]), xml))

    def write_report(self, path: Path) -> None:
        """Every applied edit, as it was and as it now reads, for a human to check.

        The machine can tell that it put text somewhere; it cannot tell that it put the
        right text in the right place. That judgement needs the two side by side.
        """
        lines = [
            "# What was applied, and what it replaced",
            "",
            "Each entry is one edit made into the journal's formatted file: the paragraph as",
            "the editorial office sent it, and the paragraph as it now reads. Equations show",
            "as `[equation]`, since they were moved across rather than retyped.",
            "",
        ]
        for kind, index, was, xml in self.record:
            now = re.sub(r"\s+", " ", "".join(edit.TEXT.findall(edit.MATH.sub("[equation]", xml))))
            lines += [f"## {kind} at paragraph {index + 1}", ""]
            lines += [f"**{'Was' if kind == 'replace' else 'After'}:** {was or '(empty)'}", ""]
            lines += [f"**{'Now' if kind == 'replace' else 'Inserted'}:** {now.strip()}", ""]
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    def defer(self, **item) -> None:
        """Record an edit that cannot be made safely here, with the reason why."""
        self.deferred.append(item)


def apply_regions(edits: Edits, after: list[str]) -> dict[str, int]:
    """Apply the restructured passages, and say which paragraph of the file each one used.

    The paragraph matters as well as the fact: a later insertion anchored to "the previous
    paragraph" has to be told about a paragraph handled here, or it will be described as
    belonging after the paragraph before that one.
    """
    handled: dict[str, int] = {}
    for region in REGIONS:
        block = only_block(after, region["starts"])
        index = region["at"] - 1
        handled[block] = index
        original = edits.paragraphs[index]
        text = heading_text(block) if block.startswith("#") else block

        if region["op"] == "list":
            items = [
                re.sub(r"^\s*([-*+]|\d+\.)\s+", "", line)
                for line in block.splitlines()
                if re.match(r"\s*([-*+]|\d+\.)\s", line)
            ]
            style = edit.style_of(original)
            run = [
                offset
                for offset in range(len(items))
                if edit.style_of(edits.paragraphs[index + offset]) == style
            ]
            if len(run) != len(items):
                raise SystemExit(
                    f"{len(items)} list items but {len(run)} paragraphs in {style} at "
                    f"{region['at']}; the list is not laid out as assumed"
                )
            for offset, item in enumerate(items):
                paragraph = edits.paragraphs[index + offset]
                if edit.text_of(paragraph) == plain(item):
                    continue  # this item is unchanged; leave it, and leave it unhighlighted
                patched = edit.rewrite(paragraph, item, pool=edits.pool)
                if patched is None:
                    edits.defer(
                        kind="replace",
                        at=index + offset,
                        reason="the replacement's maths does not line up with the equations there",
                        old=edit.text_of(paragraph),
                        anchor="",
                        new=plain(item),
                        raw=item,
                    )
                    continue
                edits.replace(index + offset, patched, plain(item)[:64])
        elif region["op"] == "replace":
            ppr = edit.PPR.search(original)
            ppr = ppr.group(0) if ppr else "<w:pPr/>"
            if region.get("delist"):
                ppr = denumber(ppr)
            if region.get("style"):
                # Asking for a style means asking for its indentation too: the Family B
                # lead-in kept the checklist's hanging indent and sat further in than the
                # Family A lead-in facing it across the page.
                ppr = re.sub(r"<w:ind [^>]*/>", "", restyle(ppr, region["style"]))
            body = edit.runs_for(
                text,
                edit.base_properties(original),
                edit.MATH.findall(original),
                highlight=True,
                pool=edits.pool,
            )
            if body is None:
                edits.defer(
                    kind="replace",
                    at=index,
                    reason="the replacement's maths does not line up with the equations there",
                    old=edit.text_of(original),
                    anchor="",
                    new=plain(block),
                    raw=block,
                )
                continue
            edits.replace(index, f"<w:p>{ppr}{body}</w:p>", plain(block)[:64])
        else:
            style = region.get("style") or ("MDPI22heading2" if block.startswith("###") else None)
            if style:
                ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
            else:
                found = edit.PPR.search(original)
                ppr = found.group(0) if found else '<w:pPr><w:pStyle w:val="BodyText"/></w:pPr>'
                ppr = denumber(ppr) if numbering_of(original) else ppr
            made = edit.compose(ppr, edit.base_properties(original), text, pool=edits.pool)
            if made is None:
                edits.defer(
                    kind="insert",
                    at=index,
                    reason="the new paragraph contains maths, which has to be typed in Word",
                    old="",
                    anchor=edit.text_of(original),
                    new=plain(block),
                    raw=block,
                )
                continue
            edits.insert(index, made, plain(block)[:56])
    return handled


def apply_references(edits: Edits, before: list[str], after: list[str]) -> dict[str, int]:
    """Append the references the revision adds, letting Word go on numbering them."""
    existing = reference_items("\n".join(before))
    revised = reference_items("\n".join(after))
    last = max(
        index
        for index, paragraph in enumerate(edits.paragraphs)
        if numbering_of(paragraph) == REFERENCE_NUMBERING
    )
    handled = {
        block: last
        for block in after
        if sum(1 for line in block.splitlines() if re.match(r"\d+\.\s", line)) > 5
    }
    added = [item for item in revised if item not in existing]
    if not added:
        return handled
    original = edits.paragraphs[last]
    ppr = edit.PPR.search(original)
    for item in added:
        text = re.sub(r"^\d+\.\s+", "", item)  # Word supplies the number
        made = edit.compose(ppr.group(0), edit.base_properties(original), text, pool=edits.pool)
        if made is None:
            edits.defer(
                kind="insert",
                at=last,
                reason="the new reference contains maths",
                old="",
                anchor=edit.text_of(original),
                new=plain(item),
                raw=item,
            )
            continue
        edits.insert(last, made, plain(text)[:56])
    return handled


def apply_diff(edits: Edits, before: list[str], after: list[str], handled: dict[str, int]) -> None:
    word_texts = [edit.text_of(paragraph) for paragraph in edits.paragraphs]
    mapping = align(before, word_texts)

    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_blocks, new_blocks = before[old_start:old_end], after[new_start:new_end]
        pairing = pair(old_blocks, new_blocks)
        cursor = mapping[old_start - 1] if old_start else None
        for offset, block in enumerate(new_blocks):
            if block in handled:
                cursor = handled[block]  # applied already; later insertions follow it
                continue
            if block.startswith(("|", "!")):
                continue  # tables and figures are unchanged by this revision
            if block.startswith("$$"):
                # A display equation cannot be composed here, and skipping it silently
                # would drop it from the revision without anyone being told.
                edits.defer(
                    kind="insert",
                    at=cursor,
                    reason="a display equation, which has to be set in Word",
                    old="",
                    anchor=word_texts[cursor] if cursor is not None else "",
                    new=block.strip("$").strip(),
                    raw=block,
                )
                continue
            paired = pairing[offset]
            target = mapping[old_start + paired] if paired is not None else None
            if target is not None and target in edits.replacements:
                target = None  # a region already owns it; treat this as an insertion
            reason = None

            if is_multi_item_list(block):
                reason = "a list of several items; each is a separate Word paragraph"
            elif target is not None:
                original = edits.paragraphs[target]
                text = block
                ppr = None
                if block.startswith("#"):
                    text = heading_text(block)
                elif numbering_of(original) == REFERENCE_NUMBERING:
                    text = re.sub(r"^\d+\.\s+", "", block)
                elif numbering_of(original) == CHECKLIST_NUMBERING:
                    found = edit.PPR.search(original)
                    ppr = denumber(found.group(0)) if found else None

                if ppr is not None:
                    body = edit.runs_for(
                        text,
                        edit.base_properties(original),
                        edit.MATH.findall(original),
                        highlight=True,
                        pool=edits.pool,
                    )
                    patched = f"<w:p>{ppr}{body}</w:p>" if body else None
                else:
                    patched = edit.rewrite(original, text, pool=edits.pool)

                if patched is None:
                    reason = "the replacement's maths does not line up with the equations there"
                else:
                    edits.replace(target, patched, plain(block)[:64])
                    cursor = target
            elif cursor is not None:
                anchor = edits.paragraphs[cursor]
                if block.startswith("###"):
                    ppr = '<w:pPr><w:pStyle w:val="MDPI22heading2"/></w:pPr>'
                    text = heading_text(block)
                elif block.startswith("##"):
                    ppr = '<w:pPr><w:pStyle w:val="MDPI21heading1"/></w:pPr>'
                    text = heading_text(block)
                else:
                    found = edit.PPR.search(anchor)
                    ppr = found.group(0) if found else '<w:pPr><w:pStyle w:val="BodyText"/></w:pPr>'
                    ppr = denumber(ppr) if numbering_of(anchor) else ppr
                    ppr = restyle(ppr, "BodyText") if "FirstParagraph" in ppr else ppr
                    text = block

                made = edit.compose(ppr, edit.base_properties(anchor), text, pool=edits.pool)
                if made is None:
                    reason = "the new paragraph contains maths, which has to be typed in Word"
                else:
                    edits.insert(cursor, made, plain(block)[:56])
            else:
                reason = "the paragraph it belongs after could not be located"

            if reason:
                edits.defer(
                    kind="replace" if target is not None else "insert",
                    at=target if target is not None else cursor,
                    reason=reason,
                    old=word_texts[target] if target is not None else "",
                    anchor=word_texts[cursor] if cursor is not None else "",
                    new=plain(block),
                    raw=block,
                )


def write_remaining(deferred: list[dict]) -> None:
    lines = [
        "# What is left to apply by hand",
        "",
        f"Base file: `{OUTPUT.name}`. Everything else in the revision is already in it,",
        "highlighted in yellow. These are the edits that could not be applied by machine,",
        "each because applying it means setting an equation in Word or splitting one",
        "paragraph into several.",
        "",
        "Highlight each one in yellow after applying it, as the others already are.",
        "",
        "---",
        "",
    ]
    for number, item in enumerate(deferred, start=1):
        where = f"paragraph {item['at'] + 1}" if item["at"] is not None else "location unknown"
        lines += [f"## {number}. {item['kind'].upper()} — {where}", "", f"*{item['reason']}*", ""]
        locator = item["old"] or item["anchor"]
        if locator:
            words = locator.split()
            phrase = " ".join(words[3:11]) if len(words) > 12 else " ".join(words[:8])
            lines += [f"**Search for:**  `{phrase}`", ""]
        if item["old"]:
            lines += [
                "**Find this paragraph:**",
                "",
                "> " + item["old"],
                "",
                "**Replace the whole of it with:**",
            ]
        elif item["anchor"]:
            lines += [
                "**Find this paragraph:**",
                "",
                "> " + item["anchor"],
                "",
                "**Insert the following immediately after it, as a new paragraph:**",
            ]
        else:
            lines += ["**Insert this as a new paragraph:**"]
        lines += ["", "> " + item["new"], ""]
        if "$" in item["raw"]:
            maths = ", ".join(f"`{found}`" for found in re.findall(r"\$[^$]+\$", item["raw"]))
            lines += [f"Equations to set in Word: {maths}", ""]
    REMAINING.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    with zipfile.ZipFile(FORMATTED) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    paragraphs = edit.paragraphs_of(document)

    before = blocks(submitted_markdown())
    after = blocks(MANUSCRIPT.read_text(encoding="utf-8"))

    edits = Edits(paragraphs, edit.equation_pool(document))
    handled = apply_regions(edits, after)
    handled.update(apply_references(edits, before, after))
    apply_diff(edits, before, after, handled)

    patched = edit.splice(document, edits.replacements, edits.insertions)
    ElementTree.fromstring(patched)  # a document that does not parse is not written out

    # The five edits this script refuses were afterwards made by hand, in Word, in the file
    # it writes. Running it again would rebuild that file from the editorial office's
    # original and throw them away -- and the loss would be silent, because the result
    # still looks like a correctly patched manuscript.
    if OUTPUT.exists() and "--force" not in sys.argv:
        raise SystemExit(
            f"{OUTPUT.name} already exists and has been edited by hand since it was made.\n"
            "Rebuilding it would discard those edits. Delete it first, or pass --force."
        )

    with zipfile.ZipFile(FORMATTED) as source:
        items = [(item, source.read(item.filename)) for item in source.infolist()]
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as target:
        for item, data in items:
            target.writestr(
                item, patched.encode("utf-8") if item.filename == "word/document.xml" else data
            )

    write_remaining(edits.deferred)
    edits.write_report(HERE / "APPLIED_REPORT.md")

    print(f"{len(edits.applied)} edits applied into the journal's file")
    for line in edits.applied:
        print(f"  {line}")
    print(f"\n{len(edits.deferred)} edits left to apply by hand")
    for item in edits.deferred:
        where = item["at"] + 1 if item["at"] is not None else "?"
        print(f"  paragraph {where}: {item['reason']}")
    print(f"\nwritten: {OUTPUT.name}\nremaining: {REMAINING.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
