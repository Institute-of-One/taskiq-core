# Changes to apply to the journal-formatted manuscript

Base file: `jimaging-4539482- peer review.docx` (the preliminarily formatted version sent by the
editorial office). Apply these edits **in that file**, in Word, and keep its styles.

**Do not rebuild the document.** It carries 162 native Word equations and 39
MDPI paragraph styles; replacing paragraphs wholesale destroys both.

39 edits. Each gives the text to find and the text to put in its place.
Highlight each replacement in yellow so the reviewers can see what changed.

---

## 1. REPLACE — near paragraph 4

**Find this paragraph:**

> $^{1}$ Institute of One, LISIT Co., Ltd., Tokyo, Japan; yamamoto@lisit.jp; ORCID 0000-0001-9211-1071

**Replace the whole of it with:**

> $^{1}$ Institute of One, LISIT Co., Ltd., Tokyo 150-0044, Japan; yamamoto@lisit.jp; ORCID 0000-0001-9211-1071

## 2. REPLACE — near paragraph 7

**Find this paragraph:**

> Task-based image quality assessment — the modulation transfer function, the noise power spectrum, the noise-equivalent quanta and model observers — fails by returning a plausible wrong number rather than an error, and the regression test most implementations carry cannot tell a plausible right answer from a plausible wrong one, because the stored reference was recorded from the defective code. We injected six defects into a validated implementation of that chain through a severity dial that recovers the correct pipeline exactly at zero. A self-consistency regression test detected none of the six. Four internal identities, which need no ground truth, and two closed-form references, which need a phantom whose answer is known, together detected all six, in every case at or before the severity at which the reported detectability index $d'$ became wrong by more than 5%. Neither family sufficed alone: each detected three of six, and peak errors in a reported $d'$ reached 90%. Run unmodified on measured ACR phantom projections across seven reconstruction kernels, the identities transferred intact — Parseval held to $4\times10^{-16}$ — but their tolerances did not, and the strongest apodisation drove the noise dynamic range to within 0.6% of the threshold beyond which a prewhitening observer must refuse to answer.

**Replace the whole of it with:**

> Task-based image quality assessment — the modulation transfer function, the noise power spectrum, the noise-equivalent quanta and model observers — fails by returning a plausible wrong number rather than an error, and the regression test most implementations carry cannot tell a plausible right answer from a plausible wrong one, because the stored reference was recorded from the defective code. We injected six defects into a validated implementation of that chain through a severity dial that recovers the correct pipeline exactly at zero. A self-consistency regression test detected none of the six. Four internal identities, which need no ground truth, and two closed-form references, which need a phantom whose answer is known, together detected all six, in every case at or before the severity at which the reported detectability index $d'$ became wrong by more than 5%. Neither family sufficed alone: each detected three of six, and peak errors in a reported $d'$ reached 90%. Run unmodified on measured ACR phantom projections across seven reconstruction kernels, the three identities that can be evaluated without ground truth transferred intact — Parseval held to $4\times10^{-16}$ — but their tolerances did not, and the strongest apodisation drove the noise dynamic range to within 0.6% of the threshold beyond which a prewhitening observer should return no value at all rather than a computed one, because $1/\mathrm{NPS}$ has ceased to be numerically meaningful.

## 3. INSERT — near paragraph 10

**Find this paragraph:**

> Task-based assessment — judging an imaging system by how well a specified observer performs a specified detection or discrimination task, rather than by a generic fidelity metric — is the accepted framework for evaluating medical imaging systems [1,2]. Its physical ingredients are individually standardised: the modulation transfer function (MTF), classically measured from a slanted edge by the presampled-MTF method formalised in ISO 12233 [3], and the noise power spectrum (NPS) and detective-quantum-efficiency formalism standardised for digital X-ray detectors in IEC 62220-1 [4]. Its observer theory is mature [1,5,7,8], its relation to dose and patient risk has been set out in detail [11], its practice from physical measurement through to model observers has been reviewed for CT [12], and its use in computed tomography has been consolidated in AAPM Task Group 233 [9]. The quantity tying the physics to the task is the noise-equivalent quanta, $\mathrm{NEQ} = \mathrm{MTF}^2/\mathrm{NPS}$, because the ideal-observer detectability of a known signal imaged through a linear system is exactly an integral of NEQ against the signal's power spectrum.

**Insert the following immediately after it, as a new paragraph:**

> Detectability here is the index $d'$, the separation between the observer's response to signal-present and signal-absent images divided by the standard deviation of that response. It is dimensionless: $d' = 1$ means the two distributions are one standard deviation apart, and $d' \approx 2$ corresponds to roughly 92% correct in a two-alternative forced choice. For the ideal prewhitening observer it is computed in closed form from the signal and the noise spectrum rather than by simulating decisions.

## 4. INSERT — near paragraph 10

**Find this paragraph:**

