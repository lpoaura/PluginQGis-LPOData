# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : summary_map.py
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
from qgis.utils import iface
from datetime import datetime

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt, QCoreApplication, QDate
from qgis.PyQt.QtWidgets import QDateEdit
from processing.gui.wrappers import WidgetWrapper

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsSettings,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSink,
                       QgsDataSourceUri,
                       QgsVectorLayer,
                       QgsProcessingException)
from processing.tools import postgis
from .common_functions import simplify_name, check_layer_is_valid, construct_sql_array_polygons, construct_sql_taxons_filter, construct_sql_datetime_filter, load_layer, execute_sql_queries, format_layer_export

pluginPath = os.path.dirname(__file__)


class DateTimeWidget(WidgetWrapper):
    """
    QDateTimeEdit widget with calendar pop up
    """

    def createWidget(self):
        self._combo = QDateEdit()
        self._combo.setCalendarPopup(True)
        today = QDate.currentDate()
        self._combo.setDate(today)
        return self._combo

    def value(self):
        date_chosen = self._combo.dateTime()
        return date_chosen.toString(Qt.ISODate)

class SummaryMap(QgsProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    # Constants used to refer to parameters and outputs
    DATABASE = 'DATABASE'
    STUDY_AREA = 'STUDY_AREA'
    AREAS_TYPE = 'AREAS_TYPE'
    GROUPE_TAXO = 'GROUPE_TAXO'
    REGNE = 'REGNE'
    PHYLUM = 'PHYLUM'
    CLASSE = 'CLASSE'
    ORDRE = 'ORDRE'
    FAMILLE = 'FAMILLE'
    GROUP1_INPN = 'GROUP1_INPN'
    GROUP2_INPN = 'GROUP2_INPN'
    PERIOD = 'PERIOD'
    START_DATE = 'START_DATE'
    END_DATE = 'END_DATE'
    EXTRA_WHERE = 'EXTRA_WHERE'
    OUTPUT = 'OUTPUT'
    OUTPUT_NAME = 'OUTPUT_NAME'
    ADD_TABLE = 'ADD_TABLE'

    def name(self):
        return 'SummaryMap'

    def displayName(self):
        return 'Carte de synthèse'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'map.png'))

    def groupId(self):
        return 'test'

    def group(self):
        return 'Test'

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.db_variables = QgsSettings()
        self.period_variables = ["Pas de filtre temporel", "5 dernières années", "10 dernières années", "Date de début - Date de fin (à définir ci-dessous)"]

        # Data base connection
        db_param = QgsProcessingParameterString(
            self.DATABASE,
            self.tr("""<b>CONNEXION À LA BASE DE DONNÉES</b><br/>
                <b>1/</b> Sélectionnez votre connexion à la base de données LPO AuRA (<i>gnlpoaura</i>)"""),
            defaultValue='gnlpoaura'
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
                self.tr("""<b>ZONE D'ÉTUDE</b><br/>
                    <b>2/</b> Sélectionnez votre zone d'étude, à partir de laquelle seront extraites les résultats"""),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        # Areas type
        self.addParameter(
            QgsProcessingParameterEnum(
                self.AREAS_TYPE,
                self.tr("""<b>TYPE D'ENTITÉS GÉOGRAPHIQUES</b><br/>
                    <b>3/</b> Sélectionnez le type d'entités géographiques qui vous intéresse"""),
                self.db_variables.value("areas_types"),
                allowMultiple=False
            )
        )

        ### Taxons filters ###
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GROUPE_TAXO,
                self.tr("""<b>FILTRES DE REQUÊTAGE</b><br/>
                    <b>4/</b> Si nécessaire, sélectionnez un/plusieurs <u>taxon(s)</u> parmi les listes déroulantes (à choix multiples) proposées pour filtrer vos données d'observations<br/>
                    - Groupes taxonomiques :"""),
                self.db_variables.value("groupe_taxo"),
                allowMultiple=True,
                optional=True
            )
        )

        regne = QgsProcessingParameterEnum(
            self.REGNE,
            self.tr("- Règnes :"),
            self.db_variables.value("regne"),
            allowMultiple=True,
            optional=True
        )
        #regne.setFlags(regne.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(regne)

        phylum = QgsProcessingParameterEnum(
            self.PHYLUM,
            self.tr("- Phylum :"),
            self.db_variables.value("phylum"),
            allowMultiple=True,
            optional=True
        )
        #phylum.setFlags(phylum.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(phylum)

        classe = QgsProcessingParameterEnum(
            self.CLASSE,
            self.tr("- Classe :"),
            self.db_variables.value("classe"),
            allowMultiple=True,
            optional=True
        )
        #classe.setFlags(classe.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(classe)

        ordre = QgsProcessingParameterEnum(
            self.ORDRE,
            self.tr("- Ordre :"),
            self.db_variables.value("ordre"),
            allowMultiple=True,
            optional=True
        )
        #ordre.setFlags(ordre.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(ordre)

        famille = QgsProcessingParameterEnum(
            self.FAMILLE,
            self.tr("- Famille :"),
            self.db_variables.value("famille"),
            allowMultiple=True,
            optional=True
        )
        #famille.setFlags(famille.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(famille)

        group1_inpn = QgsProcessingParameterEnum(
            self.GROUP1_INPN,
            self.tr("- Groupe 1 INPN :"),
            self.db_variables.value("group1_inpn"),
            allowMultiple=True,
            optional=True
        )
        #group1_inpn.setFlags(group1_inpn.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(group1_inpn)

        group2_inpn = QgsProcessingParameterEnum(
            self.GROUP2_INPN,
            self.tr("- Groupe 2 INPN :"),
            self.db_variables.value("group2_inpn"),
            allowMultiple=True,
            optional=True
        )
        #group2_inpn.setFlags(group2_inpn.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(group2_inpn)

        ### Datetime filter ###
        period_type = QgsProcessingParameterEnum(
            self.PERIOD,
            self.tr("<b>5/</b> Si nécessaire, sélectionnez une <u>période</u> pour filtrer vos données d'observations"),
            self.period_variables,
            allowMultiple=False,
            optional=True
        )
        period_type.setMetadata(
            {
                'widget_wrapper': {
                    'useCheckBoxes': True,
                    'columns': len(self.period_variables)
                }
            }
        )
        self.addParameter(period_type)

        start_date = QgsProcessingParameterString(
            self.START_DATE,
            '- Date de début :',
            defaultValue="",
            optional=True
        )
        start_date.setMetadata(
            {'widget_wrapper': {'class': DateTimeWidget}}
        )
        self.addParameter(start_date)

        end_date = QgsProcessingParameterString(
            self.END_DATE,
            '- Date de fin :',
            optional=True
        )
        end_date.setMetadata(
            {'widget_wrapper': {'class': DateTimeWidget}}
        )
        self.addParameter(end_date)

        # Extra "where" conditions
        self.addParameter(
            QgsProcessingParameterString(
                self.EXTRA_WHERE,
                self.tr("""<b>6/</b> Si nécessaire, ajoutez des <u>conditions "where"</u> supplémentaires dans l'encadré suivant, en langage SQL (commencez par <i>and</i>)"""),
                multiLine=True,
                optional=True
            )
        )

        # Output PostGIS layer name
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_NAME,
                self.tr("""<b>PARAMÉTRAGE DES RESULTATS EN SORTIE</b><br/>
                    <b>7/</b> Définissez un nom pour votre nouvelle couche"""),
                self.tr("Carte synthèse")
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

        # Output PostGIS layer = summary map data
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('<b>8/</b> Si nécessaire, enregistrez votre nouvelle couche (cette étape est <b>optionnelle</b>, vous pouvez aussi <i>Ignorer la sortie</i>)'),
                QgsProcessing.TypeVectorPolygon,
                optional=True,
                createByDefault=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        ### RETRIEVE PARAMETERS ###
        # Retrieve the input vector layer = study area
        study_area = self.parameterAsSource(parameters, self.STUDY_AREA, context)
        # Retrieve the output PostGIS layer name and format it
        layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        ts = datetime.now()
        format_name = "{} {}".format(layer_name, str(ts.strftime('%Y%m%d_%H%M%S')))
        # Retrieve the areas type
        areas_type = self.db_variables.value("areas_types")[self.parameterAsEnum(parameters, self.AREAS_TYPE, context)]
        # Retrieve the taxons filters
        groupe_taxo = [self.db_variables.value('groupe_taxo')[i] for i in (self.parameterAsEnums(parameters, self.GROUPE_TAXO, context))]
        regne = [self.db_variables.value('regne')[i] for i in (self.parameterAsEnums(parameters, self.REGNE, context))]
        phylum = [self.db_variables.value('phylum')[i] for i in (self.parameterAsEnums(parameters, self.PHYLUM, context))]
        classe = [self.db_variables.value('classe')[i] for i in (self.parameterAsEnums(parameters, self.CLASSE, context))]
        ordre = [self.db_variables.value('ordre')[i] for i in (self.parameterAsEnums(parameters, self.ORDRE, context))]
        famille = [self.db_variables.value('famille')[i] for i in (self.parameterAsEnums(parameters, self.FAMILLE, context))]
        group1_inpn = [self.db_variables.value('group1_inpn')[i] for i in (self.parameterAsEnums(parameters, self.GROUP1_INPN, context))]
        group2_inpn = [self.db_variables.value('group2_inpn')[i] for i in (self.parameterAsEnums(parameters, self.GROUP2_INPN, context))]
        # Retrieve the datetime filter
        period_type = self.period_variables[self.parameterAsEnum(parameters, self.PERIOD, context)]
        # Retrieve the extra "where" conditions
        extra_where = self.parameterAsString(parameters, self.EXTRA_WHERE, context)

        ### CONSTRUCT "WHERE" CLAUSE (SQL) ###
        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = map data
        where = "ST_intersects(la.geom, ST_union({}))".format(array_polygons)
        # Define the "where" filter for "Nb de données" and "Nb d'espèces"
        where_filter = "is_valid"
        # Define a dictionnary with the aggregated taxons filters and complete the "where" clause thanks to it
        taxons_filters = {
            "groupe_taxo": groupe_taxo,
            "regne": regne,
            "phylum": phylum,
            "classe": classe,
            "ordre": ordre,
            "famille": famille,
            "obs.group1_inpn": group1_inpn,
            "obs.group2_inpn": group2_inpn
        }
        taxons_where = construct_sql_taxons_filter(taxons_filters)
        where_filter += taxons_where
        # Complete the "where" filter with the datetime filter
        datetime_where = construct_sql_datetime_filter(self, period_type, ts, parameters, context)
        where_filter += datetime_where
        # Complete the "where" filter with the extra conditions
        where_filter += " " + extra_where
        
        #feedback.pushInfo(where)

        ### EXECUTE THE SQL QUERY ###
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        # Define the SQL query
        query = """SELECT id_area, area_name AS "Nom", area_code AS "Code", la.geom,
                COUNT(*) filter (where {}) AS "Nb de données",
                COUNT(DISTINCT taxref_cdnom) filter (where {}) AS "Nb d'espèces"
            FROM src_lpodatas.observations obs
            LEFT JOIN taxonomie.taxref t ON obs.taxref_cdnom = t.cd_nom
            RIGHT JOIN ref_geo.l_areas la ON public.ST_INTERSECTS(obs.geom, la.geom)
            LEFT JOIN ref_geo.bib_areas_types bib ON la.id_type=bib.id_type
            WHERE type_name='{}' and {}
            GROUP BY id_area, area_name, area_code, la.geom
            ORDER BY area_code""".format(where_filter, where_filter, areas_type, where)
        feedback.pushInfo(query)
        # Retrieve the boolean add_table
        add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)
        if add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = simplify_name(format_name)
            # Define the SQL queries
            queries = [
                "DROP TABLE if exists {}".format(table_name),
                "CREATE TABLE {} AS ({})".format(table_name, query),
                "ALTER TABLE {} add primary key (id_area)".format(table_name)
            ]
            # Execute the SQL queries
            execute_sql_queries(context, feedback, connection, queries)
            # Format the URI
            uri.setDataSource(None, table_name, "geom", "", "id_area")
        else:
            # Format the URI with the query
            uri.setDataSource("", "("+query+")", "geom", "", "id_area")

        ### GET THE OUTPUT LAYER ###
        # Retrieve the output PostGIS layer = map data
        layer_map = QgsVectorLayer(uri.uri(), format_name, "postgres")
        # Check if the PostGIS layer is valid
        check_layer_is_valid(feedback, layer_map)
        
        ### MANAGE EXPORT ###
        # Create new valid fields for the sink
        new_fields = format_layer_export(layer_map)
        # Retrieve the sink for the export
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, new_fields, layer_map.wkbType(), layer_map.sourceCrs())
        if sink is None:
            # Load the PostGIS layer and return it
            load_layer(context, layer_map)
            return {self.OUTPUT: layer_map.id()}
        else:
            # Fill the sink and return it
            for feature in layer_map.getFeatures():
                sink.addFeature(feature)
            return {self.OUTPUT: dest_id}
        
        return {self.OUTPUT: layer_map.id()}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SummaryMap()
