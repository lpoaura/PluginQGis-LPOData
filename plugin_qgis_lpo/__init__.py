import os

from qgis.gui import QgisInterface

from plugin_qgis_lpo.qgis_plugin_tools.infrastructure.debugging import (  # noqa F401
    setup_debugpy,
    setup_ptvsd,
    setup_pydevd,
)

debugger = os.environ.get("QGIS_PLUGIN_USE_DEBUGGER", "").lower()
if debugger in {"debugpy", "ptvsd", "pydevd"}:
    locals()["setup_" + debugger]()


def classFactory(iface: QgisInterface):  # noqa N802
    from plugin_qgis_lpo.plugin import Plugin

    return Plugin(iface)
