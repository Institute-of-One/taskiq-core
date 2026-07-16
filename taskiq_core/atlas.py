"""Condition sweeps and the physical-to-task transfer — PLANNED, not yet implemented.

The point of the project: sweep acquisition conditions, measure both the physical
metrics and the task performance on the same synthetic images, and quantify how one
predicts the other.

Planned API
-----------
``sweep(conditions, seed) -> AtlasTable``
    Cartesian sweep over conditions (dose / noise level, blur, signal size and contrast).
    Each cell records MTF, NPS, NEQ, and observer ``d'`` / AUC for the same seeded
    realisation, so physical and task metrics are paired rather than merely adjacent.

``neq(mtf, nps) -> NEQResult``
    :math:`\\mathrm{NEQ}(f) = \\mathrm{MTF}^2(f) / \\mathrm{NPS}(f)`, on a common
    frequency axis interpolated from the two estimators.

``transfer(table, x, y) -> RegressionResult``
    Regress task performance on the physical summaries, with the fit and its residuals
    reported — the "physical -> task" transfer the study is about.

Deferred by design: sweeping is cheap; only worth doing once each metric in a cell is
known to be right.
"""

from __future__ import annotations

__all__: list[str] = []
