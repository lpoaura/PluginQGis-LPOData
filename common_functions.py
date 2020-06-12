# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : common_functions.py
        -------------------
        Date                 : 2020-04-16
        Copyright            : (C) 2020 by Elsa Guilley (LPO AuRA)
        Email                : lpo-aura@lpo.fr
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

__author__ = 'Elsa Guilley (LPO AuRA)'
__date__ = '2020-04-16'
__copyright__ = '(C) 2020 by Elsa Guilley (LPO AuRA)'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.utils import iface
from qgis.gui import QgsMessageBar

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsWkbTypes,
                       QgsField,
                       QgsProcessingException,
                       Qgis)
import processing


def simplify_name(string):
    """
    Simplify a layer name written by the user.
    """
    translation_table = str.maketrans(
        'àâäéèêëîïôöùûüŷÿç~- ',
        'aaaeeeeiioouuuyyc___',
        "&'([{|}])`^\/@+-=*°$£%§#.?!;:<>"
    )
    return string.lower().translate(translation_table)

# def check_layer_geometry(layer):
#     """
#     Check if the input vector layer is a polygon layer.
#     """
#     if QgsWkbTypes.displayString(layer.wkbType()) not in ['Polygon', 'MultiPolygon']:
#         iface.messageBar().pushMessage("Erreur", "La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE.", level=Qgis.Critical, duration=10)
#         raise QgsProcessingException("La zone d'étude fournie n'est pas valide ! Veuillez sélectionner une couche vecteur de type POLYGONE.")
#     return None

def check_layer_is_valid(feedback, layer):
    """
    Check if the input vector layer is valid.
    """
    if not layer.isValid():
        raise QgsProcessingException(""""La couche PostGIS chargée n'est pas valide !
            Checkez les logs de PostGIS pour visualiser les messages d'erreur.""")
    else:
        #iface.messageBar().pushMessage("Info", "La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !", level=Qgis.Info, duration=10)
        feedback.pushInfo("La couche PostGIS demandée est valide, la requête SQL a été exécutée avec succès !")
    return None

def construct_sql_array_polygons(layer):
    """
    Construct the sql array containing the input vector layer's features geometry.
    """
    # Initialization of the sql array containing the study area's features geometry
    array_polygons = "array["
    # Retrieve the CRS of the layer
    crs = layer.sourceCrs().authid().split(':')[1]
    # For each entity in the study area...
    for feature in layer.getFeatures():
        # Retrieve the geometry
        area = feature.geometry() # QgsGeometry object
        # Retrieve the geometry type (single or multiple)
        geomSingleType = QgsWkbTypes.isSingleType(area.wkbType())
        # Increment the sql array
        if geomSingleType:
            array_polygons += "ST_transform(ST_PolygonFromText('{}', {}), 2154), ".format(area.asWkt(), crs)
        else:
            array_polygons += "ST_transform(ST_MPolyFromText('{}', {}), 2154), ".format(area.asWkt(), crs)
    # Remove the last "," in the sql array which is useless, and end the array
    array_polygons = array_polygons[:len(array_polygons)-2] + "]"
    return array_polygons

def construct_sql_taxons_filter(taxons_dict):
    """
    Construct the sql "where" clause with taxons filters.
    """
    taxons_where = " and ("
    for key, value in taxons_dict.items():
        if len(value) > 0:
            if len(value) == 1:
                taxons_where += "{} = '{}' or ".format(key, value[0])
            else:
                taxons_where += "{} in {} or ".format(key, str(tuple(value)))
    if taxons_where != " and (":
        taxons_where = taxons_where[:len(taxons_where)-4] + ")"
        return taxons_where
    else:
        return ""

def construct_sql_datetime_filter(self, period_filter, timestamp, parameters, context):
    """
    Construct the sql "where" clause with the datetime filter.
    """
    datetime_where = ""
    if period_filter == "5 dernières années":
        end_year = int(timestamp.strftime('%Y'))
        start_year = end_year - 5
        datetime_where += " and (date_an > {} and date_an <= {})".format(start_year, end_year)
    elif period_filter == "10 dernières années":
        end_year = int(timestamp.strftime('%Y'))
        start_year = end_year - 10
        datetime_where += " and (date_an > {} and date_an <= {})".format(start_year, end_year)
    elif period_filter == "Date de début - Date de fin (à définir ci-dessous)":
        # Retrieve the start and end dates
        start_date = self.parameterAsString(parameters, self.START_DATE, context)
        end_date = self.parameterAsString(parameters, self.END_DATE, context)
        if end_date < start_date:
            raise QgsProcessingException("Veuillez renseigner une date de fin postérieure ou égale à la date de début !")
        else:
            datetime_where += " and (date >= '{}'::date and date <= '{}'::date)".format(start_date, end_date)
    return datetime_where

