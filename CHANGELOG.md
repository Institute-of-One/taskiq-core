# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

No tagged release has been published yet; the versions below are development
milestones. The first public release will coincide with the first Zenodo
deposition.

## [Unreleased]

### Added
- Continuous integration (GitHub Actions): a `ruff` lint + format and `mypy` job,
  and a `pytest` matrix across Python 3.10, 3.11 and 3.12.
- Author ORCID (`0000-0001-9211-1071`) in `CITATION.cff` (URL form) and
  `.zenodo.json` (16-digit form), and this `CHANGELOG.md` and `CONTRIBUTING.md`.

### Changed
- Tooling configuration in `pyproject.toml`: `ruff` (line length 100, docstring and
  import rules) and `mypy` (strict, analysed against 3.12). `filterwarnings` now
  promotes only the project's own `DeprecationWarning`s to errors and ignores those
  raised inside the scientific stack (numpy / scipy / scikit-image / pandas /
  matplotlib), whose release cadence the project does not control.

### Fixed
- `test_atlas.py` tolerances now reflect the phantom generator's actual numerical
  precision (~1e-7 relative): the "d' is linear in contrast" identities are checked
  at `rtol=1e-6` rather than a bit-exact `1e-9`, the NEQ DC-limit check samples the
  true `f=0` bin, and the measured-input NEQ tracking test respects the lower bound of
  the NPS frequency axis rather than requesting an extrapolation.

## [0.4.0] — 2026-07-16

The atlas: the module the project is *for* — physics and task, side by side.

### Added
- `taskiq_core/atlas.py`:
  - `neq()` — noise-equivalent quanta, `MTF² / NPS`, on a common frequency axis, from
    `MTFResult`/`NPSResult` objects, callables, scalars or `(2, N)` arrays; refuses to
    extrapolate and refuses a zero/negative NPS unless given a floor.
  - `sweep()` — sweeps one or more acquisition conditions (contrast, radius, blur,
    dose/noise, noise correlation, noise floor) and records the paired physical
    (`mtf50`, `nps0`, `neq_peak`, `neq_integral`) and task (`d'`, PC, efficiency, and
    optional Monte-Carlo `d'`) metrics per cell in an `AtlasTable`; a refused cell is
    recorded as `nan` with a named reason rather than repaired.
  - `fit_transfer()` — ordinary-least-squares regression of a task metric on physical
    predictor(s), with `R²` and residuals, dropping refused (NaN) cells.
- `tests/test_atlas.py`: the NEQ closed form, the physical→task bridge identity to
  machine precision, and the exact `contrast²` / dose transfer laws.

## [0.3.0] — 2026-07-14

Initial open-core: the physical descriptors, the task, and the model observers.

### Added
- `taskiq_core/phantoms.py`: deterministic synthetic images — a slanted edge for MTF,
  a uniform field plus noise for NPS, and a disk signal for the detection task — each
  validated against its closed form (the erf edge profile, the white-field variance,
  the disk area).
- `taskiq_core/physical.py`: `mtf_from_edge` (slanted-edge MTF), `nps_2d` (2-D and
  radial NPS), and `gaussian_mtf`.
- `taskiq_core/tasks.py`: SKE/BKE trial generation, `d'`, AUC, ROC and 2AFC.
- `taskiq_core/observers.py`: model observers — NPWE, the ideal linear (prewhitening)
  observer, and the channelized Hotelling observer, with channel sets.
- Repository scaffold: packaging, licence (MIT), `README.md`, `CITATION.cff`,
  `.zenodo.json`, examples and a full test suite.

[Unreleased]: https://github.com/Institute-of-One/taskiq-core/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Institute-of-One/taskiq-core/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Institute-of-One/taskiq-core/releases/tag/v0.3.0
