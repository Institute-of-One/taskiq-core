# What was applied, and what it replaced

Each entry is one edit made into the journal's formatted file: the paragraph as
the editorial office sent it, and the paragraph as it now reads. Equations show
as `[equation]`, since they were moved across rather than retyped.

## replace at paragraph 86

**Was:** 2.7. Use of Generative AI

**Now:** 2.7. Implementation

## replace at paragraph 87

**Was:** Code scaffolding and refactoring, test drafting, figure and script generation, and manuscript drafting were assisted by a large language model (Claude, Anthropic). The author independently re-executed every numerical result reported here and verified all figures, equations and claims against the code. No AI system is an author.

**Now:** The estimators, the phantoms and the observers are taskiq-core, a pure-Python package depending only on NumPy and SciPy, with Matplotlib for figures. It contains no DICOM handling and no patient data by design, which is what allows every quantity in it to be checked against a closed form. The MTF, NPS, NEQ and observer routines are the ones named in Section 2.2; the injection study is a single script, paper/make_injection_study.py, that imports them unmodified and applies each defect through the severity dial rather than by editing the library. Reconstruction from real projection data is not in that package but in ldct-io, for the same reason: the archive, its private tags and its geometry have no business inside a library whose correctness is established analytically. The test suite runs on Python 3.10 to 3.12 in continuous integration, and asserts the identities of Section 4.2 on the correct pipeline as well as the study's own preconditions.

## insert at paragraph 87

**After:** Code scaffolding and refactoring, test drafting, figure and script generation, and manuscript drafting were assisted by a large language model (Claude, Anthropic). The author independently re-executed every numerical result reported here and verified all figures, equations and claims against the code. No AI system is an author.

**Inserted:** 2.8. Use of Generative AI

## insert at paragraph 87

**After:** Code scaffolding and refactoring, test drafting, figure and script generation, and manuscript drafting were assisted by a large language model (Claude, Anthropic). The author independently re-executed every numerical result reported here and verified all figures, equations and claims against the code. No AI system is an author.

**Inserted:** A large language model (Claude, Anthropic) was used as a tool. Concretely: it drafted initial versions of the estimator and phantom routines and of the test suite, wrote the figure and study scripts, refactored code the author had written, and drafted and edited manuscript text. It did not choose which defects to inject, did not set any tolerance, and did not decide what the results mean.

## insert at paragraph 87

**After:** Code scaffolding and refactoring, test drafting, figure and script generation, and manuscript drafting were assisted by a large language model (Claude, Anthropic). The author independently re-executed every numerical result reported here and verified all figures, equations and claims against the code. No AI system is an author.

**Inserted:** The relationship between that assistance and this paper's subject is not incidental and is stated plainly here. Three of the six defects studied were not invented for the experiment: they were real errors present in drafted code — the bin-centre position error, the radially-blurred disk, and the missing noise floor — found by the closed-form checks described here and only then turned into a controlled injection. The checks were the means of verifying the assistance, which is the argument of the paper applied to its own production. The author independently re-executed every numerical result reported here and verified all figures, equations and claims against the code. No AI system is an author.

## replace at paragraph 264

**Was:** The four internal identities are cheap, need no phantom, and can be asserted inside any implementation of this chain:

**Now:** Six checks, in two families. Nothing else in this list is a check.

## insert at paragraph 264

**After:** The four internal identities are cheap, need no phantom, and can be asserted inside any implementation of this chain:

**Inserted:** Family A — the four internal identities. Cheap, needing no phantom, and assertable inside any implementation of this chain:

## replace at paragraph 265

**Was:** equals the pixel variance of the data the NPS was estimated from, to floating-point tolerance.

**Now:** A1. equals the pixel variance of the data the NPS was estimated from, to floating-point tolerance.

## replace at paragraph 266

**Was:** Ideal-observer computed through NEQ equals computed by the prewhitening observer, when both use the same noise model.

**Now:** A2. Ideal-observer computed through NEQ equals computed by the prewhitening observer, when both use the same noise model.

## replace at paragraph 267

**Was:** The integral of a blurred signal equals the integral of the unblurred signal.

**Now:** A3. The integral of a blurred signal equals the integral of the unblurred signal.

## replace at paragraph 268

