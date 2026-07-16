r"""The detection task, and the three figures of merit that must agree on it.

The headline here is an identity. For an equal-variance Gaussian test statistic,

    PC(2AFC) = AUC = Phi(d' / sqrt(2))

and the three quantities are computed by three genuinely different routes: ``d'`` from the
separation of the score means, AUC by counting correctly ordered pairs, and PC by running a
forced-choice experiment. They have no shared code path, so their agreeing is evidence, not
tautology.

Then the end-to-end test: build an SKE/BKE experiment, hand its *analytic* NPS to an
observer, and check that the ``d'`` the observer predicts in closed form is the ``d'`` you
actually measure from the scores — and that the forced-choice experiment you run on those
same scores lands where that ``d'`` says it should. That chain, phantom → NPS → observer →
trials → PC, is the whole pipeline this project exists to make trustworthy.
"""

from __future__ import annotations

import numpy as np
import pytest

from taskiq_core import (
    auc_from_scores,
    burgess_eye_filter,
    d_prime_from_pc,
    d_prime_from_scores,
    ideal_linear,
    make_disk_signal,
    nps_2d,
    npwe,
    pc_from_d_prime,
    roc_curve,
    score_images,
    ske_bke_trials,
    two_afc,
)

SPACING = 0.1
SIZE = 64
NOISE_SD = 20.0


def _signal(contrast: float = 6.0) -> np.ndarray:
    return make_disk_signal(
        SIZE, radius_mm=0.8, contrast=contrast, spacing=SPACING, edge_sigma_mm=0.1
    ).image.astype(np.float64)


