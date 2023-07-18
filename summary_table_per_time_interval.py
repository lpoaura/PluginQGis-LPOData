# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : summary_table_per_time_interval.py
        -------------------
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

__author__ = 'LPO AuRA'
__date__ = '2020-2023'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import os
from qgis.utils import iface
from datetime import datetime
import matplotlib.pyplot as plt

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsSettings,
                       QgsProcessingParameterProviderConnection,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterDefinition,
                       QgsVectorLayer,
                       QgsProcessingException,
                       QgsAction)
# from processing.tools import postgis
from .qgis_processing_postgis import uri_from_name
from .common_functions import simplify_name, check_layer_is_valid, construct_sql_select_data_per_time_interval, construct_sql_array_polygons, construct_queries_list, construct_sql_taxons_filter, load_layer, execute_sql_queries

pluginPath = os.path.dirname(__file__)


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
    TEST = 'TEST'
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
    OUTPUT_HISTOGRAM = 'OUTPUT_HISTOGRAM'
    ADD_HISTOGRAM = 'ADD_HISTOGRAM'

    def name(self):
        return 'SummaryTablePerTime Interval'

    def displayName(self):
        return 'Tableau de synthèse par intervalle de temps'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'table.png'))

    def groupId(self):
        return 'summary_tables'

    def group(self):
        return 'Tableaux de synthèse'

    def shortDescription(self):
        return self.tr("""<font style="font-size:18px"><b>Besoin d'aide ?</b> Vous pouvez vous référer au <b>Wiki</b> accessible sur ce lien : <a href="https://github.com/lpoaura/PluginQGis-LPOData/wiki" target="_blank">https://github.com/lpoaura/PluginQGis-LPOData/wiki</a>.</font><br/><br/>
            Cet algorithme vous permet, à partir des données d'observation enregistrées dans la base de données LPO,  d'obtenir un <b>tableau bilan</b> (couche PostgreSQL)...
            <ul><li>par année <u>ou</u> par mois (au choix)</li>
            <li>et par espèce <u>ou</u> par groupe taxonomique (au choix)</li></ul>
            ... basé sur une <b>zone d'étude</b> présente dans votre projet QGis (couche de type polygones) et selon une période de votre choix.
            <b style='color:#952132'>Les données d'absence sont exclues de ce traitement.</b><br/><br/>
            <font style='color:#0a84db'><u>IMPORTANT</u> : Les <b>étapes indispensables</b> sont marquées d'une <b>étoile *</b> avant leur numéro. Prenez le temps de lire <u>attentivement</U> les instructions pour chaque étape, et particulièrement les</font> <font style ='color:#952132'>informations en rouge</font> <font style='color:#0a84db'>!</font>""")

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
        # db_param = QgsProcessingParameterString(
        #     self.DATABASE,
        #     self.tr("""<b style="color:#0a84db">CONNEXION À LA BASE DE DONNÉES</b><br/>
        #         <b>*1/</b> Sélectionnez votre <u>connexion</u> à la base de données LPO"""),
        #     defaultValue='geonature_lpo'
        # )
        # db_param.setMetadata(
        #     {
        #         'widget_wrapper': {'class': 'processing.gui.wrappers_postgis.ConnectionWidgetWrapper'}
        #     }
        # )
        # self.addParameter(db_param)
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.DATABASE,
                self.tr("""<b style="color:#0a84db">CONNEXION À LA BASE DE DONNÉES</b><br/>
                    <b>*1/</b> Sélectionnez votre <u>connexion</u> à la base de données LPO"""),
                'postgres',
                defaultValue='geonature_lpo'
            )
        )

        # Input vector layer = study area
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STUDY_AREA,
                self.tr("""<b style="color:#0a84db">ZONE D'ÉTUDE</b><br/>
                    <b>*2/</b> Sélectionnez votre <u>zone d'étude</u>, à partir de laquelle seront extraits les résultats"""),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        ### Time interval and period ###
        time_interval = QgsProcessingParameterEnum(
            self.TIME_INTERVAL,
            self.tr("""<b style="color:#0a84db">AGRÉGATION TEMPORELLE ET PÉRIODE</b><br/>
                <b>*3/</b> Sélectionnez l'<u>agrégation temporelle</u> qui vous intéresse"""),
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

        add_five_years = QgsProcessingParameterEnum(
            self.ADD_FIVE_YEARS,
            self.tr("""<b>4/</b> <u style="color:#952132">Si (et seulement si !)</u> vous avez sélectionné l'<u>agrégation <b>Par année</b></u> :<br/> cochez la case ci-dessous si vous souhaitez ajouter des colonnes dîtes "bilan" par intervalle de 5 ans.<br/>
            <i style="color:#952132"><b>N.B.</b> : En cochant cette case, vous devez vous assurer de renseigner une période en années (cf. <b>*5/</b>) qui soit <b>divisible par 5</b>.<br/> Exemple : 2011 - 2020.</i>"""),
            ['Oui, je souhaite ajouter des colonnes dîtes "bilan" par intervalle de 5 ans'],
            allowMultiple=True,
            optional=True
        )
        add_five_years.setMetadata(
            {
                'widget_wrapper': {
                    'useCheckBoxes': True,
                    'columns': 1
                }
            }
        )
        self.addParameter(add_five_years)

        self.addParameter(
            QgsProcessingParameterEnum(
                self.START_MONTH,
                self.tr("""<b>*5/</b> Sélectionnez la <u>période</u> qui vous intéresse<br/>
                    - Mois de début <i style="color:#952132">(nécessaire seulement si vous avez sélectionné l'agrégation <b>Par mois</b>)</i> :"""),
                self.months_names_variables,
                allowMultiple=False,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.START_YEAR,
                self.tr("- *Année de début :"),
                QgsProcessingParameterNumber.Integer,
                defaultValue=2010,
                minValue=1800,
                maxValue=int(self.ts.strftime('%Y'))
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.END_MONTH,
                self.tr("""- Mois de fin <i style="color:#952132">(nécessaire seulement si vous avez sélectionné l'agrégation <b>Par mois</b>)</i> :"""),
                self.months_names_variables,
                allowMultiple=False,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.END_YEAR,
                self.tr("- *Année de fin :"),
                QgsProcessingParameterNumber.Integer,
                defaultValue=self.ts.strftime('%Y'),
                minValue=1800,
                maxValue=int(self.ts.strftime('%Y'))
            )
        )

        # Taxonomic rank
        taxonomic_rank = QgsProcessingParameterEnum(
            self.TAXONOMIC_RANK,
            self.tr("""<b style="color:#0a84db">RANG TAXONOMIQUE</b><br/>
                <b>*6/</b> Sélectionnez le <u>rang taxonomique</u> qui vous intéresse"""),
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
            self.tr("""<b style="color:#0a84db">AGRÉGATION DES RÉSULTATS</b><br/>
                <b>*7/</b> Sélectionnez le <u>type d'agrégation</u> qui vous intéresse pour les résultats<br/>
                <i style="color:#952132"><b>N.B.</b> : Si vous avez choisi <b>Espèces</b> pour le rang taxonomique, <b>Nombre de données</b> sera utilisé <b>par défaut</b></i>"""),
            self.agg_variables,
            allowMultiple=False,
            defaultValue="Nombre de données"
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
                self.tr("""<b style="color:#0a84db">FILTRES DE REQUÊTAGE</b><br/>
                    <b>8/</b> Si cela vous intéresse, vous pouvez sélectionner un/plusieurs <u>taxon(s)</u> dans la liste déroulante suivante (à choix multiples)<br/> pour filtrer vos données d'observations. <u>Sinon</u>, vous pouvez ignorer cette étape.<br/>
                    <i style="color:#952132"><b>N.B.</b> : D'autres filtres taxonomiques sont disponibles dans les paramètres avancés (plus bas, juste avant l'enregistrement des résultats).</i><br/>
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
        regne.setFlags(regne.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(regne)

        phylum = QgsProcessingParameterEnum(
            self.PHYLUM,
            self.tr("- Phylum :"),
            self.db_variables.value("phylum"),
            allowMultiple=True,
            optional=True
        )
        phylum.setFlags(phylum.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(phylum)

        classe = QgsProcessingParameterEnum(
            self.CLASSE,
            self.tr("- Classe :"),
            self.db_variables.value("classe"),
            allowMultiple=True,
            optional=True
        )
        classe.setFlags(classe.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(classe)

        ordre = QgsProcessingParameterEnum(
            self.ORDRE,
            self.tr("- Ordre :"),
            self.db_variables.value("ordre"),
            allowMultiple=True,
            optional=True
        )
        ordre.setFlags(ordre.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(ordre)

        famille = QgsProcessingParameterEnum(
            self.FAMILLE,
            self.tr("- Famille :"),
            self.db_variables.value("famille"),
            allowMultiple=True,
            optional=True
        )
        famille.setFlags(famille.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(famille)

        group1_inpn = QgsProcessingParameterEnum(
            self.GROUP1_INPN,
            self.tr("- Groupe 1 INPN (regroupement vernaculaire du référentiel national - niveau 1) :"),
            self.db_variables.value("group1_inpn"),
            allowMultiple=True,
            optional=True
        )
        group1_inpn.setFlags(group1_inpn.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(group1_inpn)

        group2_inpn = QgsProcessingParameterEnum(
            self.GROUP2_INPN,
            self.tr("- Groupe 2 INPN (regroupement vernaculaire du référentiel national - niveau 2) :"),
            self.db_variables.value("group2_inpn"),
            allowMultiple=True,
            optional=True
        )
        group2_inpn.setFlags(group2_inpn.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(group2_inpn)

        # Extra "where" conditions
        extra_where = QgsProcessingParameterString(
            self.EXTRA_WHERE,
            self.tr("""Vous pouvez ajouter des <u>conditions "where"</u> supplémentaires dans l'encadré suivant, en langage SQL <b style="color:#952132">(commencez par <i>and</i>)</b>"""),
            multiLine=True,
            optional=True
        )
        extra_where.setFlags(extra_where.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(extra_where)

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
                self.tr("""<b style="color:#0a84db">PARAMÉTRAGE DES RESULTATS EN SORTIE</b><br/>
                    <b>*9/</b> Définissez un <u>nom</u> pour votre couche PostGIS"""),
                self.tr("Tableau synthèse temps")
            )
        )

        # Boolean : True = add the summary table in the DB ; False = don't
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ADD_TABLE,
                self.tr("Enregistrer les résultats en sortie dans une nouvelle table PostgreSQL"),
                False
            )
        )

        ### Histogram ###
        add_histogram = QgsProcessingParameterEnum(
            self.ADD_HISTOGRAM,
            self.tr("""<b>10/</b> Cochez la case ci-dessous si vous souhaitez <u>exporter</u> les résultats sous la forme d'un <u>histogramme</u> du total par<br/> pas de temps choisi."""),
            ["Oui, je souhaite exporter les résultats sous la forme d'un histogramme du total par pas de temps choisi"],
            allowMultiple=True,
            optional=True
        )
        add_histogram.setMetadata(
            {
                'widget_wrapper': {
                    'useCheckBoxes': True,
                    'columns': 1
                }
            }
        )
        self.addParameter(add_histogram)

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_HISTOGRAM,
                self.tr("""<b style="color:#0a84db">ENREGISTREMENT DES RESULTATS</b><br/>
                <b>11/</b> <u style="color:#952132">Si (et seulement si !)</u> vous avez sélectionné l'export sous forme d'<u>histogramme</u>, veuillez renseigner un emplacement<br/> pour l'enregistrer sur votre ordinateur (au format image). <u>Dans le cas contraire</u>, vous pouvez ignorer cette étape.<br/>
                <font style='color:#06497a'><u>Aide</u> : Cliquez sur le bouton [...] puis sur 'Enregistrer vers un fichier...'</font>"""),
                self.tr('image PNG (*.png)'),
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
        format_name = f"{layer_name} {str(self.ts.strftime('%Y%m%d_%H%M%S'))}"
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
        # Retrieve the histogram parameter
        add_histogram = self.parameterAsEnums(parameters, self.ADD_HISTOGRAM, context)
        if len(add_histogram) > 0:
            output_histogram = self.parameterAsFileOutput(parameters, self.OUTPUT_HISTOGRAM, context)
            if output_histogram == "":
                raise QgsProcessingException("Veuillez renseigner un emplacement pour enregistrer votre histogramme !")

        ### CONSTRUCT "SELECT" CLAUSE (SQL) ###
        # Select data according to the time interval and the period
        select_data, x_var = construct_sql_select_data_per_time_interval(self, time_interval, start_year, end_year, aggregation_type, parameters, context)
        # Select species info (optional)
        select_species_info = """/*source_id_sp, */taxref_cdnom AS cd_nom, obs.cd_ref, nom_rang as "Rang", groupe_taxo AS "Groupe taxo",
            obs.nom_vern AS "Nom vernaculaire", nom_sci AS "Nom scientifique\""""
        # Select taxonomic groups info (optional)
        select_taxo_groups_info = 'groupe_taxo AS "Groupe taxo"'
        ### CONSTRUCT "WHERE" CLAUSE (SQL) ###
        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = summary table
        where = f"is_valid and is_present and ST_intersects(obs.geom, ST_union({array_polygons}))"
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
        group_by_species = "/*source_id_sp, */taxref_cdnom, obs.cd_ref, nom_rang, nom_sci, obs.nom_vern, " if taxonomic_rank == 'Espèces' else ""

        ### EXECUTE THE SQL QUERY ###
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        # uri = postgis.uri_from_name(connection)
        uri = uri_from_name(connection)
        # Define the SQL query
        query = f"""SELECT row_number() OVER () AS id, {select_species_info if taxonomic_rank == 'Espèces' else select_taxo_groups_info}{select_data}
            FROM src_lpodatas.v_c_observations_light obs
            LEFT JOIN taxonomie.bib_taxref_rangs r ON obs.id_rang = r.id_rang
            WHERE {where}
            GROUP BY {group_by_species}groupe_taxo
            ORDER BY groupe_taxo{ ", obs.nom_vern" if taxonomic_rank == 'Espèces' else ""}"""
        #feedback.pushInfo(query)
        # Retrieve the boolean add_table
        add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)
        if add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = simplify_name(format_name)
            # Define the SQL queries
            queries = construct_queries_list(table_name, query)
            # Execute the SQL queries
            execute_sql_queries(context, feedback, connection, queries)
            # Format the URI
            uri.setDataSource(None, table_name, None, "", "id")
        else:
            # Format the URI with the query
            uri.setDataSource("", "("+query+")", None, "", "id")

        ### GET THE OUTPUT LAYER ###
        # Retrieve the output PostGIS layer = summary table
        self.layer_summary = QgsVectorLayer(uri.uri(), format_name, "postgres")
        # Check if the PostGIS layer is valid
        check_layer_is_valid(feedback, self.layer_summary)
        # Load the PostGIS layer
        load_layer(context, self.layer_summary)
        # Add action to layer
        with open(os.path.join(pluginPath, 'format_csv.py'), 'r') as file:
            action_code = file.read()
        action = QgsAction(QgsAction.GenericPython, 'Exporter la couche sous format Excel dans mon dossier utilisateur avec la mise en forme adaptée', action_code, os.path.join(pluginPath, 'icons', 'excel.png'), False, 'Exporter sous format Excel', {'Layer'})
        self.layer_summary.actions().addAction(action)
        # JOKE
        with open(os.path.join(pluginPath, 'joke.py'), 'r') as file:
            joke_action_code = file.read()
        joke_action = QgsAction(QgsAction.GenericPython, 'Rédiger mon rapport', joke_action_code, os.path.join(pluginPath, 'icons', 'logo_LPO.png'), False, 'Rédiger mon rapport', {'Layer'})
        self.layer_summary.actions().addAction(joke_action)

        ### CONSTRUCT THE HISTOGRAM ###
        if len(add_histogram) > 0:
            plt.close()
            y_var = []
            for x in x_var:
                y = 0
                for feature in self.layer_summary.getFeatures():
                    y += feature[x]
                y_var.append(y)
            if len(x_var) <= 20:
                plt.subplots_adjust(bottom=0.4)
            elif len(x_var) <= 80:
                plt.figure(figsize=(20, 8))
                plt.subplots_adjust(bottom=0.3, left=0.05, right=0.95)
            else:
                plt.figure(figsize=(40, 16))
                plt.subplots_adjust(bottom=0.2, left=0.03, right=0.97)
            plt.bar(range(len(x_var)), y_var, tick_label=x_var)
            plt.xticks(rotation='vertical')
            x_label = time_interval.split(' ')[1].title()
            if x_label[-1] != 's':
                x_label += 's'
            plt.xlabel(x_label)
            plt.ylabel(aggregation_type)
            plt.title(f'{aggregation_type} {(time_interval[0].lower() + time_interval[1:])}')
            if output_histogram[-4:] != ".png":
                output_histogram += ".png"
            plt.savefig(output_histogram)
            #plt.show()

        return {self.OUTPUT: self.layer_summary.id()}

    def postProcessAlgorithm(self, context, feedback):
        # Open the attribute table of the PostGIS layer
        iface.showAttributeTable(self.layer_summary)
        iface.setActiveLayer(self.layer_summary)

        return {}

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SummaryTablePerTimeInterval()
