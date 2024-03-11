"""Generic Qgis Processing Algorithm classes"""

import ast
import json
import os
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
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
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
    sql_array_polygons_builder,
    sql_datetime_filter_builder,
    sql_geom_type_filter_builder,
    sql_queries_list_builder,
    sql_source_filter_builder,
    sql_taxons_filter_builder,
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
    GROUPE_TAXO = "GROUPE_TAXO"
    # REGNE = "REGNE"
    # PHYLUM = "PHYLUM"
    # CLASSE = "CLASSE"
    # ORDRE = "ORDRE"
    # FAMILLE = "FAMILLE"
    # GROUP1_INPN = "GROUP1_INPN"
    # GROUP2_INPN = "GROUP2_INPN"
    PERIOD = "PERIOD"
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
    TIME_INTERVAL = "TIME_INTERVAL"
    ADD_FIVE_YEARS = "ADD_FIVE_YEARS"
    TEST = "TEST"
    START_MONTH = "START_MONTH"
    START_YEAR = "START_YEAR"
    END_MONTH = "END_MONTH"
    END_YEAR = "END_YEAR"
    EXTRA_WHERE = "EXTRA_WHERE"
    OUTPUT = "OUTPUT"
    OUTPUT_NAME = "OUTPUT_NAME"
    ADD_TABLE = "ADD_TABLE"
    OUTPUT_HISTOGRAM = "OUTPUT_HISTOGRAM"
    ADD_HISTOGRAM = "ADD_HISTOGRAM"
    HISTOGRAM_OPTIONS = "HISTOGRAM_OPTIONS"
    SOURCE_DATA = "SOURCE_DATA"
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
        self._has_time_interval_form = False
        self._has_histogram = False
        self._has_taxonomic_rank_form = False
        self._has_source_data_filter = False
        self._has_type_geom_filter = False
        self._export_output = False
        self._query = ""
        self._return_geo_agg: bool = False
        self._db_variables = QgsSettings()
        self._connection: str
        self._add_table: bool
        self._layer_name: str
        self._layer: QgsVectorLayer
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
        self._output_name = "output"
        self._study_area = None
        self._format_name: str = "output"
        self._areas_type: str
        self._ts = datetime.now()
        self._array_polygons = None
        self._taxons_filters: Dict[str, List[str]] = {}
        self._is_data_extraction: bool = False
        self._filters: List[str] = []
        self._period_type: str
        self._extra_where: Optional[str] = None
        self._source_data_where: Optional[str] = None
        self._type_geom_where: Optional[str] = None
        self._geographic_where_clause: Optional[str] = None
        self._uri: QgsDataSourceUri
        self._primary_key = "id"
        self._output_histogram: str
        self._group_by_species: str = ""
        self._taxa_fields: Optional[str] = None
        self._custom_fields: Optional[str] = None
        self._x_var: Optional[List[str]] = None
        self._lr_columns_db: List[str] = ["lr_r"]
        self._lr_columns_with_alias: List[str] = ['lr_r as "LR Régionale"']
        self._time_interval: str
        self._start_year: int
        self._end_year: int

    def tr(self, string: str) -> str:
        """QgsProcessingAlgorithm translatable string with the self.tr() function."""
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):  # noqa N802
        return type(self)()

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

    def groupId(self) -> str:  # noqa N802
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self._group_id

    def group(self) -> str:
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self._group)

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
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.DATABASE,
                self.tr(
                    f"""<b style="color:#0a84db">BASE DE DONNÉES</b> {required_text} :
                    sélectionnez votre <u>connexion</u> à la base de données LPO"""
                ),
                "postgres",
                defaultValue="geonature_lpo",
                optional=False,
            )
        )
        # Input vector layer = study area
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STUDY_AREA,
                self.tr(
                    f"""<b style="color:#0a84db">ZONE D'ÉTUDE</b> {required_text} :
                    sélectionnez votre <u>zone d'étude</u>,
                    à partir de laquelle seront extraits les résultats"""
                ),
                [QgsProcessing.TypeVectorPolygon],
            )
        )

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
                    f"""<b style="color:#0a84db">RANG TAXONOMIQUE</b> {required_text}"""
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

        if self._has_time_interval_form:
            # ## Time interval and period ###
            time_interval = QgsProcessingParameterEnum(
                self.TIME_INTERVAL,
                self.tr(
                    f"""<b style="color:#0a84db">AGRÉGATION TEMPORELLE</b> {required_text}"""
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

            self.addParameter(
                QgsProcessingParameterEnum(
                    self.START_MONTH,
                    self.tr("Mois de début"),
                    self._months_names_variables,
                    allowMultiple=False,
                    optional=True,
                )
            )

            self.addParameter(
                QgsProcessingParameterNumber(
                    self.START_YEAR,
                    self.tr("Année de début"),
                    QgsProcessingParameterNumber.Integer,
                    defaultValue=2010,
                    minValue=1800,
                    maxValue=int(self._ts.strftime("%Y")),
                )
            )

            self.addParameter(
                QgsProcessingParameterEnum(
                    self.END_MONTH,
                    self.tr("Mois de fin"),
                    self._months_names_variables,
                    allowMultiple=False,
                    optional=True,
                )
            )

            self.addParameter(
                QgsProcessingParameterNumber(
                    self.END_YEAR,
                    self.tr("Année de fin"),
                    QgsProcessingParameterNumber.Integer,
                    defaultValue=self._ts.strftime("%Y"),
                    minValue=1800,
                    maxValue=int(self._ts.strftime("%Y")),
                )
            )
        else:
            period_type = QgsProcessingParameterEnum(
                self.PERIOD,
                self.tr(
                    f"""<b style="color:#0a84db">PÉRIODE</b> {required_text} :
                    sélectionnez une <u>période</u> pour filtrer vos données
                    d'observations"""
                ),
                self._period_variables,
                allowMultiple=False,
                optional=False,
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
                optional=True,
            )
            end_date.setMetadata({"widget_wrapper": {"class": DateTimeWidget}})
            self.addParameter(end_date)

        if self._return_geo_agg:
            areas_types = QgsProcessingParameterEnum(
                self.AREAS_TYPE,
                self.tr(
                    f"""<b style="color:#0a84db">TYPE D'ENTITÉS GÉOGRAPHIQUES</b> {required_text} :
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
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GROUPE_TAXO,
                self.tr(
                    f"""<b style="color:#0a84db">TAXONS</b> {optional_text} :
                    filtrer les données par groupes taxonomiques"""
                ),
                self._db_variables.value("groupe_taxo"),
                allowMultiple=True,
                optional=True,
            )
        )

        if self._has_histogram:
            # add_histogram = QgsProcessingParameterEnum(
            #     self.ADD_HISTOGRAM,
            #     self.tr(
            #         """<b>10/</b> Cochez la case ci-dessous si vous souhaitez <u>exporter</u> les résultats sous la forme d'un <u>histogramme</u> du total par<br/> pas de temps choisi."""
            #     ),
            #     [
            #         "Oui, je souhaite exporter les résultats sous la forme d'un histogramme du total par pas de temps choisi"
            #     ],
            #     allowMultiple=True,
            #     optional=True,
            # )
            # add_histogram.setMetadata(
            #     {"widget_wrapper": {"useCheckBoxes": True, "columns": 1}}
            # )
            # self.addParameter(add_histogram)

            histogram_options = QgsProcessingParameterEnum(
                self.HISTOGRAM_OPTIONS,
                self.tr(
                    f"""<b style="color:#0a84db">HISTOGRAMME</b> {optional_text} :
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
                self.tr(
                    """Emplacement de l'enregistrement du ficher
                    (format image PNG) de l'histogramme"""
                ),
                self.tr("image PNG (*.png)"),
                # optional=True,
                # createByDefault=False,
            )
            output_histogram.setFlags(
                output_histogram.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
            self.addParameter(output_histogram)

        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_NAME,
                self.tr(
                    f"""<b style="color:#0a84db">PARAMÉTRAGE DES RESULTATS EN SORTIE</b>
                    {optional_text} : personnalisez le nom de votre couche
                    en base de données"""
                ),
                self.tr(self._output_name),
            )
        )

        # Boolean : True = add the summary table in the DB ; False = don't
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ADD_TABLE,
                self.tr(
                    "Enregistrer les résultats en sortie dans une nouvelle table en base de données"
                ),
                False,
            )
        )

        # Output PostGIS layer = summary map data
        # if self._is_map_layer:
        #     self.addParameter(
        #         QgsProcessingParameterFeatureSink(
        #             self.OUTPUT,
        #             self.tr(
        #                 f"""<b style="color:#DF7401">EXPORT DES RESULTATS</b> {optional_text}<br/>
        #                 <b>7/</b> Si cela vous intéresse, vous pouvez <u>exporter</u> votre nouvelle couche sur votre ordinateur. <u>Sinon</u>, vous pouvez ignorer cette étape.<br/>
        #                 <u>Précisions</u> : La couche exportée est une couche figée qui n'est pas rafraîchie à chaque réouverture de QGis, contrairement à la couche PostGIS.<br/>
        #                 <font style='color:#DF7401'><u>Aide</u> : Cliquez sur le bouton [...] puis sur le type d'export qui vous convient</font>"""
        #             ),
        #             QgsProcessing.TypeVectorPolygon,
        #             optional=True,
        #             createByDefault=False,
        #         )
        #     )

        if self._has_source_data_filter:
            source_data_where = QgsProcessingParameterEnum(
                self.SOURCE_DATA,
                self.tr("Sources de données"),
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
                self.tr("Type de géométries"),
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
        # Extra "where" conditions
        extra_where = QgsProcessingParameterString(
            self.EXTRA_WHERE,
            self.tr(
                """Vous pouvez ajouter des <u>conditions <code>where</code>
                supplémentaires dans l'encadré suivant, en langage SQL"""
            ),
            multiLine=True,
            optional=True,
        )
        extra_where.setFlags(
            extra_where.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(extra_where)

    def processAlgorithm(  # noqa N802
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Optional[dict]:
        """
        Here is where the processing itself takes place.
        """
        # PARAMETERS
        # Retrieve the input vector layer = study area
        if feedback is None:
            feedback = QgsProcessingFeedback()

        # Form values
        self._connection = self.parameterAsString(parameters, self.DATABASE, context)
        self._add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)
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

        self._extra_where = self.parameterAsString(
            parameters, self.EXTRA_WHERE, context
        )
        self._layer_name = self.parameterAsString(parameters, self.OUTPUT_NAME, context)
        self._areas_type = self._areas_types_codes[
            self.parameterAsEnum(parameters, self.AREAS_TYPE, context)
        ]
        self._groupe_taxo = [
            self._db_variables.value("groupe_taxo")[i]
            for i in (self.parameterAsEnums(parameters, self.GROUPE_TAXO, context))
        ]
        self._period_type = self._period_variables[
            self.parameterAsEnum(parameters, self.PERIOD, context)
        ]
        # regne = [
        #     self._db_variables.value("regne")[i]
        #     for i in (self.parameterAsEnums(parameters, self.REGNE, context))
        # ]
        # phylum = [
        #     self._db_variables.value("phylum")[i]
        #     for i in (self.parameterAsEnums(parameters, self.PHYLUM, context))
        # ]
        # classe = [
        #     self._db_variables.value("classe")[i]
        #     for i in (self.parameterAsEnums(parameters, self.CLASSE, context))
        # ]
        # ordre = [
        #     self._db_variables.value("ordre")[i]
        #     for i in (self.parameterAsEnums(parameters, self.ORDRE, context))
        # ]
        # famille = [
        #     self._db_variables.value("famille")[i]
        #     for i in (self.parameterAsEnums(parameters, self.FAMILLE, context))
        # ]
        # group1_inpn = [
        #     self._db_variables.value("group1_inpn")[i]
        #     for i in (self.parameterAsEnums(parameters, self.GROUP1_INPN, context))
        # ]
        # group2_inpn = [
        #     self._db_variables.value("group2_inpn")[i]
        #     for i in (self.parameterAsEnums(parameters, self.GROUP2_INPN, context))
        # ]
        # Retrieve the output PostGIS layer name and format it
        self._format_name = (
            f"{self._layer_name} {str(self._ts.strftime('%Y%m%d_%H%M%S'))}"
        )

        self._taxons_filters = {
            "groupe_taxo": self._groupe_taxo,
            # "regne": regne,
            # "phylum": phylum,
            # "classe": classe,
            # "ordre": ordre,
            # "famille": famille,
            # "obs.group1_inpn": group1_inpn,
            # "obs.group2_inpn": group2_inpn,
        }

        # WHERE clauses builder
        # TODO: Manage use case
        # self._filters.append(
        #     f"ST_Intersects(la.geom, ST_union({sql_array_polygons_builder(self._study_area)})"
        # )
        if self._study_area:
            self._array_polygons = sql_array_polygons_builder(self._study_area)
        if not self._is_data_extraction:
            self._filters += ["is_present", "is_valid"]
        taxon_filters = sql_taxons_filter_builder(self._taxons_filters)
        if taxon_filters:
            self._filters.append(taxon_filters)

        # Complete the "where" filter with the datetime filter
        time_filter = sql_datetime_filter_builder(
            self, self._period_type, self._ts, parameters, context
        )
        if time_filter:
            self._filters.append(time_filter)
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
            # taxonomic_rank_index = self.parameterAsEnum(
            #     parameters, self.TAXONOMIC_RANK, context
            # )
            # self._taxonomic_rank_label = self._taxonomic_ranks_labels[
            #     taxonomic_rank_index
            # ]
            # self._taxonomic_rank_db = self._taxonomic_ranks_db[taxonomic_rank_index]

        if self._has_time_interval_form:
            self._time_interval = self._time_interval_variables[
                self.parameterAsEnum(parameters, self.TIME_INTERVAL, context)
            ]
            self.log(message=f"time_interval {self._time_interval}", log_level=4)
            self._start_year = self.parameterAsInt(parameters, self.START_YEAR, context)
            self.log(message=f"start_year {self._start_year}", log_level=4)
            self._end_year = self.parameterAsInt(parameters, self.END_YEAR, context)
            self.log(message=f"end_year {self._end_year}", log_level=4)
            if self._end_year < self._start_year:
                raise QgsProcessingException(
                    "Veuillez renseigner une année de fin postérieure à l'année de début !"
                )
            taxonomic_rank = self._taxonomic_ranks_labels[
                self.parameterAsEnum(parameters, self.TAXONOMIC_RANK, context)
            ]
            self.log(message=f"taxonomic_rank {taxonomic_rank}", log_level=4)
            aggregation_type = "Nombre de données"
            self._group_by_species = (
                "obs.cd_nom, obs.cd_ref, nom_rang, nom_sci, obs.nom_vern, "
                if taxonomic_rank == "Espèces"
                else ""
            )
            (
                self._custom_fields,
                self._x_var,
            ) = sql_timeinterval_cols_builder(
                self,
                self._time_interval,
                self._start_year,
                self._end_year,
                aggregation_type,
                parameters,
                context,
                feedback,
            )
            # Select species info (optional)
            select_species_info = """
                /*source_id_sp, */
                obs.cd_nom,
                obs.cd_ref,
                nom_rang as "Rang",
                groupe_taxo AS "Groupe taxo",
                obs.nom_vern AS "Nom vernaculaire",
                nom_sci AS "Nom scientifique\"
                """
            # Select taxonomic groups info (optional)
            select_taxo_groups_info = 'groupe_taxo AS "Groupe taxo"'
            self._taxa_fields = (
                select_species_info
                if taxonomic_rank == "Espèces"
                else select_taxo_groups_info
            )
            self.log(message=self._taxa_fields, log_level=4)

        lr_columns = self._db_variables.value("lr_columns")
        if lr_columns:
            try:
                lr_columns_as_dict = ast.literal_eval(
                    json.loads(self._db_variables.value("lr_columns"))
                )
                self._lr_columns_db = [
                    key for key, _value in lr_columns_as_dict.items()
                ]
                self._lr_columns_with_alias = [
                    f'{key} as "{value}"' for key, value in lr_columns_as_dict.items()
                ]
            except Exception as e:
                print(e)
                pass

        # EXECUTE THE SQL QUERY
        self._uri = uri_from_name(self._connection)
        query = self._query.format(
            areas_type=self._areas_type,
            array_polygons=self._array_polygons,
            where_filters=" AND ".join(self._filters),
            taxonomic_rank_label=self._taxonomic_rank_label,
            taxonomic_rank_db=self._taxonomic_rank_db,
            group_by_species=self._group_by_species,
            taxa_fields=self._taxa_fields,
            custom_fields=self._custom_fields,
            lr_columns_fields="\n, ".join(self._lr_columns_db),
            lr_columns_with_alias="\n, ".join(self._lr_columns_with_alias),
        )
        self.log(message=query, log_level=4)
        geom_field = "geom" if self._is_map_layer else None
        if self._add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = simplify_name(self._format_name)
            # Define the SQL queries
            queries = sql_queries_list_builder(table_name, query)
            # Execute the SQL queries
            execute_sql_queries(context, feedback, self._connection, queries)
            # Format the URI
            self._uri.setDataSource(None, table_name, geom_field, "", self._primary_key)  # type: ignore
        else:
            # Format the URI with the query
            self._uri.setDataSource("", f"({query})", geom_field, "", self._primary_key)  # type: ignore

        self._layer = QgsVectorLayer(self._uri.uri(), self._format_name, "postgres")
        self.log(message=f"features count {self._layer.featureCount()}", log_level=4)

        if self._layer.featureCount() == 0:
            raise QgsProcessingException(f"Couche de résultat vide")
        check_layer_is_valid(feedback, self._layer)

        if self._histogram_option != "Pas d'histogramme" and self._output_histogram:
            self.histogram_builder(self._taxonomic_rank_label)

        load_layer(context, self._layer)

        # if self._is_map_layer:
        if False:
            new_fields = format_layer_export(self._layer)
            (sink, dest_id) = self.parameterAsSink(
                parameters,
                self.OUTPUT,
                context,
                new_fields,
                self._layer.wkbType(),
                self._layer.sourceCrs(),
            )
            if sink is None:
                # Return the PostGIS layer
                return {self.OUTPUT: self._layer.id()}
            else:
                # Dealing with jsonb fields
                old_fields = self._layer.fields()
                invalid_fields = []
                invalid_formats = ["jsonb"]
                for field in old_fields:
                    if field.typeName() in invalid_formats:
                        invalid_fields.append(field.name())
                # Fill the sink and return it
                for feature in self._layer.getFeatures():
                    for invalid_field in invalid_fields:
                        if feature[invalid_field] is not None:
                            feature[invalid_field] = json.dumps(
                                feature[invalid_field],
                                sort_keys=True,
                                indent=4,
                                separators=(",", ": "),
                            )
                    sink.addFeature(feature)
                return {self.OUTPUT: dest_id}
        else:
            with open(
                os.path.join(
                    plugin_path, os.pardir, "action_scripts", "csv_formatter.py"
                ),
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

            return {self.OUTPUT: self._layer.id()}

    def postProcessAlgorithm(self, _context, _feedback) -> Dict:  # noqa N802
        # Open the attribute table of the PostGIS layer
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
