r"""NEQ, the condition sweep, and the physical-to-task transfer, against analytic truth.

This is the module that states the project's thesis — that physical image quality predicts
task performance — so its tests are built around the identities that make that statement
exact rather than approximate:

* **NEQ arithmetic.** For a Gaussian system and white noise, ``NEQ = MTF²/NPS`` has the closed
  form ``exp(-4π²σ²f²)/(σ_n²ΔxΔy)``; `neq` must reproduce it to machine precision.
* **The bridge.** The ideal-observer detectability of an object signal imaged through a system
  is exactly ``d'² = ∬ NEQ(f)|S_obj(f)|² df``. This is *the* physical-to-task identity, and it
  is checked here against the independently-validated `ideal_linear`, bin for bin, to ~1e-15.
* **The transfer laws.** Ideal ``d'²`` is exactly linear in ``contrast²`` and in ``1/σ_n²``,
  so `fit_transfer` on the swept data must return R² = 1 and the slope the closed form fixes.
"""

from __future__ import annotations

import numpy as np
import pytest

from taskiq_core import (
    AtlasConfig,
    fit_transfer,
    gaussian_mtf,
    ideal_linear,
    make_disk_signal,
    make_edge_phantom,
    make_uniform_phantom,
    mtf_from_edge,
    neq,
    nps_2d,
    sweep,
)

SPACING = 0.1


# --------------------------------------------------------------------------------------
# NEQ
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("sigma", [0.1, 0.2, 0.35])
@pytest.mark.parametrize("noise_sd", [10.0, 25.0])
def test_neq_matches_the_analytic_closed_form(sigma, noise_sd):
    """NEQ = MTF²/NPS = exp(-4π²σ²f²)/(σ_n²ΔxΔy) for a Gaussian system in white noise."""
    level = noise_sd**2 * SPACING**2
    f = np.linspace(0.0, 5.0, 256)  # include DC so the f->0 limit below is exact, not near-DC

    result = neq(lambda ff: gaussian_mtf(ff, sigma), level, frequency=f)

    truth = np.exp(-4.0 * np.pi**2 * sigma**2 * f**2) / level
    rel = np.abs(result.neq - truth) / truth
    assert rel.max() < 1e-12
    # NEQ -> 1/level as f -> 0 (MTF -> 1).
    assert result.neq[0] == pytest.approx(1.0 / level, rel=1e-3)


def test_neq_accepts_result_objects_from_the_estimators():
    """`neq` takes an MTFResult and an NPSResult directly and lines up their axes."""
    edge = make_edge_phantom(
        512, spacing=SPACING, contrast=1000.0, angle_deg=5.0, blur_sigma_mm=0.2
    )
    mtf = mtf_from_edge(edge.image, edge.spacing)
    rois = make_uniform_phantom(64, spacing=SPACING, noise_sd=20.0, seed=0, n_realizations=64)
    nps = nps_2d(rois.image, rois.spacing)

    # Report NEQ on the overlap of the two axes — the NPS axis starts above DC, so the
    # lower bound must respect it too or `neq` will (correctly) refuse to extrapolate.
    fmin = max(mtf.frequency.min(), nps.frequency.min())
    fmax = min(mtf.frequency.max(), nps.frequency.max())
    freq = np.linspace(fmin, fmax, 50)
    result = neq(mtf, nps, frequency=freq)

    assert result.neq.shape == freq.shape
    assert np.all(np.isfinite(result.neq))
    # Loosely, it should track the analytic NEQ of this system (measured inputs -> ~10%).
    truth = gaussian_mtf(freq, 0.2) ** 2 / (20.0**2 * SPACING**2)
    band = truth > 0.2 * truth.max()
    assert np.abs(result.neq[band] / truth[band] - 1.0).mean() < 0.15


def test_neq_refuses_to_extrapolate_and_to_divide_by_zero():
    f = np.linspace(0.1, 3.0, 40)
    mtf_data = np.stack([f, gaussian_mtf(f, 0.2)])
    nps_data = np.stack([f, np.full_like(f, 4.0)])

    # A requested frequency outside the data range is refused, not extrapolated.
    with pytest.raises(ValueError, match="exceeds"):
        neq(mtf_data, nps_data, frequency=np.linspace(0.1, 5.0, 20))

    # Zero NPS with no floor would divide by zero.
    with pytest.raises(ValueError, match="divide by zero|zero or negative|zero everywhere"):
        neq(mtf_data, np.stack([f, np.zeros_like(f)]), frequency=f)

    # ... but a floor makes it well-posed.
    result = neq(
        mtf_data, np.stack([f, np.linspace(0.0, 4.0, f.size)]), frequency=f, nps_floor_fraction=1e-3
    )
    assert np.all(np.isfinite(result.neq))