def _gaussian_scores(d_prime: float, n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Two equal-variance Gaussian score samples separated by exactly ``d_prime``."""
    rng = np.random.default_rng(seed)
    return rng.normal(d_prime, 1.0, n), rng.normal(0.0, 1.0, n)


def _standard_error(d_prime: float, n: int) -> float:
    return float(np.sqrt(2.0 / n + d_prime**2 / (4.0 * n)))


# --------------------------------------------------------------------------------------
# the identity
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("true_d", [0.5, 1.0, 2.0, 3.0])
def test_pc_equals_auc_equals_phi_of_d_prime_over_root_two(true_d):
    """PC(2AFC) = AUC = Phi(d'/sqrt2), by three independent routes, on Gaussian scores.

    d' comes from the score means and variances; AUC from a rank statistic; PC from an actual
    forced-choice experiment. Nothing is shared between the three, so agreement is a real check
    on all of them.
    """
    n = 200_000
    present, absent = _gaussian_scores(true_d, n, seed=int(true_d * 100))

    measured_d = d_prime_from_scores(present, absent)
    measured_auc = auc_from_scores(present, absent)
    measured_pc = two_afc(present, absent, pairing="all")
    predicted = float(pc_from_d_prime(true_d))

    assert measured_d == pytest.approx(true_d, abs=4 * _standard_error(true_d, n))
    assert measured_auc == pytest.approx(predicted, abs=0.005)
    assert measured_pc == pytest.approx(predicted, abs=0.005)
    # PC with all-pairs pairing IS the Mann-Whitney AUC: same number, by construction.
    assert measured_pc == measured_auc


def test_pc_and_d_prime_conversions_round_trip():
    d = np.array([0.25, 0.5, 1.0, 2.0, 4.0])
    np.testing.assert_allclose(d_prime_from_pc(pc_from_d_prime(d)), d, rtol=1e-12)
    # Sanity anchors: d' = 0 is chance; d' = 2 is the textbook 0.9214.
    assert float(pc_from_d_prime(0.0)) == pytest.approx(0.5)
    assert float(pc_from_d_prime(2.0)) == pytest.approx(0.9214, abs=1e-4)


def test_d_prime_from_pc_refuses_a_saturated_experiment():
    """PC = 1 means the experiment saturated; d' is not identifiable, so this raises."""
    for bad in (0.0, 1.0, 1.2, -0.1):
        with pytest.raises(ValueError, match="strictly inside"):
            d_prime_from_pc(bad)


def test_sequential_pairing_is_noisier_but_unbiased():
    """A really-run forced-choice experiment estimates the same PC, with more scatter.

    Note *how much* more: a constant factor (~1.4 here), not an order of magnitude. Averaging
    over all n_p * n_a pairs does not divide the variance by n, because the pairs are not
    independent — every one of them reuses an image. Both estimators are O(1/sqrt(n)).
    """
    true_d = 1.5
    predicted = float(pc_from_d_prime(true_d))

    sequential, all_pairs = [], []
    for rep in range(60):
        present, absent = _gaussian_scores(true_d, 400, seed=500 + rep)
        sequential.append(two_afc(present, absent, pairing="sequential"))
        all_pairs.append(two_afc(present, absent, pairing="all"))
    sequential, all_pairs = np.array(sequential), np.array(all_pairs)

    assert sequential.mean() == pytest.approx(predicted, abs=0.01)  # unbiased
    assert all_pairs.mean() == pytest.approx(predicted, abs=0.01)  # and so is all-pairs
    assert sequential.std() > 1.2 * all_pairs.std()  # noisier, but only modestly


def test_sequential_pairing_needs_equal_samples():
    present, absent = _gaussian_scores(1.0, 100, seed=1)
    with pytest.raises(ValueError, match="equally many"):
        two_afc(present, absent[:50], pairing="sequential")
    # all-pairs handles unequal samples fine
    assert 0.0 < two_afc(present, absent[:50], pairing="all") < 1.0


# --------------------------------------------------------------------------------------
# ROC
# --------------------------------------------------------------------------------------


def test_roc_curve_area_equals_the_rank_auc_exactly():
    """Trapezoidal area under the sampled ROC == Mann-Whitney AUC, ties included.

    They are computed completely differently — one sweeps thresholds, the other counts ordered
    pairs — so this pins down the tie handling in both. Collapsing tied scores into one ROC
    point is what makes it exact rather than merely close.
    """
    present, absent = _gaussian_scores(1.5, 5000, seed=7)
    roc = roc_curve(present, absent)

    trapezoid = float(np.trapezoid(roc.tpr, roc.fpr))
    assert trapezoid == pytest.approx(roc.auc, abs=1e-12)
    assert roc.auc == pytest.approx(auc_from_scores(present, absent), abs=1e-12)


def test_roc_curve_is_well_formed():
    present, absent = _gaussian_scores(2.0, 1000, seed=3)
    roc = roc_curve(present, absent)

    assert roc.fpr[0] == 0.0 and roc.tpr[0] == 0.0
    assert roc.fpr[-1] == pytest.approx(1.0)
    assert roc.tpr[-1] == pytest.approx(1.0)
    assert np.all(np.diff(roc.fpr) >= -1e-12)  # monotone
    assert np.all(np.diff(roc.tpr) >= -1e-12)
    assert roc.thresholds[0] == np.inf
    assert roc.fpr.shape == roc.tpr.shape == roc.thresholds.shape


def test_roc_of_identical_distributions_is_the_diagonal():
    """No signal, no discrimination: AUC = 0.5, and ties are handled without blowing up."""
    same = np.zeros(50)
    roc = roc_curve(same, same)
    assert roc.auc == pytest.approx(0.5)
    assert float(np.trapezoid(roc.tpr, roc.fpr)) == pytest.approx(0.5)


# --------------------------------------------------------------------------------------
# the experiment
# --------------------------------------------------------------------------------------


def test_ske_bke_trials_are_what_they_claim_to_be():
    signal = _signal()
    trials = ske_bke_trials(signal, 100, SPACING, NOISE_SD, seed=0, background=100.0)

    assert trials.present.shape == (100, SIZE, SIZE)
    assert trials.absent.shape == (100, SIZE, SIZE)
    assert trials.shape == (SIZE, SIZE)
    assert trials.n_trials == 100

    # Absent images are background + noise; present are the same plus the signal.
    assert trials.absent.mean() == pytest.approx(100.0, abs=0.5)
    assert trials.absent.std() == pytest.approx(NOISE_SD, rel=0.02)
    assert trials.meta["pixel_sd"] == pytest.approx(NOISE_SD, rel=1e-12)
    # The difference of the two class means recovers the signal. Each class mean carries
    # noise of SD sigma/sqrt(n), so their difference carries sigma*sqrt(2/n) per pixel; the
    # largest of 64*64 such deviations sits around 3.6 of those, so 5 is a safe bound.
    recovered = trials.present.mean(axis=0) - trials.absent.mean(axis=0)
    per_pixel_sd = NOISE_SD * np.sqrt(2.0 / 100)
    assert np.abs(recovered - signal).max() < 5.0 * per_pixel_sd


def test_ske_bke_trials_are_bit_reproducible():
    signal = _signal()
    kwargs = dict(
        n_trials=20, spacing=SPACING, noise_sd=NOISE_SD, seed=1234,
        correlation_sigma_mm=0.3, white_floor_sd=5.0,
    )
    a = ske_bke_trials(signal, **kwargs)
    b = ske_bke_trials(signal, **kwargs)
    c = ske_bke_trials(signal, **{**kwargs, "seed": 1235})

    assert a.present.tobytes() == b.present.tobytes()
    assert a.absent.tobytes() == b.absent.tobytes()
    assert a.present.tobytes() != c.present.tobytes()


def test_the_analytic_nps_really_is_the_nps_of_the_generated_noise():
    """The NPS a TrialSet reports is not a model of its noise — it *is* its noise.

    Measure the NPS of the signal-absent images with nps_2d and it must reproduce the closed
    form the TrialSet carries, bin by bin, to within the statistical error of the measurement.
    If this ever drifts, every closed-form d' downstream is being computed for a different
    noise field than the one the observer is actually scoring.
    """
    signal = _signal()
    trials = ske_bke_trials(
        signal, 256, SPACING, NOISE_SD, seed=4, correlation_sigma_mm=0.3, white_floor_sd=6.0
    )
    measured = nps_2d(trials.absent, SPACING)

    truth = np.fft.ifftshift(trials.nps)  # both to fft layout for a bin-by-bin comparison
    est = np.fft.ifftshift(measured.nps)

    # Skip DC, which detrending zeroes in the measurement (the analytic NPS has real power there).
    mask = np.ones_like(truth, dtype=bool)
    mask[0, 0] = False

    # A periodogram bin has 100 % relative SD; averaging 256 realisations cuts it to 1/16.
    ratio = est[mask] / truth[mask]
    assert ratio.mean() == pytest.approx(1.0, rel=0.02)
    assert ratio.std() == pytest.approx(1.0 / np.sqrt(256), rel=0.15)


def test_correlated_noise_reports_its_true_pixel_sd_not_the_prefilter_one():
    """The correlation filter attenuates, so pixel_sd < noise_sd — and meta says so."""
    signal = _signal()
    trials = ske_bke_trials(signal, 64, SPACING, NOISE_SD, seed=2, correlation_sigma_mm=0.3)
    assert trials.meta["pixel_sd"] < NOISE_SD
    assert trials.absent.std() == pytest.approx(trials.meta["pixel_sd"], rel=0.05)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"n_trials": 1}, "n_trials"),
        ({"spacing": 0.0}, "spacing"),
        ({"noise_sd": -1.0}, "noise_sd"),
        ({"correlation_sigma_mm": -1.0}, "correlation_sigma_mm"),
        ({"noise_sd": 0.0}, "no noise at all"),
    ],
)
def test_ske_bke_trials_rejects_bad_arguments(kwargs, message):
    args = {
        "signal": _signal(), "n_trials": 10, "spacing": SPACING,
        "noise_sd": NOISE_SD, "seed": 0, **kwargs,
    }
    with pytest.raises(ValueError, match=message):
        ske_bke_trials(**args)


