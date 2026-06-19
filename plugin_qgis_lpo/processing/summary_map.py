"""
/***************************************************************************
        ScriptsLPO : summary_map.py
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


class SummaryMap(BaseProcessingAlgorithm):
    return_geo_agg = True

    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "summarymap"
        self._display_name = "Carte de synthèse"
        self._output_name = self._display_name
        self._group_id = "map"
        self._group = "Cartes"
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
                Cet algorithme vous permet, à partir des données d'observation enregistrées
                dans la base de données LPO, de générer une <strong>carte de synthèse</strong>
                (couche de type polygones) par maille ou par commune (au choix)
                basée sur une <strong>zone d'étude</strong> présente dans votre projet QGIS (couche
                de type polygones). <strong style='color:#952132'>Les données d'absence et non valides sont
                exclues de ce traitement.</strong> Pour une maille à cheval sur la zone d'étude, l'ensemble des données
                de la maille est pris en compte, même celles à l'extérieur de la zone.
            </p>

            <p>
                <strong>Pour chaque entité géographique</strong>, la table attributaire de la
                nouvelle couche fournit les informations suivantes :
                <ul>
                    <li>Code de l'entité</li>
                    <li>Surface (en km<sup>2</sup>)</li>
                    <li>Nombre de données</li>
                    <li>Nombre de données / Nombre de données TOTAL</li>
                    <li>Nombre d'espèces</li>
                    <li>Nombre d'observateurs</li>
                    <li>Nombre de dates</li>
                    <li>Nombre de données de mortalité</li>
                    <li>Liste des espèces observées</li>
                </ul>
                Vous pouvez ensuite modifier la <strong>symbologie</strong> de la couche comme bon
                vous semble, en fonction du critère de votre choix.
            </p>

            <p>
                <span style='color:#0a84db'><u>IMPORTANT</u> : prenez le temps de lire
                <u>attentivement</u> les instructions pour chaque étape, et particulièrement
                les</span> <span style ='color:#952132'>informations en rouge</span>
                <span style='color:#0a84db'>!</span>
            </p>
            """
        self._icon = "map.png"
        self._short_help_string = ""
        self._is_map_layer = True
        self._return_geo_agg = True
        self._query = """
            WITH query_geom AS (
                SELECT  {query_area} AS geom
            ),
            areas AS MATERIALIZED (
                SELECT
                    la.id_area,
                    la.area_name,
                    la.area_code,
                    ROUND((ST_Area(la.geom)::numeric / 1000000), 2) AS area_surface,
                    la.geom
                FROM ref_geo.l_areas la
                JOIN query_geom g ON ST_Intersects(la.geom, g.geom)
                WHERE la.id_type = ref_geo.get_id_area_type('{areas_type}')
            ),
            cor_area_synthese AS MATERIALIZED (
                SELECT cas.id_area, cas.id_synthese
                FROM areas a
                JOIN gn_synthese.cor_area_synthese cas
                    ON cas.id_area = a.id_area
            ),
            aggregation AS (
                SELECT
                    cas.id_area,
                    COUNT(DISTINCT obs.id_synthese) AS nb_donnees,
                    COUNT(DISTINCT obs.cd_nom) FILTER (WHERE obs.id_rang = 'ES') AS nb_especes,
                    COUNT(DISTINCT obs.observateur) AS nb_observateurs,
                    COUNT(DISTINCT obs.date) AS nb_dates,
                    COUNT(DISTINCT obs.id_synthese) FILTER (WHERE obs.mortalite) AS nb_mortalite,
                    STRING_AGG(DISTINCT obs.nom_vern, ', ') FILTER (WHERE obs.id_rang = 'ES') AS especes
                FROM cor_area_synthese cas
                JOIN src_lpodatas.v_c_observations obs
                    ON obs.id_synthese = cas.id_synthese
                WHERE {where_filters}
                GROUP BY cas.id_area
            )
            SELECT
                ROW_NUMBER() OVER () AS id
                , a.id_area
                , a.area_name
                , a.area_code
                , a.area_surface                                                             AS "Surface (km2)"
                , COALESCE(agg.nb_donnees, 0)                                                AS "Nb de données"
                , ROUND(COALESCE(agg.nb_donnees, 0)::NUMERIC / NULLIF(a.area_surface, 0), 2) AS "Densité (Nb de données/km2)"
                , COALESCE(agg.nb_especes, 0)                                                AS "Nb d'espèces"
                , COALESCE(agg.nb_observateurs, 0)                                           AS "Nb d'observateurs"
                , COALESCE(agg.nb_dates, 0)                                                  AS "Nb de dates"
                , COALESCE(agg.nb_mortalite, 0)                                              AS "Nb de données de mortalité"
                , agg.especes                                                                AS "Liste des espèces observées"
                , a.geom
            FROM areas a
            LEFT JOIN aggregation agg ON agg.id_area = a.id_area
        """

    # def createInstance(self):  # noqa N802
    #     return SummaryMap()
