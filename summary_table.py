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
                       QgsProcessingParameterBoolean,
                       QgsDataSourceUri,
                       QgsVectorLayer,
                       QgsWkbTypes,
                       QgsProcessingContext,
                       Qgis,
                       QgsProcessingException)
from qgis.utils import iface
from processing.tools import postgis
from .common_functions import simplifyName

import processing

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
            QgsProcessingParameterVectorLayer(
                self.STUDY_AREA,
                self.tr("Zone d'étude"),
                [QgsProcessing.TypeVectorAnyGeometry]
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

        # Output PostGIS layer
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

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the output PostGIS layer name
        layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        format_name = simplifyName(layer_name)
        feedback.pushInfo('Nom formaté : {}'.format(format_name))

        # Retrieve the input vector layer = study area
        study_area = self.parameterAsVectorLayer(parameters, self.STUDY_AREA, context)
        # Check if the study area is a polygon layer
        if QgsWkbTypes.displayString(study_area.wkbType()) not in ['Polygon', 'MultiPolygon']:
            iface.messageBar().pushMessage("Erreur", "La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE.", level=Qgis.Critical, duration=10)
            raise QgsProcessingException(self.tr("La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE."))
        # Retrieve the CRS
        crs = study_area.dataProvider().crs().authid().split(':')[1]
        # Retrieve the potential features selection
        if len(study_area.selectedFeatures()) > 0:
            selection = study_area.selectedFeatures() # Get only the selected features
        else:
            selection = study_area.getFeatures() # If there is no feature selected, get all of them
        # Define the name of the output PostGIS layer (summary table) which will be loaded in the QGis project
        layer_name = "Tableau synthèse {}".format(study_area.name())

        # Initialization of the "where" clause of the SQL query, aiming to retrieve the data for the summary table
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

        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        # Retrieve the boolean
        add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)
        if add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = "summary_table_{}".format(study_area.name())
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
            # Format the URI
            uri.setDataSource(None, table_name, None, "", "id")
        else:
            # Define the SQL queries
            query = """(select row_number() OVER () AS id, source_id_sp, nom_sci, nom_vern, 
                count(*) as nb_observations, count(distinct(observateur)) as nb_observateurs, max(date_an) as derniere_observation 
                from src_lpodatas.observations 
                where is_valid {} 
                group by source_id_sp, nom_sci, nom_vern 
                order by source_id_sp)""".format(where)
            # Format the URI
            uri.setDataSource("", query, None, "", "id")
        # Retrieve the output PostGIS layer (summary table) which has just been created
        layer_summary = QgsVectorLayer(uri.uri(), layer_name, "postgres")

        # Check if the PostGIS layer is valid
        if not layer_summary.isValid():
            raise QgsProcessingException(self.tr("""Cette couche n'est pas valide !
                Checker les logs de PostGIS pour visualiser les messages d'erreur."""))
        else:
             feedback.pushInfo('La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !')
        
        # Load the PostGIS layer
        root = context.project().layerTreeRoot()
        plugin_lpo_group = root.findGroup('Résultats plugin LPO')
        if not plugin_lpo_group:
            plugin_lpo_group = root.insertGroup(0, 'Résultats plugin LPO')
        context.project().addMapLayers([layer_summary], False)
        plugin_lpo_group.addLayer(layer_summary)
        # Variant
        # context.temporaryLayerStore().addMapLayer(layer_summary)
        # context.addLayerToLoadOnCompletion(
        #     layer_summary.id(),
        #     QgsProcessingContext.LayerDetails(layer_name, context.project(), self.OUTPUT)
        # )

        # Open the attribute table of the PostGIS layer
        iface.setActiveLayer(layer_summary)
        iface.showAttributeTable(layer_summary)
        
        return {self.OUTPUT: layer_summary.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SummaryTable()
