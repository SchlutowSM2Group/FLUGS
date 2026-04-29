"""Data manipulation helpers used by plotting functions."""

import numpy as np


def compute_symmetric_vminmax(data):
    """Compute symmetric vmin/vmax for diverging colormaps.

    Parameters
    ----------
    data : array-like
        Numeric data.

    Returns
    -------
    vmin, vmax : float
        Symmetric limits around zero.
    """
    absmax = np.nanmax(np.abs(data))
    return -absmax, absmax


def apply_boundary_mask(field, boundary_mask):
    """Apply boundary mask to field (sets boundary cells to NaN).

    Parameters
    ----------
    field : ndarray
        2D numpy array.
    boundary_mask : ndarray
        2D boolean/int array (1 = boundary).

    Returns
    -------
    field_masked : ndarray
        Copy with NaN at boundaries.
    """
    field_masked = field.copy()
    field_masked[boundary_mask == 1] = np.nan
    return field_masked


def get_flux_columns(df):
    """Extract flux column names from dataframe.

    Parameters
    ----------
    df : DataFrame

    Returns
    -------
    list of str
        Column names starting with 'flux_lc'.
    """
    return [col for col in df.columns if col.startswith("flux_lc")]
