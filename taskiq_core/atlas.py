r"""Condition sweeps, NEQ, and the physical-to-task transfer.

This is the module the project is *for*. The earlier increments measure the two physical
descriptors of the system (MTF, NPS) and the performance of model observers on a detection
task; this one sweeps acquisition conditions, records the physical and the task metrics for
the *same* synthetic realisation in each cell, and quantifies how the first predicts the
second.

Three things live here.

**NEQ — the physical quantity that already knows about the task.**
:func:`neq` computes

.. math::  \mathrm{NEQ}(f) = \frac{\mathrm{MTF}^2(f)}{\mathrm{NPS}(f)}

on a common frequency axis. NEQ is not a third independent metric bolted on beside MTF and
NPS: it is exactly the combination of them that governs ideal-observer detectability. For an
ideal (prewhitening) observer detecting an *object* signal :math:`s_\mathrm{obj}` imaged
through a system of transfer :math:`\mathrm{MTF}`,

.. math::  d'^2_\mathrm{ideal}
           = \iint \frac{|\mathrm{MTF}(f)\,S_\mathrm{obj}(f)|^2}{\mathrm{NPS}(f)}\,df
           = \iint \mathrm{NEQ}(f)\,|S_\mathrm{obj}(f)|^2\,df

— so NEQ *is* the bridge from physics to task, and that identity (validated in the test
suite to machine precision) is the analytic ground truth NEQ is held to.

**The sweep.** :func:`sweep` takes a base configuration and a grid of one or more conditions
(signal contrast, disk radius, system blur, dose/noise level, noise correlation, noise
floor), and for every combination records the physical summaries and the observer
detectabilities in one :class:`AtlasTable`. It is deterministic in its seed, and — like the
rest of the library — it does not paper over a configuration the observers refuse; that cell
is recorded with a reason instead of a number.

**The transfer.** :func:`fit_transfer` regresses a task metric on physical predictor(s) and
reports the fit, its :math:`R^2`, and the residuals. Its own correctness is checked against a
law that is exact rather than empirical: ideal-observer :math:`d'^2` is exactly proportional
to signal contrast squared, so a fit of :math:`d'^2` on :math:`\mathrm{contrast}^2` must
recover a straight line through the origin with :math:`R^2 = 1` and the slope the closed form
predicts.

Notation and units
------------------
* ``NEQ`` is in ``(value^2 mm^2)^{-1}`` — the reciprocal of the NPS units, MTF being
  dimensionless. This is the unnormalised NEQ; the ICRU/DQE convention multiplies by the
  squared large-area signal-transfer gain to obtain ``mm^{-2}`` ("equivalent quanta per unit
  area"). That gain is a property of an acquisition, not of a phantom, so it is left to the
  caller; :func:`neq` reports the ratio and records the convention in ``meta``.
* Frequencies are cycles/mm; ``spacing`` is the pixel pitch in mm.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from taskiq_core.observers import burgess_eye_filter, ideal_linear, npwe, score_images
from taskiq_core.physical import MTFResult, NPSResult, gaussian_mtf
from taskiq_core.tasks import d_prime_from_scores, ske_bke_trials

__all__ = [
    "NEQResult",
    "AtlasConfig",
    "AtlasTable",
    "RegressionResult",
    "neq",
    "sweep",
    "fit_transfer",
]


# --------------------------------------------------------------------------------------
# NEQ
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class NEQResult:
    """Noise-equivalent quanta on a common frequency axis.

    Attributes
    ----------
    frequency:
        Radial spatial frequency in cycles/mm.
    neq:
        ``MTF^2 / NPS`` on :attr:`frequency`, in ``(value^2 mm^2)^{-1}``.
    mtf, nps:
        The MTF and NPS values interpolated onto :attr:`frequency`, so the ratio can be
        inspected term by term.
    integral:
        ``∫ NEQ(f) 2πf df`` over the axis — the rotationally-averaged area integral of NEQ,
        useful as a single-number summary of the system.
    peak:
        Maximum of :attr:`neq`.
    meta:
        Records the NEQ convention (unnormalised) and the interpolation.

    """

    frequency: np.ndarray
    neq: np.ndarray
    mtf: np.ndarray
    nps: np.ndarray
    integral: float
    peak: float
    meta: dict[str, Any] = field(default_factory=dict)


def _as_curve(
    obj: Any, kind: str
) -> tuple[np.ndarray | None, np.ndarray] | Callable[[np.ndarray], np.ndarray] | float:
    """Normalise an MTF/NPS argument to (freq, values), a callable, or a scalar."""
    if kind == "mtf" and isinstance(obj, MTFResult):
        return obj.frequency, obj.mtf
    if kind == "nps" and isinstance(obj, NPSResult):
        return obj.frequency, obj.nps_radial
    if callable(obj):
        return obj
    if np.isscalar(obj):
        return float(obj)  # type: ignore[arg-type]
    arr = np.asarray(obj)
    if arr.ndim == 2 and arr.shape[0] == 2:  # (freq, values) stacked
        return arr[0], arr[1]
    raise ValueError(
        f"{kind} must be a {'MTFResult' if kind == 'mtf' else 'NPSResult'}, a callable of "
        f"frequency, a scalar, or a (2, N) array of (frequency, values); got {type(obj)}"
    )


def _sample(curve: Any, frequency: np.ndarray, kind: str) -> np.ndarray:
    """Evaluate a normalised curve on ``frequency``, refusing to extrapolate."""
    if callable(curve):
        return np.asarray(curve(frequency), dtype=np.float64)
    if isinstance(curve, float):
        return np.full(frequency.shape, curve, dtype=np.float64)
    f, v = curve
    f = np.asarray(f, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    if frequency.min() < f.min() - 1e-9 or frequency.max() > f.max() + 1e-9:
        raise ValueError(
            f"the requested frequency range [{frequency.min():.3g}, {frequency.max():.3g}] "
            f"exceeds the {kind} data range [{f.min():.3g}, {f.max():.3g}] cycles/mm; NEQ "
            "will not extrapolate. Pass an explicit `frequency` inside the overlap of the MTF "
            "and NPS axes."
        )
    return np.interp(frequency, f, v)


def neq(
    mtf: MTFResult | np.ndarray | Callable[[np.ndarray], np.ndarray],
    nps: NPSResult | np.ndarray | Callable[[np.ndarray], np.ndarray] | float,
    *,
    frequency: np.ndarray | None = None,
    nps_floor_fraction: float = 0.0,
) -> NEQResult:
    r"""Noise-equivalent quanta, :math:`\mathrm{NEQ}(f) = \mathrm{MTF}^2(f)/\mathrm{NPS}(f)`.

    Parameters
    ----------
    mtf:
        The system MTF: an :class:`~taskiq_core.physical.MTFResult`, a callable of radial
        frequency (e.g. :func:`~taskiq_core.physical.gaussian_mtf` bound to a σ), or a
        ``(2, N)`` array of ``(frequency, mtf)``.
    nps:
        The NPS: an :class:`~taskiq_core.physical.NPSResult` (its radial average is used), a
        scalar (white noise), a callable of radial frequency, or a ``(2, N)`` array.
    frequency:
        The common axis to report NEQ on. Defaults to the MTF's own frequency axis
        (excluding DC, where NEQ is not defined for a band-pass system). Must lie within the
        range of both inputs — NEQ does not extrapolate.
    nps_floor_fraction:
        If ``> 0``, the NPS is clamped from below at this fraction of its maximum before the
        division, exactly as :func:`~taskiq_core.observers.ideal_linear` does — because
        ``1/NPS`` is meaningless where the noise power has decayed to nothing. ``0`` (default)
        divides as-is and raises on a zero NPS bin.

    Returns
    -------
    NEQResult

    Raises
    ------
    ValueError
        On a requested frequency outside the data, or a zero/negative NPS with no floor.

    """
    mtf_curve = _as_curve(mtf, "mtf")
    nps_curve = _as_curve(nps, "nps")

    if frequency is None:
        if isinstance(mtf, MTFResult):
            f = np.asarray(mtf.frequency, dtype=np.float64)
            frequency = f[f > 0.0]
        elif not callable(mtf_curve) and not isinstance(mtf_curve, float):
            f = np.asarray(mtf_curve[0], dtype=np.float64)
            frequency = f[f > 0.0]
        else:
            raise ValueError(
                "frequency must be given explicitly when the MTF is a callable or scalar "
                "(there is no frequency axis to inherit)"
            )
    frequency = np.asarray(frequency, dtype=np.float64)
    if frequency.ndim != 1 or frequency.size < 2:
        raise ValueError("frequency must be a 1-D array of at least 2 points")

    mtf_vals = _sample(mtf_curve, frequency, "MTF")
    nps_vals = _sample(nps_curve, frequency, "NPS")

    if not np.all(np.isfinite(mtf_vals)) or not np.all(np.isfinite(nps_vals)):
        raise ValueError("the interpolated MTF or NPS contains non-finite values")

    nps_max = float(np.max(nps_vals))
    if nps_max <= 0.0:
        raise ValueError("the NPS is zero everywhere; NEQ is undefined")
    if nps_floor_fraction > 0.0:
        if not (0.0 < nps_floor_fraction < 1.0):
            raise ValueError(f"nps_floor_fraction must be in (0, 1), got {nps_floor_fraction}")
        nps_vals = np.maximum(nps_vals, nps_floor_fraction * nps_max)
    elif np.any(nps_vals <= 0.0):
        raise ValueError(
            "the NPS is zero or negative at some frequency, so NEQ = MTF^2/NPS would divide "
            "by zero. Pass nps_floor_fraction to clamp the NPS from below, or restrict the "
            "frequency range to where the NPS is positive."
        )

    neq_vals = mtf_vals**2 / nps_vals
    integral = float(np.trapezoid(neq_vals * 2.0 * np.pi * frequency, frequency))

    return NEQResult(
        frequency=frequency,
        neq=neq_vals,
        mtf=mtf_vals,
        nps=nps_vals,
        integral=integral,
        peak=float(np.max(neq_vals)),
        meta={
            "convention": "unnormalised NEQ = MTF^2 / NPS, units (value^2 mm^2)^-1",
            "nps_floor_fraction": nps_floor_fraction,
        },
    )


# --------------------------------------------------------------------------------------
# the sweep
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class AtlasConfig:
    """The base acquisition and task configuration a sweep varies from.

    A cell of the sweep is this configuration with one or more fields overridden. The disk is
    imaged through a Gaussian system blur of ``blur_sigma_mm`` — which is what gives the cell
    a non-trivial MTF, ``exp(-2π²·blur_sigma_mm²·f²)`` — so sweeping the blur sweeps MTF and
    task performance together, the whole point of the atlas.
    """

    size: int = 64
    spacing: float = 0.1
    radius_mm: float = 0.8
    contrast: float = 6.0
    blur_sigma_mm: float = 0.15  # system blur applied to the disk; sets the MTF
    noise_sd: float = 20.0
    correlation_sigma_mm: float = 0.0
    white_floor_sd: float = 0.0
    eye_peak: float = 1.0


#: Which conditions a sweep understands, and the ``AtlasConfig`` field each drives.
SWEEP_FIELDS: tuple[str, ...] = (
    "contrast",
    "radius_mm",
    "blur_sigma_mm",
    "noise_sd",
    "correlation_sigma_mm",
    "white_floor_sd",
)


@dataclass
class AtlasTable:
    """The result of a sweep: paired physical and task metrics, one row per cell.

    Attributes
    ----------
    variables:
        The names of the swept conditions, in grid order.
    columns:
        Ordered column names: the swept variables first, then the recorded metrics.
    data:
        ``{column: np.ndarray}``; every array has one entry per cell. Refused cells carry
        ``np.nan`` in their metric columns (their reason is in :attr:`failures`).
    failures:
        ``(cell_values, message)`` for each configuration the observers refused.
    meta:
        Provenance (base config, observers, seed, whether Monte Carlo was run).

    """

    variables: tuple[str, ...]
    columns: tuple[str, ...]
    data: dict[str, np.ndarray]
    failures: list[tuple[dict[str, float], str]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def column(self, name: str) -> np.ndarray:
        """The array for one column."""
        if name not in self.data:
            raise KeyError(f"no column {name!r}; have {self.columns}")
        return self.data[name]

    @property
    def n_rows(self) -> int:
        """The number of cells (rows) in the table."""
        return len(next(iter(self.data.values()))) if self.data else 0

    def to_dataframe(self) -> Any:  # pragma: no cover - exercised only if pandas is installed
        """Return the table as a ``pandas.DataFrame`` (requires the optional pandas extra)."""
        try:
            import pandas as pd  # type: ignore[import-untyped]
        except ImportError as exc:  # noqa: F841
            raise ImportError(
                "to_dataframe requires pandas; install the optional extra "
                "(`pip install taskiq-core[pandas]`) or use .data / .column()"
            ) from exc
        return pd.DataFrame({c: self.data[c] for c in self.columns})


def _cell_nps(config: AtlasConfig) -> tuple[Callable[[np.ndarray], np.ndarray], float]:
    """The analytic radial NPS of a cell's noise, and its white-floor level."""
    area = config.spacing * config.spacing
    coloured_level = config.noise_sd**2 * area
    floor_level = config.white_floor_sd**2 * area
    sigma_c = config.correlation_sigma_mm

    def nps(fr: np.ndarray) -> np.ndarray:
        return coloured_level * np.exp(-4.0 * np.pi**2 * sigma_c**2 * fr**2) + floor_level

    return nps, floor_level


