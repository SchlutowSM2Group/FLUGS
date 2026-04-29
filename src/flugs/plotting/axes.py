"""Axis formatting and setup utilities."""

import matplotlib.dates as mdates


def format_datetime_axis(ax, rotation=45):
    """Apply standard datetime formatting to x-axis.

    Parameters
    ----------
    ax : matplotlib Axes
    rotation : float
        X-tick label rotation in degrees.
    """
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
    ax.tick_params(axis="x", rotation=rotation)
    ax.xaxis.get_offset_text().set_visible(False)


def format_spatial_axis(ax, lon_ext, lat_ext, nx, ny):
    """Apply spatial coordinate formatting to axes.

    Parameters
    ----------
    ax : matplotlib Axes
    lon_ext : list
        [lon_min, lon_max] in degrees.
    lat_ext : list
        [lat_min, lat_max] in degrees.
    nx, ny : int
        Number of pixels in x and y directions.
    """
    ax.set_xlabel("longitude [deg.]", x=0.5, rotation=0, labelpad=-10)
    ax.set_ylabel("latitude [deg.]", labelpad=-15)
    ax.set_xticks([0, nx])
    ax.set_xticklabels(lon_ext)
    ax.set_yticks([0, ny])
    ax.set_yticklabels(lat_ext, rotation=90, va="center")


def set_equal_axes(ax):
    """Set equal axis limits for both x and y (useful for 1:1 comparison plots).

    Parameters
    ----------
    ax : matplotlib Axes
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    overall_min = min(xlim[0], ylim[0])
    overall_max = max(xlim[1], ylim[1])
    ax.set_xlim(overall_min, overall_max)
    ax.set_ylim(overall_min, overall_max)


def add_grid(ax, alpha=0.3, linestyle="--", linewidth=0.5):
    """Add standard grid styling to axes.

    Parameters
    ----------
    ax : matplotlib Axes
    alpha : float
        Grid transparency.
    linestyle : str
        Grid line style.
    linewidth : float
        Grid line width.
    """
    ax.grid(True, alpha=alpha, linestyle=linestyle, linewidth=linewidth)


def add_oneonone_line(ax, label="y=x", **kwargs):
    """Add 1:1 reference line (y=x) to axes.

    Parameters
    ----------
    ax : matplotlib Axes
    label : str
        Legend label for the line.
    **kwargs
        Additional arguments passed to ``axline()``.
    """
    defaults = {"linestyle": "--", "color": "gray", "label": label}
    defaults.update(kwargs)
    ax.axline((0, 0), slope=1, **defaults)
