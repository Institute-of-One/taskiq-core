r"""Model observers against analytic ground truth, and against simulation.

The observers are validated two independent ways, and the two ways have to agree:

* **Closed form vs identity.** In white noise the non-prewhitening observer's detectability
  collapses to :math:`d' = \|s\|_2/\sigma` exactly. That single identity ties the NPS
  normalisation of :mod:`taskiq_core.physical` to :math:`d'`, so it is checked at machine
  precision — if the NPS were off by a factor of the pixel area, this is the test that would
  catch it.
* **Closed form vs Monte Carlo.** The Fourier-domain ``d'`` is compared with the empirical
  separation of scores on thousands of simulated SKE/BKE trials. The tolerance is the
  standard error of the empirical estimate, ``sqrt(2/N + d'^2/(4N))``, not a tuned constant.

And the guards get their own tests: the three traps in the module docstring each produce a
*plausible* wrong number, so each has a test that the wrong number is refused.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from taskiq_core import (
    auc_from_scores,
    burgess_eye_filter,
    cho,
    d_prime_from_scores,
    dense_dog_channels,
    gabor_channels,
    ideal_linear,
    laguerre_gauss_channels,
    make_disk_signal,
    make_uniform_phantom,
    nps_2d,
    npwe,
    score_images,
)

SPACING = 0.1
SIZE = 64
SIGMA = 20.0  # white-noise pixel SD
WHITE_NPS = SIGMA**2 * SPACING**2  # the flat NPS level, value^2 mm^2
CORR_SIGMA = 0.3  # mm


def _signal() -> np.ndarray:
    disk = make_disk_signal(SIZE, radius_mm=0.8, contrast=6.0, spacing=SPACING, edge_sigma_mm=0.1)
    return disk.image.astype(np.float64)


def _correlated_nps(floor: float = 0.0):
    """Analytic NPS of Gaussian-correlated noise, optionally over a white floor.

    The floor is what makes the spectrum usable by a prewhitening observer, and it is also
    physically what a detector has: correlated structure on top of a white electronic floor.
    """

    def model(fr: np.ndarray) -> np.ndarray:
        return WHITE_NPS * np.exp(-4.0 * np.pi**2 * CORR_SIGMA**2 * fr**2) + floor

    return model


def _trials(n: int, seed: int, *, correlation_sigma_mm: float = 0.0, white_sd: float = 0.0):
    """``n`` signal-present and ``n`` signal-absent SKE/BKE images."""
    ph = make_uniform_phantom(
        SIZE,
        spacing=SPACING,
        mean=100.0,
        noise_sd=SIGMA,
        seed=seed,
        correlation_sigma_mm=correlation_sigma_mm,
        n_realizations=2 * n,
    )
    images = ph.image.astype(np.float64)
    if white_sd > 0.0:
        extra = make_uniform_phantom(
            SIZE,
            spacing=SPACING,
            mean=0.0,
            noise_sd=white_sd,
            seed=seed + 77_000,
            n_realizations=2 * n,
        )
        images = images + extra.image.astype(np.float64)
    return images[n:] + _signal(), images[:n]


def _standard_error(d_prime: float, n: int) -> float:
    """SE of an empirical d' from ``n`` trials per class: sqrt(2/n + d'^2/(4n))."""
    return float(np.sqrt(2.0 / n + d_prime**2 / (4.0 * n)))


# --------------------------------------------------------------------------------------
# the exact identity
# --------------------------------------------------------------------------------------


def test_npw_in_white_noise_is_exactly_signal_norm_over_sigma():
    """THE identity: in white noise the NPW observer has d' = ||s||_2 / sigma, exactly.

    This is the test that ties the NPS normalisation to detectability. The Fourier
    machinery carries factors of the pixel area through S = A*fft2(s) and du dv = 1/(N A);
    they must cancel exactly, so this holds at machine precision, not approximately. A
    misplaced pixel-area factor in nps_2d would show up here as a factor of 10 in d'.
    """
    s = _signal()
    result = npwe(s, WHITE_NPS, SPACING)  # no eye filter -> plain NPW
    exact = float(np.linalg.norm(s) / SIGMA)

    assert result.name == "npw"
    assert result.d_prime == pytest.approx(exact, rel=1e-12)
    # AUC = Phi(d'/sqrt2), written out independently as 0.5*(1 + erf(d'/2)).
    assert result.auc == pytest.approx(0.5 * (1.0 + math.erf(exact / 2.0)), rel=1e-9)


def test_ideal_equals_npw_when_the_noise_is_white():
    """With a flat NPS there is nothing to prewhiten, so the two observers coincide."""
    s = _signal()
    npw = npwe(s, WHITE_NPS, SPACING)
    ideal = ideal_linear(s, WHITE_NPS, SPACING)
    assert ideal.d_prime == pytest.approx(npw.d_prime, rel=1e-12)


def test_d_prime_scales_as_contrast_over_noise():
    """D' is linear in signal contrast and inverse in noise SD — the analytic scaling."""
    base = make_disk_signal(SIZE, 0.8, 6.0, SPACING).image.astype(np.float64)
    doubled = make_disk_signal(SIZE, 0.8, 12.0, SPACING).image.astype(np.float64)

    d1 = npwe(base, WHITE_NPS, SPACING).d_prime
    d2 = npwe(doubled, WHITE_NPS, SPACING).d_prime
    assert d2 == pytest.approx(2.0 * d1, rel=1e-10)

    quarter_noise = (SIGMA / 2.0) ** 2 * SPACING**2
    d3 = npwe(base, quarter_noise, SPACING).d_prime
    assert d3 == pytest.approx(2.0 * d1, rel=1e-10)


