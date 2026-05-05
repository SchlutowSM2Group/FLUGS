# Changelog

## v1.0.0 (2026-05-04)

Initial public release. Reproduction package for the FLUGS submeso
flux-inversion manuscript.

### Highlights

- Reproduces the **synth** experiment (synthetic data, two land-cover classes).
- Reproduces the **cherskii** experiment (EddyPro towers 1 and 2, CO₂ and sensible heat).
- Self-contained: depends only on BLDFM and standard scientific Python.
- Released under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0); commercial use requires a separate licence.
- CI builds the Sphinx docs and deploys them to GitHub Pages on every push to `main`.
- Inversion uses the Visick (2000) eigendecomposition of the weighted kernel
  (``[K ⊙ (W W^T) + λI] α = y``) — see ``flugs.inversion.run_optimizer_eig``.
- LCM is produced in canonical ``(ny, nx)`` layout (row 0 = south, col 0 = west)
  matching ``imshow(origin='lower')`` and BLDFM's internal convention.
