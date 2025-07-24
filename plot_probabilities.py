import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hermpy import plotting
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Set limits on heliocentric distance. If either are set to -1, that bound will be ignored
heliocentric_distance_bounds = [-1, -1]
# heliocentric_distance_bounds = [0.3, 0.33]
# heliocentric_distance_bounds = [0.44, 0.47]

# First load the messenger dataset
region_predictions = pd.read_csv("./messenger_region_observations.csv")

# Convert heliocentric distance from km to AU
region_predictions["Heliocentric Distance"] = (
    region_predictions["Heliocentric Distance"] * 6.684587e-9
)

# Limit in heliocentric distance
if heliocentric_distance_bounds[0] == -1:
    heliocentric_distance_bounds[0] = np.min(
        region_predictions["Heliocentric Distance"]
    )

if heliocentric_distance_bounds[1] == -1:
    heliocentric_distance_bounds[1] = np.max(
        region_predictions["Heliocentric Distance"]
    )

region_predictions = region_predictions.loc[
    region_predictions["Heliocentric Distance"].between(*heliocentric_distance_bounds)
]

# Create bins
bin_size = 0.25
x_bins = np.arange(-5, 5 + bin_size, bin_size)  # Radii
cyl_bins = np.arange(0, 8 + bin_size, bin_size)  # Radii

# Make histograms for each region prediction
region_data = {"Names": ["Solar Wind", "Magnetosheath", "Magnetosphere"], "Data": {}}

x_edges = []  # Just initialising to avoid LSP unbound variable errors
y_edges = []
for region_name in region_data["Names"]:

    filtered_predictions = region_predictions.loc[
        region_predictions["Predicted Region"] == region_name
    ][["X MSM' (radii)", "CYL MSM' (radii)"]]

    region_histogram, x_edges, y_edges = np.histogram2d(
        filtered_predictions["X MSM' (radii)"],
        filtered_predictions["CYL MSM' (radii)"],
        bins=[x_bins, cyl_bins],
    )

    region_data["Data"][region_name] = region_histogram

bin_totals = np.sum(list(region_data["Data"].values()), axis=0)

# Create totals (residence) plot
fig, axes = plt.subplots(2, 2, sharex=True, sharey=True)

ax = axes[0][0]

plotting.Format_Cylindrical_Plot(ax, size=5)

mesh = ax.pcolormesh(
    x_edges,
    y_edges,
    bin_totals.T
    * 5
    / 3600,  # Each count here represents 5 seconds of data (as determined in the dataset generating script)
    cmap="binary_r",
    shading="auto",
    norm="log",
    zorder=0,
)
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0)
fig.colorbar(mesh, cax=cax, label=f"Hours")

ax.set_xlabel(r"$X_{\rm MSM'}$ [$R_M$]")
ax.set_ylabel(
    r"$\left( Y_{\text{MSM'}}^2 + Z_{\text{MSM'}}^2 \right)^{0.5} \quad \left[ \text{R}_\text{M} \right]$"
)
ax.set_ylim(0, cyl_bins[-1])
# Set ax background hatching
ax.axvspan(*ax.get_xlim(), color="#648FFF", alpha=0.3, zorder=-1)
ax.set_title("MESSENGER's Residence")

# Create plot
axes = axes.flatten()[1:]

for ax, region_name in zip(axes, region_data["Names"]):

    plotting.Format_Cylindrical_Plot(ax, size=5)

    region_ratio = region_data["Data"][region_name] / bin_totals

    mesh = ax.pcolormesh(
        x_edges,
        y_edges,
        region_ratio.T,
        vmin=0,
        vmax=1,
        cmap="binary_r",
        shading="auto",
        zorder=0,
    )
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0)
    fig.colorbar(mesh, cax=cax, label=f"P({region_name})")

    ax.set_title(f"{region_name}")

    if ax == axes[1]:
        ax.set_ylabel(
            r"$\left( Y_{\text{MSM'}}^2 + Z_{\text{MSM'}}^2 \right)^{0.5} \quad \left[ \text{R}_\text{M} \right]$"
        )

    else:
        ax.set_ylabel("")

    if ax in axes[1:]:
        ax.set_xlabel(r"$X_{\rm MSM'}$ [$R_M$]")

    ax.set_ylim(0, cyl_bins[-1])

    # Set ax background hatching
    ax.axvspan(*ax.get_xlim(), color="#648FFF", alpha=0.3, zorder=-1)

plt.show()
