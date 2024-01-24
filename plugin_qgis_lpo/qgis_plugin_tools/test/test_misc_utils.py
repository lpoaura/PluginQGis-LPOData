from qgis.core import QgsRectangle

from ..tools.misc_utils import extent_to_bbox


def test_extent_to_bbox():
    extent = QgsRectangle(1, 2, 3, 4)
    bbox = extent_to_bbox(extent, precision=1)
    assert bbox == "1.0,2.0,3.0,4.0"
