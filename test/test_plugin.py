from plugin_qgis_lpo.qgis_plugin_tools.tools.resources import plugin_name


def test_plugin_name():
    assert plugin_name() == "PluginQGISLPO"
