# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- ## Unreleased [{version_tag}](https://github.com/opengisch/qgis-plugin-ci/releases/tag/{version_tag}) - YYYY-MM-DD -->

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
