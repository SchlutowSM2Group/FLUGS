FLUGS — Submeso Flux Inversion
==============================

**FLUGS** reconstructs spatially-resolved surface fluxes from eddy-covariance
tower measurements by combining kernel ridge regression with atmospheric
footprints from `BLDFM <https://github.com/SchlutowSM2Group/BLDFM>`_.

This package reproduces the synth and cherskii experiments from the
manuscript end-to-end.

Key features
------------

- **Kernel Ridge Regression** with Kronecker-structured matrices and a
  conjugate-gradient solver.
- **BLDFM Integration** for steady-state footprint computation, with on-disk
  hash-keyed caching of per-timestep footprints.
- **YAML Configuration** for dataset paths, land-cover groups, regularisation,
  and diagnostics.
- **Synthetic Data Generator** with prescribed Runkle response functions for
  validation experiments.
- **Plotting** module for environmental response functions, time series, and
  spatial fields.

Reproducing the manuscript
--------------------------

1. **Install** (pulls BLDFM at the pinned pre-abl-tk commit ``0728e41``):

   .. code-block:: bash

      $ git clone https://github.com/SchlutowSM2Group/FLUGS.git
      $ cd FLUGS && pip install -e .

2. **Reproduce the synth experiment**:

   .. code-block:: bash

      $ python runs/generate_synth_data.py
      $ python -m flugs -c synth
      $ python runs/vis_synth.py

3. **Reproduce the cherskii experiment**:

   .. code-block:: bash

      $ for cfg in co2_cherskii_twr1 co2_cherskii_twr2 \
                   shf_cherskii_twr1 shf_cherskii_twr2; do
            python -m flugs -c $cfg
        done
      $ python runs/vis_cherskii.py -c co2_cherskii_twr1
      $ python runs/vis_cherskii.py -c shf_cherskii_twr1

About
-----

FLUGS is developed by Mark Schlutow, Ray Chew, and Mathias Göckede.

.. toctree::
   :maxdepth: 2
   :hidden:
   :includehidden:

   Home <self>
   overview
   reproducing_synth
   reproducing_cherskii
   API Reference <src>
   GitHub Repository <https://github.com/SchlutowSM2Group/FLUGS>

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :hidden:

   Glossary Index <genindex>
   Module Index <modindex>
