---
title: "An Open, Closed-Form-Validated Framework for Task-Based Image Quality on Synthetic Phantoms: from MTF and NPS to Model-Observer Detectability through NEQ"
author:
  - Shuji Yamamoto, PhD
date: "Preprint --- 2026-07-18"
abstract: |
  Task-based assessment evaluates an imaging system by how well a specified observer performs a specified detection task, and its ingredients — the modulation transfer function (MTF), the noise power spectrum (NPS), the noise-equivalent quanta (NEQ), and model observers — are individually standardised and theoretically mature. Assembling them correctly is nonetheless error-prone: the estimators are subtle and their mistakes are quiet, producing plausible but wrong numbers that a self-consistent regression test will certify as correct. We present taskiq-core, an open, pure-Python framework that measures physical image quality (MTF, NPS, NEQ) and task performance (model-observer detectability d' and the area under the ROC curve) on the same synthetic phantoms, through one pipeline, and quantifies how the physical metrics transfer to task performance as acquisition conditions are swept. The distinguishing design choice is that every estimator is held to a closed-form analytic answer rather than to a snapshot of its own output: the slanted-edge MTF is required to reproduce exp(-2 pi^2 sigma^2 f^2) for an analytically Gaussian-blurred edge (matched to 0.004% over fifteen blur-by-angle combinations); the NPS normalisation satisfies the exact identity that its integral over the frequency plane equals the pixel variance; and the ideal-observer detectability computed from NEQ against an object's power spectrum, d'^2 = integral of NEQ times |S_obj|^2, agrees with the independently implemented prewhitening observer to floating-point precision (relative error 4.4e-16 across nine conditions). On a swept dataset the framework recovers the exact transfer laws that theory fixes — d'^2 is linear in contrast^2 and in inverse noise variance (coefficient of determination 1.000 in each) — and the efficiency of a non-prewhitening eye-filter observer relative to the ideal observer is constant in contrast to nine significant figures. All data are synthetic and generated analytically; the code (185 tests, continuous integration on Python 3.10-3.12) is released under the MIT licence and archived on Zenodo. The contribution is a transparent, patient-data-free, citable reference implementation of the physical-to-task chain, in which the physics-to-task identity is made exact rather than approximate.
keywords: "task-based image quality; model observer; MTF; NPS; NEQ; detectability; synthetic phantom; reproducible research; open source"
geometry: margin=1in
fontsize: 11pt
linkcolor: blue
urlcolor: blue
colorlinks: true
papersize: a4
---

**Author affiliation.** Shuji Yamamoto, PhD — Institute of One, LISIT Co., Ltd., Tokyo, Japan.

**Corresponding author.** Shuji Yamamoto — yamamoto@lisit.jp · ORCID [0000-0001-9211-1071](https://orcid.org/0000-0001-9211-1071).

**Software.** `taskiq-core` v0.4.0 (MIT). Code: <https://github.com/Institute-of-One/taskiq-core>. Archive DOI: [10.5281/zenodo.21422924](https://doi.org/10.5281/zenodo.21422924) (all versions).

---

## 1. Background and Motivation

Task-based assessment — judging an imaging system by how well a specified observer performs a specified detection or discrimination task, rather than by a generic fidelity metric — is the accepted framework for evaluating medical imaging systems [1,2]. Its physical ingredients are individually standardised: the modulation transfer function (MTF) measured from a slanted edge [3], and the noise power spectrum (NPS) and detective-quantum-efficiency formalism [4]. Its observer theory is mature: the ideal (prewhitening) observer, channelized-Hotelling observers, and the detectability index d' that summarises task performance [1,5]. The quantity that ties the physics to the task is the noise-equivalent quanta, NEQ = MTF^2 / NPS, because the ideal-observer detectability of a known signal imaged through a linear system is exactly an integral of NEQ against the signal's power spectrum.

A researcher assembling these pieces faces two recurring, under-served difficulties. First, **the estimators are subtle and their errors are quiet.** A slanted-edge MTF routine that neglects the finite-difference and bin-averaging transfer functions is biased by a few percent near Nyquist; an NPS routine with a misplaced factor of the pixel area is wrong by a constant that no internal check reveals; a prewhitening observer handed a noise spectrum that decays to zero returns an enormous, entirely spurious d'. None of these announce themselves — they produce plausible numbers, and a test that compares the code to its own previous output passes on all of them. Second, **reproducibility is hard to guarantee when the ground truth is an image.** If the reference for "is the MTF right?" is a previously computed MTF, the pipeline can only be shown to be self-consistent, never correct.

**Contribution.** We provide (a) an open, deterministic framework that measures MTF, NPS, and NEQ and evaluates model observers on a detection task, all on the same synthetic phantoms and through one pipeline; (b) a validation discipline in which every estimator is held to a closed-form analytic answer, so the test suite checks correctness rather than mere stability; and (c) a demonstration that, on synthetic data with known truth, the physics-to-task chain — NEQ predicting ideal-observer detectability, and detectability following the exact contrast and dose laws — holds to floating-point precision, making the central claim of task-based assessment exact rather than approximate. Because nothing derives from a human subject, the whole study is shareable and, for a fixed software environment, reproducible from a seed.

## 2. Methods

### 2.1 Synthetic phantoms

Three analytic phantoms are generated, each constructed so that the quantity to be recovered is known in closed form. A **slanted edge** is the exact error-function profile of an analytically Gaussian-blurred step, so its presampled MTF is exactly exp(-2 pi^2 sigma^2 f^2). A **uniform field** carries additive white or Gaussian-correlated noise, so its NPS is known analytically (flat at sigma^2 dx dy for white noise). A low-contrast **disk signal** is formed as the exact two-dimensional Gaussian convolution of a disk — a non-central chi-squared cumulative distribution — so that its energy, and therefore its detectable signal, does not silently depend on the blur applied to it. Every generator takes a seed and, within a fixed software environment, returns the same array.

### 2.2 Physical metrics

`mtf_from_edge` estimates the MTF by the slanted-edge method: it forms the edge-spread function, differentiates to the line-spread function, and transforms, analytically dividing out the bin-average (a boxcar, sinc(f h)) and central-difference (sinc(2 f h)) transfer functions the estimator itself introduces, and correcting each edge-profile bin from its measured mean sample position to the bin centre — an angle-dependent correction without which the estimate is biased by more than one percent at some angles. `nps_2d` estimates the two-dimensional and radially averaged NPS from an ensemble of noise realisations, detrending each region and normalising so that the integral of the NPS over the frequency plane equals the pixel variance as an exact identity.

### 2.3 Model observers and the detection task

A signal-known-exactly / background-known-exactly (SKE/BKE) trial generator produces signal-present and signal-absent images and carries the *analytic* NPS of the noise it just produced. Three model observers are provided: the non-prewhitening matched filter with an optional human eye filter [6]; the ideal prewhitening (Hotelling) observer, whose template is the signal weighted by the inverse noise spectrum; and the channelized-Hotelling observer with Laguerre-Gauss, difference-of-Gaussian, or Gabor channels [5]. Task performance is summarised by the detectability index d', the area under the ROC curve (computed exactly via the Mann-Whitney statistic), and the two-alternative-forced-choice percent-correct, which are tied together by the identity PC = AUC = Phi(d'/sqrt 2).

### 2.4 NEQ and the physical-to-task bridge

The noise-equivalent quanta, NEQ(f) = MTF^2(f) / NPS(f), is computed on a common frequency axis; it is not a third independent metric but exactly the combination of MTF and NPS that governs ideal-observer detectability. For an ideal observer detecting an object signal s_obj imaged through a system of transfer MTF in noise of spectrum NPS,

    d'^2_ideal = integral of |MTF(f) S_obj(f)|^2 / NPS(f) df
               = integral of NEQ(f) |S_obj(f)|^2 df,

so NEQ is the bridge from physics to task. Because 1/NPS is meaningless where the noise power decays to nothing, the implementation refuses (raises) rather than returning a spurious number when the NPS dynamic range is unphysical, unless the caller supplies a floor.

### 2.5 Condition sweep and the transfer

A sweep takes a base configuration and a grid of one or more acquisition conditions (signal contrast, disk radius, system blur, dose/noise level, noise correlation, noise floor) and, for every combination, records the physical summaries (the MTF-50 frequency, the low-frequency NPS, and the peak and integral of NEQ) and the model-observer detectabilities in one table. A cell whose configuration an observer refuses is recorded with its reason rather than repaired. An ordinary-least-squares routine then regresses a task metric on physical predictor(s) and reports the fit and its coefficient of determination, quantifying how strongly, and how linearly, the physics predicts the task.

## 3. Implementation and Scope

The software is pure Python (numpy, scipy, scikit-image, matplotlib; an optional pandas export) and is deterministic within a pinned software environment for a fixed seed. It is covered by 185 automated tests; continuous-integration tests verify numerical outputs against predefined tolerances across Python 3.10-3.12, and the suite runs fully offline because every input is generated from a seed. It is released under the MIT licence (text and figures under CC BY 4.0) and archived on Zenodo. A separate interactive desktop workbench (`taskiq-studio`) depends on this library and lets a user vary parameters and watch each estimate move against its closed-form reference. This preprint reports the open core and its reproducible synthetic benchmarks; no clinical or real-data validation is claimed.

## 4. Validation and Results

### 4.1 Physical estimators against their closed forms

The slanted-edge MTF matched the analytic Gaussian to a maximum relative error of **0.004%** across fifteen blur-by-angle combinations (blur standard deviations 0.15-0.35 mm, edge angles 3-15 degrees), compared where the MTF carries signal (Figure 1, left). For white noise of standard deviation 20 units at 0.1 mm pixel pitch, the radially averaged NPS is flat at its analytic level, and integrating the estimated two-dimensional NPS over the frequency plane recovers the input variance to **0.03%** over 128 realisations — a sampling error, not a bias (Figure 1, right); the estimator's normalisation identity itself (that this integral equals the sample variance) holds to floating-point precision by construction and is asserted to about 2e-16 in the test suite.

![**Figure 1.** Physical estimators held to their closed forms. Left: the slanted-edge MTF estimate (points) against the analytic Gaussian exp(-2 pi^2 sigma^2 f^2) (line) for an edge of blur 0.2 mm. Right: the radially averaged NPS estimate (points) against the analytic white level sigma^2 dx dy (line) for noise of standard deviation 20 units.](figures/fig1_physical.png)

### 4.2 The physical-to-task bridge

The central identity — that NEQ determines ideal-observer detectability — was tested by computing d'^2 two independent ways for a disk signal imaged through a Gaussian system: (A) from the independently validated prewhitening observer applied to the imaged signal, and (B) by integrating NEQ = MTF^2/NPS against the *object* signal's power spectrum. Across nine conditions (contrast 3, 6, 9; system blur 0.10, 0.15, 0.20 mm) the two routes agreed to a maximum relative error of **4.4e-16** — floating-point precision (Figure 2). This is the claim of task-based assessment made exact: on synthetic data with known truth, the physics (NEQ) determines the task (d') not approximately but to the last bit.

![**Figure 2.** The physical-to-task bridge. Left: the NEQ = MTF^2/NPS of the system. Right: d'^2 computed from the ideal observer (horizontal) against d'^2 computed by integrating NEQ against the object power spectrum (vertical), for nine contrast-by-blur conditions; the points lie on the identity line to floating-point precision.](figures/fig2_bridge.png)

### 4.3 The transfer laws

On swept data the framework recovers the transfer laws that theory fixes exactly. Ideal-observer d'^2 is exactly proportional to contrast^2, so a fit of d'^2 on contrast^2 through the origin returned a coefficient of determination of **1.000** (Figure 3, left); it is exactly proportional to inverse noise variance (the dose law), and a fit of d'^2 on 1/sigma^2 likewise returned **1.000** (Figure 3, right). The efficiency of the non-prewhitening eye-filter observer relative to the ideal observer, (d'/d'_ideal)^2, was constant across contrast to nine significant figures (spread 3.4e-9), as it must be for two linear observers, confirming that the sweep and regression carry the exactness of the underlying identities rather than blurring it.

![**Figure 3.** The transfer laws recovered from swept data. Left: ideal-observer d'^2 against contrast^2, with the through-origin fit (coefficient of determination 1.000). Right: ideal-observer d'^2 against inverse noise variance 1/sigma^2, with the through-origin fit (coefficient of determination 1.000).](figures/fig3_transfer.png)

### 4.4 Defects surfaced by closed-form validation

The discipline of validating against a closed form, rather than against the code's own past output, repeatedly exposed defects that each returned a plausible but wrong value and that a self-consistent regression test would have certified as correct. Three examples: an angle-dependent sub-bin sampling bias in the slanted-edge MTF, which biased the estimate by 1.4% at some edge angles and not others until each bin was corrected from its measured mean position to the bin centre; a prewhitening observer that returned a d' of order 1e29 on a Gaussian-correlated noise model whose power decays below floating-point underflow, assembled entirely from bins where the "signal" was rounding noise — now refused unless the noise model has a floor; and a soft-edged disk that, when its blur was applied as the one-dimensional edge profile radially, gained pi sigma^2 of area, so that the detectable signal energy silently depended on the blur — corrected by using the exact two-dimensional blurred disk. Each is now guarded and regression-tested. These are recorded because they illustrate the general hazard the framework is built to address: in this domain a wrong number that looks right is the primary risk.

## 5. Reproducibility

Every result in this preprint is deterministic and, within a pinned software environment, re-runs to identical values from a fixed seed and the released code; continuous-integration tests verify numerical outputs against predefined tolerances across Python 3.10-3.12. The figures and every quoted number are produced by `paper/make_figures.py` and written to `paper/figures/results.json`, so that text and figures cannot diverge. The full suite of 185 tests runs offline in continuous integration.

## 6. AI-Use Disclosure

This manuscript and the associated software were produced by a human author (S. Yamamoto), who is solely accountable for their content. AI agents were used as tools: code scaffolding and refactoring, test drafting, figure and script generation, and manuscript drafting were assisted by a large language model (Claude, Anthropic). The author independently re-executed every numerical result reported here (the physical-estimator validation, the physical-to-task bridge, the transfer laws, and the test suite) and verified all figures, equations, and claims against the code. No AI system is an author. This disclosure follows ICMJE and COPE guidance: AI is reported as a tool, not credited with authorship.

## 7. Limitations

The framework is a linear-systems, synthetic-data idealisation. It assumes shift-invariant, linear imaging and stationary noise, and models a Gaussian system blur; real detectors depart from these assumptions, and the results here are exact *within* the model rather than validated against a physical scanner. The detection task is signal- and background-known-exactly, the most tractable and least clinically realistic paradigm; signal-known-statistically and background-variable tasks are more demanding and are not treated here. The channelized-Hotelling observer is evaluated by Monte-Carlo simulation rather than a closed form, and is not part of the analytic sweep. No clinical, regulatory, or real-data validation is claimed. Calibration of the phantoms to a specific system, additional acquisition effects, statistically varying signals and backgrounds, and validation against measured data are planned. As released, `taskiq-core` is a research reference, not a clinical or regulatory-grade tool.

## Declarations

**Data and code availability.** All code, the phantom generators, the physical and observer estimators, the atlas, and the test suite are openly available at <https://github.com/Institute-of-One/taskiq-core> under the MIT license, archived on Zenodo (concept DOI [10.5281/zenodo.21422924](https://doi.org/10.5281/zenodo.21422924), all versions). No patient, clinical, or client data were used; all data in this study are synthetic and produced by the included reproducible generators.

**Ethics.** Not applicable. This study involved no human participants, animal subjects, or patient data; only synthetic data were analyzed.

**Competing interests.** S.Y. is the Representative Director (CEO) of LISIT Co., Ltd. and Chief Executive Officer of TexelCraft OÜ. Institute of One is the open-research initiative of LISIT Co., Ltd., which provides institutional oversight and accountability for this work. These commercial relationships are disclosed as potential competing interests. The work used no client or patient data and presents openly licensed research software. The author declares no other competing interests.

**Funding.** This work received no external grant funding. Computing resources and author time were supported in kind by LISIT Co., Ltd. and TexelCraft OÜ.

**Author contributions.** S.Y. is the sole author and is responsible for conceptualization, methodology, software, validation, formal analysis, visualization, and writing. AI tools were used as disclosed in Section 6.

## References

1. Barrett HH, Myers KJ. *Foundations of Image Science.* Hoboken, NJ: Wiley-Interscience; 2004.
2. International Commission on Radiation Units and Measurements. Medical Imaging: The Assessment of Image Quality. *ICRU Report 54.* Bethesda, MD: ICRU; 1996.
3. International Organization for Standardization. Photography — Electronic still picture imaging — Resolution and spatial frequency responses. *ISO 12233.* Geneva: ISO; 2017.
4. International Electrotechnical Commission. Medical electrical equipment — Characteristics of digital X-ray imaging devices — Part 1: Determination of the detective quantum efficiency. *IEC 62220-1.* Geneva: IEC; 2003.
5. Myers KJ, Barrett HH. Addition of a channel mechanism to the ideal-observer model. *Journal of the Optical Society of America A.* 1987;4(12):2447–2457.
6. Burgess AE. Statistically defined backgrounds: performance of a modified nonprewhitening observer model. *Journal of the Optical Society of America A.* 1994;11(4):1237–1242.
