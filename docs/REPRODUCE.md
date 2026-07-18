# Development log & reproduction guide

This document records **how `taskiq-core` (and its companion GUI, `taskiq-studio`) were
built** and **how to reproduce every number and figure** from a clean checkout. It has two
audiences: someone who wants to re-run the software and confirm the results, and someone who
wants to understand — or repeat — the AI-assisted, increment-by-increment process that
produced it.

---

## 1. How it was built

The software was written with an AI coding assistant (Anthropic **Claude**, via the **Claude
Code** CLI) under human direction. The human author set the goal, the design constraints, and
the increment boundaries; reviewed each increment before authorising the next; and made every
design decision. The assistant wrote code, tests, and figures, and — importantly — was
directed to **probe each estimator's accuracy empirically before fixing any test tolerance**,
so that the tests document real accuracy rather than being tuned to pass.

Nothing about the results depends on that process: the code is ordinary Python and the tests
are ordinary `pytest`. The process is recorded here for transparency and because the
increment structure is a useful map of the codebase.

### The governing brief

Every increment was held to the same rules, set out at the start:

1. **Pure Python**, runtime dependencies limited to `numpy`, `scipy`, `scikit-image`,
   `matplotlib` (optionally `pandas`). No deep learning. No DICOM or patient data anywhere in
   the repository — all images are synthetic.
2. **Deterministic**: generators take a `seed`; the same seed yields bit-identical output. No
   silent failure — degenerate input raises an explicit error rather than returning NaN or a
   plausible wrong number.
3. **Closed-form validation first.** Every estimator ships with a `pytest` that checks it
   against an *analytic* ground truth, not against a snapshot of its own output.
4. MIT licence, Python ≥ 3.10, `dataclass` results, type hints, docstrings, pure functions,
   no global state.

### The increments

| Increment | Module(s) | What was added | Closed-form checks |
|---|---|---|---|
| **1** | `phantoms`, `physical` | Edge/uniform/disk phantoms; slanted-edge MTF; 2-D & radial NPS | MTF vs `exp(-2π²σ²f²)`; NPS flat at `σ²ΔxΔy`; `∫NPS = σ²` |
| **2** | `observers` | NPWE (± eye filter), ideal prewhitening observer, CHO; channels | NPW white-noise `d′ = ‖s‖/σ`; closed form vs Monte Carlo; CHO vs `(Us)ᵀ(σ²UUᵀ)⁻¹(Us)` |
| **3** | `tasks` | SKE/BKE trials carrying analytic NPS; `d′`, AUC, ROC, 2AFC | `PC = AUC = Φ(d′/√2)`; end-to-end predicted vs measured `d′` |
| **GUI** | `taskiq-studio` | Tk workbench: Physical / Detection / Sweep tabs | every panel shows estimate vs closed form; live-verified |
| **split** | — | Two repositories; paper; this document | — |

`atlas` (NEQ, condition sweeps, physical→task regression) is a documented stub, planned as
increment 4.

### Bugs the closed-form discipline caught

Each of these returned a *plausible* value and would have passed a self-consistent regression
test. All are now guarded and regression-tested. They are the clearest evidence for why the
method was worth the effort.

1. **ESF bin-position jitter (MTF).** The mean sample position inside an ESF bin is not the
   bin centre; the offset depends on the edge angle. Treating the bin average as a centre
   sample biased the MTF by **1.4 %** at some angles. Fixed by a first-order shift to the bin
   centre → error `< 0.01 %`.
2. **Estimator transfer functions (MTF).** The bin boxcar (`sinc(f·h)`) and the central
   difference (`sinc(2f·h)`) each bias the MTF; both are divided out analytically.
3. **Area-gaining soft disk (signal).** A radial `erf` "soft edge" adds `πσ²` of area, so the
   signal energy — and hence `d′` — silently depended on the blur. Replaced with the exact 2-D
   Gaussian-blurred disk (a non-central χ² CDF), which conserves area.
4. **Noise-biased angle estimator.** A rectified-gradient centroid reported a 5° edge as 0.6°
   at 2 % noise. Replaced with a first-moment (area) estimator that is linear in the pixels, so
   noise adds variance but no bias.
5. **Prewhitening on a decaying NPS.** `1/NPS` weighting makes the least-noisy frequencies
   dominate, so a Gaussian-correlated NPS gives the ideal observer a `d′ ≈ 10²⁹` built from
   numerical underflow. `ideal_linear` now refuses an NPS whose dynamic range is unphysical and
   asks for a noise floor.
