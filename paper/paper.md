---
title: 'taskiq-core: closed-form-validated task-based image quality on synthetic phantoms'
tags:
  - Python
  - medical imaging
  - image quality
  - task-based assessment
  - model observers
  - MTF
  - NPS
  - detectability
authors:
  - name: Shuji Yamamoto
    orcid: 0000-0000-0000-0000   # TODO: replace with the author's real ORCID before submission
    affiliation: 1
affiliations:
  - name: Institute of One
    index: 1
date: 16 July 2026
bibliography: paper.bib
---

# Summary

`taskiq-core` is a pure-Python library for **task-based image quality assessment** on
synthetic phantoms. It measures the two physical descriptors of a linear imaging system —
the modulation transfer function (MTF) and the noise power spectrum (NPS) — and the
performance of model observers on a signal-detection task (the detectability index *d′*,
the area under the ROC curve, and the two-alternative-forced-choice percent-correct), all on
the *same* synthetic images and through the *same* pipeline. The intended use is to study how
physical image quality transfers to task performance as acquisition conditions are varied,
without any patient data: every image the library touches is generated analytically from a
seed.

The distinguishing design choice is that **every estimator is validated against a
closed-form analytic answer rather than against a stored snapshot of its own output.** Each
phantom is constructed so that the quantity to be recovered is known exactly — the presampled
MTF of an analytically Gaussian-blurred edge is $\exp(-2\pi^2\sigma^2 f^2)$; the NPS of white
noise is flat at $\sigma^2\,\Delta x\,\Delta y$; the non-prewhitening matched filter's
detectability in white noise is exactly $\lVert s\rVert_2/\sigma$ — and the corresponding
estimator is required to reproduce it. This turns the test suite into a check on correctness,
not merely on stability, and in practice it has repeatedly exposed defects that a
self-consistent regression test would have certified as correct.

An interactive GUI workbench, `taskiq-studio`, is distributed separately and depends on this
library; it lets a user vary parameters and watch each estimate move against its closed-form
reference in real time.

# Statement of need

Task-based assessment — judging an imaging system by how well a specified observer performs a
specified detection or discrimination task, rather than by a generic fidelity metric — is the
accepted framework for evaluating medical imaging systems [@barrett2004; @icru54]. Its
ingredients are individually standardised (the slanted-edge MTF [@iso12233], the DQE and NPS
formalism [@iec62220]) and its theory is mature (ideal and channelized-Hotelling observers,
detectability indices [@myers1987; @barrett2004]). Yet a researcher assembling these pieces
faces two recurring, under-served difficulties.

First, **the estimators are subtle and their errors are quiet.** A slanted-edge MTF routine
that neglects the finite-difference and bin-averaging transfer functions is biased by a few
percent near Nyquist; an NPS routine with a misplaced factor of the pixel area is wrong by a
constant that no internal check will reveal; a prewhitening observer handed a noise spectrum
that decays to zero returns an enormous, entirely spurious *d′*. None of these announce
themselves. They produce plausible numbers, and a test that compares the code to its own
previous output will pass on all of them.

Second, **reproducibility is hard to guarantee when the ground truth is an image.** If the
reference for "is the MTF right?" is a previously computed MTF, the pipeline can only be shown
to be self-consistent, never correct.

`taskiq-core` addresses both by generating phantoms whose analytic ground truth is known and
holding every estimator to it. Because the phantoms are synthetic and deterministic
(`numpy.random.default_rng(seed)` throughout, with bit-for-bit reproducibility asserted in the
test suite), the reference is exact and the whole pipeline is reproducible from a seed. The
library deliberately **fails loudly**: a degenerate configuration raises a `ValueError` with a
specific, actionable message rather than returning a plausible wrong number — because in this
domain a wrong number that looks right is the primary hazard.

The library is aimed at medical-imaging physicists and image-science researchers who need a
transparent, dependency-light, citable reference implementation for teaching, for
methodological experiments on the physical-to-task transfer, and as a validated substrate on
which to build. Its runtime dependencies are limited to `numpy`, `scipy`, `scikit-image`, and
`matplotlib`; it uses no deep learning and stores no patient data.

# Functionality

The library is organised as a short pipeline of pure functions returning frozen dataclasses:

- **`phantoms`** — analytic phantoms: a slanted edge with an exact `erf` blur profile (for
  MTF), a uniform field with white or Gaussian-correlated noise (for NPS), and a low-contrast
  disk formed as the exact 2-D Gaussian convolution of a disk, a non-central $\chi^2$ CDF (the
  detection signal).
- **`physical`** — `mtf_from_edge`, an ESF→LSF→MTF slanted-edge estimator that analytically
  removes the bin-average and central-difference transfer functions and corrects for
  angle-dependent sub-bin sampling; and `nps_2d`, a 2-D and radially averaged NPS normalised so
  that $\iint \mathrm{NPS}\,du\,dv = \sigma^2$ holds as an exact identity.
- **`tasks`** — an SKE/BKE (signal- and background-known-exactly) trial generator that carries
  the *analytic* NPS of the noise it just produced, plus the figures of merit *d′*, AUC (exact,
  via the Mann–Whitney statistic), the ROC curve, and 2AFC percent-correct, tied together by the
  identity $\mathrm{PC} = \mathrm{AUC} = \Phi(d'/\sqrt{2})$.
- **`observers`** — the non-prewhitening matched filter with an optional human "eye" filter
  [@burgess1994], the ideal prewhitening (Hotelling) observer, and the channelized-Hotelling
  observer with Laguerre–Gauss, difference-of-Gaussian, or Gabor channels [@myers1987].

Representative validated results (all from the test suite): the slanted-edge MTF matches the
analytic Gaussian to $\le 0.004\%$ over fifteen blur/angle combinations; the NPS normalisation
identity holds to $\sim 2\times10^{-16}$; the non-prewhitening detectability equals
$\lVert s\rVert_2/\sigma$ to machine precision; and the full pipeline — phantom to analytic NPS
to closed-form *d′* to scored trials to measured *d′* and 2AFC — agrees end to end to $\le 1.3\%$
across eighteen contrast-by-observer experiments.

The closed-form-validation discipline has, during development, exposed six defects that each
returned a plausible but wrong value, including an angle-dependent sub-bin sampling bias in the
MTF (1.4% error), a prewhitening observer producing a *d′* of order $10^{29}$ on a noise model
without a floor, and a "soft-edged" disk whose area — and therefore whose detectable signal
energy — silently depended on its blur. Each is now guarded and regression-tested.

# Reproducibility

Every result and figure in the repository can be regenerated from a clean checkout: the test
suite runs offline and deterministically, and the `examples/` scripts reproduce the figures.
A development log and reproduction guide (`docs/REPRODUCE.md`) records how the software was
built incrementally and how to reproduce each reported number.

# Acknowledgements

The software was developed with the assistance of an AI coding assistant (Anthropic Claude,
via the Claude Code CLI) under human direction; all design decisions, the closed-form
validation strategy, and the review of every increment were carried out by the author. See
`docs/REPRODUCE.md` for details.

# References
