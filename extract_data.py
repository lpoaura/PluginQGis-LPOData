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
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsDataSourceUri,
                       QgsVectorLayer,
                       QgsProcessingContext,
                       QgsProcessingException)

pluginPath = os.path.dirname(__file__)


class ExtractData(QgsProcessingAlgorithm):
    """
    This algorithm takes a vector layer with only one entity and
    returns an intersected points PostGIS layer.
    """

    # Constants used to refer to parameters and outputs
    ZONE_ETUDE = 'ZONE_ETUDE'
    OUTPUT = 'OUTPUT'

    def name(self):
        return 'ExtractData'

    def displayName(self):
        return 'Extract observation data'

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

        # Input vector layer
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
        # feedback.pushInfo('Bonjour')

        # Retrieve the input vector layer
        zone_etude = self.parameterAsVectorLayer(parameters, self.ZONE_ETUDE, context)
        # Retrieve the geometry of the unique entity
        for feature in zone_etude.getFeatures(): # There must be only one entity
            emprise = feature.geometry() # QgsGeometry object

        # URI --> Configures connection to database and the SQL query
        uri = QgsDataSourceUri()
        uri.setConnection("bdd.lpo-aura.org", "5432", "gnlpoaura", "lpoaura_egu", "Pra52@o2")
        query = "st_within(geom, ST_MPolyFromText('{}', 2154))".format(emprise.asWkt()) #Ou ST_PolygonFromText
        uri.setDataSource("src_vn", "observations", "geom", query)
        # Retrieve the PostGIS layer
        layer_obs = QgsVectorLayer(uri.uri(), "Données d'observations", "postgres")

        # Check if the PostGIS layer is valid
        if not layer_obs.isValid():
            raise QgsProcessingException(self.tr("""Cette couche n'est pas valide !
                Checker les logs de PostGIS pour visualiser les messages d'erreur."""))   
        
        # Prepare the PostGIS layer display
        context.temporaryLayerStore().addMapLayer(layer_obs)
        context.addLayerToLoadOnCompletion(
            layer_obs.id(),
            QgsProcessingContext.LayerDetails("Données d'observations", context.project(), self.OUTPUT)
        )

        return {self.OUTPUT: layer_obs.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExtractData()
