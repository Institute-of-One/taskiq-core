"""Edit paragraphs inside a Word document without rebuilding it.

Rebuilding the manuscript from markdown is what lost the journal's template the first time.
The opposite approach is to leave the document alone and change only the text inside the
paragraphs that the revision touches, so every paragraph style, every native equation and
every table stays exactly where the editorial office put it.

That is possible because a Word paragraph keeps its identity in two places this module
never discards: `<w:pPr>`, which carries the style, and the run properties of its first
run, which carry the font. New text is written as fresh runs that inherit both.

Equations are the hard part, because a native Word equation is an object, not text, and
nothing here can compose one. What it can do is move an existing one. Every equation in the
document is collected into a pool keyed by the symbols it renders, and a maths span in the
replacement is satisfied by an equation from the paragraph itself, or failing that by an
identical equation from anywhere else in the document. A span that matches nothing is
refused, and the edit stays a job for Word. That refusal is the whole safety property: the
alternative to refusing is typing an equation as plain text, which looks like an edit that
worked and is not.

The module knows nothing about this particular revision. It offers paragraph surgery; what
to apply and where is decided in apply_changes.py.
"""

from __future__ import annotations

import re

# The order Word requires of a run-properties element's children. A run-properties element
# whose children are out of this order is schema-invalid, and Word reports the file as
# corrupt rather than ignoring the offending child.
RPR_ORDER = [
    "w:rStyle",
    "w:rFonts",
    "w:b",
    "w:bCs",
    "w:i",
    "w:iCs",
    "w:caps",
    "w:smallCaps",
    "w:strike",
    "w:dstrike",
    "w:outline",
    "w:shadow",
    "w:emboss",
    "w:imprint",
    "w:noProof",
    "w:snapToGrid",
    "w:vanish",
    "w:webHidden",
    "w:color",
    "w:spacing",
    "w:w",
    "w:kern",
    "w:position",
    "w:sz",
    "w:szCs",
    "w:highlight",
    "w:u",
    "w:effect",
    "w:bdr",
    "w:shd",
    "w:fitText",
    "w:vertAlign",
    "w:rtl",
    "w:cs",
    "w:em",
    "w:lang",
    "w:eastAsianLayout",
    "w:specVanish",
    "w:oMath",
]

PARAGRAPH = re.compile(r"<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>", re.S)
MATH = re.compile(r"<m:oMathPara>.*?</m:oMathPara>|<m:oMath>.*?</m:oMath>", re.S)
PPR = re.compile(r"<w:pPr>.*?</w:pPr>", re.S)
RUN = re.compile(r"<w:r(?: [^>]*)?>.*?</w:r>", re.S)
RPR = re.compile(r"<w:rPr>.*?</w:rPr>", re.S)
TEXT = re.compile(r"<w:t(?: [^>]*)?>([^<]*)</w:t>")
SYMBOL = re.compile(r"<m:t(?: [^>]*)?>([^<]*)</m:t>")
BOOKMARK = re.compile(r"<w:bookmark(?:Start|End)[^>]*/>")
ELEMENT = re.compile(r"<(w14?:[A-Za-z]+)(?: [^>]*?)?(?:/>|>.*?</\1>)", re.S)

# A sub- or superscript written as maths -- an affiliation marker, MTF_50 -- is a script,
# not an equation, and Word sets it as one. Both are matched before the general maths.
SEGMENT = re.compile(
    r"\$\^\{(?P<superscript>[^}]+)\}\$"
    r"|\$_\{(?P<subscript>[^}]+)\}\$"
    r"|\*\*(?P<bold>[^*]+)\*\*|\*(?P<italic>[^*]+)\*|`(?P<code>[^`]+)`|\$(?P<math>[^$]+)\$"
)

GREEK = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\Delta": "Δ",
    r"\sigma": "σ",
    r"\Sigma": "Σ",
    r"\pi": "π",
    r"\mu": "μ",
    r"\lambda": "λ",
    r"\theta": "θ",
    r"\phi": "φ",
    r"\omega": "ω",
    r"\times": "×",
    r"\cdot": "·",
    r"\int": "∫",
    r"\in": "∈",
    r"\ldots": "…",
    r"\dots": "…",
    r"\approx": "≈",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\pm": "±",
    r"\infty": "∞",
    r"\sqrt": "√",
}


