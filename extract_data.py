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
from qgis.utils import iface
from qgis.gui import QgsMessageBar

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
                       Qgis,
                       QgsProcessingException)
from processing.tools import postgis

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
        study_area = self.parameterAsVectorLayer(parameters, self.STUDY_AREA, context)
        # Check if the study area is a polygon layer
        if QgsWkbTypes.displayString(study_area.wkbType()) not in ['Polygon', 'MultiPolygon']:
            iface.messageBar().pushMessage("Erreur", "La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE.", level=Qgis.Critical, duration=10)
            raise QgsProcessingException(self.tr("La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE."))
        # Retrieve the CRS
        crs = study_area.dataProvider().crs().authid().split(':')[1]
        #feedback.pushInfo('SRC : {}'.format(crs))
        # Retrieve the potential features selection
        if len(study_area.selectedFeatures()) > 0:
            selection = study_area.selectedFeatures() # Get only the selected features
        else:
            selection = study_area.getFeatures() # If there is no feature selected, get all of them

        # Initialization of the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer
        where = "and ("
        # Format the geometry of src_lpodatas.observations if different from the study area
        if crs == '2154':
            geom = "geom"
        else:
            geom = "st_transform(geom, {})".format(crs)
        # For each entity in the study area...
        for feature in selection:
            # Retrieve the geometry
            area = feature.geometry() # QgsGeometry object
            # Retrieve the geometry type (single or multiple)
            geomSingleType = QgsWkbTypes.isSingleType(area.wkbType())
            # Increment the "where" clause
            if geomSingleType:
                where = where + "st_within({}, ST_PolygonFromText('{}', {})) or ".format(geom, area.asWkt(), crs)
            else:
                where = where + "st_within({}, ST_MPolyFromText('{}', {})) or ".format(geom, area.asWkt(), crs)
        # Remove the last "or" in the "where" clause which is useless
        where = where[:len(where)-4] + ")"
        #feedback.pushInfo('Clause where : {}'.format(where))

        # Define the SQL query
        query = """(select *
            from src_lpodatas.observations 
            where is_valid {})""".format(where)
        #feedback.pushInfo('Requête : {}'.format(query))
        
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # Retrieve the output PostGIS layer
            # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        #uri.setDataSource("src_lpodatas", "observations", "geom", "is valid {}".format(where))
        uri.setDataSource("", query, "geom", "", "id_observations")
        layer_obs = QgsVectorLayer(uri.uri(), "Données d'observations {}".format(study_area.name()), "postgres")

        # Check if the PostGIS layer is valid
        if not layer_obs.isValid():
            raise QgsProcessingException(self.tr("""La couche PostGIS chargée n'est pas valide !
                Checkez les logs de PostGIS pour visualiser les messages d'erreur."""))
        else:
             feedback.pushInfo('La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !')
                
        # Load the PostGIS layer
        root = context.project().layerTreeRoot()
        plugin_lpo_group = root.findGroup('Résultats plugin LPO')
        if not plugin_lpo_group:
            plugin_lpo_group = root.insertGroup(0, 'Résultats plugin LPO')
        context.project().addMapLayers([layer_obs], False)
        plugin_lpo_group.addLayer(layer_obs)
        # Variant
        # context.temporaryLayerStore().addMapLayer(layer_obs)
        # context.addLayerToLoadOnCompletion(
        #     layer_obs.id(),
        #     QgsProcessingContext.LayerDetails("Données d'observations", context.project(), self.OUTPUT)
        # )

        return {self.OUTPUT: layer_obs.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExtractData()
