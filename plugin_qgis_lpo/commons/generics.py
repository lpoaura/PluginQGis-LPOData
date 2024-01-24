# -*- coding: utf-8 -*-

"""Generic Qgis Processing Algorithm classes"""
from typing import List

from qgis.core import QgsMessageLog  # QgsProcessingParameterDefinition,
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterProviderConnection,
    QgsProcessingParameterString,
    QgsSettings,
)

from .widgets import DateTimeWidget


class BaseQgsProcessingAlgorithm(QgsProcessingAlgorithm):
    """Generic custom QgsProcessingAlgorithm class"""

    DATABASE = "DATABASE"
    STUDY_AREA = "STUDY_AREA"
    AREAS_TYPE = "AREAS_TYPE"
    GROUPE_TAXO = "GROUPE_TAXO"
    REGNE = "REGNE"
    PHYLUM = "PHYLUM"
    CLASSE = "CLASSE"
    ORDRE = "ORDRE"
    FAMILLE = "FAMILLE"
    GROUP1_INPN = "GROUP1_INPN"
    GROUP2_INPN = "GROUP2_INPN"
    PERIOD = "PERIOD"
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
    EXTRA_WHERE = "EXTRA_WHERE"
    OUTPUT = "OUTPUT"
    OUTPUT_NAME = "OUTPUT_NAME"
    ADD_TABLE = "ADD_TABLE"

    db_variables = None
    areas_variables: List[str] = []
    period_variables: List[str] = []
    output_name = "output"

    def initAlgorithm(self, _config: None) -> None:  # noqa N802
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.db_variables = QgsSettings()

        self.areas_variables = [
            "Mailles 0.5*0.5",
            "Mailles 1*1",
            "Mailles 5*5",
            "Mailles 10*10",
            "Communes",
        ]
        self.period_variables = [
            "Pas de filtre temporel",
            "5 dernières années",
            "10 dernières années",
            "Cette année",
            "Date de début - Date de fin (à définir ci-dessous)",
        ]
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.DATABASE,
                self.tr(
                    """<b style="color:#0a84db">CONNEXION À LA BASE DE DONNÉES</b><br/>
                    <b>*1/</b> Sélectionnez votre <u>connexion</u> à la base de données LPO"""
                ),
                "postgres",
                defaultValue="geonature_lpo",
            )
        )

        # Input vector layer = study area
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STUDY_AREA,
                self.tr(
                    """<b style="color:#0a84db">ZONE D'ÉTUDE</b><br/>
                    <b>*2/</b> Sélectionnez votre <u>zone d'étude</u>, à partir de laquelle seront extraits les résultats"""
                ),
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        ### Taxons filters ###
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GROUPE_TAXO,
                self.tr(
                    """<b style="color:#0a84db">FILTRES DE REQUÊTAGE</b><br/>
                    <b>4/</b> Si cela vous intéresse, vous pouvez sélectionner un/plusieurs <u>taxon(s)</u> dans la liste déroulante suivante (à choix multiples)<br/> pour filtrer vos données d'observations. <u>Sinon</u>, vous pouvez ignorer cette étape.<br/>
                    - Groupes taxonomiques :"""
                ),
                self.db_variables.value("groupe_taxo"),
                allowMultiple=True,
                optional=True,
            )
        )
        period_type = QgsProcessingParameterEnum(
            self.PERIOD,
            self.tr(
                "<b>*5/</b> Sélectionnez une <u>période</u> pour filtrer vos données d'observations"
            ),
            self.period_variables,
            allowMultiple=False,
            optional=False,
        )
        period_type.setMetadata(
            {
                "widget_wrapper": {
                    "useCheckBoxes": True,
                    "columns": len(self.period_variables) / 2,
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

        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_NAME,
                self.tr(
                    """<b style="color:#0a84db">PARAMÉTRAGE DES RESULTATS EN SORTIE</b><br/>
                    <b>*6/</b> Définissez un <u>nom</u> pour votre nouvelle couche PostGIS"""
                ),
                self.tr(self.output_name),
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
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr(
                    """<b style="color:#DF7401">EXPORT DES RESULTATS</b><br/>
                    <b>7/</b> Si cela vous intéresse, vous pouvez <u>exporter</u> votre nouvelle couche sur votre ordinateur. <u>Sinon</u>, vous pouvez ignorer cette étape.<br/>
                    <u>Précisions</u> : La couche exportée est une couche figée qui n'est pas rafraîchie à chaque réouverture de QGis, contrairement à la couche PostGIS.<br/>
                    <font style='color:#DF7401'><u>Aide</u> : Cliquez sur le bouton [...] puis sur le type d'export qui vous convient</font>"""
                ),
                QgsProcessing.TypeVectorPolygon,
                optional=True,
                createByDefault=False,
            )
        )
