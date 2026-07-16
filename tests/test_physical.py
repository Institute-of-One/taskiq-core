r"""Physical metrics against analytic ground truth.

This is the file that decides whether the rest of the project can be believed. Both
estimators are held to a closed-form answer, not to a snapshot of their own output:

* MTF: a phantom that *is* the exact erf profile of a Gaussian-blurred step has
  presampled MTF exp(-2 pi^2 sigma^2 f^2). The estimate must match it to < 1 %.
* NPS: the chosen normalisation makes ``integral(NPS) == variance`` an exact identity, so
  it is checked at machine precision, and white noise must come back flat at
  sigma^2 dx dy.

Where a test is statistical rather than exact, its tolerance is derived from the number
of samples that went into the estimate (see ``_relative_error_bound``) instead of being
tuned until it passed.
"""

from __future__ import annotations

import numpy as np
import pytest

from taskiq_core import (
    estimate_edge_angle,
    gaussian_mtf,
    make_edge_phantom,
    make_uniform_phantom,
    mtf_from_edge,
    nps_2d,
)

SPACING = 0.1  # mm
CONTRAST = 1000.0


def _edge(sigma_mm: float, angle_deg: float = 5.0, size: int = 512, **kwargs):
    return make_edge_phantom(
        size,
        spacing=SPACING,
        contrast=CONTRAST,
        angle_deg=angle_deg,
        blur_sigma_mm=sigma_mm,
        **kwargs,
    )


def _relative_error_bound(counts: np.ndarray, n_rois: int, n_sigma: float = 6.0) -> np.ndarray:
    """Statistical tolerance for one radial NPS bin.

    A periodogram value is exponentially distributed with 100 % relative standard
    deviation. Averaging ``counts`` frequency bins over ``n_rois`` realisations cuts that
    to ``1/sqrt(counts * n_rois)``; the conjugate symmetry of a real DFT halves the
    number of independent samples, hence the factor 2 under the root. The tolerance is
    ``n_sigma`` of *that*, so it is a property of the estimator, not a tuned constant.
    """
    return n_sigma * np.sqrt(2.0 / (counts * n_rois))


# --------------------------------------------------------------------------------------
# MTF vs the analytic Gaussian
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("angle_deg", [2.0, 3.5, 5.0, 8.0, -5.0])
@pytest.mark.parametrize("sigma_mm", [0.15, 0.25, 0.40])
def test_mtf_analytic_gaussian(sigma_mm, angle_deg):
    """THE test: estimated MTF == exp(-2 pi^2 sigma^2 f^2) to better than 1 % relative.

    Compared wherever the true MTF exceeds 0.05, i.e. across the whole range in which the
    modulation is physically measurable. (Above ~1.4 cycles/mm for sigma = 0.25 mm the
    true MTF is below 1 %, where a "relative error" says more about floating point than
    about the estimator.)
    """
    ph = _edge(sigma_mm, angle_deg)
    res = mtf_from_edge(ph.image, ph.spacing, angle_deg=angle_deg)

    truth = gaussian_mtf(res.frequency, sigma_mm)
    measurable = truth > 0.05
    assert measurable.sum() > 10  # the comparison band is not degenerate

    rel_err = np.abs(res.mtf[measurable] - truth[measurable]) / truth[measurable]
    assert rel_err.max() < 0.01, f"max relative MTF error {rel_err.max():.3%} exceeds 1 %"

    assert res.mtf[0] == pytest.approx(1.0)  # normalised at DC
    assert res.angle_estimated is False
    assert np.all(res.bin_counts > 0)


def test_mtf_accuracy_is_far_better_than_the_1_percent_requirement():
    """Pin down the accuracy actually achieved, so a regression cannot hide under a loose bound."""
    ph = _edge(0.25, 5.0)
    res = mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0)
    truth = gaussian_mtf(res.frequency, 0.25)
    band = truth > 0.05
    rel_err = np.abs(res.mtf[band] - truth[band]) / truth[band]
    assert rel_err.max() < 1e-3