def test_physical_to_task_bridge_holds_to_machine_precision():
    r"""THE identity: d'²_ideal = ∬ NEQ(f) |S_obj(f)|² df, computed two independent ways.

    Route A: build the image signal as the object disk blurred by the analytic system MTF, and
    ask the (independently validated) ideal observer for its d'².
    Route B: integrate NEQ = MTF²/NPS against the *object* signal's power spectrum.

    They are the same integral rearranged, so they must agree to floating-point precision — and
    that agreement is the whole claim of the project made exact: the physics (NEQ) determines
    the task (d').
    """
    size, sigma, noise_sd = 64, 0.15, 20.0
    level = noise_sd**2 * SPACING**2

    s_obj = make_disk_signal(size, radius_mm=0.8, contrast=6.0, spacing=SPACING).image.astype(
        np.float64
    )
    fy = np.fft.fftfreq(size, d=SPACING)[:, None]
    fx = np.fft.fftfreq(size, d=SPACING)[None, :]
    mtf2d = np.exp(-2.0 * np.pi**2 * sigma**2 * (fy**2 + fx**2))  # analytic system MTF

    s_img = np.fft.ifft2(np.fft.fft2(s_obj) * mtf2d).real  # image = object through the system

    # Route A — the validated observer.
    d2_observer = ideal_linear(s_img, level, SPACING).d_prime ** 2

    # Route B — NEQ against the object spectrum.
    area = SPACING * SPACING
    s_obj_spectrum = area * np.fft.fft2(s_obj)
    neq2d = mtf2d**2 / level
    du_dv = 1.0 / (size * size * area)
    d2_neq = float(np.sum(neq2d * np.abs(s_obj_spectrum) ** 2) * du_dv)

    assert d2_neq == pytest.approx(d2_observer, rel=1e-10)


# --------------------------------------------------------------------------------------
# sweep
# --------------------------------------------------------------------------------------


def _base() -> AtlasConfig:
    return AtlasConfig(
        size=64,
        spacing=SPACING,
        radius_mm=0.8,
        blur_sigma_mm=0.15,
        noise_sd=20.0,
        white_floor_sd=0.0,
    )


def test_sweep_records_paired_physical_and_task_metrics():
    table = sweep(_base(), {"contrast": [2, 4, 6, 8, 10]}, observers=("ideal", "NPWE"), seed=0)

    assert table.n_rows == 5
    for col in (
        "contrast",
        "mtf50",
        "neq_peak",
        "neq_integral",
        "d_ideal",
        "d_NPWE",
        "pc_ideal",
        "efficiency_NPWE",
    ):
        assert col in table.columns
        assert np.all(np.isfinite(table.column(col)))
    assert not table.failures

    # d' is linear in contrast for a linear observer...
    d = table.column("d_ideal")
    ratios = d[1:] / d[:-1]
    # d' is linear in contrast to the phantom generator's precision (~1e-7 relative), not bit-exact.
    np.testing.assert_allclose(ratios, [2.0, 1.5, 8 / 6, 10 / 8], rtol=1e-6)
    # ... and the efficiency of NPWE relative to ideal does not depend on contrast.
    eff = table.column("efficiency_NPWE")
    np.testing.assert_allclose(eff, eff[0], rtol=1e-6)


def test_sweep_blur_worsens_both_the_mtf_and_the_task():
    table = sweep(
        _base(), {"blur_sigma_mm": [0.05, 0.1, 0.2, 0.3, 0.4]}, observers=("ideal",), seed=0
    )
    mtf50 = table.column("mtf50")
    d = table.column("d_ideal")
    neq_int = table.column("neq_integral")
    # More blur -> lower MTF50, lower NEQ, lower detectability. All monotone.
    assert np.all(np.diff(mtf50) < 0)
    assert np.all(np.diff(neq_int) < 0)
    assert np.all(np.diff(d) < 0)


def test_sweep_dose_gives_d_squared_proportional_to_inverse_variance():
    table = sweep(_base(), {"noise_sd": [10, 15, 20, 30, 40]}, observers=("ideal",), seed=0)
    sd = table.column("noise_sd")
    d = table.column("d_ideal")
    # d'^2 ∝ 1/σ² exactly.
    product = d**2 * sd**2
    np.testing.assert_allclose(product, product[0], rtol=1e-9)


def test_sweep_over_two_conditions_is_the_cartesian_product():
    table = sweep(
        _base(), {"contrast": [3, 6], "blur_sigma_mm": [0.1, 0.3]}, observers=("ideal",), seed=0
    )
    assert table.n_rows == 4
    assert set(zip(table.column("contrast"), table.column("blur_sigma_mm"), strict=True)) == {
        (3.0, 0.1),
        (3.0, 0.3),
        (6.0, 0.1),
        (6.0, 0.3),
    }


def test_sweep_is_deterministic():
    kwargs = dict(observers=("ideal", "NPWE"), seed=7)
    a = sweep(_base(), {"contrast": [3, 6, 9]}, **kwargs)
    b = sweep(_base(), {"contrast": [3, 6, 9]}, **kwargs)
    for col in a.columns:
        np.testing.assert_array_equal(a.column(col), b.column(col))


