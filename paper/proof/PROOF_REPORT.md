# Proof check: `manuscript.v7-corrected.docx`

## What production left in the file

- tracked insertions: **3**  (authors: ['Shuji Yamamoto'])
- tracked deletions: **3**  (authors: ['Shuji Yamamoto'])
- formatting changes: **0**
- comments: **1**

## Strings that decide the proof

- ok    abstract: the three identities, not all four
- ok    abstract: return no value, not refuse
- ok    affiliation, exactly
- ok    funding statement
- ok    generative AI declared
- ok    ldct-io named
- ok    taskiq-core named
- ok    checklist relabelled A1
- ok    checklist relabelled B2
- ok    section 2.7 Implementation
- ok    section 2.8 generative AI
- ok    abstract overclaim
- ok    unclear 'refuse' wording
- ok    lower-case affiliation
- ok    affiliation's extra comma

## Structure, accepted -> proof

- **FEWER**  equations: 148 -> 146
- ok    display equations: 27 -> 28
- ok    tables: 4 -> 6
- ok    images: 5 -> 5
- reference-list paragraphs (numId 8): 21 -> 0

## Comments from production

### Comment 0 — Shuji Yamamoto

> Restored to "disk" in the three places where it is the name of a defect rather than the English word: this entry, the row label in Table 2, and the Results sentence listing what the internal identities caught. The defect is called "disk" in the released code (paper/make_injection_study.py and taskiq_core/phantoms.py, kind="disk"), alongside sinc, jitter, nps_area, detrend and no_floor, so a reader looking up the Table 2 row in the repository needs the same spelling. Everywhere the word means the shape - disc phantom, disc signal, blurred disc - the British spelling you introduced is right and has been kept.

Anchored on: *disk*

## Tracked changes, paragraph by paragraph

- **in:** `disk—the signal built by interpolating between the exact two-dimensional blurred disc and the one obtained by `
  - deleted: `disc`
  - inserted: `disk`
- **in:** `disk`
  - deleted: `disc`
  - inserted: `disk`
- **in:** `Internal identities caught nps_area (Parseval), disk (conserved signal area) and no_floor (NPS dynamic range)—`
  - deleted: `disc`
  - inserted: `disk`

## Paragraphs that differ from the accepted file: 38 runs

- *replace* — {+Academic+} {+Editors:+} {+Zheyun+} {+Qin+} {+and+} {+Yanyan+} {+Wang+} {+/+} {+Received:+} {+18+} {+August+} {+2026+} {+/+} {+Revised:+} {+07+} {+September+} {+2026+} {+/+} {+Accepted:+} {+10+} {+September+} {+2026+} {+/+} {+Published:+} {+date+} {+/+} {+Copyright:+} {+©+} {+2026+} {+by+} {+the+} {+authors.+} {+Submitted+} {+for+} {+possible+} {+open+} {+access+} {+publication+} {+under+} {+the+} {+terms+} {+and+} {+conditions+} {+of+} {+the+} {+Creative+} {+Commons+} {+Attribution+} {+(CC+} {+BY)+} {+license.+} {+/+} Shuji Yamamoto [-1,*-] / [-1-] Institute of One, LISIT Co., Ltd., Tokyo 15

- *replace* — Task-based image quality [-assessment-] {+assessment—the+} [-—-] [-the-] modulation transfer function, the noise power spectrum, the noise-equivalent quanta and model [-observers-] {+observers—fails+} [-—-] [-fails-] by returning a plausible wrong number rather than an error, and the regression test most implementations carry cannot tell a plausible right answer from a plausible wrong one, because the stored reference was recorded from the defective code. We injected six defects into a validated implementation of that chain through a severity dial that recovers the correct pipeline exactly at 