def construct_sql_select_data_per_time_interval(self, time_interval_param, start_year_param, end_year_param, aggregation_type_param, parameters, context):
    """
    Construct the sql "select" data according to a time interval and a period.
    """
    select_data = ""
    if time_interval_param == 'Par année':
        add_five_years = self.parameterAsBool(parameters, self.ADD_FIVE_YEARS, context)
        if add_five_years:
            if (end_year_param-start_year_param+1)%5 != 0:
                raise QgsProcessingException("Veuillez renseigner une période en année qui soit divisible par 5 ! Ex : 2011 - 2020.")
            else:
                counter = start_year_param
                step_limit = start_year_param
                while counter <= end_year_param:
                    select_data += ", COUNT({}) filter (WHERE date_an={}) AS \"{}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", counter, counter)
                    if counter == step_limit+4:
                        select_data += ", COUNT({}) filter (WHERE date_an>={} and date_an<={}) AS \"{} - {}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", counter-4, counter, counter-4, counter)
                        step_limit += 5
                    counter += 1
        else:
            for year in range(start_year_param, end_year_param+1):
                select_data += ", COUNT({}) filter (WHERE date_an={}) AS \"{}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", year, year)
        select_data += ", COUNT({}) filter (WHERE date_an>={} and date_an<={}) AS \"TOTAL\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", start_year_param, end_year_param)
    else:
        start_month = self.parameterAsEnum(parameters, self.START_MONTH, context)
        end_month = self.parameterAsEnum(parameters, self.END_MONTH, context)
        months_numbers_variables = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        if start_year_param == end_year_param:
            if end_month < start_month:
                raise QgsProcessingException("Veuillez renseigner un mois de fin postérieur ou égal au mois de début !")
            else:
                for month in range(start_month, end_month+1):
                    select_data += ", COUNT({}) filter (WHERE to_char(date, 'YYYY-MM')='{}-{}') AS \"{} {}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", start_year_param, months_numbers_variables[month], self.months_names_variables[month], start_year_param)
        elif end_year_param == start_year_param+1:
            for month in range(start_month, 12):
                select_data += ", COUNT({}) filter (WHERE to_char(date, 'YYYY-MM')='{}-{}') AS \"{} {}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", start_year_param, months_numbers_variables[month], self.months_names_variables[month], start_year_param)
            for month in range(0, end_month+1):
                select_data += ", COUNT({}) filter (WHERE to_char(date, 'YYYY-MM')='{}-{}') AS \"{} {}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", end_year_param, months_numbers_variables[month], self.months_names_variables[month], end_year_param)
        else:
            for month in range(start_month, 12):
                select_data += ", COUNT({}) filter (WHERE to_char(date, 'YYYY-MM')='{}-{}') AS \"{} {}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", start_year_param, months_numbers_variables[month], self.months_names_variables[month], start_year_param)
            for year in range(start_year_param+1, end_year_param):
                for month in range(0, 12):
                    select_data += ", COUNT({}) filter (WHERE to_char(date, 'YYYY-MM')='{}-{}') AS \"{} {}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", year, months_numbers_variables[month], self.months_names_variables[month], year)
            for month in range(0, end_month+1):
                select_data += ", COUNT({}) filter (WHERE to_char(date, 'YYYY-MM')='{}-{}') AS \"{} {}\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", end_year_param, months_numbers_variables[month], self.months_names_variables[month], end_year_param)
        select_data += ", COUNT({}) filter (WHERE to_char(date, 'YYYY-MM')>='{}-{}' and to_char(date, 'YYYY-MM')<='{}-{}') AS \"TOTAL\"".format("*" if aggregation_type_param == 'Nombre de données' else "DISTINCT cd_nom", start_year_param, months_numbers_variables[start_month], end_year_param, months_numbers_variables[end_month])
    return select_data

def load_layer(context, layer):
    """
    Load a layer in the current project.
    """
    root = context.project().layerTreeRoot()
    plugin_lpo_group = root.findGroup('Résultats plugin LPO')
    if not plugin_lpo_group:
        plugin_lpo_group = root.insertGroup(0, 'Résultats plugin LPO')
    context.project().addMapLayer(layer, False)
    plugin_lpo_group.addLayer(layer)
    ### Variant
    # context.temporaryLayerStore().addMapLayer(layer)
    # context.addLayerToLoadOnCompletion(
    #     layer.id(),
    #     QgsProcessingContext.LayerDetails("Données d'observations", context.project(), self.OUTPUT)
    # )

def execute_sql_queries(context, feedback, connection, queries):
    """
    Execute several sql queries.
    """
    for query in queries:
        processing.run(
            'qgis:postgisexecutesql',
            {
                'DATABASE': connection,
                'SQL': query
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )
        feedback.pushInfo('Requête SQL exécutée avec succès !')
    return None

def format_layer_export(layer):
    """
    Create new valid fields for the sink.
    """
    old_fields = layer.fields()
    new_fields = layer.fields()
    new_fields.clear()
    invalid_formats = ["_text", "jsonb"]
    for field in old_fields:
        if field.typeName() in invalid_formats:
            new_fields.append(QgsField(field.name(), QVariant.String, "str"))
        else:
            new_fields.append(field)
    # for i,field in enumerate(new_fields):
    #     feedback.pushInfo('Elt : {}- {} {}'.format(i, field.name(), field.typeName()))
    return new_fields
