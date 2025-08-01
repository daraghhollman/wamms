"""
Script to load the MESSENGER crossing list and find all direct crossing events


A copy of create_direct_traversals_dataset.py but referencing Philpott 2020
instead of Hollman 2025
"""

import pandas as pd
from hermpy import boundaries, mag, trajectory, utils


def main():
    # Load crossing list
    crossing_list = boundaries.Load_Crossings(
        utils.User.CROSSING_LISTS["Philpott"], include_data_gaps=True
    ).drop(
        columns=[  # Removing unneeded columns to make things clearer
            "Start MSO X (km)",
            "Start MSO Y (km)",
            "Start MSO Z (km)",
            "End MSO X (km)",
            "End MSO Y (km)",
            "End MSO Z (km)",
            "Start MSO X (radii)",
            "Start MSO Y (radii)",
            "Start MSO Z (radii)",
            "End MSO X (radii)",
            "End MSO Y (radii)",
            "End MSO Z (radii)",
            "Start MSM X (km)",
            "Start MSM Y (km)",
            "Start MSM Z (km)",
            "End MSM X (km)",
            "End MSM Y (km)",
            "End MSM Z (km)",
            "Start MSM X (radii)",
            "Start MSM Y (radii)",
            "Start MSM Z (radii)",
            "End MSM X (radii)",
            "End MSM Y (radii)",
            "End MSM Z (radii)",
        ]
    )

    print(crossing_list)
    crossing_list["Start Time"] = pd.to_datetime(crossing_list["Start Time"])
    crossing_list["End Time"] = pd.to_datetime(crossing_list["End Time"])

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
            consecutive_crossing.get(current_crossing["Type"], "")
            != next_crossing["Type"]
        ):
            continue

        this_sheath_traversal = {
            "Start Time": current_crossing["End Time"],
            "End Time": next_crossing["Start Time"],
            "Direction": (
                "Inbound" if "BS" in current_crossing["Type"] else "Outbound"
            ),
        }

        direct_sheath_traversals.append(this_sheath_traversal)

    # Convert this list to a dataframe
    direct_sheath_traversals = pd.DataFrame(direct_sheath_traversals)

    direct_sheath_traversals = get_traversal_metadata(direct_sheath_traversals)

    direct_sheath_traversals.to_csv("../data/direct_sheath_traversals_philpott.csv")


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
    full_mission = mag.Load_Mission("../data/messenger_mag")
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
    new_dataframe["Heliocentic Distance (AU)"] = utils.Constants.KM_TO_AU(
        trajectory.Get_Heliocentric_Distance(new_dataframe["Mid Time"])
    )

    # We remove the columns we don' want
    new_dataframe = new_dataframe.drop(
        columns=["date", "Mid Time", "|B|", "Bx", "By", "Bz"]
    )

    return new_dataframe


if __name__ == "__main__":
    main()
