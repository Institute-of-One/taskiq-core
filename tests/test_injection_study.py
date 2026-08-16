"""The injection study must not cry wolf, and must not be fooled by itself.

Every finding in the study rests on two properties that are easy to break and whose
breakage looks like a result rather than a bug. Both cost a few seconds to check and
both were violated by earlier drafts of the study, in ways that read as discoveries:

* **No check may fire on a correct pipeline.** An invariant that fires at severity
  zero reports every defect as "detected at the first severity tried", which looks
  like a very sensitive guard and is in fact a broken one. Three separate causes did
  this -- the DC bin of a mean-detrended NPS sitting at 1e-31, a bridge comparing two
  routes that disagreed about the noise model, and a tolerance set below the
  estimator's own reproducibility.
* **The self-consistency control must never fire.** Its whole role is to be the check
  that cannot see any of this. If it ever disagrees, it is comparing against the wrong
  snapshot and the study's headline ("0 of 6") is measuring nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "paper"))

from make_injection_study import (  # noqa: E402
    CHECKS,
    DEFECTS,
    run_pipeline,
)


@pytest.fixture(scope="module")
def reference():
    return run_pipeline()


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.key)
def test_no_check_fires_on_a_correct_pipeline(check, reference) -> None:
    """A guard that fires when nothing is wrong cannot date the onset of anything."""
    value = check.measure(reference)
    assert value <= check.tolerance, (
        f"{check.key} fires on the reference pipeline: {value:.3e} > {check.tolerance:.3e}"
    )


@pytest.mark.parametrize("defect", DEFECTS, ids=lambda d: d.key)
def test_no_check_fires_at_severity_zero(defect) -> None:
    """Severity zero must recover the correct pipeline for every defect separately."""
    bundle = defect.build(0.0)
    fired = {c.key: c.measure(bundle) for c in CHECKS if c.measure(bundle) > c.tolerance}
    assert not fired, f"{defect.key} already violates {fired} before it is injected"


@pytest.mark.parametrize("defect", DEFECTS, ids=lambda d: d.key)
def test_every_defect_is_caught_by_something(defect) -> None:
    """If a defect at full severity trips nothing, the check set has a hole in it.

    A precondition that refuses to run at all is the strongest detection available,
    so a raised guard counts, and counts first.
    """
    try:
        bundle = defect.build(1.0)
    except ValueError:
        return  # the pipeline refused: detected before it could return a number
    fired = [c.key for c in CHECKS if c.measure(bundle) > c.tolerance]
    assert fired, f"{defect.key} at full severity trips no check"


@pytest.mark.parametrize("defect", DEFECTS, ids=lambda d: d.key)
def test_self_consistency_never_fires(defect) -> None:
    """The regression test compares the defective pipeline to itself, so it agrees."""
    for severity in (0.0, 0.5, 1.0):
        try:
            first = defect.build(severity)
            second = defect.build(severity)
        except ValueError:
            continue  # refused deterministically; there is no number to disagree about
        assert first.d_prime_neq == pytest.approx(second.d_prime_neq, rel=1e-12)
        assert first.d_prime_pw == pytest.approx(second.d_prime_pw, rel=1e-12)


def test_the_bridge_is_exact_not_approximate(reference) -> None:
    """The two routes are the same integral rearranged; nothing may erode that."""
    assert reference.d_prime_bridge_exact == pytest.approx(reference.d_prime_pw, rel=1e-12)
