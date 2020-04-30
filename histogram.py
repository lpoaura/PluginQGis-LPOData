# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : graph.py
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
import matplotlib.pyplot as plt
import numpy as np

pluginPath = os.path.dirname(__file__)


class Histogram(QgsProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    # Constants used to refer to parameters and outputs
    DATABASE = 'DATABASE'
    ZONE_ETUDE = 'ZONE_ETUDE'
    OUTPUT = 'OUTPUT'

    def name(self):
        return 'Histogram'

    def displayName(self):
        return 'Create an histogram'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'histogram.png'))

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

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the input vector layer = study area
        zone_etude = self.parameterAsVectorLayer(parameters, self.ZONE_ETUDE, context)
        # Initialization of the "where" clause of the SQL query, aiming to retrieve the data for the histogram
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

        query = """(select groupe_taxo, count(*) as nb_observations
            from src_lpodatas.observations 
            where is_valid {} 
            group by groupe_taxo 
            order by count(*) desc)""".format(where)
        
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # Retrieve the data for the histogram through a layer
            # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        uri.setDataSource("", query, None, "", "groupe_taxo")
        layer_histo = QgsVectorLayer(uri.uri(), "Histogram", "postgres")

        # Check if the PostGIS layer is valid
        if not layer_histo.isValid():
            raise QgsProcessingException(self.tr("""Cette couche n'est pas valide !
                Checker les logs de PostGIS pour visualiser les messages d'erreur."""))
        else:
             feedback.pushInfo('La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !')

        plt.rcdefaults()
        libel = [feature['groupe_taxo'] for feature in layer_histo.getFeatures()]
        feedback.pushInfo('Libellés : {}'.format(libel))
        #X = np.arange(len(libel))
        #feedback.pushInfo('Valeurs en X : {}'.format(X))
        Y = [int(feature['nb_observations']) for feature in layer_histo.getFeatures()]
        feedback.pushInfo('Valeurs en Y : {}'.format(Y))
        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        # fig, ax = plt.subplots()
        ax.bar(libel, Y)
        # ax.set_xticks(X)
        ax.set_xticklabels(libel)
        ax.set_ylabel(u'Nombre d\'observations')
        ax.set_title(u'Etat des connaissances par groupes d\'espèces')
        plt.show()
        
        return {}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Histogram()
