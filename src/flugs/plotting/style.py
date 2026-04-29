"""Style management and base plotter class."""

import matplotlib.pyplot as plt

from .axes import (
    format_datetime_axis,
    format_spatial_axis,
    set_equal_axes,
    add_grid,
    add_oneonone_line,
)
from .helpers import (
    compute_symmetric_vminmax,
    apply_boundary_mask,
    get_flux_columns,
)


class StyleManager:
    """Manages colors, markers, fonts, and colormaps for consistent styling."""

    def __init__(self, preset="default"):
        """Initialize style manager.

        Parameters
        ----------
        preset : str
            Style preset name (currently only 'default' is supported).
        """
        self.cmaps = [
            "cividis",
            "plasma",
            "viridis",
            "inferno",
            "magma",
            "twilight",
            "terrain",
        ]
        self.markers = ["o", "s", "x", "*", "4", "+", "1"]
        self.fontsize = {"suptitle": 15, "title": 13, "label": 12.5, "legend": 11}
        self.lcc_cmaps = ["cividis", "plasma"]

        # Propagate font sizes to matplotlib rcParams so tick labels,
        # axis labels, and titles scale consistently.
        plt.rcParams.update(
            {
                "axes.titlesize": self.fontsize["title"],
                "axes.labelsize": self.fontsize["label"],
                "xtick.labelsize": self.fontsize["legend"],
                "ytick.labelsize": self.fontsize["legend"],
                "legend.fontsize": self.fontsize["legend"],
                "figure.titlesize": self.fontsize["suptitle"],
            }
        )

    def get_cmap(self, i):
        """Get colormap by index (cycles through available colormaps)."""
        return self.cmaps[i % len(self.cmaps)]

    def get_marker(self, i):
        """Get marker by index (cycles through available markers)."""
        return self.markers[i % len(self.markers)]

    def get_color(self, i):
        """Get matplotlib color cycle color (C0, C1, C2, ...)."""
        return f"C{i}"


class PlotBase:
    """Base class with common plotting utilities shared across all plotters."""

    def __init__(self, style_manager=None, label_manager=None):
        """Initialize base plotter.

        Parameters
        ----------
        style_manager : StyleManager, optional
            Creates default if None.
        label_manager : LabelManager, optional
            If None, no label manager is set (must be provided by caller
            or subclass if labels are needed).
        """
        self.style = style_manager or StyleManager()
        if label_manager is None:
            self.labels = None
        else:
            self.labels = label_manager

    # --- Axis Formatters (delegate to standalone functions) ---

    @staticmethod
    def format_datetime_axis(ax, rotation=45):
        """Apply standard datetime formatting to x-axis."""
        format_datetime_axis(ax, rotation)

    @staticmethod
    def format_spatial_axis(ax, lon_ext, lat_ext, nx, ny):
        """Apply spatial coordinate formatting to axes."""
        format_spatial_axis(ax, lon_ext, lat_ext, nx, ny)

    @staticmethod
    def set_equal_axes(ax):
        """Set equal axis limits for both x and y."""
        set_equal_axes(ax)

    # --- Common Plot Elements ---

    @staticmethod
    def add_grid(ax, alpha=0.3, linestyle="--", linewidth=0.5):
        """Add standard grid styling to axes."""
        add_grid(ax, alpha, linestyle, linewidth)

    @staticmethod
    def add_oneonone_line(ax, label="y=x", **kwargs):
        """Add 1:1 reference line (y=x) to axes."""
        add_oneonone_line(ax, label, **kwargs)

    # --- Scatter Configurations ---

    def scatter_hollow(self, ax, x, y, label=None, **kwargs):
        """Create hollow scatter plot (typically for aggregated/observed flux)."""
        defaults = {
            "marker": "o",
            "facecolors": "none",
            "edgecolors": "gray",
            "s": 40,
            "alpha": 0.8,
            "linewidths": 1,
        }
        defaults.update(kwargs)
        return ax.scatter(x, y, label=label, **defaults)

    def scatter_filled(self, ax, x, y, color, marker, label=None, **kwargs):
        """Create filled scatter plot (typically for learned fluxes)."""
        defaults = {"s": 25, "alpha": 0.7, "edgecolors": "black", "linewidths": 0.5}
        defaults.update(kwargs)
        return ax.scatter(x, y, color=color, marker=marker, label=label, **defaults)

    def scatter_synth(self, ax, x, y, color, label=None, **kwargs):
        """Create synthetic data scatter plot (typically crosses for ground truth)."""
        defaults = {"marker": "x", "s": 20, "alpha": 0.7, "linewidths": 1.5}
        defaults.update(kwargs)
        return ax.scatter(x, y, color=color, label=label, **defaults)

    # --- Data Utilities (delegate to standalone functions) ---

    @staticmethod
    def get_flux_columns(df):
        """Extract flux column names from dataframe."""
        return get_flux_columns(df)

    @staticmethod
    def apply_boundary_mask(field, boundary_mask):
        """Apply boundary mask to field (sets boundary cells to NaN)."""
        return apply_boundary_mask(field, boundary_mask)

    @staticmethod
    def compute_symmetric_vminmax(data):
        """Compute symmetric vmin/vmax for diverging colormaps."""
        return compute_symmetric_vminmax(data)

    # --- Figure Management ---

    def create_figure(self, figsize=(8, 4), constrained_layout=True):
        """Create figure with standard settings."""
        return plt.figure(figsize=figsize, constrained_layout=constrained_layout)

    def finalize_and_save(self, fig, output_path, show=True, **savefig_kwargs):
        """Save and optionally show figure."""
        defaults = {"bbox_inches": "tight"}
        defaults.update(savefig_kwargs)
        fig.savefig(output_path, **defaults)
        if show:
            plt.show()
