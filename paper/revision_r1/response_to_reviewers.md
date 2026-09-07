# Response to reviewers — jimaging-4539482

**Error Injection in Task-Based Image Quality Pipelines: What Regression Testing Cannot
Catch, and Why Neither Internal Identities nor Closed-Form References Suffice Alone**

Shuji Yamamoto

---

Dear Dr Jiang and reviewers,

Thank you for the careful reading. Every point is addressed below, in order, with the
change made and where to find it. All changes are highlighted in the revised manuscript.

Two of the comments — Reviewer 1's point 5 and Reviewer 2's point 6 — led to corrections
larger than the comments asked for, and I have said so rather than quietly making the
minimum change. One further correction was found while acting on Reviewer 1's point 2 and
is reported at the end under **Corrections not prompted by a comment**, because it was a
false statement in the manuscript and you should know it was there.

---

## Reviewer 1

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

## Reviewer 2

Thank you for the generous assessment and for nine precise requests. Almost all are places
where the paper used a term without introducing it, which is a fair criticism of a paper
that hopes to be read outside its own subfield. Each is answered by defining the term at
first use rather than by pointing at a reference.

**1. Define "detectability" and how it is evaluated; explain the $10^{29}$ number; define
"phantom" and "synthetic phantom".**

All three are now defined in Section 1. Detectability is introduced as the index $d'$ — the
separation between the observer's responses to signal-present and signal-absent images
divided by the standard deviation of that response — with the note that it is dimensionless
and that $d' \approx 2$ corresponds to roughly 92% correct in a two-alternative forced
choice, and that for the ideal observer it is computed in closed form rather than by
simulating decisions.

The $10^{29}$ passage now explains the mechanism: where the computed NPS falls below the
smallest representable number, weighting by $1/\mathrm{NPS}$ multiplies those bins by an
enormous factor, and the result is an arithmetic artefact assembled from bins where the
"signal" is rounding error. The text also makes the point that matters: a plausible $d'$ is
near unity, so $10^{29}$ is at least visibly wrong, and the same mechanism at milder decay
produces a number that is not.

A phantom is now defined as an object of known composition imaged in place of a patient,
and a synthetic phantom as one existing only as an array of numbers, generated rather than
scanned, so that the answer is known analytically. The distinction carries weight
throughout the paper — a synthetic phantom supplies ground truth and a physical one does
not — so it is worth the sentence.

**2. Define "severity" and "severity dial". Is severity an exact parameter that can be
exactly evaluated, and how? Also explain "omitted-sinc bias" and "floating-point
underflow".**

Section 2.4 now says that severity is an exact parameter of the injection and not an
estimate of anything: it is the interpolation weight between the correct implementation and
the defective one, defined separately for each defect and computed rather than measured. A
severity dial is that parameter used as a continuous control, and the text now says why
that matters — a defect that is only present or absent gives one data point, whereas one
that can be turned up from nothing gives a curve, and the curve is where the comparison
between detection and materiality lives.

Floating-point underflow is explained where it first appears, as above. The omitted-sinc
defect is defined by its formula in the same section: the bin-average and central-difference
transfer functions left in the MTF estimate,
$\mathrm{MTF}_\alpha = \mathrm{MTF} \cdot [\mathrm{sinc}(fh)\,\mathrm{sinc}(2fh)]^{\alpha}$.

**3. Define the edge-spread and line-spread functions and how they are formed; clarify the
mean-detrending passage at lines 163–165.**

Both done. The ESF is now defined at first use as the mean profile across the edge obtained
by projecting every pixel onto the edge normal and binning far below the pixel pitch — which
is what the edge's tilt buys — and the LSF as its central difference between adjacent bins.

The detrending passage was genuinely confusing and has been rewritten. It now says that
subtracting the mean from each region of interest sets the zero-frequency component to zero
up to rounding, so the DC bin holds the residue of that subtraction rather than a
measurement; that including it would make the dynamic range enormous for any field, white
noise included; and that the exclusion is bookkeeping about how the estimator works, not a
claim about the spectrum.

**4. Define the "bridge" measure and give its mathematical expression; it is only mentioned
in Table 1.**

Section 2.2 now gives it in the text, as two displayed integrals — $d'^2$ through NEQ
against the object power spectrum, and $d'^2$ from the prewhitening observer — with the
check itself defined as the relative difference between them, and the observation that with
$\mathrm{NEQ} = \mathrm{MTF}^2/\mathrm{NPS}$ the two integrands are the same expression
rearranged, which is why it is an identity and not an approximation.

**5. Line 355, "beyond which a prewhitening observer is refused", is unclear.**

Rewritten to say what was meant: *the threshold beyond which a prewhitening observer should
return no value at all rather than a computed one, because $1/\mathrm{NPS}$ has ceased to be
numerically meaningful.*

**6. More detail about the Python implementation, specifically taskiq-core; and explain more
clearly how AI tools were used in "code scaffolding and refactoring".**

The implementation now has a section of its own (2.7): a pure-Python package on NumPy and
SciPy, containing no DICOM handling and no patient data by design — which is what allows
every quantity in it to be checked against a closed form — the injection study as a single
script importing the library unmodified, and the test matrix.

The second half of your comment was the more important one, and acting on it produced a
correction I would not otherwise have made. **The reconstruction of real projection data is
not in `taskiq-core` at all.** It is in a second package, `ldct-io`, which the submitted
manuscript did not cite and which was not published. Please see *Corrections not prompted by
a comment*, below.

The AI disclosure (now Section 2.8) has been made specific rather than reassuring. It states
what the model drafted — initial versions of the estimator, phantom and test code, the
figure and study scripts, refactoring, and manuscript text — and what it did not do: it did
not choose which defects to inject, set any tolerance, or decide what the results mean.

It also states a fact that belongs in this paper more than in most: **three of the six
defects studied were not invented for the experiment.** They were real errors in drafted
code — the bin-centre position error, the radially-blurred disk, and the missing noise floor
— found by the closed-form checks described here and only then turned into controlled
injections. The checks were the means by which the assistance was verified, which is this
paper's argument applied to its own production.

**7. Grammar, line 287: "throughout" → "throughout the interval".**

Corrected; the sentence now reads "the same estimators used throughout the study", which is
what was meant there.

**8. Two suggested references.**

Thank you for both. I have taken one and, following the editorial checklist's instruction
to assess suggested references critically, declined the other with a reason.

**Taken.** Song K-H, Shan C, Xu G, et al., *Phantom evaluation of small-pixel effect in
ultra-high-resolution photon-counting CT* (J Appl Clin Med Phys 2026;27:e70776), now
reference [21]. It is directly relevant: it reports noise texture and high-contrast
resolution as the paired quantities a change of pixel size moves, which is the same coupling
this paper observes under a change of reconstruction kernel. It is cited in Section 3.7
where that coupling is discussed, and used to make the point that the checks are stated on
those quantities rather than on any particular detector.

**Declined.** Kline A, Gaonkar A, Pittman D, et al., *From Redaction to Restoration: Deep
Learning for Medical Image Deidentification and Reconstruction* (J Digit Imaging Inform Med
2026). I read it and could not find a place where it would inform this manuscript's
argument: it concerns de-identification and restoration of medical images, whereas this
paper is about implementation errors in physical and observer estimators and how they are
detected. Citing it would add a reference the text does not use. I would of course include
it if you see a connection I have missed.

**9. Inline expressions and numerical values should be the same size as the text.**

Corrected throughout. Inline mathematics is now set inline rather than as display
mathematics, including the paragraph between lines 121 and 132 that you identified, and the
whole text was checked for the same problem.

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
