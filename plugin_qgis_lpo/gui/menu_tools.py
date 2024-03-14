#! python3  # noqa: E265

"""
    Custom menu.

    Ressources: https://realpython.com/python-menus-toolbars/#adding-help-tips-to-actions
"""

# PyQGIS
from qgis import processing
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu

# project
from plugin_qgis_lpo.__about__ import __title__
from plugin_qgis_lpo.processing.provider import (
    ExtractData,
    ExtractDataObservers,
    RefreshData,
    StateOfKnowledge,
    SummaryMap,
    SummaryTablePerSpecies,
    SummaryTablePerTimeInterval,
)


class MenuTools(QMenu):
    """Menu pointing to plugin processings.


    Example:

        from .menu_tools import MenuTools
        menubar.addMenu(MenuTools(self))
    """

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent)

        # menu definition
        self.setTitle(self.tr("&Tools"))
        self.setObjectName("LSCIToolsMenu")
        self.setToolTipsVisible(True)
        self.setToolTip(self.tr("Related utilities"))

        # build menu actions and triggers
        self.initGui()

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # -- Actions
        self.act_extract_data = QAction(
            icon=QIcon(ExtractData().icon()),
            text=ExtractData().displayName(),
        )
        self.act_extract_data_observers = QAction(
            icon=QIcon(ExtractDataObservers().icon()),
            text=ExtractDataObservers().displayName(),
        )
        self.act_state_of_knowledge = QAction(
            icon=QIcon(StateOfKnowledge().icon()),
            text=StateOfKnowledge().displayName(),
        )
        self.act_summary_map = QAction(
            icon=QIcon(SummaryMap().icon()),
            text=SummaryMap().displayName(),
        )
        self.act_summary_per_species = QAction(
            icon=QIcon(SummaryTablePerSpecies().icon()),
            text=SummaryTablePerSpecies().displayName(),
        )
        self.act_summary_per_time_interval = QAction(
            icon=QIcon(SummaryTablePerTimeInterval().icon()),
            text=SummaryTablePerTimeInterval().displayName(),
        )
        self.act_refresh_data = QAction(
            icon=QIcon(RefreshData().icon()),
            text=RefreshData().displayName(),
        )

        # -- Connections
        self.act_extract_data.triggered.connect(
            lambda: processing.createAlgorithmDialog(
                f"plugin_qgis_lpo:{ExtractData().name()}"
            ).show()
        )
        self.act_extract_data_observers.triggered.connect(
            lambda: processing.createAlgorithmDialog(
                f"plugin_qgis_lpo:{ExtractDataObservers().name()}"
            ).show()
        )
        self.act_state_of_knowledge.triggered.connect(
            lambda: processing.createAlgorithmDialog(
                f"plugin_qgis_lpo:{StateOfKnowledge().name()}"
            ).show()
        )

        self.act_summary_map.triggered.connect(
            lambda: processing.createAlgorithmDialog(
                f"plugin_qgis_lpo:{SummaryMap().name()}"
            ).show()
        )
        self.act_summary_per_species.triggered.connect(
            lambda: processing.createAlgorithmDialog(
                f"plugin_qgis_lpo:{SummaryTablePerSpecies().name()}"
            ).show()
        )
        self.act_summary_per_time_interval.triggered.connect(
            lambda: processing.createAlgorithmDialog(
                f"plugin_qgis_lpo:{SummaryTablePerTimeInterval().name()}"
            ).show()
        )
        self.act_refresh_data.triggered.connect(
            lambda: processing.createAlgorithmDialog(
                f"plugin_qgis_lpo:{RefreshData().name()}"
            ).show()
        )

        # -- Menu
        self.addAction(self.act_refresh_data)
        self.addSeparator()
        self.addAction(self.act_summary_map)
        self.addSeparator()
        self.addAction(self.act_extract_data)
        self.addAction(self.act_extract_data_observers)
        self.addSeparator()
        self.addAction(self.act_summary_per_species)
        self.addAction(self.act_summary_per_time_interval)
        self.addAction(self.act_state_of_knowledge)

    def tr(self, string: str) -> str:
        """Returns a translatable string with the self.tr() function.

        Args:
            string (str): text to translate

        Returns:
            str: translated text
        """
        return QCoreApplication.translate(self.__class__.__name__, string)
