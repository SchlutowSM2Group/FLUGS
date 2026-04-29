import numpy as np
import pandas as pd
from datetime import datetime

from bldfm.pbl_model import vertical_profiles
from bldfm.solver import steady_state_transport_solver

from .response_functions import ERF

from ..prepare import initialise_grid, initialise_land_cover_by_group
from .config_loader import load_config


def generate(config):
    np.random.seed(config.random_seed)
    run_config = load_config(config.run_name, config.run_name)
    grid = initialise_grid(run_config)
    _, masks = initialise_land_cover_by_group(run_config, grid)

    ny, nx = grid.ny, grid.nx
    I_gtyp = len(masks)
    meas_pt = (
        grid.grid_src_col * run_config.landcover.dx,
        grid.grid_src_row * run_config.landcover.dy,
    )
    domain = (grid.xmx, grid.ymx)
    modes = run_config.footprint_model.modes

    # initialize empty list for results
    dlist = []

    # create array of datetimes
    start_datetime = datetime.strptime(run_config.dataset.start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(run_config.dataset.end_date, "%Y-%m-%d")
    datetimes = pd.date_range(start=start_datetime, end=end_datetime, freq=config.freq)

    for now in datetimes:

        # hour of the day with minutes
        hour = (now.day - 1) * 24 + now.hour + now.minute / 60.0

        # diurnal cycle with noise
        PAR = -config.PARmax * np.cos(np.pi / 12.0 * hour)  # in mumol m-1 m-2
        PAR = np.where(PAR > 0, PAR, 0.0)
        Ts = (
            config.Tamp * np.sin(np.pi / 24.0 * (hour - 2.0)) ** 4 + 5.0
        )  # + 7.0 * hour / 24.0

        # add noise to driver
        PAR += np.random.normal(0.0, config.noise_amplitude * config.PARmax)
        PAR = np.where(PAR > 0, PAR, 0.0)
        Ts += np.random.normal(0.0, config.noise_amplitude * config.Tamp)

        # compute per-class surface fluxes and aggregate
        srf_flx_per_class = [ERF(PAR, Ts, c) for c in range(I_gtyp)]
        srf_flx = sum(masks[c] * srf_flx_per_class[c] for c in range(I_gtyp))

        # wind up to 5 m/s from all directions
        u = 5.0 * 2.0 * (np.random.rand() - 0.5)
        v = 5.0 * 2.0 * (np.random.rand() - 0.5)

        wind = u, v

        # assume neutrally stratified PBL
        z, profs = vertical_profiles(
            run_config.footprint_model.nz,
            run_config.dataset.zm,
            wind,
            ustar=config.ustar,
        )

        _, _, flx = steady_state_transport_solver(
            srf_flx,
            z,
            profs,
            domain,
            run_config.footprint_model.nz,
            meas_pt=meas_pt,
            modes=modes,
        )

        # measurement
        flx_m = flx[ny // 2, nx // 2]

        # add normally distributed noise to measurement
        flx_m += np.random.normal(0.0, config.noise_amp * abs(flx_m))

        # Extract date in yyyy-mm-dd format
        date = now.strftime("%Y-%m-%d")

        # Extract time in HH:MM format
        time = now.strftime("%H:%M")

        # wind to polar coordinates
        u_rot = np.sqrt(u**2 + v**2)
        wind_dir = np.arctan2(u, v)
        wind_dir = np.rad2deg(wind_dir) + 180

        drow = {
            "date": date,
            "time": time,
            "PAR": PAR,
            "Ts": Ts,
            "u": u,
            "v": v,
            "u_rot": u_rot,
            "wind_dir": wind_dir,
            "u*": config.ustar,
            "NEE": flx_m,
            "qc_flx": config.qc_flx,
        }
        for c in range(I_gtyp):
            drow[f"srf_flx{c}"] = srf_flx_per_class[c]

        dlist.append(drow)

    df = pd.DataFrame.from_dict(dlist)

    # Build units row dynamically
    units_dict = {
        "date": "[yyyy-mm-dd]",
        "time": "[HH:MM]",
        "PAR": "mumolm-2s-1",
        "Ts": "degC",
        "u": "[ms-1]",
        "v": "[ms-1]",
        "u_rot": "[ms-1]",
        "wind_dir": "[deg_from_north]",
        "u*": "[ms-1]",
        "NEE": "mugm-2s-1",
        "qc_flx": "",
    }
    for c in range(I_gtyp):
        units_dict[f"srf_flx{c}"] = "mugm-2s-1"

    units = pd.DataFrame({k: [v] for k, v in units_dict.items()})

    # Concatenate units row with data
    df_units = pd.concat([units, df], ignore_index=True)

    # Write Biomet file
    df_units.to_csv(
        run_config.dataset.bm_path, columns=["date", "time", "PAR", "Ts"], index=False
    )

    # Write full_output file
    srf_flx_cols = [f"srf_flx{c}" for c in range(I_gtyp)]
    full_output_cols = [
        "date",
        "time",
        "u",
        "v",
        "u_rot",
        "wind_dir",
        "u*",
        "NEE",
        "qc_flx",
    ] + srf_flx_cols

    num_columns = len(df.columns)
    empty_row = ",".join([""] * num_columns) + "\n"

    with open(run_config.dataset.csv_path, "w") as f:
        f.write(empty_row)

    df_units.to_csv(
        run_config.dataset.csv_path,
        columns=full_output_cols,
        mode="a",
        index=False,
    )