def test_sweep_records_a_refused_cell_as_nan_and_a_named_failure():
    """The library's guards survive the sweep: a refused cell is a gap, not a repaired point."""
    table = sweep(_base(), {"correlation_sigma_mm": [0.0, 0.3]}, observers=("ideal",), seed=0)
    d = table.column("d_ideal")
    assert np.isfinite(d[0])  # white noise is fine
    assert np.isnan(d[1])  # correlated + no floor -> refused
    assert len(table.failures) == 1
    overrides, message = table.failures[0]
    assert overrides["correlation_sigma_mm"] == 0.3
    assert "dynamic range" in message

    # Giving the noise a floor fixes it, as the message implies.
    floored = sweep(
        AtlasConfig(size=64, spacing=SPACING, white_floor_sd=8.0),
        {"correlation_sigma_mm": [0.0, 0.3]},
        observers=("ideal",),
        seed=0,
    )
    assert np.all(np.isfinite(floored.column("d_ideal")))


def test_sweep_monte_carlo_measured_tracks_the_closed_form():
    table = sweep(
        _base(), {"contrast": [4, 8]}, observers=("NPWE",), seed=1, monte_carlo=True, n_trials=8000
    )
    predicted = table.column("d_NPWE")
    measured = table.column("d_meas_NPWE")
    for p, m in zip(predicted, measured, strict=True):
        se = np.sqrt(2.0 / 8000 + p**2 / (4 * 8000))
        assert abs(m - p) < 4.0 * se


@pytest.mark.parametrize(
    "grid, message",
    [
        ({}, "grid is empty"),
        ({"nonsense": [1, 2]}, "unknown sweep condition"),
    ],
)
def test_sweep_rejects_bad_grids(grid, message):
    with pytest.raises(ValueError, match=message):
        sweep(_base(), grid, seed=0)


def test_sweep_rejects_an_unknown_observer():
    with pytest.raises(ValueError, match="unknown observer"):
        sweep(_base(), {"contrast": [3, 6]}, observers=("psychic",), seed=0)


# --------------------------------------------------------------------------------------
# transfer (regression)
# --------------------------------------------------------------------------------------


def test_fit_transfer_recovers_the_contrast_squared_law_exactly():
    """d'²_ideal = k·contrast² is exact, so the fit is a line through the origin with R² = 1."""
    table = sweep(_base(), {"contrast": [2, 3, 4, 6, 8, 10]}, observers=("ideal",), seed=0)
    c = table.column("contrast")
    d = table.column("d_ideal")

    reg = fit_transfer(c**2, d**2, names=["contrast^2"], fit_intercept=False)
    assert reg.r_squared == pytest.approx(1.0, abs=1e-9)
    # The recovered slope reproduces every point, to the phantom generator's ~1e-7 precision.
    np.testing.assert_allclose(reg.predict(c**2), d**2, rtol=1e-6)
    assert reg.coef[0] > 0.0
    assert reg.n == 6 and reg.n_predictors == 1


def test_fit_transfer_dose_law():
    table = sweep(_base(), {"noise_sd": [10, 15, 20, 30, 40]}, observers=("ideal",), seed=0)
    inv_var = 1.0 / table.column("noise_sd") ** 2
    d2 = table.column("d_ideal") ** 2
    reg = fit_transfer(inv_var, d2, fit_intercept=False)
    assert reg.r_squared == pytest.approx(1.0, abs=1e-9)


def test_fit_transfer_multiple_predictors_and_prediction():
    rng = np.random.default_rng(0)
    x0 = rng.normal(size=40)
    x1 = rng.normal(size=40)
    y = 2.0 + 3.0 * x0 - 1.5 * x1  # exact plane
    reg = fit_transfer(np.column_stack([x0, x1]), y, names=["a", "b"])
    assert reg.intercept == pytest.approx(2.0, abs=1e-9)
    np.testing.assert_allclose(reg.coef, [3.0, -1.5], atol=1e-9)
    assert reg.r_squared == pytest.approx(1.0, abs=1e-12)
    assert reg.predict(np.array([[1.0, 1.0]]))[0] == pytest.approx(2.0 + 3.0 - 1.5)


def test_fit_transfer_drops_nan_rows_from_refused_cells():
    """A sweep with a refused cell leaves NaNs; the regression drops them rather than failing."""
    x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
    y = np.array([2.0, 4.0, 6.0, np.nan, 10.0])
    reg = fit_transfer(x, y, fit_intercept=False)
    assert reg.n == 3  # two rows dropped
    assert reg.coef[0] == pytest.approx(2.0, rel=1e-9)


def test_fit_transfer_rejects_too_few_points():
    with pytest.raises(ValueError, match="too few finite rows"):
        fit_transfer(np.array([1.0]), np.array([2.0]))
