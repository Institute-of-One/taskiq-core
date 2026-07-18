# Contributing to taskiq-core

Thank you for your interest. This is a research kernel meant to be **citable and
reproducible**, so the contribution bar is less about volume of code and more
about keeping the guarantees below intact. Please read this before opening a pull
request.

## Development setup

Python 3.10 or newer.

```bash
git clone https://github.com/Institute-of-One/taskiq-core
cd taskiq-core
python -m pip install -e ".[dev]"
python -m pytest          # expect the whole suite to pass
```

Everything the tests need is generated from a seed, so the suite runs fully
offline and deterministically — there are no external reference data to fetch.

## The five guarantees

Every change must preserve these. They are what make the project trustworthy.

1. **Pure, minimal dependencies.** Runtime code imports only `numpy`, `scipy`,
   `scikit-image` and `matplotlib`. `pandas` is an optional extra used only by
   `AtlasTable.to_dataframe`, never on the core path. No deep-learning frameworks,
   no DICOM toolkits.
2. **Validated against closed forms, not against itself.** Where an analytic ground
   truth exists — the MTF of a Gaussian-blurred edge `exp(-2π²σ²f²)`, the identity
   `∫ NPS = σ²`, the `NEQ = MTF²/NPS` closed form, the ideal-observer `d'² = ∬ NEQ|S|² df`
   bridge — the estimator is checked against *that*, to machine precision, rather than
   against a stored snapshot of its own output. New estimators need a matching
   analytic test.
3. **Determinism.** Every stochastic function takes a `seed` and, given the same
   inputs, produces the same result across runs within a pinned environment. Do not
   use unseeded randomness.
4. **No silent failure.** A degenerate or undefined result raises a specific,
   messageful `ValueError` — never a silent `nan`. A refused sweep cell is recorded
   as a gap with its reason, not repaired. If `1/NPS` would divide by zero, say so.
5. **No patient data, ever.** No DICOM, no scans, nothing derived from a human
   subject. Everything is synthetic and generated from a seed.

## Code style

The house style follows the existing modules:

- Return results as frozen `@dataclass` objects with typed fields.
- Pure functions, type hints, and a docstring on every public function giving its
  parameters, returns, and the exceptions it raises.
- Images are indexed `(y, x)`; `spacing` is the pixel pitch in millimetres;
  frequencies are in cycles/mm.
- Keep comments about *why*, not *what*; match the surrounding density.

Run the linters and type-checker before submitting — CI runs exactly these:

```bash
ruff check .
ruff format --check .
mypy taskiq_core
```

## Pull requests

- One focused change per PR; keep the diff reviewable.
- All tests green, linters and `mypy` clean.
- Update `CHANGELOG.md` under `Unreleased`.
- Describe *what physical or mathematical fact* your change relies on, and how you
  verified it (closed-form reference, analytic case, or a Monte-Carlo cross-check
  against the closed form).

## Licence of contributions

Code contributions are licensed under the [MIT License](LICENSE); documentation
and figures under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). By
contributing you agree your work is released under these terms.