def test_mtf_jitter_correction_is_what_buys_the_accuracy():
    """Bias A is real: without the bin-centre correction the same image misses by > 1 %.

    Guards the correction against being "simplified away" — and documents why it exists.
    """
    ph = _edge(0.15, 5.0)  # sharp blur, so the comparison band reaches high frequency
    truth_of = lambda r: gaussian_mtf(r.frequency, 0.15)  # noqa: E731

    on = mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0, jitter_correction=True)
    off = mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0, jitter_correction=False)

    def worst(res):
        t = truth_of(res)
        band = t > 0.1
        return float((np.abs(res.mtf[band] - t[band]) / t[band]).max())

    assert worst(off) > 0.01  # would fail the 1 % requirement
    assert worst(on) < 1e-4  # two orders of magnitude better
    assert on.meta["max_bin_jitter_frac"] > 0.01  # the jitter it corrects is measurable


def test_mtf_auto_angle_matches_the_known_angle():
    ph = _edge(0.25, 5.0)
    res = mtf_from_edge(ph.image, ph.spacing, angle_deg=None)
    assert res.angle_estimated is True
    assert res.angle_deg == pytest.approx(5.0, abs=0.01)

    truth = gaussian_mtf(res.frequency, 0.25)
    band = truth > 0.05
    assert (np.abs(res.mtf[band] - truth[band]) / truth[band]).max() < 0.01


@pytest.mark.parametrize("noise_sd", [2.0, 5.0, 20.0])
def test_edge_angle_estimate_survives_noise(noise_sd):
    """The area/moment estimator is linear in the pixels, so noise adds variance, not bias.

    A rectified-gradient centroid fails here: at noise_sd = 20 (2 % of contrast) it reports
    a 5 deg edge as ~0.6 deg. Half a degree of angle error smears the ESF by more than the
    blur being measured, so this is a correctness requirement, not a nicety.
    """
    ph = _edge(0.25, 5.0, noise_sd=noise_sd, seed=42)
    assert estimate_edge_angle(ph.image) == pytest.approx(5.0, abs=0.05)


def test_mtf_with_noise_is_still_accurate_at_low_frequency():
    """Noise raises the high-frequency MTF floor; the low-frequency estimate stays honest."""
    ph = _edge(0.25, 5.0, noise_sd=5.0, seed=7)
    res = mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0)
    truth = gaussian_mtf(res.frequency, 0.25)
    band = truth > 0.3
    assert (np.abs(res.mtf[band] - truth[band]) / truth[band]).max() < 0.02


# --------------------------------------------------------------------------------------
# MTF: refuse to return a wrong answer
# --------------------------------------------------------------------------------------


def test_mtf_raises_when_the_esf_window_truncates_the_blur():
    """A window too narrow for the blur biases the MTF, so it must raise, not truncate."""
    ph = _edge(0.25, 5.0)
    # 0.6 mm half-width = 2.4 sigma: the ESF has not flattened, and the MTF would be ~5 % off.
    with pytest.raises(ValueError, match="window is too narrow"):
        mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0, esf_halfwidth_mm=0.6)
    # 1.0 mm = 4 sigma is enough, and is accepted.
    res = mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0, esf_halfwidth_mm=1.0)
    truth = gaussian_mtf(res.frequency, 0.25)
    band = truth > 0.05
    assert (np.abs(res.mtf[band] - truth[band]) / truth[band]).max() < 0.01


def test_mtf_raises_on_underpopulated_esf_bins():
    """Too fine a bin for the image size leaves empty bins — an error, not a NaN in the ESF."""
    ph = _edge(0.25, 5.0, size=64)
    with pytest.raises(ValueError, match="ESF bins hold fewer than"):
        mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0, bin_subsample=200)


def test_mtf_raises_on_a_uniform_image():
    flat = np.full((64, 64), 3.0, dtype=np.float32)
    with pytest.raises(ValueError):
        mtf_from_edge(flat, SPACING, angle_deg=5.0)


def test_mtf_raises_on_non_finite_input():
    ph = _edge(0.25, 5.0, size=128)
    img = ph.image.astype(np.float64)
    img[10, 10] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        mtf_from_edge(img, SPACING, angle_deg=5.0)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"spacing": 0.0}, "spacing"),
        ({"bin_subsample": 1}, "bin_subsample"),
        ({"f_max": 0.0}, "f_max"),
        ({"f_max": 1e6}, "f_max"),
    ],
)
def test_mtf_rejects_bad_arguments(kwargs, message):
    ph = _edge(0.25, 5.0, size=128)
    args = {"image": ph.image, "spacing": SPACING, "angle_deg": 5.0, **kwargs}
    with pytest.raises(ValueError, match=message):
        mtf_from_edge(**args)


