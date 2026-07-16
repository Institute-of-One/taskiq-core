"""Generate the observer figure: from physical image quality to task performance.

Four panels:

* the SKE/BKE task itself — the signal, and a signal-present trial it has to be found in;
* d' vs signal contrast, for every observer, closed form against Monte Carlo;
* d' vs noise correlation length, showing the gap between the ideal (prewhitening)
  observer and the non-prewhitening ones opening up as the noise becomes structured —
  which is the whole reason NPWE exists;
* the observer templates.

The dashed curves are closed forms and the markers are simulations. They are computed
independently of one another, so the fact that they land on top of each other is the
result, not the styling.

Run:
    python examples/observers.py
Writes:
    examples/output/observers.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # runnable without install

from taskiq_core import (
    burgess_eye_filter,
    cho,
    d_prime_from_scores,
    ideal_linear,
    laguerre_gauss_channels,
    make_disk_signal,
    make_uniform_phantom,
    npwe,
    score_images,
)

SPACING = 0.1  # mm/pixel
SIZE = 64
SIGMA = 20.0  # white-noise pixel SD
WHITE_NPS = SIGMA**2 * SPACING**2
WHITE_FLOOR_SD = 8.0  # the white component every physical detector has
FLOOR = WHITE_FLOOR_SD**2 * SPACING**2
RADIUS_MM = 0.8
N_TRIALS = 4000
SEED = 20260714

EYE = burgess_eye_filter(peak_cycles_per_mm=1.0)


def _transfer(correlation_sigma_mm: float) -> np.ndarray:
    """The Gaussian correlation filter H(f) on the DFT grid — the same one the phantom uses."""
    fy = np.fft.fftfreq(SIZE, d=SPACING)[:, None]
    fx = np.fft.fftfreq(SIZE, d=SPACING)[None, :]
    f2 = fy**2 + fx**2
    return np.exp(-2.0 * np.pi**2 * correlation_sigma_mm**2 * f2)


def prefilter_sd(correlation_sigma_mm: float) -> float:
    """White-field SD that leaves the *correlated* field at a pixel SD of SIGMA.

    Without this, sweeping the correlation length would also be sweeping the total noise
    power: the phantom's correlation filter attenuates, so a more correlated field is simply
    a quieter one, and every observer's d' would rise for a reason that has nothing to do
    with noise structure. Rescaling to a fixed variance is what isolates the effect the panel
    claims to show — the ideal observer exploiting *structure*, not merely less noise.
    """
    if correlation_sigma_mm == 0.0:
        return SIGMA
    h = _transfer(correlation_sigma_mm)
    return SIGMA / float(np.sqrt(np.mean(h**2)))


def nps_model(correlation_sigma_mm: float):
    """Correlated noise over a white floor — the floor is what a prewhitening observer needs."""
    sd = prefilter_sd(correlation_sigma_mm)
    level = sd**2 * SPACING**2

    def model(fr: np.ndarray) -> np.ndarray:
        return level * np.exp(-4.0 * np.pi**2 * correlation_sigma_mm**2 * fr**2) + FLOOR

    return model


def trials(n: int, signal: np.ndarray, seed: int, correlation_sigma_mm: float):
    """``n`` signal-present and ``n`` signal-absent images with the matching noise."""
    coloured = make_uniform_phantom(
        SIZE, spacing=SPACING, mean=100.0, noise_sd=prefilter_sd(correlation_sigma_mm),
        seed=seed, correlation_sigma_mm=correlation_sigma_mm, n_realizations=2 * n,
    ).image.astype(np.float64)
    white = make_uniform_phantom(
        SIZE, spacing=SPACING, mean=0.0, noise_sd=WHITE_FLOOR_SD, seed=seed + 77_000,
        n_realizations=2 * n,
    ).image.astype(np.float64)
    images = coloured + white
    return images[n:] + signal, images[:n]


def monte_carlo(result, signal, seed, correlation_sigma_mm):
    present, absent = trials(N_TRIALS, signal, seed, correlation_sigma_mm)
    return d_prime_from_scores(
        score_images(present, result.template), score_images(absent, result.template)
    )


def main() -> Path:
    signal = make_disk_signal(
        SIZE, radius_mm=RADIUS_MM, contrast=6.0, spacing=SPACING, edge_sigma_mm=0.1
    ).image.astype(np.float64)
    channels = laguerre_gauss_channels((SIZE, SIZE), SPACING, n_channels=6, width_mm=1.0)

    # ---------------------------------------------------- d' vs contrast (white noise)
    contrasts = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    curves: dict[str, list[float]] = {"npw": [], "npwe": [], "ideal": [], "cho": []}
    for c in contrasts:
        s = make_disk_signal(
            SIZE, radius_mm=RADIUS_MM, contrast=float(c), spacing=SPACING, edge_sigma_mm=0.1
        ).image.astype(np.float64)
        curves["npw"].append(npwe(s, WHITE_NPS, SPACING).d_prime)
        curves["npwe"].append(npwe(s, WHITE_NPS, SPACING, eye_filter=EYE).d_prime)
        curves["ideal"].append(ideal_linear(s, WHITE_NPS, SPACING).d_prime)
        present, absent = trials(N_TRIALS, s, SEED + 3, 0.0)
        curves["cho"].append(cho(present, absent, channels, method="split").d_prime)

    # ------------------------------------------- d' vs noise correlation length
    corr_lengths = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    by_corr: dict[str, list[float]] = {"npw": [], "npwe": [], "ideal": [], "cho": []}
    mc_corr: dict[str, list[float]] = {"npw": [], "npwe": [], "ideal": []}
    for corr in corr_lengths:
        model = nps_model(float(corr))
        r_npw = npwe(signal, model, SPACING)
        r_npwe = npwe(signal, model, SPACING, eye_filter=EYE)
        r_ideal = ideal_linear(signal, model, SPACING)
        by_corr["npw"].append(r_npw.d_prime)
        by_corr["npwe"].append(r_npwe.d_prime)
        by_corr["ideal"].append(r_ideal.d_prime)
        for key, res in (("npw", r_npw), ("npwe", r_npwe), ("ideal", r_ideal)):
            mc_corr[key].append(monte_carlo(res, signal, SEED + 11, float(corr)))
        present, absent = trials(N_TRIALS, signal, SEED + 5, float(corr))
        by_corr["cho"].append(cho(present, absent, channels, method="split").d_prime)

    # ---------------------------------------------------------------- figure
    example_present, _ = trials(1, signal, SEED, 0.3)
    templates = {
        "NPW": npwe(signal, nps_model(0.3), SPACING).template,
        "NPWE": npwe(signal, nps_model(0.3), SPACING, eye_filter=EYE).template,
        "ideal (prewhitening)": ideal_linear(signal, nps_model(0.3), SPACING).template,
    }

    fig = plt.figure(figsize=(13.5, 8.4))
    fig.suptitle(
        "taskiq-core — model observers on the SKE/BKE task "
        "(lines = closed form, markers = Monte Carlo)",
        fontsize=12,
    )
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.0])

    ax = fig.add_subplot(gs[0, 0])
    ax.imshow(signal, cmap="gray", origin="lower")
    ax.set_title(f"the signal s\nr = {RADIUS_MM} mm, contrast 6")
    ax.set_xlabel("x [px]")
    ax.set_ylabel("y [px]")

    ax = fig.add_subplot(gs[0, 1])
    ax.imshow(example_present[0], cmap="gray", origin="lower")
    ax.set_title("one signal-present trial\n(correlated noise, 0.3 mm)")
    ax.set_xlabel("x [px]")

    ax = fig.add_subplot(gs[0, 2])
    for label, style in (("npw", "-o"), ("npwe", "-s"), ("ideal", "-^"), ("cho", "--d")):
        ax.plot(contrasts, curves[label], style, ms=4, label=label.upper())
    ax.set_xlabel("signal contrast")
    ax.set_ylabel("d'")
    ax.set_title("d' vs contrast (white noise)\nlinear in contrast, as the algebra says")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[1, 0:2])
    colors = {"npw": "tab:blue", "npwe": "tab:orange", "ideal": "tab:green", "cho": "tab:red"}
    for label in ("ideal", "npw", "npwe"):
        ax.plot(corr_lengths, by_corr[label], "-", color=colors[label], lw=2,
                label=f"{label.upper()} (closed form)")
        ax.plot(corr_lengths, mc_corr[label], "o", color=colors[label], ms=6, mfc="none",
                label=f"{label.upper()} (Monte Carlo, {N_TRIALS} trials)")
    ax.plot(corr_lengths, by_corr["cho"], "--d", color=colors["cho"], lw=1.5, ms=5,
            label="CHO (6 Laguerre-Gauss channels, split)")
    ax.set_xlabel("noise correlation length σ_c [mm]   (total noise variance held fixed)")
    ax.set_ylabel("d'")
    ax.set_title(
        "d' vs noise structure, at constant noise power\n"
        "The ideal observer prewhitens the correlation away and recovers; the "
        "non-prewhitening ones cannot, and stay down.",
        fontsize=10,
    )
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)

    ax = fig.add_subplot(gs[1, 2])
    for i, (name, tmpl) in enumerate(templates.items()):
        profile = tmpl[SIZE // 2] / np.abs(tmpl[SIZE // 2]).max()
        x = (np.arange(SIZE) - (SIZE - 1) / 2) * SPACING
        ax.plot(x, profile + 2.4 * i, lw=1.6, label=name)
        ax.axhline(2.4 * i, color="0.85", lw=0.6, zorder=0)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("template profile (offset, normalised)")
    ax.set_title("observer templates\n(σ_c = 0.3 mm)")
    ax.set_yticks([])
    ax.legend(fontsize=8)
    ax.set_xlim(-2.0, 2.0)

    fig.tight_layout(rect=(0, 0, 1, 0.95))

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "observers.png"
    fig.savefig(out_path, dpi=140)
    plt.close(fig)

    print("d' at σ_c = 0 (white noise):")
    exact = float(np.linalg.norm(signal) / np.hypot(SIGMA, WHITE_FLOOR_SD))
    print(f"  NPW closed form {by_corr['npw'][0]:.4f} | ||s||/σ_total = {exact:.4f} "
          f"(exact identity, rel. diff {abs(by_corr['npw'][0] / exact - 1):.1e})")
    print("closed form vs Monte Carlo, worst disagreement over the correlation sweep:")
    for key in ("npw", "npwe", "ideal"):
        err = np.abs(np.array(by_corr[key]) - np.array(mc_corr[key]))
        rel = err / np.array(by_corr[key])
        print(f"  {key:5s}: max |Δd'| = {err.max():.4f} ({rel.max():.2%} relative)")
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    main()
