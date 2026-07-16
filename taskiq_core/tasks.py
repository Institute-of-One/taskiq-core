r"""Detection tasks: the experiment, and the figures of merit that score it.

This module owns the *task* side of the pipeline. :mod:`taskiq_core.observers` turns an
image into a score; this module produces the images to be scored, and turns the resulting
scores into the numbers a study reports — ``d'``, AUC, and the proportion correct in a
two-alternative forced-choice experiment.

The SKE/BKE task
----------------
Signal-known-exactly / background-known-exactly. The observer is told precisely what it is
looking for (the signal ``s``) and precisely what the background is (flat); the only thing
it does not know is whether the signal is there. It is the simplest detection task that
still has all the structure that matters, and — crucially — the one for which ``d'`` has a
closed form, which is what lets every observer in this codebase be validated analytically.

:func:`ske_bke_trials` builds such an experiment: ``n_trials`` signal-present and
``n_trials`` signal-absent images, from a single seeded RNG stream, together with the
**analytic NPS of the noise it just generated**. That last part matters — it means an
observer can be handed the exact noise power spectrum of the images it is about to score,
rather than an estimate of it, so a disagreement between the closed-form ``d'`` and the
measured one is a bug in the observer and nothing else.

The identity that ties it all together
--------------------------------------
For an equal-variance Gaussian test statistic — which is what every linear observer here
produces, since its score is a linear functional of Gaussian noise —

.. math::  \mathrm{PC}_{2\mathrm{AFC}} = \mathrm{AUC} = \Phi\!\left(\frac{d'}{\sqrt2}\right)

Three quantities, three independent routes to them: ``d'`` from the separation of the score
means, AUC from counting correctly ordered pairs (Mann-Whitney), and PC from actually
running a forced-choice experiment. They must agree, and the test suite checks that they do
— which is a stronger statement than any one of them checked alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.special import ndtr, ndtri

from taskiq_core.phantoms import make_uniform_phantom

#: The white floor is drawn from its own RNG stream. The offset is large and arbitrary rather
#: than ``+1`` so that one experiment's floor stream cannot coincide with the *main* stream of
#: the experiment seeded one higher.
_FLOOR_SEED_OFFSET = 982_451_653

__all__ = [
    "TrialSet",
    "ROCResult",
    "ske_bke_trials",
    "d_prime_from_scores",
    "auc_from_scores",
    "roc_curve",
    "two_afc",
    "pc_from_d_prime",
    "d_prime_from_pc",
]


# --------------------------------------------------------------------------------------
# the experiment
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class TrialSet:
    """A complete SKE/BKE detection experiment, and the truth about the noise in it.

    Attributes
    ----------
    present, absent:
        Image stacks ``(n_trials, ny, nx)``. ``present`` is background + noise + signal;
        ``absent`` is background + noise. Both noise fields come from the same seeded RNG
        stream, so the whole experiment is reproducible from ``seed`` alone.
    signal:
        The signal ``s`` that was added — the same array an observer takes as its template.
    nps:
        The **analytic** noise power spectrum of these images, in ``value^2 mm^2``, DC-centred
        (the layout of :class:`~taskiq_core.physical.NPSResult` and of the ``nps`` argument to
        the observers). Not measured from the images: computed in closed form from the noise
        model that generated them. Hand it to an observer and any disagreement between its
        closed-form ``d'`` and the ``d'`` you measure from the scores is a bug in the
        observer, not noise in an NPS estimate.
    spacing, noise_sd, correlation_sigma_mm, white_floor_sd, background, n_trials, seed:
        Everything needed to reconstruct the experiment.
    meta:
        Derived facts about the noise, including ``pixel_sd`` (the true total pixel standard
        deviation, which is *not* ``noise_sd`` when the noise is correlated) and
        ``nps_dc_is_zero`` (always ``False`` here — an analytic NPS has real power at DC,
        unlike a measured one).
    """

    present: np.ndarray
    absent: np.ndarray
    signal: np.ndarray
    nps: np.ndarray
    spacing: float
    noise_sd: float
    correlation_sigma_mm: float
    white_floor_sd: float
    background: float
    n_trials: int
    seed: int
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, int]:
        """``(ny, nx)`` of a single trial image."""
        return self.present.shape[1:]  # type: ignore[return-value]


def ske_bke_trials(
    signal: np.ndarray,
    n_trials: int,
    spacing: float,
    noise_sd: float,
    seed: int,
    *,
    background: float = 100.0,
    correlation_sigma_mm: float = 0.0,
    white_floor_sd: float = 0.0,
) -> TrialSet:
    r"""Generate a signal-known-exactly / background-known-exactly detection experiment.

    ``n_trials`` signal-present and ``n_trials`` signal-absent images, all drawn from one
    seeded RNG stream, plus the closed-form NPS of the noise that went into them:

    .. math::  \mathrm{NPS}(f) = \sigma^2\,\Delta x\,\Delta y\;
               e^{-4\pi^2\sigma_c^2 f^2} \;+\; \sigma_w^2\,\Delta x\,\Delta y

    the first term from the (optionally Gaussian-correlated) noise field and the second from
    the white floor.

    On the white floor
    ------------------
    ``white_floor_sd`` adds an independent white noise field. It is worth understanding why
    it exists rather than treating it as an extra knob: a *purely* Gaussian-correlated noise
    field has power decaying like :math:`e^{-4\pi^2\sigma_c^2 f^2}`, which is to say
    essentially zero at high frequency — and a prewhitening observer, which weights by
    ``1/NPS``, then reports an essentially infinite ``d'`` built entirely out of numerical
    rounding (:func:`taskiq_core.observers.ideal_linear` refuses to). Real detectors have a
    white floor: electronic noise, quantisation. Give the experiment one and the ideal
    observer becomes well-posed. Leave it at zero and the non-prewhitening observers still
    work fine.

    Parameters
    ----------
    signal:
        The signal to embed, e.g. ``make_disk_signal(...).image``. Shape ``(ny, nx)``.
    n_trials:
        Number of trials **per class**; the experiment holds ``2 * n_trials`` images.
    spacing:
        Pixel pitch in mm.
    noise_sd:
        Standard deviation of the noise field *before* any correlation filter. When
        ``correlation_sigma_mm > 0`` the filter attenuates, so the resulting pixel standard
        deviation is smaller; the true value is reported as ``meta["pixel_sd"]`` rather than
        being papered over by a rescaling.
    seed:
        Seed for the whole experiment. Required — a detection experiment you cannot reproduce
        is not evidence of anything.
    background:
        The flat background level (the "BKE" part).
    correlation_sigma_mm:
        Gaussian correlation length of the noise, in mm. ``0`` gives white noise.
    white_floor_sd:
        Standard deviation of an additional, independent white noise field. See above.

    Returns
    -------
    TrialSet

    Raises
    ------
    ValueError
        On a non-2-D or zero signal, a non-positive ``n_trials`` or ``spacing``, negative
        noise parameters, or noise with no power at all (``noise_sd`` and ``white_floor_sd``
        both zero, which would make every score identical and ``d'`` undefined).
    """
    sig = np.asarray(signal, dtype=np.float64)
    if sig.ndim != 2:
        raise ValueError(f"signal must be a 2-D image, got shape {sig.shape}")
    if not np.all(np.isfinite(sig)):
        raise ValueError("signal contains non-finite values")
    if not np.any(sig):
        raise ValueError("signal is identically zero: there would be nothing to detect")

    n_trials = int(n_trials)
    if n_trials < 2:
        raise ValueError(f"n_trials must be >= 2 (a variance needs two samples), got {n_trials}")

    spacing = float(spacing)
    if not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError(f"spacing must be a finite positive number of mm, got {spacing!r}")

    for name, value in (
        ("noise_sd", noise_sd),
        ("correlation_sigma_mm", correlation_sigma_mm),
        ("white_floor_sd", white_floor_sd),
    ):
        value = float(value)
        if not np.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and >= 0, got {value!r}")
    noise_sd = float(noise_sd)
    correlation_sigma_mm = float(correlation_sigma_mm)
    white_floor_sd = float(white_floor_sd)

    if noise_sd == 0.0 and white_floor_sd == 0.0:
        raise ValueError(
            "the trials would have no noise at all, so every score would be identical and d' "
            "undefined; set noise_sd and/or white_floor_sd"
        )

    ny, nx = sig.shape

    # One phantom call, 2 * n_trials realisations from a single RNG stream: absent first,
    # present second. Deterministic in `seed` alone.
    field_ = make_uniform_phantom(
        (ny, nx),
        spacing=spacing,
        mean=background,
        noise_sd=noise_sd,
        seed=seed,
        correlation_sigma_mm=correlation_sigma_mm,
        n_realizations=2 * n_trials,
    )
    images = field_.image.astype(np.float64)
    pixel_variance = float(field_.ground_truth["pixel_sd_expected"] ** 2)

    if white_floor_sd > 0.0:
        floor = make_uniform_phantom(
            (ny, nx),
            spacing=spacing,
            mean=0.0,
            noise_sd=white_floor_sd,
            seed=seed + _FLOOR_SEED_OFFSET,
            n_realizations=2 * n_trials,
        )
        images = images + floor.image.astype(np.float64)
        pixel_variance += white_floor_sd**2

    absent = images[:n_trials]
    present = images[n_trials:] + sig

    nps = _analytic_nps(
        (ny, nx), spacing, noise_sd, correlation_sigma_mm, white_floor_sd
    )

    return TrialSet(
        present=present,
        absent=absent,
        signal=sig,
        nps=nps,
        spacing=spacing,
        noise_sd=noise_sd,
        correlation_sigma_mm=correlation_sigma_mm,
        white_floor_sd=white_floor_sd,
        background=background,
        n_trials=n_trials,
        seed=int(seed),
        meta={
            "pixel_sd": float(np.sqrt(pixel_variance)),
            "nps_layout": "centered",
            "nps_dc_is_zero": False,
            "signal_energy": float(np.sum(sig**2)),
        },
    )


def _analytic_nps(
    shape: tuple[int, int],
    spacing: float,
    noise_sd: float,
    correlation_sigma_mm: float,
    white_floor_sd: float,
) -> np.ndarray:
    """Closed-form NPS of the noise ``ske_bke_trials`` generates, DC-centred.

    The correlation filter is applied by the phantom as an exact circular convolution on the
    DFT grid, so this is not an approximation of the noise in those images — it is the noise
    in those images.
    """
    ny, nx = shape
    fy = np.fft.fftfreq(ny, d=spacing)[:, None]
    fx = np.fft.fftfreq(nx, d=spacing)[None, :]
    f2 = fy**2 + fx**2
    area = spacing * spacing

    nps = noise_sd**2 * area * np.exp(-4.0 * np.pi**2 * correlation_sigma_mm**2 * f2)
    nps = nps + white_floor_sd**2 * area
    return np.fft.fftshift(nps)


# --------------------------------------------------------------------------------------
# figures of merit
# --------------------------------------------------------------------------------------


def d_prime_from_scores(present: np.ndarray, absent: np.ndarray) -> float:
    r"""Detectability from two score samples, using the pooled standard deviation.

    .. math::  d' = \frac{\bar\lambda_1 - \bar\lambda_0}{\sqrt{\tfrac12(s_1^2 + s_0^2)}}

    Uses the unbiased (``ddof=1``) sample variances. This is the *empirical* ``d'``; for the
    linear observers it must agree with their closed form, and checking that it does is the
    job of the Monte-Carlo tests.
    """
    p = np.asarray(present, dtype=np.float64).ravel()
    a = np.asarray(absent, dtype=np.float64).ravel()
    if p.size < 2 or a.size < 2:
        raise ValueError(
            f"need at least 2 scores per class to estimate a variance, got {p.size} present "
            f"and {a.size} absent"
        )
    if not np.all(np.isfinite(p)) or not np.all(np.isfinite(a)):
        raise ValueError("scores contain non-finite values")
    pooled = 0.5 * (p.var(ddof=1) + a.var(ddof=1))
    if pooled <= 0.0:
        raise ValueError(
            "both score distributions have zero variance, so d' is undefined (noise-free "
            "images?)"
        )
    return float((p.mean() - a.mean()) / np.sqrt(pooled))


def auc_from_scores(present: np.ndarray, absent: np.ndarray) -> float:
    """Area under the ROC curve, exactly, via the Mann-Whitney U statistic.

    This *is* the proportion of present/absent score pairs the observer orders correctly,
    counting ties as half — so it needs no threshold sweep, no interpolation, and no
    assumption about the shape of the score distributions (unlike
    :func:`pc_from_d_prime`, which assumes equal-variance Gaussians).
    """
    p = np.asarray(present, dtype=np.float64).ravel()
    a = np.asarray(absent, dtype=np.float64).ravel()
    if p.size == 0 or a.size == 0:
        raise ValueError("need at least one score in each class")
    if not np.all(np.isfinite(p)) or not np.all(np.isfinite(a)):
        raise ValueError("scores contain non-finite values")

    ranks = _average_ranks(np.concatenate([p, a]))
    u = ranks[: p.size].sum() - p.size * (p.size + 1) / 2.0
    return float(u / (p.size * a.size))


def _average_ranks(values: np.ndarray) -> np.ndarray:
    """1-based ranks, with tied values sharing their average rank."""
    order = np.argsort(values, kind="stable")
    sorted_vals = values[order]
    ranks = np.empty(values.size, dtype=np.float64)
    i = 0
    while i < values.size:
        j = i
        while j + 1 < values.size and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        ranks[order[i : j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


@dataclass(frozen=True, eq=False)
class ROCResult:
    """An empirical ROC curve.

    Attributes
    ----------
    fpr, tpr:
        False- and true-positive rates, starting at ``(0, 0)`` and ending at ``(1, 1)``.
    thresholds:
        The score threshold at each point (``+inf`` at the leading ``(0, 0)``).
    auc:
        Area under the curve — computed by :func:`auc_from_scores` (Mann-Whitney), *not* by
        integrating the sampled curve. The two agree exactly, including under ties, and the
        test suite checks that they do; but the rank statistic is the one to trust, because
        trapezoidal integration of a curve with ties depends on how the ties were broken.
    """

    fpr: np.ndarray
    tpr: np.ndarray
    thresholds: np.ndarray
    auc: float


def roc_curve(present: np.ndarray, absent: np.ndarray) -> ROCResult:
    """Empirical ROC curve from two score samples.

    Tied scores are collapsed into a single ROC point, which is what makes the trapezoidal
    area under this curve equal the Mann-Whitney AUC exactly rather than approximately: a run
    of ties becomes one diagonal segment whose trapezoid contributes precisely the half-credit
    the rank statistic gives it.
    """
    p = np.asarray(present, dtype=np.float64).ravel()
    a = np.asarray(absent, dtype=np.float64).ravel()
    if p.size == 0 or a.size == 0:
        raise ValueError("need at least one score in each class")
    if not np.all(np.isfinite(p)) or not np.all(np.isfinite(a)):
        raise ValueError("scores contain non-finite values")

    scores = np.concatenate([p, a])
    is_present = np.concatenate([np.ones(p.size), np.zeros(a.size)])

    order = np.argsort(-scores, kind="stable")  # descending
    scores = scores[order]
    is_present = is_present[order]

    tp = np.cumsum(is_present)
    fp = np.cumsum(1.0 - is_present)

    # Keep only the last index of each run of equal scores, so ties give one ROC point.
    last_of_run = np.r_[np.diff(scores) != 0.0, True]
    tp, fp, thresh = tp[last_of_run], fp[last_of_run], scores[last_of_run]

    tpr = np.r_[0.0, tp / p.size]
    fpr = np.r_[0.0, fp / a.size]
    thresholds = np.r_[np.inf, thresh]

    return ROCResult(
        fpr=fpr,
        tpr=tpr,
        thresholds=thresholds,
        auc=auc_from_scores(p, a),
    )


def two_afc(present: np.ndarray, absent: np.ndarray, *, pairing: str = "all") -> float:
    r"""Proportion correct in a two-alternative forced-choice experiment.

    The observer is shown one signal-present and one signal-absent image and must say which is
    which; it is correct when it scores the present one higher. Ties count as half — the
    observer is guessing.

    Parameters
    ----------
    pairing:
        ``"all"`` (default) averages over **every** present/absent pair, which makes PC exactly
        equal to the Mann-Whitney AUC — the same statistic, computed the same way, so
        :func:`two_afc` and :func:`auc_from_scores` return the identical number by construction
        rather than by coincidence.

        ``"sequential"`` pairs trial *i* with trial *i*, giving the proportion correct of an
        actually-run experiment of ``n`` forced-choice trials. It is unbiased for the same
        quantity but noisier — by a constant factor of roughly 1.4 at typical detectability,
        *not* by an order of magnitude. (It is tempting to reason that averaging over all
        ``n_p * n_a`` pairs must reduce the variance by a factor of ``n``, but those pairs are
        not independent: each one reuses images. The all-pairs estimator's standard error is
        still ``O(1/sqrt(n))``; it just has a smaller constant.) It requires equal-sized
        samples.

    Returns
    -------
    float
        Proportion correct, in ``[0, 1]``. For an equal-variance Gaussian statistic this must
        equal ``Phi(d'/sqrt(2))`` — see :func:`pc_from_d_prime`.
    """
    p = np.asarray(present, dtype=np.float64).ravel()
    a = np.asarray(absent, dtype=np.float64).ravel()
    if p.size == 0 or a.size == 0:
        raise ValueError("need at least one score in each class")
    if not np.all(np.isfinite(p)) or not np.all(np.isfinite(a)):
        raise ValueError("scores contain non-finite values")

    if pairing == "all":
        # Identical to the Mann-Whitney AUC, by construction.
        return auc_from_scores(p, a)
    if pairing == "sequential":
        if p.size != a.size:
            raise ValueError(
                f"pairing='sequential' pairs trial i with trial i, so it needs equally many "
                f"scores in each class, got {p.size} present and {a.size} absent. Use "
                "pairing='all' for unequal samples."
            )
        wins = (p > a).astype(np.float64) + 0.5 * (p == a)
        return float(wins.mean())
    raise ValueError(f"pairing must be 'all' or 'sequential', got {pairing!r}")


def pc_from_d_prime(d_prime: float | np.ndarray) -> np.ndarray:
    r"""Proportion correct in 2AFC implied by ``d'``: :math:`\Phi(d'/\sqrt2)`.

    Exact for an equal-variance Gaussian test statistic — which is what every linear observer
    in :mod:`taskiq_core.observers` produces, its score being a linear functional of Gaussian
    noise. It is also the AUC, so this one function converts ``d'`` into both.

    Not exact for a CHO with internal noise, or for any observer whose score distribution you
    have not checked is Gaussian; in that case measure it with :func:`two_afc` instead of
    assuming it.
    """
    d = np.asarray(d_prime, dtype=np.float64)
    if not np.all(np.isfinite(d)):
        raise ValueError("d_prime must be finite")
    return ndtr(d / np.sqrt(2.0))


def d_prime_from_pc(pc: float | np.ndarray) -> np.ndarray:
    r"""Invert :func:`pc_from_d_prime`: :math:`d' = \sqrt2\,\Phi^{-1}(\mathrm{PC})`.

    The route from a measured forced-choice experiment back to a detectability index. ``PC``
    must lie strictly inside ``(0, 1)``: a perfect score means the experiment saturated and
    ``d'`` is not identifiable from it — which is a fact about the experiment, so it raises
    rather than returning infinity.
    """
    p = np.asarray(pc, dtype=np.float64)
    if not np.all(np.isfinite(p)):
        raise ValueError("pc must be finite")
    if np.any(p <= 0.0) or np.any(p >= 1.0):
        raise ValueError(
            "pc must be strictly inside (0, 1): a proportion correct of exactly 0 or 1 means "
            "the experiment saturated, and d' cannot be recovered from it. Run more trials, or "
            "make the task harder."
        )
    return np.sqrt(2.0) * ndtri(p)
