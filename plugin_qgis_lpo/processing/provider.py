#! python3  # noqa: E265

"""
    Processing provider module.
"""

# PyQGIS
from qgis.core import QgsProcessingProvider, QgsSettings
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

# project
from plugin_qgis_lpo.toolbelt.log_handler import PlgLogger
from plugin_qgis_lpo.__about__ import __icon_dir_path__, __title__, __version__
from plugin_qgis_lpo.processing.extract_data import ExtractData
from plugin_qgis_lpo.processing.extract_sinp_data import ExtractSinpData
from plugin_qgis_lpo.processing.extract_data_observers import ExtractDataObservers
from plugin_qgis_lpo.processing.refresh_data import RefreshData
from plugin_qgis_lpo.processing.state_of_knowledge import StateOfKnowledge
from plugin_qgis_lpo.processing.summary_map import SummaryMap
from plugin_qgis_lpo.processing.summary_table_per_species import SummaryTablePerSpecies
from plugin_qgis_lpo.processing.summary_table_per_time_interval import (
    SummaryTablePerTimeInterval,
)

# ############################################################################
# ########## Classes ###############
# ##################################


class QgisLpoProvider(QgsProcessingProvider):
    """
    Processing provider class.
    """

    def loadAlgorithms(self):
        """Loads all algorithms belonging to this provider."""
        self.log = PlgLogger().log
        self._db_variables = QgsSettings()
        algorithms = [
            RefreshData(),
            ExtractData(),
            ExtractDataObservers(),
            SummaryTablePerSpecies(),
            SummaryTablePerTimeInterval(),
            StateOfKnowledge(),
            SummaryMap(),
        ]
        export_sinp = not eval((self._db_variables.value("exclude_export_sinp")).capitalize())
        self.log(message=f"export_sinp {export_sinp}", log_level=0, push=False)
        if export_sinp:
            algorithms += [
                ExtractSinpData(),
            ]
        for alg in algorithms:
            self.addAlgorithm(alg)

    def id(self) -> str:
        """Unique provider id, used for identifying it. This string should be unique, \
        short, character only string, eg "qgis" or "gdal". \
        This string should not be localised.

        :return: provider ID
        :rtype: str
        """
        return "plugin_qgis_lpo"

    def name(self) -> str:
        """Returns the provider name, which is used to describe the provider
        within the GUI. This string should be short (e.g. "Lastools") and localised.

        :return: provider name
        :rtype: str
        """
        return __title__

    def longName(self) -> str:
        """Longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools".
        This string should be localised. The default
        implementation returns the same string as name().

        :return: provider long name
        :rtype: str
        """
        return self.tr("{} - Tools".format(__title__))

    def icon(self) -> QIcon:
        """QIcon used for your provider inside the Processing toolbox menu.

        :return: provider icon
        :rtype: QIcon
        """
        return QIcon(str(__icon_dir_path__ / "logo_lpo_aura_carre.png"))

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: str
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(self.__class__.__name__, message)

    def versionInfo(self) -> str:
        """Version information for the provider, or an empty string if this is not \
        applicable (e.g. for inbuilt Processing providers). For plugin based providers, \
        this should return the plugin’s version identifier.

        :return: version
        :rtype: str
        """
        return __version__
