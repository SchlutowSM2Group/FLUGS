"""
Complete visualization script for Cherskii tower comparison.

Uses the full plotting infrastructure to compare shf_cherskii_twr1 and shf_cherskii_twr2.
"""

# %%
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from flugs.prepare import get_data
from flugs.config import DATA_DIR, OUTPUT_DIR
from flugs.utils.io import load_data, get_latest_run_dir
from flugs.plotting import (
    StyleManager,
    LabelManager,
    TimeSeriesPlotter,
    ResponsePlotter,
    SpatialPlotter,
)

# Initialize plotters
style = StyleManager()
labels = LabelManager(f"{DATA_DIR}/variables_metadata.toml")
ts_plotter = TimeSeriesPlotter(style, labels)
erf_plotter = ResponsePlotter(style, labels)
lcm_plotter = SpatialPlotter(style, labels)

# Parse obs_var from --config argument (e.g. "co2_cherskii_twr1" -> "co2")
obs_var = None
for i, arg in enumerate(sys.argv):
    if arg in ("--config", "-c") and i + 1 < len(sys.argv):
        obs_var = sys.argv[i + 1].split("_")[0]
        break
if obs_var is None:
    raise SystemExit(
        "Usage: python -m runs.vis_cherskii -c <config_name> (e.g. co2_cherskii_twr1)"
    )

towers = [f"{obs_var}_cherskii_twr1", f"{obs_var}_cherskii_twr2"]
tower_data = {}

# Resolve run directories; use the first tower's directory for shared plots
first_run_dir = get_latest_run_dir(OUTPUT_DIR, towers[0])
plot_dir = first_run_dir / "plots"

print("Loading data for towers...")
for tower in towers:
    run_config, sim_data = get_data(config=tower)

    tower_run_dir = get_latest_run_dir(OUTPUT_DIR, run_config.run_name)
    csv_fn = tower_run_dir / f"{run_config.run_name}_flugs.csv"
    df = pd.read_csv(csv_fn)

    # Prepare driver data
    N = len(df)
    P = len(run_config.dataset.driver_variables)
    drivers = np.zeros((N, P))
    for p, driver_var_name in enumerate(run_config.dataset.driver_variables):
        drivers[..., p] = df[driver_var_name]

    # Prepare target data
    target_name = run_config.observation_variable
    target = df[target_name]
    time = pd.to_datetime(df["dt"] + " " + df["tt"], format="%Y-%m-%d %H:%M")

    # Prepare flux dictionary
    I_gtyp = run_config.landcover.I_gtyp
    flux_dict = {f"flux_lc{i}": df[f"flux_lc{i}"].values for i in range(I_gtyp)}

    tower_data[tower] = {
        "run_config": run_config,
        "sim_data": sim_data,
        "time": time,
        "drivers": drivers,
        "target": target,
        "target_name": target_name,
        "flux_dict": flux_dict,
        "I_gtyp": I_gtyp,
        "driver_names": run_config.dataset.driver_variables,
    }
    print(f"  Loaded {tower}: {N} data points")

# %%
#############################################################
# Land Cover Maps - Side by Side
#############################################################

fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True, sharey=True)

full_lcm = load_data(tower_data[towers[0]]["run_config"].landcover.land_cover_fn)
full_lcm = full_lcm.to_numpy()[::-1, ...]  # Flip rows N→S to S→N (canonical layout)

lcm_by_group = tower_data[towers[0]]["sim_data"].land_cover_by_group
# Convert (group, ny, nx) to 2D array where group 0 → 1, group 1 → 2, etc.
grouped_lcm = np.full(lcm_by_group.shape[1:], np.nan)  # Initialize with NaN
for i in range(lcm_by_group.shape[0]):
    # Where this group has data (non-NaN), assign group index + 1
    mask = ~np.isnan(lcm_by_group[i])
    grouped_lcm[mask] = i + 1

marker_locs = [
    tower_data[towers[0]]["sim_data"].grid.measurement_point,
    tower_data[towers[1]]["sim_data"].grid.measurement_point,
]

_rc = tower_data[towers[0]]["run_config"]
_grid = tower_data[towers[0]]["sim_data"].grid
_field2d_kw = dict(
    xmx=_grid.xmx,
    ymx=_grid.ymx,
    lon_ext=_rc.dataset.longitude_extent,
    lat_ext=_rc.dataset.latitude_extent,
    land_cover_names=_rc.landcover.land_cover_names,
)

