# WAMMS
Where Are My Mercury Spacecraft
...with respect to the magnetospheric boundaries.

This tool uses magnetospheric region predictions from the entire MESSNEGER mission, based on bow shock and magnetopause crossings (Hollman 2025, in review, [PREPRINT](https://essopenarchive.org/users/867402/articles/1320325-identifying-messenger-magnetospheric-boundary-crossings-using-a-random-forest-region-classifier))
These are used to predict regions for the BepiColombo mission, based on trajectories available in SPICE kernels


## Installation

This repository and needed data can be installed with the following command. This will take some time, as the required kernel files are large.

```shell
git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/daraghhollman/wamms
cd wamms
```

Following this, the package must be installed to python. This will also take some time, as the kernel files are installed along with the package into the Python package directories.

```shell
pip install .
```

Lastly, some of the data needed are too large to store on Github, but can be downloaded from this Zenodo repository:

```shell
mkdir ./data && curl 'https://zenodo.org/records/16687232/files/messenger_region_observations.csv' > ./data/messenger_region_observations.csv
```

A test script is included under `examples/`, which should run out-of-the-box after the above steps. The dates in this file can be changed to quickly explore different scenarios.
