"""Array operations used throughout FLUGS."""

import numpy as np

from .data_classes import RunConfig, SimData


def get_df_col(df, var, skip_rows=0):
    """Extract a column from a multi-index DataFrame by level-1 key.

    Returns a flattened 1-D numpy array.

    Parameters
    ----------
    df : pandas.DataFrame
        Frame with a 3-level column MultiIndex (categories / headers / units).
    var : str
        Name to look up on the second level (``headers``).
    skip_rows : int
        Number of leading rows to skip.
    """
    col = df.xs(var, axis=1, level=1, drop_level=True)
    return col[skip_rows:].to_numpy().flatten()


def prepare_output(
    result: np.ndarray, run_config: RunConfig, sim_data: SimData
) -> tuple[np.ndarray, list[str]]:
    """Stack the inversion result with timestamps, drivers and observations.

    Returns
    -------
    out_arr : ndarray
        Columns: ``[dt, tt, obs_var, *drivers, *flux_lc{i}]``.
    col_names : list of str
        Header strings matching the columns of *out_arr*.
    """
    measurement_data = sim_data.measurement_data

    tt = get_df_col(measurement_data, "time").reshape(-1, 1)
    dt = get_df_col(measurement_data, "date").reshape(-1, 1)
    N = len(measurement_data)
    P = len(run_config.dataset.driver_variables)
    drivers = np.zeros((N, P))
    for p, driver_var_name in enumerate(run_config.dataset.driver_variables):
        drivers[..., p] = get_df_col(measurement_data, driver_var_name)

    obs_var = get_df_col(measurement_data, run_config.obs_var).reshape(-1, 1)

    out_arr = np.hstack((dt, tt, obs_var, drivers, result))
    col_names = ["dt", "tt", run_config.obs_var]

    for p, driver_var_name in enumerate(run_config.dataset.driver_variables):
        col_names.append(driver_var_name)

    for i in range(run_config.landcover.I_gtyp):
        col_names.append(f"flux_lc{i}")

    return out_arr, col_names