lcm_plotter.plot_field2d(
    full_lcm,
    **_field2d_kw,
    zm=0.0,
    title=f"Full Land Cover Map",
    marker_loc=marker_locs,
    ax=axes[0],  # Plot on first panel
    cmap_start=0.0,  # Use full terrain colormap
    cmap_end=0.9,
    y_tickpad=-0.1,
    set_land_cover_indices=True,
)

lcm_plotter.plot_field2d(
    grouped_lcm,
    **_field2d_kw,
    zm=0.0,
    title=f"Land Cover by Group",
    marker_loc=marker_locs,
    ax=axes[1],  # Plot on second panel
    skip_zero=True,  # Skip the zero background
    cmap_start=0.25,  # Use truncated/smaller terrain colormap
    cmap_end=0.8,
    show_ylabel=False,  # Hide y-label on second panel
    set_land_cover_names=True,
)

plt.savefig(plot_dir / "cherskii_lcm.pdf")
plt.show()

# %%
#############################################################
# Timeseries Drivers - Combined View
# Rows=Towers, Cols=Selected Drivers from both SHF and CO2
#############################################################

# Load SHF data for combined drivers (if not already loaded)
shf_towers = ["shf_cherskii_twr1", "shf_cherskii_twr2"]
shf_tower_data = {}

print("Loading SHF data for driver comparison...")
for tower in shf_towers:
    run_config, sim_data = get_data(config=tower)
    tower_run_dir = get_latest_run_dir(OUTPUT_DIR, run_config.run_name)
    csv_fn = tower_run_dir / f"{run_config.run_name}_flugs.csv"
    df = pd.read_csv(csv_fn)

    # Prepare driver data
    N = len(df)
    P = len(run_config.dataset.driver_variables)
    drivers = np.zeros((N, P))
    for p, driver_var_name in enumerate(run_config.dataset.driver_variables):
        drivers[..., p] = df[driver_var_name]

    time = pd.to_datetime(df["dt"] + " " + df["tt"], format="%Y-%m-%d %H:%M")

    shf_tower_data[tower] = {
        "time": time,
        "drivers": drivers,
        "driver_names": run_config.dataset.driver_variables,
    }
    print(f"  Loaded {tower}: {N} data points")

# Load CO2 data to get additional drivers
co2_towers = ["co2_cherskii_twr1", "co2_cherskii_twr2"]
co2_tower_data = {}

print("Loading CO2 data for driver comparison...")
for tower in co2_towers:
    run_config, sim_data = get_data(config=tower)
    tower_run_dir = get_latest_run_dir(OUTPUT_DIR, run_config.run_name)
    csv_fn = tower_run_dir / f"{run_config.run_name}_flugs.csv"
    df = pd.read_csv(csv_fn)

    # Prepare driver data
    N = len(df)
    P = len(run_config.dataset.driver_variables)
    drivers = np.zeros((N, P))
    for p, driver_var_name in enumerate(run_config.dataset.driver_variables):
        drivers[..., p] = df[driver_var_name]

    time = pd.to_datetime(df["dt"] + " " + df["tt"], format="%Y-%m-%d %H:%M")

    co2_tower_data[tower] = {
        "time": time,
        "drivers": drivers,
        "driver_names": run_config.dataset.driver_variables,
    }
    print(f"  Loaded {tower}: {N} data points")

# Define which drivers to show and from which dataset
# Format: (variable_pattern, dataset_key)
# Note: Variable names contain tower number, e.g., Rn_1_1_1 for tower 1, Rn_2_1_1 for tower 2
# We'll use patterns like 'Rn_{}_1_1' which will be formatted with tower number
selected_drivers = [
    ("Rn", "shf"),  # Net Radiation from SHF
    ("SWin", "co2"),  # Shortwave Incoming Radiation from CO2
    ("Ta", "shf"),  # Air Temperature (same in both, use SHF)
]

n_selected_drivers = len(selected_drivers)
tower_names = ["RU-Che", "RU-Ch2"]
n_towers = 2

# Create grid: rows=drivers, cols=towers
fig, axes = plt.subplots(
    n_selected_drivers,
    n_towers,
    figsize=(6 * n_towers, 2.8 * n_selected_drivers),
    constrained_layout=True,
    sharey="row",  # Share y-axis within each row
    sharex="col",
)  # Share x-axis within each column

# Define colors for each tower
tower_colors = ["#1f77b4", "#ff7f0e"]  # Blue for RU-Che, Orange for RU-Ch2

