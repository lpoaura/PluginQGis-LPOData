# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : scripts_lpo.py
        -------------------

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction, QMenu

# from plugin_qgis_lpo.processing.provider import Provider
from plugin_qgis_lpo.qgis_plugin_tools.tools.custom_logging import (
    setup_logger,
    teardown_logger,
)
from plugin_qgis_lpo.qgis_plugin_tools.tools.resources import plugin_name

from .processing.provider import Provider
from .processing.qgis_processing_postgis import get_connection_name
from .processing.species_map import CarteParEspece

# cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

# if cmd_folder not in sys.path:
#     sys.path.insert(0, cmd_folder)


class Plugin(object):
    """QGIS Plugin Implementation."""

    name = plugin_name()

    def __init__(self, iface) -> None:
        setup_logger(Plugin.name)
        # self.provider = None
        self.provider = Provider()
        self.iface = iface
        # def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        # self.provider = Provider()
        # QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):  # noqa N802
        # self.initProcessing()
        QgsApplication.processingRegistry().addProvider(self.provider)

        self.especes_action = QAction(
            #  QIcon(),
            "Carte par espèces",
            self.iface.mainWindow(),
        )
        self.especes_action.triggered.connect(self.runEspeces)
        try:
            # Try to put the button in the LPO menu bar
            lpo_menu = [
                a
                for a in self.iface.pluginMenu().parent().findChildren(QMenu)
                if a.title() == "Plugin LPO"
            ][0]
            lpo_menu.addAction(self.especes_action)
        except IndexError:
            # If not successful put the button in the Plugins toolbar
            self.iface.addToolBarIcon(self.especes_action)
            self.iface.messageBar().pushWarning(
                "Attention",
                "La carte par espèces est accessible via la barre d'outils d'Extensions",
            )

    def runEspeces(self):  # noqa N802
        connection_name = get_connection_name()
        if connection_name is not None:
            CarteParEspece(connection_name).exec()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

        try:
            lpo_menu = [
                a
                for a in self.iface.pluginMenu().parent().findChildren(QMenu)
                if a.title() == "Plugin LPO"
            ][0]
            lpo_menu.removeAction(self.especes_action)
        except IndexError:
            pass
        teardown_logger(Plugin.name)
        self.iface.removeToolBarIcon(self.especes_action)