def sweep(
    config: AtlasConfig,
    grid: dict[str, Sequence[float]],
    *,
    observers: Sequence[str] = ("ideal", "NPWE"),
    seed: int = 0,
    monte_carlo: bool = False,
    n_trials: int = 2000,
    progress: Callable[[str], None] | None = None,
) -> AtlasTable:
    r"""Sweep one or more acquisition conditions and record physics and task side by side.

    For every combination in the Cartesian product of ``grid``, the cell's configuration is
    ``config`` with those fields overridden. Recorded per cell:

    * **physical** — ``mtf50`` (the frequency where the Gaussian system MTF falls to 0.5),
      ``nps0`` (the NPS level at low frequency), ``neq_peak`` and ``neq_integral``;
    * **task** — for each requested observer, the closed-form ``d'`` (``d_<obs>``) and the
      corresponding ``pc_<obs>`` = Φ(d'/√2); plus ``efficiency_<obs>`` = (d'/d'_ideal)² when
      the ideal observer is included. With ``monte_carlo=True`` the measured ``d'`` from
      ``n_trials`` scored trials is also recorded as ``d_meas_<obs>``.

    Observers understood: ``"ideal"`` (prewhitening), ``"NPW"``, ``"NPWE"`` (with the eye
    filter). The channelized observer is not swept here — it has no closed form and would
    turn a fast analytic sweep into a slow Monte-Carlo one; use :func:`taskiq_core.cho`
    directly for that.

    A cell the observers refuse (e.g. the ideal observer on correlated noise with no floor)
    is not skipped and not repaired: its metric columns are ``nan`` and the reason is appended
    to :attr:`AtlasTable.failures`.

    Parameters
    ----------
    config:
        The base configuration.
    grid:
        ``{condition: values}`` for one or more of :data:`SWEEP_FIELDS`.
    observers:
        Which observers to evaluate.
    seed:
        Base seed. Each cell uses a distinct, deterministic offset of it, so the whole sweep
        is reproducible.
    monte_carlo:
        Also generate and score trials per cell (slower), to record measured ``d'`` beside the
        closed form.
    n_trials:
        Trials per class when ``monte_carlo`` is true.
    progress:
        Optional callback receiving a short status string per cell.

    Returns
    -------
    AtlasTable

    """
    say = progress or (lambda _m: None)

    for name in grid:
        if name not in SWEEP_FIELDS:
            raise ValueError(f"unknown sweep condition {name!r}; choose from {SWEEP_FIELDS}")
    if not grid:
        raise ValueError("grid is empty; give at least one condition to sweep")
    for name, values in grid.items():
        if len(list(values)) < 1:
            raise ValueError(f"condition {name!r} has no values")

    obs_names = tuple(observers)
    for o in obs_names:
        if o not in ("ideal", "NPW", "NPWE"):
            raise ValueError(f"unknown observer {o!r}; choose from 'ideal', 'NPW', 'NPWE'")

    variables = tuple(grid.keys())
    value_lists = [list(grid[v]) for v in variables]

    metric_cols: list[str] = ["mtf50", "nps0", "neq_peak", "neq_integral"]
    for o in obs_names:
        metric_cols += [f"d_{o}", f"pc_{o}"]
        if "ideal" in obs_names:
            metric_cols.append(f"efficiency_{o}")
        if monte_carlo:
            metric_cols.append(f"d_meas_{o}")
    # dedupe while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for c in metric_cols:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    metric_cols = deduped

    columns = variables + tuple(metric_cols)
    data: dict[str, list[float]] = {c: [] for c in columns}
    failures: list[tuple[dict[str, float], str]] = []

    combos = list(itertools.product(*value_lists))
    for i, combo in enumerate(combos):
        overrides = {v: float(x) for v, x in zip(variables, combo, strict=True)}
        cell = replace(config, **overrides)  # type: ignore[arg-type]
        say(f"cell {i + 1}/{len(combos)}: " + ", ".join(f"{k}={v:g}" for k, v in overrides.items()))

        for v, x in overrides.items():
            data[v].append(x)

        try:
            row = _evaluate_cell(cell, obs_names, seed + i, monte_carlo, n_trials)
        except ValueError as exc:
            for c in metric_cols:
                data[c].append(float("nan"))
            failures.append((overrides, str(exc)))
            continue

        for c in metric_cols:
            data[c].append(row[c])

    return AtlasTable(
        variables=variables,
        columns=columns,
        data={c: np.asarray(v, dtype=np.float64) for c, v in data.items()},
        failures=failures,
        meta={
            "base_config": config,
            "observers": obs_names,
            "seed": seed,
            "monte_carlo": monte_carlo,
            "n_trials": n_trials if monte_carlo else 0,
        },
    )


