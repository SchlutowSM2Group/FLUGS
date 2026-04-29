import os
import numpy as np
from pathlib import Path
import logging

# import BLDFM
from bldfm import config
from bldfm.utils import compute_wind_fields, point_measurement
from bldfm.pbl_model import vertical_profiles
from bldfm.solver import steady_state_transport_solver

from .utils.array_utils import get_df_col
from .utils.data_classes import SimData, RunConfig
from .config import CACHE_DIR

config.NUM_THREADS = min(16, os.cpu_count() or 1)


def get_footprints(
    run_config: RunConfig, sim_data: SimData
) -> tuple[np.ndarray, np.ndarray]:
    """Compute or load cached footprints.

    Returns
    -------
    footprints : ndarray, shape (N, ny, nx)
    success_mask : boolean ndarray, shape (N,)
        True for timesteps where the footprint was computed successfully.
    """

    df = sim_data.measurement_data
    grid = sim_data.grid
    N = sim_data.N

    u_rot = get_df_col(df, "u_rot")
    wind_dir = get_df_col(df, "wind_dir")
    ustar = get_df_col(df, "u*")

    try:
        mol = get_df_col(df, "L")
    except Exception:
        mol = [1e9] * N

    meas_pt = (
        grid.grid_src_col * run_config.landcover.dx,
        grid.grid_src_row * run_config.landcover.dy,
    )
    meas_height = run_config.dataset.zm
    domain = (grid.xmx, grid.ymx)
    modes = run_config.footprint_model.modes

    # checksum of all parameters that define a footprint
    checksum = (
        np.sum(u_rot + wind_dir + ustar + mol + meas_height)
        + sum(domain)
        + sum(meas_pt)
        + sum(modes)
    )

    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    footprints_fn = f"{CACHE_DIR}/footprints_{hash(checksum)}.npy"
    success_fn = f"{CACHE_DIR}/fp_success_{hash(checksum)}.npy"

    try:

        # check if footprints were already computed and saved
        footprints = np.load(footprints_fn)
        try:
            success_mask = np.load(success_fn)
        except FileNotFoundError:
            # legacy cache without mask — assume all succeeded
            success_mask = np.ones(footprints.shape[0], dtype=bool)

    except Exception:

        # compute footprints and save them with hash of checksum
        footprints = np.zeros((N,) + grid.curr.shape)
        success_mask = np.ones(N, dtype=bool)

        # wind as cartesian vector
        um, vm = compute_wind_fields(u_rot, wind_dir)

        for n in range(N):

            try:

                z, profiles = vertical_profiles(
                    n=run_config.footprint_model.nz,
                    meas_height=meas_height,
                    wind=(um[n], vm[n]),
                    ustar=ustar[n],
                    # z0=0.16,
                    mol=mol[n],
                )

                _, _, footprints[n, ...] = steady_state_transport_solver(
                    srf_flx=np.zeros_like(grid.curr),
                    z=z,
                    profiles=profiles,
                    domain=domain,
                    levels=run_config.footprint_model.nz,
                    meas_pt=meas_pt,
                    modes=modes,
                    footprint=True,
                )
            except Exception as e:

                logging.info(
                    f"Computation of footprint {n} failed ({e}). Marking as excluded."
                )
                success_mask[n] = False

        np.save(footprints_fn, footprints)
        np.save(success_fn, success_mask)

    return footprints, success_mask


point_measurement = point_measurement
