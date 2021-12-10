import re
import json
from pathlib import Path

from qgis.gui import QgsCheckableComboBox
from qgis.core import QgsVectorLayer, QgsProviderRegistry, QgsDataSourceUri, QgsProject
from qgis.utils import OverrideCursor

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QDialog,
    QComboBox,
    QVBoxLayout,
    QLineEdit,
    QHBoxLayout,
    QDialogButtonBox,
    QRadioButton,
    QGroupBox,
)
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.PyQt.QtCore import Qt, QSortFilterProxyModel, QEvent


class MyCheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skip_hide = False
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setPlaceholderText("Aucune espèce sélectionnée")
        self.setLineEdit(self.line_edit)
        self.view().viewport().installEventFilter(self)
        self.line_edit.installEventFilter(self)

    def hidePopup(self):
        # Most of the time (= when clicking inside the list) we
        # do want the list to remain opened and we skip the hidePopup step
        if not self.skip_hide:
            super().hidePopup()
        self.skip_hide = False

    def eventFilter(self, obj, event):
        """
        Handle the mouse clics
        """
        # Show the list on a clic on the lineEdit
        if obj == self.lineEdit():
            if (
                event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.LeftButton
            ):
                self.skip_hide = True
                self.showPopup()

        # Inside the list, a clic checks or unchecks the box
        elif (
            event.type() == QEvent.MouseButtonPress
            or event.type() == QEvent.MouseButtonRelease
        ) and obj == self.view().viewport():
            self.skip_hide = True
            if (
                event.type() == QEvent.MouseButtonRelease
                and event.button() == Qt.RightButton
            ):
                return True
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                if index.isValid():
                    if self.model().data(index, Qt.CheckStateRole) == Qt.Checked:
                        self.model().setData(index, Qt.Unchecked, Qt.CheckStateRole)
                    else:
                        self.model().setData(index, Qt.Checked, Qt.CheckStateRole)
                    self.updateText()
                    return True
        return super().eventFilter(obj, event)

    def checkedItemsData(self, role=Qt.UserRole):
        """
        Returns the list of data for the checked items
        """
        data_list = []
        for row in range(self.model().sourceModel().rowCount()):
            if (
                self.model().sourceModel().item(row, 0).data(Qt.CheckStateRole)
                == Qt.Checked
            ):
                data_list.append(self.model().sourceModel().item(row, 0).data(role))
        return data_list

    def updateText(self):
        """
        The text on the combobox should be the list of the selected items
        """
        name_list = self.checkedItemsData(Qt.DisplayRole)
        if len(name_list) == 0:
            self.lineEdit().setText("")
            return

        self.lineEdit().setText(", ".join(name_list))


