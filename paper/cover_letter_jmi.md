---
geometry: margin=1in
fontsize: 11pt
papersize: a4
---

Shuji Yamamoto, PhD
Representative Director (CEO), LISIT Co., Ltd.
Institute of One, Tokyo, Japan
yamamoto@lisit.jp · ORCID 0000-0001-9211-1071

2026

To the Editors, *Journal of Medical Imaging* (SPIE)

Dear Editors,

Please consider our manuscript, "An Open, Closed-Form-Validated Framework for Task-Based Image Quality on Synthetic Phantoms: From MTF and NPS to Model-Observer Detectability Through NEQ," as a **Research Article** in the Physics of Medical Imaging area.

**Problem and significance.** Task-based assessment is the accepted framework for evaluating medical imaging systems, but its estimators — the modulation transfer function (MTF), noise power spectrum (NPS), noise-equivalent quanta (NEQ), and model observers — are subtle and fail quietly: a self-consistent regression test will certify plausible but wrong numbers as correct, and reproducibility is hard to guarantee when the ground truth is itself an image.

**What is new.** We present taskiq-core, an open, pure-Python framework that measures physical image quality and model-observer task performance on the same synthetic phantoms through one pipeline, and holds every estimator to a *closed-form analytic answer* rather than to a snapshot of its own output. The slanted-edge MTF reproduces the analytic Gaussian-blur transfer to 0.004% over fifteen blur-by-angle combinations; the ideal-observer detectability computed from the unnormalised NEQ agrees with an independently computed prewhitening observer to a relative error of 4.4e-16; and on swept data the framework recovers the transfer laws theory fixes (d'^2 linear in contrast^2 and in inverse noise variance, with coefficient of determination numerically equal to 1). All data are synthetic and generated analytically; the code (185 tests, continuous integration on Python 3.10–3.12) is MIT-licensed and archived on Zenodo.

**Why this journal.** The manuscript is a transparent, patient-data-free reference implementation of the physical-to-task chain — precisely the imaging-physics and observer-performance methodology at the core of JMI's scope.

**Declarations.** The study involves no human participants, no animal subjects, and no patient or third-party data; only synthetic data are analysed, so no ethics approval or informed consent applies. A draft has been archived on Zenodo (version DOI 10.5281/zenodo.21422924, v0.4.0); this is not a peer-reviewed publication and the manuscript is not under consideration elsewhere. Generative AI was used as a tool and is disclosed in the manuscript; no AI system is an author. The author declares the competing interests stated in the manuscript (LISIT Co., Ltd. and TexelCraft OU).

Thank you for your consideration.

Sincerely,

Shuji Yamamoto, PhD
Representative Director (CEO), LISIT Co., Ltd.
Institute of One, Tokyo, Japan
