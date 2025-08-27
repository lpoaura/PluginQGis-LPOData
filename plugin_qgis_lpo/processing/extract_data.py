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


class ExtractData(BaseProcessingAlgorithm):
    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "ExtractData"
        self._display_name = "Extraction de données d'observation"
        self._output_name = self._display_name
        self._group_id = "raw_data"
        self._group = "Données brutes"
        self._short_description = """
        <p style='background-color:#952132;color:white;font-style:bold;'>
            <span style="color:yellow">⚠️</span> 
            Cette extraction inlut les données <strong>non valides</strong> et 
            <strong>d'absence</strong>.
        </p>
        
        <p style="font-size:18px"><strong>Besoin d'aide ?</strong>
            
            <br/>
            
            Vous pouvez vous référer aux options de 
            <a href="https://lpoaura.github.io/PluginQGis-LPOData/usage/advanced_filter.html" target="_blank">
            filtrage avancé</a>.
        </p>


        <p>
            Cet algorithme vous permet d'<strong>extraire des données d'observation</strong> contenues dans la
            base de données LPO (couche type points) à partir d'une <strong>zone d'étude</strong>
            présente dans votre projet QGIS (couche de type polygones).<br /><br />
            <span style='color:#0a84db'><u>IMPORTANT</u> : Prenez le temps de lire
            <u>attentivement</U> les instructions pour chaque étape, et particulièrement les</span>
            <span style='color:#952132'>informations en rouge</span>
            <span style='color:#0a84db'>!</span>
        </p>
            """
        self._icon = "extract_data.png"
        self._short_help_string = ""
        self._is_map_layer = True
        self._has_source_data_filter = True
        self._has_type_geom_filter = True
        self._primary_key = "id_synthese"
        self._query = """SELECT obs.*
        FROM src_lpodatas.v_c_observations obs
        LEFT JOIN taxonomie.taxref t ON obs.cd_nom = t.cd_nom
        WHERE st_intersects(obs.geom, {query_area}) AND {where_filters}"""
        self._is_data_extraction = True

    # def createInstance(self):  # noqa N802
    #     return SummaryMap()