> Task-based assessment — judging an imaging system by how well a specified observer performs a specified detection or discrimination task, rather than by a generic fidelity metric — is the accepted framework for evaluating medical imaging systems [1,2]. Its physical ingredients are individually standardised: the modulation transfer function (MTF), classically measured from a slanted edge by the presampled-MTF method formalised in ISO 12233 [3], and the noise power spectrum (NPS) and detective-quantum-efficiency formalism standardised for digital X-ray detectors in IEC 62220-1 [4]. Its observer theory is mature [1,5,7,8], its relation to dose and patient risk has been set out in detail [11], its practice from physical measurement through to model observers has been reviewed for CT [12], and its use in computed tomography has been consolidated in AAPM Task Group 233 [9]. The quantity tying the physics to the task is the noise-equivalent quanta, $\mathrm{NEQ} = \mathrm{MTF}^2/\mathrm{NPS}$, because the ideal-observer detectability of a known signal imaged through a linear system is exactly an integral of NEQ against the signal's power spectrum.

**Insert the following immediately after it, as a new paragraph:**

> A phantom is an object of known composition imaged in place of a patient; a synthetic phantom is one that exists only as an array of numbers, generated rather than scanned, so that the answer the estimator should return is known analytically. The distinction matters throughout this paper: a synthetic phantom supplies ground truth, and a physical one does not.

## 5. REPLACE — near paragraph 15

**Find this paragraph:**

> A slanted-edge MTF routine locates each edge-profile sample in the bin it falls into, but uses the bin centre as its position. The mean sample position inside a bin is not the bin centre, and the resulting position jitter biases the estimate. The bias depends on the edge angle, so it is invisible to anyone who tests at one angle. A prewhitening observer weights by $1/\mathrm{NPS}$. Handed a noise model whose power decays below floating-point underflow, it returns a detectability of order $10^{29}$, assembled entirely from frequency bins where the "signal" is rounding error. * A soft-edged disk phantom, blurred by applying a one-dimensional edge profile radially rather than by an exact two-dimensional convolution, gains $\pi\sigma^2$ of area. The detectable signal energy then depends on the blur without any indication that it does, so every conclusion drawn about resolution is contaminated by a change in the signal itself.

**Replace the whole of it with:**

> A slanted-edge MTF routine locates each edge-profile sample in the bin it falls into, but uses the bin centre as its position. The mean sample position inside a bin is not the bin centre, and the resulting position jitter biases the estimate. The bias depends on the edge angle, so it is invisible to anyone who tests at one angle. A prewhitening observer weights by $1/\mathrm{NPS}$. Handed a noise model whose power decays below floating-point underflow — that is, where the computed NPS falls below the smallest number the arithmetic can represent and is stored as a denormal or as zero — it weights those bins by $1/\mathrm{NPS}$ and so multiplies them by an enormous factor. The resulting $d'$ is of order $10^{29}$: not a large detectability but an arithmetic artefact, assembled entirely from bins where the "signal" is rounding error. A plausible $d'$ is a number near unity, so this one is at least visibly wrong; the same mechanism at milder decay produces one that is not. * A soft-edged disk phantom, blurred by applying a one-dimensional edge profile radially rather than by an exact two-dimensional convolution, gains $\pi\sigma^2$ of area. The detectable signal energy then depends on the blur without any indication that it does, so every conclusion drawn about resolution is contaminated by a change in the signal itself.

## 6. INSERT — near paragraph 23

**Find this paragraph:**

> Internal identities must hold for algebraic reasons, whatever the data. That the integral of the NPS over the frequency plane equals the pixel variance is not an empirical fact about a particular phantom; it is Parseval's theorem. Identities of this kind need no ground truth, and therefore continue to work on measured patient data where no truth exists. Closed-form references compare an estimate to the analytic answer for an object constructed so that the answer is known: an analytically blurred edge whose presampled MTF is exactly $\exp(-2\pi^2\sigma^2 f^2)$, or white noise of known variance whose spectrum is exactly $\sigma^2\,\Delta x\,\Delta y$. These are stronger, and they require a phantom.

**Insert the following immediately after it, as a new paragraph:**

> Neither idea is new to software engineering, and it is worth naming what they are. A check that must hold whatever the input is a property in the sense of property-based testing [18], where properties are asserted over generated inputs rather than over stored examples; the internal identities here are properties of that kind, with the algebra of the imaging chain supplying the property instead of a programmer's intuition. A check comparing two routes to the same quantity, or the same computation under a transformation that should leave the answer predictable, is a metamorphic relation [19], the standard response to the oracle problem — the situation, exactly this paper's situation, where correct output cannot be recognised by inspection. Verification practice for computational science has made the same argument from the scientific side [20].

## 7. INSERT — near paragraph 23

**Find this paragraph:**

> Internal identities must hold for algebraic reasons, whatever the data. That the integral of the NPS over the frequency plane equals the pixel variance is not an empirical fact about a particular phantom; it is Parseval's theorem. Identities of this kind need no ground truth, and therefore continue to work on measured patient data where no truth exists. Closed-form references compare an estimate to the analytic answer for an object constructed so that the answer is known: an analytically blurred edge whose presampled MTF is exactly $\exp(-2\pi^2\sigma^2 f^2)$, or white noise of known variance whose spectrum is exactly $\sigma^2\,\Delta x\,\Delta y$. These are stronger, and they require a phantom.

**Insert the following immediately after it, as a new paragraph:**

> What this paper adds is not the idea but its content for one chain: which relations exist in task-based image quality, what each detects, what it costs, and — the part that cannot be borrowed — the finding that the two families are not interchangeable.

## 8. REPLACE — near paragraph 34

**Find this paragraph:**

