"""Same seed, same bits.

Reproducibility is a load-bearing claim of this project, so it is tested as an identity
(``bytes`` equality of the raw buffers), not as "close enough". The check runs from the
phantom all the way through to the estimated MTF and NPS: a pipeline that is only
*almost* deterministic cannot support a citable result.
"""

from __future__ import annotations

import numpy as np
import pytest

from taskiq_core import (
    make_disk_signal,
    make_edge_phantom,
    make_uniform_phantom,
    mtf_from_edge,
    nps_2d,
)


def _identical(a: np.ndarray, b: np.ndarray) -> bool:
    """Bit-for-bit identity, which is stricter than ``==`` (it also pins dtype and shape)."""
    return a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()


def test_edge_phantom_is_bit_reproducible():
    kwargs = dict(
        size=128, spacing=0.1, contrast=1000.0, angle_deg=5.0,
        blur_sigma_mm=0.25, noise_sd=8.0,
    )
    a = make_edge_phantom(seed=1234, **kwargs)
    b = make_edge_phantom(seed=1234, **kwargs)
    c = make_edge_phantom(seed=1235, **kwargs)

    assert _identical(a.image, b.image)
    assert not _identical(a.image, c.image)
    assert a.seed == 1234


def test_uniform_phantom_is_bit_reproducible():
    kwargs = dict(size=64, spacing=0.1, mean=100.0, noise_sd=15.0)
    assert _identical(
        make_uniform_phantom(seed=7, **kwargs).image,
        make_uniform_phantom(seed=7, **kwargs).image,
    )
    assert not _identical(
        make_uniform_phantom(seed=7, **kwargs).image,
        make_uniform_phantom(seed=8, **kwargs).image,
    )


def test_correlated_noise_and_stacks_are_bit_reproducible():
    kwargs = dict(size=64, noise_sd=20.0, correlation_sigma_mm=0.3, n_realizations=5)
    a = make_uniform_phantom(seed=99, **kwargs)
    b = make_uniform_phantom(seed=99, **kwargs)
    assert _identical(a.image, b.image)
    assert a.image.shape == (5, 64, 64)
    # Realisations within a stack are drawn from one RNG, so they differ from each other.
    assert not _identical(a.image[0], a.image[1])


def test_disk_signal_is_deterministic_without_a_seed():
    kwargs = dict(size=64, radius_mm=1.0, contrast=10.0, spacing=0.1)
    a = make_disk_signal(**kwargs)
    b = make_disk_signal(**kwargs)
    assert _identical(a.image, b.image)
    assert a.seed is None


def test_phantoms_are_float32():
    assert make_edge_phantom(32, angle_deg=5.0).image.dtype == np.float32
    assert make_uniform_phantom(32, noise_sd=1.0, seed=0).image.dtype == np.float32
    assert make_disk_signal(32, 0.5, 10.0, 0.1).image.dtype == np.float32


def test_estimators_are_deterministic_end_to_end():
    """The measured MTF and NPS are themselves reproducible bit-for-bit from the seed."""
    edge = make_edge_phantom(
        256, spacing=0.1, contrast=1000.0, angle_deg=5.0,
        blur_sigma_mm=0.25, noise_sd=5.0, seed=2024,
    )
    edge_again = make_edge_phantom(
        256, spacing=0.1, contrast=1000.0, angle_deg=5.0,
        blur_sigma_mm=0.25, noise_sd=5.0, seed=2024,
    )
    m1 = mtf_from_edge(edge.image, edge.spacing)
    m2 = mtf_from_edge(edge_again.image, edge_again.spacing)
    assert _identical(m1.mtf, m2.mtf)
    assert _identical(m1.frequency, m2.frequency)
    assert m1.angle_deg == m2.angle_deg

    noise = make_uniform_phantom(64, noise_sd=20.0, seed=2024, n_realizations=8)
    noise_again = make_uniform_phantom(64, noise_sd=20.0, seed=2024, n_realizations=8)
    n1 = nps_2d(noise.image, noise.spacing)
    n2 = nps_2d(noise_again.image, noise_again.spacing)
    assert _identical(n1.nps, n2.nps)
    assert _identical(n1.nps_radial, n2.nps_radial)
    assert n1.variance == n2.variance


def test_no_phantom_or_estimate_contains_nan():
    """Silent NaN is the failure mode this project most needs to not have."""
    edge = make_edge_phantom(
        128, angle_deg=5.0, blur_sigma_mm=0.25, contrast=1000.0, noise_sd=5.0, seed=3
    )
    noise = make_uniform_phantom(64, noise_sd=10.0, seed=3, n_realizations=4)
    disk = make_disk_signal(64, 1.0, 10.0, 0.1, edge_sigma_mm=0.1)
    for ph in (edge, noise, disk):
        assert np.all(np.isfinite(ph.image))

    m = mtf_from_edge(edge.image, edge.spacing, angle_deg=5.0)
    assert np.all(np.isfinite(m.mtf))
    assert np.all(np.isfinite(m.esf))
    assert np.all(np.isfinite(m.lsf))

    n = nps_2d(noise.image, noise.spacing)
    assert np.all(np.isfinite(n.nps))
    assert np.all(np.isfinite(n.nps_radial))
    assert np.isfinite(n.variance) and np.isfinite(n.integral)


def test_seed_zero_is_a_real_seed_not_a_missing_one():
    """seed=0 is falsy in Python; make sure it is not treated as 'no seed given'."""
    a = make_uniform_phantom(32, noise_sd=5.0, seed=0)
    b = make_uniform_phantom(32, noise_sd=5.0, seed=0)
    assert _identical(a.image, b.image)
    assert a.seed == 0
    with pytest.raises(ValueError, match="requires an explicit seed"):
        make_uniform_phantom(32, noise_sd=5.0, seed=None)
