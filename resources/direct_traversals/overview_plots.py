"""
Script to investigate direct sheath traversals statistically
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hermpy.plotting import wong_colours

# We first want to load the sheath traversals data set
traversals = pd.read_csv("../data/direct_sheath_traversals.csv", index_col=0)
# traversals = pd.read_csv("../data/direct_sheath_traversals_philpott.csv", index_col=0)

inbound_traversals = traversals.loc[traversals["Direction"] == "Inbound"]
outbound_traversals = traversals.loc[traversals["Direction"] == "Outbound"]

fig, axes = plt.subplots(2, 1, sharex=True, sharey=True)

bins = np.linspace(0, np.max(traversals["Length (seconds)"]) / 3600, 30)

# To be able to change the order of panels around easily, we leave everything
# in terms of ax, and simply redefine it each time.

# Distribution of traversal length
ax = axes[0]

ax.hist(
    traversals["Length (seconds)"] / 3600,
    color="black",
    histtype="step",
    linewidth=3,
    label=f"All Magnetosheath Traversals (N={len(traversals)})",
    bins=bins,
)
ax.hist(
    inbound_traversals["Length (seconds)"] / 3600,
    color=wong_colours["orange"],
    histtype="step",
    linewidth=3,
    label=f"Inbound Only (N={len(inbound_traversals)})",
    bins=bins,
)
ax.hist(
    outbound_traversals["Length (seconds)"] / 3600,
    color=wong_colours["light blue"],
    histtype="step",
    linewidth=3,
    label=f"Outbound Only (N={len(outbound_traversals)})",
    bins=bins,
)

# Split by local time quadrants
ax = axes[1]

local_time_quads = [(9, 15), (15, 21), (21, 3), (3, 9)]
local_time_labels = ["Noon", "Dusk", "Midnight", "Dawn"]
local_time_colors = ["red", "orange", "blue", "pink"]

ax.hist(
    traversals["Length (seconds)"] / 3600,
    color="black",
    histtype="step",
    linewidth=3,
    label=f"All Magnetosheath Traversals (N={len(traversals)})",
    bins=bins,
)

for bounds, label, colour in zip(
    local_time_quads, local_time_labels, local_time_colors
):

    # We have to factor for moving across 0 at midnight
    if label == "Midnight":
        filtered_traversals = traversals.loc[
            (traversals["Local Time (hrs)"] > bounds[0])
            | (traversals["Local Time (hrs)"] < bounds[1])
        ]
    else:
        filtered_traversals = traversals.loc[
            traversals["Local Time (hrs)"].between(*bounds)
        ]

    ax.hist(
        filtered_traversals["Length (seconds)"] / 3600,
        color=wong_colours[colour],
        histtype="step",
        linewidth=3,
        label=f"{label} (N={len(filtered_traversals)})",
        bins=bins,
    )


axes[-1].set_xlabel("Traversal Time [hours]")

for ax in axes:
    ax.set_yscale("log")
    ax.set_ylabel("Occurance")
    ax.margins(x=0)

    ax.legend()

plt.show()

# New plot entirely, to look at latitude / local time covariance with length

fig, ax = plt.subplots()

latitude_bins = np.linspace(
    traversals["Magnetic Latitude (deg.)"].min(),
    traversals["Magnetic Latitude (deg.)"].max(),
    10,
)
local_time_bins = np.arange(0, 24 + 1, 1)

hist, latitude_edges, local_time_edges = np.histogram2d(
    traversals["Magnetic Latitude (deg.)"],
    traversals["Local Time (hrs)"],
    bins=[latitude_bins, local_time_bins],
    weights=traversals["Length (seconds)"],
)

mesh = ax.pcolormesh(
    local_time_edges, latitude_edges, hist, shading="auto", cmap="viridis"
)

fig.colorbar(mesh, label="Summed Magnetosheath Length [seconds]")

ax.set_xlabel("Local Time [hrs]")
ax.set_ylabel("Magnetic Latitude [deg.]")

plt.show()