**Was:** The NPS dynamic range, excluding DC, stays within the range where is meaningful; a prewhitening observer should refuse rather than return a number when it does not. Section 3.8 shows this is not a theoretical precaution: strong apodisation on a real scanner approaches the threshold closely enough that the check decides real cases.

**Now:** A4. The NPS dynamic range, excluding DC, stays within the range where is meaningful; a prewhitening observer should refuse rather than return a number when it does not. Section 3.8 shows this is not a theoretical precaution: strong apodisation on a real scanner approaches the threshold closely enough that the check decides real cases.

## replace at paragraph 269

**Was:** The two closed-form references require a phantom and catch what the identities cannot:

**Now:** Family B — the two closed-form references. These require a phantom, and catch what the identities cannot:

## replace at paragraph 270

**Was:** The presampled MTF of an analytically blurred edge equals .

**Now:** B1. The presampled MTF of an analytically blurred edge equals .

## replace at paragraph 271

**Was:** The NPS of white noise of known variance equals .

**Now:** B2. The NPS of white noise of known variance equals .

## replace at paragraph 272

**Was:** The injection study adds two methodological items to these six. Check 5 must be evaluated over a sweep of edge angles, not one, because the bias it detects is not monotone in angle and can be an order of magnitude larger between two angles half a degree apart. And every tolerance must be set from the estimator’s measured reproducibility in the configuration actually in use: too loose and it misses the defect, too tight and it fires on correct code, and the correct value differs by four orders of magnitude between synthetic and measured data for the same identity.

**Now:** The injection study adds two methodological requirements to these six checks. Check B1 must be evaluated over a sweep of edge angles, not one, because the bias it detects is not monotone in angle and can be an order of magnitude larger between two angles half a degree apart. And every tolerance must be set from the estimator's measured reproducibility in the configuration actually in use: too loose and it misses the defect, too tight and it fires on correct code, and the correct value differs by four orders of magnitude between synthetic and measured data for the same identity.

## replace at paragraph 101

**Was:** Figure 4. What each check sees. Left: the injected severity at which each check first fires, grey where it never does; the rightmost column is the self-consistency regression test, grey for every defect. The white rules separate internal identities (left) from closed-form references (centre) and from the regression control (right). Right: the relative error each defect produces in a reported , against the 5% materiality threshold (dashed).

**Now:** Figure 4. What each check sees. (a) The injected severity at which each check first fires, printed in the cell and shown by colour, grey where the check never fires; the rightmost column is the self-consistency regression test, grey for every defect. The white rules separate internal identities (left) from closed-form references (centre) and from the regression control (right). (b) The relative error each defect produces in a reported , against the 5% materiality threshold (dashed).

## replace at paragraph 217

**Was:** Figure 5. The same chain on measured ACR phantom projections, with the reconstruction kernel swept from a bare ramp through Hann apodisation at cutoffs 1.00 to 0.25. Nothing about the acquisition is simulated; the same projections are reconstructed seven ways.

**Now:** Figure 5. The same chain on measured ACR phantom projections, with the reconstruction kernel swept from a bare ramp through Hann apodisation at cutoffs 1.00 to 0.25. (a) measured MTF; (b) measured NPS; (c) NEQ; (d) detectability for the ideal and the non-prewhitening eye-filter observer against MTF50. Nothing about the acquisition is simulated; the same projections are reconstructed seven ways.

## replace at paragraph 221

**Was:** The three internal identities that can be evaluated without ground truth were run on all seven real-scanner reconstructions (Table 4).

**Now:** Three of the four internal identities were run on all seven real-scanner reconstructions (Table 4). The fourth, bridge, is absent for a reason specific to measured data rather than by omission: it compares a prewhitening observer using the measured noise spectrum against an NEQ route that requires an analytic noise scalar, and on a physical scanner those two routes no longer share a noise model. What it then measures is that disagreement, not the correctness of the pipeline, and Section 4.6 gives the residual it produces. The claim of transfer in this paper is therefore made for three identities, not four.

## replace at paragraph 69

