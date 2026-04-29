"""I/O helpers for FLUGS.

Includes:

- EddyPro CSV loaders (``load_data``, ``filter_data``, ``merge_dfs``,
  ``split_headers``, ``clean_and_validate_headers``, ``save_data``).
- Filesystem utilities (``create_run_dir``, ``get_latest_run_dir``).
- Run-metadata writer (``save_metadata``) and dataclass-to-dict
  serialization (``config_to_dict``).
"""

import json
import operator
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# EddyPro CSV / generic tabular loaders
# ---------------------------------------------------------------------------


def load_dat(file_path: str) -> pd.DataFrame:
    """Load a space-separated ``.dat`` file as numeric DataFrame."""
    df = pd.read_csv(file_path, sep=" ", header=None, na_values="NA")
    return df.apply(pd.to_numeric, errors="coerce", downcast="integer")


def load_txt(file_path: str) -> pd.DataFrame:
    """Load a comma-separated ``.txt`` file as numeric DataFrame."""
    df = pd.read_csv(file_path, header=None, na_values="NA")
    return df.apply(pd.to_numeric, errors="coerce", downcast="integer")


def load_csv(
    input_fn: str,
    variables_to_keep: list,
    read_categories: bool = True,
    read_headers: bool = True,
    read_units: bool = True,
    header_names: list = ["categories", "headers", "units"],
) -> pd.DataFrame:
    """Load an EddyPro-style multi-header CSV.

    The first three rows are interpreted as ``(categories, headers, units)``
    and combined into a 3-level pandas ``MultiIndex`` on the columns.

    Parameters
    ----------
    input_fn : str
        Path to the CSV file.
    variables_to_keep : list of str
        Variable names (level-1 keys) to retain.
    read_categories, read_headers, read_units : bool
        Toggle each header row.
    header_names : list of str
        Names for the resulting column index levels.

    Returns
    -------
    pandas.DataFrame
        Frame restricted to *variables_to_keep* with a MultiIndex on columns.
    """
    nrows = 0
    indices = []
    names = []

    if read_categories:
        categories = pd.read_csv(input_fn, nrows=1, header=None).iloc[0]
        categories = pd.concat([categories, pd.Series([np.nan])])
        categories = pd.Series(categories).ffill()
        indices.append(categories)
        names.append(header_names[nrows])
        nrows += 1

    if read_headers:
        headers = pd.read_csv(input_fn, skiprows=nrows, nrows=1).columns
        indices.append(headers)
        names.append(header_names[nrows])
        nrows += 1

    if read_units:
        units = pd.read_csv(input_fn, skiprows=nrows, nrows=1, na_values="NA").columns
        indices.append(units)
        names.append(header_names[nrows])
        nrows += 1

    column_tuples = list(zip(*indices))
    multi_index = pd.MultiIndex.from_tuples(column_tuples, names=names)

    df = pd.read_csv(input_fn, skiprows=nrows, header=None, names=headers)
    df.columns = multi_index

    idx = pd.IndexSlice
    slice_tuple = (
        (slice(None),) * (df.columns.nlevels - 2)
        + (variables_to_keep,)
        + (slice(None),)
    )
    df = df.loc[:, idx[slice_tuple]].copy()
    df.columns = df.columns.remove_unused_levels()

    return df


def load_data(file_path, **kwargs):
    """Load a tabular file dispatched on extension (``.csv`` / ``.txt`` / ``.dat``)."""
    extension = str(file_path).split(".")[-1].lower()
    loaders = {"txt": load_txt, "dat": load_dat, "csv": load_csv}
    loader = loaders.get(extension)
    if loader is None:
        raise ValueError(f"Unsupported file type: {extension}")
    return loader(file_path, **kwargs)


def save_data(file_path: str, data: dict, columns: list):
    """Write a tabular CSV from ``data`` with the given column order."""
    df_out = pd.DataFrame(data, columns=columns)
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(file_path, index=False)


def filter_data(
    df: pd.DataFrame,
    filter_type: dict,
    obs_var: str = None,
) -> pd.DataFrame:
    """Filter a multi-index DataFrame by per-column operator comparisons.

    Parameters
    ----------
    df : pandas.DataFrame
        Input frame with a 3-level column MultiIndex.
    filter_type : dict
        Mapping ``column-name → [operator, value]``. Operators must be one of
        ``"lt"``, ``"le"``, ``"gt"``, ``"ge"``.
    obs_var : str, optional
        Observation variable; if given, rows with NaN/inf/-9999 in this column
        are dropped after the operator filtering.

    Returns
    -------
    pandas.DataFrame
        Filtered (and copied) frame.
    """
    allowed_operators = {"lt", "le", "gt", "ge"}
    op_map = {
        "lt": operator.lt,
        "le": operator.le,
        "gt": operator.gt,
        "ge": operator.ge,
    }

    mask = np.ones(len(df), dtype=bool)

    for key, values in filter_type.items():
        filter_cols = [(col[0], col[1], col[2]) for col in df.columns if col[1] == key]
        assert (
            len(filter_cols) > 0
        ), f"Filter variable '{key}' not found in dataframe columns."

        if not isinstance(values[0], list):
            values = [values]

        for value in values:
            filter_operator, filter_range = value
            assert (
                filter_operator in allowed_operators
            ), f"Invalid operator '{filter_operator}'. Allowed: {allowed_operators}"
            op = op_map[filter_operator]
            mask &= op(df[filter_cols[0]], filter_range)

    df = df[mask].copy()

    if obs_var is not None:
        obs_cols = [(col[0], col[1], col[2]) for col in df.columns if col[1] in obs_var]
        df.replace([np.inf, -np.inf, -9999], np.nan, inplace=True)
        df.dropna(subset=obs_cols, how="any", inplace=True)

    return df