> The MTF estimator forms the edge-spread function, differentiates to the line-spread function, and transforms, analytically dividing out the two transfer functions the estimator itself introduces: the bin-average boxcar, $\mathrm{sinc}(fh)$, and the central-difference derivative, $\mathrm{sinc}(2fh)$, where $h$ is the ESF bin width. It additionally corrects each bin from its measured mean sample position to the bin centre. The NPS estimator detrends each region of interest and normalises so that the integral of the NPS over the frequency plane equals the pixel variance as an exact identity.

**Replace the whole of it with:**

> The MTF estimator forms the edge-spread function — the ESF, the mean profile across the edge obtained by projecting every pixel onto the edge normal and binning far below the pixel pitch, which is what the edge's tilt buys — differentiates it to the line-spread function, the LSF, by a central difference between adjacent bins, and transforms the LSF, analytically dividing out the two transfer functions the estimator itself introduces: the bin-average boxcar, $\mathrm{sinc}(fh)$, and the central-difference derivative, $\mathrm{sinc}(2fh)$, where $h$ is the ESF bin width. It additionally corrects each bin from its measured mean sample position to the bin centre. The NPS estimator detrends each region of interest and normalises so that the integral of the NPS over the frequency plane equals the pixel variance as an exact identity.

## 9. REPLACE — near paragraph 62

**Find this paragraph:**

> Two points deserve emphasis. First, bridge compares two routes to the same number — the prewhitening observer applied to the imaged signal, and the integral of NEQ against the object's power spectrum — that share no code path but are, under the discrete conventions used here, the same integral rearranged. It is therefore an exact identity rather than an approximation, and holds to zero on the reference pipeline. It is only an identity when both routes use the same noise model; comparing routes that disagree about the noise tests nothing but that disagreement. Second, dynamic_range excludes the DC bin, which mean-detrending drives to $\sim10^{-31}$ by construction. That is bookkeeping, not a decayed spectrum, and reading it as one causes the check to fire on every field including white noise.

**Replace the whole of it with:**

> Two points deserve emphasis. First, the bridge check states that the two routes to ideal-observer detectability agree:

## 10. INSERT — near paragraph 61

**Find this paragraph:**

> Tolerances are not chosen for convenience. Each is set from the estimator's own measured reproducibility on the correct pipeline, with an order of magnitude of margin: the residual of mtf_closed_form on a correct run is $4.9\times10^{-6}$, so its tolerance is $5\times10^{-5}$; the residual of nps_closed_form is $3.6\times10^{-2}$ against a tolerance of $0.25$; parseval and bridge hold to $2.2\times10^{-16}$ and exactly zero respectively. A tolerance set tighter than the estimator's reproducibility produces a check that fires on correct code, which is not a sensitive guard but a broken one — a failure mode we encountered and discuss in Section 4.6.

**Insert the following immediately after it, as a new paragraph:**

> where $S(f)$ is the Fourier transform of the signal, and the check is the relative difference $|d'^2_{\text{NEQ}} - d'^2_{\text{PW}}| / d'^2_{\text{PW}}$. With $\mathrm{NEQ} = \mathrm{MTF}^2/\mathrm{NPS}$ the two integrands are the same expression rearranged, which is why the check is an identity rather than an approximation. It compares two routes to the same number — the prewhitening observer applied to the imaged signal, and the integral of NEQ against the object's power spectrum — that share no code path but are, under the discrete conventions used here, the same integral rearranged. It is therefore an exact identity rather than an approximation, and holds to zero on the reference pipeline. It is only an identity when both routes use the same noise model; comparing routes that disagree about the noise tests nothing but that disagreement. Second, dynamic_range excludes the DC bin. Subtracting the mean from each region of interest sets the zero-frequency component to zero up to rounding, so the DC bin holds a value of order $10^{-31}$ — the residue of that subtraction, not a measurement. Including it would make the ratio of largest to smallest NPS value enormous for any field, white noise included, and the check would fire on correct code every time. The exclusion is bookkeeping about how the estimator works, not a claim about the spectrum.

## 11. REPLACE — near paragraph 66

**Find this paragraph:**

> Each defect is applied to the correct pipeline through a severity $\alpha \in [0,1]$ constructed so that $\alpha = 0$ recovers the correct pipeline exactly. Nothing is rewritten to break it; the defect is injected from outside the library.

**Replace the whole of it with:**

> Each defect is applied to the correct pipeline through a severity $\alpha \in [0,1]$ constructed so that $\alpha = 0$ recovers the correct pipeline exactly. Severity is an exact parameter of the injection, not an estimate of anything: it is the interpolation weight between the correct implementation and the defective one, defined separately for each defect in the list below and computed rather than measured. A severity dial is that parameter used as a continuous control, which is what makes the experiment possible — a defect that can only be present or absent gives one data point, whereas one that can be turned up from nothing gives a curve, and the curve is where the comparison between detection and materiality lives. Nothing is rewritten to break it; the defect is injected from outside the library.

## 12. INSERT — near paragraph 76

**Find this paragraph:**

> A check that fires only after the answer is already wrong is not a guard, so the comparison of these two severities, and not the mere fact of detection, is the endpoint.

**Insert the following immediately after it, as a new paragraph:**

