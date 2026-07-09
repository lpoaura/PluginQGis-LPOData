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

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from qgis import processing
from qgis.core import (
    QgsDistanceArea,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QVariant

d = QgsDistanceArea()
d.setEllipsoid("WGS84")

# Seuils de simplification de la zone d'étude.
#
# Le plugin conserve la géométrie inline dans la requête PostGIS pour que les
# couches QGIS restent rechargeables après fermeture/réouverture du projet. Le
# coût de cette approche est la taille du WKB injecté dans la requête. Ces seuils
# déclenchent donc une simplification légère dès qu'une géométrie devient
# assez détaillée pour alourdir le parsing SQL ou le transfert vers PostgreSQL.
SIMPLIFY_MIN_VERTICES = 5000
SIMPLIFY_MIN_WKB_BYTES = 250_000

# Garde-fou: si la simplification modifie trop la surface, on revient à la
# géométrie originale. Ce seuil est volontairement conservateur, car la zone
# d'étude sert à inclure/exclure des observations naturalistes.
SIMPLIFY_MAX_AREA_DELTA_RATIO = 0.005

# Seuils empiriques pour qualifier la forme. La compacité vaut 1 pour une forme
# proche du disque et tend vers 0 pour les formes découpées/linéaires. Le ratio
# de bbox protège aussi les corridors très allongés.
SIMPLIFY_LINEAR_COMPACTNESS = 0.03
SIMPLIFY_IRREGULAR_COMPACTNESS = 0.12
SIMPLIFY_LINEAR_BBOX_RATIO = 0.05
SIMPLIFY_IRREGULAR_BBOX_RATIO = 0.20
METERS_PER_DEGREE = 111320


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
        raise QgsProcessingException("""La couche PostGIS chargée n'est pas valide !
            Checkez les logs de PostGIS pour visualiser les messages d'erreur.
            Pour cela, rendez-vous dans l'onglet "Vue > Panneaux > Journal des messages"
            de QGis, puis l'onglet "PostGIS".""")
    else:

        # iface.messageBar().pushMessage("Info", "La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !", level=Qgis.Info, duration=10)
        feedback.pushInfo(
            "La couche PostGIS demandée est valide, "
            "la requête SQL a été exécutée avec succès !"
            f"{layer} {layer.featureCount()}"
        )
    return None


def get_deep_count(nested_list):
    total_count = 0
    for item in nested_list:
        if isinstance(item, list):
            total_count += get_deep_count(item)
        else:
            total_count += 1
    return total_count


def get_geom_vertices_count(geom: QgsGeometry) -> int:
    """Count vertices for any geometry type supported by QgsGeometry."""
    return sum(1 for _vertex in geom.vertices())


def get_geom_info(geom: QgsGeometry, feedback) -> dict:
    """Return metrics used to decide whether a geometry can be simplified.

    The simplification decision deliberately mixes size and shape indicators:
    a compact administrative polygon can tolerate more simplification than a
    narrow corridor following a river, even with a similar number of vertices.
    """
    num_vertices = get_geom_vertices_count(geom)
    feedback.pushInfo(f"Type geom: {type(geom)}")
    area, perimiter = d.measureArea(geom), d.measurePerimeter(geom)
    bbox = geom.boundingBox()
    bbox_width = bbox.width()
    bbox_height = bbox.height()
    min_bbox_side = min(bbox_width, bbox_height)
    max_bbox_side = max(bbox_width, bbox_height)
    compactness = (
        (4 * math.pi * area / (perimiter * perimiter)) if perimiter else 0
    )
    bbox_ratio = (min_bbox_side / max_bbox_side) if max_bbox_side else 0
    # feedback.pushInfo(f'Unit: {d.areaUnits(geom)}, ellipsoid {d.ellipsoid(geom)}, elipsoidCrs {d.ellipsoidCrs(geom)}')
    return {
        "area": area,
        "perimiter": perimiter,
        "count_nodes": num_vertices,
        "node_mean_dist": perimiter / num_vertices if num_vertices else 0,
        "compactness": compactness,
        "bbox_ratio": bbox_ratio,
        "min_bbox_side": min_bbox_side,
    }


def simplify_tolerance_to_crs_units(tolerance_meters: float, crs: str) -> float:
    """Convert meter-based tolerances for geographic CRS used in user layers."""
    if crs == "4326":
        return tolerance_meters / METERS_PER_DEGREE
    return tolerance_meters


def push_simplification_debug(
    geom_info: dict, wkb_size: int, feedback: QgsProcessingFeedback
) -> None:
    """Log all metrics used by the simplification decision."""
    feedback.pushDebugInfo(
        "Critères de simplification zone d'étude: "
        f"sommets={geom_info['count_nodes']} "
        f"(seuil={SIMPLIFY_MIN_VERTICES}), "
        f"wkb={wkb_size} octets "
        f"(seuil={SIMPLIFY_MIN_WKB_BYTES}), "
        f"surface={round(geom_info['area'], 3)} m², "
        f"périmètre={round(geom_info['perimiter'], 3)} m, "
        f"longueur moyenne segment={round(geom_info['node_mean_dist'], 3)} m, "
        f"compacité={round(geom_info['compactness'], 6)} "
        f"(linéaire<{SIMPLIFY_LINEAR_COMPACTNESS}, "
        f"irrégulier<{SIMPLIFY_IRREGULAR_COMPACTNESS}), "
        f"ratio bbox={round(geom_info['bbox_ratio'], 6)} "
        f"(linéaire<{SIMPLIFY_LINEAR_BBOX_RATIO}, "
        f"irrégulier<{SIMPLIFY_IRREGULAR_BBOX_RATIO}), "
        f"petit côté bbox={round(geom_info['min_bbox_side'], 3)}."
    )


def choose_simplification_tolerance(
    geom_info: dict, wkb_size: int, crs: str, feedback: QgsProcessingFeedback
) -> Optional[float]:
    """Choose a conservative simplification tolerance from geometry metrics.

    The thresholds are generic and do not depend on GeoNature/ref_geo area
    types. They are designed to keep linear or narrow study areas precise while
    still reducing very detailed compact polygons.
    """
    push_simplification_debug(geom_info, wkb_size, feedback)

    if (
        geom_info["count_nodes"] < SIMPLIFY_MIN_VERTICES
        and wkb_size < SIMPLIFY_MIN_WKB_BYTES
    ):
        feedback.pushInfo(
            "Simplification non nécessaire: "
            f"{geom_info['count_nodes']} sommets et {wkb_size} octets WKB, "
            "sous les seuils de complexité."
        )
        return None

    area = geom_info["area"]
    compactness = geom_info["compactness"]
    bbox_ratio = geom_info["bbox_ratio"]
    min_bbox_side = geom_info["min_bbox_side"]

    # Shape profile first, then area bucket. Linear profiles are capped to a few
    # meters because a small displacement can change the meaning of a corridor.
    if (
        compactness < SIMPLIFY_LINEAR_COMPACTNESS
        or bbox_ratio < SIMPLIFY_LINEAR_BBOX_RATIO
    ):
        profile = "linéaire"
        tolerance_meters = 0.5 if area < 100e6 else 1 if area < 1000e6 else 2
    elif (
        compactness < SIMPLIFY_IRREGULAR_COMPACTNESS
        or bbox_ratio < SIMPLIFY_IRREGULAR_BBOX_RATIO
    ):
        profile = "irrégulier"
        tolerance_meters = 1 if area < 100e6 else 3 if area < 1000e6 else 5
    else:
        profile = "compact"
        tolerance_meters = 2 if area < 100e6 else 5 if area < 1000e6 else 10

    # Never simplify more than 1% of the smallest bbox side. This protects
    # narrow polygons whose area alone would otherwise allow a large tolerance.
    if min_bbox_side:
        tolerance_meters = min(tolerance_meters, min_bbox_side * 0.01)

    tolerance = simplify_tolerance_to_crs_units(tolerance_meters, crs)
    feedback.pushInfo(
        "Géométrie complexe détectée: "
        f"{geom_info['count_nodes']} sommets, profil {profile}, "
        f"tolérance {round(tolerance_meters, 2)} m."
    )
    return tolerance if tolerance > 0 else None


def simplified_geometry_is_acceptable(
    original_geom: QgsGeometry,
    simplified_geom: QgsGeometry,
    original_info: dict,
    feedback: QgsProcessingFeedback,
) -> bool:
    """Validate the simplified geometry before using it in the SQL query."""
    if simplified_geom.isEmpty():
        feedback.pushInfo("Simplification ignorée: géométrie simplifiée vide.")
        return False

    if not simplified_geom.isGeosValid():
        feedback.pushInfo("Simplification ignorée: géométrie simplifiée invalide.")
        return False

    simplified_area = d.measureArea(simplified_geom)
    original_area = original_info["area"]
    if original_area:
        area_delta_ratio = abs(simplified_area - original_area) / original_area
        if area_delta_ratio > SIMPLIFY_MAX_AREA_DELTA_RATIO:
            feedback.pushInfo(
                "Simplification ignorée: variation de surface "
                f"{round(area_delta_ratio * 100, 3)}% supérieure au seuil "
                f"{SIMPLIFY_MAX_AREA_DELTA_RATIO * 100}%."
            )
            return False

    original_vertices = original_info["count_nodes"]
    simplified_vertices = get_geom_vertices_count(simplified_geom)
    feedback.pushInfo(
        "Simplification appliquée: "
        f"{original_vertices} -> {simplified_vertices} sommets."
    )
    return True


def prepare_study_area_geometry(
    geom: QgsGeometry, crs: str, feedback: QgsProcessingFeedback
) -> QgsGeometry:
    """Validate and simplify a study-area geometry when it is safe to do so.

    The original geometry is returned whenever validation or simplification
    fails one of the quality checks. The caller can therefore use the returned
    geometry directly without handling partial simplification failures.
    """
    if geom.isEmpty():
        return geom

    if not geom.isGeosValid():
        feedback.pushInfo("Géométrie zone d'étude invalide: correction makeValid().")
        geom = geom.makeValid()

    geom_info = get_geom_info(geom, feedback)
    wkb_size = len(bytes(geom.asWkb()))
    tolerance = choose_simplification_tolerance(geom_info, wkb_size, crs, feedback)
    if tolerance is None:
        return geom

    simplified_geom = geom.simplify(tolerance)
    if simplified_geometry_is_acceptable(geom, simplified_geom, geom_info, feedback):
        return simplified_geom
    return geom


def simplify_area(area, crs, feedback):
    geom_info = get_geom_info(area, feedback)
    feedback.pushInfo(f"Geom specs: {geom_info}")
    # If area hover 10km² and mean distance between node on perimeter is less than 500m
    if geom_info["area"] > 10e6 and geom_info["node_mean_dist"] < 500:
        # if True:
        feedback.pushInfo(f"!!! Géométrie complexe, une dégradation sera appliquée")
        # I need to simplify geometry with a tolerance of 500 meters
        if crs == "4326":  # Lambert 93
            degrees_per_meter = 1 / 111320  # Roughly 1 degree = 111.32 km
            tolerance = 500 * degrees_per_meter
        else:  # WGS84
            # Convt     500 meters to (approximate conversion)
            tolerance = 50  # in meters
        return area.simplify(tolerance)
    return area


def sql_geom_from_wkb(geom: QgsGeometry, crs: str, layer_crs: str) -> str:
    """
    Construct a PostGIS geometry expression from WKB instead of WKT.

    WKB is still inlined in the query so saved QGIS project layers remain
    reloadable without any temporary database table.
    """
    wkb_hex = bytes(geom.asWkb()).hex()
    return (
        "ST_Transform("
        f"ST_GeomFromWKB(decode('{wkb_hex}', 'hex'), {crs}), "
        f"{layer_crs}"
        ")"
    )


def sql_query_area_builder(
    feedback: QgsProcessingFeedback, layer: QgsVectorLayer, layer_crs: str = "2154"
):
    """
    Construct the sql array containing the input vector layer's features geometry.

    The study area is unioned and optionally simplified before WKB generation.
    Producing a single geometry keeps the final SQL shorter than one WKB literal
    per feature followed by a PostGIS ST_Union.
    """
    # Initialization of the list containing the study area's features geometry.
    geoms = []
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
    for feature in layer.getFeatures():
        area = feature.geometry()  # QgsGeometry object
        if area.isEmpty():
            feedback.pushDebugInfo("empty geometry ignored")
            continue
        geoms.append(area)

    if not geoms:
        raise QgsProcessingException(
            "La couche zone d'étude ne contient aucune géométrie exploitable."
        )

    geom = QgsGeometry.unaryUnion(geoms) if len(geoms) > 1 else geoms[0]
    geom = prepare_study_area_geometry(geom, crs, feedback)

    if geom.isEmpty():
        raise QgsProcessingException(
            "La couche zone d'étude ne contient aucune géométrie exploitable."
        )

    return f"(select {sql_geom_from_wkb(geom, crs, layer_crs)} as geom)"


def sql_query_area_builder_new(
    feedback: QgsProcessingFeedback, layer: QgsVectorLayer, layer_crs: str = "2154"
):
    """
    Construct the sql array containing the input vector layer's features geometry.
    """
    # Initialization of the sql array containing the study area's features geometry

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

    geoms = [f.geometry() for f in layer.getFeatures() if not f.geometry().isEmpty()]
    if not geoms:
        raise QgsProcessingException(
            "La couche zone d'étude ne contient aucune géométrie exploitable."
        )
    ugeom = QgsGeometry.unaryUnion(geoms)
    ugeom = prepare_study_area_geometry(ugeom, crs, feedback)

    if ugeom.isEmpty():
        raise QgsProcessingException(
            "La couche zone d'étude ne contient aucune géométrie exploitable."
        )

    feedback.pushDebugInfo(f"new geom: {get_geom_info(ugeom)}")
    return sql_geom_from_wkb(ugeom, crs, layer_crs)


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
        datetime_where = f"(date_an >= {str(start_year)} and date_an < {str(end_year)})"

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
            datetime_where = f"(date_jour >= '{start_date}'::date and date_jour <= '{end_date}'::date)"
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
        if period_type_filter in (
            "5 dernières années",
            "10 dernières années",
            "Pas de filtre temporel",
        ):
            end_year = int(timestamp.strftime("%Y"))
            period = period_type_filter.split()[0]
            start_year = end_year - int(period if period.isdigit() else 10)
            years = [str(year) for year in range(start_year, end_year)]

        elif period_type_filter == "Cette année":
            end_year = int(timestamp.strftime("%Y"))
            start_year = end_year
            years = [
                timestamp.strftime("%Y"),
            ]

        elif period_type_filter == "Date de début - Date de fin (à définir ci-dessous)":
            # Retrieve the start and end dates
            start_date = datetime.fromisoformat(
                self.parameterAsString(parameters, self.START_DATE, context)
            )
            end_date = datetime.fromisoformat(
                self.parameterAsString(parameters, self.END_DATE, context)
            )

            if end_date < start_date:
                raise QgsProcessingException(
                    "Veuillez renseigner une date de fin postérieure ou égale à la date de début !"
                )
            else:
                end_year = int(end_date.strftime("%Y"))
                start_year = int(start_date.strftime("%Y"))
                years = [str(year) for year in range(start_year, end_year)]

        for year in years:
            select_data.append(
                f"""COUNT({count_param}) filter (WHERE date_an={year}) AS \"{year}\""""
            )
            x_var.append(str(year))

    else:
        monthes = self.parameterAsEnums(parameters, self.MONTHES, context)
        self.log(message=f"MONTHES {monthes}")
        for month in monthes:
            select_data.append(
                f"""COUNT({count_param}) filter (WHERE extract(month from date)={month+1}) AS \"{self._months_names_variables[month]}\""""
            )
            x_var.append(self._months_names_variables[month])  # type: ignore
    # Adding total count
    select_data.append(f"""COUNT({count_param}) AS \"TOTAL\"""")
    final_select_data = ", ".join(select_data)
    feedback.pushDebugInfo(final_select_data)
    return final_select_data, x_var


def load_layer(
    context: QgsProcessingContext, layer: QgsVectorLayer, output_name: str = ""
):
    """
    Load a layer in the current project.
    """
    if context.project() is not None:
        context.temporaryLayerStore().addMapLayer(layer)
        layer_details = QgsProcessingContext.LayerDetails(
            layer.name(), context.project(), output_name
        )
        layer_details.groupName = "Résultats plugin LPO"
        context.addLayerToLoadOnCompletion(layer.id(), layer_details)


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
