import datetime as dt

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable

from main import env, spacecraft

wong_colours = {
    "black": "black",
    "orange": "#E69F00",
    "light blue": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "red": "#D55E00",
    "pink": "#CC79A7",
}

times = (dt.datetime(2027, 8, 1, 17), dt.datetime(2027, 8, 1, 21))

# Get Data
mpo = spacecraft("mpo")
mpo.update_trajectory(*times, dt.timedelta(minutes=5))
mpo.update_probabilities()

mmo = spacecraft("mmo")
mmo.update_trajectory(*times, dt.timedelta(minutes=5))
mmo.update_probabilities()

mmo.region_probabilities.to_csv("~/test.csv")
mmo.trajectory.to_csv("~/test-other.csv")

# Plot probability time series
fig, axes = plt.subplots(2, 1, sharex=True)
mpo_ax, mmo_ax = axes

mpo_ax.plot(
    mpo.region_probabilities["Time"],
    mpo.region_probabilities["Solar Wind"],
    color=wong_colours["yellow"],
)
mpo_ax.plot(
    mpo.region_probabilities["Time"],
    mpo.region_probabilities["Magnetosheath"],
    color=wong_colours["orange"],
)
mpo_ax.plot(
    mpo.region_probabilities["Time"],
    mpo.region_probabilities["Magnetosphere"],
    color=wong_colours["blue"],
)

mmo_ax.plot(
    mmo.region_probabilities["Time"],
    mmo.region_probabilities["Solar Wind"],
    color=wong_colours["yellow"],
    label="P(Solar Wind)",
)
mmo_ax.plot(
    mmo.region_probabilities["Time"],
    mmo.region_probabilities["Magnetosheath"],
    color=wong_colours["orange"],
    label="P(Magnetosheath)",
)
mmo_ax.plot(
    mmo.region_probabilities["Time"],
    mmo.region_probabilities["Magnetosphere"],
    color=wong_colours["blue"],
    label="P(Magnetosphere)",
)

mmo_ax.legend()

mmo_ax.text(0, 1, "MMO", color=wong_colours["pink"], transform=mmo_ax.transAxes)
mpo_ax.text(0, 1, "MPO", color=wong_colours["light blue"], transform=mpo_ax.transAxes)

for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
    ax.set_ylabel("Region Probability")


# Plot trajectories
# First load the messenger dataset
region_predictions = pd.read_csv(
    f"{env.WAMMSDIR}/data/messenger_region_observations.csv"
)

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

ax.set_ylabel(
    r"$\left( Y_{\text{MSM'}}^2 + Z_{\text{MSM'}}^2 \right)^{0.5} \quad \left[ \text{R}_\text{M} \right]$"
)
ax.set_ylim(0, cyl_bins[-1])
# Set ax background hatching
ax.axvspan(*ax.get_xlim(), color="#648FFF", alpha=0.1, zorder=-1)
ax.set_title("MESSENGER's Residence")

# Create plot
all_axes = axes.flatten()
axes = axes.flatten()[1:]

for ax, region_name in zip(axes, region_data["Names"]):

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

    # Set ax background
    ax.axvspan(*ax.get_xlim(), color="#648FFF", alpha=0.1, zorder=-1)

# Overplot trajectories onto each panel
for ax in all_axes:

    ax.plot(
        mpo.trajectory["X MSM'"],
        mpo.trajectory["CYL MSM'"],
        color=wong_colours["light blue"],
    )
    ax.plot(
        mmo.trajectory["X MSM'"], mmo.trajectory["CYL MSM'"], color=wong_colours["pink"]
    )

    ax.annotate(
        "",
        xytext=(
            mpo.trajectory["X MSM'"].iloc[len(mpo.trajectory) // 2 - 1],
            mpo.trajectory["CYL MSM'"].iloc[len(mpo.trajectory) // 2 - 1],
        ),
        xy=(
            mpo.trajectory["X MSM'"].iloc[len(mpo.trajectory) // 2],
            mpo.trajectory["CYL MSM'"].iloc[len(mpo.trajectory) // 2],
        ),
        arrowprops=dict(arrowstyle="-|>", color=wong_colours["light blue"]),
    )

    ax.annotate(
        "",
        xytext=(
            mmo.trajectory["X MSM'"].iloc[len(mmo.trajectory) // 2 - 1],
            mmo.trajectory["CYL MSM'"].iloc[len(mmo.trajectory) // 2 - 1],
        ),
        xy=(
            mmo.trajectory["X MSM'"].iloc[len(mmo.trajectory) // 2],
            mmo.trajectory["CYL MSM'"].iloc[len(mmo.trajectory) // 2],
        ),
        arrowprops=dict(arrowstyle="-|>", color=wong_colours["pink"]),
    )


plt.show()
