r"""Physical image quality: presampled MTF and noise power spectrum (NPS).

These are the two "physical" legs of the task-based pipeline. Together with the signal
they feed NEQ and, through the model observers, detectability ``d'``.

Estimators
----------
:func:`mtf_from_edge`
    Slanted-edge MTF (the ISO 12233 / IEC 62220-1 construction): project every pixel
    onto the edge normal, bin the projections far below the pixel pitch to build an
    oversampled edge spread function (ESF), differentiate to the line spread function
    (LSF), and Fourier transform. Two exactly-known biases of that construction — the
    finite-difference derivative and the boxcar bin average — are divided out
    analytically, which is what lets the estimate match the closed-form MTF of a
    Gaussian-blurred edge to well under 1 %.

:func:`nps_2d`
    Ensemble 2-D noise power spectrum and its radial average, normalised so that

    .. math::  \iint \mathrm{NPS}(u, v)\, du\, dv = \sigma^2

    i.e. the integral of the NPS over the frequency plane is the pixel variance. This is
    the normalisation that makes NPS comparable across pixel pitches, and it is checked
    to machine precision in the test suite (``test_nps_integral_equals_variance``).

Everything here is a pure function of its arguments. Degenerate inputs raise
``ValueError`` with an actionable message; nothing returns a silent NaN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

__all__ = [
    "MTFResult",
    "NPSResult",
    "gaussian_mtf",
    "estimate_edge_angle",
    "mtf_from_edge",
    "nps_2d",
]


# --------------------------------------------------------------------------------------
# analytic reference
# --------------------------------------------------------------------------------------


def gaussian_mtf(frequency: np.ndarray | float, sigma_mm: float) -> np.ndarray:
    r"""Closed-form MTF of an isotropic Gaussian blur, :math:`\exp(-2\pi^2\sigma^2 f^2)`.

    This is the analytic ground truth that :func:`mtf_from_edge` is validated against
    when applied to a phantom from
    ``make_edge_phantom(..., blur_sigma_mm=sigma_mm, oversample=1)``. It is exported
    because the same reference is useful in examples and in downstream NEQ checks — not
    because the estimator uses it internally (it does not).

    Parameters
    ----------
    frequency:
        Spatial frequency in cycles/mm.
    sigma_mm:
        Gaussian standard deviation in mm. ``0`` gives an all-pass MTF of 1.

    """
    sigma_mm = float(sigma_mm)
    if not np.isfinite(sigma_mm) or sigma_mm < 0.0:
        raise ValueError(f"sigma_mm must be finite and >= 0, got {sigma_mm!r}")
    f = np.asarray(frequency, dtype=np.float64)
    return np.exp(-2.0 * np.pi**2 * sigma_mm**2 * f**2)


# --------------------------------------------------------------------------------------
# MTF
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class MTFResult:
    """Result of a slanted-edge MTF measurement.

    Attributes
    ----------
    frequency:
        Spatial frequency axis in cycles/mm, starting at 0 (DC).
    mtf:
        Presampled MTF, normalised to 1 at DC, on :attr:`frequency`.
    esf_position:
        Bin-centre positions of the oversampled ESF, in mm, signed along the edge normal.
    esf:
        Oversampled edge spread function on :attr:`esf_position`.
    lsf:
        Line spread function (derivative of :attr:`esf`), on the same positions.
    angle_deg:
        Edge-normal angle actually used, in degrees — either the value passed in or the
        one estimated from the image.
    angle_estimated:
        ``True`` if :attr:`angle_deg` came from :func:`estimate_edge_angle`.
    spacing:
        Pixel pitch in mm, echoed from the input.
    bin_width_mm:
        ESF bin width in mm (``spacing / bin_subsample``).
    bin_counts:
        Number of pixels contributing to each ESF bin. Useful for spotting a phantom too
        small or an angle too shallow to fill the bins.
    nyquist:
        Pixel Nyquist frequency ``1 / (2 * spacing)`` in cycles/mm, for reference; the
        slanted-edge method resolves the presampled MTF beyond it.
    meta:
        Free-form record of the estimator settings.

    """

    frequency: np.ndarray
    mtf: np.ndarray
    esf_position: np.ndarray
    esf: np.ndarray
    lsf: np.ndarray
    angle_deg: float
    angle_estimated: bool
    spacing: float
    bin_width_mm: float
    bin_counts: np.ndarray
    nyquist: float
    meta: dict[str, Any] = field(default_factory=dict)

    def at(self, frequency: np.ndarray | float) -> np.ndarray:
        """Linearly interpolate the MTF at arbitrary frequencies (cycles/mm)."""
        return np.interp(
            np.asarray(frequency, dtype=np.float64),
            self.frequency,
            self.mtf,
            left=np.nan,
            right=np.nan,
        )


def estimate_edge_angle(image: np.ndarray, *, level_fraction: float = 0.1) -> float:
    r"""Estimate the edge-normal angle of a slanted-edge image, in degrees.

    Locates the edge in every row by the **area (first-moment) method** and least-squares
    fits a line through those positions. For a row that runs from a dark level ``lo`` to
    a bright level ``hi`` across an edge at column :math:`x_e`,

    .. math::

        \sum_x \left[\,\mathrm{hi} - I(x)\,\right] = (\mathrm{hi}-\mathrm{lo})\,(x_e + \tfrac12)

    for *any* symmetric blur, so :math:`x_e` follows from a plain sum over the row. Two
    properties matter here:

    * It is **linear in the pixel values**, so zero-mean image noise does not bias it —
      it only adds variance, which the fit over many rows averages down. A centroid of
      the *rectified* gradient :math:`|\nabla I|`, the more obvious construction, does
      not have this property: noise rectifies to a positive pedestal spread across the
      whole row and drags the estimate toward the row centre. At 2 % noise that error is
      large enough to report a 5 deg edge as 0.6 deg, which would then wreck the MTF.
    * The blur cancels, so no assumption about the LSF width is needed.

    ``lo`` and ``hi`` are read from vertical strips at the left and right of the image
    (``level_fraction`` of the width each), pooled over all rows: a common error in them
    shifts every row's :math:`x_e` equally and therefore cannot tilt the fitted line.

    The convention matches :func:`taskiq_core.phantoms.make_edge_phantom`: the angle is that of
    the edge *normal* from the +x axis, so 0 deg is a vertical edge. Assumes a
    near-vertical edge (|angle| well under 45 deg) that crosses every row while leaving
    the two level strips clear of it — all of which is checked.

    Raises
    ------
    ValueError
        Non-2-D image, no net contrast across the image in x, or an edge that strays into
        (or past) the level strips, in which case ``lo``/``hi`` are not edge-free and the
        estimate would be silently wrong.

    """
    img = np.asarray(image, dtype=np.float64)
    if img.ndim != 2:
        raise ValueError(f"image must be 2-D, got shape {img.shape}")
    if not (0.0 < level_fraction < 0.5):
        raise ValueError(f"level_fraction must be in (0, 0.5), got {level_fraction}")

    ny, nx = img.shape
    n_strip = max(1, int(round(level_fraction * nx)))
    lo = float(img[:, :n_strip].mean())
    hi = float(img[:, -n_strip:].mean())
    step = hi - lo

    scale = float(np.abs(img).max())
    if abs(step) <= 1e-9 * max(scale, 1.0):
        raise ValueError(
            "no net contrast between the left and right edges of the image, so there is "
            "no vertical-ish edge to locate; is this a slanted-edge image?"
        )

    x_edge = (nx * hi - img.sum(axis=1)) / step - 0.5
    if np.any(x_edge < n_strip) or np.any(x_edge > nx - 1 - n_strip):
        raise ValueError(
            f"the edge reaches column {x_edge.min():.1f}..{x_edge.max():.1f} of {nx}, which "
            f"runs into the {n_strip}-pixel level strips used to read the dark and bright "
            "levels. The edge angle is too large (or the image too narrow) for this "
            "estimator; pass a known angle_deg instead."
        )

    rows = np.arange(ny, dtype=np.float64)
    # Edge line is  x = x0 - (y - y0) tan(theta), so slope dx/dy = -tan(theta).
    slope = np.polyfit(rows, x_edge, 1)[0]
    return float(np.rad2deg(np.arctan(-slope)))


def mtf_from_edge(
    image: np.ndarray,
    spacing: float,
    angle_deg: float | None = None,
    *,
    bin_subsample: int = 10,
    esf_halfwidth_mm: float | None = None,
    f_max: float | None = None,
    min_bin_count: int = 1,
    jitter_correction: bool = True,
    tail_tolerance: float = 0.002,
) -> MTFResult:
    r"""Presampled MTF of a slanted edge (ESF -> LSF -> MTF).

    Construction, and the three biases it has to undo
    ------------------------------------------------
    1. Every pixel centre is projected onto the edge normal, giving a signed distance
       ``u`` in mm. Because the edge is tilted, those projections land on a grid far
       finer than the pixel pitch.
    2. The ``(u, value)`` samples are averaged into bins of width ``h = spacing /
       bin_subsample`` to form the oversampled ESF.

       *Bias A — bin-position jitter.* The mean sample position inside a bin is not the
       bin centre: the projected positions are set by the edge angle, so they pile up
       off-centre by an angle-dependent amount (up to ~0.04 h at 5 deg). Treating the
       bin average as a sample *at the bin centre* therefore evaluates the ESF at the
       wrong place, and the resulting position jitter shows up as an MTF error that
       grows with frequency — 1.4 % at MTF = 0.1 for a sharp edge, which is exactly the
       regime the estimator is supposed to be trusted in. The fix is a first-order shift
       back to the bin centre, ``ESF(c) ~= ESF(u_bar) + (c - u_bar) * dESF/du``, using
       the mean position ``u_bar`` actually measured in each bin. This drops the error
       by two to three orders of magnitude (to <0.01 %) and is what ``jitter_correction``
       controls.

       *Bias B — the bin average itself.* Averaging over a bin is a boxcar of width
       ``h``, which multiplies the measured MTF by ``sinc(f h)``.
    3. The LSF is the central difference of the ESF. A central difference over ``2h``
       has transfer ``sin(2 pi f h) / (2 pi f h) = sinc(2 f h)`` relative to a true
       derivative (*bias C*), so it multiplies the measured MTF by a second ``sinc(2 f h)``.
    4. ``MTF = |FFT(LSF)|``, normalised to 1 at DC, then **divided by
       ``sinc(f h) * sinc(2 f h)``** to undo B and C.

    All three corrections are exact consequences of the estimator, not fudge factors.
    Without them the estimate is biased by ~2 % at the pixel Nyquist frequency (B and C)
    and by ~1 % at some edge angles (A) — the difference between passing and failing a
    1 % agreement test against the analytic MTF.

    Note that no pixel-aperture term is divided out. For a real detector the aperture is
    part of the presampled MTF and belongs in the answer; for a point-sampled phantom
    (``make_edge_phantom(..., oversample=1)``) there is no aperture to remove.

    Parameters
    ----------
    image:
        2-D slanted-edge image.
    spacing:
        Pixel pitch in mm.
    angle_deg:
        Edge-normal angle in degrees (see :func:`taskiq_core.phantoms.make_edge_phantom`).
        ``None`` estimates it with :func:`estimate_edge_angle`.
    bin_subsample:
        ESF bins per pixel. 10 (bins of ``spacing / 10``) is a good default: fine enough
        that the two sinc corrections stay near 1, coarse enough that every bin is
        populated.
    esf_halfwidth_mm:
        Half-width of the analysis window around the edge, in mm. Defaults to
        ``min(ny, nx) * spacing / 5``, which for a square phantom keeps every bin well
        populated. Must be wide enough for the LSF to have decayed to zero at the window
        edges (this is checked; see ``tail_tolerance``).
    f_max:
        Highest frequency to report, in cycles/mm. Defaults to the pixel Nyquist
        ``1 / (2 * spacing)``. The oversampled ESF supports frequencies up to
        ``1 / (2 h)``, so a larger value is legitimate if you want the supra-Nyquist part
        of the presampled MTF.
    min_bin_count:
        Minimum number of pixels an ESF bin must contain. Bins below this raise, rather
        than quietly producing a NaN in the ESF.
    jitter_correction:
        Correct each ESF bin from its measured mean sample position to the bin centre
        (bias A above). On by default; exposed so the correction's effect can be
        measured rather than taken on faith (see ``tests/test_physical.py``).
    tail_tolerance:
        The ESF must have flattened at both ends of the window: the residual step across
        the outermost 5 % of the window, as a fraction of the full edge contrast, must be
        below this. Otherwise the window is too narrow for the blur and truncation would
        bias the MTF, so this raises. The check is made on block means of the ESF (not on
        the peak of the LSF) precisely so that it responds to truncation and not to noise.

    Returns
    -------
    MTFResult

    Raises
    ------
    ValueError
        Non-2-D image, non-positive spacing, ``bin_subsample < 2``, an underpopulated
        ESF bin, a zero-contrast edge, or an ESF window too narrow for the blur.

    """
    img = np.asarray(image, dtype=np.float64)
    if img.ndim != 2:
        raise ValueError(f"image must be 2-D, got shape {img.shape}")
    if not np.all(np.isfinite(img)):
        raise ValueError("image contains non-finite values; refusing to estimate an MTF from it")

    spacing = float(spacing)
    if not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError(f"spacing must be a finite positive number of mm, got {spacing!r}")

    bin_subsample = int(bin_subsample)
    if bin_subsample < 2:
        raise ValueError(
            f"bin_subsample must be >= 2 (the point of the slanted edge is to sample the "
            f"ESF below the pixel pitch), got {bin_subsample}"
        )
    if not (0.0 < tail_tolerance < 1.0):
        raise ValueError(f"tail_tolerance must be in (0, 1), got {tail_tolerance}")

    ny, nx = img.shape
    angle_estimated = angle_deg is None
    if angle_deg is None:
        angle_deg = estimate_edge_angle(img)
    angle_deg = float(angle_deg)
    if not np.isfinite(angle_deg):
        raise ValueError(f"angle_deg must be finite, got {angle_deg!r}")

    theta = np.deg2rad(angle_deg)
    n_x, n_y = float(np.cos(theta)), float(np.sin(theta))

    # A point on the edge line: the centroid of the derivative taken *along the edge
    # normal*. That derivative is the LSF, so for a straight edge with a symmetric LSF
    # its centroid lies on the edge, whatever the blur. It is signed, which is the whole
    # point: image noise is zero-mean in it and averages out, whereas the centroid of the
    # rectified |grad I| would be dragged toward the image centre by the noise pedestal.
    gy, gx = np.gradient(img)
    w = gx * n_x + gy * n_y
    w_sum = w.sum()
    if abs(w_sum) <= 1e-12 * float(np.abs(w).sum() + 1.0):
        raise ValueError(
            "the derivative along the edge normal sums to zero: there is no net step "
            "across the edge (zero contrast, or a badly wrong angle_deg)"
        )
    yy, xx = np.meshgrid(
        np.arange(ny, dtype=np.float64), np.arange(nx, dtype=np.float64), indexing="ij"
    )
    x0 = float((w * xx).sum() / w_sum)
    y0 = float((w * yy).sum() / w_sum)

    # Signed distance of each pixel from the edge line, in mm.
    u = ((xx - x0) * n_x + (yy - y0) * n_y) * spacing

    h = spacing / bin_subsample
    if esf_halfwidth_mm is None:
        esf_halfwidth_mm = min(ny, nx) * spacing / 5.0
    esf_halfwidth_mm = float(esf_halfwidth_mm)
    if not np.isfinite(esf_halfwidth_mm) or esf_halfwidth_mm <= 2.0 * h:
        raise ValueError(
            f"esf_halfwidth_mm must be finite and larger than a couple of bins "
            f"({2 * h:.4g} mm), got {esf_halfwidth_mm!r}"
        )
    u_span = float(np.abs(u).max())
    if esf_halfwidth_mm > u_span:
        raise ValueError(
            f"esf_halfwidth_mm={esf_halfwidth_mm:.4g} mm exceeds the largest distance from "
            f"the edge present in the image ({u_span:.4g} mm); use a smaller window"
        )

    n_half = int(round(esf_halfwidth_mm / h))
    edges = (np.arange(-n_half, n_half + 1) * h).astype(np.float64)
    centers = 0.5 * (edges[:-1] + edges[1:])

    inside = (u >= edges[0]) & (u < edges[-1])
    u_in = u[inside]
    v_in = img[inside]

    counts, _ = np.histogram(u_in, bins=edges)
    sums, _ = np.histogram(u_in, bins=edges, weights=v_in)
    pos_sums, _ = np.histogram(u_in, bins=edges, weights=u_in)
    if np.any(counts < min_bin_count):
        n_short = int(np.count_nonzero(counts < min_bin_count))
        raise ValueError(
            f"{n_short} of {counts.size} ESF bins hold fewer than {min_bin_count} pixel(s). "
            "The edge does not oversample the ESF finely enough: use a larger image, a "
            "larger edge angle, or a smaller bin_subsample."
        )
    esf = sums / counts

    # Bias A: each bin's samples sit at mean position u_bar, not at the bin centre.
    # Shift the ESF back to the centre to first order before differentiating.
    u_bar = pos_sums / counts
    jitter = centers - u_bar
    if jitter_correction:
        esf = esf + jitter * np.gradient(esf, h)

    # Check the window actually contains the blur, using block means of the ESF tails:
    # a residual step across the outermost bins means the ESF has not flattened yet.
    # (Block means, not the LSF peak, so that image noise averages down and only genuine
    # truncation trips this.)
    contrast = float(abs(esf[-1] - esf[0]))
    n_blk = max(2, int(round(0.05 * esf.size)))
    if 3 * n_blk >= esf.size:
        raise ValueError(
            f"the ESF has only {esf.size} bins, too few to check for window truncation; "
            "increase esf_halfwidth_mm or bin_subsample"
        )
    d_left = abs(float(esf[n_blk : 2 * n_blk].mean() - esf[:n_blk].mean()))
    d_right = abs(float(esf[-n_blk:].mean() - esf[-2 * n_blk : -n_blk].mean()))
    step = max(contrast, float(np.abs(esf).max()) * 1e-12)
    if step <= 0.0:
        raise ValueError("the ESF is flat (zero-contrast edge); there is no MTF to measure")
    tail = max(d_left, d_right) / step
    if tail > tail_tolerance:
        raise ValueError(
            f"the ESF is still rising by {tail:.2%} of the edge contrast across the outer "
            f"5 % of the {esf_halfwidth_mm:.3g} mm window (tolerance {tail_tolerance:.2%}). "
            "The window is too narrow for this blur; truncation would bias the MTF. "
            "Increase esf_halfwidth_mm (and the phantom, if needed)."
        )

    lsf = np.gradient(esf, h)
    if float(np.abs(lsf).max()) <= 0.0:
        raise ValueError("the ESF is flat (zero-contrast edge); there is no MTF to measure")

    freq = np.fft.rfftfreq(lsf.size, d=h)
    spectrum = np.abs(np.fft.rfft(lsf))
    dc = spectrum[0]
    if dc <= 0.0:
        raise ValueError("the LSF integrates to zero (no net step across the edge)")
    mtf = spectrum / dc

    # Undo the two exactly-known biases of the estimator: the boxcar bin average
    # (sinc(f h)) and the central-difference derivative (sinc(2 f h)).
    correction = np.sinc(freq * h) * np.sinc(2.0 * freq * h)
    nyquist = 1.0 / (2.0 * spacing)
    if f_max is None:
        f_max = nyquist
    f_max = float(f_max)
    f_limit = 1.0 / (2.0 * h)
    if not np.isfinite(f_max) or f_max <= 0.0 or f_max > f_limit:
        raise ValueError(
            f"f_max must be in (0, {f_limit:.4g}] cycles/mm — the Nyquist frequency of the "
            f"oversampled ESF — got {f_max!r}"
        )
    keep = freq <= f_max + 1e-12
    freq = freq[keep]
    mtf = mtf[keep] / correction[keep]

    return MTFResult(
        frequency=freq,
        mtf=mtf,
        esf_position=centers,
        esf=esf,
        lsf=lsf,
        angle_deg=angle_deg,
        angle_estimated=angle_estimated,
        spacing=spacing,
        bin_width_mm=h,
        bin_counts=counts,
        nyquist=nyquist,
        meta={
            "bin_subsample": bin_subsample,
            "esf_halfwidth_mm": esf_halfwidth_mm,
            "edge_point_px": (x0, y0),
            "n_pixels_used": int(u_in.size),
            "jitter_correction": jitter_correction,
            "max_bin_jitter_frac": float(np.abs(jitter).max() / h),
            "esf_tail_residual": tail,
            "corrections": (
                "bin-centre jitter (first order) + "
                "sinc(f*h) [bin boxcar] * sinc(2*f*h) [central difference]"
            ),
        },
    )


# --------------------------------------------------------------------------------------
# NPS
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class NPSResult:
    r"""Result of a noise power spectrum measurement.

    Attributes
    ----------
    nps:
        2-D NPS in ``value^2 mm^2``, ``fftshift``-ed so DC is at the centre. Units are
        such that :math:`\iint \mathrm{NPS}\, du\, dv = \sigma^2`.
    fx, fy:
        Frequency axes in cycles/mm matching the columns and rows of :attr:`nps`.
    frequency:
        Radial frequency bin centres in cycles/mm (DC excluded).
    nps_radial:
        Radially averaged NPS on :attr:`frequency`.
    radial_counts:
        Number of 2-D frequency bins averaged into each radial bin.
    variance:
        Pixel variance of the detrended ROIs, averaged over the stack. Equal to the
        integral of :attr:`nps` over the frequency plane, to machine precision.
    integral:
        :math:`\sum \mathrm{NPS}\, \Delta u\, \Delta v` — the discrete form of that
        integral. Kept alongside :attr:`variance` so the identity can be checked (and
        reported) rather than assumed.
    spacing, n_rois, roi_shape, detrend:
        Echo of the inputs and the detrending actually applied.

    """

    nps: np.ndarray
    fx: np.ndarray
    fy: np.ndarray
    frequency: np.ndarray
    nps_radial: np.ndarray
    radial_counts: np.ndarray
    variance: float
    integral: float
    spacing: float
    n_rois: int
    roi_shape: tuple[int, int]
    detrend: str

    @property
    def nyquist(self) -> float:
        """Pixel Nyquist frequency ``1 / (2 * spacing)`` in cycles/mm."""
        return 1.0 / (2.0 * self.spacing)


def nps_2d(
    images: np.ndarray,
    spacing: float,
    *,
    detrend: str = "mean",
    radial_bin_width: float | None = None,
    f_max: float | None = None,
) -> NPSResult:
    r"""Ensemble 2-D noise power spectrum and its radial average.

    Normalisation
    -------------
    For ROIs of ``ny x nx`` pixels with pitch ``dx = dy = spacing``,

    .. math::  \mathrm{NPS}(u_k, v_l) = \frac{\Delta x\, \Delta y}{n_x n_y}
               \left\langle \left| \mathrm{DFT}\{\Delta I\}_{kl} \right|^2 \right\rangle

    where :math:`\Delta I` is the detrended ROI and the average is over ROIs. With the
    DFT bin spacing :math:`\Delta u = 1/(n_x \Delta x)`, Parseval makes

    .. math::  \sum_{kl} \mathrm{NPS}(u_k, v_l)\, \Delta u\, \Delta v = \sigma^2

    an **exact identity**, not an approximation — which is why the test suite can check
    it at ``rtol=1e-10``. For white noise of SD :math:`\sigma` this gives a flat NPS at
    :math:`\sigma^2 \Delta x \Delta y`.

    Parameters
    ----------
    images:
        One ROI ``(ny, nx)`` or a stack ``(n, ny, nx)``. More ROIs means a less noisy
        NPS estimate: a single periodogram bin has 100 % relative standard deviation, so
        an ensemble (and the radial average) is what makes the estimate usable.
    spacing:
        Pixel pitch in mm.
    detrend:
        ``"mean"`` (default) subtracts each ROI's own mean — right for a genuinely
        uniform background. ``"poly2"`` fits and removes a 2-D second-order polynomial
        per ROI, for a background with a low-order shading trend. ``"none"`` leaves the
        ROI alone, which puts all the background power in the DC bin; use it only if you
        have already detrended.
    radial_bin_width:
        Width of the radial frequency bins in cycles/mm. Defaults to the coarser of the
        two DFT bin spacings, ``max(1/(nx*dx), 1/(ny*dy))``.
    f_max:
        Highest radial frequency to report. Defaults to the pixel Nyquist.

    Returns
    -------
    NPSResult

    Raises
    ------
    ValueError
        Wrong dimensionality, non-finite pixels, non-positive spacing, an unknown
        ``detrend`` mode, ROIs too small for ``poly2``, or a radial binning that would
        leave a bin empty.

    """
    arr = np.asarray(images, dtype=np.float64)
    if arr.ndim == 2:
        arr = arr[None, ...]
    if arr.ndim != 3:
        raise ValueError(f"images must have shape (ny, nx) or (n, ny, nx), got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("images contain non-finite values; refusing to estimate an NPS from them")

    n_rois, ny, nx = arr.shape
    if ny < 4 or nx < 4:
        raise ValueError(f"ROIs must be at least 4x4 pixels, got ({ny}, {nx})")

    spacing = float(spacing)
    if not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError(f"spacing must be a finite positive number of mm, got {spacing!r}")

    if detrend == "mean":
        resid = arr - arr.mean(axis=(-2, -1), keepdims=True)
    elif detrend == "poly2":
        resid = _detrend_poly2(arr)
    elif detrend == "none":
        resid = arr
    else:
        raise ValueError(f"detrend must be one of 'mean', 'poly2', 'none'; got {detrend!r}")

    # NPS with the normalisation that integrates to the variance.
    power = np.abs(np.fft.fft2(resid, axes=(-2, -1))) ** 2
    nps = (spacing * spacing / (ny * nx)) * power.mean(axis=0)

    du = 1.0 / (nx * spacing)
    dv = 1.0 / (ny * spacing)
    integral = float(nps.sum() * du * dv)
    variance = float(np.mean(resid**2))  # population variance of the detrended ROIs

    nps_shift = np.fft.fftshift(nps)
    fx = np.fft.fftshift(np.fft.fftfreq(nx, d=spacing))
    fy = np.fft.fftshift(np.fft.fftfreq(ny, d=spacing))

    freq, nps_radial, counts = _radial_average(
        nps_shift, fx, fy, radial_bin_width=radial_bin_width, f_max=f_max, spacing=spacing
    )

    return NPSResult(
        nps=nps_shift,
        fx=fx,
        fy=fy,
        frequency=freq,
        nps_radial=nps_radial,
        radial_counts=counts,
        variance=variance,
        integral=integral,
        spacing=spacing,
        n_rois=n_rois,
        roi_shape=(ny, nx),
        detrend=detrend,
    )


def _detrend_poly2(arr: np.ndarray) -> np.ndarray:
    """Remove a per-ROI 2-D second-order polynomial (6 terms) by least squares."""
    _, ny, nx = arr.shape
    if ny < 3 or nx < 3:
        raise ValueError(f"detrend='poly2' needs ROIs of at least 3x3 pixels, got ({ny}, {nx})")
    y, x = np.meshgrid(np.linspace(-1.0, 1.0, ny), np.linspace(-1.0, 1.0, nx), indexing="ij")
    basis = np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=-1).reshape(ny * nx, 6)
    flat = arr.reshape(arr.shape[0], ny * nx).T  # (npix, n_rois)
    coeffs, *_ = np.linalg.lstsq(basis, flat, rcond=None)
    fit = (basis @ coeffs).T.reshape(arr.shape)
    return arr - fit


def _radial_average(
    nps_shift: np.ndarray,
    fx: np.ndarray,
    fy: np.ndarray,
    *,
    radial_bin_width: float | None,
    f_max: float | None,
    spacing: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Radially average a centred 2-D NPS, excluding the DC bin.

    DC is excluded because detrending forces it to zero: including it would drag the
    lowest radial bin toward zero for no physical reason.
    """
    ny, nx = nps_shift.shape
    fxx, fyy = np.meshgrid(fx, fy, indexing="xy")
    fr = np.hypot(fxx, fyy)

    if radial_bin_width is None:
        radial_bin_width = max(1.0 / (nx * spacing), 1.0 / (ny * spacing))
    radial_bin_width = float(radial_bin_width)
    if not np.isfinite(radial_bin_width) or radial_bin_width <= 0.0:
        raise ValueError(f"radial_bin_width must be finite and > 0, got {radial_bin_width!r}")

    if f_max is None:
        f_max = 1.0 / (2.0 * spacing)  # pixel Nyquist
    f_max = float(f_max)
    if not np.isfinite(f_max) or f_max <= radial_bin_width:
        raise ValueError(
            f"f_max must be finite and larger than radial_bin_width "
            f"({radial_bin_width:.4g}), got {f_max!r}"
        )

    # Bins are *centred* on multiples of the bin width, so bin k covers
    # [(k - 1/2) w, (k + 1/2) w) for k = 1, 2, ... A bin starting at zero instead would
    # always come out empty: the lowest non-DC frequency in the DFT is exactly w.
    n_bins = int(np.floor(f_max / radial_bin_width))
    if n_bins < 1:
        raise ValueError(
            f"f_max={f_max:.4g} leaves no radial bins at radial_bin_width="
            f"{radial_bin_width:.4g} cycles/mm"
        )
    edges = (np.arange(n_bins + 1, dtype=np.float64) + 0.5) * radial_bin_width

    valid = (fr >= edges[0]) & (fr < edges[-1])  # DC excluded by construction
    idx = np.digitize(fr[valid], edges) - 1
    counts = np.bincount(idx, minlength=n_bins)
    if np.any(counts == 0):
        n_empty = int(np.count_nonzero(counts == 0))
        raise ValueError(
            f"{n_empty} of {n_bins} radial NPS bins are empty (radial_bin_width="
            f"{radial_bin_width:.4g} cycles/mm is too fine for a {ny}x{nx} ROI). Widen "
            "radial_bin_width or use larger ROIs."
        )
    sums = np.bincount(idx, weights=nps_shift[valid], minlength=n_bins)

    centers = (np.arange(n_bins, dtype=np.float64) + 1.0) * radial_bin_width
    return centers, sums / counts, counts