**Was:** Two points deserve emphasis. First, bridge compares two routes to the same number — the prewhitening observer applied to the imaged signal, and the integral of NEQ against the object’s power spectrum — that share no code path but are, under the discrete conventions used here, the same integral rearranged. It is therefore an exact identity rather than an approximation, and holds to zero on the reference pipeline. It is only an identity when both routes use the same noise model; comparing routes that disagree about the noise tests nothing but that disagreement. Second, dynamic_range excludes the DC bin, which mean-detrending drives to by construction. That is bookkeeping, not a decayed spectrum, and reading it as one causes the check to fire on every field including white noise.

**Now:** Two points deserve emphasis. First, the bridge check states that the two routes to ideal-observer detectability agree:

## replace at paragraph 17

**Was:** A prewhitening observer weights by . Handed a noise model whose power decays below floating-point underflow, it returns a detectability of order , assembled entirely from frequency bins where the “signal” is rounding error.

**Now:** A prewhitening observer weights by . Handed a noise model whose power decays below floating-point underflow — that is, where the computed NPS falls below the smallest number the arithmetic can represent and is stored as a denormal or as zero — it weights those bins by and so multiplies them by an enormous factor. The resulting is of order : not a large detectability but an arithmetic artefact, assembled entirely from bins where the "signal" is rounding error. A plausible is a number near unity, so this one is at least visibly wrong; the same mechanism at milder decay produces one that is not.

## insert at paragraph 307

**After:** Jia Y, Harman M. An analysis and survey of the development of mutation testing. IEEE Trans Softw Eng. 2011;37(5):649–678. doi:10.1109/TSE.2010.62.

**Inserted:** Claessen K, Hughes J. QuickCheck: a lightweight tool for random testing of Haskell programs. Proc. ACM SIGPLAN Int. Conf. Functional Programming (ICFP). 2000:268–279. doi:10.1145/351240.351266.

## insert at paragraph 307

**After:** Jia Y, Harman M. An analysis and survey of the development of mutation testing. IEEE Trans Softw Eng. 2011;37(5):649–678. doi:10.1109/TSE.2010.62.

**Inserted:** Chen TY, Kuo FC, Liu H, et al. Metamorphic testing: a review of challenges and opportunities. ACM Comput Surv. 2018;51(1):4. doi:10.1145/3143561.

## insert at paragraph 307

**After:** Jia Y, Harman M. An analysis and survey of the development of mutation testing. IEEE Trans Softw Eng. 2011;37(5):649–678. doi:10.1109/TSE.2010.62.

**Inserted:** Oberkampf WL, Roy CJ. Verification and Validation in Scientific Computing. Cambridge: Cambridge University Press; 2010.

## insert at paragraph 307

**After:** Jia Y, Harman M. An analysis and survey of the development of mutation testing. IEEE Trans Softw Eng. 2011;37(5):649–678. doi:10.1109/TSE.2010.62.

**Inserted:** Song K-H, Shan C, Xu G, et al. Phantom evaluation of small-pixel effect in ultra-high-resolution photon-counting CT: noise texture and high-contrast spatial resolution. J Appl Clin Med Phys. 2026;27:e70776. doi:10.1002/acm2.70776.

## replace at paragraph 4

**Was:** 1Institute of One, LISIT Co., Ltd., Tokyo, Japan; yamamoto@lisit.jp; ORCID 0000-0001-9211-1071

**Now:** 1 Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan; yamamoto@lisit.jp; ORCID 0000-0001-9211-1071

## replace at paragraph 7

**Was:** Task-based image quality assessment — the modulation transfer function, the noise power spectrum, the noise-equivalent quanta and model observers — fails by returning a plausible wrong number rather than an error, and the regression test most implementations carry cannot tell a plausible right answer from a plausible wrong one, because the stored reference was recorded from the defective code. We injected six defects into a validated implementation of that chain through a severity dial that recovers the correct pipeline exactly at zero. A self-consistency regression test detected none of the six. Four internal identities, which need no ground truth, and two closed-form references, which need a phantom whose answer is known, together detected all six, in every case at or before the severity at which the reported detectability index became wrong by more than 5%. Neither family sufficed alone: each detected three of six, and peak errors in a reported reached 90%. Run unmodified on measured ACR phantom projections across seven reconstruction kernels, the identities transferred intact — Parseval held to — but their tolerances did not, and the strongest apodisation drove the noise dynamic range to within 0.6% of the threshold beyond which a prewhitening observer must refuse to answer.:

