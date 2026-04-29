Reproducing the cherskii experiment
===================================

Goal
----

The cherskii experiment runs FLUGS against real EddyPro tower data from the
Cherskii site (RU-Che / RU-Ch2) for two observables — CO₂ flux and sensible
heat flux — at two towers, one week of half-hourly data each.

Inputs (shipped under ``data/``)
--------------------------------

- ``eddypro_cherskii_tower1_full_output_compressed.csv`` and the matching
  ``..._biomet_compressed.csv``.
- ``eddypro_cherskii_tower2_full_output_compressed.csv`` and biomet sidecar.
- ``cherskii_land_cover.txt`` — raster land-cover map.
- ``variables_metadata.toml`` — variable name / unit / long-name table used
  by the plot label manager.

Steps
-----

1. **Run the four configurations.**

   .. code-block:: bash

      $ for cfg in co2_cherskii_twr1 co2_cherskii_twr2 \
                   shf_cherskii_twr1 shf_cherskii_twr2; do
            python -m flugs -c $cfg
        done

   Each writes ``outputs/<cfg>_<timestamp>/<cfg>_flugs.csv``,
   ``metadata.json``, ``run.log``, and refreshes the ``<cfg>_latest`` symlink.

   The first run for each tower-meteorology pair is slow (BLDFM footprint per
   timestep). Subsequent runs reuse ``cache/footprints_<hash>.npy`` and finish
   in seconds.

2. **Render the figures.**

   .. code-block:: bash

      $ python runs/vis_cherskii.py -c co2_cherskii_twr1   # → CO₂ panels
      $ python runs/vis_cherskii.py -c shf_cherskii_twr1   # → SHF panels

   Each invocation pairs the two towers for the same observable. Outputs:

   - ``cherskii_lcm.pdf`` — full + grouped land-cover map.
   - ``combined_drivers_comparison.pdf`` — driver timeseries grid.
   - ``<obs>_timeseries_fluxes_comparison.pdf`` — observed vs learned flux.
   - ``<obs>_erf_comparison_grid.pdf`` — ERF grid rows=drivers × cols=towers.
   - ``<obs>_flux_comparison_<lc>.pdf`` — per-land-cover flux comparison
     across the two towers.

Per-config differences
----------------------

The four YAML files differ only in ``observation_variable`` (``co2_flux`` vs
``H``), ``driver_variables`` (``[SWin_1_1_1, Ta_1_1_1]`` vs
``[Rn_1_1_1, Ta_1_1_1]``), and ``source_row`` / ``source_col`` (tower
location). All other parameters are inherited from ``defaults.yml``.
