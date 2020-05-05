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
from .common_functions import simplify_name, check_layer_geometry, check_layer_is_valid, construct_sql_array_polygons, load_layer, execute_sql_queries

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
        return 'Create a summary table'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'summary_table.png'))

    def groupId(self):
        return 'treatments'

    def group(self):
        return 'Treatments'

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # Data base connection
        db_param = QgsProcessingParameterString(
            self.DATABASE,
            self.tr('Nom de la connexion à la base de données')
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
                self.tr("Zone d'étude"),
                [QgsProcessing.TypeVectorAnyGeometry]
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
                self.tr("Nom de la couche en sortie"),
                self.tr("tableau_synthese")
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

        # Retrieve the output PostGIS layer name
        layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        format_name = simplify_name(layer_name)
        feedback.pushInfo('Nom formaté : {}'.format(format_name))

        # Retrieve the input vector layer = study area
        study_area = self.parameterAsSource(parameters, self.STUDY_AREA, context)
        # Check if the study area is a polygon layer
        check_layer_geometry(study_area)
        # Define the name of the output PostGIS layer (summary table) which will be loaded in the QGis project
        layer_name = "Tableau synthèse {}".format(study_area.sourceName())

        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = summary table
        where = "is_valid and st_within(geom, st_union({}))".format(array_polygons)

        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        # Retrieve the boolean
        add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)

        if add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = "summary_table_{}".format(study_area.sourceName())
            # Define the SQL queries
            queries = [
                "drop table if exists {}".format(table_name),
                """create table {} as (
                select row_number() OVER () AS id, source_id_sp, nom_sci, nom_vern, 
                count(*) as nb_observations, count(distinct(observateur)) as nb_observateurs, max(date_an) as derniere_observation 
                from src_lpodatas.observations 
                where {} 
                group by source_id_sp, nom_sci, nom_vern 
                order by source_id_sp)""".format(table_name, where),
                "alter table {} add primary key (id)".format(table_name)
            ]
            # Execute the SQL queries
            execute_sql_queries(context, feedback, connection, queries)
            # Format the URI
            uri.setDataSource(None, table_name, None, "", "id")

        else:
            # Define the SQL queries
            query = """(select row_number() OVER () AS id, source_id_sp, nom_sci, nom_vern, 
                count(*) as nb_observations, count(distinct(observateur)) as nb_observateurs, max(date_an) as derniere_observation 
                from src_lpodatas.observations 
                where {} 
                group by source_id_sp, nom_sci, nom_vern 
                order by source_id_sp)""".format(where)
            # Format the URI
            uri.setDataSource("", query, None, "", "id")

        # Retrieve the output PostGIS layer = summary table
        layer_summary = QgsVectorLayer(uri.uri(), layer_name, "postgres")
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
