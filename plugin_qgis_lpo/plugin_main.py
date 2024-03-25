#! python3  # noqa: E265

"""
    Main plugin module.
"""

# standard
from functools import partial
from pathlib import Path
from typing import Optional

import processing

# PyQGIS
from qgis.core import (
    QgsApplication,
    QgsProcessingException,
    QgsProviderConnectionException,
    QgsProviderRegistry,
    QgsSettings,
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu

# project
from plugin_qgis_lpo.__about__ import (
    DIR_PLUGIN_ROOT,
    __icon_dir_path__,
    __icon_path__,
    __title__,
    __uri_homepage__,
)
from plugin_qgis_lpo.commons.tasking_refresh_data import bg_task
from plugin_qgis_lpo.gui.dlg_settings import PlgOptionsFactory
from plugin_qgis_lpo.gui.menu_tools import MenuTools
from plugin_qgis_lpo.processing.provider import QgisLpoProvider
from plugin_qgis_lpo.processing.qgis_processing_postgis import get_connection_name
from plugin_qgis_lpo.processing.species_map import CarteParEspece
from plugin_qgis_lpo.toolbelt import PlgLogger

# ############################################################################
# ########## Classes ###############
# ##################################


class QgisLpoPlugin:
    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class which \
        provides the hook by which you can manipulate the QGIS application at run time.
        :type iface: QgsInterface
        """

        self.options_factory: Optional[PlgOptionsFactory] = None
        self.action_help: Optional[QAction] = None
        self.action_settings: Optional[QAction] = None
        self.action_help_plugin_menu_documentation: Optional[QAction] = None
        self.especes_action: Optional[QAction] = None
        self.provider: Optional[QgisLpoProvider] = None
        self.log = PlgLogger().log
        self.iface: QgisInterface = iface
        self.tools_menu: Optional[QMenu] = None
        self.main_menu: Optional[QMenu] = None
        self.tm = QgsApplication.taskManager()
        # translation
        # initialize the locale
        self.locale: str = QgsSettings().value("locale/userLocale", QLocale().name())[
            0:2
        ]
        locale_path: Path = (
            DIR_PLUGIN_ROOT
            / "resources"
            / "i18n"
            / f"{__title__.lower()}_{self.locale}.qm"
        )
        self.log(message=f"Translation: {self.locale}, {locale_path}", log_level=4)
        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path.resolve()))
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        """Set up plugin UI elements."""

        self.initSettings()
        self.provider = QgisLpoProvider()
        # self.main_menu = self.iface.pluginMenu().parent().addMenu(__title__)

        # settings page within the QGIS preferences menu
        self.options_factory = PlgOptionsFactory()
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        # -- Actions
        self.action_help = QAction(
            QgsApplication.getThemeIcon("mActionHelpContents.svg"),
            self.tr("Help"),
            self.iface.mainWindow(),
        )
        self.action_help.triggered.connect(
            partial(QDesktopServices.openUrl, QUrl(__uri_homepage__))
        )

        self.action_settings = QAction(
            QgsApplication.getThemeIcon("console/iconSettingsConsole.svg"),
            self.tr("Settings"),
            self.iface.mainWindow(),
        )
        self.action_settings.triggered.connect(
            lambda: self.iface.showOptionsDialog(
                currentPage="mOptionsPage{}".format(__title__)
            )
        )

        # -- Menu
        self.iface.addPluginToMenu(__title__, self.action_settings)
        self.iface.addPluginToMenu(__title__, self.action_help)

        # -- Help menu

        # documentation
        self.iface.pluginHelpMenu().addSeparator()
        self.action_help_plugin_menu_documentation = QAction(
            QIcon(str(__icon_path__)),
            f"{__title__} - Documentation",
            self.iface.mainWindow(),
        )
        self.action_help_plugin_menu_documentation.triggered.connect(
            partial(QDesktopServices.openUrl, QUrl(__uri_homepage__))
        )

        self.iface.pluginHelpMenu().addAction(
            self.action_help_plugin_menu_documentation
        )

        QgsApplication.processingRegistry().addProvider(self.provider)

        self.especes_action = QAction(
            QIcon(str(__icon_dir_path__ / "map.png")),
            "Carte par espèces",
            self.iface.mainWindow(),
        )
        self.especes_action.triggered.connect(self.runEspeces)
        self.refresh_data_action = QAction(
            QIcon(str(__icon_dir_path__ / "refresh.png")),
            "Rafraichir les données TEST",
            self.iface.mainWindow(),
        )
        self.refresh_data_action.triggered.connect(self.populateSettings)
        try:
            # Try to put the button in the LPO menu bar
            # lpo_menu = [
            #     a
            #     for a in self.iface.pluginMenu().parent().findChildren(QMenu)
            #     if a.title() == "Plugin LPO"
            # ][0]
            self.main_menu = self.iface.pluginMenu().parent().addMenu(__title__)
            self.tools_menu = MenuTools(self.iface.mainWindow())
            self.main_menu.addAction(self.tools_menu.act_extract_data)
            self.main_menu.addAction(self.tools_menu.act_extract_data_observers)
            self.main_menu.addAction(self.tools_menu.addSeparator())
            self.main_menu.addAction(self.tools_menu.act_summary_map)
            self.main_menu.addAction(self.especes_action)
            self.main_menu.addAction(self.tools_menu.addSeparator())
            self.main_menu.addAction(self.tools_menu.act_summary_per_species)
            self.main_menu.addAction(self.tools_menu.act_summary_per_time_interval)
            self.main_menu.addAction(self.tools_menu.act_state_of_knowledge)

        except IndexError:
            # If not successful put the button in the Plugins toolbar
            self.iface.addToolBarIcon(self.especes_action)
            self.iface.messageBar().pushWarning(
                "Attention",
                "La carte par espèces est accessible via la barre d'outils d'Extensions",
            )
        # -- Post UI initialization
        self.log(
            message="Plugin QGIS LpO loaded",
            log_level=0,
            push=True,
            duration=60,
        )
        # self.iface.initializationCompleted.connect(self.populateSettings)

    def populateSettings(self):
        self.log(
            message="Loading GeoNature required data",
            log_level=0,
            push=True,
            duration=60,
        )
        task_no = self.tm(
            bg_task("plugin_qgis_lpo:RefreshData", {"DATABASE": "geonature_lpo"})
        )
        self.log(
            message=f"{str(type(self.tm))} {str(dir(self.tm))}",
            log_level=0,
            push=True,
            duration=2,
        )
        self.log(
            message=f"task_no {task_no}",
            log_level=0,
            push=True,
            duration=2,
        )

        # self.log(
        #     message=f"Loading GeoNature terminated",
        #     log_level=0,
        #     push=True,
        #     duration=2,
        # )
        # try:
        #     postgres_metadata = QgsProviderRegistry.instance().providerMetadata(
        #         "postgres"
        #     )
        #     if "geonature_lpo" in postgres_metadata.dbConnections():
        #         self.log(
        #             message=f"Loading GeoNature required data",
        #             log_level=0,
        #             push=True,
        #             duration=60,
        #         )
        #         self.tm.addTask(
        #             bg_task(
        #                 "plugin_qgis_lpo:RefreshData", {"DATABASE": "geonature_lpo"}
        #             )
        #         )
        #         self.log(
        #             message=f"Loading GeoNature terminated",
        #             log_level=0,
        #             push=True,
        #             duration=2,
        #         )
        # except QgsProviderConnectionException as exc:
        #     self.log(
        #         message=self.tr("Houston, we've got a problem: {}".format(exc)),
        #         log_level=2,
        #         push=True,
        #     )
        #     raise QgsProcessingException(
        #         f"Could not retrieve connection details : {str(exc)}"
        #     ) from exc  # processing.run("plugin_qgis_lpo:RefreshData", {"DATABASE": "geonature_lpo"})
        return

    def runEspeces(self):  # noqa N802
        connection_name = get_connection_name()
        if connection_name is not None:
            CarteParEspece(connection_name).exec()

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        :param message: string to be translated.
        :type message: str

        :returns: Translated version of message.
        :rtype: str
        """
        return QCoreApplication.translate(self.__class__.__name__, message)

    def unload(self):
        """Cleans up when plugin is disabled/uninstalled."""
        # -- Clean up menu
        self.iface.removePluginMenu(__title__, self.action_help)
        self.iface.removePluginMenu(__title__, self.action_settings)

        # -- Clean up preferences panel in QGIS settings
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        # remove from QGIS help/extensions menu
        if self.action_help_plugin_menu_documentation:
            self.iface.pluginHelpMenu().removeAction(
                self.action_help_plugin_menu_documentation
            )

        # remove actions
        del self.action_settings
        del self.action_help

        QgsApplication.processingRegistry().removeProvider(self.provider)

        try:
            self.main_menu.clear()
            self.main_menu.setHidden(True)
            del self.main_menu
        except IndexError:
            pass
        # teardown_logger(Plugin.name)

        self.iface.removeToolBarIcon(self.especes_action)

    def run(self):
        """Main process.

        :raises Exception: if there is no item in the feed
        """
        try:
            self.populateSettings()
            self.log(
                message=self.tr("Everything ran OK."),
                log_level=3,
                push=False,
            )

        except Exception as err:
            self.log(
                message=self.tr("Houston, we've got a problem: {}".format(err)),
                log_level=2,
                push=True,
            )

    def initSettings(self):
        dbVariables = QgsSettings()
        variables = [
            "groupe_taxo",
            "regne",
            "phylum",
            "classe",
            "ordre",
            "famille",
            "group1_inpn",
            "group2_inpn",
            "source_data",
            "lr_columns",
        ]
        for variable in variables:
            if not dbVariables.value(variable):
                dbVariables.setValue(variable, set())