# Plot each combination
for driver_idx, (var_pattern, dataset_type) in enumerate(selected_drivers):
    for tower_idx in range(n_towers):
        ax = axes[driver_idx][tower_idx]

        # Get the appropriate dataset
        if dataset_type == "shf":
            tower_key = f"shf_cherskii_twr{tower_idx + 1}"
            data = shf_tower_data[tower_key]
        else:  # co2
            tower_key = f"co2_cherskii_twr{tower_idx + 1}"
            data = co2_tower_data[tower_key]

        # Construct the variable name with tower number
        # Variable names follow pattern: Rn_1_1_1, Rn_2_1_1, etc.
        var_name = f"{var_pattern}_{tower_idx + 1}_1_1"

        # Find the driver index for this variable
        driver_var_idx = data["driver_names"].index(var_name)

        # Plot the data
        ax.plot(
            data["time"],
            data["drivers"][..., driver_var_idx],
            "o",
            c=tower_colors[tower_idx],
            markeredgecolor="k",
            alpha=0.6,
            markersize=4,
        )

        # Format grid
        ts_plotter.add_grid(ax)

        # Tower name as title on top row only
        if driver_idx == 0:
            ax.set_title(tower_names[tower_idx], fontsize=style.fontsize["title"])

        # Driver name as y-label on leftmost column only
        if tower_idx == 0:
            # Use the first tower's variable name for the label
            label_var = f"{var_pattern}_1_1_1"
            ax.set_ylabel(labels.get_label(label_var), fontsize=style.fontsize["label"])

        # X-label only on bottom row
        if driver_idx == n_selected_drivers - 1:
            ax.set_xlabel("Time", fontsize=style.fontsize["label"])

# Apply concise date formatting
import matplotlib.dates as mdates

for ax in axes.flatten():
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.get_offset_text().set_visible(True)

# Only show x-tick labels on bottom row
for driver_idx in range(n_selected_drivers):
    for tower_idx in range(n_towers):
        if driver_idx < n_selected_drivers - 1:  # Not bottom row
            axes[driver_idx][tower_idx].tick_params(labelbottom=False)

fig.autofmt_xdate()
fig.suptitle(
    "Driver Variables Comparison Across Towers", fontsize=style.fontsize["suptitle"]
)
plt.savefig(plot_dir / "combined_drivers_comparison.pdf")
plt.show()

# %%
#############################################################
# Timeseries Drivers - Original Layout (Optional)
# Rows=Drivers, Cols=Towers
#############################################################

# Toggle: Set to True to merge both towers into single plots
MERGE_DRIVERS = False

n_drivers = len(tower_data[towers[0]]["driver_names"])
driver_names = tower_data[towers[0]]["driver_names"]

if MERGE_DRIVERS:
    # Merged view: single column with both towers on same axes
    fig, axes = plt.subplots(
        n_drivers, 1, figsize=(8, 3.2 * n_drivers), constrained_layout=True, sharex=True
    )

    # Handle single driver case
    if n_drivers == 1:
        axes = [axes]

    # Define colors for each tower
    tower_colors = ["#1f77b4", "#ff7f0e"]  # Blue for RU-Che, Orange for RU-Ch2
    tower_names = ["RU-Che", "RU-Ch2"]

    # Track if we need to show legend (only if there are differing drivers)
    legend_added = False

    # Plot each driver with both towers
    for driver_idx in range(n_drivers):
        ax = axes[driver_idx]

        # Check if driver data is the same between towers
        towers_list = list(tower_data.items())
        data_0 = towers_list[0][1]["drivers"][..., driver_idx]
        data_1 = towers_list[1][1]["drivers"][..., driver_idx]

        # Check if data is identical (allowing for small numerical differences)
        # First check if shapes match, if not they can't be shared
        if data_0.shape != data_1.shape:
            is_shared = False
        else:
            is_shared = np.allclose(
                data_0, data_1, rtol=1e-9, atol=1e-9, equal_nan=True
            )

        if is_shared:
            # Shared driver: plot only once in gray
            ax.plot(
                towers_list[0][1]["time"],
                data_0,
                "o",
                c="gray",
                markeredgecolor="k",
                alpha=0.6,
                markersize=4,
                label="Shared",
            )
        else:
            # Different data: plot both towers with colors
            for tower_idx, (tower, data) in enumerate(tower_data.items()):
                ax.plot(
                    data["time"],
                    data["drivers"][..., driver_idx],
                    "o",
                    c=tower_colors[tower_idx],
                    label=tower_names[tower_idx],
                    markeredgecolor="k",
                    alpha=0.6,
                    markersize=4,
                )

            # Add legend to first non-shared driver
            if not legend_added:
                ax.legend(loc="upper right", fontsize=style.fontsize["legend"])
                legend_added = True

        # Format grid
        ts_plotter.add_grid(ax)

        # Driver name as y-label
        ax.set_ylabel(
            labels.get_label(driver_names[driver_idx]), fontsize=style.fontsize["label"]
        )

        # X-label only on bottom row
        if driver_idx == n_drivers - 1:
            ax.set_xlabel("Time", fontsize=style.fontsize["label"])

    # Apply concise date formatting
    import matplotlib.dates as mdates

    for ax in axes:
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.get_offset_text().set_visible(True)

    fig.autofmt_xdate()
    fig.suptitle("Drivers Comparison", fontsize=style.fontsize["suptitle"])
