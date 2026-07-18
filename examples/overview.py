"""Generate the overview figure: phantoms, and the metrics recovered from them.

Six panels — the three phantoms on the top row, and on the bottom row the estimated MTF
and NPS plotted *against their analytic ground truth*, which is the whole point: the
dashed curves are not fits, they are the closed forms the estimators are supposed to
recover.

Run:
    python examples/overview.py
Writes:
    examples/output/overview.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: no display needed, no backend surprises in CI

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # runnable without install

from taskiq_core import (
    gaussian_mtf,
    make_disk_signal,
    make_edge_phantom,
    make_uniform_phantom,
    mtf_from_edge,
    nps_2d,
)

SPACING = 0.1  # mm/pixel
BLUR_SIGMA = 0.25  # mm
NOISE_SD = 20.0
CORR_SIGMA = 0.3  # mm — Gaussian noise correlation length
SEED = 20260714


def main() -> Path:
    # ---------------------------------------------------------------- phantoms
    edge = make_edge_phantom(
        512,
        spacing=SPACING,
        contrast=1000.0,
        angle_deg=5.0,
        blur_sigma_mm=BLUR_SIGMA,
        noise_sd=2.0,
        seed=SEED,
    )
    uniform = make_uniform_phantom(
        128,
        spacing=SPACING,
        mean=100.0,
        noise_sd=NOISE_SD,
        seed=SEED,
        correlation_sigma_mm=CORR_SIGMA,
        n_realizations=64,
    )
    disk = make_disk_signal(64, radius_mm=1.0, contrast=10.0, spacing=SPACING, edge_sigma_mm=0.1)

    # ---------------------------------------------------------------- measure
    mtf = mtf_from_edge(edge.image, edge.spacing)  # angle estimated from the image
    nps = nps_2d(uniform.image, uniform.spacing)

    # The same measurement on a noise-free edge, to separate the estimator's own error
    # from the error the image noise puts into it. The first is what the test suite pins
    # down; the second is a property of the phantom, not of the code.
    clean = make_edge_phantom(
        512, spacing=SPACING, contrast=1000.0, angle_deg=5.0, blur_sigma_mm=BLUR_SIGMA
    )
    mtf_clean = mtf_from_edge(clean.image, clean.spacing)

    # ---------------------------------------------------------------- truth
    f_mtf = mtf.frequency
    mtf_truth = gaussian_mtf(f_mtf, BLUR_SIGMA)

    def max_rel_err(res):
        truth = gaussian_mtf(res.frequency, BLUR_SIGMA)
        b = truth > 0.05
        return float((np.abs(res.mtf[b] - truth[b]) / truth[b]).max())

    max_err = max_rel_err(mtf)
    max_err_clean = max_rel_err(mtf_clean)

    nps_truth = uniform.ground_truth["nps_white_level"] * np.exp(
        -4.0 * np.pi**2 * CORR_SIGMA**2 * nps.frequency**2
    )

    # ---------------------------------------------------------------- figure
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.2))
    fig.suptitle(
        "taskiq-core — synthetic phantoms and the physical metrics recovered from them "
        "(dashed = analytic truth)",
        fontsize=12,
    )

    ax = axes[0, 0]
    ax.imshow(edge.image, cmap="gray", origin="lower")
    ax.set_title(f"edge phantom\n{edge.ground_truth['angle_deg']}°, σ_blur = {BLUR_SIGMA} mm")
    ax.set_xlabel("x [px]")
    ax.set_ylabel("y [px]")

    ax = axes[0, 1]
    im = ax.imshow(uniform.image[0], cmap="gray", origin="lower")
    ax.set_title(
        f"uniform phantom (1 of {nps.n_rois} ROIs)\n"
        f"σ_white = {NOISE_SD}, correlated at {CORR_SIGMA} mm"
    )
    ax.set_xlabel("x [px]")
    fig.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[0, 2]
    im = ax.imshow(disk.image, cmap="gray", origin="lower")
    ax.set_title(
        f"disk signal\nr = {disk.ground_truth['radius_mm']} mm, "
        f"contrast = {disk.ground_truth['contrast']}"
    )
    ax.set_xlabel("x [px]")
    fig.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1, 0]
    ax.plot(f_mtf, mtf.mtf, lw=2, label="estimated (noisy edge)")
    ax.plot(
        mtf_clean.frequency,
        mtf_clean.mtf,
        lw=1.2,
        color="tab:orange",
        label="estimated (noise-free edge)",
    )
    ax.plot(f_mtf, mtf_truth, "k--", lw=1.5, label=r"analytic $e^{-2\pi^2\sigma^2f^2}$")
    ax.axvline(mtf.nyquist, color="0.6", ls=":", lw=1)
    ax.text(mtf.nyquist, 0.9, " Nyquist", color="0.4", fontsize=8, ha="left")
    ax.set_xlabel("spatial frequency [cycles/mm]")
    ax.set_ylabel("MTF")
    ax.set_ylim(-0.02, 1.15)
    ax.set_title(f"MTF — angle estimated {mtf.angle_deg:.3f}° (true 5°)")
    ax.text(
        0.97,
        0.62,
        "max rel. error where MTF > 0.05\n"
        f"noise-free edge: {max_err_clean:.4%}\n"
        f"noisy edge:     {max_err:.2%}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        family="monospace",
        bbox=dict(boxstyle="round", fc="white", ec="0.8", alpha=0.9),
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)

    ax = axes[1, 1]
    half = 1.2  # cycles/mm shown either side of DC
    im = ax.imshow(
        nps.nps,
        origin="lower",
        cmap="viridis",
        extent=(nps.fx[0], nps.fx[-1], nps.fy[0], nps.fy[-1]),
    )
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_xlabel(r"$f_x$ [cycles/mm]")
    ax.set_ylabel(r"$f_y$ [cycles/mm]")
    ax.set_title("2-D NPS — isotropic, as the filter is\n(DC bin is 0: detrending removes it)")
    fig.colorbar(im, ax=ax, fraction=0.046, label=r"NPS [value$^2$ mm$^2$]")

    ax = axes[1, 2]
    ax.plot(nps.frequency, nps.nps_radial, lw=2, label="estimated (radial average)")
    ax.plot(
        nps.frequency,
        nps_truth,
        "k--",
        lw=1.5,
        label=r"analytic $\sigma^2\Delta x\Delta y\,e^{-4\pi^2\sigma_c^2f^2}$",
    )
    ax.set_xlabel("radial frequency [cycles/mm]")
    ax.set_ylabel(r"NPS [value$^2$ mm$^2$]")
    ax.set_title(
        "radial NPS\n"
        rf"$\int$NPS = {nps.integral:.5g} = variance = {nps.variance:.5g}"
    )
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    fig.tight_layout(rect=(0, 0, 1, 0.96))

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "overview.png"
    fig.savefig(out_path, dpi=140)
    plt.close(fig)

    print(f"MTF: angle estimated {mtf.angle_deg:.4f}° (true 5.0°)")
    print(
        f"     max relative error vs analytic, where MTF > 0.05: "
        f"{max_err:.3%} (noisy edge), {max_err_clean:.5%} (noise-free edge)"
    )
    print(
        f"NPS: integral {nps.integral:.6g} vs variance {nps.variance:.6g} "
        f"(relative difference {abs(nps.integral / nps.variance - 1):.2e})"
    )
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    main()