6. **Detrended-DC NPS inflates `d′`.** A measured NPS has `NPS(0) = 0` (detrending), which
   contributes no noise variance and inflates a plain NPW `d′` by ~3 %. Guarded; an eye filter
   (with `E(0)=0`) is exempt.
7. **Non-orthonormal Laguerre–Gauss channels.** At the default width, channel 5 kept only 81 %
   of its norm — the "orthonormal" set was truncated by the image edge. Now checked via the
   discrete Gram matrix.

(One further correction was to the project's own documentation: an early claim that the
all-pairs 2AFC estimator has standard error `∝ 1/√(nₚn_a)` was wrong — the pairs are not
independent — and was corrected to `O(1/√n)`.)

A defect found only by **running the GUI and looking**, not by the tests: observer scores live
on wildly different absolute scales, so the studio's score-distribution panel collapsed into
invisible spikes. Fixed by standardising each observer's scores to its own (absent-mean,
pooled-SD), so the axis reads directly in units of `d′`.

---

## 2. Environment used

- **OS:** Windows 11 (development); the code is OS-independent.
- **Python:** 3.14 was used; the package requires ≥ 3.10.
- **Libraries at development time:** numpy 2.5, scipy 1.17, scikit-image 0.26, matplotlib 3.10.
  The pinned lower bounds are in `pyproject.toml` / `requirements.txt`.
- **GUI:** `tkinter` (standard library; Tk 8.6).

Exact library versions are not required to reproduce the results — the checks are analytic and
deterministic — but they are recorded here for completeness.

---

## 3. Reproducing the results

### taskiq-core

```bash
git clone https://github.com/Institute-of-One/taskiq-core
cd taskiq-core
python -m pip install -e .

# 161 tests, all offline and deterministic. This is the reproduction:
python -m pytest -q

# Regenerate the three figures (into examples/output/):
python examples/overview.py     # phantoms + MTF/NPS vs analytic truth
python examples/observers.py    # observers, closed form vs Monte Carlo
python examples/detection.py    # SKE/BKE task: predicted vs measured d', ROC, PC
```

Each `examples/*.py` script prints the key agreement numbers to stdout (e.g. the worst
predicted-vs-measured `d′` disagreement) as it runs, so the reported figures can be checked
without opening the PNGs.

### taskiq-studio (the GUI)

The GUI is a **separate repository** that depends on this one:

```bash
git clone https://github.com/Institute-of-One/taskiq-studio
cd taskiq-studio
python -m pip install -e ../taskiq-core      # the dependency, first
python -m pip install -e .

python -m pytest -q                          # 16 tests (compute layer, headless)
taskiq-studio                                # or: python -m taskiq_studio
```

The studio's compute layer is deliberately Tk-free so that every number it displays is tested
headlessly; the test suite also builds the real window and pumps the event loop as a smoke
test (skipped automatically where there is no display).

### Determinism check

Reproducibility is asserted inside the suite (`tests/test_determinism.py`): the same seed
yields byte-identical phantoms and byte-identical estimated MTF/NPS. To see it directly:

```python
from taskiq_core import make_uniform_phantom
a = make_uniform_phantom(64, noise_sd=20.0, seed=0, n_realizations=8)
b = make_uniform_phantom(64, noise_sd=20.0, seed=0, n_realizations=8)
assert a.image.tobytes() == b.image.tobytes()
```

---

## 4. Repeating the AI-assisted build

To rebuild something like this with an AI coding assistant, the parts that mattered were:

1. **State the closed-form-validation rule up front**, as a hard constraint: every estimator
   must ship with a test against an analytic truth, and phantoms must be constructed to *have*
   an analytic truth (an `erf` edge, white noise, a χ² disk) rather than a numerically
   convolved approximation.
2. **Probe accuracy empirically before setting tolerances.** Have the assistant write a
   throwaway script that measures the estimator's error across a parameter grid, read the
   numbers, and only then choose the test tolerance. This is what turns "the test passes" into
   "the estimator is accurate to X".
3. **Work in reviewable increments** and stop at each boundary to report what was built, the
   agreement with analytic truth as concrete numbers, and how to run it.
4. **Insist on loud failure.** A degenerate configuration must raise with an actionable
   message; the GUI then surfaces that message rather than hiding it.
5. **For anything visual, verify by running it**, not only by testing — one display bug here
   was invisible to a passing test suite.

The increment structure in §1 doubles as a script for this: each row is one review cycle.