def text_of(paragraph: str) -> str:
    """The paragraph's visible text, with runs joined and whitespace normalised."""
    return re.sub(r"\s+", " ", "".join(TEXT.findall(paragraph))).strip()


def style_of(paragraph: str) -> str:
    found = re.search(r'<w:pStyle w:val="([^"]+)"', paragraph)
    return found.group(1) if found else ""


def paragraphs_of(document: str) -> list[str]:
    return [match.group(0) for match in PARAGRAPH.finditer(document)]


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def symbols_of(equation: str) -> str:
    """What a native equation renders as, reduced to comparable symbols."""
    return re.sub(r"\s+", "", "".join(SYMBOL.findall(equation)))


def symbols_of_latex(latex: str) -> str:
    """What a maths span would render as, reduced the same way, so the two can be compared."""
    body = latex.strip("$")
    for command, symbol in GREEK.items():
        body = body.replace(command, symbol)
    body = re.sub(r"\\(?:mathrm|mathit|mathbf|text|operatorname)\{([^}]*)\}", r"\1", body)
    body = re.sub(r"[_^]\{([^}]*)\}", r"\1", body)
    body = re.sub(r"[_^]", "", body)
    body = re.sub(r"\\(?:left|right|quad|qquad|,|;|:|!)", "", body)
    # What is left is a named function -- \exp, \log -- which Word renders as its letters,
    # so the backslash goes and the name stays. Deleting it instead loses the "exp" from
    # exp(-2*pi^2*sigma^2*f^2) and the equation stops matching the one already in the file.
    body = re.sub(r"\\([a-zA-Z]+)", r"\1", body)
    return re.sub(r"[\\{}\s,\u2061\u2062\u2063\u200b]", "", body)


def equation_pool(document: str) -> dict[str, str]:
    """Every equation in the document, keyed by what it renders as.

    An equation the revision needs may already be set somewhere else in the manuscript --
    the same symbol introduced in the methods and used again in a caption. Where it is, it
    can be copied rather than composed, which is the difference between an edit that can be
    made here and one that has to be made in Word.
    """
    pool: dict[str, str] = {}
    for equation in MATH.findall(document):
        if equation.startswith("<m:oMathPara>"):
            # A display equation is a paragraph of its own and cannot be dropped into a
            # sentence, but the inline equation inside it can.
            inner = re.search(r"<m:oMath>.*</m:oMath>", equation, re.S)
            if inner:
                pool.setdefault(symbols_of(inner.group(0)), inner.group(0))
            continue
        pool.setdefault(symbols_of(equation), equation)
    return pool


def segments(markdown: str) -> list[tuple[str, str]]:
    """Split markdown into runs of one kind each: plain, bold, italic, code, script, maths."""
    markdown = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", markdown)
    out: list[tuple[str, str]] = []
    position = 0
    for match in SEGMENT.finditer(markdown):
        if match.start() > position:
            out.append(("plain", markdown[position : match.start()]))
        kind = match.lastgroup or "plain"
        out.append((kind, match.group(kind)))
        position = match.end()
    if position < len(markdown):
        out.append(("plain", markdown[position:]))
    return [(kind, re.sub(r"\s+", " ", body)) for kind, body in out if body]


def _children(rpr: str) -> list[tuple[str, str]]:
    inner = re.sub(r"^<w:rPr>|</w:rPr>$", "", rpr)
    return [(match.group(1), match.group(0)) for match in ELEMENT.finditer(inner)]