def test_ske_bke_trials_rejects_a_zero_signal():
    with pytest.raises(ValueError, match="identically zero"):
        ske_bke_trials(np.zeros((SIZE, SIZE)), 10, SPACING, NOISE_SD, seed=0)


# --------------------------------------------------------------------------------------
# end to end: phantom -> NPS -> observer -> trials -> PC
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label, correlation, floor, observer",
    [
        ("white / NPW", 0.0, 0.0, "npw"),
        ("white / NPWE", 0.0, 0.0, "npwe"),
        ("correlated / NPWE", 0.3, 0.0, "npwe"),
        ("correlated+floor / ideal", 0.3, 8.0, "ideal"),
    ],
)
def test_end_to_end_closed_form_d_prime_predicts_the_forced_choice_experiment(
    label, correlation, floor, observer
):
    """The whole chain, checked at both ends.

    An observer is handed the TrialSet's analytic NPS and predicts d' in closed form, with no
    reference to the images. The trials are then actually scored, d' is measured from the
    scores, and a 2AFC experiment is run on them. All three must line up: the predicted d', the
    measured d', and PC = Phi(d'/sqrt2).
    """
    signal = _signal()
    trials = ske_bke_trials(
        signal, 20_000, SPACING, NOISE_SD, seed=17,
        correlation_sigma_mm=correlation, white_floor_sd=floor,
    )

    if observer == "npw":
        result = npwe(trials.signal, trials.nps, trials.spacing)
    elif observer == "npwe":
        result = npwe(
            trials.signal, trials.nps, trials.spacing, eye_filter=burgess_eye_filter(1.0)
        )
    else:
        result = ideal_linear(trials.signal, trials.nps, trials.spacing)

    scores_present = score_images(trials.present, result.template)
    scores_absent = score_images(trials.absent, result.template)

    measured_d = d_prime_from_scores(scores_present, scores_absent)
    se = _standard_error(result.d_prime, trials.n_trials)
    assert abs(measured_d - result.d_prime) < 4.0 * se, (
        f"[{label}] predicted d' = {result.d_prime:.4f}, measured {measured_d:.4f} "
        f"({abs(measured_d - result.d_prime) / se:.1f} SE apart)"
    )

    # And the forced-choice experiment lands where the predicted d' says it must.
    measured_pc = two_afc(scores_present, scores_absent)
    predicted_pc = float(pc_from_d_prime(result.d_prime))
    assert measured_pc == pytest.approx(predicted_pc, abs=0.01)

    # The ROC of the same scores agrees with the same number.
    assert roc_curve(scores_present, scores_absent).auc == pytest.approx(measured_pc, abs=1e-12)


