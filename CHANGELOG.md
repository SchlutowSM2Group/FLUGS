# Changelog

## v1.0.1 (Unreleased)

### Added

- **License.** FLUGS is now released under the [PolyForm Noncommercial
  License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0);
  see `LICENSE.md`. Noncommercial use (research, education, government,
  public-benefit organisations) is permitted; commercial use requires a
  separate licence.

### Fixed

- **LCM orientation bug for non-square grids.** The legacy loader applied
  `[::-1].T` to the LCM and stored it in `(nx, ny)` layout, then passed
  it to BLDFM's solver, which internally does `ny, nx = q0.shape`. For a
  non-square grid like Cherskii (554×670), this caused BLDFM to compute
  its internal `dx` from the long extent / short axis count and `dy`
  vice versa — a ~21% / -17% distortion of the grid spacing. Footprints
  were therefore stretched along x and squashed along y. The synth
  experiment was unaffected because the grid is square (256×256), so
  `xmx=ymx` and `dx=dy` regardless of the convention swap.
- **Effect on cherskii results:** R² for tower 2 jumps significantly
  with the fix while tower 1 is largely unchanged (tower 2's wind /
  footprint configuration was much more sensitive to the BLDFM dx/dy
  distortion than tower 1's):

  | Run | Pre-fix R² | Post-fix R² |
  |---|---|---|
  | co2_cherskii_twr1 | 0.850 | 0.852 |
  | co2_cherskii_twr2 | **0.421** | **0.887** |
  | shf_cherskii_twr1 | 0.931 | 0.939 |
  | shf_cherskii_twr2 | **0.612** | **0.925** |

### Changed

- `flugs.prepare` now produces the LCM in the canonical `(ny, nx)`
  layout (row 0 = south, col 0 = west) that matches both
  `imshow(origin='lower')` and the convention BLDFM internally uses.
  Internal change; YAML configs unchanged. Manuscript figures
  regenerated to reflect the corrected physics.
- `runs/vis_cherskii.py` and `runs/vis_synth.py`: dropped the legacy
  `.T` compensations that paired with the old `(nx, ny)` LCM layout —
  with the new layout, the by-group LCM and full LCM align without the
  transpose.

## v1.0.0 (2026-04-29)

Initial public release. Frozen reproduction package for the FLUGS submeso
flux-inversion manuscript.

- Reproduces the **synth** experiment (synthetic data, two land-cover classes).
- Reproduces the **cherskii** experiment (EddyPro towers 1 and 2, CO₂ and sensible heat).
- Self-contained: depends only on BLDFM and standard scientific Python.
- Minimal CI (black formatting, install smoke, Sphinx docs build); no test
  suite — frozen Zenodo-style artifact.
