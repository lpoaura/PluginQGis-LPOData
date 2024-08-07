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

        self._name = "SummaryMap"
        self._display_name = "Carte de synthèse"
        self._output_name = self._display_name
        self._group_id = "Map"
        self._group = "Cartes"
        self._short_description = """<font style="font-size:18px"><b>Besoin d'aide ?</b>
        Vous pouvez vous référer au <b>Wiki</b> accessible sur ce lien :
        <a href="https://lpoaura.github.io/PluginQGis-LPOData/index.html" target="_blank">
        https://lpoaura.github.io/PluginQGis-LPOData/index.html</a>.</font><br/><br/>
            Cet algorithme vous permet, à partir des données d'observation enregistrées
            dans la base de données LPO, de générer une <b>carte de synthèse</b>
            (couche PostGIS de type polygones) par maille ou par commune (au choix)
            basée sur une <b>zone d'étude</b> présente dans votre projet QGIS (couche
            de type polygones). <b style='color:#952132'>Les données d'absence ainsi que les données non valides sont
            exclues de ce traitement.</b><br/><br/>
            <b>Pour chaque entité géographique</b>, la table attributaire de la
            nouvelle couche fournit les informations suivantes :
            <ul><li>Code de l'entité</li>
            <li>Surface (en km<sup>2</sup>)</li>
            <li>Nombre de données</li>
            <li>Nombre de données / Nombre de données TOTAL</li>
            <li>Nombre d'espèces</li>
            <li>Nombre d'observateurs</li>
            <li>Nombre de dates</li>
            <li>Nombre de données de mortalité</li>
            <li>Liste des espèces observées</li></ul><br/>
            Vous pouvez ensuite modifier la <b>symbologie</b> de la couche comme bon
            vous semble, en fonction du critère de votre choix.<br/><br/>
            <font style='color:#0a84db'><u>IMPORTANT</u> : prenez le temps de lire
            <u>attentivement</u> les instructions pour chaque étape, et particulièrement
            les</font> <font style ='color:#952132'>informations en rouge</font>
            <font style='color:#0a84db'>!</font>"""
        self._icon = "map.png"
        self._short_help_string = ""
        self._is_map_layer = True
        self._return_geo_agg = True
        self._query = """/*set random_page_cost to 4;*/
WITH prep AS (SELECT la.id_area, ((st_area(la.geom))::DECIMAL / 1000000) area_surface
              FROM ref_geo.l_areas la
              WHERE la.id_type = ref_geo.get_id_area_type('{areas_type}')
                AND ST_intersects(la.geom, ST_union({array_polygons}))
                  ),
     data AS (SELECT
        row_number() OVER ()   AS id,
        la.id_area,
        round(area_surface, 2) AS "Surface (km2)",
        count(*) AS "Nb de données",
        ROUND(COUNT(*) / ROUND(area_surface, 2), 2) AS "Densité (Nb de données/km2)",
        COUNT(DISTINCT cd_ref) FILTER (WHERE id_rang='ES') AS "Nb d'espèces",
        COUNT(DISTINCT observateur)  AS "Nb d'observateurs",
        COUNT(DISTINCT DATE) AS "Nb de dates",
        COUNT(DISTINCT obs.id_synthese) FILTER (WHERE mortalite) AS "Nb de données de mortalité",
        string_agg(DISTINCT obs.nom_vern,', ') FILTER (WHERE id_rang='ES') AS "Liste des espèces observées"
FROM prep la
    LEFT JOIN gn_synthese.cor_area_synthese cor
ON la.id_area=cor.id_area
    LEFT JOIN src_lpodatas.v_c_observations_light obs ON cor.id_synthese=obs.id_synthese
WHERE {where_filters}
GROUP BY la.id_area, la.area_surface)
SELECT data.id
     , la.area_name
     , la.area_code
     , "Surface (km2)"
     , "Nb de données"
     , "Densité (Nb de données/km2)"
     , "Nb d'espèces"
     , "Nb d'observateurs"
     , "Nb de dates"
     , "Nb de données de mortalité"
     , "Liste des espèces observées"
     , la.geom
FROM data
         JOIN ref_geo.l_areas la ON data.id_area = la.id_area
ORDER BY area_code"""

    # def createInstance(self):  # noqa N802
    #     return SummaryMap()
