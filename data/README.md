# Data

This directory contains sample and observational datasets used by FLUGS.

## Synthetic data

- `sample_synth_full_output.csv` — Synthetic flux output (97 rows), generated
  by `runs/generate_synth_data.py`.
- `sample_synth_biomet.csv` — Synthetic biomet data (companion to above).

## Cherskii observational data

Compressed EddyPro output for the two Cherskii eddy-covariance towers
covering the manuscript's analysis window:

- `eddypro_cherskii_tower1_full_output_compressed.csv`
- `eddypro_cherskii_tower1_biomet_compressed.csv`
- `eddypro_cherskii_tower2_full_output_compressed.csv`
- `eddypro_cherskii_tower2_biomet_compressed.csv`

## Land cover

- `sample_land_cover_IDs_2000mx2000m_256x256_0100.dat` — Synthetic land-cover
  ID map (256x256 grid).
- `cherskii_land_cover.txt` — Cherskii land-cover classification.

## Metadata

- `variables_metadata.toml` — Variable display names and units, used by
  `flugs.plotting.labels.LabelManager`.
