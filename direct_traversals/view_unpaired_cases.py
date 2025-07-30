"""
There are some cases where there is no pair determined for a given inbound or
outbound traversal. We want to look at these and determine why that was
"""

import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hermpy import boundaries, mag, plotting, utils
from hermpy.plotting import wong_colours

# Load the crossing lists we want to plot later
philpott_intervals = boundaries.Load_Crossings(utils.User.CROSSING_LISTS["Philpott"])

hollman_crossings = pd.read_csv("../data/hollman_2025_crossing_list.csv")
hollman_crossings["Time"] = pd.to_datetime(hollman_crossings["Times"])


def main():

    # Load the traversals dataset
    traversals = pd.read_csv("../data/direct_sheath_traversals.csv", index_col=0)
    # traversals = pd.read_csv("../data/direct_sheath_traversals_philpott.csv", index_col=0)

    traversals["Start Time"] = pd.to_datetime(traversals["Start Time"])
    traversals["End Time"] = pd.to_datetime(traversals["End Time"])

    # We loop through these, if there are consecutive entries, then a traversal was
    # missed and we should investigate
    missing_pairs = []
    for i in range(len(traversals)):

        current_traversal = traversals.iloc[i]

        try:
            next_traversal = traversals.iloc[i + 1]
        except:
            break

        # If the directions are not the same, skip
        if current_traversal["Direction"] != next_traversal["Direction"]:
            continue

        # If the directions are the same, we have a missing traversal
        # Create a figure
        missing_pairs.append(current_traversal)

    # The first 19 missing pair events are for a sequence of orbits between May
    # and June of 2011, where MAG data are unavailable inside the
    # magnetosphere. Philpott intervals skip the output magnetopause crossing
    # in these cases.
    print(len(missing_pairs))
    missing_pairs = missing_pairs[19:]

    for i, traversal in enumerate(missing_pairs):
        print(i)
        create_figure(traversal)


def create_figure(traversal):

    # Load data for this orbit (1 full orbit centered around this traversal)
    if traversal["Start Time"] < dt.datetime(2012, 4, 1):
        forward_buffer = dt.timedelta(hours=14)
    else:
        forward_buffer = dt.timedelta(hours=10)

    backward_buffer = dt.timedelta(hours=2)

    start = traversal["Start Time"] - backward_buffer
    end = traversal["Start Time"] + forward_buffer

    data = mag.Load_Between_Dates(utils.User.DATA_DIRECTORIES["MAG"], start, end)

    # Where a data gap is present, insert nan to make plotting ignore it
    new_rows = []
    for i, row in data.iterrows():

        try:
            next_row = data.iloc[i + 1]
        except:
            break

        if next_row["date"] - row["date"] > dt.timedelta(seconds=10):
            new_row = {"date": row["date"] + (next_row["date"] - row["date"]) / 2}
            new_rows.append(new_row)

    new_rows = pd.DataFrame(new_rows)
    data = pd.concat([data, new_rows], ignore_index=True).sort_values(
        "date", ignore_index=True
    )

    mag_ax = plt.subplot2grid((2, 3), (1, 0), colspan=3)

    # Plot the data!
    mag_ax.plot(
        data["date"], data["|B|"], color=wong_colours["black"], label="$|B|$", zorder=5
    )
    mag_ax.plot(data["date"], data["Bx"], color=wong_colours["red"], label="$B_x$")
    mag_ax.plot(data["date"], data["By"], color=wong_colours["green"], label="$B_y$")
    mag_ax.plot(data["date"], data["Bz"], color=wong_colours["blue"], label="$B_z$")

    mag_ax.set_ylabel("Magnetic Field Strength [nT]")

    mag_ax.margins(x=0)

    # Shade the traversal in grey
    mag_ax.axvspan(
        traversal["Start Time"],
        traversal["End Time"],
        color="grey",
        alpha=0.2,
        label="Inbound Magnetosheath Traversal",
    )

    mag_ax.legend()

    # Add Hollman 2025 crossing list
    crossings_in_interval = hollman_crossings.loc[
        hollman_crossings["Time"].between(start, end)
    ]

    for _, crossing in crossings_in_interval.iterrows():

        if "BS" in crossing["Label"]:
            mag_ax.axvline(
                crossing["Time"],
                color=plotting.wong_colours["light blue"],
                ls="dashed",
                label="BS Crossing (H25)",
            )
        else:
            mag_ax.axvline(
                crossing["Time"],
                color=plotting.wong_colours["pink"],
                ls="dashed",
                label="MP Crossing (H25)",
            )

    # Add Philpott intervals
    boundaries.Plot_Crossing_Intervals(mag_ax, start, end, philpott_intervals)

    # Add ephemeris information
    plotting.Add_Tick_Ephemeris(mag_ax)

    # TRAJECTORIES
    xy_axis = plt.subplot2grid((2, 3), (0, 0))
    xz_axis = plt.subplot2grid((2, 3), (0, 1))
    xc_axis = plt.subplot2grid((2, 3), (0, 2))  # Cylindrical

    trajectory_axes = (xy_axis, xz_axis, xc_axis)

    xy_axis.plot(data["X MSM' (radii)"], data["Y MSM' (radii)"], color="black")
    xz_axis.plot(data["X MSM' (radii)"], data["Z MSM' (radii)"], color="black")
    xc_axis.plot(
        data["X MSM' (radii)"],
        np.sqrt(data["Y MSM' (radii)"] ** 2 + data["Z MSM' (radii)"] ** 2),
        color="black",
    )

    xy_axis.set_ylim(-5, 5)
    xz_axis.set_ylim(-8, 2)
    xc_axis.set_ylim(0, 10)

    xy_axis.set_ylabel(r"$Y_{\rm MSM'}$ [$R_{\rm M}$]")
    xz_axis.set_ylabel(r"$Z_{\rm MSM'}$ [$R_{\rm M}$]")
    xc_axis.set_ylabel(
        r"$\left(Y_{\rm MSM'}^2 + Z_{\rm MSM'}^2\right)^{0.5}$ [$R_{\rm M}$]"
    )

    plotting.Plot_Circle(xy_axis, (0, 0), edgecolor="black")
    plotting.Plot_Circle(xz_axis, (0, -utils.Constants.DIPOLE_OFFSET_RADII), ec="black")
    plotting.Plot_Circle(xc_axis, (0, utils.Constants.DIPOLE_OFFSET_RADII), ec="black")
    plotting.Plot_Circle(xc_axis, (0, -utils.Constants.DIPOLE_OFFSET_RADII), ec="black")

    for ax in trajectory_axes:
        ax.set_xlim(-5, 5)

        ax.set_xlabel(r"$X_{\rm MSM'}$ [$R_{\rm M}$]")

        ax.set_aspect("equal")

        plotting.Plot_Magnetospheric_Boundaries(ax)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
