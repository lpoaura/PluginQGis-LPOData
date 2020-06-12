# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : summary_table_per_time_interval.py
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
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterBoolean,
                       QgsDataSourceUri,
                       QgsVectorLayer,
                       QgsProcessingException)
from processing.tools import postgis
from .common_functions import simplify_name, check_layer_is_valid, construct_sql_select_data_per_time_interval, construct_sql_array_polygons, construct_sql_taxons_filter, construct_sql_datetime_filter, load_layer, execute_sql_queries

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

class SummaryTablePerTimeInterval(QgsProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    # Constants used to refer to parameters and outputs
    DATABASE = 'DATABASE'
    STUDY_AREA = 'STUDY_AREA'
    TIME_INTERVAL = 'TIME_INTERVAL'
    ADD_FIVE_YEARS = 'ADD_FIVE_YEARS'
    START_MONTH = 'START_MONTH'
    START_YEAR = 'START_YEAR'
    END_MONTH = 'END_MONTH'
    END_YEAR = 'END_YEAR'
    TAXONOMIC_RANK = 'TAXONOMIC_RANK'
    AGG = 'AGG'
    GROUPE_TAXO = 'GROUPE_TAXO'
    REGNE = 'REGNE'
    PHYLUM = 'PHYLUM'
    CLASSE = 'CLASSE'
    ORDRE = 'ORDRE'
    FAMILLE = 'FAMILLE'
    GROUP1_INPN = 'GROUP1_INPN'
    GROUP2_INPN = 'GROUP2_INPN'
    EXTRA_WHERE = 'EXTRA_WHERE'
    OUTPUT = 'OUTPUT'
    OUTPUT_NAME = 'OUTPUT_NAME'
    ADD_TABLE = 'ADD_TABLE'

    def name(self):
        return 'SummaryTablePerYear'

    def displayName(self):
        return 'Tableau de synthèse par année'

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

        self.ts = datetime.now()
        self.db_variables = QgsSettings()
        self.interval_variables = ["Par année", "Par mois"]
        self.months_names_variables = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        self.taxonomic_ranks_variables = ["Espèces", "Groupes taxonomiques"]
        self.agg_variables = ["Nombre de données", "Nombre d'espèces"]

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

        ### Time interval and period ###
        time_interval = QgsProcessingParameterEnum(
            self.TIME_INTERVAL,
            self.tr("""<b>AGRÉGATION TEMPORELLE ET PÉRIODE</b><br/>
                <b>3/</b> Sélectionnez l'agrégation temporelle qui vous intéresse"""),
            self.interval_variables,
            allowMultiple=False
        )
        time_interval.setMetadata(
            {
                'widget_wrapper': {
                    'useCheckBoxes': True,
                    'columns': len(self.interval_variables)
                }
            }
        )
        self.addParameter(time_interval)

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ADD_FIVE_YEARS,
                self.tr("""Pour l'agrégation 'Par année' : cochez cette case si vous souhaitez ajouter des colonnes "bilan" par intervalle de 5 ans.
                NB : En cochant cette case, vous devez vous assurer de renseigner une période en années (cf. 4/) qui soit divisible par 5 (2011 - 2020 par exemple) !"""),
                False
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.START_MONTH,
                self.tr("""<b>4/</b> Sélectionnez la période qui vous intéresse<br/>
                    - Mois de début (<b>NB</b> : Nécessaire seulement si vous avez sélectionné l'agrégation '<u>Par mois</u>')"""),
                self.months_names_variables,
                allowMultiple=False,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.START_YEAR,
                self.tr("- Année de début :"),
                QgsProcessingParameterNumber.Integer,
                defaultValue=2010,
                minValue=1800,
                maxValue=int(self.ts.strftime('%Y'))
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.END_MONTH,
                self.tr("- Mois de fin (<b>NB</b> : Nécessaire seulement si vous avez sélectionné l'agrégation '<u>Par mois</u>')"),
                self.months_names_variables,
                allowMultiple=False,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.END_YEAR,
                self.tr("- Année de fin :"),
                QgsProcessingParameterNumber.Integer,
                defaultValue=self.ts.strftime('%Y'),
                minValue=1800,
                maxValue=int(self.ts.strftime('%Y'))
            )
        )

        # Taxonomic rank
        taxonomic_rank = QgsProcessingParameterEnum(
            self.TAXONOMIC_RANK,
            self.tr("""<b>RANG TAXONOMIQUE</b><br/>
                <b>5/</b> Sélectionnez le rang taxonomique qui vous intéresse"""),
            self.taxonomic_ranks_variables,
            allowMultiple=False
        )
        taxonomic_rank.setMetadata(
            {
                'widget_wrapper': {
                    'useCheckBoxes': True,
                    'columns': len(self.taxonomic_ranks_variables)
                }
            }
        )
        self.addParameter(taxonomic_rank)

        # Aggregation type
        aggregation_type = QgsProcessingParameterEnum(
            self.AGG,
            self.tr("""<b>TYPE D'AGRÉGATION</b><br/>
                <b>6/</b> Sélectionnez le type d'agrégation qui vous intéresse (<b>NB</b> : Si vous avez choisi 'Espèces' pour le rang taxonomique, 'Nombre de données' sera utilisé <u>par défaut</u>)"""),
            self.agg_variables,
            allowMultiple=False
        )
        aggregation_type.setMetadata(
            {
                'widget_wrapper': {
                    'useCheckBoxes': True,
                    'columns': len(self.agg_variables)
                }
            }
        )
        self.addParameter(aggregation_type)

        ### Taxons filters ###
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GROUPE_TAXO,
                self.tr("""<b>FILTRES DE REQUÊTAGE</b><br/>
                    <b>7/</b> Si nécessaire, sélectionnez un/plusieurs <u>taxon(s)</u> parmi les listes déroulantes (à choix multiples) proposées pour filtrer vos données d'observations<br/>
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

        # Extra "where" conditions
        self.addParameter(
            QgsProcessingParameterString(
                self.EXTRA_WHERE,
                self.tr("""<b>8/</b> Si nécessaire, ajoutez des <u>conditions "where"</u> supplémentaires dans l'encadré suivant, en langage SQL (commencez par <i>and</i>)"""),
                multiLine=True,
                optional=True
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
                self.tr("""<b>PARAMÉTRAGE DES RESULTATS EN SORTIE</b><br/>
                    <b>9/</b> Définissez un nom pour votre couche en sortie"""),
                self.tr("Tableau synthèse années")
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

        ### RETRIEVE PARAMETERS ###
        # Retrieve the input vector layer = study area
        study_area = self.parameterAsSource(parameters, self.STUDY_AREA, context)
        # Retrieve the output PostGIS layer name and format it
        layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        format_name = "{} {}".format(layer_name, str(self.ts.strftime('%Y%m%d_%H%M%S')))
        # Retrieve the time interval
        time_interval = self.interval_variables[self.parameterAsEnum(parameters, self.TIME_INTERVAL, context)]
        # Retrieve the period
        start_year = self.parameterAsInt(parameters, self.START_YEAR, context)
        end_year = self.parameterAsInt(parameters, self.END_YEAR, context)
        if end_year < start_year:
            raise QgsProcessingException("Veuillez renseigner une année de fin postérieure à l'année de début !")
        # Retrieve the taxonomic rank
        taxonomic_rank = self.taxonomic_ranks_variables[self.parameterAsEnum(parameters, self.TAXONOMIC_RANK, context)]
        # Retrieve the aggregation type
        aggregation_type = 'Nombre de données'
        if taxonomic_rank == 'Groupes taxonomiques':
            aggregation_type = self.agg_variables[self.parameterAsEnum(parameters, self.AGG, context)]            
        # Retrieve the taxons filters
        groupe_taxo = [self.db_variables.value('groupe_taxo')[i] for i in (self.parameterAsEnums(parameters, self.GROUPE_TAXO, context))]
        regne = [self.db_variables.value('regne')[i] for i in (self.parameterAsEnums(parameters, self.REGNE, context))]
        phylum = [self.db_variables.value('phylum')[i] for i in (self.parameterAsEnums(parameters, self.PHYLUM, context))]
        classe = [self.db_variables.value('classe')[i] for i in (self.parameterAsEnums(parameters, self.CLASSE, context))]
        ordre = [self.db_variables.value('ordre')[i] for i in (self.parameterAsEnums(parameters, self.ORDRE, context))]
        famille = [self.db_variables.value('famille')[i] for i in (self.parameterAsEnums(parameters, self.FAMILLE, context))]
        group1_inpn = [self.db_variables.value('group1_inpn')[i] for i in (self.parameterAsEnums(parameters, self.GROUP1_INPN, context))]
        group2_inpn = [self.db_variables.value('group2_inpn')[i] for i in (self.parameterAsEnums(parameters, self.GROUP2_INPN, context))]
        # Retrieve the extra "where" conditions
        extra_where = self.parameterAsString(parameters, self.EXTRA_WHERE, context)

        ### CONSTRUCT "SELECT" CLAUSE (SQL) ###
        # Select data according to the time interval and the period
        select_data = construct_sql_select_data_per_time_interval(self, time_interval, start_year, end_year, aggregation_type, parameters, context)
        # Select species info (optional)
        select_species_info = """source_id_sp, taxref_cdnom AS cd_nom, cd_ref, nom_rang as "Rang", groupe_taxo AS "Groupe taxo",
            obs.nom_vern AS "Nom vernaculaire", nom_sci AS "Nom scientifique\""""
        # Select taxonomic groups info (optional)
        select_taxo_groups_info = 'groupe_taxo AS "Groupe taxo"'
        ### CONSTRUCT "WHERE" CLAUSE (SQL) ###
        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = summary table
        where = "is_valid and ST_within(obs.geom, ST_union({}))".format(array_polygons)
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
        where += taxons_where
        # Complete the "where" clause with the extra conditions
        where += " " + extra_where
        ### CONSTRUCT "GROUP BY" CLAUSE (SQL) ###
        # Group by species (optional)
        group_by_species = "source_id_sp, taxref_cdnom, cd_ref, nom_rang, nom_sci, obs.nom_vern, " if taxonomic_rank == 'Espèces' else ""

        ### EXECUTE THE SQL QUERY ###
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        uri = postgis.uri_from_name(connection)
        # Define the SQL query
        query = """SELECT row_number() OVER () AS id, {}{}
            FROM src_lpodatas.observations obs
            LEFT JOIN taxonomie.taxref t ON obs.taxref_cdnom = t.cd_nom
            LEFT JOIN taxonomie.bib_taxref_rangs r ON t.id_rang = r.id_rang
            WHERE {}
            GROUP BY {}groupe_taxo
            ORDER BY groupe_taxo{}""".format(select_species_info if taxonomic_rank == 'Espèces' else select_taxo_groups_info, select_data, where, group_by_species, ", source_id_sp" if taxonomic_rank == 'Espèces' else "")
        feedback.pushInfo(query)
        # Retrieve the boolean add_table
        add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)
        if add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = simplify_name(format_name)
            # Define the SQL queries
            queries = [
                "DROP TABLE if exists {}".format(table_name),
                """CREATE TABLE {} AS ({})""".format(table_name, query),
                "ALTER TABLE {} add primary key (id)".format(table_name)
            ]
            # Execute the SQL queries
            execute_sql_queries(context, feedback, connection, queries)
            # Format the URI
            uri.setDataSource(None, table_name, None, "", "id")
        else:
            # Format the URI with the query
            uri.setDataSource("", "("+query+")", None, "", "id")

        ### GET THE OUTPUT LAYER ###
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
        return SummaryTablePerTimeInterval()
