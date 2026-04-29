"""Environmental response functions used by the synthetic-data pipeline.

Functions
---------
runkle
    Net ecosystem exchange model from Runkle et al. (2013).
ERF
    Environmental Response Function dispatching ``runkle`` with
    land-cover-specific parameter sets.
"""


def runkle(PAR, Ts, Pmax, alpha, Rbase, Q10, Tref, gamma):
    """Net ecosystem exchange model from Runkle et al. (2013).

    Parameters
    ----------
    PAR : float or array_like
        Photosynthetically active radiation.
    Ts : float or array_like
        Soil / surface temperature.
    Pmax, alpha, Rbase, Q10, Tref, gamma : float
        Model parameters.

    Returns
    -------
    float or ndarray
        Net CO2 flux (positive = respiration, negative = uptake).
    """
    return Rbase * Q10 ** ((Ts - Tref) / gamma) - Pmax * alpha * PAR / (
        Pmax + alpha * PAR
    )


_ERF_PARAMS = {
    0: (400.0, 1.1, 30.0, 2.0, 15.0, 5.0),
    1: (200.0, 0.4, 50.0, 1.5, 15.0, 10.0),
    2: (300.0, 0.8, 40.0, 1.8, 15.0, 7.0),
    3: (150.0, 0.3, 60.0, 1.2, 15.0, 12.0),
}


def ERF(PAR, Ts, lc_type):
    """Environmental Response Function.

    Dispatches to :func:`runkle` with land-cover-specific parameters.

    Parameters
    ----------
    PAR : float or array_like
        Photosynthetically active radiation.
    Ts : float or array_like
        Soil / surface temperature.
    lc_type : int
        Land-cover type index (0-3).

    Returns
    -------
    float or ndarray
        Surface CO2 flux.
    """
    if lc_type not in _ERF_PARAMS:
        raise ValueError(f"Unknown lc_type={lc_type}. Available: {sorted(_ERF_PARAMS)}")
    return runkle(PAR, Ts, *_ERF_PARAMS[lc_type])