> The grid, and what it can and cannot resolve. Every defect is evaluated on the same eleven-point grid, $\alpha \in \{0, 0.1, 0.2, \ldots, 1.0\}$, with 64 noise realisations at each point and the random streams fixed by seed so that a rerun reproduces the table exactly. Seven of the eight detections in Table 2 occur at $\alpha = 0.1$, which is the smallest non-zero severity examined. That is a property of the grid as much as of the checks: these checks fire at or below a tenth of full severity, and this experiment cannot say how much below, because it never looked. The claim made here is therefore that detection precedes materiality, which the grid does resolve, and not that any particular detection threshold has been measured, which it does not.

## 13. INSERT — near paragraph 76

**Find this paragraph:**

> A check that fires only after the answer is already wrong is not a guard, so the comparison of these two severities, and not the mere fact of detection, is the endpoint.

**Insert the following immediately after it, as a new paragraph:**

> Each tolerance is set from the estimator's own reproducibility on the correct pipeline rather than chosen to make a check succeed: the measured residual over the 64 realisations is taken as the noise floor and the tolerance placed an order of magnitude above it, as listed in Table 1. A tolerance below that floor yields a check that fires on correct code, which is discussed in Section 4.6.

## 14. REPLACE — near paragraph 78

**Find this paragraph:**

> To establish that the chain behaves as required outside a synthetic model, the same code was run on measured ACR phantom projections from LDCT-and-Projection-data [10]. The ACR accreditation phantom is an established vehicle for measuring MTF and NPS on a clinical scanner [16], which is why it was chosen (The Cancer Imaging Archive, CC BY 4.0). Nothing about the acquisition is simulated: one set of measured projections was reconstructed seven times with progressively stronger apodisation — a bare ramp, then Hann windows at cutoffs 1.00, 0.80, 0.60, 0.45, 0.35 and 0.25 — which moves the MTF and the NPS together exactly as changing a scanner's reconstruction kernel does. The MTF, NPS, NEQ and model-observer detectabilities were then read off with the same estimators used throughout.

**Replace the whole of it with:**

> To establish that the chain behaves as required outside a synthetic model, the same code was run on measured ACR phantom projections from LDCT-and-Projection-data [10]. The ACR accreditation phantom is an established vehicle for measuring MTF and NPS on a clinical scanner [16], which is why it was chosen (The Cancer Imaging Archive, CC BY 4.0). Nothing about the acquisition is simulated: one set of measured projections was reconstructed seven times with progressively stronger apodisation — a bare ramp, then Hann windows at cutoffs 1.00, 0.80, 0.60, 0.45, 0.35 and 0.25 — which moves the MTF and the NPS together exactly as changing a scanner's reconstruction kernel does. The MTF, NPS, NEQ and model-observer detectabilities were then read off with the same estimators used throughout the study.

## 15. REPLACE — near paragraph 79

**Find this paragraph:**

> ### 2.7 Use of generative AI

**Replace the whole of it with:**

> ### 2.7 Implementation

## 16. REPLACE — near paragraph 80

**Find this paragraph:**

> Code scaffolding and refactoring, test drafting, figure and script generation, and manuscript drafting were assisted by a large language model (Claude, Anthropic). The author independently re-executed every numerical result reported here and verified all figures, equations and claims against the code. No AI system is an author.

**Replace the whole of it with:**

> The estimators, the phantoms and the observers are taskiq-core, a pure-Python package depending only on NumPy and SciPy, with Matplotlib for figures. It contains no DICOM handling and no patient data by design, which is what allows every quantity in it to be checked against a closed form. The MTF, NPS, NEQ and observer routines are the ones named in Section 2.2; the injection study is a single script, paper/make_injection_study.py, that imports them unmodified and applies each defect through the severity dial rather than by editing the library. Reconstruction from real projection data is not in that package but in ldct-io, for the same reason: the archive, its private tags and its geometry have no business inside a library whose correctness is established analytically. The test suite runs on Python 3.10 to 3.12 in continuous integration, and asserts the identities of Section 4.2 on the correct pipeline as well as the study's own preconditions.

## 17. INSERT — near paragraph 76

**Find this paragraph:**

> A check that fires only after the answer is already wrong is not a guard, so the comparison of these two severities, and not the mere fact of detection, is the endpoint.

**Insert the following immediately after it, as a new paragraph:**

> ### 2.8 Use of generative AI

## 18. INSERT — near paragraph 76

**Find this paragraph:**

> A check that fires only after the answer is already wrong is not a guard, so the comparison of these two severities, and not the mere fact of detection, is the endpoint.

**Insert the following immediately after it, as a new paragraph:**

> A large language model (Claude, Anthropic) was used as a tool. Concretely: it drafted initial versions of the estimator and phantom routines and of the test suite, wrote the figure and study scripts, refactored code the author had written, and drafted and edited manuscript text. It did not choose which defects to inject, did not set any tolerance, and did not decide what the results mean.

## 19. INSERT — near paragraph 76

**Find this paragraph:**

> A check that fires only after the answer is already wrong is not a guard, so the comparison of these two severities, and not the mere fact of detection, is the endpoint.

**Insert the following immediately after it, as a new paragraph:**

> The relationship between that assistance and this paper's subject is not incidental and is stated plainly here. Three of the six defects studied were not invented for the experiment: they were real errors present in drafted code — the bin-centre position error, the radially-blurred disk, and the missing noise floor — found by the closed-form checks described here and only then turned into a controlled injection. The checks were the means of verifying the assistance, which is the argument of the paper applied to its own production. The author independently re-executed every numerical result reported here and verified all figures, equations and claims against the code. No AI system is an author.

