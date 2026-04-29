"""Statistical diagnostics for evaluating inversion residuals."""

import numpy as np


def get_statistics(model, obs):
    """Compute regression diagnostics comparing model to observations.

    Returns a dict with keys:
        - ``r_squared``: Coefficient of determination (R²)
        - ``var_res``: Variance of residuals
        - ``durbin_watson``: Durbin-Watson autocorrelation statistic
        - ``shapiro_wilk_w``: Shapiro-Wilk W statistic
        - ``shapiro_wilk_p``: Shapiro-Wilk p-value
        - ``MAE``: Mean absolute error
    """
    from scipy.stats import shapiro

    residuals = model - obs

    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((obs - np.mean(obs)) ** 2)
    r_squared = 1.0 if ss_tot == 0.0 else 1 - (ss_res / ss_tot)

    var_res = np.var(residuals)

    diffs = np.diff(residuals)
    durbin_watson = np.nan if ss_res == 0.0 else np.sum(diffs**2) / ss_res

    if np.ptp(residuals) == 0.0:
        sw_w, sw_p = np.nan, np.nan
    else:
        sw_w, sw_p = shapiro(residuals)

    mae = np.mean(np.abs(residuals))

    return {
        "r_squared": r_squared,
        "var_res": var_res,
        "durbin_watson": durbin_watson,
        "shapiro_wilk_w": sw_w,
        "shapiro_wilk_p": sw_p,
        "MAE": mae,
    }
