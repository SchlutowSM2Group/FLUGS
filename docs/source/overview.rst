Package Overview
================

FLUGS is organised as a package under ``src/flugs/`` with four top-level
run scripts under ``runs/`` (``generate_synth_data.py``, ``run_flugs.py``,
``vis_synth.py``, ``vis_cherskii.py``).

Pipeline
--------

The orchestrator :func:`flugs.run.main` (invoked via ``python -m flugs``) runs
the following per timestep with valid eddy-covariance observations:

1. **Footprint** — :func:`flugs.footprint_interface.get_footprints` calls
   BLDFM to compute the per-timestep footprint sensitivity field. Results are
   hash-cached on disk so repeated runs with the same meteorology are fast.
2. **Weight matrix** — :func:`flugs.inversion.compute_weight_matrix` convolves
   each footprint with each land-cover-group binary mask, yielding ``W`` of
   shape ``(N, I_gtyp)``.
3. **Kernel matrix** — :func:`flugs.inversion.generate_kernel_matrix` builds
   the ``N × N`` driver kernel matrix ``K`` (linear / polynomial / RBF).
4. **Eigendecomposition solver** — :func:`flugs.inversion.run_optimizer_eig`
   solves the weighted-kernel ridge regression problem
   ``[K ⊙ (W W^T) + λI] α = y`` via the symmetric eigendecomposition
   ``K_w = V Λ V^T`` (Visick 2000), giving
   ``α = V (Λ + λI)^{-1} V^T y``.
5. **Output** — per-land-cover-group scaling factors are stacked with
   timestamps and driver values and saved to
   ``outputs/<run>_<timestamp>/<run>_flugs.csv``.

Subpackages
-----------

``flugs.utils``
    Data-classes for run configuration, EddyPro CSV I/O, statistical
    diagnostics, environmental response functions
    (:mod:`flugs.utils.response_functions`), and the synthetic-data generator.

``flugs.plotting``
    Style and label managers plus three plotters used by
    ``runs/vis_synth.py`` and ``runs/vis_cherskii.py``:

    - :class:`~flugs.plotting.TimeSeriesPlotter`
    - :class:`~flugs.plotting.ResponsePlotter`
    - :class:`~flugs.plotting.SpatialPlotter`

Configuration
-------------

Runs are configured through YAML files in ``yaml_configs/``. ``defaults.yml``
provides the base; individual experiments override it via ``deep_merge``
(see :mod:`flugs.utils.config_loader`).

Path resolution (``DATA_DIR``, ``OUTPUT_DIR``, etc.) layers in this order:

1. Environment variables ``FLUGS_DATA_DIR`` / ``FLUGS_CONFIG_DIR`` / ….
2. Defaults relative to the project root (``./data/``, ``./yaml_configs/``,
   ``./outputs/``, ``./cache/``, ``./logs/``).
