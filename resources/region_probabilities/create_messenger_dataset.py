"""
We want to look at the chance of being in one of the three magnetospheric
regions for each spatial bin in the cylindrical plane.

We want three plots - one for each class - which use a matplotlib pcolormesh

We find what region MESSENGER was in for all time (at some specified
resolution), by checking the most recent crossing to have occurred.
"""

import numpy as np
import pandas as pd
from hermpy import mag, trajectory, utils

# We want to first load the entire MESSENGER MISSION
# It is most convenient to load the pre-saved mission file from hermpy
# This is at one second resolution.
messenger_ephemeris = mag.Load_Mission(utils.User.DATA_DIRECTORIES["FULL MISSION"])
messenger_ephemeris["Time"] = pd.to_datetime(messenger_ephemeris["date"])

# We want the option to downsample this to lower resolutions
downsample = 5  # seconds

if downsample != 1:
    messenger_ephemeris = messenger_ephemeris.iloc[::downsample, :].reset_index(
        drop=True
    )

# Get heliocentric distance for each point
messenger_ephemeris["Heliocentric Distance"] = trajectory.Get_Heliocentric_Distance(
    messenger_ephemeris["Time"].tolist()
)

# We can limit down to only the columns we want
messenger_ephemeris = messenger_ephemeris[
    [
        "Time",
        "Heliocentric Distance",
        "X MSM' (radii)",
        "Y MSM' (radii)",
        "Z MSM' (radii)",
    ]
]

# For each of these data-points, we want to know which region MESSENGER was in.
# To do this, we compare the times column to a list of crossings, and use the
# most recent crossing to determine the current region.

# Load Hollman et al. (in prep., 2025) crossing list
crossings = pd.read_csv(
    "/home/daraghhollman/Main/Work/mercury/Code/MESSENGER_Region_Detection/data/hollman_2025_crossing_list.csv"
)
crossings["Time"] = pd.to_datetime(crossings["Times"])

# Shorten the columns down to just what we need
crossings = crossings[["Time", "Label"]]

# Merge the two, finding the closest past crossing to each data point
backward_merge = pd.merge_asof(
    messenger_ephemeris, crossings, on="Time", direction="backward"
).rename(columns={"Label": "Previous Crossing Label"})
# But it is not sufficient to check only which crossing was before. In the case
# of intervals missing due to data gaps, or other anomalies, it is possible for
# the current region according to the previous crossing and the current region
# according to the next crossing to disagree. We should ignore these cases. We
# need to do two merges with the crossing list, one looking forward and one
# looking backwards.
forward_merge = pd.merge_asof(
    messenger_ephemeris, crossings, on="Time", direction="forward"
).rename(columns={"Label": "Next Crossing Label"})

# We have nan values as there are some data points before the first crossing.
# We could include these by basing them off of the next crossing, but I don't
# think it matters too much for the average behaviour per bin.
ephemeris_with_crossings = backward_merge.merge(
    forward_merge[["Time", "Next Crossing Label"]], on="Time"
).dropna()

# Write a look-up table: What region are we in based on the surrounding
# crossings
previous_crossing_table = {
    "BS_OUT": "Solar Wind",
    "BS_IN": "Magnetosheath",
    "MP_OUT": "Magnetosheath",
    "MP_IN": "Magnetosphere",
    "UNPHYSICAL (MSp -> SW)": "Solar Wind",
    "UNPHYSICAL (SW -> MSp)": "Magnetosphere",
}
next_crossing_table = {
    "BS_OUT": "Magnetosheath",
    "BS_IN": "Solar Wind",
    "MP_OUT": "Magnetosphere",
    "MP_IN": "Magnetosheath",
    "UNPHYSICAL (MSp -> SW)": "Magnteosphere",
    "UNPHYSICAL (SW -> MSp)": "Solar Wind",
}

# Add the region prediction and drop unneeded columns
ephemeris_with_crossings["Predicted Region (prev. crossing)"] = [
    previous_crossing_table[previous_crossing]
    for previous_crossing in ephemeris_with_crossings["Previous Crossing Label"]
]
ephemeris_with_crossings["Predicted Region (next crossing)"] = [
    next_crossing_table[next_crossing]
    for next_crossing in ephemeris_with_crossings["Next Crossing Label"]
]

# If the regions based on the crossing before, and the crossing after, don't agree, we just exclude these points.
length_before = len(ephemeris_with_crossings)

ephemeris_with_crossings = ephemeris_with_crossings.loc[
    ephemeris_with_crossings["Predicted Region (next crossing)"]
    == ephemeris_with_crossings["Predicted Region (prev. crossing)"]
]

length_after = len(ephemeris_with_crossings)

print(
    f"Removing {100 * np.abs(length_before - length_after) / length_after} % of observations"
)

# Convert to cylindrical coordinates
ephemeris_with_crossings["CYL MSM' (radii)"] = np.sqrt(
    ephemeris_with_crossings["Y MSM' (radii)"] ** 2
    + ephemeris_with_crossings["Z MSM' (radii)"] ** 2
)

ephemeris_with_crossings.rename(
    columns={"Predicted Region (prev. crossing)": "Predicted Region"}, inplace=True
)

# Reorded columns
predicted_spatial_regions = (
    ephemeris_with_crossings[
        [
            "Predicted Region",
            "Heliocentric Distance",
            "X MSM' (radii)",
            "CYL MSM' (radii)",
        ]
    ]
    .copy()
    .reset_index(drop=True)
)

# Save this to file
predicted_spatial_regions.to_csv("./messenger_region_observations.csv")