def test_ideal_is_an_upper_bound_on_the_non_prewhitening_observers():
    """The prewhitening observer is optimal, so nothing here may beat it in correlated noise."""
    s = _signal()
    nps = _correlated_nps(floor=0.1 * WHITE_NPS)
    ideal = ideal_linear(s, nps, SPACING).d_prime
    npw = npwe(s, nps, SPACING).d_prime
    eye = npwe(s, nps, SPACING, eye_filter=burgess_eye_filter(1.0)).d_prime

    assert npw < ideal
    assert eye < ideal
    assert 0.0 < (npw / ideal) ** 2 < 1.0  # efficiency is a fraction


# --------------------------------------------------------------------------------------
# closed form vs Monte Carlo
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label, correlation, white_sd, use_eye",
    [
        ("white", 0.0, 0.0, False),
        ("white+eye", 0.0, 0.0, True),
        ("correlated", CORR_SIGMA, 0.0, False),
        ("correlated+eye", CORR_SIGMA, 0.0, True),
    ],
)
def test_npwe_closed_form_matches_monte_carlo(label, correlation, white_sd, use_eye):
    """The Fourier d' must equal the empirical d' from simulated trials, within its SE.

    Two genuinely independent computations: one integrates |S|^2 and the NPS over the
    frequency plane, the other applies the spatial template to 20 000 noisy images and
    measures how far apart the two score distributions land. Agreement means the template,
    the NPS normalisation and the d' definition are all mutually consistent.
    """
    s = _signal()
    nps = WHITE_NPS if correlation == 0.0 else _correlated_nps()
    eye = burgess_eye_filter(1.0) if use_eye else None

    result = npwe(s, nps, SPACING, eye_filter=eye)

    n = 20_000
    present, absent = _trials(n, seed=11, correlation_sigma_mm=correlation, white_sd=white_sd)
    empirical = d_prime_from_scores(
        score_images(present, result.template), score_images(absent, result.template)
    )

    se = _standard_error(result.d_prime, n)
    assert abs(empirical - result.d_prime) < 4.0 * se, (
        f"[{label}] closed form {result.d_prime:.4f} vs Monte Carlo {empirical:.4f} "
        f"({abs(empirical - result.d_prime) / se:.1f} standard errors apart)"
    )


def test_ideal_closed_form_matches_monte_carlo_with_a_noise_floor():
    """The prewhitening observer, on noise it can actually be defined for.

    The noise is Gaussian-correlated *plus* a white floor — which is both what makes the
    ideal observer well-posed (see the dynamic-range guard) and what a real detector has.
    """
    s = _signal()
    white_sd = 8.0
    floor = white_sd**2 * SPACING**2
    result = ideal_linear(s, _correlated_nps(floor=floor), SPACING)

    n = 20_000
    present, absent = _trials(n, seed=23, correlation_sigma_mm=CORR_SIGMA, white_sd=white_sd)
    empirical = d_prime_from_scores(
        score_images(present, result.template), score_images(absent, result.template)
    )

    se = _standard_error(result.d_prime, n)
    assert abs(empirical - result.d_prime) < 4.0 * se, (
        f"ideal closed form {result.d_prime:.4f} vs Monte Carlo {empirical:.4f} "
        f"({abs(empirical - result.d_prime) / se:.1f} SE apart)"
    )


