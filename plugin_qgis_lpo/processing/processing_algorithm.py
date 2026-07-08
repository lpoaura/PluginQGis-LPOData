"""Generic Qgis Processing Algorithm classes"""

import ast
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
from qgis.core import (
    QgsAction,
    QgsDataSourceUri,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterProviderConnection,
    QgsProcessingParameterString,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface

from ..__about__ import __icon_dir_path__
from ..commons.helpers import (
    check_layer_is_valid,
    execute_sql_queries,
    format_layer_export,
    load_layer,
    simplify_name,
    sql_datetime_filter_builder,
    sql_geom_type_filter_builder,
    sql_queries_list_builder,
    sql_query_area_builder,
    sql_source_filter_builder,
    sql_timeinterval_cols_builder,
)
from ..commons.widgets import DateTimeWidget
from ..toolbelt.log_handler import PlgLogger
from .qgis_processing_postgis import uri_from_name

plugin_path = os.path.dirname(__file__)


class BaseProcessingAlgorithm(QgsProcessingAlgorithm):
    """Custom Qgis processing algorithm

    Args:
        QgsProcessingAlgorithm (_type_): QgsProcessingAlgorithm
    """

    DATABASE = "DATABASE"
    STUDY_AREA = "STUDY_AREA"
    TAXONOMIC_RANK = "TAXONOMIC_RANK"
    AREAS_TYPE = "AREAS_TYPE"
    GROUPE_TAXO_FILTER = "GROUPE_TAXO_FILTER"
    TAXREF_FILTER = "TAXREF_FILTER"
    TAXREF_REGNE_FILTER = "TAXREF_REGNE_FILTER"
    TAXREF_PHYLUM_FILTER = "TAXREF_PHYLUM_FILTER"
    TAXREF_CLASSE_FILTER = "TAXREF_CLASSE_FILTER"
    TAXREF_ORDRE_FILTER = "TAXREF_ORDRE_FILTER"
    TAXREF_FAMILLE_FILTER = "TAXREF_FAMILLE_FILTER"
    TAXREF_GROUP1_INPN_FILTER = "TAXREF_GROUP1_INPN_FILTER"
    TAXREF_GROUP2_INPN_FILTER = "TAXREF_GROUP2_INPN_FILTER"
    PERIOD = "PERIOD"
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
    TIME_INTERVAL = "TIME_INTERVAL"
    ADD_FIVE_YEARS = "ADD_FIVE_YEARS"
    TEST = "TEST"
    MONTHES = "MONTHES"
    EXTRA_WHERE = "EXTRA_WHERE"
    EXTRA_FILTER_FIELD_1 = "EXTRA_FILTER_FIELD_1"
    EXTRA_FILTER_OPERATOR_1 = "EXTRA_FILTER_OPERATOR_1"
    EXTRA_FILTER_VALUE_1 = "EXTRA_FILTER_VALUE_1"
    EXTRA_FILTER_FIELD_2 = "EXTRA_FILTER_FIELD_2"
    EXTRA_FILTER_OPERATOR_2 = "EXTRA_FILTER_OPERATOR_2"
    EXTRA_FILTER_VALUE_2 = "EXTRA_FILTER_VALUE_2"
    EXTRA_FILTER_FIELD_3 = "EXTRA_FILTER_FIELD_3"
    EXTRA_FILTER_OPERATOR_3 = "EXTRA_FILTER_OPERATOR_3"
    EXTRA_FILTER_VALUE_3 = "EXTRA_FILTER_VALUE_3"
    OUTPUT = "OUTPUT"
    OUTPUT_NAME = "OUTPUT_NAME"
    OUTPUT_HISTOGRAM = "OUTPUT_HISTOGRAM"
    ADD_HISTOGRAM = "ADD_HISTOGRAM"
    HISTOGRAM_OPTIONS = "HISTOGRAM_OPTIONS"
    SOURCE_DATA = "SOURCE_DATA"
    EXPORT_VIEWS = "EXPORT_VIEWS"
    TYPE_GEOM = "TYPE_GEOM"

    def __init__(self) -> None:
        """Init class and set default values"""
        super().__init__()

        self.log = PlgLogger().log
        # Global settings
        self._name = "myprocessingalgorithm"
        self._display_name = "My Processing Algorithm"
        self._group_id = "maps"
        self._group = "Cartes"
        self._short_help_string = ""
        self._short_description = ""
        self._icon: str
        self._ts = datetime.now()

        # processAlgorithm settings
        self._is_map_layer = False
        self._is_table_layer = False
        self._layer_crs = "2154"
        self._has_time_interval_form = False
        self._has_histogram = False
        self._has_taxonomic_rank_form = False
        self._has_source_data_filter = True
        self._has_export_views_list = False
        self._has_type_geom_filter = False
        self._export_output = False
        self._query = ""
        self._return_geo_agg: bool = False
        self._db_variables = QgsSettings()
        self._connection: str
        self._layer_name: str
        self._layer: QgsVectorLayer
        self._layer_features_count: int = 0
        self._areas_variables: List[str] = [
            "Mailles 0.5*0.5",
            "Mailles 1*1",
            "Mailles 5*5",
            "Mailles 10*10",
            "Communes",
        ]
        self._areas_types_codes: List[str] = ["M0.5", "M1", "M5", "M10", "COM"]
        self._period_variables: List[str] = [
            "Pas de filtre temporel",
            "5 dernières années",
            "10 dernières années",
            "Cette année",
            "Date de début - Date de fin (à définir ci-dessous)",
        ]
        self._time_interval_variables = ["Par année", "Par mois"]
        self._months_names_variables = [
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin",
            "Juillet",
            "Août",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre",
        ]
        self._histogram_variables: List[str] = []
        self._type_geom_variables: List[str] = ["Point", "LineString", "Polygon"]
        self._taxref_filter_settings = {
            self.TAXREF_REGNE_FILTER: ("regne", "Règne", "regne"),
            self.TAXREF_PHYLUM_FILTER: ("phylum", "Phylum", "phylum"),
            self.TAXREF_CLASSE_FILTER: ("classe", "Classe", "classe"),
            self.TAXREF_ORDRE_FILTER: ("ordre", "Ordre", "ordre"),
            self.TAXREF_FAMILLE_FILTER: ("famille", "Famille", "famille"),
            self.TAXREF_GROUP1_INPN_FILTER: (
                "group1_inpn",
                "Groupe 1 INPN",
                "group1_inpn",
            ),
            self.TAXREF_GROUP2_INPN_FILTER: (
                "group2_inpn",
                "Groupe 2 INPN",
                "group2_inpn",
            ),
        }
        self._extra_filter_fields = [
            {"label": "Aucun filtre", "column": None, "type": None},
            {"label": "Année", "column": "date_an", "type": "int"},
            {"label": "Date", "column": "date_jour", "type": "date"},
            {"label": "Nombre total", "column": "nombre_total", "type": "int"},
            {"label": "Mortalité", "column": "mortalite", "type": "bool"},
            {"label": "Présence", "column": "is_present", "type": "bool"},
            {"label": "Donnée valide", "column": "is_valid", "type": "bool"},
            {"label": "Observateur", "column": "observateur", "type": "text"},
            {"label": "Code nidification", "column": "statut_repro", "type": "text"},
            {"label": "Source", "column": "source", "type": "text"},
            {"label": "Jeu de données", "column": "jdd", "type": "text"},
            {"label": "Lieu", "column": "place", "type": "text"},
            {"label": "Précision", "column": "precision", "type": "int"},
        ]
        self._extra_filter_operators = [
            "=",
            "!=",
            ">",
            ">=",
            "<",
            "<=",
            "Contient",
            "Commence par",
            "Dans la liste",
            "Est nul",
            "N'est pas nul",
        ]
        self._extra_filter_params = [
            (
                self.EXTRA_FILTER_FIELD_1,
                self.EXTRA_FILTER_OPERATOR_1,
                self.EXTRA_FILTER_VALUE_1,
            ),
            (
                self.EXTRA_FILTER_FIELD_2,
                self.EXTRA_FILTER_OPERATOR_2,
                self.EXTRA_FILTER_VALUE_2,
            ),
            (
                self.EXTRA_FILTER_FIELD_3,
                self.EXTRA_FILTER_OPERATOR_3,
                self.EXTRA_FILTER_VALUE_3,
            ),
        ]
        self._taxonomic_ranks = {
            "groupe_taxo": "Groupe taxo",
            "regne": "Règne",
            "phylum": "Phylum",
            "classe": "Classe",
            "ordre": "Ordre",
            "famille": "Famille",
            "obs.group1_inpn": "Groupe 1 INPN",
            "obs.group2_inpn": "Groupe 2 INPN",
        }
        self._taxonomic_ranks_labels: List[str]
        self._taxonomic_ranks_db: List[str]
        self._taxonomic_rank_label: str = "Groupe taxo"
        self._taxonomic_rank_db: str = "groupe_taxo"
        self._histogram_option: str = "Pas d'histogramme"
        self._groupe_taxo: List[str] = []
        self._taxref_filter: Optional[str] = None
        self._output_name = "output"
        self._study_area = None
        self._format_name: str = "output"
        self._areas_type: str
        self._ts = datetime.now()
        self._query_area = None
        self._taxons_filters: Dict[str, List[str]] = {}
        self._taxref_name_filter: Optional[str] = None
        self._taxref_rank_filters: Dict[str, List[str]] = {}
        self._is_data_extraction: bool = False
        self._filters: List[str] = []
        self._period_type: str
        self._export_view: str
        self._extra_where: Optional[str] = None
        self._source_data_where: Optional[str] = None
        self._type_geom_where: Optional[str] = None
        self._geographic_where_clause: Optional[str] = None
        self._uri: QgsDataSourceUri
        self._primary_key = "id"
        self._output_histogram: str
        self._group_by_species: str = ""
        self._taxonomic_rank: str = "Espèces"
        self._taxa_fields: Optional[str] = None
        self._custom_fields: Optional[str] = None
        self._x_var: Optional[List[str]] = None
        self._status_columns_db: List[str] = ["lr_r"]
        self._status_columns_with_alias: List[str] = ['lr_r as "LR Régionale"']
        self._time_interval: str

    def tr(self, string: str) -> str:
        """QgsProcessingAlgorithm translatable string with the self.tr() function."""
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):  # noqa N802
        return type(self)()

    def flags(self):  # noqa N802
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self._name

    def displayName(self) -> str:  # noqa N802
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self._display_name)

    def groupId(self) -> Optional[str]:  # noqa N802
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self._group_id

    def group(self) -> Optional[str]:
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self._group) if self._group else self._group

    def icon(self) -> QIcon:
        """Icon script"""
        return QIcon(str(__icon_dir_path__ / self._icon))

    def shortHelpString(self) -> str:  # noqa N802
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(self._short_help_string)

    def shortDescription(self) -> str:  # noqa N802
        return self.tr(self._short_description)

    def initAlgorithm(self, _config: None) -> None:  # noqa N802
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        required_text = '<span style="color:#952132">(requis)</span>'
        optional_text = "(facultatif)"
        # self._ts = datetime.now()
        # self._db_variables = QgsSettings()
        database = QgsProcessingParameterProviderConnection(
            self.DATABASE,
            self.tr(
                f"""<strong style="color:#0a84db">BASE DE DONNÉES</strong> {required_text} :
                    sélectionnez votre <u>connexion</u> à la base de données LPO"""
            ),
            "postgres",
            defaultValue="geonature_lpo",
            optional=False,
        )
        self.addParameter(database)
        
        study_area = QgsProcessingParameterFeatureSource(
            self.STUDY_AREA,
            self.tr(
                f"""<strong style="color:#0a84db">ZONE D'ÉTUDE</strong> {required_text} :
                    sélectionnez votre <u>zone d'étude</u>,
                    à partir de laquelle seront extraits les résultats"""
            ),
            [QgsProcessing.TypeVectorPolygon],
        )
        self.addParameter(study_area)

        if self._has_taxonomic_rank_form and self._taxonomic_ranks:
            self._taxonomic_ranks_labels = [
                value for _key, value in self._taxonomic_ranks.items()
            ]
            self._taxonomic_ranks_db = [
                key for key, _value in self._taxonomic_ranks.items()
            ]
            taxonomic_rank = QgsProcessingParameterEnum(
                self.TAXONOMIC_RANK,
                self.tr(
                    f"""<strong style="color:#0a84db">RANG TAXONOMIQUE</strong> {required_text}"""
                ),
                self._taxonomic_ranks_labels,
                allowMultiple=False,
            )
            taxonomic_rank.setMetadata(
                {
                    "widget_wrapper": {
                        "useCheckBoxes": True,
                        "columns": (
                            (len(self._taxonomic_ranks_labels) / 2)
                            if len(self._taxonomic_ranks_labels) > 3
                            else len(self._taxonomic_ranks_labels)
                        ),
                    }
                }
            )
            self.addParameter(taxonomic_rank)

        export_views = [
            json.loads(item) for item in self._db_variables.value("export_views")
        ]

        if self._has_export_views_list:
            export_views_list = QgsProcessingParameterEnum(
                self.EXPORT_VIEWS,
                self.tr(
                    f"""<strong style="color:#0a84db">FORMAT D'EXPORT</strong> {required_text} :
                        sélectionnez une <u>vue</u> pour exporter les données"""
                ),
                [f"{item['label']} ({item['relation']})" for item in export_views],
                allowMultiple=False,
                defaultValue=0,
                optional=False,
            )
            self.addParameter(export_views_list)

        period_type = QgsProcessingParameterEnum(
            self.PERIOD,
            self.tr(f"""<strong style="color:#0a84db">PÉRIODE</strong> {required_text} :
                    sélectionnez une <u>période</u> pour filtrer vos données
                    d'observations"""),
            self._period_variables,
            allowMultiple=False,
            optional=True,
        )
        period_type.setMetadata(
            {
                "widget_wrapper": {
                    "useCheckBoxes": True,
                    "columns": len(self._period_variables) / 2,
                }
            }
        )
        
        self.addParameter(period_type)

        start_date = QgsProcessingParameterString(
            self.START_DATE,
            f"Date de début {optional_text}",
            defaultValue="",
            optional=True,
        )
        start_date.setMetadata({"widget_wrapper": {"class": DateTimeWidget}})
        self.addParameter(start_date)

        end_date = QgsProcessingParameterString(
            self.END_DATE,
            f"Date de fin {optional_text}",
            defaultValue="",
            optional=True,
        )
        end_date.setMetadata({"widget_wrapper": {"class": DateTimeWidget}})
        self.addParameter(end_date)

        if self._has_time_interval_form:
            # ## Time interval and period ###
            time_interval = QgsProcessingParameterEnum(
                self.TIME_INTERVAL,
                self.tr(
                    f"""<strong style="color:#0a84db">AGRÉGATION TEMPORELLE</strong> {required_text}"""
                ),
                self._time_interval_variables,
                allowMultiple=False,
            )
            time_interval.setMetadata(
                {
                    "widget_wrapper": {
                        "useCheckBoxes": True,
                        "columns": len(self._time_interval_variables),
                    }
                }
            )
            self.addParameter(time_interval)

            monthes = QgsProcessingParameterEnum(
                self.MONTHES,
                self.tr("Sélection des mois"),
                self._months_names_variables,
                allowMultiple=True,
                optional=True,
                defaultValue=[v for v in range(12)],
            )
            self.addParameter(monthes)

        if self._return_geo_agg:
            areas_types = QgsProcessingParameterEnum(
                self.AREAS_TYPE,
                self.tr(
                    f"""<strong style="color:#0a84db">TYPE D'ENTITÉS GÉOGRAPHIQUES</strong> {required_text} :
                    Sélectionnez le <u>type d'entités géographiques</u>
                    qui vous intéresse"""
                ),
                self._areas_variables,
                allowMultiple=False,
            )
            areas_types.setMetadata(
                {"widget_wrapper": {"useCheckBoxes": True, "columns": 5}}
            )
            self.addParameter(areas_types)

        # ## Taxons filters ##
        groupe_taxo_filter = QgsProcessingParameterEnum(
            self.GROUPE_TAXO_FILTER,
            self.tr(
                f"""<strong style="color:#0a84db">GROUPE TAXONOMIQUE</strong> {optional_text} :
                    filtrer les données par groupes taxonomiques"""
            ),
            self._db_variables.value("groupe_taxo"),
            allowMultiple=True,
            optional=True,
        )
        self.addParameter(groupe_taxo_filter)

        for param_name, (setting_key, label, _column) in self._taxref_filter_settings.items():
            values = self._settings_list(setting_key)
            if not values:
                continue
            taxref_rank_filter = QgsProcessingParameterEnum(
                param_name,
                self.tr(f"<strong>{label}</strong> {optional_text}"),
                values,
                allowMultiple=True,
                optional=True,
            )
            taxref_rank_filter.setFlags(
                taxref_rank_filter.flags()
                | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(taxref_rank_filter)

        taxref_name_filter = QgsProcessingParameterString(
            self.TAXREF_FILTER,
            self.tr(
                """<strong>RECHERCHE TAXREF PAR NOM</strong>&nbsp;:
                rechercher dans <code>lb_nom</code> ou <code>nom_vern</code>.
                Plusieurs termes peuvent être séparés par des virgules."""
            ),
            optional=True,
            multiLine=False,
        )
        taxref_name_filter.setFlags(
            taxref_name_filter.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(taxref_name_filter)

        if self._has_histogram:
            histogram_options = QgsProcessingParameterEnum(
                self.HISTOGRAM_OPTIONS,
                self.tr(
                    f"""<strong style="color:#0a84db">HISTOGRAMME</strong> {optional_text} :
                    générer un histogramme à partir des résultats."""
                ),
                self._histogram_variables,
                defaultValue="Pas d'histogramme",
            )
            histogram_options.setFlags(
                histogram_options.flags()
                | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(histogram_options)

            output_histogram = QgsProcessingParameterFileDestination(
                self.OUTPUT_HISTOGRAM,
                self.tr("""Emplacement de l'enregistrement du ficher
                    (format image PNG) de l'histogramme"""),
                self.tr("image PNG (*.png)"),
            )
            output_histogram.setFlags(
                output_histogram.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(output_histogram)

        output_name = QgsProcessingParameterString(
            self.OUTPUT_NAME,
            self.tr(
                f"""<strong style="color:#0a84db">PARAMÉTRAGE DES RESULTATS EN SORTIE</strong>
                    {optional_text} : personnalisez le nom de votre couche
                    en base de données"""
            ),
            self.tr(self._output_name),
        )
        self.addParameter(output_name)

        if self._has_source_data_filter:
            source_data_where = QgsProcessingParameterEnum(
                self.SOURCE_DATA,
                self.tr("<strong>SOURCES DE DONNEES</strong>"),
                self._db_variables.value("source_data"),
                defaultValue=[0, 1, 2],
                allowMultiple=True,
                optional=False,
            )
            source_data_where.setFlags(
                source_data_where.flags()
                | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(source_data_where)

        # ## Gestion des différents types de géométries ###
        if self._has_type_geom_filter:
            geomtype_data_where = QgsProcessingParameterEnum(
                self.TYPE_GEOM,
                self.tr("<strong>TYPE DE GEOMETRIES</strong>"),
                self._type_geom_variables,
                defaultValue=[1],
                allowMultiple=False,
                optional=False,
            )
            geomtype_data_where.setFlags(
                geomtype_data_where.flags()
                | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(geomtype_data_where)

        for index, (field_param, operator_param, value_param) in enumerate(
            self._extra_filter_params, start=1
        ):
            extra_field = QgsProcessingParameterEnum(
                field_param,
                self.tr(f"<strong>FILTRE AVANCÉ {index}</strong> - Champ"),
                [field["label"] for field in self._extra_filter_fields],
                defaultValue=0,
                allowMultiple=False,
                optional=True,
            )
            extra_field.setFlags(
                extra_field.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(extra_field)

            extra_operator = QgsProcessingParameterEnum(
                operator_param,
                self.tr(f"Filtre avancé {index} - Opérateur"),
                self._extra_filter_operators,
                defaultValue=0,
                allowMultiple=False,
                optional=True,
            )
            extra_operator.setFlags(
                extra_operator.flags()
                | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(extra_operator)

            extra_value = QgsProcessingParameterString(
                value_param,
                self.tr(f"Filtre avancé {index} - Valeur"),
                optional=True,
                multiLine=False,
            )
            extra_value.setFlags(
                extra_value.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(extra_value)
        self.log(
            message=f"initAlgorithm {self._name} SD{self.START_DATE} ED{self.END_DATE} end"
        )

    def processAlgorithm(  # noqa N802
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Optional[dict]:
        """
        Here is where the processing itself takes place.
        """
        self.log(message=f"processAlgorithm <{self._name}> start")
        # PARAMETERS
        # Retrieve the input vector layer = study area
        if feedback is None:
            feedback = QgsProcessingFeedback()

        # Form values
        self._connection = self.parameterAsString(parameters, self.DATABASE, context)
        self._study_area = self.parameterAsSource(parameters, self.STUDY_AREA, context)
        self.log(
            message=str(
                [
                    self._db_variables.value("source_data")[i]
                    for i in (
                        self.parameterAsEnums(parameters, self.SOURCE_DATA, context)
                    )
                ]
            ),
            log_level=4,
        )
        self._source_data_where = sql_source_filter_builder(
            [
                self._db_variables.value("source_data")[i]
                for i in (self.parameterAsEnums(parameters, self.SOURCE_DATA, context))
            ]
        )

        self._type_geom_where = sql_geom_type_filter_builder(
            [
                self._type_geom_variables[i]
                for i in (self.parameterAsEnums(parameters, self.TYPE_GEOM, context))
            ]
        )

        self._extra_where = self.extra_filters_condition(parameters, context)
        self._layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        self._areas_type = self._areas_types_codes[
            self.parameterAsEnum(parameters, self.AREAS_TYPE, context)
        ]
        self._groupe_taxo_filter = [
            self._db_variables.value("groupe_taxo")[i]
            for i in (
                self.parameterAsEnums(parameters, self.GROUPE_TAXO_FILTER, context)
            )
        ]
        self._taxref_filter_where = self.parameterAsString(
            parameters, self.TAXREF_FILTER, context
        )
        self._taxref_rank_filters = self.taxref_rank_filters(parameters, context)
        self._period_type = self._period_variables[
            self.parameterAsEnum(parameters, self.PERIOD, context)
        ]

        export_views = [
            json.loads(item) for item in self._db_variables.value("export_views")
        ]
        self._export_view = export_views[
            self.parameterAsEnum(parameters, self.EXPORT_VIEWS, context)
        ]["relation"]

        self._format_name = (
            f"{self._layer_name} {str(self._ts.strftime('%Y%m%d_%H%M%S'))}"
        )

        self._taxons_filters = {
            "groupe_taxo": self._groupe_taxo_filter,
        }

        if self._study_area:
            self._query_area = sql_query_area_builder(
                feedback=feedback, layer=self._study_area, layer_crs=self._layer_crs
            )

        if not self._is_data_extraction:
            self._filters += ["is_present", "is_valid"]

        self.taxon_filtering()

        # Complete the "where" filter with the datetime filter

        # Complete the "where" filter with the extra conditions
        if self._source_data_where:
            self._filters.append(f"({self._source_data_where})")

        if self._type_geom_where:
            self._filters.append(f"({self._type_geom_where})")

        if self._extra_where:
            self._filters.append(f"({self._extra_where})")

        if self._has_histogram:
            self._histogram_option = self._histogram_variables[
                self.parameterAsEnum(parameters, self.HISTOGRAM_OPTIONS, context)
            ]
            if self._histogram_option != "Pas d'histogramme":
                self._output_histogram = self.parameterAsFileOutput(
                    parameters, self.OUTPUT_HISTOGRAM, context
                )
                if not self._output_histogram:
                    raise QgsProcessingException(
                        "Veuillez renseigner un emplacement pour enregistrer votre histogramme !"
                    )


        if self._has_time_interval_form:
            self._time_interval = self._time_interval_variables[
                self.parameterAsEnum(parameters, self.TIME_INTERVAL, context)
            ]
            self.log(message=f"time_interval {self._time_interval}")
            self._monthes = self.parameterAsEnum(parameters, self.MONTHES, context)
            self._taxonomic_rank = self._taxonomic_ranks_labels[
                self.parameterAsEnum(parameters, self.TAXONOMIC_RANK, context)
            ]
            if (
                self._name == "SummaryTablePerTimeInterval"
                and self._time_interval == "Par année"
                and self._period_type == "Pas de filtre temporel"
            ):
                # Exception for time interval syntheses without any time filters,
                # automatically restricted to the 10 last years
                self._period_type = "10 dernières années"
            self.log(message=f"taxonomic_rank {self._taxonomic_rank}")
            aggregation_type = "Nombre de données"
            self._group_by_species = (
                "obs.cd_nom, nom_rang, nom_sci, obs.nom_vern, "
                if self._taxonomic_rank == "Espèces"
                else ""
            )
            (
                self._custom_fields,
                self._x_var,
            ) = sql_timeinterval_cols_builder(
                self,
                self._period_type,
                self._time_interval,
                aggregation_type,
                parameters,
                context,
                feedback,
            )
            # Select species info (optional)
            select_species_info = """
                obs.cd_nom,
                nom_rang as "Rang",
                groupe_taxo AS "Groupe taxo",
                obs.nom_vern AS "Nom vernaculaire",
                nom_sci AS "Nom scientifique"
                """
            # Select taxonomic groups info (optional)
            select_taxo_groups_info = 'groupe_taxo AS "Groupe taxo"'
            self._taxa_fields = (
                select_species_info
                if self._taxonomic_rank == "Espèces"
                else select_taxo_groups_info
            )
            self.log(message=self._taxa_fields)

        time_filter = sql_datetime_filter_builder(
            self, self._period_type, self._ts, parameters, context
        )
        feedback.pushDebugInfo(f"time_filter {time_filter}")

        if time_filter:
            self._filters.append(time_filter)

        status_columns = self._db_variables.value("status_columns")
        feedback.pushDebugInfo(f"status_columns {status_columns}")
        if status_columns:
            feedback.pushDebugInfo(f"in status_columns condition {status_columns}")
            try:
                status_columns_as_dict = ast.literal_eval(
                    json.loads(self._db_variables.value("status_columns"))
                )
                feedback.pushDebugInfo(
                    f"status_columns_as_dict {status_columns_as_dict}"
                )
                self._status_columns_db = [
                    key for key, _value in status_columns_as_dict.items()
                ]
                self._status_columns_with_alias = [
                    f'{key} as "{value}"'
                    for key, value in status_columns_as_dict.items()
                ]
            except Exception as e:
                feedback.pushDebugInfo(f"status column ERROR {e}")
                pass

        # EXECUTE THE SQL QUERY
        self._uri = uri_from_name(self._connection)
        query = self._query.format(
            areas_type=self._areas_type,
            query_area=self._query_area,
            export_view=self._export_view,
            where_filters=" AND ".join(self._filters),
            taxonomic_rank_label=self._taxonomic_rank_label,
            taxonomic_rank_db=self._taxonomic_rank_db,
            group_by_species=self._group_by_species,
            taxa_fields=self._taxa_fields,
            custom_fields=self._custom_fields,
            status_columns_fields=(
                (
                    "\n, ".join(self._status_columns_db)
                    + (", " if self._status_columns_db else "")
                )
                if self._taxonomic_rank == "Espèces"
                else ""
            ),
            status_columns_with_alias=(
                (
                    "\n, ".join(self._status_columns_with_alias)
                    + (", " if self._status_columns_with_alias else "")
                )
                if self._taxonomic_rank == "Espèces"
                else ""
            ),
        )
        self.log(message=query)
        feedback.pushDebugInfo(f"query: {query}")
        geom_field = "geom" if self._is_map_layer else None

        self._uri.setDataSource("", f"({query})", geom_field, "", self._primary_key)  # type: ignore

        self._layer = QgsVectorLayer(self._uri.uri(), self._format_name, "postgres")
        self._layer_features_count = self._layer.featureCount()
        self.log(message=f"features count {self._layer_features_count}")
        feedback.pushDebugInfo(f"features count {self._layer_features_count}")

        if self._layer_features_count == 0:
            raise QgsProcessingException(f"Couche de résultat vide")
        check_layer_is_valid(feedback, self._layer)

        if self._histogram_option != "Pas d'histogramme" and self._output_histogram:
            self.histogram_builder(self._taxonomic_rank_label)


        with open(
            os.path.join(plugin_path, os.pardir, "action_scripts", "csv_formatter.py"),
            "r",
            encoding="utf-8",
        ) as file:
            action_code = file.read()
            action = QgsAction(
                QgsAction.GenericPython,
                "Exporter la couche sous format Excel dans mon dossier utilisateur avec la mise en forme adaptée",
                action_code,
                os.path.join(plugin_path, os.pardir, "icons", "excel.png"),
                False,
                "Exporter sous format Excel",
                {"Layer"},
            )
            self._layer.actions().addAction(action)
        
        # JOKE
        with open(
            os.path.join(plugin_path, os.pardir, "action_scripts", "joke.py"),
            "r",
            encoding="utf-8",
        ) as file:
            joke_action_code = file.read()
            joke_action = QgsAction(
                QgsAction.GenericPython,
                "Rédiger mon rapport",
                joke_action_code,
                os.path.join(plugin_path, os.pardir, "icons", "word.png"),
                False,
                "Rédiger mon rapport",
                {"Layer"},
            )
            self._layer.actions().addAction(joke_action)

        load_layer(context, self._layer, self.OUTPUT)

        return {self.OUTPUT: self._layer.id()}
    

    def postProcessAlgorithm(self, _context, _feedback) -> Dict:  # noqa N802
        if iface is not None and self._layer_features_count < 1000:
            iface.showAttributeTable(self._layer)
            iface.setActiveLayer(self._layer)

        return {}


    def histogram_builder(
        self,
        taxonomic_rank_label: str,
    ) -> None:
        """generate histogram"""
        plt.close()
        x_var = [
            (
                feature[self._taxonomic_rank_label]
                if feature[self._taxonomic_rank_label] != "Pas de correspondance taxref"
                else "Aucune correspondance"
            )
            for feature in self._layer.getFeatures()
        ]
        y_var = [
            int(feature[self._histogram_option])
            for feature in self._layer.getFeatures()
        ]
        if len(x_var) <= 20:
            plt.subplots_adjust(bottom=0.5)
        elif len(x_var) <= 80:
            plt.figure(figsize=(20, 8))
            plt.subplots_adjust(bottom=0.3, left=0.05, right=0.95)
        else:
            plt.figure(figsize=(40, 16))
            plt.subplots_adjust(bottom=0.2, left=0.03, right=0.97)
        plt.bar(range(len(x_var)), y_var, tick_label=x_var)
        plt.xticks(rotation="vertical")
        plt.xlabel(self._taxonomic_rank_label)
        plt.ylabel(self._histogram_option.replace("Nb", "Nombre"))
        plt.title(
            f'{self._histogram_option.replace("Nb", "Nombre")} par {self._taxonomic_rank_label[0].lower() + taxonomic_rank_label[1:].replace("taxo", "taxonomique")}'
        )
        if self._output_histogram[-4:] != ".png":
            self._output_histogram += ".png"
        plt.savefig(self._output_histogram)

    def _settings_list(self, key: str) -> List[str]:
        value = self._db_variables.value(key)
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value if item not in (None, "")]
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            try:
                loaded_value = json.loads(value)
            except json.JSONDecodeError:
                return [value]
            if isinstance(loaded_value, list):
                return [
                    str(item)
                    for item in loaded_value
                    if item not in (None, "")
                ]
            return [str(loaded_value)]
        return [str(value)]

    @staticmethod
    def _sql_literal(value: str) -> str:
        return "'{}'".format(str(value).replace("'", "''"))

    @staticmethod
    def _sql_like_value(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def taxref_rank_filters(
        self, parameters: Dict[str, Any], context: QgsProcessingContext
    ) -> Dict[str, List[str]]:
        filters = {}
        for param_name, (setting_key, _label, column) in self._taxref_filter_settings.items():
            if self.parameterDefinition(param_name) is None:
                continue
            selected_indexes = self.parameterAsEnums(parameters, param_name, context)
            values = self._settings_list(setting_key)
            selected_values = [
                values[index] for index in selected_indexes if index < len(values)
            ]
            if selected_values:
                filters[column] = selected_values
        return filters

    def extra_filters_condition(
        self, parameters: Dict[str, Any], context: QgsProcessingContext
    ) -> Optional[str]:
        conditions = []
        for field_param, operator_param, value_param in self._extra_filter_params:
            field_index = self.parameterAsEnum(parameters, field_param, context)
            if field_index <= 0:
                continue
            if field_index >= len(self._extra_filter_fields):
                raise QgsProcessingException("Filtre avancé invalide.")

            field = self._extra_filter_fields[field_index]
            operator = self._extra_filter_operators[
                self.parameterAsEnum(parameters, operator_param, context)
            ]
            value = self.parameterAsString(parameters, value_param, context).strip()
            conditions.append(
                self.extra_filter_condition(
                    field["column"], field["type"], operator, value
                )
            )

        if conditions:
            return " AND ".join(conditions)
        return None

    def extra_filter_condition(
        self, column: str, field_type: str, operator: str, value: str
    ) -> str:
        if operator in ("Est nul", "N'est pas nul"):
            sql_operator = "IS NULL" if operator == "Est nul" else "IS NOT NULL"
            return f"{column} {sql_operator}"

        if not value:
            raise QgsProcessingException(
                f"Veuillez renseigner une valeur pour le filtre avancé sur {column}."
            )

        if operator in ("Contient", "Commence par") and field_type != "text":
            raise QgsProcessingException(
                "Les opérateurs textuels ne peuvent être utilisés que sur des champs texte."
            )

        if operator == "Dans la liste":
            values = [item.strip() for item in value.split(",") if item.strip()]
            if not values:
                raise QgsProcessingException(
                    f"Veuillez renseigner une liste de valeurs pour {column}."
                )
            return f"{column} IN ({', '.join(self.sql_typed_values(values, field_type))})"

        if field_type == "text":
            if operator == "Contient":
                return (
                    f"{column} ILIKE {self._sql_literal('%' + self._sql_like_value(value) + '%')}"
                    " ESCAPE '\\'"
                )
            if operator == "Commence par":
                return (
                    f"{column} ILIKE {self._sql_literal(self._sql_like_value(value) + '%')}"
                    " ESCAPE '\\'"
                )
            if operator not in ("=", "!="):
                raise QgsProcessingException(
                    "Les champs texte acceptent uniquement =, !=, Contient, "
                    "Commence par, Dans la liste, Est nul et N'est pas nul."
                )
            return f"{column} {operator} {self._sql_literal(value)}"

        if operator in ("Contient", "Commence par"):
            raise QgsProcessingException(
                "Les opérateurs Contient et Commence par sont réservés aux champs texte."
            )

        if operator not in ("=", "!=", ">", ">=", "<", "<="):
            raise QgsProcessingException(f"Opérateur non autorisé pour {column}.")

        return f"{column} {operator} {self.sql_typed_value(value, field_type)}"

    def sql_typed_values(self, values: List[str], field_type: str) -> List[str]:
        return [self.sql_typed_value(value, field_type) for value in values]

    def sql_typed_value(self, value: str, field_type: str) -> str:
        if field_type == "int":
            if not re.fullmatch(r"-?\d+", value):
                raise QgsProcessingException(f"La valeur {value} doit être un entier.")
            return value

        if field_type == "date":
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise QgsProcessingException(
                    f"La valeur {value} doit être une date au format AAAA-MM-JJ."
                )
            return f"{self._sql_literal(value)}::date"

        if field_type == "bool":
            bool_values = {
                "true": "true",
                "1": "true",
                "t": "true",
                "yes": "true",
                "y": "true",
                "oui": "true",
                "false": "false",
                "0": "false",
                "f": "false",
                "no": "false",
                "n": "false",
                "non": "false",
            }
            normalized_value = value.strip().lower()
            if normalized_value not in bool_values:
                raise QgsProcessingException(
                    f"La valeur {value} doit être un booléen: oui/non ou true/false."
                )
            return bool_values[normalized_value]

        return self._sql_literal(value)


    def taxon_filtering_condition(self) -> Optional[str]:
        """Filtering taxa"""
        taxon_filters = self.sql_taxons_filter_builder()
        filters = []
        if taxon_filters:
            filters.append(taxon_filters)
        if len(filters):
            return " AND ".join(filters)


    def taxon_filtering(self) -> Optional[str]:
        taxon_filtering_condition = self.taxon_filtering_condition()
        if taxon_filtering_condition:
            raw_query = f"""obs.cd_nom in (SELECT cd_nom
FROM (SELECT taxref.*,
             cor.vn_id,
             cor.groupe_taxo_fr AS groupe_taxo,
             COALESCE(taxref.lb_nom, cor.tx_nom_sci, cor.vn_nom_sci) AS lb_nom_recherche,
             COALESCE(taxref.nom_vern, cor.tx_nom_fr, cor.vn_nom_fr) AS nom_vern_recherche
      FROM taxonomie.taxref
               LEFT JOIN taxonomie.mv_c_cor_vn_taxref AS cor ON cor.cd_nom = taxref.cd_nom ) as t
WHERE {taxon_filtering_condition})
         """
            return self._filters.append(raw_query)

    def sql_taxons_filter_builder(self) -> Optional[str]:
        """
        Construct the sql "where" clause with taxons filters.
        """
        rank_filters = []
        for key, value in self._taxons_filters.items():
            if value:
                value_list = ",".join([self._sql_literal(v) for v in value])
                rank_filters.append(f"{key} in ({value_list})")
        for key, value in self._taxref_rank_filters.items():
            if value:
                value_list = ",".join([self._sql_literal(v) for v in value])
                rank_filters.append(f"{key} in ({value_list})")
        if self._taxref_filter_where:
            terms = [
                term.strip()
                for term in self._taxref_filter_where.split(",")
                if term.strip()
            ]
            for term in terms:
                like_term = self._sql_literal(
                    "%" + self._sql_like_value(term) + "%"
                )
                rank_filters.append(
                    "("
                    f"lb_nom_recherche ILIKE {like_term} ESCAPE '\\' "
                    f"OR nom_vern_recherche ILIKE {like_term} ESCAPE '\\'"
                    ")"
                )
        if len(rank_filters) > 0:
            taxons_where = f"({' AND '.join(rank_filters)})"
            return taxons_where
        return None
