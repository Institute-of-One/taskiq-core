"""Generate the preprint figures and numbers from taskiq_core, deterministically.

Every value quoted in the manuscript is produced here and written to
``paper/figures/results.json`` so text and figures cannot diverge. Nothing here
uses unseeded randomness; each stochastic call takes an explicit seed.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from taskiq_core import (  # noqa: E402
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

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.titlesize": 9, "figure.dpi": 200})

SPACING = 0.1
results: dict = {}


# --------------------------------------------------------------------------
# Figure 1 — the physical estimators against their closed forms
# --------------------------------------------------------------------------
def figure_physical() -> None:
    """Slanted-edge MTF vs exp(-2 pi^2 sigma^2 f^2); white NPS vs its flat closed form."""
    # MTF: sweep blur x angle, hold each estimate to the analytic Gaussian.
    blurs = [0.15, 0.2, 0.35]
    angles = [3.0, 5.0, 7.0, 10.0, 15.0]
    max_rel = 0.0
    for sig in blurs:
        for ang in angles:
            edge = make_edge_phantom(
                512, spacing=SPACING, contrast=1000.0, angle_deg=ang, blur_sigma_mm=sig
            )
            est = mtf_from_edge(edge.image, edge.spacing)
            truth = gaussian_mtf(est.frequency, sig)
            band = truth > 0.05  # compare where the MTF carries signal
            rel = np.abs(est.mtf[band] - truth[band]) / truth[band]
            max_rel = max(max_rel, float(rel.max()))

    # A representative MTF curve for the figure.
    edge = make_edge_phantom(
        512, spacing=SPACING, contrast=1000.0, angle_deg=5.0, blur_sigma_mm=0.2
    )
    est = mtf_from_edge(edge.image, edge.spacing)
    f = est.frequency
    truth = gaussian_mtf(f, 0.2)

    # NPS: white noise -> flat at sigma^2 dx dy; check the integral identity.
    noise_sd = 20.0
    rois = make_uniform_phantom(128, spacing=SPACING, noise_sd=noise_sd, seed=0, n_realizations=128)
    nps = nps_2d(rois.image, rois.spacing)
    white_level = noise_sd**2 * SPACING**2
    # Two distinct claims, kept separate:
    #  (a) the normalisation *identity* -- integrating the returned NPS over the frequency
    #      plane returns the sample variance of the input, exactly, by construction; and
    #  (b) the estimate recovers the *population* white level sigma^2 to sampling error.
    nps2d = nps.nps
    du = 1.0 / (nps2d.shape[0] * SPACING)
    dv = 1.0 / (nps2d.shape[1] * SPACING)
    variance_from_nps = float(nps2d.sum() * du * dv)
    sample_variance = float(np.var(rois.image))
    identity_residual = abs(variance_from_nps - sample_variance) / sample_variance
    population_rel_error = abs(variance_from_nps - noise_sd**2) / noise_sd**2

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(6.6, 2.9))
    axL.plot(f, truth, color="#4C78A8", lw=1.6, label=r"analytic $e^{-2\pi^2\sigma^2 f^2}$")
    axL.plot(f, est.mtf, color="#d62728", lw=0.0, marker="o", ms=2.2, label="slanted-edge estimate")
    axL.set_xlabel("spatial frequency (cycles/mm)")
    axL.set_ylabel("MTF")
    axL.set_xlim(0, 1.0 / (2 * SPACING))
    axL.legend(frameon=False, fontsize=7)
    axL.spines[["top", "right"]].set_visible(False)

    axR.axhline(
        white_level, color="#4C78A8", lw=1.6, label=r"analytic $\sigma^2\,\Delta x\,\Delta y$"
    )
    axR.plot(
        nps.frequency,
        nps.nps_radial,
        color="#d62728",
        lw=0.0,
        marker="o",
        ms=2.2,
        label="radial NPS estimate",
    )
    axR.set_xlabel("radial frequency (cycles/mm)")
    axR.set_ylabel(r"NPS (value$^2\,$mm$^2$)")
    axR.set_ylim(0, 2 * white_level)
    axR.legend(frameon=False, fontsize=7)
    axR.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_physical.png", bbox_inches="tight")
    plt.close(fig)

    results["physical"] = {
        "mtf_n_combinations": len(blurs) * len(angles),
        "mtf_max_rel_error_pct": round(max_rel * 100.0, 4),
        "nps_noise_sd": noise_sd,
        "nps_white_level": round(white_level, 4),
        "nps_variance_recovered": round(variance_from_nps, 3),
        "nps_sample_variance": round(sample_variance, 3),
        "nps_identity_residual": float(identity_residual),
        "nps_n_realizations": 128,
        "nps_population_rel_error_pct": round(population_rel_error * 100.0, 3),
    }


# --------------------------------------------------------------------------
# Figure 2 — the physical-to-task bridge: d'^2 = integral of NEQ |S_obj|^2
# --------------------------------------------------------------------------
def figure_bridge() -> None:
    """d'^2 computed two independent ways — the validated observer, and NEQ against |S_obj|^2."""
    size, noise_sd = 64, 20.0
    level = noise_sd**2 * SPACING**2
    area = SPACING * SPACING
    fy = np.fft.fftfreq(size, d=SPACING)[:, None]
    fx = np.fft.fftfreq(size, d=SPACING)[None, :]

    settings = [(c, sig) for c in (3.0, 6.0, 9.0) for sig in (0.10, 0.15, 0.20)]
    d2_obs, d2_neq = [], []
    for contrast, sigma in settings:
        s_obj = make_disk_signal(
            size, radius_mm=0.8, contrast=contrast, spacing=SPACING
        ).image.astype(np.float64)
        mtf2d = np.exp(-2.0 * np.pi**2 * sigma**2 * (fy**2 + fx**2))
        s_img = np.fft.ifft2(np.fft.fft2(s_obj) * mtf2d).real
        # Route A: the independently validated ideal observer.
        d2_obs.append(ideal_linear(s_img, level, SPACING).d_prime ** 2)
        # Route B: NEQ = MTF^2 / NPS integrated against the object power spectrum.
        s_spec = area * np.fft.fft2(s_obj)
        neq2d = mtf2d**2 / level
        du_dv = 1.0 / (size * size * area)
        d2_neq.append(float(np.sum(neq2d * np.abs(s_spec) ** 2) * du_dv))

    d2_obs = np.array(d2_obs)
    d2_neq = np.array(d2_neq)
    bridge_max_rel = float(np.abs(d2_neq / d2_obs - 1.0).max())

    # A representative 1-D NEQ curve for the left panel.
    nyq = 1.0 / (2.0 * SPACING)
    fr = np.linspace(nyq / 200.0, nyq, 200)
    neq_res = neq(lambda ff: gaussian_mtf(ff, 0.15), level, frequency=fr)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(6.6, 2.9))
    axL.plot(fr, neq_res.neq, color="#4C78A8", lw=1.6)
    axL.set_xlabel("radial frequency (cycles/mm)")
    axL.set_ylabel(r"NEQ $=$ MTF$^2/$NPS")
    axL.set_title(r"NEQ of the system ($\sigma=0.15$ mm)", fontsize=8)
    axL.spines[["top", "right"]].set_visible(False)

    lo = float(min(d2_obs.min(), d2_neq.min()))
    hi = float(max(d2_obs.max(), d2_neq.max()))
    axR.plot([lo, hi], [lo, hi], color="#888", lw=0.9, ls="--", label="identity")
    axR.scatter(d2_obs, d2_neq, color="#d62728", s=22, zorder=3)
    axR.set_xlabel(r"$d'^2$ from the ideal observer")
    axR.set_ylabel(r"$d'^2$ from $\int$ NEQ $|S_{\rm obj}|^2$")
    axR.set_title(f"agreement to {bridge_max_rel:.1e} (rel.)", fontsize=8)
    axR.legend(frameon=False, fontsize=7, loc="upper left")
    axR.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_bridge.png", bbox_inches="tight")
    plt.close(fig)

    results["bridge"] = {
        "n_conditions": len(settings),
        "contrasts": sorted({c for c, _ in settings}),
        "blur_sigmas_mm": sorted({s for _, s in settings}),
        "max_rel_error": bridge_max_rel,
    }


