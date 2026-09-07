# Response to Reviewer 1 — jimaging-4539482

**Error Injection in Task-Based Image Quality Pipelines: What Regression Testing Cannot
Catch, and Why Neither Internal Identities nor Closed-Form References Suffice Alone**

Shuji Yamamoto

---

Thank you for the careful reading. Every point you raised is addressed below, in order,
with the change made and where to find it. All changes are highlighted in the revised
manuscript.

**1. The Introduction would benefit from briefly positioning the proposed identities
relative to property-based testing, metamorphic testing, and verification practices for
scientific software.**

Agreed, and this was a real gap: the paper proposed checks whose reference comes from
outside the code without saying that this is a named idea with a literature behind it.

A paragraph has been added at the end of Section 1.2 naming both correspondences
explicitly. The internal identities are properties in the sense of property-based testing
[18], with the algebra of the imaging chain supplying the property rather than a
programmer's intuition; the checks comparing two routes to the same quantity are
metamorphic relations [19], the standard answer to the oracle problem, which is exactly
this paper's situation. Verification practice for computational science is cited from the
scientific side [20]. The paragraph ends by saying what the paper adds that is not
borrowed: which relations exist for this particular chain, what each detects, what it
costs, and the finding that the two families are not interchangeable.

**2. Figure 4 is information-dense, and some labels and plotted series are difficult to
distinguish at normal page size. Please enlarge the labels and legend and consider adding
panel labels to Figures 4 and 5. Please also explain the boldface used in Table 2.**

Figure 4 has been regenerated: type enlarged throughout, 600 dpi instead of 300, and panel
labels **(a)** and **(b)** added. The cause was not only the base font size — every
per-call font size in the plotting code was overriding it, which is why the figure stayed
small.

Regenerating it showed a second problem your comment covers but does not name, and I have
fixed that too. Every detection in panel (a) falls between 0.1 and 0.2 on a colour scale
running 0 to 1, so colour separated almost nothing. **Each cell now prints its severity**
and the colour scale spans the data. The panel is exact rather than approximate, and it
happens to answer your point 4 visually as well.

Figure 5 now carries panel labels. The boldface in Table 2 marks the single largest value
in its column, and the caption now says so.

**3. The checklist in Section 4.2 describes six checks but is numbered as seven items
because the two closed-form checks are introduced through an additional numbered item.
Please reorganize the numbering so that the four identities and two closed-form references
are unambiguous.**

You are right, and I found the mechanism: in the markdown source the introducing sentence
sits between two lists, but the converter absorbed it into the first, so the submitted DOCX
numbered it as an item. The source looked correct and the document you read was not.

Rather than re-wrap the sentence and hope, the grouping is now explicit and cannot be
absorbed by any converter: **A1–A4** for the four internal identities and **B1–B2** for the
two closed-form references, each family under its own heading, with a lead sentence saying
"six checks, in two families; nothing else in this list is a check." Later cross-references
to "check 5" have been renamed accordingly.

**4. Please specify the complete severity grid used for each injected defect. Since the
first reported detection severity is consistently 0.1, readers should know whether this is
the resolution limit of the experiment. The number of stochastic repetitions or seeds and
the procedure used to derive each tolerance from estimator reproducibility should also be
described more explicitly.**

All three are now stated in Section 2.5, under a new paragraph headed *The grid, and what
it can and cannot resolve*:

- the grid is the same eleven points for every defect, $\alpha \in \{0, 0.1, \ldots, 1.0\}$;
- 64 noise realisations at each point, with the random streams fixed by seed so a rerun
  reproduces the table exactly;
- each tolerance is set from the estimator's measured residual over those 64 realisations,
  with an order of magnitude of margin, as listed in Table 1.

On your specific question: **yes, 0.1 is the resolution limit, and the manuscript now says
so in those terms.** Seven of the eight detections occur at the smallest non-zero severity
examined, which is a property of the grid as much as of the checks. The paper's claim is
therefore that detection precedes materiality, which the grid does resolve, and not that a
detection threshold has been measured, which it does not. I would rather state that
limitation than leave a reader to infer a precision the experiment does not have.

**5. Four internal identities are introduced, yet Table 4 reports only three for the
measured-scanner experiment. Please either explain the omission of the NEQ/prewhitening
bridge identity or include its result. If not all four identities were evaluated, the claim
that they "transferred intact" should be qualified.**

This was the most valuable comment in either report, and both halves of it were right.

The reason for the omission existed in the manuscript, in Section 4.6, and nowhere near
Table 4 — so you met the gap without meeting the reason, which is a failure of the writing
rather than of the reading. `bridge` compares a prewhitening observer using the measured
noise spectrum against an NEQ route requiring an analytic noise scalar. On a physical
scanner those two routes stop sharing a noise model, so what the check then measures is
that disagreement rather than the correctness of the pipeline. It is now stated in Section
3.8 where the reader meets the table, and again in the caption of Table 4, since a reader
may reach the table first.

**And the abstract was overclaiming.** It said "the identities transferred intact"; only
three of the four can be evaluated on measured data at all. It now reads "the three
identities that can be evaluated without ground truth transferred intact". No new
computation was needed — the claim was simply wider than the evidence, and you caught it.

---

---

## Corrections not prompted by a comment

Two things were found while acting on the comments above. Both were wrong in the submitted
manuscript, and I would rather report them than let them pass.

**1. The Data Availability Statement was false, and the code it omitted is now published.**

The submitted statement said that all the code is at `taskiq-core` and that every number is
written by the scripts producing the figures. That is true of the synthetic arm and false of
the real-scanner arm. Tables 3 and 4, Figure 5 and Sections 2.6 to 3.8 are produced by
`examples/acr_atlas.py` in a second package, `ldct-io`, which supplies the DICOM-CT-PD
reading, the single-slice rebinning and the filtered backprojection. That package was not
cited and had never been published.

For a paper whose argument is that a result you cannot re-derive is a result you cannot
check, this was not a citation slip. It has been fixed at the source rather than in the
wording:

- **`ldct-io` is now public** at <https://github.com/Institute-of-One/ldct-io> under the MIT
  licence, with 60 passing tests, continuous integration, and its reconstruction validated
  against closed-form answers rather than against a stored output of itself;
- five example scripts had a single machine's archive path hard-coded, which would have left
  a reader unable to run any of them; the location now comes from an environment variable;
- the Data Availability Statement now says which half of the work lives where, and states
  plainly that **neither package reproduces the atlas alone.**

**2. The affiliation has been corrected to the form the author's other papers carry.**

The submitted manuscript omitted the postal code, and the author record entered in the
submission system also reads "Institute of one, LISIT, Co., Ltd." The correct and
consistent form, as carried by this author's papers in *Journal of Imaging* (12(8):392,
2026) and *Tomography* (12(9):125, 2026), is:

> Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan

The manuscript is corrected. **I would be grateful if the author record in the submission
system could be corrected to match**, as I do not appear to be able to edit it at this
stage.

---

## English language

Reviewer 1 marked the English as improvable and Reviewer 2 as not requiring improvement. I
have taken the first at face value: the whole manuscript has been reread for clarity, and
the passages Reviewer 2 identified as confusing — the detrending explanation, the "refused"
sentence, and the definitions of severity, ESF, LSF and bridge — were the places where the
writing was in fact doing the least work. Those are rewritten rather than merely polished.

Thank you both for reviews that improved the paper, and in two places corrected it.

Yours sincerely,

Shuji Yamamoto
Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan
ORCID 0000-0001-9211-1071