# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- ## Unreleased [{version_tag}](https://github.com/opengisch/qgis-plugin-ci/releases/tag/{version_tag}) - YYYY-MM-DD -->

## 3.5.1 - 2025-09-11

### :bug: Fixes

* Réactive le peuplemnent des paramètres de filtrage et supprime le fichier `startup.py` obsolète (fix #173).

## 3.5.0 - 2025-09-11

### :bug: Fixes

* Intégration des statuts de protection et conservation au tableau de répartition temporelle des observations (fix #163).
* Ajout des références aux jeux de données dans les extractions de données brutes (nom et UUID) (fix #168)
* Amélioration de l'information des utilisateurs sur les choix de filtrages de données restituées (données validées inclues/exclues notamment) (fix #136)
* Ajout du statut de validité SINP des données (fix #169)
* Réécriture de la vue v_c_observations avec l'utilisation de CTE (WIP #170)
* Divers fix (#163, #164, #87)

### :ballot_box_with_check: TODO

La liste des colonnes de statuts de protection/conservation des espèces attendues dans les synthèses espèces sont à définir dans une variable de la table gn_commons.t_parameters comme dans l'exemple suivant. Elles correspondent à la liste des statuts de la vue matérialisée `taxonomie.mv_c_statut`:

```sql
INSERT INTO gn_commons.t_parameters ( 
       id_organism, 
       parameter_name, 
       parameter_desc, 
       parameter_value,
       parameter_extra_value
       )
VALUES (
       0, 
       'plugin_qgis_lpo_status_columns',
       'Liste des colonnes de statuts de protection/conservation à utilisées pour le plugin QGIS LPO',
       , '"{''lr_france'':''LR France'',''lr_r'': ''LR Régionale'',''n2k'':''Natura 2000'',''prot_nat'':''Protection nationale'',''conv_berne'':''Convention de Berne'',''conv_bonn'':''Convention de Bonn''}"'
       , NULL);
```


## 3.4.0 - 2025-01-28

* Add new algorithm script to extract data from `gn_exports.v_synthese_sinp`. This algorithm script can be disabled by setting a new parameter in database (tables `gn_commons.t_parameters`) (fix #159).

### Version note

To disable this new feature, execute this SQL script

```sql
INSERT INTO gn_commons.t_parameters ( id_organism, parameter_name, parameter_desc, parameter_value
                                    , parameter_extra_value)
VALUES ( 0, 'plugin_qgis_lpo_exclude_export_sinp'
       , 'Option pour exclure le script d''export SINP du plugin QGIS LPO (valeurs possibles: "false","true")', 'true'
       , NULL);
```

## 3.3.8 - 2024-11-05

* Condition attribute table display on layers containing less than 1000 data.

## 3.3.7 - 2024-11-04

* Fix missing data when extracting from a specific date (start_date = end_date) (fix #150).

## 3.3.6 - 2024-09-30

* Refactor query area generator (fix #148 from PR #149).

## 3.3.5 - 2024-09-25

* Time interval script (fix #145 from PR #147) is now fixed and usable as expected

## 3.3.4 - 2024-09-24

* Plugin menu is now correctly removed from bar when plugin is uninstalled or reloaded

## 3.3.3 - 2024-08-26

* update documentation

## 3.3.2 - 2024-08-26

* Restore `_is_extraction_data` var, fix #136
* Update SQL views, fix #135
* Update deps

## 3.3.1 - 2024-04-03

* Change wiki link to github pages
* Update various dependencies (almost on github actions scripts)

## 3.3.0 - 2024-03-25

* Migrate wiki docs to github pages using sphinx
* Update github workflows
* Update plugin name
* Move refresh data from plugin menu to plugin settings window

## 3.2.2 - 2024-03-14

* Load plugin menu on plugin startup
* Update queries
* New pre-commit SQL formatter
* Update tester github workflow

## 3.2.1 - 2024-03-14

* Fix typing error on windows installs

## 3.2.0 - 2024-03-14

* Migrate startup tasks to a processing algorithm

## 3.1.3 - 2024-03-12

* Update metadata
* Change experimental status to false

## 3.1.2 - 2024-03-11

* fix error on empty layer check

## 3.1.1 - 2024-03-07

* update Changelog.md for `qgis-plugin-ci`
* fix translation environment


## 3.1.0 - 2024-02-14

* test de changelog


## 3.0.0 - 2024-02-13

### Added

Nothing

### Changed

- Code refactoring, plugin is now using a QgsProcessing generic class, shared with all algorithms.
- Repository architecture is now based on [QGIS Plugins templater](https://oslandia.gitlab.io/qgis/template-qgis-plugin/).

### Fixed

- [pb avec clause where sur les groupes taxo (#109)](https://github.com/lpoaura/PluginQGis-LPOData/issues/109)
- [export xls impossible (#108)](https://github.com/lpoaura/PluginQGis-LPOData/issues/108)
- [[carte synthèse par espèce (#92)] bug ordre](https://github.com/lpoaura/PluginQGis-LPOData/issues/92)
- [code atlas dans extraction données (#91)](https://github.com/lpoaura/PluginQGis-LPOData/issues/91)
- [classement sp / groupe ordre systématique (#90)](https://github.com/lpoaura/PluginQGis-LPOData/issues/90)
- [exclusion données is_valid ? (#88)](https://github.com/lpoaura/PluginQGis-LPOData/issues/90)
