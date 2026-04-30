"""
Refactored visualization script using the new plotting module.

This script replaces the original vis_flugs.py with cleaner, class-based plotting.
"""

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from flugs.prepare import get_data
from flugs.utils.response_functions import ERF
from flugs.config import DATA_DIR, OUTPUT_DIR
from flugs.utils.io import get_latest_run_dir
from flugs.plotting import (
    StyleManager,
    LabelManager,
    TimeSeriesPlotter,
    ResponsePlotter,
    SpatialPlotter,
)

# Load data from FLUGS yaml
run_config, sim_data = get_data(config="synth")

run_dir = get_latest_run_dir(OUTPUT_DIR, run_config.run_name)
plot_dir = run_dir / "plots"

csv_fn_flugs = run_dir / f"{run_config.run_name}_flugs.csv"
df = pd.read_csv(csv_fn_flugs)

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
land_cover_names = run_config.landcover.land_cover_names
# flux_dict = {land_cover_names[i]: df[f"flux_lc{i}"].values for i in range(I_gtyp)}
flux_dict = {f"flux_lc{i}": df[f"flux_lc{i}"].values for i in range(I_gtyp)}

# Prepare synthetic flux data if applicable
synth_flux = None
if run_config.run_name == "synth":
    synth_flux = np.zeros((len(df), I_gtyp))
    for i in range(I_gtyp):
        synth_flux[..., i] = ERF(drivers[..., 0], drivers[..., 1], i)

# Initialize plotters
style = StyleManager()
labels = LabelManager(f"{DATA_DIR}/variables_metadata.toml")
ts_plotter = TimeSeriesPlotter(style, labels)
erf_plotter = ResponsePlotter(style, labels)
lcm_plotter = SpatialPlotter(style, labels)

run_config.landcover.land_cover_names = None

# %%
#############################################################
# Land Cover Map
#############################################################
if run_config.run_name == "synth":
    land_cover_stack = np.nanmax(sim_data.land_cover_by_group, axis=0)
    fig, axes = lcm_plotter.plot_field2d(
        land_cover_stack,
        xmx=sim_data.grid.xmx,
        ymx=sim_data.grid.ymx,
        lon_ext=run_config.dataset.longitude_extent,
        lat_ext=run_config.dataset.latitude_extent,
        zm=0.0,
        title=f"Stochastic land cover map",
        marker_loc=sim_data.grid.measurement_point,
        set_land_cover_names=False,
    )
    plt.savefig(plot_dir / "stochastic_lcm.pdf")
    plt.show()
else:
    pass

# %%

#############################################################
# Timeseries driver
#############################################################

fig, axes = ts_plotter.plot_drivers(
    time=time,
    drivers=drivers,
    driver_names=run_config.dataset.driver_variables,
    suptitle="Time series of synthetic drivers",
)

output_fn = f"timeseries_{run_config.run_name}"
plt.savefig(plot_dir / f"{output_fn}.pdf")
plt.show()

#############################################################
# Timeseries fluxes
#############################################################

fig, ax = ts_plotter.plot_fluxes(
    time=time,
    target=target,
    target_name=target_name,
    flux_dict=flux_dict,
    synth_flux=synth_flux,
    I_gtyp=I_gtyp,
    # land_cover_names=land_cover_names,
)

ax.set_title("Time series of synthetic fluxes", fontsize=style.fontsize["title"])

output_fn = f"timeseries_fluxes_{run_config.run_name}"
plt.savefig(plot_dir / f"{output_fn}.pdf")
plt.show()

#############################################################
# Environmental Response Function
#############################################################

fig, axes = erf_plotter.plot_erf_multipanel(
    drivers=drivers,
    driver_names=run_config.dataset.driver_variables,
    target=target,
    target_name=target_name,
    flux_dict=flux_dict,
    I_gtyp=I_gtyp,
    synth_flux=synth_flux,
    suptitle="Synthetic environmental response functions",
    figsize_per_panel=6.0,
    fig_height=5.0,
    margins=(0.06, 0.94, 0.92, 0.20),
    # land_cover_names=land_cover_names,
)

output_fn = f"erf_{run_config.run_name}"
plt.savefig(plot_dir / f"{output_fn}.pdf", bbox_inches="tight")
plt.show()

#############################################################
# Flux comparison (Real vs Learned for synthetic data)
#############################################################

if run_config.run_name == "synth":
    # Create flux dictionaries for real (synthetic) and learned fluxes
    flux_real_dict = {land_cover_names[i]: synth_flux[..., i] for i in range(I_gtyp)}
    flux_learned_dict = {
        land_cover_names[i]: df[f"flux_lc{i}"].values for i in range(I_gtyp)
    }

    # Use the comparison plotter
    fig, ax = ts_plotter.plot_comparison(
        flux1_dict=flux_real_dict,
        flux2_dict=flux_learned_dict,
        label1=f"Real flux ({labels.get_label(target_name)})",
        label2=f"Learned flux ({labels.get_label(target_name)})",
        title=f"Comparison between learned and synthetic fluxes",
        # land_cover_names=land_cover_names
    )

    output_fn = f"flux_comparison_{run_config.run_name}"
    plt.savefig(plot_dir / f"{output_fn}.pdf")
    plt.show()