## 20. REPLACE — near paragraph 91

**Find this paragraph:**

> Table 2. Six injected defects against seven checks. Detection severity is the smallest $\alpha$ at which a check fires; material severity is the smallest at which the reported $d'$ is wrong by more than 5%. The seventh check, the self-consistency regression test, fired on none of the six and so appears nowhere in the caught by column.

**Replace the whole of it with:**

> Table 2. Six injected defects against seven checks. Detection severity is the smallest $\alpha$ at which a check fires; material severity is the smallest at which the reported $d'$ is wrong by more than 5%. The seventh check, the self-consistency regression test, fired on none of the six and so appears nowhere in the caught by column. Boldface in that column marks a check that is an internal identity — one needing no phantom and no ground truth, and therefore still available on measured patient data. A defect whose entry carries no bold was caught only against an object whose answer was known in advance.

## 21. REPLACE — near paragraph 90

**Find this paragraph:**

> Figure 4. What each check sees. Left: the injected severity at which each check first fires, grey where it never does; the rightmost column is the self-consistency regression test, grey for every defect. The white rules separate internal identities (left) from closed-form references (centre) and from the regression control (right). Right: the relative error each defect produces in a reported $d'$, against the 5% materiality threshold (dashed).

**Replace the whole of it with:**

> Figure 4. What each check sees. (a) The injected severity at which each check first fires, printed in the cell and shown by colour, grey where the check never fires; the rightmost column is the self-consistency regression test, grey for every defect. The white rules separate internal identities (left) from closed-form references (centre) and from the regression control (right). (b) The relative error each defect produces in a reported $d'$, against the 5% materiality threshold (dashed).

## 22. REPLACE — near paragraph 205

**Find this paragraph:**

> Figure 5. The same chain on measured ACR phantom projections, with the reconstruction kernel swept from a bare ramp through Hann apodisation at cutoffs 1.00 to 0.25. Nothing about the acquisition is simulated; the same projections are reconstructed seven ways.

**Replace the whole of it with:**

> Figure 5. The same chain on measured ACR phantom projections, with the reconstruction kernel swept from a bare ramp through Hann apodisation at cutoffs 1.00 to 0.25. (a) measured MTF; (b) measured NPS; (c) NEQ; (d) detectability for the ideal and the non-prewhitening eye-filter observer against MTF$_{50}$. Nothing about the acquisition is simulated; the same projections are reconstructed seven ways.

## 23. REPLACE — near paragraph 206

**Find this paragraph:**

> Strengthening the apodisation reduces resolution and noise together, as it must. Ideal-observer detectability rises monotonically from 1.87 to 2.57 across the sweep: for this low-contrast task the noise reduction outweighs the resolution loss throughout the range tested. The efficiency of the non-prewhitening eye-filter observer relative to the ideal observer rises threefold over the same sweep, from 0.111 to 0.331 — the inefficient observer benefits from smoothing far more than the efficient one does, because smoothing performs part of the noise-weighting the inefficient observer cannot perform for itself.

**Replace the whole of it with:**

> Strengthening the apodisation reduces resolution and noise together, as it must. That the two move together under a change of reconstruction is the ordinary behaviour of the chain, and it is measured the same way on newer detectors: a recent phantom study of ultra-high-resolution photon-counting CT reports noise texture and high-contrast resolution as the paired quantities that a change of pixel size moves [21], which is the same coupling seen here under a change of kernel. The checks in this paper are stated on those quantities rather than on any particular detector, and so apply to that setting unchanged. Ideal-observer detectability rises monotonically from 1.87 to 2.57 across the sweep: for this low-contrast task the noise reduction outweighs the resolution loss throughout the range tested. The efficiency of the non-prewhitening eye-filter observer relative to the ideal observer rises threefold over the same sweep, from 0.111 to 0.331 — the inefficient observer benefits from smoothing far more than the efficient one does, because smoothing performs part of the noise-weighting the inefficient observer cannot perform for itself.

## 24. REPLACE — near paragraph 209

**Find this paragraph:**

> The three internal identities that can be evaluated without ground truth were run on all seven real-scanner reconstructions (Table 4).

**Replace the whole of it with:**

> Three of the four internal identities were run on all seven real-scanner reconstructions (Table 4). The fourth, bridge, is absent for a reason specific to measured data rather than by omission: it compares a prewhitening observer using the measured noise spectrum against an NEQ route that requires an analytic noise scalar, and on a physical scanner those two routes no longer share a noise model. What it then measures is that disagreement, not the correctness of the pipeline, and Section 4.6 gives the residual it produces. The claim of transfer in this paper is therefore made for three identities, not four.

## 25. REPLACE — near paragraph 210

**Find this paragraph:**

> Table 4. Internal identities evaluated on measured ACR phantom data. The two closed-form references cannot appear here: neither the true MTF nor the true NPS of a clinical scanner is known analytically.

**Replace the whole of it with:**

> Table 4. Internal identities evaluated on measured ACR phantom data. Three of the four appear here. The two closed-form references cannot: neither the true MTF nor the true NPS of a clinical scanner is known analytically. The fourth identity, bridge, cannot either, because its two routes stop sharing a noise model once the noise is measured rather than specified (Sections 3.8 and 4.6).

