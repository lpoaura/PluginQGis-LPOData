# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

<!-- ## Unreleased [{version_tag}](https://github.com/opengisch/qgis-plugin-ci/releases/tag/{version_tag}) - YYYY-MM-DD -->

## Unreleased

## 3.1.2 - 2024-03-11

* fix error on empty layer check

## 3.1.1 - 2024-03-07

* update Changelog.md for `qgis-plugin-ci`
* fix translation environment

### Changed

* Update CHANGELOG.md (`qgis-plugin-ci` fix)

## 3.1.0 - 2024-02-14

* test de changelog

### Changed

- Update database views


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
