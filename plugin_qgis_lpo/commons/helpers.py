"""
/***************************************************************************
        ScriptsLPO : common_functions.py
        -------------------
        Copyright            : (C) Collectif (LPO AuRA)
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

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from qgis import processing
from qgis.core import (
    QgsField,
    QgsFields,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant


def simplify_name(string: str) -> str:
    """
    Simplify a layer name written by the user.
    """
    translation_table = str.maketrans(
        "àâäéèêëîïôöùûüŷÿç~- ",
        "aaaeeeeiioouuuyyc___",
        "&'([{|}])`^\\/@+-=*°$£%§#.?!;:<>",
    )
    return string.lower().translate(translation_table)


def check_layer_is_valid(feedback: QgsProcessingFeedback, layer: QgsVectorLayer):
    """
    Check if the input vector layer is valid.
    """
    if not layer.isValid():
        raise QgsProcessingException(
            """La couche PostGIS chargée n'est pas valide !
            Checkez les logs de PostGIS pour visualiser les messages d'erreur.
            Pour cela, rendez-vous dans l'onglet "Vue > Panneaux > Journal des messages"
            de QGis, puis l'onglet "PostGIS"."""
        )
    else:
        # iface.messageBar().pushMessage("Info", "La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !", level=Qgis.Info, duration=10)
        feedback.pushInfo(
            "La couche PostGIS demandée est valide, "
            "la requête SQL a été exécutée avec succès !"
        )
    return None


def sql_query_area_builder(feedback: QgsProcessingFeedback, layer: QgsVectorLayer,layer_crs: str = "2154" ):
    """
    Construct the sql array containing the input vector layer's features geometry.
    """
    # Initialization of the sql array containing the study area's features geometry
    array_polygons = []
    # Retrieve the CRS of the layer
    crs = layer.sourceCrs().authid()
    if crs.split(":")[0] != "EPSG":
        raise QgsProcessingException(
            """Le SCR (système de coordonnées de référence) de votre couche zone \
d'étude n'est pas de type 'EPSG'.
Veuillez choisir un SCR adéquat.
NB : 'EPSG:2154' pour Lambert 93 !"""
        )
    else:
        crs = crs.split(":")[1]
    # For each entity in the study area...
    for feature in layer.getFeatures():
        # Retrieve the geometry
        area = feature.geometry()  # QgsGeometry object
        feedback.pushDebugInfo(f'area {area}')
        # Retrieve the geometry type (single or multiple)
        geom_single_type = QgsWkbTypes.isSingleType(area.wkbType())
        feedback.pushDebugInfo(f'geom_single_type {geom_single_type}')
        # Increment the sql array
        if geom_single_type:
            array_polygons.append(
                f"ST_transform(ST_PolygonFromText('{area.asWkt()}', {crs}), {layer_crs})"
            )
        else:
            array_polygons.append(
                f"ST_transform(ST_MPolyFromText('{area.asWkt()}', {crs}), {layer_crs})"
            )
    # Remove the last "," in the sql array which is useless, and end the array
    if len(array_polygons) > 1 :
        geom_list = ",".join(array_polygons)
        return f'(select st_union(st_collect(ARRAY[{geom_list}])) as geom)'
        
    return f'(select st_union({array_polygons[0]}) as geom)'


def sql_queries_list_builder(
    table_name: str, main_query: str, pk_field: str = "id"
) -> List[str]:
    """Table create"""
    queries = [
        f"DROP TABLE if exists {table_name}",
        f"CREATE TABLE {table_name} AS ({main_query})",
        f'ALTER TABLE {table_name} add primary key ("{pk_field}")',
    ]
    return queries


def sql_taxons_filter_builder(taxons_dict: Dict) -> Optional[str]:
    """
    Construct the sql "where" clause with taxons filters.
    """
    rank_filters = []
    for key, value in taxons_dict.items():
        if value:
            value_list = ",".join([f"'{v}'" for v in value])
            rank_filters.append(f"{key} in ({value_list})")
    if len(rank_filters) > 0:
        taxons_where = f"({' or '.join(rank_filters)})"
        return taxons_where
    return None


def sql_source_filter_builder(sources: List[str]) -> Optional[str]:
    """
    Construct the sql "where" clause with source filters.
    """
    if sources:
        return f"desc_source ILIKE ANY (array{[f'{source}%' for source in sources]})"
    return None


def sql_geom_type_filter_builder(geom_types: List[str]) -> Optional[str]:
    """
    Construct the sql "where" clause with source filters.
    """

    types_dict = {
        "Point": ["ST_Point", "ST_MultiPoint"],
        "LineString": ["ST_LineString", "ST_MultiLineString"],
        "Polygon": ["ST_Polygon", "ST_MultiPolygon"],
    }
    if geom_types:
        geom_types_list = []
        for geom_type in geom_types:
            geom_types_list += types_dict[geom_type]
        return f"type_geom = ANY (array{geom_types_list})"
    return None


