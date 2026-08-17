# Journal of Imaging (MDPI) — Submission Kit — taskiq-core

Target journal: **Journal of Imaging** (MDPI), ISSN 2313-433X. Article type: **Article**.
Submission portal: <https://susy.mdpi.com/user/manuscripts/upload?journal=jimaging>
Manuscript source: **`paper/manuscript.md`**. Figures in `paper/figures/` (≥600 dpi PNG).

## Why this venue

The two JMI decisions and the JACMP reclassification of the companion dose paper all
turned on classification and perceived novelty, never on correctness — JMI's letters said
"your paper may be original and correct". Every medical physics journal carries a Note or
Technical Note category into which a validation paper can be moved: Medical Physics,
Physics in Medicine and Biology, Physica Medica, JACMP (where it happened), PESM. MDPI's
imaging journals do not use that category in practice; **Article** is the default. This
venue removes the failure mode that has stopped this work three times.

**The author does not have an acceptance here.** IORN-002 (`jimaging-4486384`, submitted
2026-07-23) has been through two rounds of review and is at *Pending editor decision*; the
companion IORN-006 (`tomography-4516935`, submitted 2026-08-06) is *Under review*. Two
rounds without rejection says the journal engages seriously with this author's work, which
is worth something, but it is not evidence of acceptance and must not be quoted as such.
If IORN-002 is rejected, revisit this choice before sending anything further.

## Key facts about the venue (verified for IORN-002, 2026-07; re-verify before sending)

- **APC: CHF 1800** on acceptance (payment also accepted in JPY/USD/EUR/GBP/CAD). Only
  invoices from @mdpi.com are valid.
- Open access, **CC BY** licence.
- **Preprints are allowed**, provided they have not undergone peer review. Disclose in the
  cover letter.
- **Free-format submission accepted at first submission** — all required sections present,
  references in any consistent style. The MDPI Word template (`jimaging-template.dot`) is
  required only at the revision stage.
- Abstract ≈ 200 words (**ours: 205**). Keywords 3–10 (**ours: 10**). SI units. Numbered
  references in square brackets [1], MDPI/ACS style (**ours: 10 references, already in
  that form**).
- GenAI use must be disclosed in **Materials and Methods** (done, §2.7) **and**
  **Acknowledgments** (done).

## Form fields (copy–paste)

**Title:** Error injection in task-based image quality pipelines: what self-consistency
testing misses and what closed-form checks catch

**Article type:** Article

**Section:** Medical Imaging

**Author:** Shuji Yamamoto — sole & corresponding author
- Affiliation: **Institute of One, LISIT Co., Ltd., Tokyo, Japan**
- Email: yamamoto@lisit.jp · ORCID: 0000-0001-9211-1071

**Keywords:** task-based image quality; model observer; MTF; NPS; NEQ; detectability;
error injection; implementation error; quality assurance; closed-form validation

**Abstract:** paste from `manuscript.md` (205 words).

## Required declarations (already in the manuscript back-matter)

- **Author Contributions** — CRediT paragraph, sole author.
- **Funding** — "This research received no external funding."
- **Institutional Review Board Statement** — not applicable; no human or animal subjects;
  the only measured data are of a physical quality-assurance phantom from a public archive.
- **Informed Consent Statement** — not applicable.
- **Data Availability Statement** — GitHub + Zenodo concept DOI 10.5281/zenodo.21422924;
  ACR_Phantom series of LDCT-and-Projection-data (TCIA, CC BY 4.0, DOI 10.7937/9npb-2637).
- **Acknowledgments** — GenAI (Claude, Anthropic) disclosure.
- **Conflicts of Interest** — LISIT Co., Ltd. / TexelCraft OÜ; oversight relationship
  stated; no other conflict.

## Before sending — open items

- [x] **References 9 and 10 verified against Crossref.** Reference 10
      (Moen et al., *Med Phys* 2021;48(2):902–911, doi:10.1002/mp.14594) matches the
      Crossref record exactly. Reference 9 (Samei et al., AAPM TG-233,
      *Med Phys* 2019;46(11), doi:10.1002/mp.13763) is confirmed for authors, title,
      journal, volume, issue and year; Crossref carries **no page range and no article
      number** for it, so the page range that had been written from a secondary source
      was removed rather than left unverified. References 1–8 are unchanged from the JMI
      submission and were verified then.
- [ ] **Preprint status.** `paper/taskiq-core_arxiv.md` and `paper/arxiv_submission_kit.md`
      exist, but no arXiv identifier is recorded anywhere in the repository. If the
      preprint was posted, disclose it in the cover letter and give the identifier; if it
      was only prepared, delete the disclosure sentence. **Do not send until this is
      settled** — an undisclosed preprint is a real problem, and a disclosed one that does
      not exist is worse.
- [ ] Confirm the APC and the free-format policy are unchanged since July 2026.
- [ ] Figures exported at ≥600 dpi: `fig1_physical.png`, `fig2_bridge.png`,
      `fig3_transfer.png`, `fig4_injection.png`, and the ACR atlas figure.
- [ ] Regenerate before sending: `python paper/make_figures.py` and
      `python paper/make_injection_study.py`, then confirm the numbers in the text still
      match `paper/figures/injection.json`.

## Cover letter (paste into the portal)

```text
Dear Editors of the Journal of Imaging,

Please consider our manuscript, "Error injection in task-based image quality pipelines:
what self-consistency testing misses and what closed-form checks catch," as an Article.

Task-based assessment is the accepted framework for evaluating medical imaging systems,
but the chain that implements it — MTF, NPS, NEQ and model observers — fails by returning
a plausible wrong number rather than an error. The test most implementations carry, a
regression test against the code's own stored output, cannot detect this: if the defect
was present when the reference was recorded, the deterministic pipeline reproduces it and
the test passes. We therefore injected six defects into a validated implementation of the
chain, each through a severity dial that recovers the correct pipeline exactly at zero,
and measured which checks detect them and at what severity.

The self-consistency regression test detected none of the six. Internal identities, which
need no ground truth, and closed-form references, which need a phantom whose answer is
known, together detected all six, in every case at or before the severity at which the
reported detectability index became wrong by more than 5 per cent — but neither family
sufficed alone, each detecting three of six. Half of these defects are therefore
undetectable without a phantom of known truth, which is an argument for keeping one in a
workflow whose object is real images. Run unmodified on measured ACR phantom projections
across seven reconstruction kernels, the identities transferred intact while their
tolerances did not, and the strongest apodisation drove the measured noise dynamic range
to within 0.6 per cent of the point at which a prewhitening observer must refuse to return
a number at all.

The work involves no human participants, no animal subjects and no patient data; the only
measured data are of a physical quality-assurance phantom obtained from The Cancer Imaging
Archive under CC BY 4.0, so no ethics approval or informed consent applies.

Disclosure: the software is archived on Zenodo (concept DOI 10.5281/zenodo.21422924). The
manuscript is not under consideration elsewhere. Generative AI was used as a tool and is
disclosed in Section 2.7 and the Acknowledgments; no AI system is an author.

The author declares the competing interests stated in the manuscript. We believe the work
fits the scope of the Journal of Imaging and will interest its readership in medical
imaging, image quality assessment and reproducible imaging research.

Yours sincerely,
Shuji Yamamoto, PhD
Institute of One, LISIT Co., Ltd., Tokyo, Japan
yamamoto@lisit.jp · ORCID 0000-0001-9211-1071
```
