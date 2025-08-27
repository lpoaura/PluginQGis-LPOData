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


class ExtractDataObservers(BaseProcessingAlgorithm):
    # Constants used to refer to parameters and outputs
    def __init__(self) -> None:
        super().__init__()

        self._name = "ExtractDataObservers"
        self._display_name = (
            "Extraction de données d'observation (avec id observateurs - long)"
        )
        self._output_name = self._display_name
        self._group_id = "raw_data"
        self._group = "Données brutes"
        self._short_description = """
        <p style='background-color:#952132;color:white;font-style:bold;'>
            <span style="color:yellow">⚠️</span> 
            Cette extraction inlut les données <strong>non valides</strong> et 
            <strong>d'absence</strong>.
        </p>
        
        <p style="font-size:18px">
            <strong>Besoin d'aide ?</strong>
            
            <br/>
            
            Vous pouvez vous référer au <strong>Wiki</strong> accessible sur ce lien : 
            <a href="https://lpoaura.github.io/PluginQGis-LPOData/index.html" target="_blank">
            https://lpoaura.github.io/PluginQGis-LPOData/index.html</a>.
        </p>
            
        <p>
            Cet algorithme vous permet d'<strong>extraire des données d'observation</strong> 
            contenues dans la base de données LPO (couche PostGIS de type points) à partir d'une 
            <strong>zone d'étude</strong> présente dans votre projet QGis (couche de type polygones).</p>
            <p><span style='color:#0a84db'><u>IMPORTANT</u> : Les <strong>étapes indispensables</strong> sont 
            marquées d'une <strong>étoile *</strong> avant leur numéro. Prenez le temps de lire <u>attentivement</u> 
            les instructions pour chaque étape, et particulièrement les</span> 
            <span style='color:#952132'>informations en rouge</span> <span style='color:#0a84db'>!</span>
        </p>
            """
        self._icon = "extract_data.png"
        self._short_help_string = ""
        self._is_map_layer = True
        self._has_source_data_filter = True
        self._has_type_geom_filter = True
        self._primary_key = "id_synthese"
        self._query = """SELECT
            obs.*,
            (r.champs_addi ->'from_vn')->>'id_universal' as id_observateur
        FROM src_lpodatas.v_c_observations obs
            JOIN gn_synthese.synthese s on s.id_synthese=obs.id_synthese
            LEFT JOIN taxonomie.taxref t ON obs.cd_nom = t.cd_nom
            LEFT JOIN utilisateurs.t_roles r on s.id_digitiser=r.id_role
        WHERE
            st_intersects(obs.geom, {query_area}) AND {where_filters}"""
        self._is_data_extraction = True

    # def createInstance(self):  # noqa N802
    #     return SummaryMap()