def _evaluate_cell(
    cell: AtlasConfig,
    obs_names: tuple[str, ...],
    seed: int,
    monte_carlo: bool,
    n_trials: int,
) -> dict[str, float]:
    """Compute the physical and task metrics for one cell. May raise (refused config)."""
    # The disk imaged through the system blur: make_disk_signal's exact Gaussian edge IS the
    # system PSF, so the cell's MTF is gaussian_mtf(f, blur_sigma_mm).
    signal = _blurred_disk(cell)
    nps_callable, _ = _cell_nps(cell)

    # Only generate and score trials when a measured d' is actually asked for — the closed-form
    # metrics need nothing but the signal and the analytic NPS, which keeps a large sweep fast.
    trials = None
    if monte_carlo:
        trials = ske_bke_trials(
            signal,
            n_trials,
            cell.spacing,
            cell.noise_sd,
            seed=seed,
            correlation_sigma_mm=cell.correlation_sigma_mm,
            white_floor_sd=cell.white_floor_sd,
        )
        signal = trials.signal

    row: dict[str, float] = {}

    # physical summaries
    sigma = cell.blur_sigma_mm
    if sigma > 0.0:
        # MTF = exp(-2π²σ²f²) = 0.5  ->  f = sqrt(ln2 / 2) / (π σ)
        row["mtf50"] = float(np.sqrt(np.log(2.0) / 2.0) / (np.pi * sigma))
    else:
        row["mtf50"] = float("inf")
    row["nps0"] = float(nps_callable(np.zeros(1))[0])

    nyq = 1.0 / (2.0 * cell.spacing)
    freq = np.linspace(nyq / 200.0, nyq, 200)
    neq_res = neq(lambda f: gaussian_mtf(f, sigma), nps_callable, frequency=freq)
    row["neq_peak"] = neq_res.peak
    row["neq_integral"] = neq_res.integral

    # task: closed-form d' per observer
    d_ideal: float | None = None
    results = {}
    for o in obs_names:
        if o == "ideal":
            res = ideal_linear(signal, nps_callable, cell.spacing)
            d_ideal = res.d_prime
        elif o == "NPW":
            res = npwe(signal, nps_callable, cell.spacing)
        else:  # NPWE
            res = npwe(
                signal, nps_callable, cell.spacing, eye_filter=burgess_eye_filter(cell.eye_peak)
            )
        results[o] = res
        row[f"d_{o}"] = res.d_prime
        row[f"pc_{o}"] = res.auc  # AUC == Phi(d'/sqrt2) for these observers

    if "ideal" in obs_names and d_ideal and d_ideal > 0.0:
        for o in obs_names:
            row[f"efficiency_{o}"] = float((results[o].d_prime / d_ideal) ** 2)

    if monte_carlo:
        assert trials is not None  # set above whenever monte_carlo is true
        for o in obs_names:
            present = score_images(trials.present, results[o].template)
            absent = score_images(trials.absent, results[o].template)
            row[f"d_meas_{o}"] = d_prime_from_scores(present, absent)

    return row