else:
    # Original view: separate columns for each tower
    # Create grid: rows=drivers, cols=towers
    fig, axes = plt.subplots(
        n_drivers,
        len(towers),
        figsize=(6 * len(towers), 3.5 * n_drivers),
        constrained_layout=True,
        sharey="row",  # Share y-axis within each row
        sharex="col",
    )  # Share x-axis within each column

    # Handle single tower or single driver case
    if n_drivers == 1 and len(towers) == 1:
        axes = [[axes]]
    elif n_drivers == 1:
        axes = [axes]
    elif len(towers) == 1:
        axes = [[ax] for ax in axes]

    # Plot each driver-tower combination
    for driver_idx in range(n_drivers):
        for tower_idx, (tower, data) in enumerate(tower_data.items()):
            ax = axes[driver_idx][tower_idx]

            # Plot this driver's data
            ax.plot(
                data["time"],
                data["drivers"][..., driver_idx],
                "o",
                c="gray",
                markeredgecolor="k",
                alpha=0.6,
                markersize=4,
            )

            # Format grid
            ts_plotter.add_grid(ax)

            # Tower name as title on top row only
            if driver_idx == 0:
                tower_name = "RU-Che" if tower_idx == 0 else "RU-Ch2"
                ax.set_title(tower_name, fontsize=style.fontsize["title"])

            # Driver name as y-label on leftmost column only
            if tower_idx == 0:
                ax.set_ylabel(
                    labels.get_label(driver_names[driver_idx]),
                    fontsize=style.fontsize["label"],
                )

            # X-label only on bottom row
            if driver_idx == n_drivers - 1:
                ax.set_xlabel("Time", fontsize=style.fontsize["label"])

    # Apply concise date formatting to the entire figure (handles sharex correctly)
    import matplotlib.dates as mdates

    # Flatten the axes array (handles both 2D arrays and lists of lists)
    if isinstance(axes, np.ndarray):
        axes_flat = axes.flatten()
    else:
        axes_flat = [
            ax for row in axes for ax in (row if isinstance(row, list) else [row])
        ]

    for ax in axes_flat:
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        # Make sure the offset text (month/year) is visible
        ax.xaxis.get_offset_text().set_visible(True)

    # Only show x-tick labels on bottom row
    for driver_idx in range(n_drivers):
        for tower_idx in range(len(towers)):
            ax = axes[driver_idx][tower_idx]
            if driver_idx < n_drivers - 1:  # Not bottom row
                ax.tick_params(labelbottom=False)

    fig.autofmt_xdate()  # Rotate and align date labels
    fig.suptitle("Drivers Comparison", fontsize=style.fontsize["suptitle"])
plt.savefig(plot_dir / f"{obs_var}_timeseries_drivers_comparison.pdf")
plt.show()

# %%
#############################################################
# Timeseries Fluxes - Side by Side Using Plotter
#############################################################

import matplotlib.dates as mdates

fig, axes = plt.subplots(
    1, len(towers), figsize=(6 * len(towers), 5), constrained_layout=True, sharey=True
)  # Share y-axis across all panels

for col_idx, (tower, data) in enumerate(tower_data.items()):
    ax = axes[col_idx] if len(towers) > 1 else axes

    tower_name = "RU-Che" if col_idx == 0 else "RU-Ch2"

    ts_plotter.plot_fluxes_on_ax(
        ax=ax,
        time=data["time"],
        target=data["target"],
        target_name=data["target_name"],
        flux_dict=data["flux_dict"],
        I_gtyp=data["I_gtyp"],
        synth_flux=None,
        title=tower_name,
        show_legend=False,  # Don't show legend on individual panels
        add_ylabel=(col_idx == 0),  # Only show y-label on first panel
        land_cover_names=data[
            "run_config"
        ].landcover.land_cover_names,  # Use actual land cover names
    )