def test_auc_from_scores_agrees_with_the_gaussian_auc():
    """Empirical (Mann-Whitney) AUC vs the Phi(d'/sqrt2) implied by the closed-form d'."""
    s = _signal()
    result = npwe(s, WHITE_NPS, SPACING, eye_filter=burgess_eye_filter(1.0))
    present, absent = _trials(20_000, seed=31)
    empirical = auc_from_scores(
        score_images(present, result.template), score_images(absent, result.template)
    )
    assert empirical == pytest.approx(result.auc, abs=0.005)


# --------------------------------------------------------------------------------------
# the three traps: each returns a plausible wrong number, so each must raise
# --------------------------------------------------------------------------------------


def test_prewhitening_refuses_an_nps_that_decays_to_nothing():
    """Trap 1: a Gaussian-correlated NPS gives the ideal observer a d' of order 1e29.

    1/NPS explodes where the noise power underflows, so the integral is dominated by bins
    whose "signal power" is floating-point rounding. Nothing about the resulting number looks
    wrong. It must raise — and it must work once the noise has a floor, as real noise does.
    """
    s = _signal()
    with pytest.raises(ValueError, match="dynamic range"):
        ideal_linear(s, _correlated_nps(), SPACING)

    # A physical white floor makes it well-posed...
    with_floor = ideal_linear(s, _correlated_nps(floor=0.05 * WHITE_NPS), SPACING)
    assert 0.0 < with_floor.d_prime < 100.0

    # ... and so does saying so explicitly.
    clamped = ideal_linear(s, _correlated_nps(), SPACING, noise_floor=1e-4)
    assert 0.0 < clamped.d_prime < 1000.0
    assert clamped.meta["noise_floor"] == 1e-4


def test_npw_refuses_a_measured_nps_whose_dc_bin_was_detrended_away():
    """Trap 2: a measured NPS has NPS(0) = 0, which inflates d' by ~3 % for a disk.

    The zeroed DC bin carries ~6 % of the observer's noise weight, contributes no variance,
    and so silently raises d'. An eye filter has E(0) = 0 and is immune — which is exactly
    the distinction the guard has to make, rather than blanket-refusing measured spectra.
    """
    s = _signal()
    phantom = make_uniform_phantom(
        SIZE, spacing=SPACING, mean=100.0, noise_sd=SIGMA, seed=1, n_realizations=64
    )
    measured = nps_2d(phantom.image, SPACING)
    assert measured.nps[SIZE // 2, SIZE // 2] == 0.0  # detrending zeroed DC

    # Plain NPW puts weight at DC, so the measured NPS would bias it high: refuse.
    with pytest.raises(ValueError, match="noise weight"):
        npwe(s, measured, SPACING)

    # With an eye filter, DC carries no weight and the same measured NPS is fine.
    result = npwe(s, measured, SPACING, eye_filter=burgess_eye_filter(1.0))
    analytic = npwe(s, WHITE_NPS, SPACING, eye_filter=burgess_eye_filter(1.0))
    assert result.d_prime == pytest.approx(analytic.d_prime, rel=0.05)

    # And the guard can be overridden deliberately, for detrended images.
    forced = npwe(s, measured, SPACING, zero_nps_tolerance=1.0)
    exact = float(np.linalg.norm(s) / SIGMA)
    assert forced.d_prime > exact  # demonstrably biased high, which is why it is refused


def test_laguerre_gauss_refuses_a_channel_set_that_does_not_fit_the_image():
    """Trap 3: too-wide LG channels are truncated, so they are not orthonormal after all."""
    with pytest.raises(ValueError, match="do not fit"):
        laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=8, width_mm=2.0)

    # Accepting the truncation has to be a deliberate act.
    truncated = laguerre_gauss_channels(
        (SIZE, SIZE), SPACING, n_channels=8, width_mm=2.0, containment_tol=1.0
    )
    assert truncated.shape == (8, SIZE, SIZE)


def test_laguerre_gauss_channels_are_orthonormal_when_they_do_fit():
    """The property the docstring promises: <u_i, u_j> dA = delta_ij."""
    n = 8
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=n, width_mm=1.0)
    flat = channels.reshape(n, -1)
    gram = (flat @ flat.T) * SPACING**2
    np.testing.assert_allclose(gram, np.eye(n), atol=1e-3)


# --------------------------------------------------------------------------------------
# CHO
# --------------------------------------------------------------------------------------


