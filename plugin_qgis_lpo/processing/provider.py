# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : scripts_lpo_provider.py
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

__author__ = "LPO AuRA"
__date__ = "2020-2024"

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = "$Format:%H$"

import os

from qgis.core import QgsMessageLog, QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .extract_data import ExtractData
from .extract_data_observers import ExtractDataObservers
from .state_of_knowledge import StateOfKnowledge
from .summary_map import SummaryMap
from .summary_table_per_species import SummaryTablePerSpecies
from .summary_table_per_time_interval import SummaryTablePerTimeInterval
from .summary_table_per_time_interval_old import SummaryTablePerTimeIntervalOld

plugin_path = os.path.dirname(__file__)


class Provider(QgsProcessingProvider):
    def __init__(self) -> None:
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def id(self) -> str:
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return "scriptsLPO"

    def name(self) -> str:
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr("Traitements de la LPO")

    def icon(self) -> "QIcon":
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(
            os.path.join(plugin_path, os.pardir, "icons", "logo_lpo_aura_carre.png")
        )

    def unload(self) -> None:
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):  # noqa N802
        """
        Loads all algorithms belonging to this provider.
        """
        algorithms = [
            ExtractData(),
            ExtractDataObservers(),
            SummaryTablePerSpecies(),
            SummaryTablePerTimeInterval(),
            StateOfKnowledge(),
            SummaryMap(),
            SummaryTablePerTimeIntervalOld(),
        ]
        for alg in algorithms:
            self.addAlgorithm(alg)

        # def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        # return self.name()
