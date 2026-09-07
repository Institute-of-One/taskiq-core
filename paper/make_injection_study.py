"""Inject known defects at controlled severity and ask which checks notice.

The defects are not hypothetical. Three were found in this pipeline during
development; the rest are the standard ways the same chain is got wrong elsewhere.
Each is applied to a correct pipeline through one dial, so severity zero recovers
the correct case exactly and nothing is rewritten to break it.

Against them stand three kinds of check:

* a **self-consistency regression test**, which compares the pipeline to a stored
  snapshot of its own earlier output -- the check most projects actually have;
* **internal identities**, which must hold for algebraic reasons and need no ground
  truth, so they survive the move to measured data; and
* **closed-form references**, which compare an estimate to the analytic answer for a
  phantom whose truth is known, and therefore need a phantom.

The question is not whether a bug can be found but which check finds it, and whether
it is found before the reported detectability is materially wrong -- a guard that
fires only after the answer is already wrong is not a guard.

Run::

    python paper/make_injection_study.py

Writes ``paper/figures/injection.json`` and ``paper/figures/fig4_injection.png``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.special import erfc  # noqa: E402

from taskiq_core import (  # noqa: E402
    gaussian_mtf,
    ideal_linear,
    make_disk_signal,
    make_edge_phantom,
    make_uniform_phantom,
    mtf_from_edge,
    nps_2d,
)

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 13, "axes.titlesize": 13, "figure.dpi": 600})

SPACING = 0.1  # mm
SIZE = 64  # signal / noise ROI, pixels
EDGE_SIZE = 256  # edge phantom, pixels
NOISE_SD = 20.0
RADIUS_MM = 0.8
CONTRAST = 6.0
BLUR_MM = 0.15
N_REALISATIONS = 64

MATERIAL = 0.05  # a 5 % error in a reported d' is "materially wrong"
SINC_BIN_SUBSAMPLE = 4  # ESF bin of spacing/4 = 0.025 mm; the deficit is then 4.3 %
SEVERITIES = np.linspace(0.0, 1.0, 11)
JITTER_ANGLES = [5.0, 4.5, 4.0, 3.0, 2.0, 6.0, 7.0, 9.0, 11.0, 15.0, 20.0]


# ==========================================================================
# One run of the chain, and everything a check is allowed to look at
# ==========================================================================
@dataclass
class Bundle:
    """One run of the chain, and every quantity a check is allowed to look at."""

    frequency: np.ndarray  # radial frequency axis of the measured MTF
    mtf: np.ndarray  # the measured MTF on that axis
    mtf_closed_form: np.ndarray  # exp(-2 pi^2 sigma^2 f^2) on the same axis
    nps_radial: np.ndarray  # radially averaged measured NPS
    nps_closed_form: float  # sigma^2 dx dy, the analytic white level
    nps_integral: float  # integral of the 2-D NPS over the frequency plane
    nps_variance: float  # pixel variance the NPS was estimated from
    nps_dynamic_range: float  # max/min over the plane, DC excluded
    signal_integral: float  # integral of the object signal
    signal_area_closed_form: float  # contrast x pi r^2, what it must be
    d_prime_pw: float  # the observer's own number
    d_prime_neq: float  # the physics-predicts-task number
    d_prime_bridge_exact: float  # NEQ route with the *analytic* MTF


def _radial_grid(size: int, spacing: float) -> np.ndarray:
    fy = np.fft.fftfreq(size, d=spacing)[:, None]
    fx = np.fft.fftfreq(size, d=spacing)[None, :]
    return np.sqrt(fy**2 + fx**2)


def _exact_disk(contrast: float, radius_mm: float, edge_sigma_mm: float) -> np.ndarray:
    """The exact 2-D Gaussian-blurred disk, whose area does not depend on the blur."""
    return make_disk_signal(
        SIZE,
        radius_mm=radius_mm,
        contrast=contrast,
        spacing=SPACING,
        edge_sigma_mm=edge_sigma_mm,
    ).image.astype(np.float64)


def _radially_blurred_disk(contrast: float, radius_mm: float, edge_sigma_mm: float) -> np.ndarray:
    """The defect: the 1-D edge profile applied radially, which gains pi sigma^2 of area."""
    centre = (SIZE - 1) / 2.0
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float64)
    r = np.hypot(yy - centre, xx - centre) * SPACING
    if edge_sigma_mm <= 0.0:
        return np.where(r <= radius_mm, contrast, 0.0)
    return contrast * 0.5 * erfc((r - radius_mm) / (edge_sigma_mm * np.sqrt(2.0)))


def run_pipeline(
    *,
    mtf_transform: Callable[[np.ndarray, np.ndarray, float], np.ndarray] | None = None,
    nps_scale: float = 1.0,
    nps_detrend: str = "mean",
    background_ramp: float = 0.0,
    correlation_sigma_mm: float = 0.0,
    observer_nps: str = "analytic",
    noise_floor: float | None = None,
    disk_builder: Callable[[float, float, float], np.ndarray] = _exact_disk,
    edge_angle_deg: float = 5.0,
    jitter_correction: bool = True,
    bin_subsample: int = 10,
) -> Bundle:
    """MTF -> NPS -> NEQ -> d', with at most one defect injected at one stage."""
    # ---- MTF, from a slanted edge whose closed form is known ------------------------
    edge = make_edge_phantom(
        EDGE_SIZE,
        spacing=SPACING,
        angle_deg=edge_angle_deg,
        blur_sigma_mm=BLUR_MM,
        seed=0,
    )
    mtf_res = mtf_from_edge(
        edge.image,
        SPACING,
        jitter_correction=jitter_correction,
        bin_subsample=bin_subsample,
        f_max=4.0,
    )
    freq = np.asarray(mtf_res.frequency, dtype=np.float64)
    mtf = np.asarray(mtf_res.mtf, dtype=np.float64).copy()
    if mtf_transform is not None:
        mtf = mtf_transform(freq, mtf, float(mtf_res.bin_width_mm))
    mtf_cf = np.asarray(gaussian_mtf(freq, BLUR_MM), dtype=np.float64)

    # ---- NPS, from an ensemble of uniform fields ------------------------------------
    field = make_uniform_phantom(
        SIZE,
        spacing=SPACING,
        noise_sd=NOISE_SD,
        seed=1,
        n_realizations=N_REALISATIONS,
        correlation_sigma_mm=correlation_sigma_mm,
    )
    images = np.asarray(field.image, dtype=np.float64)
    if images.ndim == 2:
        images = images[None, ...]
    if background_ramp != 0.0:  # the trend the detrending is supposed to remove
        ramp = np.linspace(-background_ramp / 2.0, background_ramp / 2.0, images.shape[-1])
        images = images + ramp[None, None, :]
    nps_res = nps_2d(images, SPACING, detrend=nps_detrend)

    nps_plane = np.asarray(nps_res.nps, dtype=np.float64) * nps_scale
    nps_radial = np.asarray(nps_res.nps_radial, dtype=np.float64) * nps_scale
    nps_integral = float(nps_res.integral) * nps_scale
    # Exclude DC -- the plane is centred, so DC sits at the middle, and mean-detrending
    # drives it to ~1e-31 by construction. That is bookkeeping, not a decayed spectrum.
    plane_no_dc = nps_plane.copy()
    plane_no_dc[nps_plane.shape[0] // 2, nps_plane.shape[1] // 2] = np.nan
    positive = plane_no_dc[np.isfinite(plane_no_dc) & (plane_no_dc > 0)]
    dyn = float(np.nanmax(plane_no_dc) / positive.min()) if positive.size else np.inf

    # ---- the object signal, and the closed form of its area -------------------------
    s_obj = disk_builder(CONTRAST, RADIUS_MM, BLUR_MM)
    signal_integral = float(s_obj.sum() * SPACING * SPACING)
    area_cf = float(CONTRAST * np.pi * RADIUS_MM**2)

    # ---- the routes to d' -----------------------------------------------------------
    f_radial = _radial_grid(SIZE, SPACING)
    band = np.isfinite(nps_radial) & (nps_radial > 0) & (nps_res.frequency > 0)
    level = float(np.mean(nps_radial[band]))  # measured, not assumed
    mtf2d_true = np.exp(-2.0 * np.pi**2 * BLUR_MM**2 * f_radial**2)
    s_img = np.fft.ifft2(np.fft.fft2(s_obj) * mtf2d_true).real

    area = SPACING * SPACING
    s_spec = area * np.fft.fft2(s_obj)
    du_dv = 1.0 / (SIZE * SIZE * area)

    # Route A -- the observer's own number. Handed either the analytic level or the
    # measured spectrum, depending on what the study is testing.
    if observer_nps == "measured":
        # Repair DC before prewhitening. Mean-detrending sets the DC bin to ~1e-31,
        # which is bookkeeping, not a decayed spectrum; left in place it trips the
        # dynamic-range guard on every field, white noise included. Replacing it with
        # its neighbours' median is the standard repair and is not the defect under test.
        plane = np.asarray(nps_res.nps, dtype=np.float64).copy()
        cy, cx = plane.shape[0] // 2, plane.shape[1] // 2
        ring = np.concatenate(
            [
                plane[cy - 1 : cy + 2, cx - 1],
                plane[cy - 1 : cy + 2, cx + 1],
                plane[cy - 1, cx : cx + 1],
                plane[cy + 1, cx : cx + 1],
            ]
        )
        plane[cy, cx] = float(np.median(ring))
        nps_for_observer: object = plane * nps_scale
    else:
        nps_for_observer = level
    d_pw = float(ideal_linear(s_img, nps_for_observer, SPACING, noise_floor=noise_floor).d_prime)

    # Route B -- physics predicts task, through the *measured* MTF.
    mtf2d_measured = np.interp(f_radial, freq, mtf, left=float(mtf[0]), right=0.0)
    d_neq = float(np.sqrt(np.sum((mtf2d_measured**2 / level) * np.abs(s_spec) ** 2 * du_dv)))

    # The exact identity -- the same route with the analytic MTF, against *the noise
    # model route A actually used*. Comparing the two while they disagree about the
    # noise would test nothing but that disagreement.
    if isinstance(nps_for_observer, np.ndarray):
        denom = np.fft.ifftshift(nps_for_observer)  # centred plane -> fftfreq order
    else:
        denom = np.full_like(f_radial, float(nps_for_observer))
    d_bridge = float(np.sqrt(np.sum((mtf2d_true**2 / denom) * np.abs(s_spec) ** 2 * du_dv)))

    return Bundle(
        frequency=freq,
        mtf=mtf,
        mtf_closed_form=mtf_cf,
        nps_radial=nps_radial,
        nps_closed_form=NOISE_SD**2 * SPACING**2,
        nps_integral=nps_integral,
        nps_variance=float(nps_res.variance),
        nps_dynamic_range=dyn,
        signal_integral=signal_integral,
        signal_area_closed_form=area_cf,
        d_prime_pw=d_pw,
        d_prime_neq=d_neq,
        d_prime_bridge_exact=d_bridge,
    )


# ==========================================================================
# The checks
# ==========================================================================
@dataclass
class Check:
    """One check: what it is, what it costs to run, and what it is entitled to see."""

    key: str
    label: str
    kind: str  # "identity" (no ground truth needed) or "closed form" (needs a phantom)
    tolerance: float
    measure: Callable[[Bundle], float]
    why: str


def _parseval(b: Bundle) -> float:
    return abs(b.nps_integral / b.nps_variance - 1.0)


def _bridge(b: Bundle) -> float:
    return abs(b.d_prime_bridge_exact / b.d_prime_pw - 1.0)


def _signal_area(b: Bundle) -> float:
    return abs(b.signal_integral / b.signal_area_closed_form - 1.0)


def _dynamic_range(b: Bundle) -> float:
    return max(0.0, float(np.log10(max(b.nps_dynamic_range, 1.0))) - 6.0)


def _mtf_vs_closed_form(b: Bundle) -> float:
    band = b.frequency <= 3.0  # where the MTF still carries signal
    return float(np.abs(b.mtf[band] - b.mtf_closed_form[band]).max())


def _nps_vs_closed_form(b: Bundle) -> float:
    band = np.isfinite(b.nps_radial) & (b.nps_radial > 0)
    if not band.any():
        return np.inf
    return float(np.abs(b.nps_radial[band] / b.nps_closed_form - 1.0).max())


CHECKS = [
    Check(
        "parseval",
        "integral of NPS = pixel variance",
        "identity",
        1e-9,
        _parseval,
        "The NPS normalisation is an exact identity, whatever the noise model is.",
    ),
    Check(
        "bridge",
        "NEQ integral = prewhitening d'",
        "identity",
        1e-9,
        _bridge,
        "Two algebraically identical routes to one number, sharing no code path.",
    ),
    Check(
        "signal_area",
        "signal area = contrast x pi r^2",
        "identity",
        1e-6,
        _signal_area,
        "Blurring conserves area; the signal integral cannot depend on the blur.",
    ),
    Check(
        "dynamic_range",
        "NPS dynamic range < 1e6 (DC excluded)",
        "identity",
        0.0,
        _dynamic_range,
        "1/NPS is meaningless where the noise power has decayed into rounding error.",
    ),
    Check(
        "mtf_closed_form",
        "MTF = exp(-2 pi^2 sigma^2 f^2)",
        "closed form",
        5e-5,
        _mtf_vs_closed_form,
        "The edge is an analytically blurred step, so its presampled MTF is known.",
    ),
    Check(
        "nps_closed_form",
        "NPS = sigma^2 dx dy",
        "closed form",
        0.25,
        _nps_vs_closed_form,
        "White noise of known variance has a known flat spectrum.",
    ),
]


# ==========================================================================
# The defects
# ==========================================================================
@dataclass
class Defect:
    """One injectable defect, dialled by a severity in [0, 1]."""

    key: str
    label: str
    origin: str
    severity_label: str
    build: Callable[[float], Bundle]
    severities: np.ndarray = field(default_factory=lambda: SEVERITIES)


def _defect_sinc(alpha: float) -> Bundle:
    """The bin-average and central-difference transfer functions left in the estimate."""

    def transform(freq: np.ndarray, mtf: np.ndarray, h: float) -> np.ndarray:
        return mtf * (np.sinc(freq * h) * np.sinc(2.0 * freq * h)) ** alpha

    return run_pipeline(mtf_transform=transform, bin_subsample=SINC_BIN_SUBSAMPLE)


def _defect_jitter(alpha: float) -> Bundle:
    """The bin-centre correction omitted, at edge angles where the jitter bites."""
    return run_pipeline(
        edge_angle_deg=float(JITTER_ANGLES[int(round(alpha * (len(JITTER_ANGLES) - 1)))]),
        jitter_correction=alpha == 0.0,
    )


def _defect_nps_area(alpha: float) -> Bundle:
    """The pixel-area factor in the NPS normalisation, dropped by a fraction alpha."""
    return run_pipeline(nps_scale=(SPACING * SPACING) ** (-alpha))


def _defect_detrend(alpha: float) -> Bundle:
    """Detrending switched off over a background ramp of increasing amplitude."""
    if alpha == 0.0:
        return run_pipeline()
    return run_pipeline(nps_detrend="none", background_ramp=alpha * 60.0)


def _defect_disk(alpha: float) -> Bundle:
    """The 1-D edge profile applied radially, gaining pi sigma^2 of signal area."""

    def builder(contrast: float, radius_mm: float, edge_sigma_mm: float) -> np.ndarray:
        exact = _exact_disk(contrast, radius_mm, edge_sigma_mm)
        if alpha == 0.0:
            return exact
        wrong = _radially_blurred_disk(contrast, radius_mm, edge_sigma_mm)
        return (1.0 - alpha) * exact + alpha * wrong

    return run_pipeline(disk_builder=builder)


def _defect_no_floor(alpha: float) -> Bundle:
    """A prewhitening observer handed a measured spectrum that decays, with no floor."""
    return run_pipeline(correlation_sigma_mm=alpha * 0.5, observer_nps="measured", noise_floor=None)


DEFECTS = [
    Defect(
        "sinc",
        "MTF: bin-average and central-difference transfer left in",
        "standard failure mode",
        "fraction of the deconvolution omitted",
        _defect_sinc,
    ),
    Defect(
        "jitter",
        "MTF: bin-centre correction omitted",
        "found in this pipeline",
        "edge angle, 3 to 15 degrees",
        _defect_jitter,
    ),
    Defect(
        "nps_area",
        "NPS: pixel-area factor omitted",
        "standard failure mode",
        "fraction of the (dx dy) factor dropped",
        _defect_nps_area,
    ),
    Defect(
        "detrend",
        "NPS: detrending off under a background ramp",
        "standard failure mode",
        "ramp amplitude, 0 to 60 units",
        _defect_detrend,
    ),
    Defect(
        "disk",
        "signal: 1-D edge profile applied radially",
        "found in this pipeline",
        "fraction of the wrong construction",
        _defect_disk,
    ),
    Defect(
        "no_floor",
        "observer: no noise floor on a decaying spectrum",
        "found in this pipeline",
        "noise correlation, 0 to 0.5 mm",
        _defect_no_floor,
    ),
]


# ==========================================================================
# The study
# ==========================================================================
def _reported_error(b: Bundle, ref: Bundle) -> float:
    """The worse of the two numbers a user would report, against this defect's own zero."""
    return max(
        abs(b.d_prime_pw / ref.d_prime_pw - 1.0),
        abs(b.d_prime_neq / ref.d_prime_neq - 1.0),
    )


def main() -> None:
    reference = run_pipeline()
    print(f"reference: d'(PW) = {reference.d_prime_pw:.6f}, d'(NEQ) = {reference.d_prime_neq:.6f}")
    print(f"exact bridge at severity 0: {_bridge(reference):.2e}\n")

    rows: list[dict] = []
    for defect in DEFECTS:
        print(f"--- {defect.key}: {defect.label}")
        baseline = defect.build(0.0)  # this defect's own correct case
        alpha_detect: dict[str, float | None] = {c.key: None for c in CHECKS}
        alpha_material: float | None = None
        self_consistency_max = 0.0
        curve = []

        for alpha in defect.severities:
            refused = None
            try:
                b = defect.build(float(alpha))
            except Exception as exc:  # a precondition that refuses is a detection
                refused = type(exc).__name__
                curve.append(
                    {
                        "severity": float(alpha),
                        "reported_error": None,
                        "refused": refused,
                        "violations": {},
                    }
                )
                if alpha_detect["dynamic_range"] is None:
                    alpha_detect["dynamic_range"] = float(alpha)
                continue

            # The regression test most projects have: re-run, compare to the value
            # recorded from this same (defective) pipeline. Deterministic, so it agrees.
            snapshot = defect.build(float(alpha))
            self_consistency_max = max(
                self_consistency_max, abs(b.d_prime_neq / snapshot.d_prime_neq - 1.0)
            )

            err = _reported_error(b, baseline)
            violations = {c.key: float(c.measure(b)) for c in CHECKS}
            for c in CHECKS:
                if alpha_detect[c.key] is None and violations[c.key] > c.tolerance:
                    alpha_detect[c.key] = float(alpha)
            if alpha_material is None and alpha > 0 and err > MATERIAL:
                alpha_material = float(alpha)
            curve.append(
                {
                    "severity": float(alpha),
                    "reported_error": err,
                    "refused": None,
                    "violations": violations,
                }
            )

        fired = [k for k, v in alpha_detect.items() if v is not None]
        first = min((v for v in alpha_detect.values() if v is not None), default=None)
        max_err = max(
            (c["reported_error"] for c in curve if c["reported_error"] is not None),
            default=0.0,
        )
        rows.append(
            {
                "key": defect.key,
                "label": defect.label,
                "origin": defect.origin,
                "severity_label": defect.severity_label,
                "alpha_first_detection": first,
                "alpha_material_error": alpha_material,
                "checks_that_fired": fired,
                "per_check_alpha": alpha_detect,
                "max_reported_error": max_err,
                "self_consistency_max_disagreement": self_consistency_max,
                "curve": curve,
            }
        )
        det = "never" if first is None else f"{first:.1f}"
        mat = "never" if alpha_material is None else f"{alpha_material:.1f}"
        print(f"    fired: {fired or 'NONE'}")
        print(f"    first detection at {det}; d' materially wrong at {mat}")
        print(f"    worst error in a reported d': {max_err:.1%}")
        print(f"    self-consistency disagreement: {self_consistency_max:.1e}\n")

    caught = sum(1 for r in rows if r["checks_that_fired"])
    early = sum(
        1
        for r in rows
        if r["alpha_first_detection"] is not None
        and (
            r["alpha_material_error"] is None
            or r["alpha_first_detection"] <= r["alpha_material_error"]
        )
    )
    by_self = sum(1 for r in rows if r["self_consistency_max_disagreement"] > 1e-12)
    kind_of = {c.key: c.kind for c in CHECKS}
    # What survives the move to measured data: a defect is catchable without a phantom
    # only if at least one *identity* fires on it.
    catchable_without_truth = sum(
        1 for r in rows if any(kind_of[k] == "identity" for k in r["checks_that_fired"])
    )
    needs_known_truth = sum(
        1
        for r in rows
        if r["checks_that_fired"]
        and all(kind_of[k] == "closed form" for k in r["checks_that_fired"])
    )
    summary = {
        "n_defects": len(rows),
        "n_caught": caught,
        "n_caught_before_material_error": early,
        "n_caught_by_self_consistency": by_self,
        "n_catchable_without_ground_truth": catchable_without_truth,
        "n_requiring_a_known_truth_phantom": needs_known_truth,
        "material_threshold": MATERIAL,
        "reference": {
            "d_prime_pw": reference.d_prime_pw,
            "d_prime_neq": reference.d_prime_neq,
            "bridge_residual": _bridge(reference),
        },
        "checks": [
            {"key": c.key, "label": c.label, "kind": c.kind, "tolerance": c.tolerance, "why": c.why}
            for c in CHECKS
        ],
        "defects": rows,
    }
    (OUT / "injection.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=" * 68)
    print(f"defects injected                            {len(rows)}")
    print(f"caught by at least one check                {caught}")
    print(f"caught before d' was materially wrong       {early}")
    print(f"catchable with identities alone (no phantom) {catchable_without_truth}")
    print(f"needing a phantom of known truth            {needs_known_truth}")
    print(f"caught by self-consistency regression       {by_self}")
    print("=" * 68)

    _figure(rows)
    print(f"\nwrote {OUT / 'injection.json'} and {OUT / 'fig4_injection.png'}")


def _figure(rows: list[dict]) -> None:
    cols = [c.key for c in CHECKS] + ["self_consistency"]
    labels = [
        "Parseval",
        "bridge",
        "signal area",
        "NPS range",
        "MTF vs\nclosed form",
        "NPS vs\nclosed form",
        "self-\nconsistency",
    ]
    matrix = np.full((len(rows), len(cols)), np.nan)
    for r, row in enumerate(rows):
        for c, key in enumerate(cols[:-1]):
            a = row["per_check_alpha"].get(key)
            matrix[r, c] = np.nan if a is None else a
        matrix[r, -1] = np.nan  # never fires, by construction

    fig, (axL, axR) = plt.subplots(2, 1, figsize=(7.2, 9.6))

    cmap = plt.get_cmap("viridis_r").copy()
    cmap.set_bad("#eeeeee")
    detected = matrix[~np.isnan(matrix)]
    im = axL.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=0,
                    vmax=float(detected.max()) if detected.size else 1.0,
                    aspect="auto")
    axL.set_xticks(range(len(labels)))
    axL.set_xticklabels(labels, rotation=30, ha="right", fontsize=12)
    axL.set_yticks(range(len(rows)))
    axL.set_yticklabels([r["key"] for r in rows], fontsize=12)
    # Every detection in this experiment lands between 0.1 and 0.3 of a 0-1 colour scale,
    # so colour alone separates almost nothing -- which is what a reviewer saw. Printing
    # the severity in the cell makes the panel exact instead of approximate, and answers
    # in passing whether 0.1 is a real first detection or the grid's resolution limit.
    for r in range(len(rows)):
        for c in range(len(cols)):
            if np.isnan(matrix[r, c]):
                axL.text(c, r, "-", ha="center", va="center", fontsize=13, color="#888")
            else:
                value = matrix[r, c]
                axL.text(c, r, f"{value:.1f}", ha="center", va="center", fontsize=12,
                         color="white" if value > 0.55 else "black")
    axL.axvline(3.5, color="white", lw=2)
    axL.axvline(5.5, color="white", lw=2)
    axL.set_title("severity at first detection (grey: never)", fontsize=13)
    cb = fig.colorbar(im, ax=axL, fraction=0.030, pad=0.02)
    cb.set_label("severity", fontsize=12)
    cb.ax.tick_params(labelsize=11)

    for row in rows:
        pts = [
            (c["severity"], c["reported_error"])
            for c in row["curve"]
            if c["reported_error"] is not None and c["reported_error"] > 0
        ]
        if pts:
            axR.plot(*zip(*pts, strict=True), marker="o", ms=4.5, lw=1.8, label=row["key"])
    # The threshold goes in the legend, not floating over the axes: a text label
    # positioned in data coordinates overflows whenever the data range shifts.
    axR.axhline(MATERIAL, color="#d62728", ls="--", lw=1.1, label="5 % error in a reported $d'$")
    axR.set_yscale("log")
    # Open room below the data for the legend; otherwise it lands on the jitter curve,
    # whose errors are the smallest and so occupy exactly the corner a legend wants.
    lo, hi = axR.get_ylim()
    axR.set_ylim(lo / 60.0, hi)
    axR.set_xlabel("injected severity", fontsize=13)
    axR.set_ylabel("relative error in a reported $d'$", fontsize=13)
    axR.set_title("what the defect does to the answer", fontsize=13)
    handles, labels = axR.get_legend_handles_labels()
    order = [labels.index("5 % error in a reported $d'$")] + [
        i for i, lab in enumerate(labels) if lab != "5 % error in a reported $d'$"
    ]
    axR.legend(
        [handles[i] for i in order],
        [labels[i] for i in order],
        frameon=False,
        fontsize=11,
        ncol=2,
        loc="lower center",
    )
    axR.tick_params(labelsize=12)
    axR.spines[["top", "right"]].set_visible(False)

    # Panel labels, requested at review. Placed in axes coordinates just outside the
    # top-left corner so they do not move when the data range changes.
    for axis, letter in ((axL, "(a)"), (axR, "(b)")):
        axis.text(-0.08, 1.04, letter, transform=axis.transAxes,
                  fontsize=15, fontweight="bold", va="bottom", ha="left")

    fig.tight_layout()
    fig.savefig(OUT / "fig4_injection.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
