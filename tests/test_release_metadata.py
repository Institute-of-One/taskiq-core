"""The release metadata must agree with itself and with the manuscript.

A reader of the published article follows two things: a repository URL and an archived
DOI. If `pyproject.toml`, `CITATION.cff`, `.zenodo.json`, the package `__version__` and
the manuscript disagree about which version was archived, the citation the reader follows
is the one that is wrong, and nothing about the paper reveals it.

The DOI checks are the ones this programme has actually needed. Zenodo mints two DOIs per
software record: a concept DOI that follows whichever release is newest, and a version DOI
that is frozen to one snapshot. They differ by a digit or two in the middle of a long
number, the badge in a README shows the concept DOI, and a paper that cites it hands a
reader code that is not the code its results came from. That substitution reached print in
nineteen files across this programme before anyone noticed. Here the manuscript labels
both DOIs explicitly, which is the right thing to do and also the thing that silently
breaks the first time either number is edited by hand.

`CITATION.cff` is the authority for which DOI is which: it is the machine-readable record
a citation manager reads, and its descriptions say so in words.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

try:  # tomllib is standard-library from Python 3.11; fall back on 3.10.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised only on Python 3.10
    import tomli as tomllib

from taskiq_core import __version__

REPO = Path(__file__).resolve().parents[1]
PYPROJECT = REPO / "pyproject.toml"
CITATION = REPO / "CITATION.cff"
ZENODO = REPO / ".zenodo.json"
MANUSCRIPT = REPO / "paper" / "manuscript.md"

#: The organisation the manuscript points a reader at. A second one in the text means one
#: of the two citations is dead.
REPO_URL = "https://github.com/Institute-of-One/taskiq-core"

DOI = re.compile(r"10\.5281/zenodo\.\d+")


@pytest.fixture(scope="module")
def pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _cff() -> dict:
    yaml = pytest.importorskip("yaml", reason="pyyaml not installed")
    return yaml.safe_load(CITATION.read_text(encoding="utf-8"))


def _doi_labelled(description: str) -> str:
    """The DOI whose CITATION.cff description opens with the given word."""
    for identifier in _cff()["identifiers"]:
        if identifier["type"] == "doi" and identifier["description"].lower().startswith(
            description
        ):
            return str(identifier["value"])
    raise AssertionError(f"CITATION.cff declares no DOI described as {description!r}")


@pytest.fixture(scope="module")
def manuscript() -> str:
    if not MANUSCRIPT.exists():
        pytest.skip("paper/manuscript.md not present")
    return MANUSCRIPT.read_text(encoding="utf-8")


def test_the_version_is_the_same_everywhere(pyproject: dict) -> None:
    assert pyproject["project"]["version"] == __version__
    assert json.loads(ZENODO.read_text(encoding="utf-8"))["version"] == __version__
    assert str(_cff()["version"]) == __version__


def test_the_two_zenodo_dois_are_different_records() -> None:
    """A concept and a version DOI that are equal means one of the labels is wrong."""
    assert _doi_labelled("concept") != _doi_labelled("version")


def test_the_manuscript_binds_each_doi_to_the_label_it_belongs_to(manuscript: str) -> None:
    """Naming both DOIs is right; naming them the wrong way round is worse than one.

    A reader who is told a number is the frozen snapshot, and follows it to whatever
    was released last, has been misled more precisely than by a paper that gave only
    the concept DOI and left the ambiguity visible.
    """
    expected = {"version": _doi_labelled("version"), "concept": _doi_labelled("concept")}
    for label, doi in expected.items():
        found = False
        for phrase in re.finditer(rf"{label} DOI", manuscript, flags=re.IGNORECASE):
            line_end = manuscript.find("\n", phrase.end())
            after = manuscript[phrase.end() : line_end if line_end != -1 else None]
            match = DOI.search(after)
            assert match, f"the manuscript says {label!r} DOI but names no DOI on that line"
            assert match.group(0) == doi, (
                f"the manuscript calls {match.group(0)} the {label} DOI; CITATION.cff "
                f"records the {label} DOI as {doi}"
            )
            found = True
        assert found, f"the manuscript never names the {label} DOI"


def test_the_manuscript_names_the_version_the_archive_holds(manuscript: str) -> None:
    """A manuscript promising the archived snapshot must say which snapshot."""
    assert f"v{__version__}" in manuscript, (
        f"the manuscript cites an archive without naming v{__version__}, the version "
        f"every other declaration in this repository agrees on"
    )


def test_every_declared_url_points_at_the_repository_the_manuscript_cites(
    pyproject: dict, manuscript: str
) -> None:
    for value in pyproject["project"]["urls"].values():
        assert value.startswith(REPO_URL), f"{value} is not under {REPO_URL}"
    assert _cff()["repository-code"] == REPO_URL
    assert REPO_URL in manuscript


def test_the_manuscript_names_no_other_github_organisation(manuscript: str) -> None:
    organisations = set(re.findall(r"github\.com/([A-Za-z0-9_.-]+)", manuscript))
    assert organisations == {"Institute-of-One"}, (
        f"unexpected GitHub organisations: {organisations}"
    )


def test_the_licence_is_mit_in_every_declaration(pyproject: dict) -> None:
    licence = pyproject["project"]["license"]
    assert (licence if isinstance(licence, str) else licence["text"]) == "MIT"
    assert _cff()["license"] == "MIT"
    assert json.loads(ZENODO.read_text(encoding="utf-8"))["license"] == "MIT"
