# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : summary_table_per_species.py
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

from qgis.core import QgsAction, QgsMessageLog, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface

from ..commons.generics import BaseQgsProcessingAlgorithm
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
from .qgis_processing_postgis import uri_from_name

plugin_path = os.path.dirname(__file__)


class SummaryTablePerSpecies(BaseQgsProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    output_name = "Tableau synthèse espèces"

    def name(self) -> str:
        return "SummaryTablePerSpecies"

    def displayName(self):  # noqa N802
        return "Tableau de synthèse par espèce"

    def icon(self) -> "QIcon":
        return QIcon(os.path.join(plugin_path, os.pardir, "icons", "table.png"))

    def groupId(self):  # noqa N802
        return "summary_tables"

    def group(self) -> str:
        return "Tableaux de synthèse"

    def shortDescription(self):  # noqa N802
        return self.tr(
            """<font style="font-size:18px"><b>Besoin d'aide ?</b> Vous pouvez vous référer au <b>Wiki</b> accessible sur ce lien : <a href="https://github.com/lpoaura/PluginQGis-LPOData/wiki" target="_blank">https://github.com/lpoaura/PluginQGis-LPOData/wiki</a>.</font><br/><br/>
            Cet algorithme vous permet, à partir des données d'observation enregistrées dans la base de données LPO, d'obtenir un <b>tableau de synthèse</b> par espèce (couche PostgreSQL) basé sur une <b>zone d'étude</b> présente dans votre projet QGis (couche de type polygones).
            <b style='color:#952132'>Les données d'absence sont exclues de ce traitement.</b><br/><br/>
            <b>Pour chaque espèce</b> observée dans la zone d'étude considérée, le tableau fournit les informations suivantes :
            <ul><li>Identifiant VisioNature de l'espèce</li>
            <li>cd_nom et cd_ref</li>
            <li>Rang</li>
            <li>Groupe taxonomique auquel elle appartient</li>
            <li>Nom français de l'espèce</li>
            <li>Nom scientifique de l'espèce</li>
            <li>Nombre de données</li>
            <li>Nombre de données / Nombre de données TOTAL</li>
            <li>Nombre d'observateurs</li>
            <li>Nombre de dates</li>
            <li>Nombre de données de mortalité</li>
            <li>LR France</li>
            <li>LR régionale</li>
            <li>Directive Habitats</li>
            <li>Directive Oiseaux</li>
            <li>Protection nationale</li>
            <li>Statut nicheur (pour les oiseaux)</li>
            <li>Nombre d'individus maximum recensé pour une observation</li>
            <li>Année de la première observation</li>
            <li>Année de la dernière observation</li>
            <li>Liste des communes</li>
            <li>Liste des sources VisioNature</li></ul><br/>
            <font style='color:#0a84db'><u>IMPORTANT</u> : Les <b>étapes indispensables</b> sont marquées d'une <b>étoile *</b> avant leur numéro. Prenez le temps de lire <u>attentivement</U> les instructions pour chaque étape, et particulièrement les</font> <font style ='color:#952132'>informations en rouge</font> <font style='color:#0a84db'>!</font>"""
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
        period_type = self.period_variables[
            self.parameterAsEnum(parameters, self.PERIOD, context)
        ]
        # Retrieve the extra "where" conditions
        extra_where = self.parameterAsString(parameters, self.EXTRA_WHERE, context)

        ### CONSTRUCT "WHERE" CLAUSE (SQL) ###
        # Construct the sql array containing the study area's features geometry
        array_polygons = construct_sql_array_polygons(study_area)
        # Define the "where" clause of the SQL query, aiming to retrieve the output PostGIS layer = summary table
        filters = [
            "is_valid",
            "is_present",
            f"ST_intersects(obs.geom, ST_union({array_polygons}))",
        ]
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
        filters.append(taxons_where)
        # Complete the "where" clause with the datetime filter
        datetime_where = construct_sql_datetime_filter(
            self, period_type, ts, parameters, context
        )
        filters.append(datetime_where)
        # Complete the "where" clause with the extra conditions

        filters.append(extra_where)

        where = " AND ".join(filters)

        ### EXECUTE THE SQL QUERY ###
        # Retrieve the data base connection name
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        # URI --> Configures connection to database and the SQL query
        # uri = postgis.uri_from_name(connection)
        uri = uri_from_name(connection)
        # Define the SQL query
        query = f"""WITH obs AS (
                        -- selection des cd_nom
                        SELECT obs.*
                        FROM src_lpodatas.v_c_observations_light obs
                        WHERE {where}),
                    communes AS (
                        --selection des communes
                        SELECT DISTINCT obs.id_synthese, la.area_name
                        FROM obs
                        LEFT JOIN gn_synthese.cor_area_synthese cor ON obs.id_synthese = cor.id_synthese
                        JOIN ref_geo.l_areas la ON cor.id_area = la.id_area
                        WHERE la.id_type = ref_geo.get_id_area_type('COM')),
                    atlas_code as (
                        --préparation codes atlas
                        SELECT cd_nomenclature, label_fr, hierarchy
                        FROM ref_nomenclatures.t_nomenclatures
                        WHERE id_type=(select ref_nomenclatures.get_id_nomenclature_type('VN_ATLAS_CODE'))
                    ),
                    total_count AS (
                        --comptage nb total individus
                        SELECT COUNT(*) AS total_count
                        FROM obs),
                     data AS (
                        --selection des données + statut
                        SELECT
                         obs.cd_ref
                        , obs.vn_id
                        , r.nom_rang
                        , groupe_taxo
                        , string_agg(distinct obs.nom_vern, ', ') nom_vern
                        , string_agg(distinct obs.nom_sci, ', ') nom_sci
                        , COUNT(DISTINCT obs.id_synthese)               AS nb_donnees
                        , COUNT(DISTINCT obs.observateur)               AS nb_observateurs
                        , COUNT(DISTINCT obs.date)                      AS nb_dates
                        , SUM(CASE WHEN mortalite THEN 1 ELSE 0 END)    AS nb_mortalite
                        , st.lr_france
                        , st.lr_r
                        , st.n2k
                        , st.prot_nat as protection_nat
                        , st.conv_berne
                        , st.conv_bonn
                        , max(ac.hierarchy)                             AS max_hierarchy_atlas_code
                        , max(obs.nombre_total)                         AS nb_individus_max
                        , min(obs.date_an)                              AS premiere_observation
                        , max(obs.date_an)                              AS derniere_observation
                        , string_agg(DISTINCT com.area_name, ', ')      AS communes
                        , string_agg(DISTINCT obs.source, ', ')         AS sources
                        FROM obs
                        LEFT JOIN atlas_code ac ON obs.oiso_code_nidif = ac.cd_nomenclature::int
                        LEFT JOIN taxonomie.bib_taxref_rangs r ON obs.id_rang = r.id_rang
                        LEFT JOIN communes com ON obs.id_synthese = com.id_synthese
                        left join taxonomie.mv_c_statut st on st.cd_ref=obs.cd_ref
                       GROUP BY
                         groupe_taxo
                        , obs.cd_ref
                        , obs.vn_id
                        , r.nom_rang
                        , st.lr_france
                        , st.lr_r
                        , st.n2k
                        , st.prot_nat
                        , st.conv_berne
                        , st.conv_bonn),
                    synthese AS (
                        SELECT DISTINCT
                         d.cd_ref
                        , vn_id
                        , nom_rang                                          AS "Rang"
                        , d.groupe_taxo              AS "Groupe taxo"
                        , nom_vern                                          AS "Nom vernaculaire"
                        , nom_sci                                           AS "Nom scientifique"
                        , nb_donnees                                        AS "Nb de données"
                        , ROUND(nb_donnees::DECIMAL / total_count, 4) * 100 AS "Nb données / nb données total (%)"
                        , nb_observateurs                                   AS "Nb d'observateurs"
                        , nb_dates                                          AS "Nb de dates"
                        , nb_mortalite                                      AS "Nb de données de mortalité"
                        , lr_france                                         AS "LR France"
                        , lr_r                                              AS "LR régionale"
                        , n2k                                           AS "Natura 2000"
                        , protection_nat                                    AS "Protection nationale"
                        , conv_berne                                        AS "Convention de Berne"
                        , conv_bonn                                         AS "Convention de Bonn"
                        , ac.label_fr                                       AS "Statut nidif"
                        , nb_individus_max                                  AS "Nb d'individus max"
                        , premiere_observation                              AS "Année première obs"
                        , derniere_observation                              AS "Année dernière obs"
                        , communes                                          AS "Liste de communes"
                        , sources                                           AS "Sources"
                        FROM total_count, data d
                        LEFT JOIN atlas_code ac ON d.max_hierarchy_atlas_code = ac.hierarchy
                        ORDER BY groupe_taxo,vn_id, nom_vern)
                    SELECT row_number() OVER () AS id, *
                    FROM synthese"""
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

        return {self.OUTPUT: self.layer_summary.id()}

    def postProcessAlgorithm(self, _context, _feedback) -> Dict:  # noqa N802
        # Open the attribute table of the PostGIS layer
        iface.showAttributeTable(self.layer_summary)
        iface.setActiveLayer(self.layer_summary)

        return {}

    def tr(self, string: str) -> str:
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):  # noqa N802
        return SummaryTablePerSpecies()
