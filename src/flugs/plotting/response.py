"""Environmental Response Function (ERF) plotting."""

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.gridspec import GridSpec

from .style import PlotBase


class ResponsePlotter(PlotBase):
    """Plots environmental response functions (ERF) and binned analysis."""

    def plot_erf_single_on_ax(
        self,
        ax,
        x_driver,
        x_driver_name,
        color_driver,
        color_driver_name,
        target,
        target_name,
        flux_dict,
        I_gtyp,
        synth_flux=None,
        **kwargs,
    ):
        """
        Plot a single ERF panel on an existing axis.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axis to plot on.
        x_driver : array-like
            X-axis driver values.
        x_driver_name : str
            Name of x-axis driver variable.
        color_driver : array-like
            Driver values used for coloring.
        color_driver_name : str
            Name of driver used for coloring.
        target : array-like
            Observed/aggregated flux values.
        target_name : str
            Name of target variable.
        flux_dict : dict
            Mapping of flux names to arrays.
        I_gtyp : int
            Number of land cover types.
        synth_flux : ndarray, optional
            Shape (N, I_gtyp) with synthetic fluxes.
        **kwargs
            Additional options: show_labels, add_ylabel, add_xlabel,
            land_cover_names.

        Returns
        -------
        scatter_collections : list
            List of scatter plot collections (for colorbars).
        """
        show_labels = kwargs.get("show_labels", False)
        add_ylabel = kwargs.get("add_ylabel", True)
        add_xlabel = kwargs.get("add_xlabel", True)
        land_cover_names = kwargs.get("land_cover_names", None)

        # Get color values for colorbar range
        vmin, vmax = color_driver.min(), color_driver.max()

        scatter_collections = []

        for i in range(I_gtyp):
            flux_key = f"flux_lc{i}"
            flux = flux_dict[flux_key]
            marker = self.style.get_marker(i)

            # Use different colormap for each LCC type
            lcc_cmap = self.style.lcc_cmaps[i % len(self.style.lcc_cmaps)]
            cmap_obj = mpl.colormaps[lcc_cmap]

            # Get a single color from this colormap for the synth data
            color = cmap_obj(0.6 * i)

            # Get land cover name
            lc_name = land_cover_names[i] if land_cover_names else f"LCC {i}"

            # Plot synthetic data if provided
            if synth_flux is not None:
                label = f"Real {lc_name}" if show_labels and i < 2 else None
                ax.scatter(
                    x_driver,
                    synth_flux[..., i],
                    marker="x",
                    color=color,
                    label=label,
                    s=20,
                    alpha=0.7,
                    linewidths=1.5,
                )

            # Plot learned fluxes colored by other driver
            label = f"Learned {lc_name}" if show_labels and i < 2 else None
            sc = ax.scatter(
                x_driver,
                flux,
                c=color_driver,
                label=label,
                cmap=lcc_cmap,
                marker=marker,
                s=25,
                alpha=0.7,
                edgecolors="black",
                linewidths=0.5,
                vmin=vmin,
                vmax=vmax,
                zorder=10,
            )
            scatter_collections.append(sc)

        # Format axes
        if add_xlabel:
            ax.set_xlabel(
                self.labels.get_label(x_driver_name),
                fontsize=self.style.fontsize["label"],
            )
        if add_ylabel:
            ax.set_ylabel(
                self.labels.get_label(target_name),
                fontsize=self.style.fontsize["label"],
            )

        self.add_grid(ax)

        return scatter_collections

    def plot_erf_multipanel(
        self,
        drivers,
        driver_names,
        target,
        target_name,
        flux_dict,
        I_gtyp,
        synth_flux=None,
        land_cover_names=None,
        **kwargs,
    ):
        """
        Create multi-panel ERF plot with colorbars for each land cover type.

        Parameters
        ----------
        drivers : ndarray of shape (N, P)
            Driver values where P is number of drivers.
        driver_names : list of str
            Driver variable names.
        target : array-like
            Observed/aggregated flux values.
        target_name : str
            Name of target variable.
        flux_dict : dict
            Mapping of flux names to arrays.
        I_gtyp : int
            Number of land cover types.
        synth_flux : ndarray, optional
            Shape (N, I_gtyp) with synthetic fluxes.
        land_cover_names : list of str, optional
            Names for land cover types.
        **kwargs
            Additional options: figsize_per_panel, suptitle, panel_width,
            colorbar_width, panel_gap, fig_height, wspace, margins.

        Returns
        -------
        fig, axes
            Matplotlib figure and list of axes objects.
        """
        P = len(driver_names)
        num_colorbars = I_gtyp

        # Provide sensible defaults but allow callers to override via kwargs.
        defaults = {
            "panel_width": 20,
            "colorbar_width": 0.625,
            "panel_gap": 5,
            "figsize_per_panel": 6,
            "fig_height": 4,
            "wspace": 0.0,
            # Grid margins: left, right, top, bottom
            "margins": (0.08, 0.92, 0.92, 0.20),
        }

        # Merge defaults with kwargs, but do not overwrite kwargs in place.
        merged = {**defaults, **kwargs}

        # Build GridSpec with colorbars using merged values
        width_ratios = []
        panel_to_gridspec_idx = {}

        for p in range(P):
            panel_to_gridspec_idx[p] = len(width_ratios)
            width_ratios.append(merged["panel_width"])  # Panel width
            for _ in range(num_colorbars):
                width_ratios.append(merged["colorbar_width"])  # Colorbar width
            if p < P - 1:
                width_ratios.append(merged["panel_gap"])  # Gap between panels

        fig = plt.figure(
            figsize=(merged["figsize_per_panel"] * P, merged["fig_height"])
        )
        left, right, top, bottom = merged["margins"]
        gs = GridSpec(
            1,
            len(width_ratios),
            figure=fig,
            width_ratios=width_ratios,
            wspace=merged["wspace"],
            left=left,
            right=right,
            top=top,
            bottom=bottom,
        )

        # Create panels
        axes = []
        panel_scatter_collections = {}

        for p in range(P):
            sharey = axes[0] if p > 0 else None
            ax = fig.add_subplot(gs[0, panel_to_gridspec_idx[p]], sharey=sharey)
            axes.append(ax)
            if p > 0:
                ax.tick_params(labelleft=False)

            # Variable used for coloring is the other driver
            color_var_name = driver_names[(p + 1) % P]

            # Use the single panel plotting method
            scatter_collections = self.plot_erf_single_on_ax(
                ax=ax,
                x_driver=drivers[..., p],
                x_driver_name=driver_names[p],
                color_driver=drivers[..., (p + 1) % P],
                color_driver_name=color_var_name,
                target=target,
                target_name=target_name,
                flux_dict=flux_dict,
                I_gtyp=I_gtyp,
                synth_flux=synth_flux,
                show_labels=True,
                add_ylabel=(p == 0),
                add_xlabel=True,
                land_cover_names=land_cover_names,
                **kwargs,
            )

            # Store scatter collections for this panel
            panel_scatter_collections[p] = scatter_collections

        # Add colorbars using the GridSpec columns
        for p in panel_scatter_collections:
            scatter_collections = panel_scatter_collections[p]
            color_var_name = driver_names[(p + 1) % P]

            # Find the GridSpec index for this panel
            panel_gs_idx = panel_to_gridspec_idx[p]

            # Add colorbars for each LCC type
            for i, sc in enumerate(scatter_collections):
                # Colorbar is in the next GridSpec column after the panel
                cbar_gs_idx = panel_gs_idx + 1 + i
                cax = fig.add_subplot(gs[0, cbar_gs_idx])
                cbar = fig.colorbar(sc, cax=cax)

                # Add LCC name below each colorbar
                label = (
                    land_cover_names[i] if land_cover_names is not None else f"LCC {i}"
                )
                cbar.ax.set_xlabel(label, fontsize=13, rotation=270)

                # Only show tick labels on the outermost (rightmost/last) colorbar
                if i == len(scatter_collections) - 1:
                    cbar.set_label(
                        self.labels.get_label(color_var_name), rotation=270, labelpad=15
                    )
                else:
                    cbar.ax.set_yticklabels([])
                    cbar.ax.tick_params(length=0)

        # Create figure-level legend centered below all panels
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="outside lower center",
            ncol=5,
            framealpha=0.9,
            fontsize=self.style.fontsize["legend"],
        )

        # Set y-label on first axis
        axes[0].set_ylabel(
            self.labels.get_label(target_name), fontsize=self.style.fontsize["label"]
        )

        # Add suptitle if provided
        if "suptitle" in kwargs:
            plt.suptitle(kwargs["suptitle"], fontsize=self.style.fontsize["suptitle"])

        return fig, axes
