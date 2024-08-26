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
        self._short_description = """<font style="font-size:18px"><b>Besoin d'aide ?</b> Vous pouvez vous référer au <b>Wiki</b> accessible sur ce lien : <a href="https://lpoaura.github.io/PluginQGis-LPOData/index.html" target="_blank">https://lpoaura.github.io/PluginQGis-LPOData/index.html</a>.</font><br/><br/>
            Cet algorithme vous permet d'<b>extraire des données d'observation</b> contenues dans la base de données LPO (couche PostGIS de type points) à partir d'une <b>zone d'étude</b> présente dans votre projet QGis (couche de type polygones).<br/><br/>
            <font style='color:#0a84db'><u>IMPORTANT</u> : Les <b>étapes indispensables</b> sont marquées d'une <b>étoile *</b> avant leur numéro. Prenez le temps de lire <u>attentivement</U> les instructions pour chaque étape, et particulièrement les</font> <font style ='color:#952132'>informations en rouge</font> <font style='color:#0a84db'>!</font>"""
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
            st_intersects(obs.geom, st_union({array_polygons})) AND {where_filters}"""
        self._is_data_extraction = True

    # def createInstance(self):  # noqa N802
    #     return SummaryMap()
