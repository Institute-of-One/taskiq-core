r"""Model observers: the link from physical image quality to task performance.

An observer reduces an image to a scalar test statistic. The separation between that
statistic's signal-present and signal-absent distributions is the detectability index

.. math::  d' = \frac{\langle\lambda\rangle_1 - \langle\lambda\rangle_0}
                     {\sqrt{\tfrac12(\sigma_1^2 + \sigma_0^2)}}

which, for the SKE/BKE detection task these observers are built for, is the number this
whole project is trying to predict from MTF and NPS.

Two families are implemented.

**Fourier-domain linear observers** (:func:`npwe`, :func:`ideal_linear`). For a
signal-known-exactly task in stationary Gaussian noise, a linear observer with template
:math:`w` has a *closed-form* detectability

.. math::  d'^2 = \frac{\left[\iint W^*(f) S(f)\, df\right]^2}
                       {\iint |W(f)|^2\, \mathrm{NPS}(f)\, df}

so no Monte Carlo is needed — and, more to the point, the closed form is an analytic
ground truth to validate the implementation against. The two templates are

* :func:`npwe` — non-prewhitening with an eye filter, :math:`W = S E^2`, giving

  .. math::  d'^2_{\mathrm{NPWE}} = \frac{\left[\iint |S|^2 E^2\, df\right]^2}
                                          {\iint |S|^2 E^4\, \mathrm{NPS}\, df}

  With no eye filter (:math:`E \equiv 1`) this is the plain non-prewhitening matched
  filter, whose white-noise detectability collapses to :math:`d' = \|s\|_2 / \sigma` — an
  exact identity, used as the primary unit test because it ties the NPS normalisation in
  :mod:`taskiq_core.physical` directly to :math:`d'`.

* :func:`ideal_linear` — the prewhitening matched filter :math:`W = S/\mathrm{NPS}`,
  which for stationary Gaussian noise *is* the Hotelling observer and hence the upper
  bound on every linear observer:

  .. math::  d'^2_{\mathrm{ideal}} = \iint \frac{|S(f)|^2}{\mathrm{NPS}(f)}\, df

**The channelized Hotelling observer** (:func:`cho`), which is *not* closed-form: it
estimates a channel covariance from image ensembles. That makes it the one place in this
codebase where a statistical estimate can quietly go wrong, so it is guarded. An
ill-conditioned covariance raises instead of returning a number; the two estimation
methods are biased in opposite directions and are documented as bracketing the truth
rather than as "the" answer; and the tests hold the observer to the closed-form
white-noise value :math:`d'^2 = (Us)^\top (\sigma^2 U U^\top)^{-1} (U s)`.

Three traps that return a *plausible* number rather than an error
-----------------------------------------------------------------
Every one of these was found by comparing the closed form against a simulation, and each
now raises rather than lying:

1. **A prewhitening observer cannot use a noise model whose power decays to nothing.**
   Weighting by :math:`1/\mathrm{NPS}` makes the least-noisy frequencies dominate, so a
   Gaussian-correlated NPS (which falls ~70 orders of magnitude across the frequency
   plane) yields a ``d'`` of order ``1e29``, assembled entirely from bins where the noise
   has underflowed and the "signal" is floating-point rounding. Real noise has a floor;
   see :func:`ideal_linear`.
2. **A measured NPS has a zeroed DC bin**, because :func:`~taskiq_core.physical.nps_2d`
   detrends. Bins with zero NPS contribute no noise variance, so ``d'`` comes out high —
   about 3 % high for a disk signal, whose DC bin carries ~6 % of the noise weight. An eye
   filter has :math:`E(0) = 0` and is immune; plain NPW is not. See :func:`npwe`.
3. **Laguerre-Gauss channels are only orthonormal if they fit in the image.** Too wide a
   channel set is silently truncated, and "orthonormal channels" that are not orthonormal
   is exactly the kind of thing nothing downstream would catch. See
   :func:`laguerre_gauss_channels`.

Conventions
-----------
* Templates and channels are applied as plain pixel sums, :math:`\lambda = \sum_i w_i g_i`,
  so any overall scaling of :math:`w` cancels in :math:`d'`.
* ``nps`` is in the units and layout of :class:`taskiq_core.physical.NPSResult` —
  ``value^2 mm^2``, DC-centred — and an ``NPSResult`` can be passed straight in.
* Frequencies are cycles/mm; ``spacing`` is the pixel pitch in mm.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.special import eval_laguerre, ndtr

from taskiq_core.physical import NPSResult
from taskiq_core.tasks import auc_from_scores, d_prime_from_scores

__all__ = [
    "ObserverResult",
    "CHOResult",
    "burgess_eye_filter",
    "npwe",
    "ideal_linear",
    "score_images",
    "d_prime_from_scores",
    "auc_from_scores",
    "laguerre_gauss_channels",
    "dense_dog_channels",
    "gabor_channels",
    "cho",
]


# --------------------------------------------------------------------------------------
# results
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class ObserverResult:
    """Detectability of a Fourier-domain linear observer.

    Attributes
    ----------
    name:
        ``"npwe"``, ``"npw"`` (an NPWE with no eye filter), or ``"ideal_linear"``.
    d_prime:
        Detectability index, from the closed form — not from simulated trials.
    auc:
        Area under the ROC curve implied by :attr:`d_prime`, ``Phi(d' / sqrt(2))``. Exact
        for these observers: their test statistic is a linear functional of Gaussian noise,
        hence Gaussian with the same variance under both hypotheses.
    template:
        Spatial template ``w``, the same shape as the signal. Feed it to
        :func:`score_images` to score real images with this observer.
    signal_power, noise_power:
        Numerator and denominator of ``d_prime**2`` before the ratio is taken, kept so that
        a surprising ``d'`` can be traced to whichever of the two moved.
    spacing, meta:
        Echo of the inputs and settings.
    """

    name: str
    d_prime: float
    auc: float
    template: np.ndarray
    signal_power: float
    noise_power: float
    spacing: float
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, eq=False)
class CHOResult:
    """Detectability of a channelized Hotelling observer, estimated from image ensembles.

    Attributes
    ----------
    d_prime:
        Detectability index. With ``method="split"`` this is the *empirical* separation of
        the scores on held-out images, so it carries no resubstitution bias. With
        ``method="resubstitution"`` it is ``sqrt(dv^T K^-1 dv)`` evaluated on the same data
        that trained the template, which is biased **high**.
    auc:
        Empirical area under the ROC curve of the scores (Mann-Whitney U) — measured, not
        assumed Gaussian.
    scores_present, scores_absent:
        The test statistic on each scored image.
    channel_template:
        The Hotelling template in channel space, ``w = K^-1 dv`` (length ``n_channels``).
    spatial_template:
        The same template projected back to pixels, ``U^T w`` — comparable, up to scale,
        with the templates from :func:`npwe` and :func:`ideal_linear`.
    channel_covariance:
        The pooled channel covariance ``K``.
    delta_v:
        Mean channel-response difference between the two classes.
    condition_number:
        Condition number of ``K``. Large means the channel set is close to degenerate at
        this sample size; past ``max_condition`` the estimate raises rather than returning
        a number that only looks like an answer.
    method, n_channels, n_present, n_absent, internal_noise, meta:
        Provenance of the estimate.
    """

    d_prime: float
    auc: float
    scores_present: np.ndarray
    scores_absent: np.ndarray
    channel_template: np.ndarray
    spatial_template: np.ndarray
    channel_covariance: np.ndarray
    delta_v: np.ndarray
    condition_number: float
    method: str
    n_channels: int
    n_present: int
    n_absent: int
    internal_noise: float
    meta: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------------------


def _check_spacing(spacing: float) -> float:
    spacing = float(spacing)
    if not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError(f"spacing must be a finite positive number of mm, got {spacing!r}")
    return spacing


def _as_signal(signal: np.ndarray) -> np.ndarray:
    sig = np.asarray(signal, dtype=np.float64)
    if sig.ndim != 2:
        raise ValueError(f"signal must be a 2-D image, got shape {sig.shape}")
    if not np.all(np.isfinite(sig)):
        raise ValueError("signal contains non-finite values")
    if not np.any(sig):
        raise ValueError("signal is identically zero: there is nothing to detect")
    return sig


def _frequency_grid(shape: tuple[int, int], spacing: float) -> np.ndarray:
    """Radial frequency in cycles/mm on the ``fft2`` layout (DC at ``[0, 0]``)."""
    ny, nx = shape
    fy = np.fft.fftfreq(ny, d=spacing)[:, None]
    fx = np.fft.fftfreq(nx, d=spacing)[None, :]
    return np.hypot(fy, fx)


def _nps_grid(
    nps: NPSResult | np.ndarray | Callable[[np.ndarray], np.ndarray] | float,
    shape: tuple[int, int],
    spacing: float,
    *,
    layout: str = "centered",
    require_positive: bool = False,
) -> np.ndarray:
    """Normalise any accepted NPS specification to an ``fft2``-layout grid.

    Accepts an :class:`~taskiq_core.physical.NPSResult` (the usual case), a scalar (white
    noise), a callable of radial frequency (an analytic model), or a raw 2-D array.

    The ``layout`` of a raw array has to be stated rather than guessed: an NPS that is
    silently off by an ``fftshift`` still yields a plausible-looking ``d'``, and nothing
    downstream would ever catch it.
    """
    fr = _frequency_grid(shape, spacing)

    if isinstance(nps, NPSResult):
        if nps.roi_shape != shape:
            raise ValueError(
                f"the NPS was measured on {nps.roi_shape} ROIs but the signal is {shape}; "
                "they must lie on the same grid for the frequency axes to line up"
            )
        if not np.isclose(nps.spacing, spacing):
            raise ValueError(
                f"the NPS was measured at spacing {nps.spacing} mm but the signal is at "
                f"{spacing} mm"
            )
        grid = np.fft.ifftshift(np.asarray(nps.nps, dtype=np.float64))
    elif callable(nps):
        grid = np.asarray(nps(fr), dtype=np.float64)
        if grid.shape != shape:
            raise ValueError(
                f"the nps callable returned shape {grid.shape}, expected {shape}: it must be "
                "a function of the radial-frequency grid it is handed"
            )
    elif np.isscalar(nps):
        level = float(nps)  # type: ignore[arg-type]
        if not np.isfinite(level) or level <= 0.0:
            raise ValueError(f"a scalar (white) NPS must be finite and > 0, got {nps!r}")
        grid = np.full(shape, level, dtype=np.float64)
    else:
        grid = np.asarray(nps, dtype=np.float64)
        if grid.shape != shape:
            raise ValueError(f"the nps array has shape {grid.shape}, expected {shape}")
        if layout == "centered":
            grid = np.fft.ifftshift(grid)
        elif layout != "fft":
            raise ValueError(f"nps_layout must be 'centered' or 'fft', got {layout!r}")

    if not np.all(np.isfinite(grid)):
        raise ValueError("the NPS contains non-finite values")
    if np.any(grid < 0.0):
        raise ValueError("the NPS contains negative values, but it is a power spectrum")
    if require_positive and np.any(grid <= 0.0):
        n_zero = int(np.count_nonzero(grid <= 0.0))
        hint = (
            " The DC bin is one of them, which is exactly what nps_2d leaves behind after "
            "detrending. A prewhitening observer divides by the NPS, so it cannot use a "
            "measured NPS unmodified: pass an analytic NPS model (a callable or a scalar), "
            "or fill the DC bin with whatever noise power at DC you are prepared to assume."
            if grid[0, 0] <= 0.0
            else ""
        )
        raise ValueError(
            f"a prewhitening observer needs a strictly positive NPS, but {n_zero} frequency "
            f"bin(s) are zero or negative.{hint}"
        )
    return grid


def burgess_eye_filter(
    peak_cycles_per_mm: float = 1.0, exponent: float = 1.3
) -> Callable[[np.ndarray], np.ndarray]:
    r"""Human visual-response ("eye") filter, :math:`E(f) \propto f^{n} e^{-c f^2}`.

    Returns a callable of radial frequency, normalised to a peak of 1 at
    ``peak_cycles_per_mm`` (the constant follows from the peak location:
    :math:`c = n/(2 f_p^2)`). The band-pass shape is what makes a non-prewhitening observer
    a plausible model of a human: it discounts the very low frequencies that a plain matched
    filter would happily integrate over.

    Note ``E(0) = 0``. That is intended — and it has a useful consequence: an NPWE observer
    is indifferent to the DC bin, so a *measured* (detrended, DC-zero) NPS can be handed to
    :func:`npwe` with no special treatment, unlike :func:`ideal_linear`.

    Parameters
    ----------
    peak_cycles_per_mm:
        Frequency of peak sensitivity, in cycles/mm. The human literature quotes the peak in
        cycles/*degree*; converting needs a viewing distance and a display pitch, which are
        properties of an experiment rather than of an image, so that conversion is left to
        the caller.
    exponent:
        The exponent ``n``; 1.3 is the usual value.
    """
    f_peak = float(peak_cycles_per_mm)
    n = float(exponent)
    if not np.isfinite(f_peak) or f_peak <= 0.0:
        raise ValueError(f"peak_cycles_per_mm must be finite and > 0, got {peak_cycles_per_mm!r}")
    if not np.isfinite(n) or n <= 0.0:
        raise ValueError(f"exponent must be finite and > 0, got {exponent!r}")

    def eye(fr: np.ndarray) -> np.ndarray:
        rho = np.asarray(fr, dtype=np.float64) / f_peak
        # (f/f_p)^n exp(-(n/2)((f/f_p)^2 - 1)), which is exactly 1 at f = f_p.
        return rho**n * np.exp(-0.5 * n * (rho**2 - 1.0))

    return eye


def _gaussian_auc(d_prime: float) -> float:
    """AUC implied by ``d'`` for an equal-variance Gaussian statistic: ``Phi(d'/sqrt(2))``."""
    return float(ndtr(d_prime / np.sqrt(2.0)))


# --------------------------------------------------------------------------------------
# Fourier-domain linear observers
# --------------------------------------------------------------------------------------


#: Below this fraction of its peak, a prewhitening observer's ``1/NPS`` weighting is
#: numerically meaningless — see the guard in :func:`_linear_observer`.
_MIN_NPS_FRACTION = 1e-8


def _linear_observer(
    name: str,
    signal: np.ndarray,
    nps: Any,
    spacing: float,
    *,
    eye_filter: Callable[[np.ndarray], np.ndarray] | None,
    prewhiten: bool,
    nps_layout: str,
    zero_nps_tolerance: float = 1e-3,
    noise_floor: float | None = None,
) -> ObserverResult:
    """Shared machinery for the closed-form linear observers.

    The sums below approximate the continuous integrals with ``S = A * fft2(s)`` (``A`` the
    pixel area) and frequency bin width ``du dv = 1/(N A)``. Those factors of ``A`` cancel
    exactly in the ratio that forms ``d'``, so the result is identical to the pixel-domain
    definition ``w.s / sqrt(w^T K w)`` — which is what makes the white-noise identity
    ``d' = ||s||/sigma`` exact rather than approximate.

    Two guards live here, because both failure modes return a plausible number rather than
    an error. See :func:`npwe` and :func:`ideal_linear` for what they mean to a caller.
    """
    sig = _as_signal(signal)
    spacing = _check_spacing(spacing)
    ny, nx = sig.shape
    area = spacing * spacing
    du_dv = 1.0 / (ny * nx * area)

    nps_grid = _nps_grid(nps, (ny, nx), spacing, layout=nps_layout, require_positive=prewhiten)
    fr = _frequency_grid((ny, nx), spacing)

    if eye_filter is None:
        eye = np.ones((ny, nx), dtype=np.float64)
    else:
        eye = np.asarray(eye_filter(fr), dtype=np.float64)
        if eye.shape != (ny, nx):
            raise ValueError(f"eye_filter returned shape {eye.shape}, expected {(ny, nx)}")
        if not np.all(np.isfinite(eye)) or np.any(eye < 0.0):
            raise ValueError("eye_filter must return finite, non-negative values")

    spectrum = area * np.fft.fft2(sig)  # S(f)
    power = np.abs(spectrum) ** 2  # |S(f)|^2

    nps_max = float(nps_grid.max())
    if nps_max <= 0.0:
        raise ValueError("the NPS is zero everywhere: there is no noise, so d' is infinite")

    if prewhiten:
        # Guard: a prewhitening observer weights by 1/NPS, so a noise model whose power
        # decays to (numerically) nothing at high frequency produces an enormous d' built
        # entirely out of bins where BOTH the noise power has underflowed and the signal
        # power is floating-point rounding. A Gaussian-correlated NPS does exactly this.
        # Real noise has a floor; an NPS model without one is not usable here.
        floor_applied = None
        if noise_floor is not None:
            floor = float(noise_floor)
            if not (0.0 < floor < 1.0):
                raise ValueError(
                    f"noise_floor is a fraction of the peak NPS and must be in (0, 1), got "
                    f"{noise_floor!r}"
                )
            nps_grid = np.maximum(nps_grid, floor * nps_max)
            floor_applied = floor
        elif float(nps_grid.min()) < _MIN_NPS_FRACTION * nps_max:
            ratio = _dynamic_range(nps_grid)
            raise ValueError(
                f"the NPS spans a dynamic range of {ratio:.3g} (min = "
                f"{float(nps_grid.min()):.3g}, max = {nps_max:.3g}), which a prewhitening "
                "observer cannot use: it weights by "
                "1/NPS, so d' would be dominated by high frequencies where the noise power "
                "has decayed to nothing and the signal power is numerical rounding — giving "
                "an enormous and meaningless d'. Real noise has a floor (electronic noise, "
                "quantisation). Model it: add a white component to the NPS, or pass "
                "noise_floor=<fraction of peak NPS> to clamp the spectrum from below."
            )

        # W = S / NPS, so the numerator and the denominator coincide.
        transfer = 1.0 / nps_grid
        signal_power = float(np.sum(power * transfer) * du_dv)
        noise_power = signal_power
    else:
        floor_applied = None
        # W = S E^2.
        transfer = eye**2
        weight = power * eye**4  # how the observer weights the NPS when forming its variance

        # Guard: a *measured* NPS has a zeroed DC bin (nps_2d detrends), and possibly other
        # zeroed bins. Those contribute nothing to the observer's noise variance, so d' comes
        # out too high — silently. For a disk signal with no eye filter, DC alone carries ~6 %
        # of the noise weight, which inflates d' by ~3 %. An eye filter has E(0) = 0 and so is
        # immune; that is why NPWE proper can use a measured NPS and plain NPW cannot.
        zero_bins = nps_grid <= 0.0
        if np.any(zero_bins):
            total = float(weight.sum())
            lost = float(weight[zero_bins].sum()) / total if total > 0.0 else 0.0
            if lost > zero_nps_tolerance:
                dc_note = " (the DC bin is among them)" if zero_bins[0, 0] else ""
                raise ValueError(
                    f"the NPS is zero at frequency bins carrying {lost:.1%} of this observer's "
                    f"noise weight{dc_note}. Those bins would contribute no noise variance, so "
                    f"d' would be biased high by about {1 / np.sqrt(1 - lost) - 1:.1%}. This is "
                    "what a measured NPS looks like: nps_2d detrends, which zeroes DC. Fix it "
                    "by using an eye filter (E(0) = 0, so DC carries no weight), by passing an "
                    "analytic NPS model, or by filling the zeroed bins. Raise "
                    "zero_nps_tolerance only if the images you will score are detrended the "
                    "same way the NPS was, in which case they really do have no noise power "
                    "there."
                )

        signal_power = float(np.sum(power * eye**2) * du_dv)
        noise_power = float(np.sum(weight * nps_grid) * du_dv)

    if signal_power <= 0.0:
        raise ValueError(
            "the observer sees no signal power: the eye filter suppresses every frequency at "
            "which the signal has content"
        )
    if noise_power <= 0.0:
        raise ValueError(
            "the observer's noise variance is zero, so d' is undefined: the NPS vanishes at "
            "every frequency where the observer's template has weight"
        )

    d_prime = float(signal_power / np.sqrt(noise_power))
    template = np.real(np.fft.ifft2(np.fft.fft2(sig) * transfer))

    return ObserverResult(
        name=name,
        d_prime=d_prime,
        auc=_gaussian_auc(d_prime),
        template=template,
        signal_power=signal_power,
        noise_power=noise_power,
        spacing=spacing,
        meta={
            "eye_filter": eye_filter is not None,
            "prewhiten": prewhiten,
            "shape": (ny, nx),
            "noise_floor": floor_applied,
            "nps_dynamic_range": _dynamic_range(nps_grid),
        },
    )


def _dynamic_range(nps_grid: np.ndarray) -> float:
    """``max/min`` of the NPS, reported as ``inf`` when a bin is zero rather than overflowing."""
    lo = float(nps_grid.min())
    hi = float(nps_grid.max())
    if lo <= 0.0:
        return float("inf")
    return hi / lo


def npwe(
    signal: np.ndarray,
    nps: NPSResult | np.ndarray | Callable[[np.ndarray], np.ndarray] | float,
    spacing: float,
    *,
    eye_filter: Callable[[np.ndarray], np.ndarray] | None = None,
    nps_layout: str = "centered",
    zero_nps_tolerance: float = 1e-3,
) -> ObserverResult:
    r"""Non-prewhitening observer with an eye filter (NPWE).

    Template :math:`W = S E^2`. It does **not** invert the noise covariance, and that is the
    point: it models an observer who cannot prewhiten correlated noise, which is why it
    tracks human performance where the ideal observer does not.

    .. math::  d'^2 = \frac{\left[\iint |S|^2 E^2\, df\right]^2}
                           {\iint |S|^2 E^4\, \mathrm{NPS}\, df}

    With ``eye_filter=None`` (:math:`E \equiv 1`) this is the plain non-prewhitening matched
    filter (NPW), which in white noise of standard deviation :math:`\sigma` reduces exactly
    to :math:`d' = \|s\|_2/\sigma`.

    Feeding it a measured NPS
    -------------------------
    A measured NPS from :func:`~taskiq_core.physical.nps_2d` has a **zeroed DC bin** — that
    is what detrending does — and possibly other zeroed bins. Those bins then contribute no
    noise variance to the denominator, so ``d'`` comes out too high, silently. It is not a
    small effect: a disk signal scored with no eye filter carries about 6 % of its noise
    weight at DC, which inflates ``d'`` by about 3 %.

    An eye filter is immune, because :math:`E(0) = 0` puts no weight at DC. So NPWE proper
    can take a measured NPS directly, while plain NPW cannot — and rather than let that
    difference pass unnoticed, this raises when more than ``zero_nps_tolerance`` of the
    observer's noise weight sits on zeroed bins.

    Parameters
    ----------
    signal:
        The signal to be detected — the signal-present minus signal-absent difference image,
        e.g. ``make_disk_signal(...).image``.
    nps:
        Noise power spectrum: an :class:`~taskiq_core.physical.NPSResult`, a scalar (white
        noise, ``sigma^2 * dx * dy``), a callable of radial frequency, or a 2-D array.
    spacing:
        Pixel pitch in mm.
    eye_filter:
        Callable of radial frequency, e.g. from :func:`burgess_eye_filter`. ``None`` gives
        the plain NPW observer.
    nps_layout:
        ``"centered"`` (default: DC in the middle, the layout of ``NPSResult.nps``) or
        ``"fft"`` if you are passing a raw array straight from ``np.fft.fft2``.
    zero_nps_tolerance:
        Largest fraction of the observer's noise weight allowed to fall on zero-NPS bins
        before this raises. Set it to 1.0 only if the images you will score are detrended the
        same way the NPS was — in which case they genuinely have no noise power there and the
        zeroed bins are correct.
    """
    name = "npwe" if eye_filter is not None else "npw"
    return _linear_observer(
        name, signal, nps, spacing,
        eye_filter=eye_filter, prewhiten=False, nps_layout=nps_layout,
        zero_nps_tolerance=zero_nps_tolerance,
    )


def ideal_linear(
    signal: np.ndarray,
    nps: NPSResult | np.ndarray | Callable[[np.ndarray], np.ndarray] | float,
    spacing: float,
    *,
    nps_layout: str = "centered",
    noise_floor: float | None = None,
) -> ObserverResult:
    r"""Prewhitening matched filter — the ideal linear (Hotelling) observer.

    For stationary Gaussian noise the Hotelling observer *is* the prewhitening matched filter
    :math:`W = S/\mathrm{NPS}`, and

    .. math::  d'^2_{\mathrm{ideal}} = \iint \frac{|S(f)|^2}{\mathrm{NPS}(f)}\, df

    This is the upper bound on every other observer here, which makes it the natural
    reference: the efficiency of NPWE or CHO is ``(d' / d'_ideal)**2``. It is also the
    quantity that connects straight to NEQ, and it will be reused when ``atlas.py`` computes
    the physical→task transfer.

    Why this is the fragile one
    ---------------------------
    Weighting by :math:`1/\mathrm{NPS}` means the answer is dominated by whatever frequencies
    have the *least* noise — so a noise model whose power decays to nothing is catastrophic.
    A Gaussian-correlated NPS, :math:`\sigma^2\Delta x\Delta y\, e^{-4\pi^2\sigma_c^2 f^2}`,
    falls by 70-odd orders of magnitude across the frequency plane, and the resulting ``d'``
    is built entirely from bins where the noise power has underflowed and the "signal power"
    is floating-point rounding. It comes out around ``1e29``, and nothing about it looks
    wrong until you compare it with a simulation.

    Real noise has a floor — electronic noise, quantisation — and an NPS model without one
    cannot be prewhitened. So this **raises** when the NPS dynamic range exceeds ``1e8``,
    unless you say what the floor is:

    * add a white component to the NPS model (the physical fix: detector noise really is
      correlated structure *plus* a white floor), or
    * pass ``noise_floor`` to clamp the spectrum from below.

    It likewise raises on a zero NPS bin, which is what a measured (detrended) NPS has at DC.

    Parameters
    ----------
    noise_floor:
        If given, the NPS is clamped from below at ``noise_floor * max(NPS)``. A fraction in
        ``(0, 1)``. Recorded in ``meta`` so the assumption travels with the result.
    """
    return _linear_observer(
        "ideal_linear", signal, nps, spacing,
        eye_filter=None, prewhiten=True, nps_layout=nps_layout,
        noise_floor=noise_floor,
    )


# --------------------------------------------------------------------------------------
# scoring and figures of merit
# --------------------------------------------------------------------------------------


def score_images(images: np.ndarray, template: np.ndarray) -> np.ndarray:
    """Apply a spatial template to images: ``lambda_n = sum_i w_i g_{n,i}``.

    Parameters
    ----------
    images:
        One image ``(ny, nx)`` or a stack ``(n, ny, nx)``.
    template:
        Observer template, shape ``(ny, nx)``.

    Returns
    -------
    np.ndarray
        Scores, shape ``(n,)`` — a stack of one for a single image.
    """
    imgs = np.asarray(images, dtype=np.float64)
    tmpl = np.asarray(template, dtype=np.float64)
    if imgs.ndim == 2:
        imgs = imgs[None, ...]
    if imgs.ndim != 3:
        raise ValueError(f"images must have shape (ny, nx) or (n, ny, nx), got {imgs.shape}")
    if tmpl.shape != imgs.shape[1:]:
        raise ValueError(
            f"template shape {tmpl.shape} does not match the image shape {imgs.shape[1:]}"
        )
    if not np.all(np.isfinite(imgs)) or not np.all(np.isfinite(tmpl)):
        raise ValueError("images and template must be finite")
    return imgs.reshape(imgs.shape[0], -1) @ tmpl.reshape(-1)


# `d_prime_from_scores` and `auc_from_scores` live in taskiq_core.tasks — they are figures of
# merit of the *task*, not of any particular observer — and are re-exported here because this
# is where the scores they consume are produced.


# --------------------------------------------------------------------------------------
# channels
# --------------------------------------------------------------------------------------


def _channel_grid(shape: tuple[int, int], spacing: float) -> tuple[np.ndarray, np.ndarray]:
    """Pixel-centre coordinates ``(yy, xx)`` in mm, relative to the image centre."""
    ny, nx = shape
    y = (np.arange(ny, dtype=np.float64) - (ny - 1) / 2.0) * spacing
    x = (np.arange(nx, dtype=np.float64) - (nx - 1) / 2.0) * spacing
    return np.meshgrid(y, x, indexing="ij")


def _validate_channel_args(shape: tuple[int, int], spacing: float, n_channels: int) -> None:
    ny, nx = shape
    if ny < 4 or nx < 4:
        raise ValueError(f"channels need an image of at least 4x4 pixels, got {shape}")
    if n_channels < 1:
        raise ValueError(f"n_channels must be >= 1, got {n_channels}")
    _check_spacing(spacing)


def laguerre_gauss_channels(
    shape: tuple[int, int],
    spacing: float,
    n_channels: int = 6,
    width_mm: float = 1.0,
    *,
    containment_tol: float = 0.01,
) -> np.ndarray:
    r"""Laguerre-Gauss channels — rotationally symmetric, and orthonormal.

    .. math::  u_j(r) = \frac{\sqrt2}{a}\, e^{-\pi r^2/a^2}\,
               L_j\!\left(\frac{2\pi r^2}{a^2}\right)

    with :math:`L_j` the Laguerre polynomial. They are orthonormal under
    :math:`\iint u_i u_j\, dA = \delta_{ij}`, and being rotationally symmetric they are the
    efficient choice for a rotationally symmetric signal such as
    :func:`taskiq_core.phantoms.make_disk_signal`: a handful of them span the signal, where a
    Gabor set would need dozens — and every extra channel costs sample size in the covariance
    estimate.

    Orthonormality holds **on the infinite plane**. On a finite image it holds only while the
    channels fit inside the field of view, and higher-order channels are wider: at ``a = 2 mm``
    on a 6.4 mm image, channel 5 retains only 81 % of its norm and the Gram matrix is off the
    identity by 0.25. Since silently non-orthonormal "orthonormal channels" is precisely the
    kind of thing that produces a believable but wrong ``d'``, the discrete Gram matrix is
    checked here and a truncated set raises. (Non-orthonormal channels are not *invalid* for
    a CHO — the covariance absorbs them — so ``containment_tol`` can be relaxed deliberately.)

    Parameters
    ----------
    shape:
        ``(ny, nx)`` of the images to be scored.
    spacing:
        Pixel pitch in mm.
    n_channels:
        How many channels, ``j = 0 .. n_channels-1``.
    width_mm:
        The scale ``a``. It should be comparable to the signal size: too small and the
        channels cannot represent the signal; too large and they both spend degrees of freedom
        on noise and run off the edge of the image. Something near the signal radius is a
        reasonable starting point.
    containment_tol:
        Largest deviation of the discrete Gram matrix from the identity before this raises.
        Set to a large value to accept a truncated (non-orthonormal) set on purpose.

    Returns
    -------
    np.ndarray
        ``(n_channels, ny, nx)``.
    """
    _validate_channel_args(shape, spacing, n_channels)
    a = float(width_mm)
    if not np.isfinite(a) or a <= 0.0:
        raise ValueError(f"width_mm must be finite and > 0, got {width_mm!r}")
    if not np.isfinite(containment_tol) or containment_tol <= 0.0:
        raise ValueError(f"containment_tol must be finite and > 0, got {containment_tol!r}")

    yy, xx = _channel_grid(shape, spacing)
    r2 = xx**2 + yy**2
    arg = 2.0 * np.pi * r2 / a**2
    envelope = (np.sqrt(2.0) / a) * np.exp(-np.pi * r2 / a**2)

    channels = np.empty((n_channels, *shape), dtype=np.float64)
    for j in range(n_channels):
        channels[j] = envelope * eval_laguerre(j, arg)

    flat = channels.reshape(n_channels, -1)
    gram = (flat @ flat.T) * spacing * spacing
    deviation = float(np.abs(gram - np.eye(n_channels)).max())
    if deviation > containment_tol:
        worst = int(np.argmin(np.diag(gram)))
        raise ValueError(
            f"the Laguerre-Gauss channels do not fit inside a {shape[0]}x{shape[1]} image at "
            f"{spacing} mm ({shape[1] * spacing:.3g} mm across) with width_mm={a}: the discrete "
            f"Gram matrix is off the identity by {deviation:.3g} (channel {worst} retains only "
            f"{gram[worst, worst]:.1%} of its norm), so the set is not orthonormal and the "
            "higher channels are clipped. Use a smaller width_mm, fewer channels, or a larger "
            "image — or raise containment_tol if a truncated set is what you want."
        )
    return channels


def dense_dog_channels(
    shape: tuple[int, int],
    spacing: float,
    n_channels: int = 8,
    f0_cycles_per_mm: float = 0.15,
    alpha: float = 1.4,
    q: float = 1.67,
) -> np.ndarray:
    r"""Dense difference-of-Gaussian channels — band-pass, rotationally symmetric.

    Built in the frequency domain,

    .. math::  C_j(f) = e^{-f^2/(2 (Q\sigma_j)^2)} - e^{-f^2/(2\sigma_j^2)},
               \qquad \sigma_j = f_0\,\alpha^j

    then transformed to the spatial domain and normalised to unit L2 norm. Every channel is
    zero at DC, so the set is blind to a uniform background — worth having when the
    background level is a nuisance parameter rather than the signal.

    Parameters
    ----------
    n_channels, f0_cycles_per_mm, alpha, q:
        The number of bands, the lowest band's width in cycles/mm, the geometric spacing
        between bands, and the width ratio of the two Gaussians (``q > 1``).
    """
    _validate_channel_args(shape, spacing, n_channels)
    f0, alpha, q = float(f0_cycles_per_mm), float(alpha), float(q)
    if not np.isfinite(f0) or f0 <= 0.0:
        raise ValueError(f"f0_cycles_per_mm must be finite and > 0, got {f0_cycles_per_mm!r}")
    if not np.isfinite(alpha) or alpha <= 1.0:
        raise ValueError(f"alpha must be > 1 (the bands must widen), got {alpha!r}")
    if not np.isfinite(q) or q <= 1.0:
        raise ValueError(f"q must be > 1 (the outer Gaussian must be the wider), got {q!r}")

    fr = _frequency_grid(shape, spacing)
    channels = np.empty((n_channels, *shape), dtype=np.float64)
    for j in range(n_channels):
        sigma = f0 * alpha**j
        band = np.exp(-(fr**2) / (2.0 * (q * sigma) ** 2)) - np.exp(-(fr**2) / (2.0 * sigma**2))
        spatial = np.fft.fftshift(np.real(np.fft.ifft2(band)))
        norm = float(np.linalg.norm(spatial))
        if norm <= 0.0:
            raise ValueError(
                f"DoG channel {j} (sigma = {sigma:.3g} cycles/mm) is identically zero on this "
                "grid: its band falls outside the sampled frequency range"
            )
        channels[j] = spatial / norm
    return channels


def gabor_channels(
    shape: tuple[int, int],
    spacing: float,
    frequencies_cycles_per_mm: tuple[float, ...] = (0.2, 0.4, 0.8),
    orientations_deg: tuple[float, ...] = (0.0, 45.0, 90.0, 135.0),
    phases_deg: tuple[float, ...] = (0.0, 90.0),
    width_mm: float = 2.0,
) -> np.ndarray:
    r"""Gabor channels — oriented band-pass, the classic human-vision-motivated set.

    One channel per (frequency, orientation, phase) combination: a Gaussian envelope of width
    ``width_mm`` times a sinusoid, mean-removed (so, like the DoG set, blind to a uniform
    background) and normalised to unit L2 norm.

    Orientation selectivity is wasted on a rotationally symmetric signal — prefer
    :func:`laguerre_gauss_channels` there — but it is what you want for an anisotropic signal
    or an anisotropic noise field.
    """
    n_channels = len(frequencies_cycles_per_mm) * len(orientations_deg) * len(phases_deg)
    _validate_channel_args(shape, spacing, n_channels)
    w = float(width_mm)
    if not np.isfinite(w) or w <= 0.0:
        raise ValueError(f"width_mm must be finite and > 0, got {width_mm!r}")

    yy, xx = _channel_grid(shape, spacing)
    envelope = np.exp(-(xx**2 + yy**2) / (2.0 * w**2))

    channels = np.empty((n_channels, *shape), dtype=np.float64)
    k = 0
    for f in frequencies_cycles_per_mm:
        for theta_deg in orientations_deg:
            theta = np.deg2rad(theta_deg)
            proj = xx * np.cos(theta) + yy * np.sin(theta)
            for phase_deg in phases_deg:
                g = envelope * np.cos(2.0 * np.pi * f * proj + np.deg2rad(phase_deg))
                g = g - g.mean()  # blind to a uniform background
                norm = float(np.linalg.norm(g))
                if norm <= 0.0:
                    raise ValueError(
                        f"the Gabor channel (f={f}, orientation={theta_deg} deg, "
                        f"phase={phase_deg} deg) is identically zero on this grid"
                    )
                channels[k] = g / norm
                k += 1
    return channels


# --------------------------------------------------------------------------------------
# channelized Hotelling observer
# --------------------------------------------------------------------------------------


def cho(
    present: np.ndarray,
    absent: np.ndarray,
    channels: np.ndarray,
    *,
    method: str = "split",
    internal_noise: float = 0.0,
    seed: int | None = None,
    max_condition: float = 1e10,
) -> CHOResult:
    r"""Channelized Hotelling observer, estimated from signal-present/absent ensembles.

    Images are projected onto the channels, :math:`v = U g`, and the Hotelling template is
    formed in that low-dimensional space:

    .. math::  w = K^{-1}\,\Delta\bar v, \qquad K = \tfrac12(K_1 + K_0), \qquad
               \Delta\bar v = \bar v_1 - \bar v_0

    The channels are what make this tractable at all: the pixel-space covariance of a 64x64
    image is 4096x4096 and cannot be estimated from any realistic number of trials, whereas a
    6x6 channel covariance can.

    Two things about this estimator are easy to get wrong, so neither is left implicit:

    **The two methods are biased in opposite directions, and neither is "the" answer.**

    * ``method="resubstitution"`` reports ``sqrt(dv^T K^-1 dv)`` evaluated on the very data
      that produced ``K`` and ``dv``. That overfits, so it is biased **high**, and the bias
      grows with the channel count and shrinks with the sample size — it inflates ``d'``
      precisely when you are least equipped to notice. With 8 channels and 40 images per
      class it runs about +6 % above the asymptotic value.
    * ``method="split"`` (the default) trains the template on the first half of the images
      and reports the empirical score separation on the held-out second half. That removes
      the overfitting, but it measures a *different thing*: the performance of a template
      estimated from half the data, which is genuinely worse than the template you would get
      with infinite data. So it is biased **low** — about −11 % in the same 8-channel,
      40-image case.

    Both converge to the asymptotic ``d'`` as the sample size grows, from opposite sides, so
    running both **brackets** it. That is the honest way to report a CHO on limited data, and
    the test suite checks the bracketing rather than pretending either estimate is unbiased.

    **A near-singular channel covariance.** With too few samples for the number of channels,
    ``K`` is ill-conditioned and ``K^-1 dv`` is dominated by estimation noise. Rather than
    return the resulting plausible-looking number, this raises once the condition number
    exceeds ``max_condition``.

    Parameters
    ----------
    present, absent:
        Image stacks ``(n, ny, nx)`` of signal-present and signal-absent trials. They need not
        be the same length.
    channels:
        ``(n_channels, ny, nx)``, e.g. from :func:`laguerre_gauss_channels`.
    method:
        ``"split"`` (default; biased low) or ``"resubstitution"`` (biased high). See above —
        run both to bracket the asymptotic value.
    internal_noise:
        Observer internal noise, as a fraction of each channel's response standard deviation:
        noise of SD ``internal_noise * std(v_c)`` is added to channel ``c``. ``0`` (default)
        is a noiseless observer. Requires ``seed`` when non-zero.
    seed:
        Seed for the internal-noise realisation, so the estimate stays reproducible.
    max_condition:
        Raise if the channel covariance's condition number exceeds this.

    Returns
    -------
    CHOResult
    """
    p = np.asarray(present, dtype=np.float64)
    a = np.asarray(absent, dtype=np.float64)
    u = np.asarray(channels, dtype=np.float64)

    if p.ndim != 3 or a.ndim != 3:
        raise ValueError(
            f"present and absent must be image stacks (n, ny, nx), got {p.shape} and {a.shape}"
        )
    if u.ndim != 3:
        raise ValueError(f"channels must have shape (n_channels, ny, nx), got {u.shape}")
    if p.shape[1:] != u.shape[1:] or a.shape[1:] != u.shape[1:]:
        raise ValueError(
            f"the image shapes {p.shape[1:]} / {a.shape[1:]} do not match the channel shape "
            f"{u.shape[1:]}"
        )
    if not (np.all(np.isfinite(p)) and np.all(np.isfinite(a)) and np.all(np.isfinite(u))):
        raise ValueError("images and channels must be finite")
    if method not in ("split", "resubstitution"):
        raise ValueError(f"method must be 'split' or 'resubstitution', got {method!r}")

    internal_noise = float(internal_noise)
    if not np.isfinite(internal_noise) or internal_noise < 0.0:
        raise ValueError(f"internal_noise must be finite and >= 0, got {internal_noise!r}")
    if internal_noise > 0.0 and seed is None:
        raise ValueError(
            "internal_noise > 0 requires an explicit seed so the result stays reproducible"
        )

    n_channels = u.shape[0]
    n_p, n_a = p.shape[0], a.shape[0]

    u_flat = u.reshape(n_channels, -1)
    v_p = p.reshape(n_p, -1) @ u_flat.T  # (n_present, n_channels)
    v_a = a.reshape(n_a, -1) @ u_flat.T

    if internal_noise > 0.0:
        rng = np.random.default_rng(seed)
        sd = 0.5 * (v_p.std(axis=0, ddof=1) + v_a.std(axis=0, ddof=1))
        v_p = v_p + rng.normal(0.0, 1.0, size=v_p.shape) * (internal_noise * sd)
        v_a = v_a + rng.normal(0.0, 1.0, size=v_a.shape) * (internal_noise * sd)

    need = n_channels + 2
    if method == "split":
        n_p_train, n_a_train = n_p // 2, n_a // 2
        if n_p_train < need or n_a_train < need:
            raise ValueError(
                f"method='split' halves the data, leaving {n_p_train} present and {n_a_train} "
                f"absent images to estimate a {n_channels}x{n_channels} channel covariance. "
                f"That needs at least {need} per class per half, i.e. {2 * need} images per "
                "class in total. Use more trials, fewer channels, or method='resubstitution' "
                "if you accept its upward bias."
            )
        v_p_train, v_a_train = v_p[:n_p_train], v_a[:n_a_train]
        v_p_test, v_a_test = v_p[n_p_train:], v_a[n_a_train:]
    else:
        if n_p < need or n_a < need:
            raise ValueError(
                f"estimating a {n_channels}x{n_channels} channel covariance needs at least "
                f"{need} images per class, got {n_p} present and {n_a} absent"
            )
        v_p_train, v_a_train = v_p, v_a
        v_p_test, v_a_test = v_p, v_a

    delta_v = v_p_train.mean(axis=0) - v_a_train.mean(axis=0)
    k_matrix = np.atleast_2d(
        0.5
        * (
            np.cov(v_p_train, rowvar=False, ddof=1)
            + np.cov(v_a_train, rowvar=False, ddof=1)
        )
    )

    condition = float(np.linalg.cond(k_matrix))
    if not np.isfinite(condition) or condition > max_condition:
        raise ValueError(
            f"the channel covariance is ill-conditioned (condition number {condition:.3g} > "
            f"{max_condition:.3g}): with {n_channels} channels and {n_p}/{n_a} images the "
            "Hotelling template would be dominated by estimation noise. Use more trials, "
            "fewer channels, or a channel set that is less degenerate on this grid."
        )

    w = np.linalg.solve(k_matrix, delta_v)
    scores_present = v_p_test @ w
    scores_absent = v_a_test @ w

    if method == "split":
        d_prime = d_prime_from_scores(scores_present, scores_absent)
    else:
        quad = float(delta_v @ w)
        if quad <= 0.0:
            raise ValueError(
                "the estimated Hotelling d'^2 came out non-positive, which means the channel "
                "covariance estimate is degenerate; use more trials or fewer channels"
            )
        d_prime = float(np.sqrt(quad))

    return CHOResult(
        d_prime=d_prime,
        auc=auc_from_scores(scores_present, scores_absent),
        scores_present=scores_present,
        scores_absent=scores_absent,
        channel_template=w,
        spatial_template=(w @ u_flat).reshape(u.shape[1:]),
        channel_covariance=k_matrix,
        delta_v=delta_v,
        condition_number=condition,
        method=method,
        n_channels=n_channels,
        n_present=n_p,
        n_absent=n_a,
        internal_noise=internal_noise,
        meta={
            "n_train_present": int(v_p_train.shape[0]),
            "n_test_present": int(v_p_test.shape[0]),
            "seed": seed,
        },
    )