# --------------------------------------------------------------------------
# Figure 3 — the transfer laws: d'^2 linear in contrast^2 and in 1/sigma^2
# --------------------------------------------------------------------------
def figure_transfer() -> None:
    """fit_transfer recovers the exact contrast^2 and inverse-variance laws (R^2 = 1)."""
    base = AtlasConfig(size=64, spacing=SPACING, radius_mm=0.8, blur_sigma_mm=0.15, noise_sd=20.0)

    contrasts = [2, 3, 4, 6, 8, 10]
    tc = sweep(base, {"contrast": contrasts}, observers=("ideal",), seed=0)
    c = tc.column("contrast")
    d2_c = tc.column("d_ideal") ** 2
    reg_c = fit_transfer(c**2, d2_c, names=["contrast^2"], fit_intercept=False)

    noises = [10, 15, 20, 30, 40]
    tn = sweep(base, {"noise_sd": noises}, observers=("ideal",), seed=0)
    inv_var = 1.0 / tn.column("noise_sd") ** 2
    d2_n = tn.column("d_ideal") ** 2
    reg_n = fit_transfer(inv_var, d2_n, names=["1/sigma^2"], fit_intercept=False)

    # Efficiency of NPWE relative to the ideal observer, across contrast (should be flat).
    te = sweep(base, {"contrast": contrasts}, observers=("ideal", "NPWE"), seed=0)
    eff = te.column("efficiency_NPWE")

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(6.6, 2.9))
    xx = np.linspace(0, max(c**2) * 1.05, 50)
    axL.plot(
        xx, reg_c.predict(xx), color="#4C78A8", lw=1.4, label=f"fit, $R^2$={reg_c.r_squared:.4f}"
    )
    axL.scatter(c**2, d2_c, color="#d62728", s=22, zorder=3)
    axL.set_xlabel(r"contrast$^2$")
    axL.set_ylabel(r"$d'^2$ (ideal)")
    axL.legend(frameon=False, fontsize=7)
    axL.spines[["top", "right"]].set_visible(False)

    xn = np.linspace(0, max(inv_var) * 1.05, 50)
    axR.plot(
        xn, reg_n.predict(xn), color="#4C78A8", lw=1.4, label=f"fit, $R^2$={reg_n.r_squared:.4f}"
    )
    axR.scatter(inv_var, d2_n, color="#d62728", s=22, zorder=3)
    axR.set_xlabel(r"$1/\sigma^2$")
    axR.set_ylabel(r"$d'^2$ (ideal)")
    axR.legend(frameon=False, fontsize=7)
    axR.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_transfer.png", bbox_inches="tight")
    plt.close(fig)

    results["transfer"] = {
        "contrast_r_squared": round(float(reg_c.r_squared), 8),
        "contrast_slope": round(float(reg_c.coef[0]), 6),
        "dose_r_squared": round(float(reg_n.r_squared), 8),
        "dose_slope": round(float(reg_n.coef[0]), 4),
        "npwe_efficiency_mean": round(float(np.mean(eff)), 4),
        "npwe_efficiency_spread": float(np.max(eff) - np.min(eff)),
    }


if __name__ == "__main__":
    print("Figure 1: physical estimators vs closed form ...")
    figure_physical()
    print("Figure 2: physical-to-task bridge ...")
    figure_bridge()
    print("Figure 3: transfer laws ...")
    figure_transfer()
    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\nSaved figures and results.json to", OUT)
    print(json.dumps(results, indent=2))