## 26. REPLACE — near paragraph 231

**Find this paragraph:**

> The four internal identities are cheap, need no phantom, and can be asserted inside any implementation of this chain:

**Replace the whole of it with:**

> Six checks, in two families. Nothing else in this list is a check.

## 27. REPLACE — location not found automatically

**Find this paragraph:**

> 1. $\int \mathrm{NPS}(f)\,df$ equals the pixel variance of the data the NPS was estimated from, to floating-point tolerance. 2. Ideal-observer $d'$ computed through NEQ equals $d'$ computed by the prewhitening observer, when both use the same noise model. 3. The integral of a blurred signal equals the integral of the unblurred signal. 4. The NPS dynamic range, excluding DC, stays within the range where $1/\mathrm{NPS}$ is meaningful; a prewhitening observer should refuse rather than return a number when it does not. Section 3.8 shows this is not a theoretical precaution: strong apodisation on a real scanner approaches the threshold closely enough that the check decides real cases.

**Replace the whole of it with:**

> Family A — the four internal identities. Cheap, needing no phantom, and assertable inside any implementation of this chain:

## 28. REPLACE — near paragraph 236

**Find this paragraph:**

> The two closed-form references require a phantom and catch what the identities cannot:

**Replace the whole of it with:**

> A1. $\int \mathrm{NPS}(f)\,df$ equals the pixel variance of the data the NPS was estimated from, to floating-point tolerance.

## 29. REPLACE — near paragraph 237

**Find this paragraph:**

> 5. The presampled MTF of an analytically blurred edge equals $\exp(-2\pi^2\sigma^2f^2)$. 6. The NPS of white noise of known variance equals $\sigma^2\,\Delta x\,\Delta y$.

**Replace the whole of it with:**

> A2. Ideal-observer $d'$ computed through NEQ equals $d'$ computed by the prewhitening observer, when both use the same noise model.

## 30. REPLACE — near paragraph 239

**Find this paragraph:**

> The injection study adds two methodological items to these six. Check 5 must be evaluated over a sweep of edge angles, not one, because the bias it detects is not monotone in angle and can be an order of magnitude larger between two angles half a degree apart. And every tolerance must be set from the estimator's measured reproducibility in the configuration actually in use: too loose and it misses the defect, too tight and it fires on correct code, and the correct value differs by four orders of magnitude between synthetic and measured data for the same identity.

**Replace the whole of it with:**

> A3. The integral of a blurred signal equals the integral of the unblurred signal.

## 31. INSERT — near paragraph 229

**Find this paragraph:**

> We do not claim that published detectability values are commonly wrong; we have not surveyed them and this study cannot support such a claim. What it does support is narrower and still uncomfortable: for six defects of a kind that occur in practice, the standard apparatus provides zero detection power, and the errors they produce in a reported $d'$ reach 90%.

**Insert the following immediately after it, as a new paragraph:**

> A4. The NPS dynamic range, excluding DC, stays within the range where $1/\mathrm{NPS}$ is meaningful; a prewhitening observer should refuse rather than return a number when it does not. Section 3.8 shows this is not a theoretical precaution: strong apodisation on a real scanner approaches the threshold closely enough that the check decides real cases.

## 32. INSERT — near paragraph 229

**Find this paragraph:**

> We do not claim that published detectability values are commonly wrong; we have not surveyed them and this study cannot support such a claim. What it does support is narrower and still uncomfortable: for six defects of a kind that occur in practice, the standard apparatus provides zero detection power, and the errors they produce in a reported $d'$ reach 90%.

**Insert the following immediately after it, as a new paragraph:**

> Family B — the two closed-form references. These require a phantom, and catch what the identities cannot:

## 33. INSERT — near paragraph 229

**Find this paragraph:**

> We do not claim that published detectability values are commonly wrong; we have not surveyed them and this study cannot support such a claim. What it does support is narrower and still uncomfortable: for six defects of a kind that occur in practice, the standard apparatus provides zero detection power, and the errors they produce in a reported $d'$ reach 90%.

**Insert the following immediately after it, as a new paragraph:**

> B1. The presampled MTF of an analytically blurred edge equals $\exp(-2\pi^2\sigma^2f^2)$.

## 34. INSERT — near paragraph 229

**Find this paragraph:**

> We do not claim that published detectability values are commonly wrong; we have not surveyed them and this study cannot support such a claim. What it does support is narrower and still uncomfortable: for six defects of a kind that occur in practice, the standard apparatus provides zero detection power, and the errors they produce in a reported $d'$ reach 90%.

**Insert the following immediately after it, as a new paragraph:**

> B2. The NPS of white noise of known variance equals $\sigma^2\,\Delta x\,\Delta y$.

## 35. INSERT — near paragraph 229

**Find this paragraph:**

> We do not claim that published detectability values are commonly wrong; we have not surveyed them and this study cannot support such a claim. What it does support is narrower and still uncomfortable: for six defects of a kind that occur in practice, the standard apparatus provides zero detection power, and the errors they produce in a reported $d'$ reach 90%.

**Insert the following immediately after it, as a new paragraph:**