def sql_datetime_filter_builder(
    self: QgsProcessingAlgorithm,
    period_type_filter: str,
    timestamp: datetime,
    parameters: Dict[str, Any],
    context: QgsProcessingContext,
) -> Optional[str]:
    """
    Construct the sql "where" clause with the datetime filter.
    """
    datetime_where = None
    if period_type_filter in ("5 dernières années", "10 dernières années"):
        end_year = int(timestamp.strftime("%Y"))
        start_year = end_year - int(period_type_filter.split()[0])
        datetime_where = f"(date_an > {str(start_year)} and date_an <= {str(end_year)})"

    elif period_type_filter == "Cette année":
        year = int(timestamp.strftime("%Y"))
        datetime_where = f"(date_an = {str(year)})"
    elif period_type_filter == "Date de début - Date de fin (à définir ci-dessous)":
        # Retrieve the start and end dates
        start_date = self.parameterAsString(parameters, self.START_DATE, context)
        end_date = self.parameterAsString(parameters, self.END_DATE, context)
        if end_date < start_date:
            raise QgsProcessingException(
                "Veuillez renseigner une date de fin postérieure ou égale à la date de début !"
            )
        else:
            datetime_where = (
                f"(date_jour >= '{start_date}'::date and date_jour <= '{end_date}'::date)"
            )
    return datetime_where


def sql_timeinterval_cols_builder(  # noqa C901
    self: QgsProcessingAlgorithm,
    period_type_filter: str,
    time_interval_param: str,
    aggregation_type_param: str,
    parameters: Dict,
    context: QgsProcessingContext,
    feedback: QgsProcessingFeedback,
) -> Tuple[str, List[str]]:
    """
    Construct the sql "select" data according to a time interval and a period.
    """
    select_data = []
    x_var = []
    count_param = (
        "*" if aggregation_type_param == "Nombre de données" else "DISTINCT t.cd_ref"
    )
    if time_interval_param == "Par année":
        timestamp = datetime.now()
        if period_type_filter in ("5 dernières années", "10 dernières années", "Pas de filtre temporel"):
            end_year = int(timestamp.strftime("%Y"))
            period = period_type_filter.split()[0] 
            start_year = end_year - int(period if period.isdigit() else 10)
            years = [str(year) for year in range(start_year,end_year)]

        elif period_type_filter == "Cette année":
            end_year = int(timestamp.strftime("%Y"))
            start_year = end_year
            years = [timestamp.strftime("%Y"),]

        elif period_type_filter == "Date de début - Date de fin (à définir ci-dessous)":
            # Retrieve the start and end dates
            start_date = datetime.fromisoformat(self.parameterAsString(parameters, self.START_DATE, context))
            end_date = datetime.fromisoformat(self.parameterAsString(parameters, self.END_DATE, context))
            
            if end_date < start_date:
                raise QgsProcessingException(
                    "Veuillez renseigner une date de fin postérieure ou égale à la date de début !"
                )
            else:
                end_year = int(end_date.strftime("%Y"))
                start_year = int(start_date.strftime("%Y"))
                years = [str(year) for year in range(start_year,end_year)]

        for year in years:
                select_data.append(
                    f"""COUNT({count_param}) filter (WHERE date_an={year}) AS \"{year}\""""
                )
                x_var.append(str(year))

    else:
        monthes = self.parameterAsEnums(parameters, self.MONTHES, context)
        self.log(message=f'MONTHES {monthes}')
        months_numbers_variables = [
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "10",
            "11",
            "12",
        ]
        for month in monthes:
            select_data.append(
                f"""COUNT({count_param}) filter (WHERE extract(month from date)={month+1}) AS \"{self._months_names_variables[month]}\""""
                )
            x_var.append(
                self._months_names_variables[month]  # type: ignore
            )
    # Adding total count
    select_data.append(
        f"""COUNT({count_param}) AS \"TOTAL\""""
    )
    final_select_data = ", ".join(select_data)
    feedback.pushDebugInfo(final_select_data)
    return final_select_data, x_var


def load_layer(context: QgsProcessingContext, layer: QgsVectorLayer):
    """
    Load a layer in the current project.
    """
    if context.project() is not None:
        root = context.project().layerTreeRoot()
        plugin_lpo_group = root.findGroup("Résultats plugin LPO")
        if not plugin_lpo_group:
            plugin_lpo_group = root.insertGroup(0, "Résultats plugin LPO")
        context.project().addMapLayer(layer, False)
        plugin_lpo_group.insertLayer(0, layer)


def execute_sql_queries(
    context: QgsProcessingContext,
    feedback: QgsProcessingFeedback,
    connection: str,
    queries: List[str],
) -> None:
    """
    Execute several sql queries.
    """
    for query in queries:
        processing.run(
            "qgis:postgisexecutesql",
            {"DATABASE": connection, "SQL": query},
            is_child_algorithm=True,
            context=context,
            feedback=feedback,
        )
        feedback.pushInfo("Requête SQL exécutée avec succès !")
    return None


def format_layer_export(layer: QgsVectorLayer) -> QgsFields:
    """
    Create new valid fields for the sink.
    """
    old_fields = layer.fields()
    new_fields = layer.fields()
    new_fields.clear()
    invalid_formats = ["_text", "jsonb"]
    for field in old_fields:
        if field.typeName() in invalid_formats:
            new_fields.append(QgsField(field.name(), QVariant.String, "text"))
        else:
            new_fields.append(field)
    # for i,field in enumerate(new_fields):
    #     feedback.pushInfo('Elt : {}- {} {}'.format(i, field.name(), field.typeName()))
    return new_fields