**Now:** Task-based image quality assessment — the modulation transfer function, the noise power spectrum, the noise-equivalent quanta and model observers — fails by returning a plausible wrong number rather than an error, and the regression test most implementations carry cannot tell a plausible right answer from a plausible wrong one, because the stored reference was recorded from the defective code. We injected six defects into a validated implementation of that chain through a severity dial that recovers the correct pipeline exactly at zero. A self-consistency regression test detected none of the six. Four internal identities, which need no ground truth, and two closed-form references, which need a phantom whose answer is known, together detected all six, in every case at or before the severity at which the reported detectability index became wrong by more than 5%. Neither family sufficed alone: each detected three of six, and peak errors in a reported reached 90%. Run unmodified on measured ACR phantom projections across seven reconstruction kernels, the three identities that can be evaluated without ground truth transferred intact — Parseval held to — but their tolerances did not, and the strongest apodisation drove the noise dynamic range to within 0.6% of the threshold beyond which a prewhitening observer should return no value at all rather than a computed one, because has ceased to be numerically meaningful.

## insert at paragraph 11

**After:** Task-based assessment — judging an imaging system by how well a specified observer performs a specified detection or discrimination task, rather than by a generic fidelity metric — is the accepted framework for evaluating medical imaging systems [1,2]. Its physical ingredients are individually standardised: the modulation transfer function (MTF), classically measured from a slanted edge by the presampled-MTF method formalised in ISO 12233 [3], and the noise power spectrum (NPS) and detective-quantum-efficiency formalism standardised for digital X-ray detectors in IEC 62220-1 [4]. Its observer theory is mature [1,5,7,8], its relation to dose and patient risk has been set out in detail [11], its practice from physical measurement through to model observers has been reviewed for CT [12], and its use in computed tomography has been consolidated in AAPM Task Group 233 [9]. The quantity tying the physics to the task is the noise-equivalent quanta, , because the ideal-observer detectability of a known signal imaged through a linear system is exactly an integral of NEQ against the signal’s power spectrum.

**Inserted:** A phantom is an object of known composition imaged in place of a patient; a synthetic phantom is one that exists only as an array of numbers, generated rather than scanned, so that the answer the estimator should return is known analytically. The distinction matters throughout this paper: a synthetic phantom supplies ground truth, and a physical one does not.

## insert at paragraph 24

**After:** Internal identities must hold for algebraic reasons, whatever the data. That the integral of the NPS over the frequency plane equals the pixel variance is not an empirical fact about a particular phantom; it is Parseval’s theorem. Identities of this kind need no ground truth, and therefore continue to work on measured patient data where no truth exists.

**Inserted:** Neither idea is new to software engineering, and it is worth naming what they are. A check that must hold whatever the input is a property in the sense of property-based testing [18], where properties are asserted over generated inputs rather than over stored examples; the internal identities here are properties of that kind, with the algebra of the imaging chain supplying the property instead of a programmer's intuition. A check comparing two routes to the same quantity, or the same computation under a transformation that should leave the answer predictable, is a metamorphic relation [19], the standard response to the oracle problem — the situation, exactly this paper's situation, where correct output cannot be recognised by inspection. Verification practice for computational science has made the same argument from the scientific side [20].

## insert at paragraph 24

**After:** Internal identities must hold for algebraic reasons, whatever the data. That the integral of the NPS over the frequency plane equals the pixel variance is not an empirical fact about a particular phantom; it is Parseval’s theorem. Identities of this kind need no ground truth, and therefore continue to work on measured patient data where no truth exists.

**Inserted:** What this paper adds is not the idea but its content for one chain: which relations exist in task-based image quality, what each detects, what it costs, and — the part that cannot be borrowed — the finding that the two families are not interchangeable.

## replace at paragraph 35

**Was:** The MTF estimator forms the edge-spread function, differentiates to the line-spread function, and transforms, analytically dividing out the two transfer functions the estimator itself introduces: the bin-average boxcar, , and the central-difference derivative, , where is the ESF bin width. It additionally corrects each bin from its measured mean sample position to the bin centre. The NPS estimator detrends each region of interest and normalises so that the integral of the NPS over the frequency plane equals the pixel variance as an exact identity.