> The injection study adds two methodological requirements to these six checks. Check B1 must be evaluated over a sweep of edge angles, not one, because the bias it detects is not monotone in angle and can be an order of magnitude larger between two angles half a degree apart. And every tolerance must be set from the estimator's measured reproducibility in the configuration actually in use: too loose and it misses the defect, too tight and it fires on correct code, and the correct value differs by four orders of magnitude between synthetic and measured data for the same identity.

## 36. REPLACE — location not found automatically

**Find this paragraph:**

> All code — the phantom generators, the physical and observer estimators, the injection study (paper/make_injection_study.py) and the test suite — is openly available at <https://github.com/Institute-of-One/taskiq-core> under the MIT licence and archived on Zenodo (concept DOI 10.5281/zenodo.21422924). Every number in this article is written to paper/figures/injection.json and paper/results/acr_atlas.json by the scripts that produce the figures, so the text and the figures cannot diverge. The real-scanner projections are the ACR_Phantom series of LDCT-and-Projection-data [10], available from The Cancer Imaging Archive under CC BY 4.0.

**Replace the whole of it with:**

> The synthetic arm — the phantom generators, the physical and observer estimators, the injection study (paper/make_injection_study.py) and the test suite — is openly available at <https://github.com/Institute-of-One/taskiq-core> under the MIT licence and archived on Zenodo (version DOI 10.5281/zenodo.21422924 for v0.4.0, the archived snapshot behind every synthetic number here; concept DOI 10.5281/zenodo.21422923 resolves to the latest version). Every number in that arm is written to paper/figures/injection.json by the script that produces Figure 4, so the text and the figure cannot diverge.

## 37. INSERT — location not found automatically

**Find this paragraph:**

> Not applicable.

**Insert the following immediately after it, as a new paragraph:**

