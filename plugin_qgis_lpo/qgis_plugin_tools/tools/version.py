"""Tools about version."""
from typing import Tuple

from osgeo import osr

from .exceptions import QgsPluginVersionInInvalidFormat
from .resources import metadata_config


def format_version_integer(version_string: str) -> int:
    """Transform version string to integers to allow comparing versions.

    Transform "0.1.2" into "000102"
    Transform "10.9.12" into "100912"
    """
    return int("".join([a.zfill(2) for a in version_string.strip().split(".")]))


def version(remove_v_prefix: bool = True) -> str:
    """Return the version defined in metadata.txt."""
    v = metadata_config()["general"]["version"]
    if v.startswith("v") and remove_v_prefix:
        v = v[1:]
    return v


def proj_version() -> Tuple[int, int]:
    """Returns PROJ library version"""
    major: int = osr.GetPROJVersionMajor()
    minor: int = osr.GetPROJVersionMinor()
    return major, minor


def version_from_string(version: str) -> Tuple[int, int, int]:
    """
    Transforms version string in format 'x.y.z' to tuple (x,y,z) for comparisons
    :param version:
    :return:
    """
    parts = version.split(".")
    if len(parts) != 3:
        raise QgsPluginVersionInInvalidFormat()
    return int(parts[0]), int(parts[1]), int(parts[2])


def string_from_version(version: Tuple[int, int, int]) -> str:
    """
    Transforms version tuple in format (x,y,z) to string in format 'x.y.z'
    :param version:
    :return:
    """
    if len(version) != 3:
        raise QgsPluginVersionInInvalidFormat()
    return ".".join(map(str, version))
