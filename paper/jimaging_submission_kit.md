# Journal of Imaging (MDPI) — Submission Kit — taskiq-core

Target journal: **Journal of Imaging** (MDPI), ISSN 2313-433X. Article type: **Article**.
Submission portal: <https://susy.mdpi.com/user/manuscripts/upload?journal=jimaging>
Manuscript source: **`paper/manuscript.md`**. Upload **`paper/taskiq-core_jimaging.docx`**,
built with pandoc. Build it fresh before uploading and delete any other .docx in the
directory: a stale build with a plausible name sitting beside the current one is the
easiest way to submit the wrong file. Figures in `paper/figures/`.

```bash
python paper/make_figures.py && python paper/make_injection_study.py
python -c "import pypandoc,os; os.chdir('paper'); "\n  "pypandoc.convert_file('manuscript.md','docx',outputfile='taskiq-core_jimaging.docx',"\n  "extra_args=['--resource-path=.'])"
```

**Do not submit a `build_pdf.py` render.** That script states in its own docstring that
it works "without pandoc/LaTeX", which means it cannot typeset `$...$`: every equation
comes out as literal source. pandoc turns them into 143 Word equation objects and
embeds all five figures. The near-accepted IORN-002 submission went the same way.

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
  references in square brackets [1], MDPI/ACS style (**ours: 17 references, already in
  that form**).
- GenAI use must be disclosed in **Materials and Methods** (done, §2.7) **and**
  **Acknowledgments** (done).

## Form fields (copy–paste)

**Title:** Error Injection in Task-Based Image Quality Pipelines: What Regression
Testing Cannot Catch, and Why Neither Internal Identities nor Closed-Form
References Suffice Alone

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

- [x] **All seventeen references verified.** 1-8 are unchanged from the JMI submission
      and were verified then; 9-17 were each checked against the Crossref record, and
      the list was measured against this author's own manuscripts before being
      extended: 10 references over 6214 words was 1.6 per 1000, the lowest of his five
      papers, against 3.2 for the near-accepted IORN-002 and 2.7 for ctdose-core. It is
      now 17 over 6498 words, 2.6 per 1000. Every added reference is cited where the
      text argues rather than appended to the list: the reproducibility and
      software-defect literature under the regression-test argument, the CT task-based
      review where Section 4.1 makes a claim about published practice, the ACR phantom
      MTF/NPS method beside the real-scanner arm, and mutation testing where Section
      4.3 named it without citing it. No reference is listed that the text does not
      use, and none is cited that is not listed.
- [x] **Detail on the two that needed care.** Reference 10
      (Moen et al., *Med Phys* 2021;48(2):902–911, doi:10.1002/mp.14594) matches the
      Crossref record exactly. Reference 9 (Samei et al., AAPM TG-233,
      *Med Phys* 2019;46(11), doi:10.1002/mp.13763) is confirmed for authors, title,
      journal, volume, issue and year; Crossref carries **no page range and no article
      number** for it, so the page range that had been written from a secondary source
      was removed rather than left unverified. References 1–8 are unchanged from the JMI
      submission and were verified then.
- [x] **No preprint exists, and none can be posted.** `paper/taskiq-core_arxiv.md` and
      `paper/arxiv_submission_kit.md` were prepared and could not be submitted: arXiv
      requires an endorser in these categories and the author has none, and medRxiv
      refused the submission because Institute of One / LISIT Co., Ltd. is not recognised
      as a research institution. Only servers that gate on neither an endorser nor an
      institutional affiliation are open to him; Zenodo is the one in use, and it holds
      the *software*, not a preprint of this manuscript. The cover letter therefore
      discloses the Zenodo software archive only, which is correct as written.
- [ ] Confirm the APC and the free-format policy are unchanged since July 2026.
- [x] **Five figures embedded, and legible after reduction.** Both multi-panel figures
      were drawn far wider than the column they print into, so their type shrank by a
      third to a half on the page. Figure 4 is now stacked rather than side by side and
      its type set explicitly; Figure 5 is 2x2 at 7.8 in rather than 1x4 at 19 in. Judge
      figures at printed size, not on screen: every collision in both -- the threshold
      label running off the axes, a legend on top of the smallest curve, seven
      annotations overlapping each other, and two end labels pushed outside the frame --
      became visible only once the type was large enough to read.
- [x] **One caption per figure and per table.** Each figure briefly carried two: pandoc
      renders an image's alt text as a caption of its own, so alt text plus a numbered
      paragraph printed every description twice, in two wordings. The alt text is now
      empty and the numbered paragraph carries the fuller text. Verified in the built
      .docx: five figure captions and three table captions, one occurrence each.
- [ ] Regenerate before sending: `python paper/make_figures.py` and
      `python paper/make_injection_study.py`, then confirm the numbers in the text still
      match `paper/figures/injection.json`.

## Cover letter (paste into the portal)

```text
Dear Editors of the Journal of Imaging,

Please consider our manuscript, "Error Injection in Task-Based Image Quality
Pipelines: What Regression Testing Cannot Catch, and Why Neither Internal
Identities nor Closed-Form References Suffice Alone," as an Article.

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