> The real-scanner arm requires a second package, and neither reproduces it alone. Reading DICOM-CT-PD projections, restoring acquisition order from headers, single-slice rebinning and filtered backprojection with selectable apodisation are in ldct-io (<https://github.com/Institute-of-One/ldct-io>, MIT); the NPS, NEQ and observer estimators applied to those reconstructions are in taskiq-core. Tables 3 and 4 and Figure 5 are written to results/acr_atlas.json by examples/acr_atlas.py in ldct-io, which requires both packages in one environment. The projections themselves are the ACR_Phantom series of LDCT-and-Projection-data [10], available from The Cancer Imaging Archive under CC BY 4.0 and not redistributed here; the path to a local copy is supplied through the LDCT_IO_DATA environment variable.

## 38. REPLACE — near paragraph 254

**Find this paragraph:**

> Generative AI (Claude, Anthropic) was used as a tool for code scaffolding, test drafting, figure generation and manuscript drafting, as disclosed in Section 2.7. The author is solely accountable for the content and independently verified every result. No AI system is an author. This disclosure follows ICMJE and COPE guidance.

**Replace the whole of it with:**

> Generative AI (Claude, Anthropic) was used as a tool for code scaffolding, test drafting, figure generation and manuscript drafting, as disclosed in Section 2.8. The author is solely accountable for the content and independently verified every result. No AI system is an author. This disclosure follows ICMJE and COPE guidance.

## 39. REPLACE — near paragraph 257

**Find this paragraph:**

> 1. Barrett HH, Myers KJ. Foundations of Image Science. Hoboken, NJ: Wiley-Interscience; 2004. 2. International Commission on Radiation Units and Measurements. Medical Imaging — The Assessment of Image Quality. ICRU Report 54. Bethesda, MD: ICRU; 1996. 3. International Organization for Standardization. Photography — Electronic still picture imaging — Resolution and spatial frequency responses. ISO 12233:2017. Geneva: ISO; 2017. 4. International Electrotechnical Commission. Medical electrical equipment — Characteristics of digital X-ray imaging devices — Part 1-1: Determination of the detective quantum efficiency. IEC 62220-1-1:2015. Geneva: IEC; 2015. 5. Myers KJ, Barrett HH. Addition of a channel mechanism to the ideal-observer model. J Opt Soc Am A. 1987;4(12):2447–2457. doi:10.1364/JOSAA.4.002447. 6. Burgess AE. Statistically defined backgrounds: performance of a modified nonprewhitening observer model. J Opt Soc Am A. 1994;11(4):1237–1242. doi:10.1364/JOSAA.11.001237. 7. Barrett HH, Yao J, Rolland JP, Myers KJ. Model observers for assessment of image quality. Proc Natl Acad Sci USA. 1993;90(21):9758–9765. doi:10.1073/pnas.90.21.9758. 8. He X, Park S. Model observers in medical imaging research. Theranostics. 2013;3(10):774–786. doi:10.7150/thno.5138. 9. Samei E, Bakalyar D, Boedeker K, et al. Performance evaluation of computed tomography systems: Summary of AAPM Task Group 233. Med Phys. 2019;46(11). doi:10.1002/mp.13763. 10. Moen TR, Chen B, Holmes DR III, et al. Low-dose CT image and projection dataset. Med Phys. 2021;48(2):902–911. doi:10.1002/mp.14594. 11. Barrett HH, Myers KJ, Hoeschen C, Kupinski MA, Little MP. Task-based measures of image quality and their relation to radiation dose and patient risk. Phys Med Biol. 2015;60(2):R1–R75. doi:10.1088/0031-9155/60/2/R1. 12. Verdun FR, Racine D, Ott JG, et al. Image quality in CT: From physical measurements to model observers. Phys Med. 2015;31(8):823–843. doi:10.1016/j.ejmp.2015.08.007. 13. Peng RD. Reproducible research in computational science. Science. 2011;334(6060):1226–1227. doi:10.1126/science.1213847. 14. Soergel DAW. Rampant software errors may undermine scientific results. F1000Research. 2015;3:303. doi:10.12688/f1000research.5930.2. 15. Merali Z. Computational science: ...Error. Nature. 2010;467(7317):775–777. doi:10.1038/467775a. 16. Friedman SN, Fung GSK, Siewerdsen JH, et al. A simple approach to measure computed tomography (CT) modulation transfer function (MTF) and noise-power spectrum (NPS) using the American College of Radiology (ACR) accreditation phantom. Med Phys. 2013;40(5):051907. doi:10.1118/1.4800795. 17. Jia Y, Harman M. An analysis and survey of the development of mutation testing. IEEE Trans Softw Eng. 2011;37(5):649–678. doi:10.1109/TSE.2010.62.

**Replace the whole of it with:**

> 1. Barrett HH, Myers KJ. Foundations of Image Science. Hoboken, NJ: Wiley-Interscience; 2004. 2. International Commission on Radiation Units and Measurements. Medical Imaging — The Assessment of Image Quality. ICRU Report 54. Bethesda, MD: ICRU; 1996. 3. International Organization for Standardization. Photography — Electronic still picture imaging — Resolution and spatial frequency responses. ISO 12233:2017. Geneva: ISO; 2017. 4. International Electrotechnical Commission. Medical electrical equipment — Characteristics of digital X-ray imaging devices — Part 1-1: Determination of the detective quantum efficiency. IEC 62220-1-1:2015. Geneva: IEC; 2015. 5. Myers KJ, Barrett HH. Addition of a channel mechanism to the ideal-observer model. J Opt Soc Am A. 1987;4(12):2447–2457. doi:10.1364/JOSAA.4.002447. 6. Burgess AE. Statistically defined backgrounds: performance of a modified nonprewhitening observer model. J Opt Soc Am A. 1994;11(4):1237–1242. doi:10.1364/JOSAA.11.001237. 7. Barrett HH, Yao J, Rolland JP, Myers KJ. Model observers for assessment of image quality. Proc Natl Acad Sci USA. 1993;90(21):9758–9765. doi:10.1073/pnas.90.21.9758. 8. He X, Park S. Model observers in medical imaging research. Theranostics. 2013;3(10):774–786. doi:10.7150/thno.5138. 9. Samei E, Bakalyar D, Boedeker K, et al. Performance evaluation of computed tomography systems: Summary of AAPM Task Group 233. Med Phys. 2019;46(11). doi:10.1002/mp.13763. 10. Moen TR, Chen B, Holmes DR III, et al. Low-dose CT image and projection dataset. Med Phys. 2021;48(2):902–911. doi:10.1002/mp.14594. 11. Barrett HH, Myers KJ, Hoeschen C, Kupinski MA, Little MP. Task-based measures of image quality and their relation to radiation dose and patient risk. Phys Med Biol. 2015;60(2):R1–R75. doi:10.1088/0031-9155/60/2/R1. 12. Verdun FR, Racine D, Ott JG, et al. Image quality in CT: From physical measurements to model observers. Phys Med. 2015;31(8):823–843. doi:10.1016/j.ejmp.2015.08.007. 13. Peng RD. Reproducible research in computational science. Science. 2011;334(6060):1226–1227. doi:10.1126/science.1213847. 14. Soergel DAW. Rampant software errors may undermine scientific results. F1000Research. 2015;3:303. doi:10.12688/f1000research.5930.2. 15. Merali Z. Computational science: ...Error. Nature. 2010;467(7317):775–777. doi:10.1038/467775a. 16. Friedman SN, Fung GSK, Siewerdsen JH, et al. A simple approach to measure computed tomography (CT) modulation transfer function (MTF) and noise-power spectrum (NPS) using the American College of Radiology (ACR) accreditation phantom. Med Phys. 2013;40(5):051907. doi:10.1118/1.4800795. 17. Jia Y, Harman M. An analysis and survey of the development of mutation testing. IEEE Trans Softw Eng. 2011;37(5):649–678. doi:10.1109/TSE.2010.62. 18. Claessen K, Hughes J. QuickCheck: a lightweight tool for random testing of Haskell programs. Proc. ACM SIGPLAN Int. Conf. Functional Programming (ICFP). 2000:268–279. doi:10.1145/351240.351266. 19. Chen TY, Kuo FC, Liu H, et al. Metamorphic testing: a review of challenges and opportunities. ACM Comput Surv. 2018;51(1):4. doi:10.1145/3143561. 20. Oberkampf WL, Roy CJ. Verification and Validation in Scientific Computing. Cambridge: Cambridge University Press; 2010. 21. Song K-H, Shan C, Xu G, et al. Phantom evaluation of small-pixel effect in ultra-high-resolution photon-counting CT: noise texture and high-contrast spatial resolution. J Appl Clin Med Phys. 2026;27:e70776. doi:10.1002/acm2.70776.
