# Installation

## Configurations préalables

### Création de la connexion `PostGIS`

Dans QGIS, créez une nouvelle connexion PostGIS et nommez-la `geonature_lpo`, en choisissant les paramètres d'identification adaptés à votre situation.

### Enregistrement du fichier `startup.py`

Téléchargez le fichier [`startup.py`](https://raw.githubusercontent.com/lpoaura/PluginQGis-LPOData/master/config/startup.py) et placez le dans votre dossier de configuration de QGIS (**sans modifier son nom !**) à l'emplacement suivant de votre ordinateur : `C:\Users\<VotreNomUtilisateur>\AppData\Roaming\QGIS\QGIS3`

> :warning: Le dossier `<VotreNomUtilisateur>` correspond à **VOTRE propre** dossier utilisateur.

> :information_source: Le dossier `AppData` est un dossier **caché**, il est possible que vous ayez besoin de l'afficher manuellement !

## Installation du plugin

Ajouter le lien suivant à la liste des dépots d'extensions (Menu <kbd>Extension</kbd> > <kbd>Installer/Gérer les extensions...</kbd> puis sur le menu <kbd>Paramètres</kbd>):

<https://github.com/lpoaura/PluginQGis-LPOData/releases/latest/download/plugins.xml>

Rechargez ensuite les dépots et rendez-vous sur l'onglet <kbd>Toutes</kbd>, recherchez le plugin `LPO GeoNature tools` et installez le. Vous disposez maitenant d'une nouvelle liste de scripts votre **Boîte à outils de traitements** :

![processing_toolbox](../images/processing_toolbox.png)
