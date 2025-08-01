# Retrieve package version from pyproject.toml
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version(__name__)
except PackageNotFoundError:
    pass

from wamms.main import *
