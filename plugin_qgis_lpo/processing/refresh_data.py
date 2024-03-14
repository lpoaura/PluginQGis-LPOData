"""
/***************************************************************************
        ScriptsLPO : state_of_knowledge.py
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

from typing import Any, Dict

from qgis.core import (
    QgsDataSourceUri,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterProviderConnection,
    QgsSettings,
    QgsVectorLayer,
)

from ..toolbelt.log_handler import PlgLogger
from .processing_algorithm import BaseProcessingAlgorithm
from .qgis_processing_postgis import uri_from_name


class RefreshData(BaseProcessingAlgorithm):
    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "RefreshData"
        self._display_name = "Rafraichissement des données"
        self._output_name = "Etat des connaissances"
        self._group_id = None
        self._group = None
        self._short_help_string = ""
        self._icon = "refresh.png"
        self._short_description = (
            "Rafraissement manuel des données nécessaires au fonctionnement du plugin"
        )
        self._is_map_layer = False
        self._has_histogram = False
        self._db_variables = QgsSettings()
        self.log = PlgLogger().log

    def initAlgorithm(self, _config: None) -> None:  # noqa N802
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        required_text = '<span style="color:#952132">(requis)</span>'

        # self._ts = datetime.now()
        # self._db_variables = QgsSettings()
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.DATABASE,
                self.tr(
                    f"""<b style="color:#0a84db">BASE DE DONNÉES</b> {required_text} :
                    sélectionnez votre <u>connexion</u> à la base de données LPO"""
                ),
                "postgres",
                defaultValue="geonature_lpo",
                optional=False,
            )
        )

    def processAlgorithm(
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict | None:
        if feedback is None:
            feedback = QgsProcessingFeedback()
        self.log(
            message=self.tr("Starting to populate default settings from database"),
            log_level=3,
            push=False,
        )
        # Form values
        self._connection = self.parameterAsString(parameters, self.DATABASE, context)
        self._uri = uri_from_name(self._connection)
        taxonomy_query = """SELECT 1 as id, liste
            FROM dbadmin.mv_taxonomy
            WHERE rang='{rank}'"""
        ranks = [
            "groupe_taxo",
            "regne",
            "phylum",
            "classe",
            "ordre",
            "famille",
            "group1_inpn",
            "group2_inpn",
        ]

        queries = {rank: taxonomy_query.format(rank=rank) for rank in ranks}
        queries[
            "source_data"
        ] = """
        SELECT 1 as id, list_source as source_data FROM dbadmin.mv_source
        """
        queries[
            "lr_columns"
        ] = """SELECT 1 as id, parameter_value as lr_columns
        from gn_commons.t_parameters
        where parameter_name like 'plugin_qgis_lpo_lr_columns'"""

        for key, query in queries.items():
            self.populate_settings(key, query)
        self.log(
            message=self.tr("All settings have been correctly populated"),
            log_level=3,
            push=False,
        )
        return {}

    def postProcessAlgorithm(self, _context, _feedback) -> Dict:  # noqa N802
        # Open the attribute table of the PostGIS layer

        return {}

    def populate_settings(
        self, setting: str, query: str, key_column: str = "id"
    ) -> None:
        """Querying database and populate Qgis Settings"""
        self.log(
            message=self.tr(f"Populate {setting} settings from database - BEGIN"),
            log_level=3,
            push=False,
        )
        self._uri.setDataSource("", f"({query})", "", "", key_column)
        layer = QgsVectorLayer(self._uri.uri(), setting, "postgres")
        for feature in layer.getFeatures():
            query_output = feature[1]
        self._db_variables.setValue(setting, query_output)
        self.log(
            message=self.tr(f"Populate {setting} settings from database - END"),
            log_level=3,
            push=False,
        )
