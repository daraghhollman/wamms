import datetime as dt

import matplotlib.pyplot as plt

import main
from main import spacecraft

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

times = (dt.datetime(2027, 1, 1), dt.datetime(2027, 2, 1))

mpo = spacecraft("mpo")
mpo.update_trajectory(*times, dt.timedelta(minutes=1))
mpo.update_probabilities()

mmo = spacecraft("mmo")
mmo.update_trajectory(*times, dt.timedelta(minutes=1))
mmo.update_probabilities()

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
)
mmo_ax.plot(
    mmo.region_probabilities["Time"],
    mmo.region_probabilities["Magnetosheath"],
    color=wong_colours["orange"],
)
mmo_ax.plot(
    mmo.region_probabilities["Time"],
    mmo.region_probabilities["Magnetosphere"],
    color=wong_colours["blue"],
)

plt.show()
