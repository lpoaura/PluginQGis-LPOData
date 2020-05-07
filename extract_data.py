# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : extract_data.py
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

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsDataSourceUri,
                       QgsVectorLayer,
                       QgsField)
from processing.tools import postgis
from .common_functions import check_layer_is_valid, construct_sql_array_polygons, load_layer

pluginPath = os.path.dirname(__file__)


class ExtractData(QgsProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns an intersected points PostGIS layer.
    """

    # Constants used to refer to parameters and outputs
    DATABASE = 'DATABASE'
    STUDY_AREA = 'STUDY_AREA'
    OUTPUT = 'OUTPUT'
    OUTPUT_NAME = 'OUTPUT_NAME'
    TABLE = 'TABLE'

    TARGET_CRS = 'TARGET_CRS'

    def name(self):
        return 'ExtractData'

    def displayName(self):
        return "Extraction de données d'observation"

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'extract_data.png'))

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
                self.tr("2/ Sélectionnez votre zone d'étude, à partir de laquelle seront extraites les données d'observations"),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        # Output PostGIS layer = biodiversity data
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
                self.tr("3/ Définissez un nom pour votre nouvelle couche"),
                self.tr("Données d'observation")
            )
        )

        # Output PostGIS layer = biodiversity data
        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         self.OUTPUT,
        #         self.tr('4/ Enregistrez votre nouvelle couche...'),
        #         QgsProcessing.TypeVectorPoint
        #     )
        # )

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
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = biodiversity data
        where = "is_valid and ST_within(geom, ST_union({}))".format(array_polygons)

        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        uri.setDataSource("src_lpodatas", "observations", "geom", where)

        # Retrieve the output PostGIS layer = biodiversity data
        layer_obs = QgsVectorLayer(uri.uri(), format_name, "postgres")
        # Check if the PostGIS layer is valid
        check_layer_is_valid(feedback, layer_obs)
        # Load the PostGIS layer
        load_layer(context, layer_obs)

        # Retrieve sink
        # try:
        #     (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, layer_obs.fields(), layer_obs.wkbType(), layer_obs.sourceCrs())
        # except Exception as e:
        #     raise e
        
        # try:
        #     if sink is None:
        #         raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        #     for feature in layer_obs.getFeatures():
        #         sink.addFeature(feature)
        # except Exception as e:
        #     raise e

        #return {self.OUTPUT: dest_id}
        return {self.OUTPUT: layer_obs.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExtractData()