def test_a_trial_set_with_pure_correlated_noise_still_refuses_the_ideal_observer():
    """The dynamic-range trap survives the convenience of TrialSet handing over its own NPS.

    A TrialSet's analytic NPS is exactly right — and for purely Gaussian-correlated noise it is
    exactly the spectrum a prewhitening observer cannot use. Convenience must not smuggle the
    trap back in: it still raises, and still tells you to give the noise a floor.
    """
    trials = ske_bke_trials(_signal(), 10, SPACING, NOISE_SD, seed=0, correlation_sigma_mm=0.3)
    with pytest.raises(ValueError, match="dynamic range"):
        ideal_linear(trials.signal, trials.nps, trials.spacing)

    # Give the same experiment a white floor, as a real detector has, and it works.
    floored = ske_bke_trials(
        _signal(), 10, SPACING, NOISE_SD, seed=0, correlation_sigma_mm=0.3, white_floor_sd=8.0
    )
    assert 0.0 < ideal_linear(floored.signal, floored.nps, floored.spacing).d_prime < 100.0


def test_detectability_rises_with_contrast_in_a_real_experiment():
    """The end-to-end sanity check: a stronger lesion is easier to see, in measured PC."""
    previous_pc = 0.0
    for contrast in (2.0, 4.0, 8.0):
        signal = _signal(contrast)
        trials = ske_bke_trials(signal, 4000, SPACING, NOISE_SD, seed=21)
        result = npwe(trials.signal, trials.nps, trials.spacing)
        pc = two_afc(
            score_images(trials.present, result.template),
            score_images(trials.absent, result.template),
        )
        assert pc > previous_pc
        previous_pc = pc
    assert previous_pc > 0.99  # contrast 8 is easy
