"""Synthetic phantoms for task-based image quality.

All phantoms are generated analytically on a regular grid. Nothing here reads a
file, and nothing here is patient data: every image in ``taskiq_core`` is synthetic by
construction.

Three phantoms are provided, one per measurement in the pipeline:

``make_edge_phantom``
    Slanted edge, for presampled MTF estimation (:func:`taskiq_core.physical.mtf_from_edge`).
    The edge can be blurred *analytically* (exact ``erf`` profile of a Gaussian-blurred
    step), which makes the true MTF known in closed form and gives the estimator an
    analytic ground truth to be validated against.

``make_uniform_phantom``
    Uniform background plus noise, for NPS estimation (:func:`taskiq_core.physical.nps_2d`).
    Noise is either white or Gaussian-correlated; in both cases the true NPS is known
    in closed form.

``make_disk_signal``
    Low-contrast disk, used as the signal ``s`` of the SKE/BKE detection task that the
    model observers (``taskiq_core.observers``) will operate on.

Conventions
-----------
* Images are ``numpy.float32``, indexed ``image[row, col]`` == ``image[y, x]``.
* ``spacing`` is the pixel pitch in **mm** (isotropic). Frequencies are cycles/mm.
* Randomness always flows through ``numpy.random.default_rng(seed)``: the same ``seed``
  reproduces bit-identical images.
* Invalid arguments raise ``ValueError`` immediately. Nothing is silently clipped,
  and no NaN is ever produced or swallowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.special import erf
from scipy.stats import ncx2

__all__ = [
    "Phantom",
    "make_edge_phantom",
    "make_uniform_phantom",
    "make_disk_signal",
]


@dataclass(frozen=True, eq=False)
class Phantom:
    """A synthetic image together with everything needed to score an estimate of it.

    Attributes
    ----------
    image:
        ``float32`` array of shape ``(ny, nx)``, indexed ``[row, col]``.
    spacing:
        Isotropic pixel pitch in mm.
    ground_truth:
        Closed-form description of what was drawn (geometry, contrast, and — where it
        exists — the analytic MTF/NPS the estimator is supposed to recover). Keys are
        documented by the factory function that produced the phantom.
    seed:
        Seed passed to ``numpy.random.default_rng``. ``None`` when the phantom is
        deterministic (no noise realisation).
    kind:
        Which factory produced this phantom: ``"edge"``, ``"uniform"`` or ``"disk"``.
    """

    image: np.ndarray
    spacing: float
    ground_truth: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    kind: str = ""

    @property
    def shape(self) -> tuple[int, int]:
        """``(ny, nx)`` of :attr:`image`."""
        return self.image.shape  # type: ignore[return-value]

    @property
    def extent_mm(self) -> tuple[float, float]:
        """Physical size ``(height, width)`` of the image in mm."""
        ny, nx = self.image.shape
        return (ny * self.spacing, nx * self.spacing)


# --------------------------------------------------------------------------------------
# validation helpers
# --------------------------------------------------------------------------------------


def _as_shape(size: int | tuple[int, int]) -> tuple[int, int]:
    """Normalise ``size`` to ``(ny, nx)`` and reject anything degenerate."""
    if isinstance(size, (int, np.integer)):
        ny = nx = int(size)
    else:
        try:
            ny, nx = (int(v) for v in size)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"size must be an int or a (ny, nx) pair of ints, got {size!r}"
            ) from exc
    if ny < 4 or nx < 4:
        raise ValueError(f"size must be at least 4x4 pixels, got (ny={ny}, nx={nx})")
    return ny, nx


def _check_spacing(spacing: float) -> float:
    spacing = float(spacing)
    if not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError(f"spacing must be a finite positive number of mm, got {spacing!r}")
    return spacing


def _check_finite(name: str, value: float) -> float:
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return value


def _check_nonneg(name: str, value: float) -> float:
    value = _check_finite(name, value)
    if value < 0.0:
        raise ValueError(f"{name} must be >= 0, got {value!r}")
    return value


def _pixel_grid(ny: int, nx: int) -> tuple[np.ndarray, np.ndarray]:
    """Pixel-centre coordinates ``(yy, xx)`` in pixel units, shape ``(ny, nx)``."""
    yy, xx = np.meshgrid(
        np.arange(ny, dtype=np.float64),
        np.arange(nx, dtype=np.float64),
        indexing="ij",
    )
    return yy, xx


def _finalize(image: np.ndarray, what: str) -> np.ndarray:
    """Cast to float32 and refuse to hand back a non-finite image (no silent NaN)."""
    if not np.all(np.isfinite(image)):
        n_bad = int(np.count_nonzero(~np.isfinite(image)))
        raise ValueError(
            f"{what} produced {n_bad} non-finite pixel(s); this is a bug in taskiq_core, "
            "please report the arguments that triggered it"
        )
    return np.ascontiguousarray(image, dtype=np.float32)


# --------------------------------------------------------------------------------------
# edge phantom (MTF)
# --------------------------------------------------------------------------------------


def make_edge_phantom(
    size: int | tuple[int, int] = 512,
    spacing: float = 0.1,
    contrast: float = 1000.0,
    angle_deg: float = 5.0,
    seed: int | None = None,
    *,
    background: float = 0.0,
    blur_sigma_mm: float = 0.0,
    noise_sd: float = 0.0,
    oversample: int = 1,
) -> Phantom:
    r"""Slanted step edge for presampled MTF estimation.

    The image is a step of height ``contrast`` whose edge line passes through the image
    centre, with the edge **normal** rotated ``angle_deg`` from the +x axis (so
    ``angle_deg=0`` is a vertical edge with intensity increasing to the right). The
    small tilt is what makes the edge useful: each image row samples the edge profile at
    a different sub-pixel phase, so the rows collectively oversample the edge spread
    function far beyond the pixel Nyquist frequency.

    Blur is applied **analytically**, not by convolving the sampled image. For an ideal
    step convolved with an isotropic Gaussian of width :math:`\sigma`, the exact
    continuous image is

    .. math::  I(u) = b + \frac{c}{2}\left[1 + \operatorname{erf}\!\left(\frac{u}{\sigma\sqrt 2}\right)\right]

    where :math:`u` is the signed distance from the edge line in mm. Sampling *that*
    function at the pixel centres avoids every discretisation and boundary artefact a
    numerical convolution would introduce, so the true presampled MTF of the resulting
    image is exactly

    .. math::  \mathrm{MTF}(f) = \exp(-2\pi^2\sigma^2 f^2)

    with no pixel-aperture term (see ``oversample`` below). This closed form is what
    ``tests/test_physical.py::test_mtf_analytic_gaussian`` holds the estimator to.

    Parameters
    ----------
    size:
        ``n`` for an ``n x n`` image, or ``(ny, nx)``.
    spacing:
        Pixel pitch in mm.
    contrast:
        Step height (value on the bright side minus the dark side). May be negative.
    angle_deg:
        Rotation of the edge normal from the +x axis, in degrees. Must not be an exact
        multiple of 90 deg: a perfectly axis-aligned edge gives every row the same
        sub-pixel phase and the ESF cannot be oversampled. Typical values are 2-10 deg.
    seed:
        Seed for the noise realisation. Required (i.e. must not be ``None``) when
        ``noise_sd > 0``, so that a noisy phantom is always reproducible.
    background:
        Value on the dark side of the edge.
    blur_sigma_mm:
        Standard deviation in mm of the Gaussian blur applied analytically. ``0.0``
        gives an ideal (unblurred) step, whose MTF is flat at 1.
    noise_sd:
        Standard deviation of additive white Gaussian noise, applied after blurring
        (i.e. the noise is *not* blurred, as befits a detector-noise model).
    oversample:
        ``1`` (default) point-samples the continuous image at the pixel centres, which
        is what the analytic MTF above describes. ``k > 1`` instead averages ``k x k``
        sub-samples per pixel, emulating a square pixel aperture; that multiplies the
        MTF by an extra ``sinc(f * spacing)`` aperture term, so do **not** use it when
        comparing against the Gaussian-only analytic MTF.

    Returns
    -------
    Phantom
        ``ground_truth`` contains ``angle_deg``, ``normal`` (unit vector ``(nx, ny)``),
        ``edge_point_px`` (a point on the edge line, ``(x, y)``), ``contrast``,
        ``background``, ``blur_sigma_mm``, ``noise_sd``, ``oversample``, and
        ``mtf_kind`` (``"gaussian"`` or ``"ideal"``; ``"gaussian*aperture"`` if
        ``oversample > 1``).

    Raises
    ------
    ValueError
        On a degenerate size, non-positive spacing, axis-aligned edge, negative blur or
        noise, ``oversample < 1``, or noise requested without a seed.
    """
    ny, nx = _as_shape(size)
    spacing = _check_spacing(spacing)
    contrast = _check_finite("contrast", contrast)
    background = _check_finite("background", background)
    angle_deg = _check_finite("angle_deg", angle_deg)
    blur_sigma_mm = _check_nonneg("blur_sigma_mm", blur_sigma_mm)
    noise_sd = _check_nonneg("noise_sd", noise_sd)

    oversample = int(oversample)
    if oversample < 1:
        raise ValueError(f"oversample must be >= 1, got {oversample}")
    if abs(angle_deg % 90.0) < 1e-9 or abs(angle_deg % 90.0 - 90.0) < 1e-9:
        raise ValueError(
            f"angle_deg={angle_deg} is axis-aligned; the slanted-edge method needs a "
            "tilted edge (typically 2-10 deg) so that image rows sample the edge at "
            "different sub-pixel phases"
        )
    if noise_sd > 0.0 and seed is None:
        raise ValueError("noise_sd > 0 requires an explicit seed so the image is reproducible")

    theta = np.deg2rad(angle_deg)
    normal = (float(np.cos(theta)), float(np.sin(theta)))  # (x, y) components
    x0, y0 = (nx - 1) / 2.0, (ny - 1) / 2.0

    yy, xx = _pixel_grid(ny, nx)
    if oversample == 1:
        u = ((xx - x0) * normal[0] + (yy - y0) * normal[1]) * spacing
        image = _step(u, background, contrast, blur_sigma_mm)
    else:
        # Sub-sample offsets at the centres of a k x k grid inside each pixel.
        offs = (np.arange(oversample) + 0.5) / oversample - 0.5
        acc = np.zeros((ny, nx), dtype=np.float64)
        for dy in offs:
            for dx in offs:
                u = ((xx + dx - x0) * normal[0] + (yy + dy - y0) * normal[1]) * spacing
                acc += _step(u, background, contrast, blur_sigma_mm)
        image = acc / (oversample * oversample)

    if noise_sd > 0.0:
        rng = np.random.default_rng(seed)
        image = image + rng.normal(0.0, noise_sd, size=image.shape)

    if blur_sigma_mm > 0.0:
        mtf_kind = "gaussian"
    else:
        mtf_kind = "ideal"
    if oversample > 1:
        mtf_kind = f"{mtf_kind}*aperture"

    ground_truth: dict[str, Any] = {
        "angle_deg": float(angle_deg),
        "normal": normal,
        "edge_point_px": (x0, y0),
        "contrast": contrast,
        "background": background,
        "blur_sigma_mm": blur_sigma_mm,
        "noise_sd": noise_sd,
        "oversample": oversample,
        "mtf_kind": mtf_kind,
    }
    return Phantom(
        image=_finalize(image, "make_edge_phantom"),
        spacing=spacing,
        ground_truth=ground_truth,
        seed=seed,
        kind="edge",
    )


def _step(u: np.ndarray, background: float, contrast: float, sigma_mm: float) -> np.ndarray:
    """Ideal step (``sigma_mm == 0``) or its exact Gaussian-blurred ``erf`` profile."""
    if sigma_mm == 0.0:
        return background + contrast * (u > 0.0).astype(np.float64)
    return background + contrast * 0.5 * (1.0 + erf(u / (sigma_mm * np.sqrt(2.0))))


# --------------------------------------------------------------------------------------
# uniform phantom (NPS)
# --------------------------------------------------------------------------------------


def make_uniform_phantom(
    size: int | tuple[int, int] = 256,
    spacing: float = 0.1,
    mean: float = 0.0,
    noise_sd: float = 10.0,
    seed: int | None = 0,
    *,
    correlation_sigma_mm: float = 0.0,
    n_realizations: int = 1,
) -> Phantom:
    r"""Uniform background plus noise, for NPS estimation.

    With ``correlation_sigma_mm == 0`` the noise is white Gaussian with standard
    deviation ``noise_sd``, whose noise power spectrum is flat at

    .. math::  \mathrm{NPS}(f) = \sigma^2\,\Delta x\,\Delta y \quad[\text{value}^2\,\mathrm{mm}^2]

    which integrates over the full frequency plane back to :math:`\sigma^2` — the
    normalisation :func:`taskiq_core.physical.nps_2d` is built to satisfy.

    With ``correlation_sigma_mm > 0`` the white field is filtered **in the Fourier
    domain** by the exact continuous Gaussian transfer function
    :math:`H(f) = \exp(-2\pi^2\sigma_c^2 f^2)` evaluated on the DFT grid. That makes the
    filtering an exact circular convolution, so the resulting noise has, again in closed
    form,

    .. math::  \mathrm{NPS}(f) = \sigma^2\,\Delta x\,\Delta y\,\exp(-4\pi^2\sigma_c^2 f^2)

    and pixel variance :math:`\sigma^2 \langle |H|^2 \rangle` (reported as
    ``pixel_sd_expected``). Note ``noise_sd`` is the SD of the *pre-filter* white field;
    the filtered image is smoother and therefore has a smaller pixel SD. Both facts are
    recorded in ``ground_truth`` rather than being papered over by a rescaling.

    Parameters
    ----------
    size, spacing:
        As in :func:`make_edge_phantom`.
    mean:
        Constant background level.
    noise_sd:
        Standard deviation of the white Gaussian field (before any correlation filter).
    seed:
        Seed for the noise realisation. Must not be ``None`` when ``noise_sd > 0``.
    correlation_sigma_mm:
        Gaussian correlation length in mm. ``0.0`` gives white noise.
    n_realizations:
        If ``> 1``, :attr:`Phantom.image` is a stack of shape ``(n, ny, nx)`` of
        independent realisations drawn from the same ``rng`` — exactly the ROI stack
        :func:`taskiq_core.physical.nps_2d` wants for an ensemble-averaged NPS.

    Returns
    -------
    Phantom
        ``ground_truth`` contains ``mean``, ``noise_sd`` (white-field SD),
        ``correlation_sigma_mm``, ``nps_white_level`` (:math:`\sigma^2\Delta x\Delta y`),
        ``nps_kind`` (``"white"`` or ``"gaussian_correlated"``), ``pixel_sd_expected``,
        and ``n_realizations``.

    Raises
    ------
    ValueError
        On a degenerate size/spacing, negative ``noise_sd`` or ``correlation_sigma_mm``,
        ``n_realizations < 1``, or noise requested without a seed.
    """
    ny, nx = _as_shape(size)
    spacing = _check_spacing(spacing)
    mean = _check_finite("mean", mean)
    noise_sd = _check_nonneg("noise_sd", noise_sd)
    correlation_sigma_mm = _check_nonneg("correlation_sigma_mm", correlation_sigma_mm)

    n_realizations = int(n_realizations)
    if n_realizations < 1:
        raise ValueError(f"n_realizations must be >= 1, got {n_realizations}")
    if noise_sd > 0.0 and seed is None:
        raise ValueError("noise_sd > 0 requires an explicit seed so the image is reproducible")

    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, noise_sd, size=(n_realizations, ny, nx))

    if correlation_sigma_mm > 0.0 and noise_sd > 0.0:
        h = _gaussian_transfer(ny, nx, spacing, correlation_sigma_mm)
        noise = np.fft.ifft2(np.fft.fft2(noise, axes=(-2, -1)) * h, axes=(-2, -1)).real
        pixel_sd_expected = float(noise_sd * np.sqrt(np.mean(h**2)))
        nps_kind = "gaussian_correlated"
    else:
        pixel_sd_expected = float(noise_sd)
        nps_kind = "white"

    image = mean + noise
    if n_realizations == 1:
        image = image[0]

    ground_truth: dict[str, Any] = {
        "mean": mean,
        "noise_sd": noise_sd,
        "correlation_sigma_mm": correlation_sigma_mm,
        "nps_white_level": float(noise_sd**2 * spacing * spacing),
        "nps_kind": nps_kind,
        "pixel_sd_expected": pixel_sd_expected,
        "n_realizations": n_realizations,
    }
    return Phantom(
        image=_finalize(image, "make_uniform_phantom"),
        spacing=spacing,
        ground_truth=ground_truth,
        seed=seed,
        kind="uniform",
    )


def _gaussian_transfer(ny: int, nx: int, spacing: float, sigma_mm: float) -> np.ndarray:
    """Continuous Gaussian transfer function ``exp(-2 pi^2 sigma^2 f^2)`` on the DFT grid."""
    fy = np.fft.fftfreq(ny, d=spacing)[:, None]
    fx = np.fft.fftfreq(nx, d=spacing)[None, :]
    f2 = fy**2 + fx**2
    return np.exp(-2.0 * np.pi**2 * sigma_mm**2 * f2)


# --------------------------------------------------------------------------------------
# disk signal (detection task)
# --------------------------------------------------------------------------------------


def make_disk_signal(
    size: int | tuple[int, int] = 64,
    radius_mm: float = 1.0,
    contrast: float = 10.0,
    spacing: float = 0.1,
    *,
    center_px: tuple[float, float] | None = None,
    edge_sigma_mm: float = 0.0,
    oversample: int = 4,
) -> Phantom:
    r"""Low-contrast disk: the signal ``s`` of the SKE/BKE detection task.

    The returned image is the signal **alone** on a zero background, i.e. the
    signal-present minus signal-absent difference image. Model observers
    (``taskiq_core.observers``) take exactly this as their template, and detection
    experiments (``taskiq_core.tasks``) add it to a noisy background.

    A hard disk edge aliases badly on a pixel grid, so by default each pixel is
    area-averaged over an ``oversample x oversample`` sub-grid; a pixel straddling the
    boundary therefore carries ``contrast x (covered fraction)``. Set
    ``edge_sigma_mm > 0`` instead for a Gaussian-blurred (soft) disk. This function is
    deterministic — it draws no random numbers and takes no seed.

    Parameters
    ----------
    size, spacing:
        As in :func:`make_edge_phantom`.
    radius_mm:
        Disk radius in mm. Must be positive and must fit inside the image.
    contrast:
        Peak signal amplitude (disk interior value). May be negative for a cold lesion.
    center_px:
        ``(x, y)`` disk centre in pixel coordinates. Defaults to the image centre.
    edge_sigma_mm:
        If ``> 0``, the disk is convolved with an isotropic 2-D Gaussian of this width
        (exactly, in closed form), giving a soft-edged lesion whose integral is unchanged
        — so ``signal_sum`` stays ``contrast * area / spacing^2`` no matter how much the
        edge is blurred.
    oversample:
        Sub-pixel sampling factor for area coverage. ``1`` point-samples (aliased).

    Returns
    -------
    Phantom
        ``ground_truth`` contains ``radius_mm``, ``contrast``, ``center_px``,
        ``edge_sigma_mm``, ``area_mm2`` (:math:`\pi r^2`), ``signal_sum``
        (:math:`\sum_i s_i`, which for a well-resolved disk approaches
        ``contrast * area_mm2 / spacing^2``), and ``signal_energy``
        (:math:`\sum_i s_i^2`).

    Raises
    ------
    ValueError
        On a degenerate size/spacing, non-positive radius, negative ``edge_sigma_mm``,
        ``oversample < 1``, or a disk that does not fit inside the image.
    """
    ny, nx = _as_shape(size)
    spacing = _check_spacing(spacing)
    contrast = _check_finite("contrast", contrast)
    edge_sigma_mm = _check_nonneg("edge_sigma_mm", edge_sigma_mm)

    radius_mm = _check_finite("radius_mm", radius_mm)
    if radius_mm <= 0.0:
        raise ValueError(f"radius_mm must be > 0, got {radius_mm}")

    oversample = int(oversample)
    if oversample < 1:
        raise ValueError(f"oversample must be >= 1, got {oversample}")

    if center_px is None:
        cx, cy = (nx - 1) / 2.0, (ny - 1) / 2.0
    else:
        try:
            cx, cy = (float(v) for v in center_px)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"center_px must be an (x, y) pair, got {center_px!r}") from exc

    radius_px = radius_mm / spacing
    margin_px = radius_px + 3.0 * edge_sigma_mm / spacing
    if (
        cx - margin_px < -0.5
        or cx + margin_px > nx - 0.5
        or cy - margin_px < -0.5
        or cy + margin_px > ny - 0.5
    ):
        raise ValueError(
            f"disk (radius {radius_mm} mm = {radius_px:.1f} px, centre {(cx, cy)}) does not "
            f"fit inside a {ny}x{nx} image at spacing {spacing} mm; enlarge size, shrink "
            "radius_mm, or move center_px"
        )

    yy, xx = _pixel_grid(ny, nx)
    offs = (np.arange(oversample) + 0.5) / oversample - 0.5
    acc = np.zeros((ny, nx), dtype=np.float64)
    for dy in offs:
        for dx in offs:
            r = np.hypot((xx + dx - cx) * spacing, (yy + dy - cy) * spacing)
            acc += _disk_profile(r, radius_mm, edge_sigma_mm)
    image = contrast * acc / (oversample * oversample)

    image32 = _finalize(image, "make_disk_signal")
    ground_truth: dict[str, Any] = {
        "radius_mm": radius_mm,
        "contrast": contrast,
        "center_px": (cx, cy),
        "edge_sigma_mm": edge_sigma_mm,
        "area_mm2": float(np.pi * radius_mm**2),
        "signal_sum": float(image32.sum()),
        "signal_energy": float(np.sum(image32.astype(np.float64) ** 2)),
    }
    return Phantom(
        image=image32,
        spacing=spacing,
        ground_truth=ground_truth,
        seed=None,
        kind="disk",
    )


def _disk_profile(r: np.ndarray, radius_mm: float, edge_sigma_mm: float) -> np.ndarray:
    r"""Unit-amplitude disk of radius ``radius_mm``, optionally with a soft edge.

    The soft edge is the **exact 2-D convolution** of the disk with an isotropic Gaussian,
    not the 1-D ``erf`` profile of a blurred straight edge applied radially. The two are
    not the same and the difference is not subtle: the annulus just outside the boundary
    has more area than the one just inside, so the radial-``erf`` version *adds*
    :math:`\pi\sigma^2` of area (2.3 % for a 1 mm disk blurred by 0.15 mm) — a signal
    whose integral silently depends on its blur, which would then propagate straight into
    ``d'``.

    The exact profile has a closed form. The blurred disk evaluated at distance
    :math:`r` from the centre is the probability that a 2-D Gaussian centred at that point
    lands inside the disk, i.e. that a non-central chi-square with 2 degrees of freedom and
    non-centrality :math:`(r/\sigma)^2` falls below :math:`(R/\sigma)^2`. That is a proper
    convolution, so it conserves the integral exactly.
    """
    if edge_sigma_mm == 0.0:
        return (r <= radius_mm).astype(np.float64)
    scale = edge_sigma_mm**2
    return ncx2.cdf(radius_mm**2 / scale, df=2, nc=r**2 / scale)
