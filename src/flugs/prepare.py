# import libraries
from dataclasses import dataclass
import logging
from pathlib import Path
import numpy as np

from .utils.io import (
    load_data,
    filter_data,
    merge_dfs,
    split_headers,
    clean_and_validate_headers,
)

# import classes and functions
from .config import OUTPUT_DIR

from .utils.config_loader import load_config
from .utils.data_classes import GridParams, RunConfig, SimData


def get_data(config=None, run_name=None, run_dir=None):
    """
    Load FLUGS configuration and simulation data.

    Parameters
    ----------
    config : str, optional
        Config file name (without extension). If None, uses argparse.
    run_name : str, optional
        Run name for outputs. If None, defaults to config name.
    run_dir : str, optional
        Run output directory. When provided, diagnostic masks are saved
        there instead of the flat OUTPUT_DIR.

    Returns
    -------
    run_config, sim_data
        Configuration and simulation data objects.
    """
    from argparse import ArgumentParser

    # If arguments not provided, parse from command line
    if config is None:
        parser = ArgumentParser()
        parser.add_argument("-c", "--config", type=str, default="defaults")
        parser.add_argument("-r", "--run_name", type=str, default=None)
        args = parser.parse_args()
        config = args.config
        run_name = args.run_name

    # If run_name is not provided, use the config name
    if run_name is None:
        run_name = config

    run_config = load_config(run_name, config)

    # Initialize the simulation data from the config parameters
    measurement_data = initialise_dataframe(run_config)
    grid_params = initialise_grid(run_config)
    land_cover_by_group, land_cover_mask_by_group = initialise_land_cover_by_group(
        run_config, grid_params, run_dir=run_dir
    )

    sim_data = SimData(
        grid=grid_params,
        land_cover_by_group=land_cover_by_group,
        land_cover_mask_by_group=land_cover_mask_by_group,
        measurement_data=measurement_data,
    )

    return run_config, sim_data


def initialise_dataframe(run_config: RunConfig):
    dataset = run_config.dataset
    diagnostics = run_config.diagnostics

    logging.info(f"z_m = {dataset.zm}, q_c = {dataset.qc_lvl}")

    # Combine vtk and vtk_bm headers
    all_headers = dataset.vtk + dataset.driver_variables

    # Split headers into those in the CSV and those in the biomet file
    headers_in_csv, headers_in_bm = split_headers(
        dataset.csv_path, dataset.bm_path, all_headers
    )
    headers_in_csv, headers_in_bm = clean_and_validate_headers(
        dataset.csv_path, dataset.bm_path, headers_in_csv, headers_in_bm
    )

    # Load data from csv_path and store into a dataframe
    if headers_in_csv:
        measurement_data = load_data(dataset.csv_path, variables_to_keep=headers_in_csv)
    else:
        measurement_data = None  # No relevant headers in csv_path

    # Load data from bm_path and store into a dataframe
    if headers_in_bm:
        bm_measurement_data = load_data(
            dataset.bm_path, variables_to_keep=headers_in_bm, read_categories=False
        )
    else:
        bm_measurement_data = None  # No relevant headers in bm_path

    # Optionally merge the dataframes if needed
    if measurement_data is not None and bm_measurement_data is not None:
        measurement_data = merge_dfs(
            measurement_data, bm_measurement_data, new_header="biomet"
        )
    elif measurement_data is not None:
        pass
    else:
        measurement_data = bm_measurement_data

    assert (
        measurement_data is not None
    ), "No data loaded. Please check the provided file paths and headers."

    measurement_data = filter_data(
        measurement_data,
        {run_config.filter_var: ["lt", dataset.qc_lvl]},
        obs_var=run_config.obs_var,
    )
    measurement_data = filter_data(
        measurement_data,
        {"date": [["le", dataset.end_date], ["ge", dataset.start_date]]},
    )

    if diagnostics.sample_size > 0:
        measurement_data = measurement_data.sample(n=diagnostics.sample_size)

    measurement_data = measurement_data.reset_index(drop=True)

    logging.info(f"(data points , cols) : {measurement_data.shape}")

    # TODO: update dataclass with measurement_data

    return measurement_data


def _debug_plot(arr, grid_params, run_config, title="", marker_loc=None):
    """Save a quick diagnostic plot using SpatialPlotter."""
    import matplotlib.pyplot as plt
    from .plotting.spatial import SpatialPlotter

    plotter = SpatialPlotter()
    fig, ax = plotter.plot_field2d(
        arr,
        xmx=grid_params.xmx,
        ymx=grid_params.ymx,
        lon_ext=run_config.dataset.longitude_extent,
        lat_ext=run_config.dataset.latitude_extent,
        title=title,
        zm=0.0,
        marker_loc=marker_loc,
    )
    fig.savefig(f"plots/{title}.png")
    plt.close(fig)


