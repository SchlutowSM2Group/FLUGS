"""Spatial field plotting."""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import ListedColormap, BoundaryNorm

from .style import PlotBase


class SpatialPlotter(PlotBase):
    """Plots 2D spatial fields."""

    def __init__(self, style_manager=None, label_manager=None):
        """
        Initialize spatial plotter.

        Parameters
        ----------
        style_manager : StyleManager, optional
            Creates default if None.
        label_manager : LabelManager, optional
            If None, no label manager is set.
        """
        super().__init__(style_manager, label_manager)
        # For discrete colormaps
        self.start_bound = 0.25
        self.end_bound = 0.8

    def plot_field2d(
        self,
        field,
        xmx,
        ymx,
        lon_ext,
        lat_ext,
        land_cover_names=None,
        zm=None,
        title="",
        marker_loc=None,
        wind_u=None,
        wind_v=None,
        ax=None,
        **kwargs,
    ):
        """
        Plot 2D spatial field with optional wind overlay and tower marker.

        Parameters
        ----------
        field : ndarray
            2D array to plot.
        xmx : float
            Maximum x-coordinate in plot units.
        ymx : float
            Maximum y-coordinate in plot units.
        lon_ext : list
            Longitude extent [min, max] in degrees.
        lat_ext : list
            Latitude extent [min, max] in degrees.
        land_cover_names : list of str, optional
            Names for land cover classes (for colorbar labels).
        zm : float, optional
            Height or depth level (for title).
        title : str
            Base title for the plot.
        marker_loc : tuple or list, optional
            Single (row, col) or list of (row, col) for markers.
        wind_u : ndarray, optional
            2D array of zonal wind component (for quiver).
        wind_v : ndarray, optional
            2D array of meridional wind component (for quiver).
        ax : matplotlib.axes.Axes, optional
            Axis to plot on. If None, creates new figure.
        **kwargs
            Additional options: figsize, cmap, vmin, vmax, quiver_step,
            quiver_scale, cmap_start, cmap_end, skip_zero,
            set_land_cover_names, set_land_cover_indices, show_ylabel,
            y_tickpad.

        Returns
        -------
        fig, ax
            Matplotlib figure and axes objects.
        """
        # Create figure if ax not provided
        if ax is None:
            figsize = kwargs.get("figsize", (6, 4))
            fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        else:
            fig = ax.get_figure()

        # Plot the field
        im_kwargs = {"extent": [0, xmx, 0, ymx], "origin": "lower", "aspect": "auto"}

        if "vmin" in kwargs:
            im_kwargs["vmin"] = kwargs["vmin"]
        if "vmax" in kwargs:
            im_kwargs["vmax"] = kwargs["vmax"]

        # Define discrete colors for each land cover class
        n_classes = len(np.unique(field[~np.isnan(field)]))

        cmap = self.style.get_cmap(-1)  # Always use terrain by default
        cmap_obj = mpl.colormaps[cmap]

        # Allow custom colormap bounds
        cmap_start = kwargs.get("cmap_start", self.start_bound)
        cmap_end = kwargs.get("cmap_end", self.end_bound)

        colors = cmap_obj(np.linspace(cmap_start, cmap_end, n_classes))
        cmap_discrete = ListedColormap(colors)

        # Define boundaries
        skip_zero = kwargs.get("skip_zero", False)
        shift = 1 if skip_zero else 0
        bounds = [-0.5 + i + shift for i in range(n_classes + 1)]
        norm = BoundaryNorm(bounds, cmap_discrete.N)

        # Update imshow call
        im = ax.imshow(field, cmap=cmap_discrete, norm=norm, **im_kwargs)

        # Update colorbar with discrete ticks
        cb = plt.colorbar(im, ax=ax, spacing="proportional", pad=0.0)
        cb.set_ticks(np.arange(n_classes) + shift)
        if kwargs.get("set_land_cover_names") is True and land_cover_names is not None:
            cb.set_ticklabels(
                land_cover_names,
                rotation=270,
                fontsize=self.style.fontsize["label"],
                va="center",
                x=0.55,
            )
        elif kwargs.get("set_land_cover_indices") is True:
            indices = [str(i) for i in range(n_classes)]
            cb.set_ticklabels(
                indices,
                rotation=270,
                fontsize=self.style.fontsize["label"],
                va="center",
                x=0.55,
            )
        else:
            cb.set_ticklabels(
                [f"LCC {i}" for i in range(n_classes)],
                rotation=270,
                fontsize=self.style.fontsize["label"],
                va="center",
                x=0.55,
            )

        # Add wind field arrows if provided
        if wind_u is not None and wind_v is not None:
            step = kwargs.get("quiver_step", 75)
            x = np.linspace(0, xmx, field.shape[1])
            y = np.linspace(0, ymx, field.shape[0])
            X, Y = np.meshgrid(x, y)

            # Subsample
            X_q = X[::step, ::step]
            Y_q = Y[::step, ::step]
            um_q = wind_u
            vm_q = wind_v

            quiver_scale = kwargs.get("quiver_scale", 50)
            ax.quiver(
                X_q,
                Y_q,
                um_q,
                vm_q,
                color="white",
                scale=quiver_scale,
                pivot="middle",
                alpha=0.8,
            )

        # Add measurement point marker(s) if provided
        if marker_loc is not None:
            ny, nx = field.shape

            # Check if marker_loc is a list of locations or a single location
            if isinstance(marker_loc, list):
                # Plot multiple markers with labels
                for i, loc in enumerate(marker_loc, 1):
                    twr_col, twr_row = loc
                    twr_row = twr_row / ny * ymx
                    twr_col = twr_col / nx * xmx
                    marker = ax.scatter(
                        twr_col,
                        twr_row,
                        color="red",
                        marker="*",
                        alpha=1.0,
                        s=60,
                        linewidths=1,
                    )
                    marker.set_path_effects(
                        [pe.withStroke(linewidth=4, foreground="black")]
                    )

                    # Add text label
                    tower_name = "RU-Che" if i == 1 else "RU-Ch2"
                    text = ax.text(
                        twr_col,
                        twr_row + ymx * 0.03,
                        tower_name,
                        color="white",
                        fontsize=self.style.fontsize["label"] - 1,
                        ha="center",
                        va="bottom",
                        weight="bold",
                    )
                    text.set_path_effects(
                        [pe.withStroke(linewidth=2, foreground="black")]
                    )
            else:
                # Plot single marker (backward compatible)
                twr_col, twr_row = marker_loc
                twr_row = twr_row / ny * ymx
                twr_col = twr_col / nx * xmx
                marker = ax.scatter(
                    twr_col,
                    twr_row,
                    color="red",
                    marker="*",
                    alpha=1.0,
                    s=60,
                    linewidths=1,
                )
                marker.set_path_effects(
                    [pe.withStroke(linewidth=4, foreground="black")]
                )

        # Format axes
        if zm is not None:
            full_title = f"{title} at $z = {zm}\\,$m"
        else:
            full_title = title

        y_tickpad = kwargs.get("y_tickpad", 0.0)
        ax.set_title(full_title, fontsize=self.style.fontsize["title"])
        ax.tick_params(axis="y", which="major", pad=y_tickpad)
        ax.set_xlabel(
            "longitude [deg. E]",
            x=0.5,
            rotation=0,
            labelpad=-10,
            fontsize=self.style.fontsize["label"],
        )
        ax.set_xticks([0, xmx])
        # Format lon/lat to 2 decimal places to avoid overlap
        lon_labels = [f"{lon:.2f}" for lon in lon_ext]
        ax.set_xticklabels(lon_labels)
        # Set horizontal alignment: left tick = left, right tick = right
        for i, label in enumerate(ax.get_xticklabels()):
            label.set_ha("left" if i == 0 else "right")

        # Optionally show/hide y-axis label
        show_ylabel = kwargs.get("show_ylabel", True)
        if show_ylabel:
            ax.set_ylabel(
                "latitude [deg. N]", labelpad=-10, fontsize=self.style.fontsize["label"]
            )
        ax.set_yticks([0, ymx])
        lat_labels = [f"{lat:.2f}" for lat in lat_ext]
        ax.set_yticklabels(lat_labels, rotation=90, va="center")

        return fig, ax
