# Scripts de processing framework de la LPO AuRA

![tests](https://github.com/lpoaura/plugin_qgis_lpo/workflows/Tests/badge.svg)
[![codecov.io](https://codecov.io/github/lpoaura/plugin_qgis_lpo/coverage.svg?branch=main)](https://codecov.io/github/lpoaura/plugin_qgis_lpo?branch=main)
![release](https://github.com/lpoaura/plugin_qgis_lpo/workflows/Release/badge.svg)

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)


Ce plugin ajoute à QGIS des scripts d'exploitation des données naturalistes de
la [LPO Auvergne-Rhône-Alpes](https://auvergne-rhone-alpes.lpo.fr/). Il s'appuie sur une base de données [Géonature] (https://github.com/pnx-si/).

L'installation et l'utilisation sont documentatées [ici] (https://github.com/lpoaura/PluginQGis-LPOData/wiki).

Outre la structure de la base de données Géonature, il nécessite :
- la présence de vues matérialisées dans le schéma `taxonomie` (sql dans le dossier config)
- la création du schéma `dbadmin` et de vues matérialisées (sql dans le dossier config)
- la création du schéma `src_lpodatas` et des vues associées (sql dans le dossier config)
- la présence du fichier `startup.py` dans le dossier racine de configuration de QGIS:
    - Linux: `~/.local/share/QGIS/QGIS3/`
    - Windows: `%AppData%/QGIS/QGIS3/`

La base de données sur laquelle les développements ont été faits dispose également des fonctionnalités de [gn_vn2synthese] (https://github.com/lpoaura/gn_vn2synthese).

Pour permettre l'export des données formatées, il est nécessaire de disposer de la libraire `openpyxl`. Pour l'installer `py3_env` puis `python3 -m pip install --user openpyxl`.

<img align="center" src="https://github.com/lpoaura/PluginQGis-LPOData/blob/develop_aura/icons/logo_lpo_aura.png">


## Development

Refer to [development](docs/development.md) for developing this QGIS3 plugin.

## License
This plugin is licenced with[GNU General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html)


See [LICENSE](LICENSE) for more information.
