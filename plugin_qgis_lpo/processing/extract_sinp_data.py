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


class ExtractSinpData(BaseProcessingAlgorithm):
    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "ExtractSinpData"
        self._display_name = "Extraction de données d'observation au format SINP"
        self._output_name = self._display_name
        self._group_id = "raw_data"
        self._group = "Données brutes"
        self._short_description = """<font style="font-size:18px"><b>Besoin d'aide ?</b>
            <br/><br/>
            Vous pouvez vous référer aux options de 
            <a href="https://lpoaura.github.io/PluginQGis-LPOData/usage/advanced_filter.html" target="_blank">
            filtrage avancé</a>.</font><br/><br/>
            Cet algorithme vous permet d'<b>extraire des données d'observation</b> contenues dans la
            base de données LPO (couche type points) à partir d'une <b>zone d'étude</b>
            présente dans votre projet QGIS (couche de type polygones).<br /><br />
            <font style='color:#0a84db'><u>IMPORTANT</u> : Prenez le temps de lire
            <u>attentivement</U> les instructions pour chaque étape, et particulièrement les</font>
            <font style='color:#952132'>informations en rouge</font>
            <font style='color:#0a84db'>!</font>
            <br /><br />
            <font style='color:#952132'>Cette extraction <b>inlut les données non valides et d'absence<b>.</font>"""
        self._icon = "extract_data.png"
        self._short_help_string = ""
        self._is_map_layer = True
        self._layer_crs = '4326'
        self._has_source_data_filter = True
        self._has_type_geom_filter = True
        self._primary_key = "id_synthese"
        self._query = """SELECT obs.*
        FROM gn_exports.v_synthese_sinp obs
         JOIN (SELECT id_synthese, date_an, date_jour, desc_source, is_present, is_valid, type_geom, groupe_taxo
               FROM src_lpodatas.v_c_observations) AS t
                ON t.id_synthese = obs.id_synthese
        WHERE st_intersects(obs.geom, {query_area}) AND {where_filters}"""
        self._is_data_extraction = True

    # def createInstance(self):  # noqa N802
    #     return SummaryMap()
