"""
Script to investigate direct sheath traversals statistically
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hermpy.plotting import wong_colours


def main():
    # We first want to load the sheath traversals data set
    traversals = pd.read_csv("../data/direct_sheath_traversals.csv", index_col=0)

    dayside_traversals = traversals.loc[traversals["Local Time (hrs)"].between(9, 15)]
    dawn_traversals = traversals.loc[traversals["Local Time (hrs)"].between(3, 9)]
    dusk_traversals = traversals.loc[traversals["Local Time (hrs)"].between(15, 21)]
    nightside_traversals = traversals.loc[
        (traversals["Local Time (hrs)"] > 21) | (traversals["Local Time (hrs)"] <= 3)
    ]

    # First we look at dayside vs nightside to test the method. We expect dayside
    # and nightside to have very different distributions in latitude and radial
    # distance.
    colours = ["red", "blue"]
    labels = ["9h ≤ LT ≤ 15h", "21h ≤ LT ≤ 3h"]
    title = "Dayside-Nightside Comparison"
    make_plot([dayside_traversals, nightside_traversals], title, labels, colours)

    colours = ["pink", "orange"]
    labels = ["3h ≤ LT ≤ 9h", "15h ≤ LT ≤ 21h"]
    title = "Dawn-Dusk Comparison"
    make_plot([dawn_traversals, dusk_traversals], title, labels, colours)


def make_plot(local_time_quads, title, labels, colours):
    fig, axes = plt.subplots(1, 2)
    latitude_ax, radial_ax = axes

    latitude_bin_size = 5  # degrees
    latitude_bins = np.arange(-90, 90 + latitude_bin_size, latitude_bin_size)

    radial_bin_size = 0.5  # RM
    radial_bins = np.arange(0.5, 8 + radial_bin_size, radial_bin_size)

    for quad, colour, label in zip(local_time_quads, colours, labels):
        latitude_ax.hist(
            quad["Magnetic Latitude (deg.)"],
            color=wong_colours[colour],
            label=label + "\n" + f"N={len(quad)}",
            histtype="step",
            linewidth=5,
            bins=latitude_bins,
            density=True,
        )

        radial_distance = np.sqrt(
            quad["X MSM' (radii)"] ** 2
            + quad["Y MSM' (radii)"] ** 2
            + quad["Z MSM' (radii)"] ** 2
        )
        radial_ax.hist(
            radial_distance,
            color=wong_colours[colour],
            label=label + "\n" + f"N={len(quad)}",
            histtype="step",
            linewidth=5,
            bins=radial_bins,
            density=True,
        )

    radial_ax.legend()

    latitude_ax.set_xlabel("Magnetic Latitude [deg.]")
    radial_ax.set_xlabel(
        r"$\left(X_{\rm MSM'}^2 + Y_{\rm MSM'}^2 + Z_{\rm MSM'}^2\right)^{0.5}$ [$R_{\rm M}$]"
    )

    fig.suptitle(title)

    for ax in axes:
        ax.margins(x=0)
        ax.set_ylabel("Occurrence")

    plt.show()


if __name__ == "__main__":
    main()
