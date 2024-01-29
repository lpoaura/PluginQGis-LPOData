# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : state_of_knowledge.py
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

import os
from datetime import datetime
from typing import Dict

import matplotlib.pyplot as plt
from qgis.core import (
    QgsAction,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputVectorLayer,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterProviderConnection,
    QgsProcessingParameterString,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface

from ..commons.helpers import (
    check_layer_is_valid,
    construct_queries_list,
    construct_sql_array_polygons,
    construct_sql_datetime_filter,
    construct_sql_taxons_filter,
    execute_sql_queries,
    load_layer,
    simplify_name,
)

# from processing.tools import postgis
from ..commons.widgets import DateTimeWidget
from .qgis_processing_postgis import uri_from_name

plugin_path = os.path.dirname(__file__)


class StateOfKnowledge(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs
    DATABASE = "DATABASE"
    STUDY_AREA = "STUDY_AREA"
    TAXONOMIC_RANK = "TAXONOMIC_RANK"
    GROUPE_TAXO = "GROUPE_TAXO"
    REGNE = "REGNE"
    PHYLUM = "PHYLUM"
    CLASSE = "CLASSE"
    ORDRE = "ORDRE"
    FAMILLE = "FAMILLE"
    GROUP1_INPN = "GROUP1_INPN"
    GROUP2_INPN = "GROUP2_INPN"
    PERIOD = "PERIOD"
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
    EXTRA_WHERE = "EXTRA_WHERE"
    OUTPUT = "OUTPUT"
    OUTPUT_NAME = "OUTPUT_NAME"
    ADD_TABLE = "ADD_TABLE"
    OUTPUT_HISTOGRAM = "OUTPUT_HISTOGRAM"
    HISTOGRAM_OPTIONS = "HISTOGRAM_OPTIONS"

    def name(self) -> str:
        return "StateOfKnowledgeOld"

    def displayName(self):  # noqa N802
        return "État des connaissances (old)"

    def icon(self) -> "QIcon":
        return QIcon(os.path.join(plugin_path, os.pardir, "icons", "table.png"))

    def groupId(self):  # noqa N802
        return "summary_tables"

    def group(self) -> str:
        return "Tableaux de synthèse"

    def shortDescription(self):  # noqa N802
        return self.tr(
            """<font style="font-size:18px"><b>Besoin d'aide ?</b> Vous pouvez vous référer au <b>Wiki</b> accessible sur ce lien : <a href="https://github.com/lpoaura/PluginQGis-LPOData/wiki" target="_blank">https://github.com/lpoaura/PluginQGis-LPOData/wiki</a>.</font><br/><br/>
            Cet algorithme vous permet, à partir des données d'observation enregistrées dans la base de données LPO,  d'obtenir un <b>état des connaissances</b> par taxon (couche PostgreSQL), basé sur une <b>zone d'étude</b> présente dans votre projet QGis (couche de type polygones) et selon le rang taxonomique de votre choix, à savoir : groupes taxonomiques / règnes / phylum / classes / ordres / familles / groupes 1 INPN / groupes 2 INPN. <b style='color:#952132'>Les données d'absence sont exclues de ce traitement.</b><br/><br/>
            Cet état des connaissances correspond en fait à un <b>tableau</b>, qui, <b>pour chaque taxon</b> observé dans la zone d'étude considérée, fournit les informations suivantes :
            <ul><li>Nombre de données</li>
            <li>Nombre de données / Nombre de données TOTAL</li>
            <li>Nombre d'espèces</li>
            <li>Nombre d'observateurs</li>
            <li>Nombre de dates</li>
            <li>Nombre de données de mortalité</li>
            <li>Nombre d'individus maximum recensé pour une observation</li>
            <li>Année de la première observation</li>
            <li>Année de la dernière observation</li>
            <li>Liste des espèces impliquées</li>
            <li>Liste des communes</li>
            <li>Liste des sources VisioNature</li></ul><br/>
            <font style='color:#0a84db'><u>IMPORTANT</u> : Les <b>étapes indispensables</b> sont marquées d'une <b>étoile *</b> avant leur numéro. Prenez le temps de lire <u>attentivement</U> les instructions pour chaque étape, et particulièrement les</font> <font style ='color:#952132'>informations en rouge</font> <font style='color:#0a84db'>!</font>"""
        )

    def initAlgorithm(self, _config=None):  # noqa N802
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.db_variables = QgsSettings()
        self.taxonomic_ranks_variables = [
            "Groupes taxonomiques",
            "Règnes",
            "Phylum",
            "Classes",
            "Ordres",
            "Familles",
            "Groupes 1 INPN (regroupement vernaculaire du référentiel national - niveau 1)",
            "Groupes 2 INPN (regroupement vernaculaire du référentiel national - niveau 2)",
        ]
        self.period_variables = [
            "Pas de filtre temporel",
            "5 dernières années",
            "10 dernières années",
            "Cette année",
            "Date de début - Date de fin (à définir ci-dessous)",
        ]
        histogram_variables = [
            "Pas d'histogramme",
            "Histogramme du nombre de données par taxon",
            "Histogramme du nombre d'espèces par taxon",
            "Histogramme du nombre d'observateurs par taxon",
            "Histogramme du nombre de dates par taxon",
            "Histogramme du nombre de données de mortalité par taxon",
        ]
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.DATABASE,
                self.tr(
                    """<b style="color:#0a84db">CONNEXION À LA BASE DE DONNÉES</b><br/>
                    <b>*1/</b> Sélectionnez votre <u>connexion</u> à la base de données LPO"""
                ),
                "postgres",
                defaultValue="geonature_lpo",
            )
        )

        # Input vector layer = study area
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STUDY_AREA,
                self.tr(
                    """<b style="color:#0a84db">ZONE D'ÉTUDE</b><br/>
                    <b>*2/</b> Sélectionnez votre <u>zone d'étude</u>, à partir de laquelle seront extraits les résultats"""
                ),
                [QgsProcessing.TypeVectorPolygon],
            )
        )

        # Taxonomic rank
        taxonomic_rank = QgsProcessingParameterEnum(
            self.TAXONOMIC_RANK,
            self.tr(
                """<b style="color:#0a84db">RANG TAXONOMIQUE</b><br/>
                <b>*3/</b> Sélectionnez le <u>rang taxonomique</u> qui vous intéresse"""
            ),
            self.taxonomic_ranks_variables,
            allowMultiple=False,
        )
        taxonomic_rank.setMetadata(
            {
                "widget_wrapper": {
                    "useCheckBoxes": True,
                    "columns": len(self.taxonomic_ranks_variables) / 2,
                }
            }
        )
        self.addParameter(taxonomic_rank)

        ### Taxons filters ###
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GROUPE_TAXO,
                self.tr(
                    """<b style="color:#0a84db">FILTRES DE REQUÊTAGE</b><br/>
                    <b>4/</b> Si cela vous intéresse, vous pouvez sélectionner un/plusieurs <u>taxon(s)</u> dans la liste déroulante suivante (à choix multiples)<br/> pour filtrer vos données d'observations. <u>Sinon</u>, vous pouvez ignorer cette étape.<br/>
                    <i style="color:#952132"><b>N.B.</b> : D'autres filtres taxonomiques sont disponibles dans les paramètres avancés (plus bas, juste avant l'enregistrement des résultats).</i><br/>
                    - Groupes taxonomiques :"""
                ),
                self.db_variables.value("groupe_taxo"),
                allowMultiple=True,
                optional=True,
            )
        )

        regne = QgsProcessingParameterEnum(
            self.REGNE,
            self.tr("- Règnes :"),
            self.db_variables.value("regne"),
            allowMultiple=True,
            optional=True,
        )
        regne.setFlags(regne.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(regne)

        phylum = QgsProcessingParameterEnum(
            self.PHYLUM,
            self.tr("- Phylum :"),
            self.db_variables.value("phylum"),
            allowMultiple=True,
            optional=True,
        )
        phylum.setFlags(phylum.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(phylum)

        classe = QgsProcessingParameterEnum(
            self.CLASSE,
            self.tr("- Classe :"),
            self.db_variables.value("classe"),
            allowMultiple=True,
            optional=True,
        )
        classe.setFlags(classe.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(classe)

        ordre = QgsProcessingParameterEnum(
            self.ORDRE,
            self.tr("- Ordre :"),
            self.db_variables.value("ordre"),
            allowMultiple=True,
            optional=True,
        )
        ordre.setFlags(ordre.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(ordre)

        famille = QgsProcessingParameterEnum(
            self.FAMILLE,
            self.tr("- Famille :"),
            self.db_variables.value("famille"),
            allowMultiple=True,
            optional=True,
        )
        famille.setFlags(
            famille.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(famille)

        group1_inpn = QgsProcessingParameterEnum(
            self.GROUP1_INPN,
            self.tr(
                "- Groupe 1 INPN (regroupement vernaculaire du référentiel national - niveau 1) :"
            ),
            self.db_variables.value("group1_inpn"),
            allowMultiple=True,
            optional=True,
        )
        group1_inpn.setFlags(
            group1_inpn.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(group1_inpn)

        group2_inpn = QgsProcessingParameterEnum(
            self.GROUP2_INPN,
            self.tr(
                "- Groupe 2 INPN (regroupement vernaculaire du référentiel national - niveau 2) :"
            ),
            self.db_variables.value("group2_inpn"),
            allowMultiple=True,
            optional=True,
        )
        group2_inpn.setFlags(
            group2_inpn.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(group2_inpn)

        ### Datetime filter ###
        period = QgsProcessingParameterEnum(
            self.PERIOD,
            self.tr(
                "<b>*5/</b> Sélectionnez une <u>période</u> pour filtrer vos données d'observations"
            ),
            self.period_variables,
            allowMultiple=False,
            optional=False,
        )
        period.setMetadata(
            {
                "widget_wrapper": {
                    "useCheckBoxes": True,
                    "columns": len(self.period_variables) / 2,
                }
            }
        )
        self.addParameter(period)

        start_date = QgsProcessingParameterString(
            self.START_DATE,
            """- Date de début <i style="color:#952132">(nécessaire seulement si vous avez sélectionné l'option <b>Date de début - Date de fin</b>)</i> :""",
            defaultValue="",
            optional=True,
        )
        start_date.setMetadata({"widget_wrapper": {"class": DateTimeWidget}})
        self.addParameter(start_date)

        end_date = QgsProcessingParameterString(
            self.END_DATE,
            """- Date de fin <i style="color:#952132">(nécessaire seulement si vous avez sélectionné l'option <b>Date de début - Date de fin</b>)</i> :""",
            optional=True,
        )
        end_date.setMetadata({"widget_wrapper": {"class": DateTimeWidget}})
        self.addParameter(end_date)

        # Extra "where" conditions
        extra_where = QgsProcessingParameterString(
            self.EXTRA_WHERE,
            self.tr(
                """Vous pouvez ajouter des <u>conditions "where"</u> supplémentaires dans l'encadré suivant, en langage SQL <b style="color:#952132">(commencez par <i>and</i>)</b>"""
            ),
            multiLine=True,
            optional=True,
        )
        extra_where.setFlags(
            extra_where.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(extra_where)

        # Output PostGIS layer = summary table
        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.OUTPUT,
                self.tr("Couche en sortie"),
                QgsProcessing.TypeVectorAnyGeometry,
            )
        )

        # Output PostGIS layer name
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_NAME,
                self.tr(
                    """<b style="color:#0a84db">PARAMÉTRAGE DES RESULTATS EN SORTIE</b><br/>
                    <b>*6/</b> Définissez un <u>nom</u> pour votre nouvelle couche PostGIS"""
                ),
                self.tr("État des connaissances"),
            )
        )

        # Boolean : True = add the summary table in the DB ; False = don't
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ADD_TABLE,
                self.tr(
                    "Enregistrer les résultats en sortie dans une nouvelle table PostgreSQL"
                ),
                defaultValue=False,
            )
        )

        ### Histogram ###
        histogram_options = QgsProcessingParameterEnum(
            self.HISTOGRAM_OPTIONS,
            self.tr(
                "<b>7/</b> Si cela vous intéresse, vous pouvez <u>exporter</u> les résultats sous forme d'<u>histogramme</u>. Dans ce cas, sélectionnez le type<br/> d'histogramme qui vous convient. <u>Sinon</u>, vous pouvez ignorer cette étape."
            ),
            histogram_variables,
            defaultValue="Pas d'histogramme",
        )
        # histogram_options.setMetadata(
        #     {
        #         "widget_wrapper": {
        #             "useCheckBoxes": True,
        #             "columns": len(histogram_variables) / 3,
        #         }
        #     }
        # )
        self.addParameter(histogram_options)

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_HISTOGRAM,
                self.tr(
                    """<b style="color:#0a84db">ENREGISTREMENT DES RESULTATS</b><br/>
                <b>8/</b> <u style="color:#952132">Si (et seulement si !)</u> vous avez sélectionné un type d'<u>histogramme</u>, veuillez renseigner un emplacement pour l'enregistrer<br/> sur votre ordinateur (au format image). <u>Dans le cas contraire</u>, vous pouvez ignorer cette étape.<br/>
                <font style='color:#06497a'><u>Aide</u> : Cliquez sur le bouton [...] puis sur 'Enregistrer vers un fichier...'</font>"""
                ),
                self.tr("image PNG (*.png)"),
                optional=True,
                createByDefault=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa N802
        """
        Here is where the processing itself takes place.
        """

        ### RETRIEVE PARAMETERS ###
        # Retrieve the input vector layer = study area
        study_area = self.parameterAsSource(parameters, self.STUDY_AREA, context)
        # Retrieve the output PostGIS layer name and format it
        layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        ts = datetime.now()
        format_name = f"{layer_name} {str(ts.strftime('%Y%m%d_%H%M%S'))}"
        # Retrieve the taxonomic rank
        taxonomic_ranks_labels = [
            "Groupe taxo",
            "Règne",
            "Phylum",
            "Classe",
            "Ordre",
            "Famille",
            "Groupe 1 INPN",
            "Groupe 2 INPN",
        ]
        taxonomic_ranks_db = [
            "groupe_taxo",
            "regne",
            "phylum",
            "classe",
            "ordre",
            "famille",
            "obs.group1_inpn",
            "obs.group2_inpn",
        ]
        taxonomic_rank_label = taxonomic_ranks_labels[
            self.parameterAsEnum(parameters, self.TAXONOMIC_RANK, context)
        ]
        taxonomic_rank_db = taxonomic_ranks_db[
            self.parameterAsEnum(parameters, self.TAXONOMIC_RANK, context)
        ]
        # Retrieve the taxons filters
        groupe_taxo = [
            self.db_variables.value("groupe_taxo")[i]
            for i in (self.parameterAsEnums(parameters, self.GROUPE_TAXO, context))
        ]
        regne = [
            self.db_variables.value("regne")[i]
            for i in (self.parameterAsEnums(parameters, self.REGNE, context))
        ]
        phylum = [
            self.db_variables.value("phylum")[i]
            for i in (self.parameterAsEnums(parameters, self.PHYLUM, context))
        ]
        classe = [
            self.db_variables.value("classe")[i]
            for i in (self.parameterAsEnums(parameters, self.CLASSE, context))
        ]
        ordre = [
            self.db_variables.value("ordre")[i]
            for i in (self.parameterAsEnums(parameters, self.ORDRE, context))
        ]
        famille = [
            self.db_variables.value("famille")[i]
            for i in (self.parameterAsEnums(parameters, self.FAMILLE, context))
        ]
        group1_inpn = [
            self.db_variables.value("group1_inpn")[i]
            for i in (self.parameterAsEnums(parameters, self.GROUP1_INPN, context))
        ]
        group2_inpn = [
            self.db_variables.value("group2_inpn")[i]
            for i in (self.parameterAsEnums(parameters, self.GROUP2_INPN, context))
        ]
        # Retrieve the datetime filter
        period = self.period_variables[
            self.parameterAsEnum(parameters, self.PERIOD, context)
        ]
        # Retrieve the extra "where" conditions
        extra_where = self.parameterAsString(parameters, self.EXTRA_WHERE, context)
        # Retrieve the histogram parameter
        histogram_variables = [
            "Pas d'histogramme",
            "Nb de données",
            "Nb d'espèces",
            "Nb d'observateurs",
            "Nb de dates",
            "Nb de données de mortalité",
        ]
        histogram_option = histogram_variables[
            self.parameterAsEnum(parameters, self.HISTOGRAM_OPTIONS, context)
        ]
        if histogram_option != "Pas d'histogramme":
            output_histogram = self.parameterAsFileOutput(
                parameters, self.OUTPUT_HISTOGRAM, context
            )
            if output_histogram == "":
                raise QgsProcessingException(
                    "Veuillez renseigner un emplacement pour enregistrer votre histogramme !"
                )

        ### CONSTRUCT "WHERE" CLAUSE (SQL) ###
        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = summary table
        where = f"is_valid and is_present and ST_within(obs.geom, ST_union({array_polygons}))"
        # Define a dictionnary with the aggregated taxons filters and complete the "where" clause thanks to it
        taxons_filters = {
            "groupe_taxo": groupe_taxo,
            "regne": regne,
            "phylum": phylum,
            "classe": classe,
            "ordre": ordre,
            "famille": famille,
            "obs.group1_inpn": group1_inpn,
            "obs.group2_inpn": group2_inpn,
        }
        taxons_where = construct_sql_taxons_filter(taxons_filters)
        where += taxons_where
        # Complete the "where" clause with the datetime filter
        datetime_where = construct_sql_datetime_filter(
            self, period, ts, parameters, context
        )
        where += datetime_where
        # Complete the "where" clause with the extra conditions
        where += " " + extra_where

        ### EXECUTE THE SQL QUERY ###
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        # uri = postgis.uri_from_name(connection)
        uri = uri_from_name(connection)
        # Define the SQL query
        query = f"""WITH obs AS (
            SELECT obs.*
            FROM src_lpodatas.v_c_observations_light obs
            WHERE {where}),
        communes AS (
            SELECT DISTINCT obs.id_synthese, la.area_name
            FROM obs
            JOIN gn_synthese.cor_area_synthese cor ON obs.id_synthese = cor.id_synthese
            JOIN ref_geo.l_areas la ON cor.id_area = la.id_area
            WHERE la.id_type = (SELECT ref_geo.get_id_area_type('COM'))),
        total_count AS (
            SELECT COUNT(*) AS total_count
            FROM obs)
        SELECT row_number() OVER () AS id, COALESCE({taxonomic_rank_db}, 'Pas de correspondance taxref') AS "{taxonomic_rank_label}", {'groupe_taxo AS "Groupe taxo", ' if taxonomic_rank_label in ['Ordre', 'Famille'] else ""}
            COUNT(*) AS "Nb de données",
            ROUND(COUNT(*)::decimal/total_count, 4)*100 AS "Nb données / Nb données TOTAL (%)",
            COUNT(DISTINCT obs.cd_ref) FILTER (WHERE id_rang='ES') AS "Nb d'espèces",
            COUNT(DISTINCT observateur) AS "Nb d'observateurs",
            COUNT(DISTINCT date) AS "Nb de dates",
            COUNT(DISTINCT obs.id_synthese) FILTER (WHERE mortalite) AS "Nb de données de mortalité",
            max(nombre_total) AS "Nb d'individus max",
            min (date_an) AS "Année première obs", max(date_an) AS "Année dernière obs",
            string_agg(DISTINCT obs.nom_vern,', ') FILTER (WHERE id_rang='ES') AS "Liste des espèces",
            string_agg(DISTINCT com.area_name,', ') AS "Communes",
            string_agg(DISTINCT obs.source,', ') AS "Sources"
        FROM total_count, obs
        LEFT JOIN communes com ON obs.id_synthese = com.id_synthese
        GROUP BY {"groupe_taxo, " if taxonomic_rank_label in ['Ordre', 'Famille'] else ""}{taxonomic_rank_db}, total_count
        ORDER BY {"groupe_taxo, " if taxonomic_rank_label in ['Ordre', 'Famille'] else ""}{taxonomic_rank_db}"""
        # feedback.pushInfo(query)
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
            uri.setDataSource("", "(" + query + ")", None, "", "id")

        ### GET THE OUTPUT LAYER ###
        # Retrieve the output PostGIS layer = summary table
        self.layer_summary = QgsVectorLayer(uri.uri(), format_name, "postgres")
        # Check if the PostGIS layer is valid
        check_layer_is_valid(feedback, self.layer_summary)
        # Load the PostGIS layer
        load_layer(context, self.layer_summary)
        # Add action to layer
        with open(os.path.join(plugin_path, "format_csv.py"), "r") as file:
            action_code = file.read()
        action = QgsAction(
            QgsAction.GenericPython,
            "Exporter la couche sous format Excel dans mon dossier utilisateur avec la mise en forme adaptée",
            action_code,
            os.path.join(plugin_path, "icons", "excel.png"),
            False,
            "Exporter sous format Excel",
            {"Layer"},
        )
        self.layer_summary.actions().addAction(action)
        # JOKE
        with open(os.path.join(plugin_path, "joke.py"), "r") as file:
            joke_action_code = file.read()
        joke_action = QgsAction(
            QgsAction.GenericPython,
            "Rédiger mon rapport",
            joke_action_code,
            os.path.join(plugin_path, "icons", "logo_LPO.png"),
            False,
            "Rédiger mon rapport",
            {"Layer"},
        )
        self.layer_summary.actions().addAction(joke_action)

        ### CONSTRUCT THE HISTOGRAM ###
        if histogram_option != "Pas d'histogramme":
            plt.close()
            x_var = [
                (
                    feature[taxonomic_rank_label]
                    if feature[taxonomic_rank_label] != "Pas de correspondance taxref"
                    else "Aucune correspondance"
                )
                for feature in self.layer_summary.getFeatures()
            ]
            y_var = [
                int(feature[histogram_option])
                for feature in self.layer_summary.getFeatures()
            ]
            if len(x_var) <= 20:
                plt.subplots_adjust(bottom=0.5)
            elif len(x_var) <= 80:
                plt.figure(figsize=(20, 8))
                plt.subplots_adjust(bottom=0.3, left=0.05, right=0.95)
            else:
                plt.figure(figsize=(40, 16))
                plt.subplots_adjust(bottom=0.2, left=0.03, right=0.97)
            plt.bar(range(len(x_var)), y_var, tick_label=x_var)
            plt.xticks(rotation="vertical")
            plt.xlabel(
                self.taxonomic_ranks_variables[
                    self.parameterAsEnum(parameters, self.TAXONOMIC_RANK, context)
                ]
            )
            plt.ylabel(histogram_option.replace("Nb", "Nombre"))
            plt.title(
                f'{histogram_option.replace("Nb", "Nombre")} par {taxonomic_rank_label[0].lower() + taxonomic_rank_label[1:].replace("taxo", "taxonomique")}'
            )
            if output_histogram[-4:] != ".png":
                output_histogram += ".png"
            plt.savefig(output_histogram)
            # plt.show()

        return {self.OUTPUT: self.layer_summary.id()}

    def postProcessAlgorithm(self, _context, _feedback) -> Dict:  # noqa N802
        # Open the attribute table of the PostGIS layer
        iface.showAttributeTable(self.layer_summary)
        iface.setActiveLayer(self.layer_summary)

        return {}

    def tr(self, string: str) -> str:
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):  # noqa N802
        return StateOfKnowledge()