def initialise_land_cover_by_group(
    run_config: RunConfig, grid_params: GridParams, run_dir=None
):
    """
    Preprocess and stack land cover maps for all groups.
    Saves the stacked maps to a file and returns the stacked data.

    When *run_dir* is provided, diagnostic masks are saved there instead
    of the flat OUTPUT_DIR.
    """
    mask_dir = str(run_dir) if run_dir is not None else OUTPUT_DIR

    meas_pt = grid_params.measurement_point
    pad_width = run_config.footprint_model.pad_width

    # Create stacked land cover arrays for all groups
    lc_stacked_by_grp = np.empty(
        (run_config.landcover.I_gtyp, grid_params.nx, grid_params.ny)
    )
    lc_stacked_by_grp[...] = np.nan

    lc_masks_by_grp = np.empty_like(lc_stacked_by_grp)

    for g_idx, grp in enumerate(run_config.landcover.lt_grp):
        for ltyp in grp:
            # Load and process this land type
            curr = _load_land_cover_in_grid_format(
                run_config.landcover.land_cover_fn, ltyp, pad_width
            )
            # Update stack
            lc_stacked_by_grp[g_idx, ...] = np.fmax(lc_stacked_by_grp[g_idx, ...], curr)

        lc_by_group_T = lc_stacked_by_grp[g_idx, ...].T

        if run_config.diagnostics.debug_plot_stacked_land_covers:
            _debug_plot(
                lc_by_group_T,
                grid_params,
                run_config,
                title=f"run_{run_config.run_name}_ltyp_grp_{g_idx}",
                marker_loc=meas_pt,
            )

    if run_config.diagnostics.debug_plot_stacked_land_covers:
        full_stack = np.nanmax(lc_stacked_by_grp, axis=0).T
        _debug_plot(
            full_stack,
            grid_params,
            run_config,
            title=f"run_{run_config.run_name}_full_stack",
            marker_loc=meas_pt,
        )

    if run_config.diagnostics.output_land_cover_mask:
        full_stack = np.nanmax(lc_stacked_by_grp, axis=0).T
        full_boundary_mask = np.where(np.isnan(full_stack), 1.0, 0.0)

        _debug_plot(
            full_boundary_mask,
            grid_params,
            run_config,
            title=f"run_{run_config.run_name}_full_boundary_mask",
        )
        Path(mask_dir).mkdir(parents=True, exist_ok=True)
        np.save(f"{mask_dir}/mask_boundary.npy", full_boundary_mask)

    lc_masks_by_grp[...] = np.where(
        ~np.isnan(lc_stacked_by_grp), 1.0, 0.0
    )  # 1 where landcover exists, 0 elsewhere

    for g_idx, grp in enumerate(run_config.landcover.lt_grp):
        if run_config.diagnostics.output_land_cover_mask:
            Path(mask_dir).mkdir(parents=True, exist_ok=True)
            np.save(f"{mask_dir}/mask_lc{g_idx}.npy", lc_masks_by_grp[g_idx, ...].T)

    return lc_stacked_by_grp, lc_masks_by_grp


def initialise_grid(run_config: RunConfig, ltyp: int = 0) -> GridParams:
    """Load domain and initialize grid parameters."""
    # Load and process domain
    pad_width = run_config.footprint_model.pad_width
    curr = _load_land_cover_in_grid_format(
        run_config.landcover.land_cover_fn, ltyp, pad_width
    )
    nx, ny = curr.shape

    # Calculate grid
    xmx = run_config.landcover.dx * (nx - 1)
    ymx = run_config.landcover.dy * (ny - 1)
    x = np.linspace(0, xmx, nx)
    y = np.linspace(0, ymx, ny)

    # Adjust tower location to match model grid
    grid_src_row = ny - (run_config.dataset.source_row + pad_width)
    grid_src_col = run_config.dataset.source_col + pad_width

    # Copy attributes from config to grid data class; store grid info
    return GridParams(
        nx, ny, xmx, ymx, x, y, grid_src_row, grid_src_col, pad_width, curr
    )


def _load_land_cover_in_grid_format(
    land_cover_fn: Path, ltyp: int, pad_width: int
) -> np.ndarray:
    """
    Load and process land cover data in grid format.

    Args:
        land_cover_fn: Path to land cover file
        ltyp: Land type to filter for
        pad_width: Padding width for the array

    Returns:
        Processed land cover array with grid orientation and padding
    """
    land_cover_data = load_data(land_cover_fn)
    curr = (
        land_cover_data.where(land_cover_data == ltyp)
        .to_numpy(dtype=float)[::-1, ...]
        .T
    )
    curr = np.pad(curr, pad_width, mode="constant", constant_values=np.nan)
    return curr