class CarteParEspece(QDialog):
    def __init__(self, connection_name, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Carte par espèce(s)")

        self.cbx_nom_vern = MyCheckableComboBox()
        self.cbx_nom_sci = MyCheckableComboBox()
        nom_vern_proxy_model = QSortFilterProxyModel()
        nom_vern_proxy_model.setSourceModel(QStandardItemModel())
        nom_sci_proxy_model = QSortFilterProxyModel()
        nom_sci_proxy_model.setSourceModel(QStandardItemModel())
        self.cbx_nom_vern.setModel(nom_vern_proxy_model)
        self.cbx_nom_sci.setModel(nom_sci_proxy_model)
        rbtn_sci = QRadioButton("Nom scientifique")
        rbtn_vern = QRadioButton("Nom vernaculaire")
        ledt_search = QLineEdit()
        ledt_search.setPlaceholderText("Espèce à rechercher")

        grp_box = QGroupBox()
        grp_box.setLayout(QHBoxLayout())
        grp_box.layout().addWidget(rbtn_vern)
        grp_box.layout().addWidget(rbtn_sci)

        dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(ledt_search)
        self.layout().addWidget(self.cbx_nom_vern)
        self.layout().addWidget(self.cbx_nom_sci)
        self.layout().addWidget(grp_box)
        self.layout().addWidget(dialog_buttons)

        connection = (
            QgsProviderRegistry.instance()
            .providerMetadata("postgres")
            .createConnection(connection_name)
        )

        with OverrideCursor(Qt.WaitCursor):
            query = """SELECT unnest(liste_object)
                FROM qgis_shared.vm_taxonomy
                WHERE rang='species'"""
            especes = [json.loads(item[0]) for item in connection.executeSql(query)]

            # Remplissage des combobox
            for espece in especes:
                nom_sci = espece["nom_sci"]
                nom_vern = espece["nom_vern"]
                cd_nom = espece["cd_nom"]
                if nom_sci is not None and nom_sci.strip() != "":
                    sci_item = QStandardItem()
                    sci_item.setCheckable(True)
                    sci_item.setText(nom_sci)
                    sci_item.setData(cd_nom, Qt.UserRole)
                    self.cbx_nom_sci.model().sourceModel().appendRow(
                        [sci_item, QStandardItem(sanitizeName(nom_sci))]
                    )
                if nom_vern is not None and nom_vern.strip() != "":
                    vern_item = QStandardItem()
                    vern_item.setCheckable(True)
                    vern_item.setText(nom_vern)
                    vern_item.setData(cd_nom, Qt.UserRole)
                    self.cbx_nom_vern.model().sourceModel().appendRow(
                        [vern_item, QStandardItem(sanitizeName(nom_vern))]
                    )
            self.cbx_nom_vern.updateText()
            self.cbx_nom_sci.updateText()

            self.cbx_nom_vern.model().setFilterKeyColumn(1)
            self.cbx_nom_sci.model().setFilterKeyColumn(1)
            self.cbx_nom_vern.model().setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.cbx_nom_sci.model().setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.cbx_nom_vern.model().sort(0)
            self.cbx_nom_sci.model().sort(0)

        rbtn_vern.toggled.connect(
            lambda checked: self.cbx_nom_vern.setVisible(checked)
        )
        rbtn_sci.toggled.connect(
            lambda checked: self.cbx_nom_sci.setVisible(checked)
        )
        rbtn_vern.setChecked(True)
        self.cbx_nom_sci.setHidden(True)

        ledt_search.textChanged.connect(
            lambda text: self.cbx_nom_vern.model().setFilterWildcard(sanitizeName(text))
        )
        ledt_search.textChanged.connect(
            lambda text: self.cbx_nom_sci.model().setFilterWildcard(sanitizeName(text))
        )

    def accept(self):
        if self.cbx_nom_vern.isVisible():
            cd_noms = self.cbx_nom_vern.checkedItemsData()
        else:
            cd_noms = self.cbx_nom_sci.checkedItemsData()

        if len(cd_noms) == 0:
            QMessageBox.warning(None, "Attention", "Aucune espèce sélectionnée")
            return

        connection = (
            QgsProviderRegistry.instance()
            .providerMetadata("postgres")
            .createConnection("gnlpoaura")
        )
        query = f"""SELECT id_synthese,
                nom_sci,
                nom_vern,
                date::date,
                date_an,
                nombre_total,
                details::character varying AS details,
                oiso_code_nidif,
                oiso_statut_nidif,
                geom::geometry(Point,2154) AS geom,
                commentaires,
                comportement::character varying AS comportement,
                precision,
                place,
                observateur,
                source,
                mortalite,
                mortalite_cause
               FROM src_lpodatas.v_c_observations
              WHERE is_valid and st_geometrytype(geom) = 'ST_Point'
              and taxref_cdnom in ({', '.join(str(a) for a in cd_noms)})"""
        uri = QgsDataSourceUri(connection.uri())
        uri.setDataSource("", "(" + query + ")", "geom", "", "id_synthese")
        with OverrideCursor(Qt.WaitCursor):
            layer = QgsVectorLayer(uri.uri(), "Espèces", "postgres")
            layer.loadNamedStyle(str(Path(__file__).parent / "styles" / "bird_reproduction.qml"))
            QgsProject.instance().addMapLayer(layer)

        super().accept()


def sanitizeName(txt):
    """
    Remove diacritics
    """
    safename = re.sub(r"[áàâä]", "a", txt)
    safename = re.sub(r"[éèêë]", "e", safename)
    safename = re.sub(r"[íìîï]", "i", safename)
    safename = re.sub(r"[óòôö]", "o", safename)
    safename = re.sub(r"[úùûü]", "u", safename)
    safename = re.sub(r"[ýỳŷÿ]", "y", safename)
    safename = re.sub(r"[c]", "c", safename)
    return safename
