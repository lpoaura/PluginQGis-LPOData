__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 3"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

import pytest

from ..tools.exceptions import QgsPluginInvalidProjectSetting
from ..tools.settings import (
    get_project_setting,
    get_setting,
    set_project_setting,
    set_setting,
)


def test_set_setting(qgis_new_project):
    set_setting("test_setting", "test_value")
    assert get_setting("test_setting") == "test_value"


def test_get_setting(qgis_new_project):
    assert get_setting("non-existent", 2, int) == 2


def test_get_setting2(qgis_new_project):
    assert get_setting("non-existent", 2, str) == "2"


def test_get_setting3(qgis_new_project):
    assert get_setting("non-existent", 2, bool) is True


def test_set_project_setting(qgis_new_project):
    set_project_setting("test_setting", "test_value")
    assert get_project_setting("test_setting") == "test_value"


def test_get_project_setting(qgis_new_project):
    assert get_project_setting("non-existent", 2, int) == 2


def test_get_project_setting2(qgis_new_project):
    assert get_project_setting("non-existent", "2", str) == "2"


def test_get_project_setting3(qgis_new_project):
    assert get_project_setting("non-existent", True, bool) is True


def test_get_project_setting_throws_error(qgis_new_project):
    with pytest.raises(QgsPluginInvalidProjectSetting):
        get_project_setting("non-existent", 2, list)
