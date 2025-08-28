"""Qgis STARTUP script
Must be copied in QGIS root config directory
(e.g. ~/.local/share/QGIS/QGIS3/)
"""

from qgis.core import (
    Qgis,
    QgsDataSourceUri,
    QgsProcessingException,
    QgsProviderConnectionException,
    QgsProviderRegistry,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.utils import iface

try:
    postgres_metadata = QgsProviderRegistry.instance().providerMetadata("postgres")
    connection = postgres_metadata.createConnection("geonature_lpo")
except QgsProviderConnectionException as exc:
    raise QgsProcessingException(
        f"Could not retrieve connection details : {str(exc)}"
    ) from exc
uri = QgsDataSourceUri(connection.uri())

# Groupe_taxo list
groupe_taxo_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='groupe_taxo'"""
uri.setDataSource("", "(" + groupe_taxo_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "groupe_taxo", "postgres")
for feature in layer.getFeatures():
    groupe_taxo = feature[1]
    # iface.messageBar().pushMessage("groupe_taxo : {}".format(groupe_taxo))

# Regne list
regne_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='regne'"""
uri.setDataSource("", "(" + regne_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "regne", "postgres")
for feature in layer.getFeatures():
    regne = feature[1]

# Phylum list
phylum_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='phylum'"""
uri.setDataSource("", "(" + phylum_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "phylum", "postgres")
for feature in layer.getFeatures():
    phylum = feature[1]

# Classe list
classe_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='classe'"""
uri.setDataSource("", "(" + classe_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "classe", "postgres")
for feature in layer.getFeatures():
    classe = feature[1]

# Ordre list
ordre_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='ordre'"""
uri.setDataSource("", "(" + ordre_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "ordre", "postgres")
for feature in layer.getFeatures():
    ordre = feature[1]

# Famille list
famille_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='famille'"""
uri.setDataSource("", "(" + famille_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "famille", "postgres")
for feature in layer.getFeatures():
    famille = feature[1]

# Group1_INPN list
group1_inpn_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='group1_inpn'"""
uri.setDataSource("", "(" + group1_inpn_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "group1_inpn", "postgres")
for feature in layer.getFeatures():
    group1_inpn = feature[1]

# Group2_INPN list
group2_inpn_query = """SELECT rang, liste
    FROM dbadmin.mv_taxonomy
    WHERE rang='group2_inpn'"""
uri.setDataSource("", "(" + group2_inpn_query + ")", None, "", "rang")
layer = QgsVectorLayer(uri.uri(), "group2_inpn", "postgres")
for feature in layer.getFeatures():
    group2_inpn = feature[1]

# SOURCE list
source_query = """SELECT rang, list_source
                  FROM dbadmin.mv_source ms"""
uri.setDataSource("", "(" + source_query + ")", None, "", "list_source")
layer = QgsVectorLayer(uri.uri(), "source_data", "postgres")
for feature in layer.getFeatures():
    source_data = feature[1]

status_columns_query = """SELECT parameter_value
from gn_commons.t_parameters
where parameter_name like 'plugin_qgis_lpo_status_columns'"""
uri.setDataSource("", "(" + status_columns_query + ")", None, "", "parameter_value")
layer = QgsVectorLayer(uri.uri(), "status_columns", "postgres")
for feature in layer.getFeatures():
    status_columns = feature[0]


# Add lists to QgsSettings
db_variables = QgsSettings()
# db_variables.setValue("areas_types", areas_types)
db_variables.setValue("groupe_taxo", groupe_taxo)
db_variables.setValue("regne", regne)
db_variables.setValue("phylum", phylum)
db_variables.setValue("classe", classe)
db_variables.setValue("ordre", ordre)
db_variables.setValue("famille", famille)
db_variables.setValue("group1_inpn", group1_inpn)
db_variables.setValue("group2_inpn", group2_inpn)
db_variables.setValue("source_data", source_data)
db_variables.setValue("status_columns", status_columns)
# Add Plugin LPO menu

# iface.pluginMenu().parent().addMenu("Plugin LPO")