def test_mtf_result_at_interpolates():
    ph = _edge(0.25, 5.0)
    res = mtf_from_edge(ph.image, ph.spacing, angle_deg=5.0)
    assert res.at(0.0) == pytest.approx(1.0)
    assert res.at(0.5) == pytest.approx(gaussian_mtf(0.5, 0.25), rel=0.01)
    assert np.isnan(res.at(res.nyquist * 10))  # outside the measured band: NaN, not a guess


# --------------------------------------------------------------------------------------
# NPS
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("correlation_sigma_mm", [0.0, 0.3])
def test_nps_integral_equals_variance(seed, correlation_sigma_mm):
    """The normalisation identity, at machine precision.

    ``sum(NPS) * du * dv == var(ROI)`` is an exact consequence of Parseval given the
    (dx dy / (nx ny)) scaling — not an approximation — so it is tested at rtol=1e-10. If
    this ever fails, the NPS is in the wrong units and every NEQ and d' downstream is
    wrong by the same factor.
    """
    ph = make_uniform_phantom(
        64, spacing=SPACING, mean=100.0, noise_sd=20.0, seed=seed,
        correlation_sigma_mm=correlation_sigma_mm, n_realizations=16,
    )
    res = nps_2d(ph.image, ph.spacing)
    assert res.integral == pytest.approx(res.variance, rel=1e-10)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_nps_white_is_flat_at_the_analytic_level(seed):
    """White noise: NPS == sigma^2 dx dy, flat, and integrating back to sigma^2."""
    noise_sd, n_rois = 20.0, 64
    ph = make_uniform_phantom(
        64, spacing=SPACING, mean=100.0, noise_sd=noise_sd, seed=seed, n_realizations=n_rois
    )
    res = nps_2d(ph.image, ph.spacing)
    level = ph.ground_truth["nps_white_level"]  # sigma^2 * dx * dy
    assert level == pytest.approx(noise_sd**2 * SPACING**2)

    # Level: the mean over all non-DC frequencies is an average of ~260k periodogram
    # values, so it pins the level to well under 1 %.
    mean_2d = (res.nps.sum() - res.nps[res.nps.shape[0] // 2, res.nps.shape[1] // 2]) / (
        res.nps.size - 1
    )
    assert mean_2d == pytest.approx(level, rel=0.01)

    # Flatness: every radial bin sits within its own statistical error bar of the level.
    bound = _relative_error_bound(res.radial_counts, res.n_rois)
    deviation = np.abs(res.nps_radial / level - 1.0)
    assert np.all(deviation < bound), (
        f"radial NPS bin {int(np.argmax(deviation - bound))} deviates by "
        f"{deviation.max():.2%}, beyond its {bound[np.argmax(deviation - bound)]:.2%} bound"
    )

    # And the variance it integrates to is the variance that was put in.
    assert res.variance == pytest.approx(noise_sd**2, rel=0.01)


@pytest.mark.parametrize("seed", [0, 1])
def test_nps_correlated_matches_the_analytic_gaussian_spectrum(seed):
    r"""Gaussian-correlated noise: NPS == sigma^2 dx dy exp(-4 pi^2 sigma_c^2 f^2).

    The filter is applied as an exact circular convolution in the Fourier domain, so this
    is a closed-form target for the *shape* of the NPS, not just its level — the shape
    being what NEQ and the model observers actually weight.
    """
    sigma_c, noise_sd, n_rois = 0.3, 20.0, 128
    ph = make_uniform_phantom(
        128, spacing=SPACING, noise_sd=noise_sd, seed=seed,
        correlation_sigma_mm=sigma_c, n_realizations=n_rois,
    )
    res = nps_2d(ph.image, ph.spacing)

    truth = ph.ground_truth["nps_white_level"] * np.exp(
        -4.0 * np.pi**2 * sigma_c**2 * res.frequency**2
    )
    band = truth > 0.02 * truth.max()  # where there is power left to compare
    assert band.sum() > 5

    bound = _relative_error_bound(res.radial_counts[band], res.n_rois)
    deviation = np.abs(res.nps_radial[band] / truth[band] - 1.0)
    assert np.all(deviation < bound), f"max deviation {deviation.max():.2%}"


def test_nps_accepts_a_single_roi_and_a_stack():
    single = make_uniform_phantom(64, noise_sd=10.0, seed=1)
    stack = make_uniform_phantom(64, noise_sd=10.0, seed=1, n_realizations=4)
    r1 = nps_2d(single.image, single.spacing)
    r4 = nps_2d(stack.image, stack.spacing)
    assert r1.n_rois == 1 and r4.n_rois == 4
    assert r1.roi_shape == (64, 64)
    # More ROIs, less scatter about the flat truth.
    level = single.ground_truth["nps_white_level"]
    assert np.std(r4.nps_radial / level) < np.std(r1.nps_radial / level)


def test_nps_detrend_poly2_removes_shading_without_eating_the_noise():
    """A second-order background trend must not be mistaken for low-frequency noise power."""
    noise_sd = 20.0
    ph = make_uniform_phantom(
        128, spacing=SPACING, mean=0.0, noise_sd=noise_sd, seed=3, n_realizations=32
    )
    y, x = np.meshgrid(np.linspace(-1, 1, 128), np.linspace(-1, 1, 128), indexing="ij")
    shading = 300.0 * x + 200.0 * y**2  # a strong low-order trend
    shaded = ph.image + shading

    plain = nps_2d(shaded, ph.spacing, detrend="mean")
    fixed = nps_2d(shaded, ph.spacing, detrend="poly2")
    clean = nps_2d(ph.image, ph.spacing, detrend="poly2")

    level = ph.ground_truth["nps_white_level"]
    # Mean-detrending leaves the whole trend in the spectrum: the variance blows up.
    assert plain.variance > 10.0 * noise_sd**2
    # poly2 removes it and recovers the noise level.
    assert fixed.variance == pytest.approx(noise_sd**2, rel=0.02)
    assert fixed.nps_radial.mean() == pytest.approx(level, rel=0.05)
    # And it does not distort noise that had no trend to begin with.
    np.testing.assert_allclose(fixed.nps_radial, clean.nps_radial, rtol=0.05)


def test_nps_radial_axis_and_nyquist():
    ph = make_uniform_phantom(64, spacing=0.2, noise_sd=5.0, seed=0, n_realizations=8)
    res = nps_2d(ph.image, ph.spacing)
    assert res.nyquist == pytest.approx(1.0 / (2 * 0.2))
    assert res.frequency[0] > 0.0  # DC is excluded from the radial profile
    assert res.frequency.max() <= res.nyquist
    assert np.all(np.diff(res.frequency) > 0)
    assert np.all(res.radial_counts > 0)
    assert res.nps.shape == (64, 64)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"spacing": 0.0}, "spacing"),
        ({"detrend": "quadratic"}, "detrend must be one of"),
        ({"radial_bin_width": 0.0}, "radial_bin_width"),
        ({"f_max": 0.0}, "f_max"),
    ],
)
def test_nps_rejects_bad_arguments(kwargs, message):
    ph = make_uniform_phantom(64, noise_sd=5.0, seed=0)
    args = {"images": ph.image, "spacing": SPACING, **kwargs}
    with pytest.raises(ValueError, match=message):
        nps_2d(**args)