# Apply concise date formatting to all axes (day on tick, month/year as offset)
axes_list = axes if isinstance(axes, np.ndarray) else [axes]
for ax in axes_list:
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    # Make sure the offset text (month/year) is visible
    ax.xaxis.get_offset_text().set_visible(True)

# Get legend handles from the first axis (they're all the same)
first_ax = axes[0] if isinstance(axes, np.ndarray) else axes
handles, labels_list = first_ax.get_legend_handles_labels()

fig.suptitle("Flux Comparison", fontsize=style.fontsize["suptitle"])

# Create a single legend below center
fig.legend(
    handles,
    labels_list,
    loc="outside lower center",
    ncol=len(handles),  # All items in one row
    framealpha=0.9,
    fontsize=style.fontsize["legend"],
)

fig.autofmt_xdate()  # Rotate and align date labels

plt.savefig(
    plot_dir / f"{obs_var}_timeseries_fluxes_comparison.pdf", bbox_inches="tight"
)
plt.show()

# %%
#############################################################
# Environmental Response Functions - Using Plotter for Each Tower
#############################################################

# for tower, data in tower_data.items():
#     fig, axes = erf_plotter.plot_erf_multipanel(
#         drivers=data['drivers'],
#         driver_names=data['driver_names'],
#         target=data['target'],
#         target_name=data['target_name'],
#         flux_dict=data['flux_dict'],
#         I_gtyp=data['I_gtyp'],
#         synth_flux=None,
#         suptitle=f"Environmental Response Functions - {tower}"
#     )

#     plt.savefig(f"plots/{obs_var}_erf_{tower}.pdf", bbox_inches='tight')
#     plt.show()

# %%
#############################################################
# ERF Comparison Grid - Rows=Drivers, Cols=Towers
# Using the ERF plotter infrastructure!
#############################################################

from matplotlib.gridspec import GridSpec

towers_list = list(tower_data.items())
n_towers = len(towers_list)
n_drivers = len(towers_list[0][1]["driver_names"])
I_gtyp = towers_list[0][1]["I_gtyp"]
driver_names = towers_list[0][1]["driver_names"]

# Build GridSpec with colorbars on the right
# Layout: tower panels, gap, then colorbars
width_ratios = []
panel_indices = []  # Track which GridSpec column corresponds to each tower panel

for tower_idx in range(n_towers):
    panel_indices.append(len(width_ratios))
    width_ratios.append(20)  # Panel width
    if tower_idx < n_towers - 1:
        width_ratios.append(0)  # Gap between towers

# Add gap before colorbars
width_ratios.append(0.0)

# Add colorbars
cbar_start_idx = len(width_ratios)
for i in range(I_gtyp):
    width_ratios.append(0.625)  # Colorbar width

# Create figure with GridSpec
fig = plt.figure(figsize=(6 * n_towers, 4 * n_drivers), constrained_layout=True)
gs = GridSpec(
    n_drivers,
    len(width_ratios),
    figure=fig,
    width_ratios=width_ratios,
    wspace=0.05,
    left=0.065,
    right=0.94,
    top=0.92,
    bottom=0.1,
    hspace=0.2,
)

# Create axes array
axes = []
all_scatter_collections = {}

for driver_idx in range(n_drivers):
    row_axes = []
    for tower_idx, (tower, data) in enumerate(towers_list):
        # Share y-axis within each row
        sharey = row_axes[0] if tower_idx > 0 else None
        ax = fig.add_subplot(gs[driver_idx, panel_indices[tower_idx]], sharey=sharey)
        row_axes.append(ax)

        # Get the other driver for coloring
        color_driver_idx = (driver_idx + 1) % n_drivers

        # Use the ERF plotter infrastructure!
        scatter_collections = erf_plotter.plot_erf_single_on_ax(
            ax=ax,
            x_driver=data["drivers"][..., driver_idx],
            x_driver_name=driver_names[driver_idx],
            color_driver=data["drivers"][..., color_driver_idx],
            color_driver_name=driver_names[color_driver_idx],
            target=data["target"],
            target_name=data["target_name"],
            flux_dict=data["flux_dict"],
            I_gtyp=I_gtyp,
            synth_flux=None,
            show_labels=(
                driver_idx == 0 and tower_idx == 0
            ),  # Only show legend on first panel
            add_ylabel=(tower_idx == 0),  # Y-label only on left column
            land_cover_names=data["run_config"].landcover.land_cover_names,
        )

        all_scatter_collections[(driver_idx, tower_idx)] = scatter_collections

        # Add tower name as title on top row
        if driver_idx == 0:
            tower_name = "RU-Che" if tower_idx == 0 else "RU-Ch2"
            ax.set_title(tower_name, fontsize=style.fontsize["title"])

        # Remove y-tick labels for non-leftmost columns
        if tower_idx > 0:
            ax.tick_params(labelleft=False)

    axes.append(row_axes)