**Now:** The MTF estimator forms the edge-spread function — the ESF, the mean profile across the edge obtained by projecting every pixel onto the edge normal and binning far below the pixel pitch, which is what the edge's tilt buys — differentiates it to the line-spread function, the LSF, by a central difference between adjacent bins, and transforms the LSF, analytically dividing out the two transfer functions the estimator itself introduces: the bin-average boxcar, , and the central-difference derivative, , where is the ESF bin width. It additionally corrects each bin from its measured mean sample position to the bin centre. The NPS estimator detrends each region of interest and normalises so that the integral of the NPS over the frequency plane equals the pixel variance as an exact identity.

## insert at paragraph 83

**After:** A check that fires only after the answer is already wrong is not a guard, so the comparison of these two severities, and not the mere fact of detection, is the endpoint.

**Inserted:** Each tolerance is set from the estimator's own reproducibility on the correct pipeline rather than chosen to make a check succeed: the measured residual over the 64 realisations is taken as the noise floor and the tolerance placed an order of magnitude above it, as listed in Table 1. A tolerance below that floor yields a check that fires on correct code, which is discussed in Section 4.6.

## replace at paragraph 85

**Was:** To establish that the chain behaves as required outside a synthetic model, the same code was run on measured ACR phantom projections from LDCT-and-Projection-data [10]. The ACR accreditation phantom is an established vehicle for measuring MTF and NPS on a clinical scanner [16], which is why it was chosen (The Cancer Imaging Archive, CC BY 4.0). Nothing about the acquisition is simulated: one set of measured projections was reconstructed seven times with progressively stronger apodisation — a bare ramp, then Hann windows at cutoffs 1.00, 0.80, 0.60, 0.45, 0.35 and 0.25 — which moves the MTF and the NPS together exactly as changing a scanner’s reconstruction kernel does. The MTF, NPS, NEQ and model-observer detectabilities were then read off with the same estimators used throughout.

**Now:** To establish that the chain behaves as required outside a synthetic model, the same code was run on measured ACR phantom projections from LDCT-and-Projection-data [10]. The ACR accreditation phantom is an established vehicle for measuring MTF and NPS on a clinical scanner [16], which is why it was chosen (The Cancer Imaging Archive, CC BY 4.0). Nothing about the acquisition is simulated: one set of measured projections was reconstructed seven times with progressively stronger apodisation — a bare ramp, then Hann windows at cutoffs 1.00, 0.80, 0.60, 0.45, 0.35 and 0.25 — which moves the MTF and the NPS together exactly as changing a scanner's reconstruction kernel does. The MTF, NPS, NEQ and model-observer detectabilities were then read off with the same estimators used throughout the study.

## replace at paragraph 102

**Was:** Table 2. Six injected defects against seven checks. Detection severity is the smallest at which a check fires; material severity is the smallest at which the reported is wrong by more than 5%. The seventh check, the self-consistency regression test, fired on none of the six and so appears nowhere in the caught by column.

**Now:** Table 2. Six injected defects against seven checks. Detection severity is the smallest at which a check fires; material severity is the smallest at which the reported is wrong by more than 5%. The seventh check, the self-consistency regression test, fired on none of the six and so appears nowhere in the caught by column. Boldface in that column marks a check that is an internal identity — one needing no phantom and no ground truth, and therefore still available on measured patient data. A defect whose entry carries no bold was caught only against an object whose answer was known in advance.

## replace at paragraph 218

**Was:** Strengthening the apodisation reduces resolution and noise together, as it must. Ideal-observer detectability rises monotonically from 1.87 to 2.57 across the sweep: for this low-contrast task the noise reduction outweighs the resolution loss throughout the range tested. The efficiency of the non-prewhitening eye-filter observer relative to the ideal observer rises threefold over the same sweep, from 0.111 to 0.331 — the inefficient observer benefits from smoothing far more than the efficient one does, because smoothing performs part of the noise-weighting the inefficient observer cannot perform for itself.

