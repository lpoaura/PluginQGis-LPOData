# Scripts de processing framework de la LPO AuRA - QGIS Plugin
[![🎳 Tester](https://github.com/lpoaura/PluginQGis-LPOData/actions/workflows/tester.yml/badge.svg)](https://github.com/lpoaura/PluginQGis-LPOData/actions/workflows/tester.yml)
[![codecov](https://codecov.io/gh/lpoaura/PluginQGis-LPOData/graph/badge.svg?token=AKE1D4GKC3)](https://codecov.io/gh/lpoaura/PluginQGis-LPOData)
[![✅ Linter](https://github.com/lpoaura/PluginQGis-LPOData/actions/workflows/linter.yml/badge.svg)](https://github.com/lpoaura/PluginQGis-LPOData/actions/workflows/linter.yml)
[![🚀 Releaser](https://github.com/lpoaura/PluginQGis-LPOData/actions/workflows/releaser.yml/badge.svg)](https://github.com/lpoaura/PluginQGis-LPOData/actions/workflows/releaser.yml)


[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![flake8](https://img.shields.io/badge/linter-flake8-green)](https://flake8.pycqa.org/)
<!-- [![pylint](https://github.com/lpoaura/PluginQGis-LPODatalint/pylint.svg)](https://github.com/lpoaura/PluginQGis-LPODatalint/) -->

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

Ce plugin ajoute à QGIS des scripts d'exploitation des données naturalistes de
la [LPO Auvergne-Rhône-Alpes](https://auvergne-rhone-alpes.lpo.fr/). Il s'appuie sur une base de données [Géonature](https://github.com/PnX-SI/).

L'installation et l'utilisation sont documentées [ici](https://github.com/lpoaura/PluginQGis-LPOData/wiki).

Outre la structure de la base de données Géonature, il nécessite :
- la présence de vues matérialisées dans le schéma `taxonomie` (sql dans le dossier config)
- la création du schéma `dbadmin` et de vues matérialisées (sql dans le dossier config)
- la création du schéma `src_lpodatas` et des vues associées (sql dans le dossier config)
- la présence du fichier `startup.py` dans le dossier racine de configuration de QGIS:
    - Linux: `~/.local/share/QGIS/QGIS3/`
    - Windows: `%AppData%/QGIS/QGIS3/`

La base de données sur laquelle les développements ont été faits dispose également des fonctionnalités de [gn_vn2synthese](https://github.com/lpoaura/gn_vn2synthese).

Pour permettre l'export des données formatées, il est nécessaire de disposer de la libraire `openpyxl`. Pour l'installer `py3_env` puis `python3 -m pip install --user openpyxl`.

<img align="center" src="https://github.com/lpoaura/PluginQGis-LPOData/blob/master/plugin_qgis_lpo/resources/images/logo_lpo_aura.png">


# Development

Refer to [development](docs/development.md) for developing this QGIS3 plugin.

# License
This plugin is licenced with[GNU General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html)


See [LICENSE](LICENSE) for more information.


### Tooling

This project is configured with the following tools:

- [Black](https://black.readthedocs.io/en/stable/) to format the code without any existential question
- [iSort](https://pycqa.github.io/isort/) to sort the Python imports

Code rules are enforced with [pre-commit](https://pre-commit.com/) hooks.  
Static code analisis is based on: both

See also: [contribution guidelines](CONTRIBUTING.md).

# CI/CD

Plugin is linted, tested, packaged and published with GitHub.

If you mean to deploy it to the [official QGIS plugins repository](https://plugins.qgis.org/), remember to set your OSGeo credentials (`OSGEO_USER_NAME` and `OSGEO_USER_PASSWORD`) as environment variables in your CI/CD tool.


### Documentation

The documentation is generated using Sphinx and is automatically generated through the CI and published on Pages.

- homepage: <https://github.com/lpoaura/PluginQGis-LPOData>
- repository: <https://github.com/lpoaura/PluginQGis-LPOData>
- tracker: <https://github.com/lpoaura/PluginQGis-LPOData/issues>

----

# Next steps

### Set up development environment

> Typical commands on Linux (Ubuntu).

1. If you don't pick the `git init` option, initialize your local repository:

    ```sh
    git init
    ```

1. Follow the [embedded documentation to set up your development environment](./docs/development/environment.md)
1. Add all files to git index to prepare initial commit:

    ```sh
    git add -A
    ```

1. Run the git hooks to ensure that everything runs OK and to start developing on quality standards:

    ```sh
    pre-commit run -a
    ```

### Try to build documentation locally

1. Have a look to the [plugin's metadata.txt file](plugin_qgis_lpo/metadata.txt): review it, complete it or fix it if needed (URLs, etc.).
1. Follow the [embedded documentation to build plugin documentation locally](./docs/development/environment.md)

----

# Contributors

<a href="https://github.com/lpoaura/PluginQGis-LPOData/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=lpoaura/PluginQGis-LPOData" />
</a>
