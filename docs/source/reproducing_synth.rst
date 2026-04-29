Reproducing the synth experiment
================================

Goal
----

The synth experiment generates a one-day synthetic dataset over a 256×256
domain with two land-cover classes (grass-like and shrub/tree-like). Drivers
``PAR`` and ``Ts`` are fed through prescribed Runkle environmental-response
functions to produce ground-truth surface fluxes; BLDFM is then run forward
to produce a synthetic tower observation. FLUGS inverts that observation and
the residuals between the inverted ERFs and the prescribed ERFs are the
manuscript figure.

Steps
-----

1. **(Optional) Regenerate the input CSVs.** The compiled
   ``data/sample_synth_full_output.csv`` and ``data/sample_synth_biomet.csv``
   are shipped, but you can regenerate them with:

   .. code-block:: bash

      $ python runs/generate_synth_data.py

   Configuration in ``yaml_configs/generate_synth_data.yml``.

2. **Solve the inversion.**

   .. code-block:: bash

      $ python -m flugs -c synth

   Reads ``yaml_configs/synth.yml``. Writes:

   - ``outputs/synth_<timestamp>/synth_flugs.csv``
   - ``outputs/synth_<timestamp>/metadata.json``
   - ``outputs/synth_<timestamp>/run.log``
   - ``outputs/synth_latest`` symlink

3. **Render the figures.**

   .. code-block:: bash

      $ python runs/vis_synth.py

   Resolves the latest run via the ``synth_latest`` symlink. Writes:

   - ``stochastic_lcm.pdf``
   - ``timeseries_synth.pdf``
   - ``timeseries_fluxes_synth.pdf``
   - ``erf_synth.pdf``
   - ``flux_comparison_synth.pdf``

Configuration knobs (``yaml_configs/synth.yml``)
------------------------------------------------

- ``observation_variable`` — column name of the synthetic tower flux.
- ``driver_variables`` — drivers fed into the ERF (``PAR``, ``Ts``).
- ``land_cover_groups`` — index lists defining each group.
- ``regularization_parameter`` — KRR ridge.
- ``kernel_type`` — ``rbf`` (default), ``polynomial``, or ``linear``.
