# Scripts de processing framework de la LPO AuRA

Ce plugin ajoute à QGIS des scripts d'exploitation des données naturalistes de
la [LPO Auvergne-Rhône-Alpes](https://auvergne-rhone-alpes.lpo.fr/). Il s'appuie sur une base de données [Géonature] (https://github.com/pnx-si/).

L'installation et l'utilisation sont documentatées [ici] (https://github.com/lpoaura/PluginQGis-LPOData/wiki).

Outre la structure de la base de données Géonature, il nécessite :
- la présence de vues matérialisées dans le schéma `taxonomie` (sql dans le dossier config)
- la création du schéma `dbadmin` et de vues matérialisées (sql dans le dossier config)
- la création du schéma `src_lpodatas` et des vues associées (sql dans le dossier config)
- la présence du fichier `startup.py`.

La base de données sur laquelle les développements ont été faits dispose également des fonctionnalités de [gn_vn2synthese] (https://github.com/lpoaura/gn_vn2synthese).




<img align="cebter" src="https://github.com/lpoaura/PluginQGis-LPOData/blob/develop_aura/config/logo_lpo_aura.png">