def _blurred_disk(cell: AtlasConfig) -> np.ndarray:
    """The disk signal for a cell — a disk with the system Gaussian blur as its edge."""
    from taskiq_core.phantoms import make_disk_signal

    return make_disk_signal(
        cell.size,
        radius_mm=cell.radius_mm,
        contrast=cell.contrast,
        spacing=cell.spacing,
        edge_sigma_mm=cell.blur_sigma_mm,
    ).image.astype(np.float64)


# --------------------------------------------------------------------------------------
# the transfer: regression
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class RegressionResult:
    """An ordinary-least-squares fit of a task metric on physical predictor(s).

    Attributes
    ----------
    coef:
        Slope(s), one per predictor.
    intercept:
        Fitted intercept (0.0 if ``fit_intercept=False``).
    r_squared:
        Coefficient of determination. For a relationship that is exactly linear — e.g. ideal
        ``d'^2`` against ``contrast^2`` — this is 1 to within floating point, which is how the
        regression itself is validated.
    predictor_names:
        Names of the predictors, in the order of :attr:`coef`.
    residuals:
        ``y - ŷ`` at the fitted points.
    n, n_predictors:
        Sample size and number of predictors.
    fit_intercept:
        Whether an intercept was fitted.

    """

    coef: np.ndarray
    intercept: float
    r_squared: float
    predictor_names: tuple[str, ...]
    residuals: np.ndarray
    n: int
    n_predictors: int
    fit_intercept: bool

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Apply the fit to new predictor values (shape ``(m,)`` or ``(m, n_predictors)``)."""
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None] if self.n_predictors == 1 else x[None, :]
        if x.shape[1] != self.n_predictors:
            raise ValueError(f"expected {self.n_predictors} predictor(s) per row, got {x.shape[1]}")
        return x @ self.coef + self.intercept


def fit_transfer(
    x: np.ndarray,
    y: np.ndarray,
    *,
    names: Sequence[str] | None = None,
    fit_intercept: bool = True,
) -> RegressionResult:
    r"""Ordinary-least-squares regression of a task metric ``y`` on physical predictor(s) ``x``.

    This is the "physical → task" transfer: fit the detectability (or ``d'^2``, or PC) that
    the sweep measured against the physical summaries (NEQ integral, MTF50, dose, …) it
    recorded alongside, and read off how strongly, and how linearly, the physics predicts the
    task.

    Rows containing NaN in ``x`` or ``y`` (a refused sweep cell) are dropped, with at least
    two finite rows required.

    Parameters
    ----------
    x:
        Predictors, shape ``(n,)`` for a single predictor or ``(n, p)`` for several.
    y:
        The response, shape ``(n,)``.
    names:
        Optional predictor names, for the result.
    fit_intercept:
        Fit an intercept term. Set ``False`` to force the line through the origin — correct
        for laws like ``d'^2 = k · contrast^2`` that have no constant term, and the setting
        under which that law's slope is recovered exactly.

    Returns
    -------
    RegressionResult

    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2:
        raise ValueError(f"x must be 1-D or 2-D, got shape {x.shape}")
    if x.shape[0] != y.shape[0]:
        raise ValueError(f"x has {x.shape[0]} rows but y has {y.shape[0]}")

    finite = np.all(np.isfinite(x), axis=1) & np.isfinite(y)
    x, y = x[finite], y[finite]
    n, p = x.shape
    if n < p + (1 if fit_intercept else 0) + 1:
        raise ValueError(
            f"too few finite rows ({n}) to fit {p} predictor(s)"
            f"{' plus an intercept' if fit_intercept else ''}"
        )

    design = np.hstack([np.ones((n, 1)), x]) if fit_intercept else x
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    y_hat = design @ beta
    residuals = y - y_hat

    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2)) if fit_intercept else float(np.sum(y**2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else float("nan")

    if fit_intercept:
        intercept, coef = float(beta[0]), beta[1:]
    else:
        intercept, coef = 0.0, beta

    if names is None:
        names = tuple(f"x{i}" for i in range(p))
    else:
        names = tuple(names)
        if len(names) != p:
            raise ValueError(f"got {len(names)} names for {p} predictor(s)")

    return RegressionResult(
        coef=coef,
        intercept=intercept,
        r_squared=r_squared,
        predictor_names=names,
        residuals=residuals,
        n=n,
        n_predictors=p,
        fit_intercept=fit_intercept,
    )
