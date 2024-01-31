# -*- coding: utf-8 -*-

"""Generic Qgis Processing Algorithm classes"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
from qgis.core import (
    QgsAction,
    QgsDataSourceUri,
    QgsMessageLog,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
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

from ..commons.helpers import (
    check_layer_is_valid,
    construct_queries_list,
    construct_sql_array_polygons,
    construct_sql_datetime_filter,
    construct_sql_taxons_filter,
    execute_sql_queries,
    format_layer_export,
    load_layer,
    simplify_name,
)
from ..commons.widgets import DateTimeWidget
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

    def __init__(self) -> None:
        super().__init__()

        # Global settings
        self._name = "myprocessingalgorithm"
        self._display_name = "My Processing Algorithm"
        self._group_id = "maps"
        self._group = "Cartes"
        self._short_help_string = ""
        self._short_description = ""
        self._icon: str

        # processAlgorithm settings
        self._is_map_layer = False
        self._is_table_layer = False
        self._has_time_interval_form = False
        self._has_histogram = False
        self._has_taxonomic_rank_form = False
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
        self._histogram_variables: List[str] = []
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
        self._areas_type: List[str] = []
        self._ts = datetime.now()
        self._array_polygons = None
        self._taxons_filters: Dict[str, List[str]] = {}
        self._is_data_extraction: bool = False
        self._filters: List[str] = []
        self._period_type: str
        self._extra_where: Optional[str] = None
        self._geographic_where_clause: Optional[str] = None
        self._uri: QgsDataSourceUri

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
        return QIcon(os.path.join(plugin_path, os.pardir, "icons", self._icon))

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
        super().initAlgorithm(_config)

        required_text = '<span style="color:#952132">(requis)</span>'
        optional_text = "(facultatif)"
        item_pos = 0
        # self._ts = datetime.now()
        # self._db_variables = QgsSettings()
        item_pos += 1
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.DATABASE,
                self.tr(
                    f"""<b style="color:#0a84db">BASE DE DONNÉES</b> {required_text}<br/>
                    <b>*{item_pos}/</b> Sélectionnez votre <u>connexion</u> à la base de données LPO"""
                ),
                "postgres",
                defaultValue="geonature_lpo",
                optional=False,
            )
        )
        item_pos += 1
        # Input vector layer = study area
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STUDY_AREA,
                self.tr(
                    f"""<b style="color:#0a84db">ZONE D'ÉTUDE</b> {required_text}<br/>
                    <b>*{item_pos}/</b> Sélectionnez votre <u>zone d'étude</u>, à partir de laquelle seront extraits les résultats"""
                ),
                [QgsProcessing.TypeVectorPolygon],
            )
        )

        # if self._has_taxonomic_rank_form and self._taxonomic_ranks:
        #     item_pos += 1
        #     self._taxonomic_ranks_labels = [
        #         value for _key, value in self._taxonomic_ranks.items()
        #     ]
        #     self._taxonomic_ranks_db = [
        #         key for key, _value in self._taxonomic_ranks.items()
        #     ]
        #     taxonomic_rank = QgsProcessingParameterEnum(
        #         self.TAXONOMIC_RANK,
        #         self.tr(
        #             f"""<b style="color:#0a84db">RANG TAXONOMIQUE</b><br/>
        #             <b>*{item_pos}/</b> Sélectionnez le <u>rang taxonomique</u> qui vous intéresse"""
        #         ),
        #         self._taxonomic_ranks_labels,
        #         allowMultiple=False,
        #     )
        #     taxonomic_rank.setMetadata(
        #         {
        #             "widget_wrapper": {
        #                 "useCheckBoxes": True,
        #                 "columns": len(self._taxonomic_ranks_labels) / 2,
        #             }
        #         }
        #     )
        #     self.addParameter(taxonomic_rank)

        if self._has_time_interval_form:
            item_pos += 1
            # ## Time interval and period ###
            time_interval = QgsProcessingParameterEnum(
                self.TIME_INTERVAL,
                self.tr(
                    f"""<b style="color:#0a84db">AGRÉGATION TEMPORELLE ET PÉRIODE</b><br/>
                    <b>*{item_pos}/</b> Sélectionnez l'<u>agrégation temporelle</u> qui vous intéresse"""
                ),
                self.interval_variables,
                allowMultiple=False,
            )
            time_interval.setMetadata(
                {
                    "widget_wrapper": {
                        "useCheckBoxes": True,
                        "columns": len(self.interval_variables),
                    }
                }
            )
            self.addParameter(time_interval)

        item_pos += 1
        period_type = QgsProcessingParameterEnum(
            self.PERIOD,
            self.tr(
                f"""<b style="color:#0a84db">PÉRIODE</b> {required_text}<br/>
                    <b>*{item_pos}/</b> Sélectionnez une <u>période</u> pour filtrer vos données d'observations"""
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
            """- Date de début <i style="color:#952132">(nécessaire seulement si vous avez sélectionné l'option <b>Date de début - Date de fin</b>)</i> :""",
            defaultValue="",
            optional=True,
        )
        start_date.setMetadata({"widget_wrapper": {"class": DateTimeWidget}})
        self.addParameter(start_date)
        end_date = QgsProcessingParameterString(
            self.END_DATE,
            """- Date de fin <i style="color:#952132">(nécessaire seulement si vous avez sélectionné l'option <b>Date de début - Date de fin</b>)</i> :""",
            optional=True,
        )
        end_date.setMetadata({"widget_wrapper": {"class": DateTimeWidget}})
        self.addParameter(end_date)

        # ## Taxons filters ##
        item_pos += 1
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GROUPE_TAXO,
                self.tr(
                    f"""<b style="color:#0a84db">TAXONS</b> {optional_text}<br/>
                    <b>{item_pos}/</b> Vous pouvez sélectionner un/plusieurs <u>groupes taxonomiques</u> dans la liste déroulante suivante (choix multiples)<u>Sinon</u>, vous pouvez ignorer cette étape.<br/>
                    - Groupes taxonomiques :"""
                ),
                self._db_variables.value("groupe_taxo"),
                allowMultiple=True,
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_NAME,
                self.tr(
                    f"""<b style="color:#0a84db">PARAMÉTRAGE DES RESULTATS EN SORTIE</b> {optional_text}<br/>
                    <b>*6/</b> Définissez un <u>nom</u> pour votre nouvelle couche PostGIS"""
                ),
                self.tr(self._output_name),
            )
        )

        # Boolean : True = add the summary table in the DB ; False = don't
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ADD_TABLE,
                self.tr(
                    "Enregistrer les résultats en sortie dans une nouvelle table PostgreSQL"
                ),
                False,
            )
        )

        # Output PostGIS layer = summary map data
        if self._is_map_layer:
            self.addParameter(
                QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    self.tr(
                        f"""<b style="color:#DF7401">EXPORT DES RESULTATS</b> {optional_text}<br/>
                        <b>7/</b> Si cela vous intéresse, vous pouvez <u>exporter</u> votre nouvelle couche sur votre ordinateur. <u>Sinon</u>, vous pouvez ignorer cette étape.<br/>
                        <u>Précisions</u> : La couche exportée est une couche figée qui n'est pas rafraîchie à chaque réouverture de QGis, contrairement à la couche PostGIS.<br/>
                        <font style='color:#DF7401'><u>Aide</u> : Cliquez sur le bouton [...] puis sur le type d'export qui vous convient</font>"""
                    ),
                    QgsProcessing.TypeVectorPolygon,
                    optional=True,
                    createByDefault=False,
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
                    "<b>7/</b> Si cela vous intéresse, vous pouvez <u>exporter</u> les résultats sous forme d'<u>histogramme</u>. Dans ce cas, sélectionnez le type<br/> d'histogramme qui vous convient. <u>Sinon</u>, vous pouvez ignorer cette étape."
                ),
                self._histogram_variables,
                defaultValue="Pas d'histogramme",
            )
            self.addParameter(histogram_options)

            self.addParameter(
                QgsProcessingParameterFileDestination(
                    self.OUTPUT_HISTOGRAM,
                    self.tr(
                        """<b style="color:#0a84db">ENREGISTREMENT DES RESULTATS</b><br/>
                    <b>11/</b> <u style="color:#952132">Si (et seulement si !)</u> vous avez sélectionné l'export sous forme d'<u>histogramme</u>, veuillez renseigner un emplacement<br/> pour l'enregistrer sur votre ordinateur (au format image). <u>Dans le cas contraire</u>, vous pouvez ignorer cette étape.<br/>
                    <font style='color:#06497a'><u>Aide</u> : Cliquez sur le bouton [...] puis sur 'Enregistrer vers un fichier...'</font>"""
                    ),
                    self.tr("image PNG (*.png)"),
                    optional=True,
                    createByDefault=False,
                )
            )

        # Extra "where" conditions
        extra_where = QgsProcessingParameterString(
            self.EXTRA_WHERE,
            self.tr(
                """Vous pouvez ajouter des <u>conditions "where"</u> supplémentaires dans l'encadré suivant, en langage SQL <b style="color:#952132">(commencez par <i>and</i>)</b>"""
            ),
            multiLine=True,
            optional=True,
        )
        extra_where.setFlags(
            extra_where.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(extra_where)

        if self._return_geo_agg:
            areas_types = QgsProcessingParameterEnum(
                self.AREAS_TYPE,
                self.tr(
                    """<b style="color:#0a84db">TYPE D'ENTITÉS GÉOGRAPHIQUES</b><br/>
                    <b>*3/</b> Sélectionnez le <u>type d'entités géographiques</u> qui vous intéresse"""
                ),
                self._areas_variables,
                allowMultiple=False,
            )
            areas_types.setMetadata(
                {"widget_wrapper": {"useCheckBoxes": True, "columns": 3}}
            )
            self.addParameter(areas_types)

    def processAlgorithm(  # noqa N802
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict:
        """
        Here is where the processing itself takes place.
        """
        # PARAMETERS
        # Retrieve the input vector layer = study area
        if feedback is None:
            feedback = QgsProcessingFeedback()

        ts = datetime.now()
        # Form values
        self._connection = self.parameterAsString(parameters, self.DATABASE, context)
        self._add_table = self.parameterAsBool(parameters, self.ADD_TABLE, context)
        self._study_area = self.parameterAsSource(parameters, self.STUDY_AREA, context)
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
        self._format_name = f"{self._layer_name} {str(ts.strftime('%Y%m%d_%H%M%S'))}"

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
        #     f"ST_Intersects(la.geom, ST_union({construct_sql_array_polygons(self._study_area)})"
        # )
        if self._study_area:
            self._array_polygons = construct_sql_array_polygons(self._study_area)
        if not self._is_data_extraction:
            self._filters += ["is_present", "is_valid"]
        taxon_filters = construct_sql_taxons_filter(self._taxons_filters)
        if taxon_filters:
            self._filters.append(taxon_filters)

        # Complete the "where" filter with the datetime filter
        time_filter = construct_sql_datetime_filter(
            self, self._period_type, ts, parameters, context
        )
        if time_filter:
            self._filters.append(time_filter)
        # Complete the "where" filter with the extra conditions
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

        # EXECUTE THE SQL QUERY
        self._uri = uri_from_name(self._connection)
        query = self._query.format(
            areas_type=self._areas_type,
            array_polygons=self._array_polygons,
            where_filters=" AND ".join(self._filters),
            taxonomic_rank_label=self._taxonomic_rank_label,
            taxonomic_rank_db=self._taxonomic_rank_db,
        )
        feedback.pushDebugInfo(query)
        geom_field = "geom" if self._is_map_layer else None
        if self._add_table:
            # Define the name of the PostGIS summary table which will be created in the DB
            table_name = simplify_name(self._format_name)
            # Define the SQL queries
            queries = construct_queries_list(table_name, query)
            # Execute the SQL queries
            execute_sql_queries(context, feedback, self._connection, queries)
            # Format the URI
            self._uri.setDataSource(None, table_name, geom_field, "", "id")
        else:
            # Format the URI with the query
            self._uri.setDataSource("", f"({query})", geom_field, "", "id")

        self._layer = QgsVectorLayer(self._uri.uri(), self._format_name, "postgres")
        check_layer_is_valid(feedback, self._layer)

        if self._histogram_option != "Pas d'histogramme" and self._output_histogram:
            self.histogram_builder(self._taxonomic_rank_label)

        load_layer(context, self._layer)

        if self._is_map_layer:
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
