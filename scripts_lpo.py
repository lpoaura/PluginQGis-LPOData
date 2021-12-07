# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : scripts_lpo.py
        -------------------
        Date                 : 2020-04-16
        Copyright            : (C) 2020 by Elsa Guilley (LPO AuRA)
        Email                : lpo-aura@lpo.fr
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

__author__ = "Elsa Guilley (LPO AuRA)"
__date__ = "2020-04-16"
__copyright__ = "(C) 2020 by Elsa Guilley (LPO AuRA)"

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = "$Format:%H$"

import os
import sys
import inspect

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction, QMenu
from .scripts_lpo_provider import ScriptsLPOProvider
from .carte_par_especes import CarteParEspece


cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class ScriptsLPOPlugin(object):
    def __init__(self, iface):
        # self.provider = None
        self.provider = ScriptsLPOProvider()
        self.iface = iface

        # def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        # self.provider = ScriptsLPOProvider()
        # QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        # self.initProcessing()
        QgsApplication.processingRegistry().addProvider(self.provider)

        self.especes_action = QAction(
            #  QIcon(),
            "Carte par espèces",
            self.iface.mainWindow(),
        )
        self.especes_action.triggered.connect(lambda: CarteParEspece().exec())
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
        self.iface.removeToolBarIcon(self.especes_action)
