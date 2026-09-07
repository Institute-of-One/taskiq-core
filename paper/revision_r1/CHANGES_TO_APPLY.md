# What is left to apply by hand

Base file: `jimaging-4539482-revised-highlighted.docx`. Everything else in the revision is already in it,
highlighted in yellow. These are the edits that could not be applied by machine,
each because applying it means setting an equation in Word or splitting one
paragraph into several.

Highlight each one in yellow after applying it, as the others already are.

---

## 1. INSERT — paragraph 11

*the new paragraph contains maths, which has to be typed in Word*

**Search for:**  `judging an imaging system by how well a`

**Find this paragraph:**

> Task-based assessment — judging an imaging system by how well a specified observer performs a specified detection or discrimination task, rather than by a generic fidelity metric — is the accepted framework for evaluating medical imaging systems [1,2]. Its physical ingredients are individually standardised: the modulation transfer function (MTF), classically measured from a slanted edge by the presampled-MTF method formalised in ISO 12233 [3], and the noise power spectrum (NPS) and detective-quantum-efficiency formalism standardised for digital X-ray detectors in IEC 62220-1 [4]. Its observer theory is mature [1,5,7,8], its relation to dose and patient risk has been set out in detail [11], its practice from physical measurement through to model observers has been reviewed for CT [12], and its use in computed tomography has been consolidated in AAPM Task Group 233 [9]. The quantity tying the physics to the task is the noise-equivalent quanta, , because the ideal-observer detectability of a known signal imaged through a linear system is exactly an integral of NEQ against the signal’s power spectrum.

**Insert the following immediately after it, as a new paragraph:**

> Detectability here is the index , the separation between the observer's response to signal-present and signal-absent images divided by the standard deviation of that response. It is dimensionless: means the two distributions are one standard deviation apart, and corresponds to roughly 92% correct in a two-alternative forced choice. For the ideal prewhitening observer it is computed in closed form from the signal and the noise spectrum rather than by simulating decisions.

Equations to set in Word: `$d'$`, `$d' = 1$`, `$d' \approx 2$`

## 2. INSERT — paragraph 69

*a display equation, which has to be set in Word*

**Search for:**  `emphasis. First, bridge compares two routes to the`

**Find this paragraph:**

> Two points deserve emphasis. First, bridge compares two routes to the same number — the prewhitening observer applied to the imaged signal, and the integral of NEQ against the object’s power spectrum — that share no code path but are, under the discrete conventions used here, the same integral rearranged. It is therefore an exact identity rather than an approximation, and holds to zero on the reference pipeline. It is only an identity when both routes use the same noise model; comparing routes that disagree about the noise tests nothing but that disagreement. Second, dynamic_range excludes the DC bin, which mean-detrending drives to by construction. That is bookkeeping, not a decayed spectrum, and reading it as one causes the check to fire on every field including white noise.

**Insert the following immediately after it, as a new paragraph:**

> d'^2_{\text{NEQ}} = \int \mathrm{NEQ}(f)\,|S(f)|^2\,df \quad\text{and}\quad d'^2_{\text{PW}} = \int \frac{|S(f)|^2}{\mathrm{NPS}(f)}\,|\mathrm{MTF}(f)|^2\,df,

Equations to set in Word: `$ d'^2_{\text{NEQ}} = \int \mathrm{NEQ}(f)\,|S(f)|^2\,df \quad\text{and}\quad d'^2_{\text{PW}} = \int \frac{|S(f)|^2}{\mathrm{NPS}(f)}\,|\mathrm{MTF}(f)|^2\,df, $`

## 3. INSERT — paragraph 69

*the new paragraph contains maths, which has to be typed in Word*

**Search for:**  `emphasis. First, bridge compares two routes to the`

**Find this paragraph:**

> Two points deserve emphasis. First, bridge compares two routes to the same number — the prewhitening observer applied to the imaged signal, and the integral of NEQ against the object’s power spectrum — that share no code path but are, under the discrete conventions used here, the same integral rearranged. It is therefore an exact identity rather than an approximation, and holds to zero on the reference pipeline. It is only an identity when both routes use the same noise model; comparing routes that disagree about the noise tests nothing but that disagreement. Second, dynamic_range excludes the DC bin, which mean-detrending drives to by construction. That is bookkeeping, not a decayed spectrum, and reading it as one causes the check to fire on every field including white noise.

**Insert the following immediately after it, as a new paragraph:**

> where is the Fourier transform of the signal, and the check is the relative difference . With the two integrands are the same expression rearranged, which is why the check is an identity rather than an approximation. It compares two routes to the same number — the prewhitening observer applied to the imaged signal, and the integral of NEQ against the object's power spectrum — that share no code path but are, under the discrete conventions used here, the same integral rearranged. It is therefore an exact identity rather than an approximation, and holds to zero on the reference pipeline. It is only an identity when both routes use the same noise model; comparing routes that disagree about the noise tests nothing but that disagreement. Second, dynamic_range excludes the DC bin. Subtracting the mean from each region of interest sets the zero-frequency component to zero up to rounding, so the DC bin holds a value of order — the residue of that subtraction, not a measurement. Including it would make the ratio of largest to smallest NPS value enormous for any field, white noise included, and the check would fire on correct code every time. The exclusion is bookkeeping about how the estimator works, not a claim about the spectrum.

Equations to set in Word: `$S(f)$`, `$|d'^2_{\text{NEQ}} - d'^2_{\text{PW}}| / d'^2_{\text{PW}}$`, `$\mathrm{NEQ} = \mathrm{MTF}^2/\mathrm{NPS}$`, `$10^{-31}$`

## 4. REPLACE — paragraph 73

*the replacement's maths does not line up with the equations there*

**Search for:**  `applied to the correct pipeline through a severity`

**Find this paragraph:**

> Each defect is applied to the correct pipeline through a severity constructed so that recovers the correct pipeline exactly. Nothing is rewritten to break it; the defect is injected from outside the library.

**Replace the whole of it with:**

> Each defect is applied to the correct pipeline through a severity constructed so that recovers the correct pipeline exactly. Severity is an exact parameter of the injection, not an estimate of anything: it is the interpolation weight between the correct implementation and the defective one, defined separately for each defect in the list below and computed rather than measured. A severity dial is that parameter used as a continuous control, which is what makes the experiment possible — a defect that can only be present or absent gives one data point, whereas one that can be turned up from nothing gives a curve, and the curve is where the comparison between detection and materiality lives. Nothing is rewritten to break it; the defect is injected from outside the library.

Equations to set in Word: `$\alpha \in [0,1]$`, `$\alpha = 0$`

## 5. INSERT — paragraph 83

*the new paragraph contains maths, which has to be typed in Word*

**Search for:**  `fires only after the answer is already wrong`

**Find this paragraph:**

> A check that fires only after the answer is already wrong is not a guard, so the comparison of these two severities, and not the mere fact of detection, is the endpoint.

**Insert the following immediately after it, as a new paragraph:**

> The grid, and what it can and cannot resolve. Every defect is evaluated on the same eleven-point grid, , with 64 noise realisations at each point and the random streams fixed by seed so that a rerun reproduces the table exactly. Seven of the eight detections in Table 2 occur at , which is the smallest non-zero severity examined. That is a property of the grid as much as of the checks: these checks fire at or below a tenth of full severity, and this experiment cannot say how much below, because it never looked. The claim made here is therefore that detection precedes materiality, which the grid does resolve, and not that any particular detection threshold has been measured, which it does not.

Equations to set in Word: `$\alpha \in \{0, 0.1, 0.2, \ldots, 1.0\}$`, `$\alpha = 0.1$`