def _cho_analytic_d_prime(channels: np.ndarray, signal: np.ndarray, sigma: float) -> float:
    r"""Closed-form CHO detectability in white noise.

    Channel responses are ``v = U g``, so in white noise ``cov(v) = sigma^2 U U^T`` and the
    mean difference is ``U s``, giving ``d'^2 = (Us)^T (sigma^2 U U^T)^-1 (U s)`` — no
    simulation and no covariance estimate involved.
    """
    u = channels.reshape(channels.shape[0], -1)
    covariance = sigma**2 * (u @ u.T)
    delta = u @ signal.ravel()
    return float(np.sqrt(delta @ np.linalg.solve(covariance, delta)))


@pytest.mark.parametrize("n_channels", [4, 6, 8])
def test_cho_matches_its_closed_form_in_white_noise(n_channels):
    """The estimated CHO d' converges on the analytic (Us)^T (sigma^2 UU^T)^-1 (Us)."""
    s = _signal()
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=n_channels, width_mm=1.0)
    exact = _cho_analytic_d_prime(channels, s, SIGMA)

    present, absent = _trials(2000, seed=5)
    result = cho(present, absent, channels, method="split")

    se = _standard_error(exact, result.scores_present.size)
    assert abs(result.d_prime - exact) < 4.0 * se
    assert result.n_channels == n_channels
    assert result.condition_number < 100.0


def test_cho_cannot_beat_the_ideal_observer():
    """A channelized observer throws information away, so it must land below the bound."""
    s = _signal()
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=6, width_mm=1.0)
    ideal = ideal_linear(s, WHITE_NPS, SPACING).d_prime
    exact_cho = _cho_analytic_d_prime(channels, s, SIGMA)
    assert exact_cho < ideal
    assert exact_cho / ideal > 0.9  # but LG channels suit a disk, so not much is lost


def test_cho_bias_directions_bracket_the_truth():
    """Resubstitution is biased high, the split estimate is biased low, and they bracket.

    Neither is "the" answer, and saying so is the point: resubstitution overfits the template
    to its own training data, while the split estimate honestly measures a template trained on
    only half the images — which really is worse than the asymptotic one. Averaged over
    repetitions, the truth sits between them. Testing that, rather than asserting either is
    unbiased, is what keeps the CHO honest.
    """
    s = _signal()
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=8, width_mm=1.0)
    exact = _cho_analytic_d_prime(channels, s, SIGMA)

    n_per_class, repeats = 40, 30
    resub, split = [], []
    for rep in range(repeats):
        present, absent = _trials(n_per_class, seed=1000 + rep)
        resub.append(cho(present, absent, channels, method="resubstitution").d_prime)
        split.append(cho(present, absent, channels, method="split").d_prime)

    mean_resub = float(np.mean(resub))
    mean_split = float(np.mean(split))
    assert mean_split < exact < mean_resub, (
        f"expected split ({mean_split:.3f}) < exact ({exact:.3f}) < resub ({mean_resub:.3f})"
    )

    # Both biases shrink as the sample grows: with 5x the data the bracket tightens.
    resub_big, split_big = [], []
    for rep in range(8):
        present, absent = _trials(200, seed=2000 + rep)
        resub_big.append(cho(present, absent, channels, method="resubstitution").d_prime)
        split_big.append(cho(present, absent, channels, method="split").d_prime)
    assert abs(np.mean(resub_big) - exact) < abs(mean_resub - exact)
    assert abs(np.mean(split_big) - exact) < abs(mean_split - exact)


def test_cho_internal_noise_lowers_detectability():
    """Internal noise is what makes a model observer able to under-perform the maths."""
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=6, width_mm=1.0)
    present, absent = _trials(2000, seed=3)

    quiet = cho(present, absent, channels, method="split", internal_noise=0.0)
    noisy = cho(present, absent, channels, method="split", internal_noise=0.5, seed=1)
    noisier = cho(present, absent, channels, method="split", internal_noise=1.5, seed=1)

    assert noisier.d_prime < noisy.d_prime < quiet.d_prime
    assert noisy.internal_noise == 0.5


def test_cho_is_reproducible_and_refuses_unseeded_internal_noise():
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=6, width_mm=1.0)
    present, absent = _trials(500, seed=8)

    a = cho(present, absent, channels, internal_noise=0.4, seed=99)
    b = cho(present, absent, channels, internal_noise=0.4, seed=99)
    assert a.d_prime == b.d_prime
    assert a.scores_present.tobytes() == b.scores_present.tobytes()

    with pytest.raises(ValueError, match="requires an explicit seed"):
        cho(present, absent, channels, internal_noise=0.4, seed=None)


def test_cho_refuses_too_few_samples_for_the_channel_count():
    """An unestimable covariance is an error, not a number."""
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=8, width_mm=1.0)
    present, absent = _trials(6, seed=2)
    with pytest.raises(ValueError, match="images per class"):
        cho(present, absent, channels, method="split")


