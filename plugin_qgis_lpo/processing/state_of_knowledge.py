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
from typing import Dict

from qgis.utils import iface

from .processing_algorithm import BaseProcessingAlgorithm


class StateOfKnowledge(BaseProcessingAlgorithm):
    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "StateOfKnowledge"
        self._display_name = "État des connaissances"
        self._output_name = "Etat des connaissances"
        self._group_id = "summary_tables"
        self._group = "Tableaux de synthèse"
        self._short_help_string = ""
        self._icon = "table.png"
        self._short_description = """<font style="font-size:18px"><b>Besoin d'aide ?</b> Vous pouvez vous référer au <b>Wiki</b> accessible sur ce lien : <a href="https://github.com/lpoaura/PluginQGis-LPOData/wiki" target="_blank">https://github.com/lpoaura/PluginQGis-LPOData/wiki</a>.</font><br/><br/>
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
        self._is_map_layer = False
        self._has_histogram = True
        # self._has_taxonomic_rank_form = True
        # self._has_time_interval_form = False
        self._histogram_variables = [
            "Pas d'histogramme",
            "Nb de données",
            "Nb d'espèces",
            "Nb d'observateurs",
            "Nb de dates",
            "Nb de données de mortalité",
        ]
        self._query = """WITH obs AS (
            SELECT obs.*
            FROM src_lpodatas.v_c_observations_light obs
            WHERE {where_filters} and st_intersects(obs.geom, st_union({array_polygons}))),
        communes AS (
            SELECT DISTINCT obs.id_synthese, la.area_name
            FROM obs
            JOIN gn_synthese.cor_area_synthese cor ON obs.id_synthese = cor.id_synthese
            JOIN ref_geo.l_areas la ON cor.id_area = la.id_area
            WHERE la.id_type = (SELECT ref_geo.get_id_area_type('COM'))),
        total_count AS (
            SELECT COUNT(*) AS total_count
            FROM obs)
        SELECT
            row_number() OVER () AS id,
            COALESCE({taxonomic_rank_db}, 'Pas de correspondance taxref') AS "{taxonomic_rank_label}",
            -- groupe_taxo as "Groupe taxo",
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
        GROUP BY {taxonomic_rank_db}, total_count
        ORDER BY {taxonomic_rank_db}"""

    # def createInstance(self):  # noqa N802
    #     return StateOfKnowledge()

    # def postProcessAlgorithm(self, _context, _feedback) -> Dict:  # noqa N802
    #     # Open the attribute table of the PostGIS layer
    #     iface.showAttributeTable(self._layer)
    #     iface.setActiveLayer(self._layer)

    #     return {}