**Now:** Strengthening the apodisation reduces resolution and noise together, as it must. That the two move together under a change of reconstruction is the ordinary behaviour of the chain, and it is measured the same way on newer detectors: a recent phantom study of ultra-high-resolution photon-counting CT reports noise texture and high-contrast resolution as the paired quantities that a change of pixel size moves [21], which is the same coupling seen here under a change of kernel. The checks in this paper are stated on those quantities rather than on any particular detector, and so apply to that setting unchanged. Ideal-observer detectability rises monotonically from 1.87 to 2.57 across the sweep: for this low-contrast task the noise reduction outweighs the resolution loss throughout the range tested. The efficiency of the non-prewhitening eye-filter observer relative to the ideal observer rises threefold over the same sweep, from 0.111 to 0.331 — the inefficient observer benefits from smoothing far more than the efficient one does, because smoothing performs part of the noise-weighting the inefficient observer cannot perform for itself.

## replace at paragraph 222

**Was:** Table 4. Internal identities evaluated on measured ACR phantom data. The two closed-form references cannot appear here: neither the true MTF nor the true NPS of a clinical scanner is known analytically.

**Now:** Table 4. Internal identities evaluated on measured ACR phantom data. Three of the four appear here. The two closed-form references cannot: neither the true MTF nor the true NPS of a clinical scanner is known analytically. The fourth identity, bridge, cannot either, because its two routes stop sharing a noise model once the noise is measured rather than specified (Sections 3.8 and 4.6).

## replace at paragraph 286

**Was:** Data Availability Statement: All code — the phantom generators, the physical and observer estimators, the injection study (paper/make_injection_study.py) and the test suite — is openly available at https://github.com/Institute-of-One/taskiq-core under the MIT licence and archived on Zenodo (concept DOI 10.5281/zenodo.21422924). Every number in this article is written to paper/figures/injection.json and paper/results/acr_atlas.json by the scripts that produce the figures, so the text and the figures cannot diverge. The real-scanner projections are the ACR_Phantom series of LDCT-and-Projection-data [10], available from The Cancer Imaging Archive under CC BY 4.0.

**Now:** The synthetic arm — the phantom generators, the physical and observer estimators, the injection study (paper/make_injection_study.py) and the test suite — is openly available at &lt;https://github.com/Institute-of-One/taskiq-core&gt; under the MIT licence and archived on Zenodo (version DOI 10.5281/zenodo.21422924 for v0.4.0, the archived snapshot behind every synthetic number here; concept DOI 10.5281/zenodo.21422923 resolves to the latest version). Every number in that arm is written to paper/figures/injection.json by the script that produces Figure 4, so the text and the figure cannot diverge.

## insert at paragraph 286

**After:** Data Availability Statement: All code — the phantom generators, the physical and observer estimators, the injection study (paper/make_injection_study.py) and the test suite — is openly available at https://github.com/Institute-of-One/taskiq-core under the MIT licence and archived on Zenodo (concept DOI 10.5281/zenodo.21422924). Every number in this article is written to paper/figures/injection.json and paper/results/acr_atlas.json by the scripts that produce the figures, so the text and the figures cannot diverge. The real-scanner projections are the ACR_Phantom series of LDCT-and-Projection-data [10], available from The Cancer Imaging Archive under CC BY 4.0.

**Inserted:** The real-scanner arm requires a second package, and neither reproduces it alone. Reading DICOM-CT-PD projections, restoring acquisition order from headers, single-slice rebinning and filtered backprojection with selectable apodisation are in ldct-io (&lt;https://github.com/Institute-of-One/ldct-io&gt;, MIT); the NPS, NEQ and observer estimators applied to those reconstructions are in taskiq-core. Tables 3 and 4 and Figure 5 are written to results/acr_atlas.json by examples/acr_atlas.py in ldct-io, which requires both packages in one environment. The projections themselves are the ACR_Phantom series of LDCT-and-Projection-data [10], available from The Cancer Imaging Archive under CC BY 4.0 and not redistributed here; the path to a local copy is supplied through the LDCT_IO_DATA environment variable.

## replace at paragraph 287

**Was:** Acknowledgments: Generative AI (Claude, Anthropic) was used as a tool for code scaffolding, test drafting, figure generation and manuscript drafting, as disclosed in Section 2.7. The author is solely accountable for the content and independently verified every result. No AI system is an author. This disclosure follows ICMJE and COPE guidance.

**Now:** Generative AI (Claude, Anthropic) was used as a tool for code scaffolding, test drafting, figure generation and manuscript drafting, as disclosed in Section 2.8. The author is solely accountable for the content and independently verified every result. No AI system is an author. This disclosure follows ICMJE and COPE guidance.
