__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

from qgis.core import QgsRectangle


def extent_to_bbox(extent: QgsRectangle, precision: int = 2) -> str:
    """
    Add extent for the query

    :param extent: QgsRectangle expected to be in the right extent
    :param precision: Precision of coordinates
    :return: string representation xmin,ymin,xmax,ymax
    """

    def rnd(c: float) -> float:
        return round(c, precision)

    bbox = (
        rnd(extent.xMinimum()),
        rnd(extent.yMinimum()),
        rnd(extent.xMaximum()),
        rnd(extent.yMaximum()),
    )
    return ",".join(map(str, bbox))
