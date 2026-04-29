"""Plotting subpackage — manuscript figure plotters.

The five public classes used by ``runs/vis_synth.py`` and ``runs/vis_cherskii.py``
are re-exported here for convenience.
"""

from .style import StyleManager, PlotBase
from .labels import LabelManager
from .timeseries import TimeSeriesPlotter
from .response import ResponsePlotter
from .spatial import SpatialPlotter

__all__ = [
    "StyleManager",
    "PlotBase",
    "LabelManager",
    "TimeSeriesPlotter",
    "ResponsePlotter",
    "SpatialPlotter",
]
