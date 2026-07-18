# arXiv Submission Kit — IORN-003 (taskiq-core)

Copy-paste-ready fields for the arXiv submission form.
Manuscript file to upload: **`taskiq-core_arxiv.pdf`** (figures embedded).

> **Why arXiv, not medRxiv.** taskiq-core is a pure methodology/open-source contribution on
> synthetic data with no clinical claim. medRxiv screens for health-research scope and
> institutional oversight (this is where IORN-002 stalled); arXiv screens for on-topic,
> non-junk methodology plus endorsement. eess.IV / physics.med-ph is the natural home.

---

## Primary category
**eess.IV** — Image and Video Processing.

## Cross-list (secondary categories)
- **physics.med-ph** — Medical Physics.
- *(optional)* **eess.SP** — Signal Processing.

> **Endorsement.** A first submission to `eess.IV` may require an endorsement from an
> existing arXiv author in that category. If the author is not yet endorsed there, request
> endorsement (arXiv provides an endorsement code/URL on the submission attempt) before
> uploading. This is the one gating step to check first.

## Title
An Open, Closed-Form-Validated Framework for Task-Based Image Quality on Synthetic Phantoms: from MTF and NPS to Model-Observer Detectability through NEQ

## Authors
Shuji Yamamoto (Institute of One, LISIT Co., Ltd., Tokyo, Japan)

- Corresponding author: Shuji Yamamoto
- Email: yamamoto@lisit.jp
- ORCID: 0000-0001-9211-1071

## Comments field
6 pages, 3 figures. Software (MIT): https://github.com/Institute-of-One/taskiq-core — archived on Zenodo, concept DOI 10.5281/zenodo.21422924.

## ACM/MSC class (optional)
ACM: I.4.0 (Image Processing and Computer Vision — General); J.3 (Life and Medical Sciences).

## Keywords
task-based image quality; model observer; MTF; NPS; NEQ; detectability; synthetic phantom; reproducible research; open source

---

## Abstract (plain text, arXiv-length ~200 words)

Task-based assessment evaluates an imaging system by how well a specified observer performs a specified detection task, and its ingredients — MTF, NPS, NEQ, and model observers — are individually standardised and theoretically mature. Assembling them correctly is nonetheless error-prone: the estimators are subtle and their mistakes are quiet, producing plausible but wrong numbers that a self-consistent regression test will certify as correct. We present taskiq-core, an open, pure-Python framework that measures physical image quality (MTF, NPS, NEQ) and task performance (model-observer detectability d' and AUC) on the same synthetic phantoms, through one pipeline. Every estimator is held to a closed-form analytic answer rather than to a snapshot of its own output: the slanted-edge MTF reproduces exp(-2 pi^2 sigma^2 f^2) to 0.004% over fifteen blur-by-angle combinations, and the ideal-observer detectability computed from NEQ against an object's power spectrum agrees with an independent prewhitening observer to 4.4e-16. On swept data the framework recovers the exact transfer laws — d'^2 linear in contrast^2 and in inverse noise variance (R^2 = 1.000 each). All data are synthetic; the code (185 tests, CI on Python 3.10-3.12) is MIT-licensed and archived on Zenodo. The contribution is a transparent, patient-data-free reference implementation of the physical-to-task chain, made exact rather than approximate.

*(~205 words. arXiv abstract limit is generous; keep under ~1920 characters.)*

---

## License (choose on arXiv)
**Recommended: CC BY 4.0** — matches the open ethos (text/figures CC BY 4.0, code MIT) and permits reuse with attribution.

*Alternatives arXiv offers:* CC BY-SA 4.0, CC BY-NC-SA 4.0, CC0, or the arXiv non-exclusive license to distribute (arXiv's default minimal grant). Avoid the minimal grant if reuse is intended.

---

## Format notes
- arXiv prefers LaTeX source but **accepts a PDF-only submission** when no TeX source exists. This manuscript is built from Markdown via `paper/build_pdf.py` (reportlab), so upload the PDF and select "PDF" as the format. (A pandoc → LaTeX path is available later if a TeX source is wanted.)
- Ensure the uploaded PDF has the three figures embedded (it does — `build_pdf.py` inlines them).
- No health/ethics/clinical-trial/IRB declarations are required by arXiv (those are medRxiv-specific). The manuscript's Declarations section already carries competing-interests, funding, data-availability, and an AI-use disclosure.

---

## Verify before submitting
- [ ] **References**: `paper/paper.bib` flags that DOIs / exact editions of the standards (ISO 12233, IEC 62220-1) and the two JOSA A papers should be verified against primary sources. Confirm before submission.
- [ ] Regenerate figures and numbers: `python paper/make_figures.py` → `paper/figures/results.json`.
- [ ] Rebuild the PDF: `python paper/build_pdf.py` → `paper/taskiq-core_arxiv.pdf`.
- [ ] Confirm eess.IV endorsement status for the author.

---

## Pre-submission checklist
- [ ] arXiv account ready (corresponding author = yamamoto@lisit.jp; ORCID linked)
- [ ] Endorsement for eess.IV obtained if needed
- [ ] Upload `taskiq-core_arxiv.pdf`; format = PDF
- [ ] Primary category eess.IV; cross-list physics.med-ph
- [ ] Paste Title / Authors / Abstract / Comments / Keywords
- [ ] Choose license: CC BY 4.0
- [ ] Submit → await arXiv moderation
- [ ] After the arXiv ID / DOI is issued, record it in the runbook Appendix C (IORN-003) and, optionally, add it to CITATION.cff and the README.

---

## After it is live
- Record the arXiv identifier and preprint DOI in `IoO_OpenCore_Publication_Runbook.md` (Appendix C, IORN-003).
- The arXiv posting does not count as prior publication for JOSS or SPIE JMI, so both remain open (JOSS from 2027-01, six months after the repository went public).
