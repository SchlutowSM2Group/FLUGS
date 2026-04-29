"""Timeseries plotting functionality."""

import numpy as np
import matplotlib.pyplot as plt

from .style import PlotBase


class TimeSeriesPlotter(PlotBase):
    """Plots timeseries data (drivers, fluxes, comparisons)."""

    def plot_drivers_on_axes(self, axes, time, drivers, driver_names, **kwargs):
        """
        Plot multiple driver timeseries on existing axes (for side-by-side comparisons).

        Parameters
        ----------
        axes : list or array of matplotlib axes
            Axes to plot on.
        time : array-like
            Datetime values.
        drivers : ndarray of shape (N, P)
            Driver values where P is number of drivers.
        driver_names : list of str
            Driver variable names.
        **kwargs
            Additional options: title.

        Returns
        -------
        axes
            The axes objects that were plotted on.
        """
        P = len(driver_names)

        # Handle single driver case
        if P == 1:
            axes = [axes] if not isinstance(axes, (list, np.ndarray)) else axes

        for p, (ax, name) in enumerate(zip(axes, driver_names)):
            ax.plot(
                time,
                drivers[..., p],
                "o",
                c="gray",
                markeredgecolor="k",
                alpha=0.6,
                markersize=4,
            )

            # Only set driver name as title if no overall title provided
            if "title" not in kwargs:
                ax.set_title(
                    self.labels.get_label(name), fontsize=self.style.fontsize["title"]
                )

            ax.set_xlabel("Time", fontsize=self.style.fontsize["label"])

            # Use core utilities
            self.format_datetime_axis(ax)
            self.add_grid(ax)

        # Set title on first axis if provided
        if "title" in kwargs and len(axes) > 0:
            axes[0].set_title(kwargs["title"], fontsize=self.style.fontsize["title"])

        return axes

    def plot_fluxes_on_ax(
        self,
        ax,
        time,
        target,
        target_name,
        flux_dict,
        synth_flux=None,
        I_gtyp=None,
        **kwargs,
    ):
        """
        Plot flux timeseries on an existing axis.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axis to plot on.
        time : array-like
            Datetime values.
        target : array-like
            Observed/aggregated flux values.
        target_name : str
            Name of target variable (for y-label).
        flux_dict : dict
            Mapping of flux names to arrays.
        synth_flux : ndarray, optional
            Shape (N, I_gtyp) with synthetic fluxes.
        I_gtyp : int, optional
            Number of land cover types (required if synth_flux provided).
        **kwargs
            Additional options: title, legend_loc, show_legend, add_ylabel,
            land_cover_names.

        Returns
        -------
        ax
            The axis that was plotted on.
        """
        # Aggregated flux (hollow scatter)
        self.scatter_hollow(ax, time, target, label="Aggregated flux")

        # Get land cover names if provided
        land_cover_names = kwargs.get("land_cover_names", None)

        # Learned fluxes (filled scatter)
        for i, (key, flux) in enumerate(flux_dict.items()):
            color = self.style.get_color(i)
            marker = self.style.get_marker(i)
            lc_name = land_cover_names[i] if land_cover_names else f"LCC {i}"
            label = f"Learned flux of {lc_name}"
            self.scatter_filled(ax, time, flux, color, marker, label=label)

        # Synthetic fluxes (crosses) - optional
        if synth_flux is not None:
            if I_gtyp is None:
                raise ValueError("I_gtyp must be provided when synth_flux is given")
            for i in range(I_gtyp):
                color = self.style.get_color(i)
                lc_name = land_cover_names[i] if land_cover_names else f"LCC {i}"
                label = f"Real flux of {lc_name}"
                self.scatter_synth(ax, time, synth_flux[..., i], color, label=label)

        # Formatting
        self.format_datetime_axis(ax)
        self.add_grid(ax)

        ax.set_xlabel("Time", fontsize=self.style.fontsize["label"])

        if kwargs.get("add_ylabel", True):
            ax.set_ylabel(
                self.labels.get_label(target_name),
                fontsize=self.style.fontsize["label"],
            )

        if kwargs.get("show_legend", True):
            legend_loc = kwargs.get("legend_loc", "lower right")
            ax.legend(loc=legend_loc, fontsize=self.style.fontsize["legend"])

        if "title" in kwargs:
            ax.set_title(kwargs["title"], fontsize=self.style.fontsize["title"])

        return ax

    def plot_drivers(self, time, drivers, driver_names, **kwargs):
        """
        Plot multiple driver timeseries in separate subplots.

        Parameters
        ----------
        time : array-like
            Datetime values.
        drivers : ndarray of shape (N, P)
            Driver values where P is number of drivers.
        driver_names : list of str
            Driver variable names.
        **kwargs
            Additional options: figsize, suptitle.

        Returns
        -------
        fig, axes
            Matplotlib figure and axes objects.
        """
        P = len(driver_names)
        figsize = kwargs.get("figsize", (6 * P, 4))
        fig, axes = plt.subplots(1, P, figsize=figsize, constrained_layout=True)

        # Handle single driver case
        if P == 1:
            axes = [axes]

        # Use the _on_axes method for the actual plotting
        self.plot_drivers_on_axes(axes, time, drivers, driver_names)

        # Apply date formatting
        fig.autofmt_xdate()

        # Add suptitle if provided
        if "suptitle" in kwargs:
            fig.suptitle(kwargs["suptitle"], fontsize=self.style.fontsize["suptitle"])

        return fig, axes

    def plot_fluxes(
        self,
        time,
        target,
        target_name,
        flux_dict,
        synth_flux=None,
        I_gtyp=None,
        **kwargs,
    ):
        """
        Plot flux timeseries with learned and optional synthetic fluxes.

        Parameters
        ----------
        time : array-like
            Datetime values.
        target : array-like
            Observed/aggregated flux values.
        target_name : str
            Name of target variable (for y-label).
        flux_dict : dict
            Mapping of flux names to arrays.
        synth_flux : ndarray, optional
            Shape (N, I_gtyp) with synthetic fluxes.
        I_gtyp : int, optional
            Number of land cover types (required if synth_flux provided).
        **kwargs
            Additional options: figsize, title, legend_loc.

        Returns
        -------
        fig, ax
            Matplotlib figure and axes objects.
        """
        figsize = kwargs.get("figsize", (8, 4))
        fig = self.create_figure(figsize=figsize)
        ax = fig.gca()

        # Use the _on_ax method for the actual plotting
        self.plot_fluxes_on_ax(
            ax,
            time,
            target,
            target_name,
            flux_dict,
            synth_flux=synth_flux,
            I_gtyp=I_gtyp,
            **kwargs,
        )

        fig.autofmt_xdate()

        return fig, ax

    def plot_comparison(self, flux1_dict, flux2_dict, label1, label2, **kwargs):
        """
        Plot 1:1 comparison between two datasets.

        Parameters
        ----------
        flux1_dict : dict
            Flux arrays from dataset 1.
        flux2_dict : dict
            Flux arrays from dataset 2.
        label1 : str
            Label for x-axis (dataset 1).
        label2 : str
            Label for y-axis (dataset 2).
        **kwargs
            Additional options: figsize, title, legend_loc, land_cover_names.

        Returns
        -------
        fig, ax
            Matplotlib figure and axes objects.
        """
        figsize = kwargs.get("figsize", (8, 4.5))
        fig = self.create_figure(figsize=figsize)
        ax = fig.gca()

        # Get land cover names if provided
        land_cover_names = kwargs.get("land_cover_names", None)

        # Plot each LCC flux comparison
        for i, key in enumerate(flux1_dict.keys()):
            flux1 = flux1_dict[key]
            flux2 = flux2_dict[key]
            color = self.style.get_color(i)
            marker = self.style.get_marker(i)
            lc_name = land_cover_names[i] if land_cover_names else f"LCC {i}"
            self.scatter_filled(ax, flux1, flux2, color, marker, label=lc_name)

        # Add 1:1 line and equalize axes
        self.add_oneonone_line(ax)
        self.set_equal_axes(ax)
        self.add_grid(ax)

        # Labels
        ax.set_xlabel(label1, fontsize=self.style.fontsize["label"])
        ax.set_ylabel(label2, fontsize=self.style.fontsize["label"])

        legend_loc = kwargs.get("legend_loc", "best")
        ax.legend(loc=legend_loc, fontsize=self.style.fontsize["legend"])

        if "title" in kwargs:
            ax.set_title(kwargs["title"], fontsize=self.style.fontsize["title"])

        return fig, ax
