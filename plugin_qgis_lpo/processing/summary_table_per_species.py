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
        self._short_description = """<font style="font-size:18px"><b>Besoin d'aide ?</b> Vous pouvez vous référer au <b>Wiki</b> accessible sur ce lien : <a
        href="https://lpoaura.github.io/PluginQGis-LPOData/index.html"
        target="_blank">https://lpoaura.github.io/PluginQGis-LPOData/index.html</a>.</font><br /><br />
Cet algorithme vous permet, à partir des données d'observation enregistrées dans la base de données LPO, d'obtenir un
<b>tableau de synthèse</b> par espèce (couche PostgreSQL) basé sur une <b>zone d'étude</b> présente dans votre projet
QGIS (couche de type polygones).
<b style='color:#952132'>Les données d'absence, ainsi que les données non valides sont exclues de ce traitement.</b><br /><br />
<b>Pour chaque espèce</b> observée dans la zone d'étude considérée, le tableau fournit les informations suivantes :
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
<br />
<font style='color:#0a84db'><u>IMPORTANT</u> : Prenez le temps de lire <u>attentivement</U> les instructions pour chaque étape, et
    particulièrement les</font>
<font style='color:#952132'>informations en rouge</font>
<font style='color:#0a84db'>!</font>"""
        self._icon = "table.png"
        # self._short_description = ""
        self._is_map_layer = False
        self._query = """
    WITH obs AS (
        /* selection des cd_nom */
        SELECT observations.*
        FROM src_lpodatas.v_c_observations_light observations
        WHERE ST_intersects(observations.geom, ST_union({array_polygons}))
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
        SELECT cd_nomenclature, label_fr, hierarchy
        FROM ref_nomenclatures.t_nomenclatures
        WHERE id_type=(
            select ref_nomenclatures.get_id_nomenclature_type('VN_ATLAS_CODE')
            )
    ),
    total_count AS (
        /* comptage nb total individus */
        SELECT COUNT(*) AS total_count
        FROM obs),
     data AS (
        /* selection des données + statut */
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
        , {lr_columns_fields}
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
        , {lr_columns_fields}
        , st.n2k
        , st.prot_nat
        , st.conv_berne
        , st.conv_bonn),
    synthese AS (
        SELECT DISTINCT
         d.cd_ref
        , array_to_string(vn_id,', ')                       as vn_id
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
        , {lr_columns_with_alias}
        , n2k                                               AS "Natura 2000"
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
