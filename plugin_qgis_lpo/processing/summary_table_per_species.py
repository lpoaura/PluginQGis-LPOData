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

from .processing_algorithm import BaseProcessingAlgorithm


class SummaryTablePerSpecies(BaseProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    # layer_map = None

    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "SummaryTablePerSpecies"
        self._display_name = "Tableau de synthèse par espèce"
        self._output_name = "Tableau de synthese par espece"
        self._group_id = "summary_tables"
        self._group = "Tableaux de synthèse"
        self._short_description = """
            <p style='background-color:#61d8c6;color:white;font-style:bold;'>
                    <span style="color:green">✔</span> 
                    Cette extraction exclut les données <strong>non valides</strong> et 
                    <strong>d'absence</strong>.
            </p>
        
            <p style="font-size:18px">
                <strong>Besoin d'aide ?</strong>
                
                <br/>
                
                Vous pouvez vous référer aux options de         
                <a href="https://lpoaura.github.io/PluginQGis-LPOData/usage/advanced_filter.html" target="_blank">
                filtrage avancé</a>.
            </p>

            <p>
                Cet algorithme vous permet, à partir des données d'observation enregistrées dans la base de données LPO, d'obtenir un
                <strong>tableau de synthèse</strong> par espèce (couche PostgreSQL) basé sur une <strong>zone d'étude</strong> présente dans votre projet
                QGIS (couche de type polygones).
            
                <strong>Pour chaque espèce</strong> observée dans la zone d'étude considérée, le tableau fournit les informations suivantes :
                <ul>
                    <li>Identifiant VisioNature de l'espèce</li>
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
                    <li>LR régionale(s)</li>
                    <li>Directive Habitats</li>
                    <li>Directive Oiseaux</li>
                    <li>Protection nationale</li>
                    <li>Statut nicheur (pour les oiseaux)</li>
                    <li>Nombre d'individus maximum recensé pour une observation</li>
                    <li>Année de la première observation</li>
                    <li>Année de la dernière observation</li>
                    <li>Liste des communes</li>
                    <li>Liste des sources VisioNature</li>
                </ul>
            </p>

            <p>
                <span style='color:#0a84db'><u>IMPORTANT</u> : Prenez le temps de lire <u>attentivement</u> les instructions pour chaque étape, et
                particulièrement les </span><span style='color:#952132'>informations en rouge</span><span style='color:#0a84db'>!</span>
            </p>
        """
        self._icon = "table.png"
        # self._short_description = ""
        self._is_map_layer = False
        self._query = """
    WITH obs AS (
        /* selection des cd_nom */
        SELECT observations.id_synthese
            , observations.cd_nom
            , observations.nom_vern
            , observations.nom_sci
            , observations.observateur
            , observations.date
            , observations.date_an
            , observations.nombre_total
            , observations.source
            , observations.statut_repro
            , observations.id_rang
            , observations.groupe_taxo
            , observations.mortalite
        FROM src_lpodatas.v_c_observations observations
        WHERE ST_intersects(observations.geom, {query_area})
        and {where_filters}),
    communes AS (
        /* selection des communes */
        SELECT DISTINCT obs.id_synthese, la.area_name
        FROM obs
        LEFT JOIN gn_synthese.cor_area_synthese cor ON obs.id_synthese = cor.id_synthese
        JOIN ref_geo.l_areas la ON cor.id_area = la.id_area
        WHERE la.id_type = ref_geo.get_id_area_type('COM')),
    atlas_code as (
        /* préparation codes atlas */
        SELECT *
        FROM (VALUES ('Possible', 1), ('Probable', 2), ('Certain', 3)) AS t(label, hierarchy)
    ),
    total_count AS (
        /* comptage nb total d'observations */
        SELECT COUNT(*) AS total_count
        FROM obs),
     data AS (
        /* selection des données + statut */
        SELECT
         obs.cd_nom
        , r.nom_rang
        , groupe_taxo
        , string_agg(distinct obs.nom_vern, ', ') nom_vern
        , string_agg(distinct obs.nom_sci, ', ') nom_sci
        , COUNT(DISTINCT obs.id_synthese)               AS nb_donnees
        , COUNT(DISTINCT obs.observateur)               AS nb_observateurs
        , COUNT(DISTINCT obs.date)                      AS nb_dates
        , SUM(CASE WHEN mortalite THEN 1 ELSE 0 END)    AS nb_mortalite
        , {status_columns_fields}
          max(ac.hierarchy)                             AS max_hierarchy_atlas_code
        , max(obs.nombre_total)                         AS nb_individus_max
        , min(obs.date_an)                              AS premiere_observation
        , max(obs.date_an)                              AS derniere_observation
        , string_agg(DISTINCT com.area_name, ', ')      AS communes
        , string_agg(DISTINCT obs.source, ', ')         AS sources
       FROM obs
        LEFT JOIN atlas_code ac ON obs.statut_repro = ac.label
        LEFT JOIN taxonomie.bib_taxref_rangs r ON obs.id_rang = r.id_rang
        LEFT JOIN communes com ON obs.id_synthese = com.id_synthese
        LEFT JOIN taxonomie.mv_c_statut st ON st.cd_ref=obs.cd_nom
       GROUP BY
         groupe_taxo
        , {status_columns_fields}
          obs.cd_nom
        , r.nom_rang
        ),
    synthese AS (
        SELECT DISTINCT
         d.cd_nom
        , nom_rang                                          AS "Rang"
        , d.groupe_taxo              AS "Groupe taxo"
        , nom_vern                                          AS "Nom vernaculaire"
        , nom_sci                                           AS "Nom scientifique"
        , nb_donnees                                        AS "Nb de données"
        , ROUND(nb_donnees::DECIMAL / total_count, 4) * 100 AS "Nb données / nb données total (%)"
        , nb_observateurs                                   AS "Nb d'observateurs"
        , nb_dates                                          AS "Nb de dates"
        , nb_mortalite                                      AS "Nb de données de mortalité"
        , {status_columns_with_alias}
          ac.label                                          AS "Statut repro"
        , nb_individus_max                                  AS "Nb d'individus max"
        , premiere_observation                              AS "Année première obs"
        , derniere_observation                              AS "Année dernière obs"
        , communes                                          AS "Liste de communes"
        , sources                                           AS "Sources"
        FROM total_count, data d
        LEFT JOIN atlas_code ac ON d.max_hierarchy_atlas_code = ac.hierarchy
        ORDER BY groupe_taxo, nom_vern)
    SELECT row_number() OVER () AS id, *
    FROM synthese"""