def run_properties(
    base: str,
    *,
    bold=False,
    italic=False,
    code=False,
    superscript=False,
    subscript=False,
    highlight=False,
) -> str:
    """A run-properties element derived from the paragraph's own, with additions in order."""
    children = _children(base) if base else []
    additions: list[tuple[str, str]] = []
    if bold:
        additions += [("w:b", "<w:b/>"), ("w:bCs", "<w:bCs/>")]
    if italic:
        additions += [("w:i", "<w:i/>"), ("w:iCs", "<w:iCs/>")]
    if code:
        additions += [("w:rFonts", '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>')]
    if superscript:
        additions += [("w:vertAlign", '<w:vertAlign w:val="superscript"/>')]
    if subscript:
        additions += [("w:vertAlign", '<w:vertAlign w:val="subscript"/>')]
    if highlight:
        additions += [("w:highlight", '<w:highlight w:val="yellow"/>')]

    names = {name for name, _ in additions}
    kept = [(name, xml) for name, xml in children if name not in names]
    combined = kept + additions
    combined.sort(key=lambda item: RPR_ORDER.index(item[0]) if item[0] in RPR_ORDER else 999)
    return "<w:rPr>" + "".join(xml for _, xml in combined) + "</w:rPr>" if combined else ""


def base_properties(paragraph: str) -> str:
    """The run properties of the paragraph's first run that actually carries text."""
    for run in RUN.finditer(paragraph):
        if "<w:t" in run.group(0):
            found = RPR.search(run.group(0))
            return found.group(0) if found else ""
    return ""


def runs_for(
    markdown: str,
    base: str,
    maths: list[str],
    *,
    highlight: bool,
    pool: dict[str, str] | None = None,
) -> str | None:
    """Render markdown as Word runs, satisfying its maths from equations that already exist.

    Returns None if any maths span matches no equation, in the paragraph or the document,
    since composing a new one is not something this module attempts.
    """
    pieces = segments(markdown)
    available = {symbols_of(equation): equation for equation in maths}
    out: list[str] = []
    for kind, body in pieces:
        if kind == "math":
            wanted = symbols_of_latex(body)
            equation = available.pop(wanted, None) or (pool or {}).get(wanted)
            if equation is None:
                return None
            out.append(equation)
            continue
        properties = run_properties(
            base,
            bold=kind == "bold",
            italic=kind == "italic",
            code=kind == "code",
            superscript=kind == "superscript",
            subscript=kind == "subscript",
            highlight=highlight,
        )
        out.append(f'<w:r>{properties}<w:t xml:space="preserve">{escape(body)}</w:t></w:r>')
    return "".join(out)


def rewrite(
    paragraph: str, markdown: str, *, highlight: bool = True, pool: dict[str, str] | None = None
) -> str | None:
    """The paragraph with its text replaced, keeping style, equations and bookmarks."""
    if "<m:oMathPara>" in paragraph:
        return None  # a display equation is the paragraph; there is no prose to rewrite
    ppr = PPR.search(paragraph)
    body = runs_for(
        markdown,
        base_properties(paragraph),
        MATH.findall(paragraph),
        highlight=highlight,
        pool=pool,
    )
    if body is None:
        return None
    opening = re.match(r"<w:p(?: [^>]*)?>", paragraph).group(0)
    bookmarks = "".join(BOOKMARK.findall(paragraph))
    return opening + (ppr.group(0) if ppr else "") + bookmarks + body + "</w:p>"


def compose(
    ppr: str,
    base: str,
    markdown: str,
    *,
    highlight: bool = True,
    pool: dict[str, str] | None = None,
) -> str | None:
    """A new paragraph in the given style. Refused if its maths is nowhere in the document."""
    body = runs_for(markdown, base, [], highlight=highlight, pool=pool)
    return None if body is None else "<w:p>" + ppr + body + "</w:p>"


def splice(document: str, replacements: dict[int, str], insertions: dict[int, list[str]]) -> str:
    """Rebuild document.xml with paragraphs replaced and inserted, everything else verbatim."""
    out, position, index = [], 0, 0
    for match in PARAGRAPH.finditer(document):
        out.append(document[position : match.start()])
        out.append(replacements.get(index, match.group(0)))
        out.extend(insertions.get(index, []))
        position, index = match.end(), index + 1
    out.append(document[position:])
    return "".join(out)
