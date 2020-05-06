# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : summary_table.py
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

__author__ = 'Elsa Guilley (LPO AuRA)'
__date__ = '2020-04-16'
__copyright__ = '(C) 2020 by Elsa Guilley (LPO AuRA)'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import os
from datetime import datetime
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterBoolean,
                       QgsDataSourceUri,
                       QgsVectorLayer)
from processing.tools import postgis
from .common_functions import simplify_name, check_layer_is_valid, construct_sql_array_polygons, load_layer, execute_sql_queries

pluginPath = os.path.dirname(__file__)


class SummaryTable(QgsProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    # Constants used to refer to parameters and outputs
    DATABASE = 'DATABASE'
    STUDY_AREA = 'STUDY_AREA'
    ADD_TABLE = 'ADD_TABLE'
    OUTPUT = 'OUTPUT'
    OUTPUT_NAME = 'OUTPUT_NAME'

    def name(self):
        return 'SummaryTable'

    def displayName(self):
        return 'Tableau de synthèse par espèce'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'table.png'))

    def groupId(self):
        return 'test'

    def group(self):
        return 'Test'

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # Data base connection
        db_param = QgsProcessingParameterString(
            self.DATABASE,
            self.tr("1/ Sélectionnez votre connexion à la base de données LPO AuRA")
        )
        db_param.setMetadata(
            {
                'widget_wrapper': {'class': 'processing.gui.wrappers_postgis.ConnectionWidgetWrapper'}
            }
        )
        self.addParameter(db_param)

        # Input vector layer = study area
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STUDY_AREA,
                self.tr("2/ Sélectionnez votre zone d'étude, à partir de laquelle seront extraites les données du tableau de synthèse"),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        # Output PostGIS layer = summary table
        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.OUTPUT,
                self.tr('Couche en sortie'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

        # Output PostGIS layer name
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_NAME,
                self.tr("3/ Définissez un nom pour votre couche en sortie"),
                self.tr("Tableau synthèse")
            )
        )

        # Boolean : True = add the summary table in the DB ; False = don't
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ADD_TABLE,
                self.tr("Enregistrer les données en sortie dans une nouvelle table PostgreSQL"),
                False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the input vector layer = study area
        study_area = self.parameterAsSource(parameters, self.STUDY_AREA, context)
        # Retrieve the output PostGIS layer name and format it
        layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        ts = datetime.now()
        format_name = layer_name + " " + str(ts.strftime('%s'))

        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = summary table
        where = "is_valid and ST_within(geom, ST_union({}))".format(array_polygons)

        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        # Retrieve the boolean
        add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)

        if add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = simplify_name(format_name)
            # Define the SQL queries
            queries = [
                "DROP TABLE if exists {}".format(table_name),
                """CREATE TABLE {} AS (WITH data AS
                (SELECT source_id_sp, nom_sci AS nom_scientifique, nom_vern AS nom_vernaculaire, groupe_taxo,
                COUNT(*) AS nb_donnees, COUNT(DISTINCT(observateur)) AS nb_observateurs,
                COUNT(DISTINCT("date")) as nb_dates,
                COALESCE(SUM(CASE WHEN mortalite THEN 1 ELSE 0 END),0) AS nb_mortalite,
                max(sn.code_nidif) AS max_atlas_code, max(nombre_total) AS nb_individus_max,
                min (date_an) as premiere_observation, max(date_an) as derniere_observation,
                string_agg(distinct source,', ') as sources
                FROM src_lpodatas.observations obs
                LEFT JOIN referentiel.statut_nidif sn ON obs.oiso_code_nidif = sn.code_repro
                WHERE {}
                GROUP BY source_id_sp, nom_sci, nom_vern, groupe_taxo),
                synthese AS
                (SELECT DISTINCT source_id_sp, nom_scientifique, nom_vernaculaire, groupe_taxo,
                nb_donnees, nb_observateurs, nb_dates, nb_mortalite,
                sn2.statut_nidif, nb_individus_max,
                premiere_observation, derniere_observation, sources
                FROM data d
                LEFT JOIN referentiel.statut_nidif sn2 ON d.max_atlas_code = sn2.code_nidif
                ORDER BY groupe_taxo, source_id_sp)
                SELECT row_number() OVER () AS id, *
                FROM synthese)""".format(table_name, where),
                "ALTER TABLE {} add primary key (id)".format(table_name)
            ]
            # Execute the SQL queries
            execute_sql_queries(context, feedback, connection, queries)
            # Format the URI
            uri.setDataSource(None, table_name, None, "", "id")

        else:
            # Define the SQL query
            query = """(WITH data AS
                (SELECT source_id_sp, nom_sci AS nom_scientifique, nom_vern AS nom_vernaculaire, groupe_taxo,
                COUNT(*) AS nb_donnees, COUNT(DISTINCT(observateur)) AS nb_observateurs,
                COUNT(DISTINCT("date")) as nb_dates,
                COALESCE(SUM(CASE WHEN mortalite THEN 1 ELSE 0 END),0) AS nb_mortalite,
                max(sn.code_nidif) AS max_atlas_code, max(nombre_total) AS nb_individus_max,
                min (date_an) as premiere_observation, max(date_an) as derniere_observation,
                string_agg(distinct source,', ') as sources 
                FROM src_lpodatas.observations obs
                LEFT JOIN referentiel.statut_nidif sn ON obs.oiso_code_nidif = sn.code_repro 
                WHERE {} 
                GROUP BY source_id_sp, nom_sci, nom_vern, groupe_taxo),
                synthese AS
                (SELECT DISTINCT source_id_sp, nom_scientifique, nom_vernaculaire, groupe_taxo,
                nb_donnees, nb_observateurs, nb_dates, nb_mortalite,
                sn2.statut_nidif, nb_individus_max,
                premiere_observation, derniere_observation, sources 
                FROM data d 
                LEFT JOIN referentiel.statut_nidif sn2 ON d.max_atlas_code = sn2.code_nidif
                ORDER BY groupe_taxo, source_id_sp)
                SELECT row_number() OVER () AS id, *
                FROM synthese)""".format(where)
            # Format the URI
            uri.setDataSource("", query, None, "", "id")

        # Retrieve the output PostGIS layer = summary table
        layer_summary = QgsVectorLayer(uri.uri(), format_name, "postgres")
        # Check if the PostGIS layer is valid
        check_layer_is_valid(feedback, layer_summary)
        # Load the PostGIS layer
        load_layer(context, layer_summary)
        # Open the attribute table of the PostGIS layer
        iface.setActiveLayer(layer_summary)
        iface.showAttributeTable(layer_summary)

        return {self.OUTPUT: layer_summary.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SummaryTable()