- *replace* — Task-based {+assessment—judging+} [-assessment-] [-—-] [-judging-] an imaging system by how well a specified observer performs a specified detection or discrimination task, rather than by a generic fidelity [-metric-] {+metric—is+} [-—-] [-is-] the accepted framework for evaluating medical imaging systems [1,2]. Its physical ingredients are individually standardised: the modulation transfer function (MTF), classically measured from a slanted edge by the presampled-MTF method formalised in ISO 12233 [3], and the noise power spectrum (NPS) and detective-quantum-efficiency formalism standardised 

- *replace* — The theory is settled. The implementations are not, and this paper is about the gap between them. The object of study is therefore the chain [-itself-] {+itself—any+} [-—-] [-any-] implementation of [-it-] [-—-] [-rather-] {+it—rather+} than a particular [-program:-] {+programme:+} each defect examined below is a step the standard formulation requires, applied to one instance so that its cost can be measured, and the checks proposed against them are stated so that they can be asserted inside any implementation. / 1.1. The Characteristic Failure [-is-] {+Is+} a Plausible Number / A pipeline ass

- *replace* — A prewhitening observer weights by . Handed a noise model whose power decays below floating-point [-underflow-] {+underflow—that+} [-—-] [-that-] is, where the computed NPS falls below the smallest number the arithmetic can represent and is stored as a denormal or as {+zero—it+} [-zero-] [-—-] [-it-] weights those bins by and so multiplies them by an enormous factor. The resulting is of order : not a large detectability but an arithmetic artefact, assembled entirely from bins where the [-"signal"-] {+“signal”+} is rounding error. A plausible is a number near unity, so this one is at least visi

- *replace* — The standard defence is a regression test: run the pipeline, store the [-output,-] {+output+} and fail the build if the output ever changes. This is a genuinely useful [-discipline-] {+discipline—it+} [-—-] [-it-] catches accidental change, and it makes refactoring safe. It also cannot, in principle, catch any of the three defects above. / The reason is structural rather than incidental. If a defect was present when the reference output was {+recorded—which+} [-recorded-] [-—-] [-which-] is the normal case for a defect that was never {+noticed—then+} [-noticed-] [-—-] [-then-] the stored value

- *replace* — Internal identities must hold for algebraic reasons, whatever the data. That the integral of the NPS over the frequency plane equals the pixel variance is not an empirical fact about a particular phantom; it is Parseval’s theorem. Identities of this kind need no ground [-truth,-] {+truth+} and therefore continue to work on measured patient data where no truth exists. / Neither idea is new to software engineering, and it is worth naming what they are. A check that must hold whatever the input is a property in the sense of property-based testing [18], where properties are asserted over generated

- *replace* — Whether the second kind is worth its {+cost—whether+} [-cost-] [-—-] [-whether-] a synthetic phantom earns its place in a workflow whose object is real [-images-] {+images—is+} [-—-] [-is-] an empirical question that this paper answers.

- *replace* — The finding that the two check families are complementary and individually insufficient, and in [-particular-] {+particular,+} that half of these defects are undetectable without a phantom of known truth. / Two corrected magnitudes for defects previously reported only qualitatively: the angular structure of the bin-centre jitter [-bias,-] {+bias+} and the dependence of the omitted-sinc bias on a free implementation parameter.

