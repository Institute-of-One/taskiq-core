"""Generate the detection figure: the task, the scores, the ROC, and the identity.

Four panels:

* the score distributions the observer actually produces on an SKE/BKE experiment, with
  the Gaussian implied by its closed-form d' drawn over them;
* the ROC curves at three contrasts, with the AUC each closed-form d' predicts;
* the identity PC = AUC = Phi(d'/sqrt2) — measured against predicted, across a contrast
  sweep and three observers, all of which must land on the diagonal;
* proportion correct vs contrast: the psychometric curve, closed form against experiment.

Nothing here is fitted. Every dashed line is a closed form computed from the phantom and
the analytic NPS, with no reference to the images; every marker is measured by scoring the
images. They coincide, or something is wrong.

Run:
    python examples/detection.py
Writes:
    examples/output/detection.png
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
    d_prime_from_scores,
    ideal_linear,
    make_disk_signal,
    npwe,
    pc_from_d_prime,
    roc_curve,
    score_images,
    ske_bke_trials,
    two_afc,
)

SPACING = 0.1
SIZE = 64
NOISE_SD = 20.0
CORR_SIGMA = 0.25  # mm
WHITE_FLOOR_SD = 8.0  # the white floor every real detector has
N_TRIALS = 8000
SEED = 20260714

EYE = burgess_eye_filter(peak_cycles_per_mm=1.0)


def signal_of(contrast: float) -> np.ndarray:
    return make_disk_signal(
        SIZE, radius_mm=0.8, contrast=contrast, spacing=SPACING, edge_sigma_mm=0.1
    ).image.astype(np.float64)


def experiment(contrast: float, seed: int):
    return ske_bke_trials(
        signal_of(contrast), N_TRIALS, SPACING, NOISE_SD, seed=seed,
        correlation_sigma_mm=CORR_SIGMA, white_floor_sd=WHITE_FLOOR_SD,
    )


def predict(signal: np.ndarray, nps: np.ndarray):
    """Every observer's closed-form prediction, from the signal and the NPS alone.

    Note what this does *not* touch: the images. The prediction is made from the phantom and
    the noise power spectrum, and only then compared with what scoring the images gives.
    """
    return {
        "NPW": npwe(signal, nps, SPACING),
        "NPWE": npwe(signal, nps, SPACING, eye_filter=EYE),
        "ideal": ideal_linear(signal, nps, SPACING),
    }


def main() -> Path:
    contrasts = np.array([2.0, 3.0, 4.0, 6.0, 8.0, 10.0])
    rows = []
    nps = None
    for i, c in enumerate(contrasts):
        trials = experiment(float(c), SEED + i)
        nps = trials.nps  # the noise, and so its spectrum, does not depend on the contrast
        for name, result in predict(trials.signal, trials.nps).items():
            present = score_images(trials.present, result.template)
            absent = score_images(trials.absent, result.template)
            rows.append(
                {
                    "contrast": float(c),
                    "observer": name,
                    "d_predicted": result.d_prime,
                    "d_measured": d_prime_from_scores(present, absent),
                    "pc_predicted": float(pc_from_d_prime(result.d_prime)),
                    "pc_measured": two_afc(present, absent),
                    "present": present,
                    "absent": absent,
                }
            )

    def pick(observer: str, key: str) -> np.ndarray:
        return np.array([r[key] for r in rows if r["observer"] == observer])

    # ---------------------------------------------------------------- figure
    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.0))
    fig.suptitle(
        "taskiq-core — the SKE/BKE detection task: predicted (closed form) vs measured "
        "(experiment). Nothing is fitted.",
        fontsize=12,
    )
    colors = {"NPW": "tab:blue", "NPWE": "tab:orange", "ideal": "tab:green"}

    # --- score distributions, for one contrast, one observer
    ax = axes[0, 0]
    row = next(r for r in rows if r["contrast"] == 6.0 and r["observer"] == "NPWE")
    absent, present = row["absent"], row["present"]
    scale = np.sqrt(0.5 * (present.var(ddof=1) + absent.var(ddof=1)))
    lo, hi = min(absent.min(), present.min()), max(absent.max(), present.max())
    grid = np.linspace(lo, hi, 400)
    for label, scores, colour in (
        ("signal absent", absent, "0.45"),
        ("signal present", present, "tab:red"),
    ):
        ax.hist(scores, bins=70, density=True, alpha=0.45, color=colour, label=label)
        gauss = np.exp(-0.5 * ((grid - scores.mean()) / scale) ** 2) / (
            scale * np.sqrt(2 * np.pi)
        )
        ax.plot(grid, gauss, color=colour, lw=1.5)
    ax.set_xlabel("observer score λ")
    ax.set_ylabel("density")
    ax.set_title(
        f"NPWE score distributions (contrast 6, {N_TRIALS} trials/class)\n"
        f"predicted d' = {row['d_predicted']:.3f}, measured {row['d_measured']:.3f}\n"
        "equal-variance Gaussian, as the theory requires",
        fontsize=10,
    )
    ax.legend(fontsize=8)

    # --- ROC at three contrasts (NPWE)
    ax = axes[0, 1]
    for c, style in ((2.0, ":"), (4.0, "--"), (8.0, "-")):
        r = next(x for x in rows if x["contrast"] == c and x["observer"] == "NPWE")
        roc = roc_curve(r["present"], r["absent"])
        ax.plot(
            roc.fpr, roc.tpr, style, color="tab:orange", lw=1.8,
            label=f"contrast {c:g}:  AUC {roc.auc:.4f}  (predicted {r['pc_predicted']:.4f})",
        )
    ax.plot([0, 1], [0, 1], color="0.7", lw=1, zorder=0)
    ax.set_xlabel("false-positive rate")
    ax.set_ylabel("true-positive rate")
    ax.set_title("ROC (NPWE)\nmeasured area vs the area Φ(d'/√2) predicts")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.3)

    # --- the identity: measured vs predicted, everything on the diagonal
    ax = axes[1, 0]
    for name in ("NPW", "NPWE", "ideal"):
        ax.plot(
            pick(name, "d_predicted"), pick(name, "d_measured"), "o", ms=6,
            color=colors[name], mfc="none", label=f"{name}: d' measured vs predicted",
        )
    lim = [0.0, 1.05 * max(r["d_predicted"] for r in rows)]
    ax.plot(lim, lim, "k--", lw=1.2, label="y = x (they must coincide)")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("d' predicted in closed form (from the signal and the analytic NPS)")
    ax.set_ylabel("d' measured from the scores")
    worst = max(abs(r["d_measured"] / r["d_predicted"] - 1) for r in rows)
    ax.set_title(
        "The closed form predicts the experiment\n"
        f"18 (contrast × observer) points, worst disagreement {worst:.1%}"
    )
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)

    # --- psychometric curve: PC vs contrast
    ax = axes[1, 1]
    fine = np.linspace(1.0, 10.5, 60)
    curves = {name: [] for name in ("NPW", "NPWE", "ideal")}
    for c in fine:
        for name, result in predict(signal_of(float(c)), nps).items():
            curves[name].append(float(pc_from_d_prime(result.d_prime)))
    for name in ("NPW", "NPWE", "ideal"):
        ax.plot(fine, curves[name], "-", color=colors[name], lw=1.6,
                label=f"{name} (closed form)")
        ax.plot(
            pick(name, "contrast"), pick(name, "pc_measured"), "o", ms=6,
            color=colors[name], mfc="none", label=f"{name} (2AFC experiment)",
        )
    ax.axhline(0.5, color="0.7", lw=1, zorder=0)
    ax.set_xlabel("signal contrast")
    ax.set_ylabel("proportion correct, 2AFC")
    ax.set_ylim(0.45, 1.02)
    ax.set_title(
        "Psychometric curve: PC = Φ(d'/√2)\n"
        "lines predicted from the phantom and its NPS,\nmarkers from running the experiment",
        fontsize=10,
    )
    ax.legend(fontsize=8, ncol=2, loc="lower right")
    ax.grid(alpha=0.3)

    fig.tight_layout(rect=(0, 0, 1, 0.95))

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "detection.png"
    fig.savefig(out_path, dpi=140)
    plt.close(fig)

    print(f"{len(rows)} (contrast x observer) experiments, {N_TRIALS} trials per class:")
    for name in ("NPW", "NPWE", "ideal"):
        d_err = np.abs(pick(name, "d_measured") / pick(name, "d_predicted") - 1.0)
        pc_err = np.abs(pick(name, "pc_measured") - pick(name, "pc_predicted"))
        print(f"  {name:5s}: worst |Δd'| = {d_err.max():.2%} relative, "
              f"worst |ΔPC| = {pc_err.max():.4f} absolute")
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    main()
