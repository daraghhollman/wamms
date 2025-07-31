"""
Primary script for WAMMS to handle calculating region probabilities for BepiColombo spacecraft
"""

import datetime as dt

import numpy as np
import pandas as pd
import spiceypy as spice

import env  # Contains environment variables determined on install


class spacecraft:
    def __init__(self, name: str, metakernel_path: str = env.PLAN_METAKERNEL):
        self.name: str = name
        self.metakernel_path: str = metakernel_path
        self.trajectory: pd.DataFrame = pd.DataFrame()
        self.probabilities: pd.DataFrame = pd.DataFrame()

    def update_probabilities(self):
        """A function to add magnetospheric region probability information based on previous MESSENGER findings.

        Creates a dataframe of region probabilities based on comparing
        trajectory information with previous MESSENGER predictions.

        self.update_trajectory() must have been run prior to this function, to
        determine what postitions to use.
        """

        if len(self.trajectory) == 0:
            # This function relies on trajectory information
            raise RuntimeError(
                "No trajectory information determined. Please run: update_trajectory()"
            )

        # The probabiliy maps we make with MESSENGER are cylindrically
        # symmetric to inprove coverage. As such, we calculate rho from the
        # trajectory data.
        x_data = self.trajectory["X MSM'"]
        cyl_data = np.sqrt(
            self.trajectory["Y MSM'"] ** 2 + self.trajectory["Z MSM'"] ** 2
        )

        # Load region prediction data
        prediction_data = pd.read_csv(
            env.WAMMSDIR + "/data/messenger_region_observations.csv"
        )

        # Create bins
        bin_size = 0.25
        x_bins = np.arange(-5, 5 + bin_size, bin_size)  # Radii
        cyl_bins = np.arange(0, 8 + bin_size, bin_size)  # Radii

        # Make histograms for each region prediction
        region_data = {
            "Names": ["Solar Wind", "Magnetosheath", "Magnetosphere"],
            "Data": {},
        }

        x_edges = []  # Just initialising to avoid LSP unbound variable errors
        y_edges = []
        for region_name in region_data["Names"]:

            filtered_predictions = prediction_data.loc[
                prediction_data["Predicted Region"] == region_name
            ][["X MSM' (radii)", "CYL MSM' (radii)"]]

            region_histogram, x_edges, y_edges = np.histogram2d(
                filtered_predictions["X MSM' (radii)"],
                filtered_predictions["CYL MSM' (radii)"],
                bins=[x_bins, cyl_bins],
            )

            region_data["Data"][region_name] = region_histogram

        bin_totals = np.sum(list(region_data["Data"].values()), axis=0)

        region_probabilities = {}
        for region_name in region_data["Names"]:
            region_probabilities[region_name] = (
                region_data["Data"][region_name] / bin_totals
            )

        # Now that we have a 2d histogram for each region, we can query this
        # for each position of the trajectory

        trajectory_probabilities = {
            region: np.zeros_like(x_data, dtype=float)
            for region in region_data["Names"]
        }

        # Digitize the trajectory data into bin indices
        x_indices = np.digitize(x_data, x_bins) - 1
        cyl_indices = np.digitize(cyl_data, cyl_bins) - 1

        # Iterate over trajectory points and assign probabilities
        for i in range(len(x_data)):
            x_index = x_indices[i]
            cyl_index = cyl_indices[i]

            # Ensure the index is within the valid histogram range
            if 0 <= x_index < len(x_bins) - 1 and 0 <= cyl_index < len(cyl_bins) - 1:
                for region in region_data["Names"]:
                    trajectory_probabilities[region][i] = region_probabilities[region][
                        x_index, cyl_index
                    ]
            else:
                print(self.trajectory.iloc[i])
                for region in region_data["Names"]:
                    trajectory_probabilities[region][
                        i
                    ] = np.nan  # Assign NaN if out of bounds

        probabilities = pd.DataFrame(trajectory_probabilities)
        probabilities["Time"] = self.trajectory["Time"]

        # Reorder columns
        probabilities = probabilities[
            ["Time", "Solar Wind", "Magnetosheath", "Magnetosphere"]
        ]

        self.region_probabilities = probabilities

    def update_trajectory(
        self,
        start_time: dt.datetime,
        end_time: dt.datetime,
        res: dt.timedelta,
        aberrate: bool = True,
    ):
        """A function to add XYZ trajectory information in the MSM'
        coordinate system

        The data are pulled from spice using the BepiColombo metakernel. This
        function can be called multiple times to add data from different time
        spans. It does not overwrite previous entries.

        Params
        ------
        start_time: dt.datetime
            From what time to start loading trajectory information

        end_time: dt.datetime
            At what time to stop trajectory information

        res: dt.timedelta
            The resolution that trajectory data are loaded at

        aberrate: bool {default True}
            If True, the average aberrated coordinate frame is used from
            SPICE: BC_MSO_AB (later converted to MSM'), if False, BC_MSO is
            used. See the inline comment below in the 'spkpos' function call
            for more details.

        Returns
        -------
        None - Function updates self.trajectory
        """

        with spice.KernelPool(self.metakernel_path):

            times = [
                start_time + i * res
                for i in range(round((end_time - start_time) / res))
            ]
            spice_times = spice.datetime2et(times)

            positions, _ = spice.spkpos(
                self.name,
                spice_times,
                # This spice frame kernel uses average Mercury velocity and
                # average solar wind velocity to determine an average
                # aberration angle, which is used for all time. We could be
                # more accurate by calculating aberration angle more frequently
                # (such as is done daily in hermpy) however this can be quite
                # slow.
                "BC_MSO_AB" if aberrate else "BC_MSO",
                "NONE",
                "MERCURY",
            )

            # We want the positions in MSM' coordinates, not MSO', and must add
            # 479 km to Z.
            positions[:, 2] += env.DIPOLE_OFFSET_KM

            # Convert to radii
            positions /= env.MERCURY_RADIUS_KM

            position_dict = {
                "Time": times,
                "X MSM'": positions[:, 0],
                "Y MSM'": positions[:, 1],
                "Z MSM'": positions[:, 2],
                "CYL MSM'": np.sqrt(positions[:, 1] ** 2 + positions[:, 2] ** 2),
            }

            # If we have already provided trajectory information, we want
            # to append instead of overwriting.
            if len(self.trajectory) == 0:
                self.trajectory = pd.DataFrame(position_dict)
            else:
                self.trajectory = pd.concat(
                    [self.trajectory, pd.DataFrame(position_dict)], ignore_index=True
                )

                # We must sort these data to allow for adding trajectory
                # information in non-chronological orders.
                self.trajectory = self.trajectory.sort_values("Time")