def test_cho_refuses_an_ill_conditioned_channel_set():
    """Duplicate channels make K singular; K^-1 dv would then be pure estimation noise."""
    base = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=4, width_mm=1.0)
    degenerate = np.concatenate([base, base], axis=0)  # each channel twice
    present, absent = _trials(500, seed=6)
    with pytest.raises(ValueError, match="ill-conditioned"):
        cho(present, absent, degenerate, method="split")


@pytest.mark.parametrize(
    "channel_factory",
    [
        lambda: dense_dog_channels((SIZE, SIZE), SPACING, n_channels=6),
        lambda: gabor_channels((SIZE, SIZE), SPACING),
    ],
)
def test_other_channel_sets_produce_a_usable_cho(channel_factory):
    """DoG and Gabor sets work too — below LG, since neither is matched to a round signal."""
    s = _signal()
    channels = channel_factory()
    present, absent = _trials(3000, seed=4)
    result = cho(present, absent, channels, method="split")

    ideal = ideal_linear(s, WHITE_NPS, SPACING).d_prime
    assert 0.0 < result.d_prime < ideal
    assert result.spatial_template.shape == (SIZE, SIZE)


# --------------------------------------------------------------------------------------
# eye filter, scoring, and argument validation
# --------------------------------------------------------------------------------------


def test_burgess_eye_filter_shape():
    eye = burgess_eye_filter(peak_cycles_per_mm=1.5, exponent=1.3)
    f = np.linspace(0.0, 6.0, 601)
    e = eye(f)
    assert e[0] == 0.0  # blind to DC, which is why NPWE tolerates a detrended NPS
    assert eye(np.array([1.5]))[0] == pytest.approx(1.0)  # normalised at the peak
    assert f[int(np.argmax(e))] == pytest.approx(1.5, abs=0.02)
    assert e[-1] < 0.01  # and rolls off


def test_score_images_handles_one_image_and_a_stack():
    template = np.ones((8, 8))
    single = np.full((8, 8), 2.0)
    stack = np.stack([single, 3.0 * np.ones((8, 8))])
    assert score_images(single, template) == pytest.approx([128.0])
    assert score_images(stack, template) == pytest.approx([128.0, 192.0])


def test_d_prime_and_auc_helpers_agree_on_gaussian_scores():
    rng = np.random.default_rng(0)
    absent = rng.normal(0.0, 1.0, 40_000)
    present = rng.normal(2.0, 1.0, 40_000)
    assert d_prime_from_scores(present, absent) == pytest.approx(2.0, abs=0.02)
    # PC in 2AFC = Phi(d'/sqrt2) = AUC; for d' = 2 that is 0.921.
    assert auc_from_scores(present, absent) == pytest.approx(0.9214, abs=0.005)


def test_auc_counts_ties_as_half():
    tied = np.zeros(10)
    assert auc_from_scores(tied, tied) == pytest.approx(0.5)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"spacing": 0.0}, "spacing"),
        ({"nps": -1.0}, "must be finite and > 0"),
        ({"nps_layout": "sideways"}, "nps_layout"),
    ],
)
def test_npwe_rejects_bad_arguments(kwargs, message):
    args = {"signal": _signal(), "nps": WHITE_NPS, "spacing": SPACING, **kwargs}
    if kwargs.get("nps_layout"):
        args["nps"] = np.full((SIZE, SIZE), WHITE_NPS)
    with pytest.raises(ValueError, match=message):
        npwe(**args)


def test_observers_reject_a_zero_signal_and_a_mismatched_nps():
    with pytest.raises(ValueError, match="identically zero"):
        npwe(np.zeros((SIZE, SIZE)), WHITE_NPS, SPACING)
    with pytest.raises(ValueError, match="expected"):
        npwe(_signal(), np.full((32, 32), WHITE_NPS), SPACING)
    with pytest.raises(ValueError, match="non-finite"):
        bad = _signal()
        bad[0, 0] = np.nan
        npwe(bad, WHITE_NPS, SPACING)


def test_nps_result_grid_must_match_the_signal_grid():
    """An NPS measured on a different grid cannot be silently reinterpolated."""
    phantom = make_uniform_phantom(32, spacing=SPACING, noise_sd=SIGMA, seed=0, n_realizations=8)
    measured = nps_2d(phantom.image, SPACING)
    with pytest.raises(ValueError, match="same grid"):
        npwe(_signal(), measured, SPACING, eye_filter=burgess_eye_filter(1.0))
