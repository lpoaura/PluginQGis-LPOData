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
from qgis.PyQt.QtGui import QIcon

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsDataSourceUri,
                       QgsVectorLayer)
from processing.tools import postgis
from .common_functions import check_layer_geometry, check_layer_is_valid, construct_sql_array_polygons, load_layer

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

    def name(self):
        return 'ExtractData'

    def displayName(self):
        return 'Extract observation data from study area'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'extract_data.png'))

    def groupId(self):
        return 'initialisation'

    def group(self):
        return 'Initialisation'

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
                self.STUDY_AREA,
                self.tr("Zone d'étude"),
                [QgsProcessing.TypeVectorAnyGeometry]
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

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the input vector layer = study area
        study_area = self.parameterAsVectorLayer(parameters, self.STUDY_AREA, context)
        # Check if the study area is a polygon layer
        check_layer_geometry(study_area)

        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)        
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = biodiversity data
        where = "is_valid and st_within(geom, st_union({}))".format(array_polygons)

        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        uri.setDataSource("src_lpodatas", "observations", "geom", where)

        # Retrieve the output PostGIS layer = biodiversity data
        layer_obs = QgsVectorLayer(uri.uri(), "Données d'observations {}".format(study_area.name()), "postgres")
        # Check if the PostGIS layer is valid
        check_layer_is_valid(feedback, layer_obs)
        # Load the PostGIS layer
        load_layer(context, layer_obs)

        return {self.OUTPUT: layer_obs.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExtractData()