def test_nps_raises_on_bad_shapes_and_non_finite_values():
    with pytest.raises(ValueError, match="images must have shape"):
        nps_2d(np.zeros((2, 2, 8, 8)), SPACING)
    with pytest.raises(ValueError, match="at least 4x4"):
        nps_2d(np.zeros((3, 3)), SPACING)
    bad = np.random.default_rng(0).normal(size=(16, 16))
    bad[0, 0] = np.inf
    with pytest.raises(ValueError, match="non-finite"):
        nps_2d(bad, SPACING)


def test_nps_raises_when_radial_bins_would_be_empty():
    ph = make_uniform_phantom(32, spacing=SPACING, noise_sd=5.0, seed=0)
    with pytest.raises(ValueError, match="radial NPS bins are empty"):
        nps_2d(ph.image, ph.spacing, radial_bin_width=1e-3)


# --------------------------------------------------------------------------------------
# analytic reference itself
# --------------------------------------------------------------------------------------


def test_gaussian_mtf_reference():
    assert gaussian_mtf(0.0, 0.25) == pytest.approx(1.0)
    assert gaussian_mtf(1.0, 0.0) == pytest.approx(1.0)  # no blur: all-pass
    # Half-maximum of exp(-2 pi^2 sigma^2 f^2) is at f = sqrt(ln 2 / 2) / (pi sigma).
    sigma = 0.25
    f_half = np.sqrt(np.log(2.0) / 2.0) / (np.pi * sigma)
    assert gaussian_mtf(f_half, sigma) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        gaussian_mtf(1.0, -1.0)
