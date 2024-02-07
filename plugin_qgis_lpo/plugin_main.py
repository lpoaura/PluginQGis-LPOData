#! python3  # noqa: E265

"""
    Main plugin module.
"""

# standard
from functools import partial
from pathlib import Path

# PyQGIS
from qgis.core import QgsApplication, QgsSettings
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu

# project
from plugin_qgis_lpo.__about__ import (
    DIR_PLUGIN_ROOT,
    __icon_path__,
    __title__,
    __uri_homepage__,
)
from plugin_qgis_lpo.gui.dlg_settings import PlgOptionsFactory
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
        self.options_factory: PlgOptionsFactory
        self.action_help: QAction
        self.action_settings: QAction
        self.action_help_plugin_menu_documentation: QAction
        self.especes_action: QAction

        self.provider = QgisLpoProvider()
        self.iface = iface
        self.log = PlgLogger().log

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
            lpo_menu = [
                a
                for a in self.iface.pluginMenu().parent().findChildren(QMenu)
                if a.title() == "Plugin LPO"
            ][0]
            lpo_menu.removeAction(self.especes_action)
        except IndexError:
            pass
        # teardown_logger(Plugin.name)
        self.iface.removeToolBarIcon(self.especes_action)

    def run(self):
        """Main process.

        :raises Exception: if there is no item in the feed
        """
        try:
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
