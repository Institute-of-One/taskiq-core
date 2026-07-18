"""taskiq_core — task-based image quality on synthetic phantoms.

Measure physical image quality (MTF, NPS, NEQ) and task performance (model-observer
``d'`` / AUC) on the *same* synthetic images, through the same pipeline, so that the
transfer from physical metrics to task performance can be quantified as acquisition
conditions are swept.

Everything is synthetic and analytic. No DICOM, no patient data, no deep learning; the
runtime dependencies are numpy / scipy / scikit-image / matplotlib. Generators take a
``seed`` and are bit-reproducible. Where a closed-form answer exists — the MTF of a
Gaussian-blurred edge, the NPS of white noise — the estimator is validated against it in
the test suite rather than against itself.

Modules
-------
``phantoms``   synthetic images: slanted edge (MTF), uniform + noise (NPS), disk (task)
``physical``   MTF from a slanted edge; 2-D and radial NPS
``tasks``      SKE/BKE trial generation; d', AUC, ROC, 2AFC
``observers``  model observers: NPWE, the ideal linear (prewhitening) observer, and CHO
``atlas``      NEQ, condition sweeps, and the physical-to-task regression
"""

from __future__ import annotations

from taskiq_core.atlas import (
    AtlasConfig,
    AtlasTable,
    NEQResult,
    RegressionResult,
    fit_transfer,
    neq,
    sweep,
)
from taskiq_core.observers import (
    CHOResult,
    ObserverResult,
    auc_from_scores,
    burgess_eye_filter,
    cho,
    d_prime_from_scores,
    dense_dog_channels,
    gabor_channels,
    ideal_linear,
    laguerre_gauss_channels,
    npwe,
    score_images,
)
from taskiq_core.phantoms import (
    Phantom,
    make_disk_signal,
    make_edge_phantom,
    make_uniform_phantom,
)
from taskiq_core.physical import (
    MTFResult,
    NPSResult,
    estimate_edge_angle,
    gaussian_mtf,
    mtf_from_edge,
    nps_2d,
)
from taskiq_core.tasks import (
    ROCResult,
    TrialSet,
    d_prime_from_pc,
    pc_from_d_prime,
    roc_curve,
    ske_bke_trials,
    two_afc,
)

__version__ = "0.4.0"

__all__ = [
    "__version__",
    # phantoms
    "Phantom",
    "make_edge_phantom",
    "make_uniform_phantom",
    "make_disk_signal",
    # physical
    "MTFResult",
    "NPSResult",
    "mtf_from_edge",
    "nps_2d",
    "estimate_edge_angle",
    "gaussian_mtf",
    # observers
    "ObserverResult",
    "CHOResult",
    "npwe",
    "ideal_linear",
    "cho",
    "burgess_eye_filter",
    "score_images",
    "d_prime_from_scores",
    "auc_from_scores",
    "laguerre_gauss_channels",
    "dense_dog_channels",
    "gabor_channels",
    # tasks
    "TrialSet",
    "ROCResult",
    "ske_bke_trials",
    "roc_curve",
    "two_afc",
    "pc_from_d_prime",
    "d_prime_from_pc",
    # atlas
    "NEQResult",
    "AtlasConfig",
    "AtlasTable",
    "RegressionResult",
    "neq",
    "sweep",
    "fit_transfer",
]