lc_names = tower_data[towers[0]]["run_config"].landcover.land_cover_short_names

# Add colorbars on the right side
for driver_idx in range(n_drivers):
    # Use scatter collections from the rightmost tower for this driver
    scatter_collections = all_scatter_collections[(driver_idx, n_towers - 1)]

    for i in range(I_gtyp):
        sc = scatter_collections[i]

        # Create colorbar axis in the GridSpec
        cbar_ax = fig.add_subplot(gs[driver_idx, cbar_start_idx + i])
        cbar = fig.colorbar(sc, cax=cbar_ax)

        # Label only the last colorbar
        if i == I_gtyp - 1:
            # Color driver is the "other" driver
            color_driver_idx = (driver_idx + 1) % n_drivers
            color_var_name = driver_names[color_driver_idx]
            cbar.set_label(
                labels.get_label(color_var_name),
                rotation=270,
                labelpad=15,
                fontsize=style.fontsize["label"],
            )

        # Get land cover name for this colorbar
        cbar_ax.set_xlabel(f"{lc_names[i]}", rotation=270, fontsize=13)

        if i < I_gtyp - 1:
            cbar.ax.set_yticklabels([])
            cbar.ax.tick_params(length=0)

# Add legend
handles, labels_list = axes[0][0].get_legend_handles_labels()
fig.legend(
    handles,
    labels_list,
    loc="outside lower center",
    ncol=4,
    bbox_to_anchor=(0.5, 0.0),
    framealpha=0.9,
    fontsize=style.fontsize["legend"],
)

fig.suptitle(
    "Environmental Response Functions - Tower Comparison",
    fontsize=style.fontsize["suptitle"],
)

plt.savefig(plot_dir / f"{obs_var}_erf_comparison_grid.pdf", bbox_inches="tight")
plt.show()

# %%
#############################################################
# Flux Comparison Between Towers
#############################################################
twr1_data = tower_data[towers[0]]
twr2_data = tower_data[towers[1]]

# Create dataframes with time index
df_1 = pd.DataFrame(twr1_data["flux_dict"])
df_1["timestamp"] = twr1_data["time"]
df_1.set_index("timestamp", inplace=True)

df_2 = pd.DataFrame(twr2_data["flux_dict"])
df_2["timestamp"] = twr2_data["time"]
df_2.set_index("timestamp", inplace=True)

# Merge datasets on timestamp
df_merged = pd.merge(
    df_1, df_2, left_index=True, right_index=True, how="inner", suffixes=("_1", "_2")
)

# Prepare flux dictionaries for comparison
I_gtyp_comp = twr1_data["I_gtyp"]
flux1_dict = {
    f"flux_lc{i}": df_merged[f"flux_lc{i}_1"].values for i in range(I_gtyp_comp)
}
flux2_dict = {
    f"flux_lc{i}": df_merged[f"flux_lc{i}_2"].values for i in range(I_gtyp_comp)
}

# Create comparison plot
fig, ax = ts_plotter.plot_comparison(
    flux1_dict=flux1_dict,
    flux2_dict=flux2_dict,
    label1=f"{labels.get_label(twr1_data['target_name'])} of RU-Che",
    label2=f"{labels.get_label(twr2_data['target_name'])} of RU-Ch2",
    title=f"Flux comparison between RU-Che and RU-Ch2",
    land_cover_names=twr1_data["run_config"].landcover.land_cover_names,
)

output_fn = f"flux_comparison_{towers[0]}_vs_{towers[1]}"
plt.savefig(plot_dir / f"{obs_var}_{output_fn}.pdf")
plt.show()

print("\nAll plots generated successfully!")