def split_headers(csv_path, bm_path, headers):
    """Partition *headers* into those present in the main CSV vs the biomet sidecar."""
    csv_headers = pd.read_csv(csv_path, skiprows=1, nrows=1).columns.tolist()
    bm_headers = pd.read_csv(bm_path, nrows=1).columns.tolist()
    headers_in_csv = [h for h in headers if h in csv_headers]
    headers_in_bm = [h for h in headers if h in bm_headers]
    return headers_in_csv, headers_in_bm


def clean_and_validate_headers(csv_path, bm_path, headers_in_csv, headers_in_bm):
    """De-duplicate header lists and assert date/time alignment across sources."""
    headers_in_csv = list(set(headers_in_csv))
    headers_in_bm = list(set(headers_in_bm))

    common_time_cols = ["date", "time"]
    if all(c in headers_in_csv for c in common_time_cols) and all(
        c in headers_in_bm for c in common_time_cols
    ):
        csv_time = pd.read_csv(csv_path, skiprows=1, usecols=common_time_cols)
        bm_time = pd.read_csv(bm_path, skiprows=0, usecols=common_time_cols)
        assert csv_time.equals(
            bm_time
        ), "Date and time columns in csv_path and bm_path are not identical."
        headers_in_bm = [h for h in headers_in_bm if h not in common_time_cols]

    return headers_in_csv, headers_in_bm


def merge_dfs(
    df_1: pd.DataFrame,
    df_2: pd.DataFrame,
    new_header: str = "",
) -> pd.DataFrame:
    """Concatenate two multi-index DataFrames horizontally, adding a level to *df_2*."""
    existing_levels = df_2.columns.levels
    new_levels = [[new_header], existing_levels[0], existing_levels[1]]
    new_codes = [[0] * len(df_2.columns), *df_2.columns.codes]
    df_2.columns = pd.MultiIndex(levels=new_levels, codes=new_codes)
    return pd.concat([df_1, df_2], axis=1).copy()


# ---------------------------------------------------------------------------
# Filesystem utilities
# ---------------------------------------------------------------------------


def create_run_dir(output_dir, run_name: str) -> Path:
    """Create ``{output_dir}/{run_name}_{timestamp}/`` plus a ``_latest`` symlink."""
    output_dir = Path(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"{run_name}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "plots").mkdir(exist_ok=True)

    latest_link = output_dir / f"{run_name}_latest"
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(run_dir.name)

    return run_dir


def get_latest_run_dir(output_dir, run_name: str) -> Path:
    """Resolve the latest output directory for *run_name*.

    Tries the ``{run_name}_latest`` symlink first, then falls back to the
    most recently modified ``{run_name}_*`` directory.
    """
    output_dir = Path(output_dir)
    latest_link = output_dir / f"{run_name}_latest"
    if latest_link.is_symlink():
        return latest_link.resolve()

    candidates = sorted(
        output_dir.glob(f"{run_name}_[0-9]*"),
        key=lambda p: p.stat().st_mtime,
    )
    if candidates:
        return candidates[-1]
    raise FileNotFoundError(f"No output directory found for run '{run_name}'")


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def config_to_dict(obj):
    """Recursively convert a (possibly nested) dataclass to a plain dict.

    Skips private fields (starting with ``_``); summarizes ``ndarray`` and
    ``DataFrame`` objects by shape rather than dumping their contents.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in dataclass_fields(obj):
            if f.name.startswith("_"):
                continue
            result[f.name] = config_to_dict(getattr(obj, f.name))
        return result
    if isinstance(obj, np.ndarray):
        return f"ndarray(shape={obj.shape})"
    if isinstance(obj, pd.DataFrame):
        return f"DataFrame(shape={obj.shape})"
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (list, tuple)):
        return [config_to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: config_to_dict(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# Run-metadata writer
# ---------------------------------------------------------------------------


def save_metadata(
    run_dir, run_config, sim_data, statistics, cost_func, start_time, end_time
):
    """Save run metadata as JSON inside *run_dir*."""
    metadata = {
        "run_name": run_config.run_name,
        "timestamp": start_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "config": config_to_dict(run_config),
        "data_summary": {
            "n_measurements": int(sim_data.N),
            "n_land_cover_types": int(run_config.landcover.I_gtyp),
            "grid_shape": [int(sim_data.grid.nx), int(sim_data.grid.ny)],
            "driver_variables": list(run_config.dataset.driver_variables),
        },
        "statistics": {k: float(v) for k, v in statistics.items()},
        "cost_function": float(cost_func) if cost_func is not None else None,
    }
    with open(Path(run_dir) / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)
