<p align="center">
  <a href="https://github.com/SchlutowSM2Group/FLUGS">
  <img alt="FLUGS Logo" src="docs/source/_static/logo.png" width=150px>
  </a>
</p>

<h2 align="center">FLUGS — Submeso Flux Inversion</h2>

<p align="center">
<a href="https://schlutowsm2group.github.io/FLUGS/">
<img alt="Documentation" src="https://img.shields.io/badge/docs-online-green?logo=github">
</a>
<a href="https://polyformproject.org/licenses/noncommercial/1.0.0">
<img alt="License: PolyForm Noncommercial 1.0.0" src="https://img.shields.io/badge/License-PolyForm%20NC%201.0.0-blue.svg">
</a>
<a href="https://github.com/psf/black">
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
</a>
</p>

FLUGS reproduces the **synth** (synthetic, two land-cover classes) and
**cherskii** (EddyPro tower data, two towers × two observables) experiments
from the submeso flux-inversion manuscript end-to-end.

The package wraps the Boundary Layer Dispersion and Footprint Model ([BLDFM](https://github.com/SchlutowSM2Group/BLDFM)) and adds:

- a kernel-ridge inversion that maps tower flux observations to per-land-cover-group response functions;
- per-timestep footprint caching (hash-keyed, on disk);
- plotting utilities for environmental response functions, timeseries, and spatial fields;
- a synthetic-data generator with prescribed Runkle response functions.

## Requirements

```
python  >= 3.10
bldfm   (pinned to git+https://github.com/SchlutowSM2Group/BLDFM.git@0728e41)
matplotlib, numpy, pandas, scipy, pyyaml, scikit-learn, tomli
```

`bldfm` is installed automatically by `pip install .`; you do not need to
clone it separately.

## Install

```console
git clone https://github.com/SchlutowSM2Group/FLUGS.git
cd FLUGS
pip install -e .
```

FLUGS resolves `data/`, `yaml_configs/`, `outputs/`, `cache/`, and `logs/`
relative to the cloned repository by default. To redirect any of them, set the
matching environment variable (`FLUGS_DATA_DIR`, `FLUGS_CONFIG_DIR`,
`FLUGS_OUTPUT_DIR`, `FLUGS_CACHE_DIR`, `FLUGS_LOG_DIR`).

## Reproduce the synth experiment

Run from the repository root:

```console
# (re)generate the synthetic CSVs (already shipped in data/, this overwrites them)
python runs/generate_synth_data.py

# solve the inversion
python -m flugs -c synth                     # → outputs/synth_<timestamp>/synth_flugs.csv

# render the figures
python runs/vis_synth.py                     # → outputs/synth_<timestamp>/plots/*.pdf
```

Expected figures: `stochastic_lcm.pdf`, `timeseries_synth.pdf`,
`timeseries_fluxes_synth.pdf`, `erf_synth.pdf`, `flux_comparison_synth.pdf`.

## Reproduce the cherskii experiment

The compressed EddyPro CSVs and land-cover map are shipped under `data/`. Run
each of the four configurations, then visualize:

```console
for cfg in co2_cherskii_twr1 co2_cherskii_twr2 shf_cherskii_twr1 shf_cherskii_twr2; do
    python -m flugs -c $cfg
done

python runs/vis_cherskii.py -c co2_cherskii_twr1
python runs/vis_cherskii.py -c shf_cherskii_twr1
```

Each `vis_cherskii.py` invocation pairs the two towers for the same observable
(`co2_flux` or `H`) and writes the manuscript's land-cover, driver, ERF, and
flux-comparison panels to `outputs/<config>_<timestamp>/plots/`.

The first cherskii run is slow (footprint computation per timestep). Subsequent
runs reuse `cache/footprints_<hash>.npy` and complete in seconds.

## Repository layout

```
FLUGS/
├── data/                   # Cherskii EddyPro CSVs, land-cover maps, synth reference
├── yaml_configs/           # 7 YAML configs (defaults + synth + 4 cherskii + synth-gen)
├── runs/                   # generate_synth_data, run_flugs, vis_synth, vis_cherskii
├── src/flugs/
│   ├── config.py               # path resolution (env vars + project-root defaults)
│   ├── prepare.py              # data loading, grid, land-cover masks
│   ├── footprint_interface.py  # BLDFM caller with on-disk cache
│   ├── inversion.py            # weight matrix, kernel matrix, eigendecomposition solver
│   ├── run.py                  # pipeline orchestrator
│   ├── plotting/               # StyleManager, LabelManager, TimeSeries/Response/SpatialPlotter
│   └── utils/                  # io, diagnostics, response_functions, data_classes, …
└── docs/                   # Sphinx documentation source
```

## Citation

```bibtex
@article{flugs,
  author = {Schlutow, Mark and Chew, Ray and Göckede, Mathias},
  title  = {Spatial decomposition of eddy covariance fluxes: the FLUGS framework},
  year   = {2026},
  doi    = {https://doi.org/10.22541/au.176800032.22523770/v2}
}
```

## License

FLUGS is released under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
Use by individuals, charitable organisations, educational institutions, public
research organisations, and government institutions is permitted; commercial
use requires a separate licence from the authors. See [`LICENSE.md`](LICENSE.md)
for the full text.
