# SPIE Journal of Medical Imaging — Submission Kit — IORN-003 (taskiq-core)

Target: **Journal of Medical Imaging (JMI)**, SPIE. Article type: **Research Article**.
Manuscript to upload (initial submission): **`taskiq-core_jmi.pdf`** — single PDF, figures embedded, **line numbers + page numbers included** (SPIE review requirement). No template needed at first submission; SPIE Word/LaTeX template is required only at revision/acceptance.

## Venue facts (verified 2026-07)
- **Initial submission = single PDF, any format.** Figures embedded near first mention; line + page numbers required. Individual figure files + templated manuscript only at revision/acceptance.
- **Cost: FREE.** Green OA is free (SPIE copyright, deposit in a repository with no embargo). A **diamond OA** option (free to publish + free to read, CC BY 4.0) may be offered — choose it if eligible. **No mandatory page charges** for Research Articles.
- **Preprint OK:** posting a draft on arXiv/medRxiv/Zenodo is allowed and is not prior publication.
- Article types: Research Article / Letter / Review. **taskiq-core = Research Article** (full validated framework; too substantial for a Letter).

## Section (choose at submission)
- **Primary: "Physics of Medical Imaging"** (MTF/NPS/NEQ estimators + reference implementation).
- Alternative: **"Image Perception, Observer Performance, and Technology Assessment"** (model-observer detectability / d' / AUC). Either fits; pick Physics of Medical Imaging unless the editor suggests otherwise.

## Open-access choice
1. **First choice: Diamond OA** if the system offers it for this paper (free to publish, free to read, CC BY 4.0) — fully open + free, matches IoO.
2. **Fallback: Green OA** (free) — publish under SPIE copyright, then **self-archive the accepted manuscript on Zenodo** (already the IoO workflow). Also free; keeps the work open.
- **Do NOT select paid Gold OA.** Not needed.

## Form fields (copy-paste)

**Title:** An Open, Closed-Form-Validated Framework for Task-Based Image Quality on Synthetic Phantoms: From MTF and NPS to Model-Observer Detectability Through NEQ

**Article type:** Research Article

**Author:** Shuji Yamamoto — sole & corresponding author
- Affiliation: **Institute of One, LISIT Co., Ltd., Tokyo, Japan**
- Email: yamamoto@lisit.jp · ORCID: 0000-0001-9211-1071

**Keywords:** task-based image quality; model observer; MTF; NPS; NEQ; detectability; synthetic phantom; reproducible research; open source

**Abstract:** (paste from the manuscript; single paragraph)

## Declarations (already in the manuscript; paste into matching form fields)
- **Conflict of interest:** The author is Representative Director (CEO) of LISIT Co., Ltd. and Chief Executive Officer of TexelCraft OU. Institute of One is the open-research initiative of LISIT Co., Ltd., which provides institutional oversight and accountability for this work. These commercial relationships are disclosed as potential competing interests. The work used no client or patient data and presents openly licensed research software. The author declares no other competing interests.
- **Human/animal subjects:** None. Synthetic data only; no IRB or informed consent applies.
- **Funding:** No external grant funding; author time and computing supported in kind by LISIT Co., Ltd. and TexelCraft OU.
- **Data & code availability:** Openly available at https://github.com/Institute-of-One/taskiq-core (MIT), archived on Zenodo, concept DOI 10.5281/zenodo.21422924 (all versions).
- **AI use:** Disclosed in the manuscript (Section 6, AI-Use Disclosure): a large language model (Claude, Anthropic) assisted with code scaffolding/refactoring, test drafting, figure/script generation, and manuscript drafting; the author re-executed and verified every result; no AI system is an author.

## Suggested reviewers (independent; get each email from their university/ORCID page — do not fabricate)
Leading, independent experts in task-based image quality / model observers (no co-authorship with the author, different institutions):
- **Ehsan Samei** — Duke University (task-based image quality, medical physics).
- **Kyle J. Myers** — (formerly US FDA/CDRH; Hologic) model observers, detectability theory.
- **Ian A. Cunningham** — Western University, Canada (DQE/NEQ, cascaded-systems analysis).
- **Craig K. Abbey** — UC Santa Barbara (model/human observers).
- **Adam Wunderlich** or **Frédéric Noo** — (observer performance / CT image quality).
Pick 3–5. Reviewer suggestions are optional at SPIE but speed assignment.

## Cover letter (optional at SPIE; paste if a field is offered)

```text
Dear Editors of the Journal of Medical Imaging,

Please consider our manuscript, "An Open, Closed-Form-Validated Framework for Task-Based
Image Quality on Synthetic Phantoms: From MTF and NPS to Model-Observer Detectability
Through NEQ," as a Research Article in the Physics of Medical Imaging area.

Task-based assessment is the accepted framework for evaluating medical imaging systems, but
its estimators (MTF, NPS, NEQ, and model observers) are subtle and fail quietly: a
self-consistent regression test will certify plausible but wrong numbers as correct. We
present taskiq-core, an open, pure-Python framework that measures physical image quality and
model-observer task performance on the same synthetic phantoms through one pipeline, and
holds every estimator to a closed-form analytic answer rather than to a snapshot of its own
output. The slanted-edge MTF reproduces the analytic Gaussian-blur transfer to 0.004%; the
ideal-observer detectability computed from the unnormalised NEQ agrees with an independently
computed prewhitening observer to 4.4e-16; and on swept data the framework recovers the
transfer laws theory fixes (d'^2 linear in contrast^2 and in inverse noise variance). All
data are synthetic and generated analytically; the code (185 tests, CI on Python 3.10-3.12)
is MIT-licensed and archived on Zenodo.

The study involves no human participants, no animal subjects, and no patient or third-party
data; only synthetic data are analysed, so no ethics approval or informed consent applies.
A draft has been archived on Zenodo (concept DOI 10.5281/zenodo.21422924); this is not a
peer-reviewed publication and the manuscript is not under consideration elsewhere.
Generative AI was used as a tool and is disclosed in the manuscript; no AI system is an
author. The author declares the competing interests stated in the manuscript.

We believe this transparent, patient-data-free reference implementation of the
physical-to-task chain fits the scope of JMI and will interest its readership in imaging
physics and observer-performance assessment.

Sincerely,
Shuji Yamamoto, PhD
Representative Director (CEO), LISIT Co., Ltd.
Institute of One, Tokyo, Japan
yamamoto@lisit.jp · ORCID 0000-0001-9211-1071
```

## Pre-submission checklist
- [ ] Create SPIE submission account (corresponding author = yamamoto@lisit.jp; link ORCID).
- [ ] Start a new Research Article submission to Journal of Medical Imaging.
- [ ] Upload `taskiq-core_jmi.pdf` (single PDF, figures embedded, line + page numbers). Format = PDF.
- [ ] Section = Physics of Medical Imaging (or Observer Performance).
- [ ] Paste Title / Abstract / Keywords; authors + affiliation + ORCID.
- [ ] Paste declarations (COI / funding / data availability); confirm no human subjects.
- [ ] OA route: choose Diamond OA if offered, else Green OA (both free). Do NOT pay Gold OA.
- [ ] (Optional) add 3–5 suggested reviewers; (optional) paste cover letter.
- [ ] Submit → await editorial check, then peer review (a few months).
- [ ] After acceptance: provide individual high-res figure files + SPIE-templated manuscript; self-archive accepted manuscript to Zenodo (green OA).
