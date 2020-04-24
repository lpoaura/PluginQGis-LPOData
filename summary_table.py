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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsDataSourceUri,
                       QgsVectorLayer,
                       QgsWkbTypes,
                       QgsProcessingContext,
                       QgsProcessingException)
from qgis.utils import iface
from processing.tools import postgis

import processing

pluginPath = os.path.dirname(__file__)


class SummaryTable(QgsProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    # Constants used to refer to parameters and outputs
    DATABASE = 'DATABASE'
    ZONE_ETUDE = 'ZONE_ETUDE'
    OUTPUT = 'OUTPUT'

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
            QgsProcessingParameterVectorLayer(
                self.ZONE_ETUDE,
                self.tr("Zone d'étude"),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        # Output PostGIS layer
        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.OUTPUT,
                self.tr('Couche en sortie'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the input vector layer = study area
        zone_etude = self.parameterAsVectorLayer(parameters, self.ZONE_ETUDE, context)
        # Define the name of the PostGIS summary table which will be created in the DB
        table_name = "summary_table_{}".format(zone_etude.name())
        # Define the name of the output PostGIS layer (summary table) which will be loaded in the QGis project
        layer_name = "Tableau synthèse {}".format(zone_etude.name())

        # Initialization of the "where" clause of the SQL query, aiming to create the summary table in the DB
        where = "and ("
        # For each entity in the study area...
        for feature in zone_etude.getFeatures():
            # Retrieve the geometry
            area = feature.geometry() # QgsGeometry object
            # Retrieve the geometry type (single or multiple)
            geomSingleType = QgsWkbTypes.isSingleType(area.wkbType())
            # Increment the "where" clause
            if geomSingleType:
                where = where + "st_within(geom, ST_PolygonFromText('{}', 2154)) or ".format(area.asWkt())
            else:
                where = where + "st_within(geom, ST_MPolyFromText('{}', 2154)) or ".format(area.asWkt())
        # Remove the last "or" in the "where" clause which is useless
        where = where[:len(where)-4] + ")"
        #feedback.pushInfo('Clause where : {}'.format(where))
        
        # Define the SQL queries
        queries = [
            "drop table if exists {}".format(table_name),
            """create table {} as (
            select row_number() OVER () AS id, source_id_sp, nom_sci, nom_vern, 
            count(*) as nb_observations, count(distinct(observateur)) as nb_observateurs, max(date_an) as derniere_observation 
            from src_lpodatas.observations 
            where is_valid {} 
            group by source_id_sp, nom_sci, nom_vern 
            order by source_id_sp)""".format(table_name, where),
            "alter table {} add primary key (id)".format(table_name)
        ]
        
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # Execute the SQL queries
        for query in queries:
            processing.run(
                'qgis:postgisexecutesql',
                {
                    'DATABASE': connection,
                    'SQL': query
                },
                is_child_algorithm=True,
                context=context,
                feedback=feedback
            )
            feedback.pushInfo('Requête SQL exécutée avec succès !')

        # Retrieve the output PostGIS layer (summary table) which has just been created
            # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        uri.setDataSource(None, table_name, None, "", "id")
        layer_summary = QgsVectorLayer(uri.uri(), layer_name, "postgres")

        # Check if the PostGIS layer is valid
        if not layer_summary.isValid():
            raise QgsProcessingException(self.tr("""Cette couche n'est pas valide !
                Checker les logs de PostGIS pour visualiser les messages d'erreur."""))
        else:
             feedback.pushInfo('La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !')
        
        # Load the PostGIS layer
        context.temporaryLayerStore().addMapLayer(layer_summary)
        context.addLayerToLoadOnCompletion(
            layer_summary.id(),
            QgsProcessingContext.LayerDetails(layer_name, context.project(), self.OUTPUT)
        )

        # Open the attribute table of the PostGIS layer
        iface.setActiveLayer(layer_summary)
        iface.showAttributeTable(layer_summary)
        
        return {self.OUTPUT: layer_summary.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SummaryTable()
