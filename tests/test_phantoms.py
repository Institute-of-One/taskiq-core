"""Phantoms: do they draw what they claim to draw?

Each phantom is checked against the closed form it is supposed to realise — the erf
profile of a Gaussian-blurred step, the variance of a white field, the area of a disk —
rather than against a stored snapshot of itself.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.special import erf

from taskiq_core import make_disk_signal, make_edge_phantom, make_uniform_phantom


# --------------------------------------------------------------------------------------
# edge
# --------------------------------------------------------------------------------------


def test_edge_phantom_basics():
    ph = make_edge_phantom(128, spacing=0.2, contrast=500.0, angle_deg=5.0, background=50.0)
    assert ph.image.dtype == np.float32
    assert ph.image.shape == (128, 128)
    assert ph.spacing == 0.2
    assert ph.kind == "edge"
    assert ph.extent_mm == (25.6, 25.6)
    # Far from the edge the image sits on its two asymptotes.
    assert ph.image[0, 0] == pytest.approx(50.0)
    assert ph.image[-1, -1] == pytest.approx(550.0)
    assert ph.ground_truth["angle_deg"] == 5.0
    assert ph.ground_truth["mtf_kind"] == "ideal"


@pytest.mark.parametrize("angle_deg", [2.0, 5.0, -5.0, 8.0])
@pytest.mark.parametrize("sigma", [0.15, 0.4])
def test_edge_phantom_is_the_exact_erf_profile(angle_deg, sigma):
    """Every pixel equals the analytic blurred-step value at its distance from the edge.

    This is what licenses the MTF test: if the image *is* the continuous erf profile
    sampled at the pixel centres, its presampled MTF is exactly exp(-2 pi^2 sigma^2 f^2),
    with no discretisation or boundary artefact from a numerical convolution.
    """
    spacing, contrast, background = 0.1, 1000.0, 20.0
    ph = make_edge_phantom(
        64,
        spacing=spacing,
        contrast=contrast,
        angle_deg=angle_deg,
        background=background,
        blur_sigma_mm=sigma,
    )
    ny, nx = ph.shape
    n_x, n_y = ph.ground_truth["normal"]
    x0, y0 = ph.ground_truth["edge_point_px"]
    yy, xx = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    u = ((xx - x0) * n_x + (yy - y0) * n_y) * spacing
    expected = background + contrast * 0.5 * (1.0 + erf(u / (sigma * np.sqrt(2.0))))

    np.testing.assert_allclose(ph.image, expected, rtol=0, atol=1e-3)
    assert ph.ground_truth["mtf_kind"] == "gaussian"


def test_edge_phantom_oversample_averages_the_pixel_aperture():
    """oversample > 1 area-averages, so it softens a hard step and flags the extra sinc."""
    sharp = make_edge_phantom(64, angle_deg=5.0, contrast=1000.0, oversample=1)
    soft = make_edge_phantom(64, angle_deg=5.0, contrast=1000.0, oversample=8)
    # Point sampling of a hard step gives only the two levels; area averaging gives
    # intermediate values in the pixels the edge cuts through.
    assert set(np.unique(sharp.image)) == {0.0, 1000.0}
    partial = (soft.image > 1.0) & (soft.image < 999.0)
    assert partial.sum() > 50
    assert soft.ground_truth["mtf_kind"] == "ideal*aperture"


def test_edge_phantom_noise_has_the_requested_sd():
    ph = make_edge_phantom(
        512, spacing=0.1, contrast=1000.0, angle_deg=5.0, blur_sigma_mm=0.25,
        noise_sd=7.0, seed=11,
    )
    clean = make_edge_phantom(
        512, spacing=0.1, contrast=1000.0, angle_deg=5.0, blur_sigma_mm=0.25,
    )
    residual = ph.image.astype(np.float64) - clean.image.astype(np.float64)
    assert residual.std() == pytest.approx(7.0, rel=0.02)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"angle_deg": 0.0}, "axis-aligned"),
        ({"angle_deg": 90.0}, "axis-aligned"),
        ({"spacing": 0.0}, "spacing"),
        ({"spacing": -0.1}, "spacing"),
        ({"size": 2}, "at least 4x4"),
        ({"blur_sigma_mm": -1.0}, "blur_sigma_mm"),
        ({"noise_sd": -1.0}, "noise_sd"),
        ({"oversample": 0}, "oversample"),
        ({"contrast": np.nan}, "contrast"),
        ({"noise_sd": 5.0, "seed": None}, "requires an explicit seed"),
    ],
)
def test_edge_phantom_rejects_bad_arguments(kwargs, message):
    """Bad input raises with an actionable message — it is never silently coerced."""
    with pytest.raises(ValueError, match=message):
        make_edge_phantom(**{"size": 64, "angle_deg": 5.0, **kwargs})


# --------------------------------------------------------------------------------------
# uniform
# --------------------------------------------------------------------------------------


def test_uniform_phantom_white_statistics():
    ph = make_uniform_phantom(256, spacing=0.1, mean=100.0, noise_sd=15.0, seed=4)
    assert ph.image.dtype == np.float32
    assert ph.image.shape == (256, 256)
    assert ph.image.mean() == pytest.approx(100.0, abs=0.2)
    assert ph.image.std() == pytest.approx(15.0, rel=0.02)
    assert ph.ground_truth["nps_kind"] == "white"
    assert ph.ground_truth["nps_white_level"] == pytest.approx(15.0**2 * 0.1 * 0.1)
    assert ph.ground_truth["pixel_sd_expected"] == pytest.approx(15.0)


def test_uniform_phantom_stack_shape():
    ph = make_uniform_phantom(32, noise_sd=5.0, seed=1, n_realizations=7)
    assert ph.image.shape == (7, 32, 32)
    assert ph.ground_truth["n_realizations"] == 7


def test_uniform_phantom_correlated_is_smoother_and_reports_it():
    """Correlated noise really is smoother, and ground_truth says so instead of hiding it."""
    ph = make_uniform_phantom(
        256, spacing=0.1, noise_sd=20.0, seed=5, correlation_sigma_mm=0.3
    )
    assert ph.ground_truth["nps_kind"] == "gaussian_correlated"
    # The filter is not renormalised, so the pixel SD drops below the white-field SD;
    # the phantom predicts the new SD in closed form rather than pretending it is 20.
    expected_sd = ph.ground_truth["pixel_sd_expected"]
    assert expected_sd < 20.0
    assert ph.image.std() == pytest.approx(expected_sd, rel=0.05)
    # Neighbouring pixels are now correlated (they are not, for white noise).
    img = ph.image.astype(np.float64)
    img -= img.mean()
    corr = float(np.mean(img[:, :-1] * img[:, 1:]) / np.mean(img**2))
    assert corr > 0.8


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"spacing": -1.0}, "spacing"),
        ({"noise_sd": -1.0}, "noise_sd"),
        ({"correlation_sigma_mm": -1.0}, "correlation_sigma_mm"),
        ({"n_realizations": 0}, "n_realizations"),
        ({"noise_sd": 5.0, "seed": None}, "requires an explicit seed"),
    ],
)
def test_uniform_phantom_rejects_bad_arguments(kwargs, message):
    with pytest.raises(ValueError, match=message):
        make_uniform_phantom(**{"size": 32, "seed": 0, **kwargs})


# --------------------------------------------------------------------------------------
# disk
# --------------------------------------------------------------------------------------


def test_disk_signal_matches_its_analytic_area():
    """Sum of pixel values = contrast x area / pixel area, to within the sub-pixel model."""
    spacing, radius_mm, contrast = 0.1, 1.0, 10.0
    ph = make_disk_signal(64, radius_mm=radius_mm, contrast=contrast, spacing=spacing)
    expected_sum = contrast * np.pi * radius_mm**2 / spacing**2
    assert ph.image.sum() == pytest.approx(expected_sum, rel=0.005)
    assert ph.ground_truth["signal_sum"] == pytest.approx(expected_sum, rel=0.005)
    assert ph.ground_truth["area_mm2"] == pytest.approx(np.pi)
    # Signal only: zero background, peak at the requested contrast.
    assert ph.image[0, 0] == 0.0
    assert ph.image.max() == pytest.approx(contrast)
    assert ph.seed is None  # deterministic; draws no random numbers


def test_disk_signal_area_converges_with_oversampling():
    """The area error shrinks as the sub-pixel grid is refined — the aliasing is the only error."""
    spacing, radius_mm, contrast = 0.1, 0.8, 10.0
    exact = contrast * np.pi * radius_mm**2 / spacing**2
    errors = [
        abs(make_disk_signal(64, radius_mm, contrast, spacing, oversample=k).image.sum() - exact)
        for k in (1, 4, 16)
    ]
    assert errors[2] < errors[1] < errors[0]
    assert errors[2] / exact < 1e-3


def test_disk_signal_soft_edge_is_smooth_and_conserves_area():
    """Blurring the edge must not change how much signal there is.

    The exact 2-D Gaussian convolution conserves the integral. Applying the 1-D erf
    profile of a blurred *straight* edge radially — the tempting shortcut — does not: it
    adds pi sigma^2 of area (+2.3 % here), making the signal energy depend on the blur.
    """
    ph = make_disk_signal(96, radius_mm=1.0, contrast=10.0, spacing=0.1, edge_sigma_mm=0.15)
    expected_sum = 10.0 * np.pi * 1.0**2 / 0.1**2
    assert ph.image.sum() == pytest.approx(expected_sum, rel=0.005)
    assert 0.0 < ph.image.max() <= 10.0001
    # No hard jump: the largest neighbour-to-neighbour step is well under the contrast.
    assert np.abs(np.diff(ph.image, axis=1)).max() < 3.0
    # ... and the sharp disk of the same radius carries the same total signal.
    sharp = make_disk_signal(96, radius_mm=1.0, contrast=10.0, spacing=0.1)
    assert ph.image.sum() == pytest.approx(sharp.image.sum(), rel=0.005)


def test_disk_signal_negative_contrast_is_a_cold_lesion():
    ph = make_disk_signal(64, radius_mm=1.0, contrast=-10.0, spacing=0.1)
    assert ph.image.min() == pytest.approx(-10.0)
    assert ph.image.max() == pytest.approx(0.0)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"radius_mm": 0.0}, "radius_mm"),
        ({"radius_mm": -1.0}, "radius_mm"),
        ({"radius_mm": 5.0}, "does not fit"),  # 5 mm disk in a 64 px x 0.1 mm image
        ({"spacing": 0.0}, "spacing"),
        ({"oversample": 0}, "oversample"),
        ({"edge_sigma_mm": -0.1}, "edge_sigma_mm"),
        ({"center_px": (2.0, 2.0)}, "does not fit"),
    ],
)
def test_disk_signal_rejects_bad_arguments(kwargs, message):
    with pytest.raises(ValueError, match=message):
        make_disk_signal(**{"size": 64, "radius_mm": 1.0, "spacing": 0.1, **kwargs})