- *replace* — The MTF estimator forms the edge-spread [-function-] {+function—the+} [-—-] [-the-] ESF, the mean profile across the edge obtained by projecting every pixel onto the edge normal and binning far below the pixel pitch, which is what the [-edge's-] {+edge’s+} tilt [-buys-] [-—-] [-differentiates-] {+buys—differentiates+} it to the line-spread function, the LSF, by a central difference between adjacent bins, and transforms the LSF, analytically dividing out the two transfer functions the estimator itself introduces: the bin-average boxcar, , and the central-difference derivative, , where is the ES

- *replace* — Six checks were [-implemented,-] {+implemented:+} four internal identities and two closed-form references (Table 1). Each returns a scalar violation magnitude; a check fires when that magnitude exceeds its tolerance.

- *replace* — Tolerances are not chosen for convenience. Each is set from the estimator’s own measured reproducibility on the correct pipeline, with an order of magnitude of margin: the residual of mtf_closed_form on a correct run is , so its tolerance is ; the residual of nps_closed_form is against a tolerance of ; parseval and bridge hold to and exactly [-zero-] {+zero,+} respectively. A tolerance set tighter than the estimator’s reproducibility produces a check that fires on correct code, which is not a sensitive guard but a broken [-one-] {+one—a+} [-—-] [-a-] failure mode we encountered and discuss in 

- *replace* — where is the Fourier transform of the signal, and the check is the relative difference . With the two integrands are the same expression rearranged, which is why the check is an identity rather than an approximation. It compares two routes to the same [-number-] {+number—the+} [-—-] [-the-] prewhitening observer applied to the imaged signal, and the integral of NEQ against the [-object's-] {+object’s+} power [-spectrum-] {+spectrum—that+} [-—-] [-that-] share no code path but are, under the discrete conventions used here, the same integral rearranged. It is therefore an exact identity rather t

- *replace* — The control is the test most implementations actually have. The pipeline is run at a given severity, its output recorded, and the pipeline re-run and compared to that record. Critically, the record is taken from the pipeline as it stands, with the defect already [-present-] {+present—the+} [-—-] [-the-] realistic case for a defect that was never noticed. The pipeline is deterministic, so the comparison is exact by construction. Reporting this as a result rather than asserting it is deliberate: it is the quantitative form of the argument in Section 1.2.

- *replace* — Each defect is applied to the correct pipeline through a severity constructed so that recovers the correct pipeline exactly. Severity is an exact parameter of the injection, not an estimate of anything: it is the interpolation weight between the correct implementation and the defective one, defined separately for each defect in the list below and computed rather than measured. A severity dial is that parameter used as a continuous control, which is what makes the experiment [-possible-] {+possible—a+} [-—-] [-a-] defect that can only be present or absent gives one data point, whereas one that 

- *replace* — For each defect the detection severity is the smallest at which any check fires, and the material severity is the smallest at which the reported [-—-] [-taken-] {+—taken+} as the worse of the prewhitening and NEQ {+routes—differs+} [-routes-] [-—-] [-differs-] from that defect’s own value by more than 5%. Measuring against the defect’s own zero rather than a global reference removes confounds: the jitter sweep varies the edge angle, which changes the estimate slightly even when the correction is applied.

- *replace* — [-Each-] [-tolerance-] [-is-] [-set-] [-from-] [-the-] [-estimator's-] [-own-] [-reproducibility-] [-on-] [-the-] [-correct-] [-pipeline-] [-rather-] [-than-] [-chosen-] [-to-] [-make-] [-a-] [-check-] [-succeed:-] [-the-] [-measured-] [-residual-] [-over-] [-the-] [-64-] [-realisations-] [-is-] [-taken-] [-as-] [-the-] [-noise-] [-floor-] [-and-] [-the-] [-tolerance-] [-placed-] [-an-] [-order-] [-of-] [-magnitude-] [-above-] [-it,-] [-as-] [-listed-] [-in-] [-Table-] [-1.-] [-A-] [-tolerance-] [-below-] [-that-] [-floor-] [-yields-] [-a-] [-check-] [-that-] [-fires-] [-on-] [-correct-] [-cod

- *replace* — {+Each+} {+tolerance+} {+is+} {+set+} {+from+} {+the+} {+estimator’s+} {+own+} {+reproducibility+} {+on+} {+the+} {+correct+} {+pipeline+} {+rather+} {+than+} {+chosen+} {+to+} {+make+} {+a+} {+check+} {+succeed:+} {+the+} {+measured+} {+residual+} {+over+} {+the+} {+64+} {+realisations+} {+is+} {+taken+} {+as+} {+the+} {+noise+} {+floor+} {+and+} {+the+} {+tolerance+} {+placed+} {+an+} {+order+} {+of+} {+magnitude+} {+above+} {+it,+} {+as+} {+listed+} {+in+} {+Table+} {+1.+} {+A+} {+tolerance+} {+below+} {+that+} {+floor+} {+yields+} {+a+} {+check+} {+that+} {+fires+} {+on+} {+correct+} {+cod

- *replace* — The self-consistency control disagreed with itself by at most [-—-] [-exactly-] {+—exactly+} zero, at every severity of every defect. It caught 0 of 6.

- *replace* — Internal identities caught nps_area (Parseval), disk (conserved signal area) and no_floor (NPS dynamic [-range)-] {+range)—3+} [-—-] [-3-] of 6. / Closed-form references caught sinc, jitter and [-detrend-] {+detrend—3+} [-—-] [-3-] of 6.

- *replace* — The practical consequence is the paper’s main claim. Internal identities are the checks that survive contact with measured data, because they need no truth; they are what remains available when the object of study is a patient image. They catch half of these defects. The other {+half—an+} [-half-] [-—-] [-an-] MTF [-biased-] {+biassed+} by its own estimator, an NPS whose level is {+wrong—are+} [-wrong-] [-—-] [-are-] detectable only against an object whose answer is known in advance. Removing the synthetic phantom from a validated workflow does not merely reduce coverage; it removes an entire 

- *replace* — The jitter bias spikes; it does not drift. Sweeping the edge angle from 2° to 20° in 0.5° steps with the bin-centre correction disabled, the maximum absolute MTF error over the band cycles/mm was at 5.0° but only at 4.5° and at [-5.5°-] {+5.5°—a+} [-—-] [-a-] factor of thirty-eight between neighbouring half-degree steps. The worst case over the whole range is 0.32%, not the 1.4% previously reported for this estimator, and the more important correction is structural: the bias is not a smooth function of angle that one could bound by testing the endpoints. It spikes where the sampling geometry b

- *replace* — The study as first written reported that every defect was detected at severity {+zero—an+} [-zero-] [-—-] [-an-] apparently excellent result, and entirely an artefact. Three independent causes were responsible, each of which produced output that read as a finding:

- *replace* — These are recorded because they are the same class of failure the paper is about, occurring one level up: a validation apparatus can return plausible wrong answers exactly as a pipeline can. The regression tests accompanying this study therefore assert the two properties that make it [-meaningful-] {+meaningful—that+} [-—-] [-that-] no check fires on a correct pipeline, and that the self-consistency control never {+fires—rather+} [-fires-] [-—-] [-rather-] than asserting the study’s conclusions.

- *insert* — {+Figure+} {+5.+} {+The+} {+same+} {+chain+} {+on+} {+measured+} {+ACR+} {+phantom+} {+projections,+} {+with+} {+the+} {+reconstruction+} {+kernel+} {+swept+} {+from+} {+a+} {+bare+} {+ramp+} {+through+} {+Hann+} {+apodisation+} {+at+} {+cutoffs+} {+1.00+} {+to+} {+0.25.+} {+(a)+} {+measured+} {+MTF;+} {+(b)+} {+measured+} {+NPS;+} {+(c)+} {+NEQ;+} {+(d)+} {+detectability+} {+for+} {+the+} {+ideal+} {+and+} {+the+} {+non-prewhitening+} {+eye-filter+} {+observer+} {+against+} {+MTF50.+} {+Nothing+} {+about+} {+the+} {+acquisition+} {+is+} {+simulated;+} {+the+} {+same+} {+projections+} {+are+} 

- *replace* — [-MTF-] {+MTF50+} [-(mm)-] {+(mm−1)+}

- *replace* — [-Figure-] [-5.-] [-The-] [-same-] [-chain-] [-on-] [-measured-] [-ACR-] [-phantom-] [-projections,-] [-with-] [-the-] [-reconstruction-] [-kernel-] [-swept-] [-from-] [-a-] [-bare-] [-ramp-] [-through-] [-Hann-] [-apodisation-] [-at-] [-cutoffs-] [-1.00-] [-to-] [-0.25.-] [-(a)-] [-measured-] [-MTF;-] [-(b)-] [-measured-] [-NPS;-] [-(c)-] [-NEQ;-] [-(d)-] [-detectability-] [-for-] [-the-] [-ideal-] [-and-] [-the-] [-non-prewhitening-] [-eye-filter-] [-observer-] [-against-] [-MTF50.-] [-Nothing-] [-about-] [-the-] [-acquisition-] [-is-] [-simulated;-] [-the-] [-same-] [-projections-] [-are-] 

- *replace* — Parseval survives intact. The identity holds to [-—-] [-machine-] {+—machine+} [-precision-] {+precision—on+} [-—-] [-on-] measured projections, exactly as on synthetic data. This is the property that makes internal identities worth having: nothing about the transition from a generated phantom to a physical one weakens [-them,-] {+them+} because they never depended on knowing the answer. / Tolerances do not survive intact. The signal-area residual is throughout, four orders of magnitude above the that the same identity achieves on synthetic data, and constant across every {+kernel—which+} [-ke

- *replace* — 4.1. What [-this-] {+This+} Implies for Reported Studies / The uncomfortable corollary of Section 3.3 is that a large fraction of published model-observer work carries no evidence bearing on the class of defect studied here. Reviews of task-based practice in CT describe the estimators and the observers in detail and say little about how an implementation of them is shown to be correct [12], and the wider evidence on software defects in published science suggests that silence is not because the problem is absent [14,15]. The usual reproducibility [-apparatus-] {+apparatus—a+} [-—-] [-a-] fixed 

- *replace* — Family [-A-] [-—-] [-the-] {+A—the+} four internal identities. Cheap, needing no phantom, and assertable inside any implementation of this chain:

- *replace* — Family [-B-] [-—-] [-the-] {+B—the+} two closed-form references. These require a phantom, and catch what the identities cannot:

- *replace* — The injection study adds two methodological requirements to these six checks. Check B1 must be evaluated over a sweep of edge angles, not one, because the bias it detects is not monotone in angle and can be an order of magnitude larger between two angles half a degree apart. [-And-] {+Additionally,+} every tolerance must be set from the [-estimator's-] {+estimator’s+} measured reproducibility in the configuration actually in use: too loose and it misses the defect, too tight and it fires on correct code, and the correct value differs by four orders of magnitude between synthetic and measured d

- *replace* — Standards documents [3,4] and task-group reports [9] specify what to measure and how, and {+they+} are the appropriate reference for the definitions used here. They do not, and are not intended to, specify how an implementation should establish that it has implemented them correctly. Model-observer methodology reviews [8] treat the estimation of observer performance from data, largely under the assumption that the physical inputs are correct. The present study concerns the layer between: the correctness of the implementation itself, treated as an empirical question with a measurable answer. / 

- *replace* — The pipeline is a linear-systems idealisation: shift-invariant imaging, stationary noise, Gaussian blur, and a signal- and background-known-exactly task, which is the most tractable and least clinically realistic paradigm. The real-scanner arm demonstrates that the chain runs and behaves correctly on measured projections; it is not a validation against a physical standard, since the true MTF and NPS of that scanner are {+unknown—which+} [-unknown-] [-—-] [-which-] is the point of Section 3.4 rather than an oversight. The channelised Hotelling observer has no closed form and is not part of the 

- *replace* — A task-based image quality pipeline that passes its own regression suite has demonstrated stability, not correctness, and for the class of defect studied [-here-] {+here,+} the distinction is total: self-consistency caught none of {+the+} six injected defects, while closed-form and identity-based checks caught all six, in every case at or before the point where the reported detectability became materially wrong. The two families of [-check-] {+checks+} are complementary and neither suffices alone. Half the defects are detectable using identities that need no ground truth and therefore travel t

- *replace* — Institutional Review Board Statement: Not applicable. [-This-] [-study-] [-involved-] [-no-] [-human-] [-participants-] [-and-] [-no-] [-animal-] [-subjects.-] [-The-] [-only-] [-measured-] [-data-] [-are-] [-of-] [-a-] [-physical-] [-quality-assurance-] [-phantom,-] [-obtained-] [-from-] [-a-] [-public-] [-archive-] [-under-] [-an-] [-open-] [-licence.-]

- *replace* — {+Data+} {+Availability+} {+Statement:+} The synthetic {+arm—the+} [-arm-] [-—-] [-the-] phantom generators, the physical and observer estimators, the injection study (paper/make_injection_study.py) and the test [-suite-] {+suite—is+} [-—-] [-is-] openly available at &lt;https://github.com/Institute-of-One/taskiq-core&gt; under the MIT licence and archived on Zenodo (version DOI 10.5281/zenodo.21422924 for v0.4.0, the archived snapshot behind every synthetic number here; concept DOI 10.5281/zenodo.21422923 resolves to the latest version). Every number in that arm is written to paper/figures/in

- *replace* — [-Barrett-] {+Barrett,+} [-HH,-] {+H.H.;+} [-Myers-] {+Myers,+} [-KJ.-] {+K.J.+} Foundations of Image [-Science.-] {+Science;+} {+Wiley-Interscience:+} Hoboken, [-NJ:-] [-Wiley-Interscience;-] {+NJ,+} {+USA,+} 2004. / International Commission on Radiation Units and Measurements. Medical [-Imaging-] {+Imaging—The+} [-—-] [-The-] Assessment of Image Quality. {+In+} ICRU Report [-54.-] {+54;+} {+ICRU:+} Bethesda, [-MD:-] [-ICRU;-] {+MD,+} {+USA,+} 1996. / [-International-] [-Organization-] [-for-] [-Standardization.-] [-Photography-] [-—-] [-Electronic-] [-still-] [-picture-] [-imaging-] [-—-] [-

## Verdict

- equations: 148 -> 146
## Resolved after reading the output

- **equations 148 -> 146 is not a loss.** Production rewrote the Table 3 column header
  `MTF50 (mm-1)` from two inline equations into ordinary subscript and superscript text,
  and turned the hyphen into a true minus. The header reads correctly; the count fell by
  exactly those two. The other differences in the equation census are zero-width spaces
  (U+200B) that production stripped from inside equations that are otherwise identical.
- **The two things known to be wrong upstream are right in the proof.** The abstract is
  the corrected one and neither removed claim survives; the affiliation matches Crossref
  character for character.
- **Moved, not changed.** Table 2 and Figure 5 were moved to follow their first citation,
  which carries "Each tolerance is set" and the Figure 5 caption with them. The prose order
  is intact and the caption text is identical.
- **All 16 reference DOIs survived** the conversion to MDPI's reference style.
- **Accepted as production's style:** closed em dashes, curly apostrophes, British
  spellings (programme, biassed, disc), comma changes, title case in 4.1, and the
  Institutional Review Board statement shortened to "Not applicable." -- the facts it
  dropped are stated in the Methods and the Data Availability Statement.
- **Corrected, with tracked changes and a comment:** "disc" back to "disk" in the three
  places it names the defect -- the defect list entry, the Table 2 row label and the
  Results sentence -- because that is the defect's name in the released code
  (`paper/make_injection_study.py`, `taskiq_core/phantoms.py`). The five places where the
  word means the shape keep production's "disc".

Output verified in `manuscript.v7-corrected.docx`, not taken from the script's log: three
insertions and three deletions, all by Shuji Yamamoto, one comment, 329 paragraphs of
which exactly three differ from the proof as sent, and Word opens it without repair.
