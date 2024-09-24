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

from plugin_qgis_lpo.processing.processing_algorithm import BaseProcessingAlgorithm


class SummaryTablePerTimeInterval(BaseProcessingAlgorithm):
    """
    This algorithm takes a connection to a data base and a vector polygons layer and
    returns a summary non geometric PostGIS layer.
    """

    # layer_map = None

    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "SummaryTablePerTimeInterval"
        self._display_name = "Tableau de synthèse par intervalle de temps"
        self._output_name = "Tableau de synthèse par intervalle de temps"
        self._group_id = "summary_tables"
        self._group = "Tableaux de synthèse"
        self._short_description = """<font style="font-size:18px"><b>Besoin d'aide ?</b>
            <br/><br/>
            Vous pouvez vous référer aux options de         
          <a href="https://lpoaura.github.io/PluginQGis-LPOData/usage/advanced_filter.html" target="_blank">
            filtrage avancé</a>.</font><br/><br/>
            Cet algorithme vous permet, à partir des données d'observation enregistrées dans la base de données LPO,  d'obtenir un <b>tableau bilan</b>...
            <ul><li>par année <u>ou</u> par mois (au choix)</li>
            <li>et par espèce <u>ou</u> par groupe taxonomique (au choix)</li></ul>
            ... basé sur une <b>zone d'étude</b> présente dans votre projet QGIS (couche de type polygones) et selon une période de votre choix.
            <b style='color:#952132'>Les données d'absence et non valides sont exclues de ce traitement.</b><br/><br/>
            <font style='color:#0a84db'><u>IMPORTANT</u> : Prenez le temps de lire <u>attentivement</U> les instructions pour chaque étape, et particulièrement les</font> <font style ='color:#952132'>informations en rouge</font> <font style='color:#0a84db'>!</font>"""
        self._icon = "table.png"
        self._is_map_layer = False
        self._has_histogram = False
        self._has_time_interval_form = True
        self._has_taxonomic_rank_form = True
        self._taxonomic_ranks = {
            "cd_nom": "Espèces",
            "groupe_taxo": "Groupes taxonomiques",
        }
        self._agg_variables = ["Nombre de données", "Nombre d'espèces"]
        self._histogram_variables = [
            "Pas d'histogramme",
            "Total par pas de temps",
        ]
        self._query = """SELECT
            row_number() OVER () AS id,
            {taxa_fields},
            {custom_fields}
            FROM src_lpodatas.v_c_observations_light obs
            LEFT JOIN taxonomie.bib_taxref_rangs r ON obs.id_rang = r.id_rang
            WHERE
                st_intersects(obs.geom, st_union({array_polygons}))
                and {where_filters}
            GROUP BY {group_by_species}groupe_taxo
            ORDER BY groupe_taxo"""
