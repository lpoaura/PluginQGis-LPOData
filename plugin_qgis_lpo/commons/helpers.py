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


def sql_array_polygons_builder(layer: QgsVectorLayer):
    """
    Construct the sql array containing the input vector layer's features geometry.
    """
    # Initialization of the sql array containing the study area's features geometry
    array_polygons = "array["
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
        # Retrieve the geometry type (single or multiple)
        geom_single_type = QgsWkbTypes.isSingleType(area.wkbType())
        # Increment the sql array
        if geom_single_type:
            array_polygons += (
                f"ST_transform(ST_PolygonFromText('{area.asWkt()}', {crs}), 2154), "
            )
        else:
            array_polygons += (
                f"ST_transform(ST_MPolyFromText('{area.asWkt()}', {crs}), 2154), "
            )
    # Remove the last "," in the sql array which is useless, and end the array
    array_polygons = array_polygons[: len(array_polygons) - 2] + "]"
    return array_polygons


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
        datetime_where = f"""
            (date_an > {str(start_year)} and date_an <= {str(end_year)})
            """

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
                f"(date >= '{start_date}'::date and date <= '{end_date}'::date)"
            )
    return datetime_where


def sql_timeinterval_cols_builder(  # noqa C901
    self: QgsProcessingAlgorithm,
    time_interval_param,
    start_year_param: int,
    end_year_param: int,
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
        add_five_years = self.parameterAsEnums(
            parameters, self.ADD_FIVE_YEARS, context  # type: ignore
        )
        if len(add_five_years) > 0:
            if (end_year_param - start_year_param + 1) % 5 != 0:
                raise QgsProcessingException(
                    "Veuillez renseigner une période en année qui soit "
                    "divisible par 5 ! Exemple : 2011 - 2020."
                )
            else:
                counter = start_year_param
                step_limit = start_year_param
                while counter <= end_year_param:
                    select_data.append(
                        f"""COUNT({count_param}) filter (WHERE date_an={counter}) AS \"{counter}\" """
                    )
                    x_var.append(str(counter))
                    if counter == step_limit + 4:
                        select_data.append(
                            f"""COUNT({count_param}) filter (WHERE date_an>={counter-4} and date_an<={counter}) AS \"{counter-4} - {counter}\" """
                        )
                        step_limit += 5
                    counter += 1
        else:
            for year in range(start_year_param, end_year_param + 1):
                select_data.append(
                    f"""COUNT({count_param}) filter (WHERE date_an={year}) AS \"{year}\""""
                )
                x_var.append(str(year))
        select_data.append(
            f"""COUNT({count_param}) filter (WHERE date_an>={start_year_param} and date_an<={end_year_param}) AS \"TOTAL\""""
        )
    else:
        start_month = self.parameterAsEnum(parameters, self.START_MONTH, context)
        end_month = self.parameterAsEnum(parameters, self.END_MONTH, context)
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
        if start_year_param == end_year_param:
            if end_month < start_month:
                raise QgsProcessingException(
                    "Veuillez renseigner un mois de fin postérieur ou égal au mois de début !"
                )
            else:
                for month in range(start_month, end_month + 1):
                    select_data.append(
                        f"""COUNT({count_param}) filter (WHERE to_char(date, 'YYYY-MM')='{start_year_param}-{months_numbers_variables[month]}') AS \"{self._months_names_variables[month]} {start_year_param}\""""
                    )
                    x_var.append(
                        self._months_names_variables[month]  # type: ignore
                        + " "
                        + str(start_year_param)
                    )
        elif end_year_param == start_year_param + 1:
            for month in range(start_month, 12):
                select_data.append(
                    f"""COUNT({count_param}) filter (WHERE to_char(date, 'YYYY-MM')='{start_year_param}-{months_numbers_variables[month]}') AS \"{self._months_names_variables[month]} {start_year_param}\""""
                )
                x_var.append(
                    self._months_names_variables[month] + " " + str(start_year_param)  # type: ignore
                )
            for month in range(0, end_month + 1):
                select_data.append(
                    f"""COUNT({count_param}) filter (WHERE to_char(date, 'YYYY-MM')='{end_year_param}-{months_numbers_variables[month]}') AS \"{self._months_names_variables[month]} {end_year_param}\""""
                )
                x_var.append(
                    self._months_names_variables[month] + " " + str(end_year_param)
                )
        else:
            for month in range(start_month, 12):
                select_data.append(
                    f"""COUNT({count_param}) filter (WHERE to_char(date, 'YYYY-MM')='{start_year_param}-{months_numbers_variables[month]}') AS \"{self._months_names_variables[month]} {start_year_param}\""""
                )
                x_var.append(
                    self._months_names_variables[month] + " " + str(start_year_param)
                )
            for year in range(start_year_param + 1, end_year_param):
                for month in range(0, 12):
                    select_data.append(
                        f"""COUNT({count_param}) filter (WHERE to_char(date, 'YYYY-MM')='{year}-{months_numbers_variables[month]}') AS \"{self._months_names_variables[month]} {year}\""""
                    )
                    x_var.append(self._months_names_variables[month] + " " + str(year))
            for month in range(0, end_month + 1):
                select_data.append(
                    f"""COUNT({count_param}) filter (WHERE to_char(date, 'YYYY-MM')='{end_year_param}-{months_numbers_variables[month]}') AS \"{self._months_names_variables[month]} {end_year_param}\""""
                )
                x_var.append(
                    self._months_names_variables[month] + " " + str(end_year_param)
                )
        select_data.append(
            f"""COUNT({count_param}) filter (WHERE to_char(date, 'YYYY-MM')>='{start_year_param}-{months_numbers_variables[start_month]}' and to_char(date, 'YYYY-MM')<='{end_year_param}-{months_numbers_variables[end_month]}') AS \"TOTAL\""""
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

