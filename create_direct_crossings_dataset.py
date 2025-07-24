"""
Script to load the MESSENGER crossing list and find all direct crossing events
"""

import pandas as pd
from hermpy import mag, trajectory


def main():
    # Load crossing list
    crossing_list = pd.read_csv("./data/hollman_2025_crossing_list.csv")
    crossing_list["Time"] = pd.to_datetime(crossing_list["Times"])

    consecutive_crossing = {
        "BS_IN": "MP_IN",
        "MP_OUT": "BS_OUT",
    }

    direct_sheath_traversals = []

    # Find direct crossing events
    for i in range(len(crossing_list)):

        current_crossing = crossing_list.iloc[i]

        try:
            next_crossing = crossing_list.iloc[i + 1]
        except:
            break

        # Ignore if not a direct magnetosheath traversal
        if (
            consecutive_crossing.get(current_crossing["Label"], "")
            != next_crossing["Label"]
        ):
            continue

        this_sheath_traversal = {
            "Start Time": current_crossing["Time"],
            "End Time": next_crossing["Time"],
            "Direction": (
                "Inbound" if "BS" in current_crossing["Label"] else "Outbound"
            ),
        }

        direct_sheath_traversals.append(this_sheath_traversal)

    # Convert this list to a dataframe
    direct_sheath_traversals = pd.DataFrame(direct_sheath_traversals)

    direct_sheath_traversals = get_traversal_metadata(direct_sheath_traversals)

    direct_sheath_traversals.to_csv("./data/direct_sheath_traversals.csv")


def get_traversal_metadata(traversals):

    new_dataframe = traversals.copy()

    # Length
    new_dataframe["Length (seconds)"] = [
        (end - start).total_seconds()
        for start, end in zip(new_dataframe["Start Time"], new_dataframe["End Time"])
    ]

    # We assume the 'position' of a sheath traversal is at the midpoint
    new_dataframe["Mid Time"] = (
        new_dataframe["Start Time"]
        + (new_dataframe["End Time"] - new_dataframe["End Time"]) / 2
    )

    # Aberraion is very time consuming to determine, and in reality, the
    # quickest is to load it from a precomputed file. We use hermpy to
    # determine aberrated position for the duration of the mission and now load
    # this file. We find the rows in the MESSENGER data which are closest to
    # the time of crossing.
    # To quickly find the position of each crossing in MSM' coordinates, we can
    # load the full mission at 1 second resolution from file, and cross-reference.
    full_mission = mag.Load_Mission("./data/messenger_mag")
    new_dataframe = pd.merge_asof(
        new_dataframe,
        full_mission,
        left_on="Mid Time",
        right_on="date",
        direction="nearest",
    )

    # Magnetic Local Time
    new_dataframe["Local Time (hrs)"] = [
        trajectory.Local_Time(list(position))
        for position in zip(
            new_dataframe["X MSM' (radii)"],
            new_dataframe["Y MSM' (radii)"],
            new_dataframe["Z MSM' (radii)"],
        )
    ]

    # Magnetic Latitude
    new_dataframe["Magnetic Latitude (deg.)"] = [
        trajectory.Magnetic_Latitude(list(position))
        for position in zip(
            new_dataframe["X MSM' (radii)"],
            new_dataframe["Y MSM' (radii)"],
            new_dataframe["Z MSM' (radii)"],
        )
    ]

    # Heliocentric distance
    new_dataframe["Heliocentic Distance (AU)"] = trajectory.Get_Heliocentric_Distance(
        new_dataframe["Mid Time"]
    )

    # We remove the columns we don' want
    new_dataframe = new_dataframe.drop(
        columns=["date", "Mid Time", "|B|", "Bx", "By", "Bz"]
    )

    return new_dataframe


if __name__ == "__main__":
    main()
