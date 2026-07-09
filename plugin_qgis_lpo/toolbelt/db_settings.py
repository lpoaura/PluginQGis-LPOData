#! python3  # noqa: E265

"""
Typed access to database-backed plugin settings.
"""

import ast
import copy
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qgis.core import QgsSettings


TAXONOMY_SETTINGS = (
    "groupe_taxo",
    "regne",
    "phylum",
    "classe",
    "ordre",
    "famille",
    "group1_inpn",
    "group2_inpn",
)

LIST_SETTINGS = (
    *TAXONOMY_SETTINGS,
    "source_data",
    "export_views",
)

STATUS_COLUMNS_SETTING = "status_columns"
EXCLUDE_EXPORT_SINP_SETTING = "exclude_export_sinp"

DB_SETTINGS_DEFAULTS = {
    **{key: [] for key in LIST_SETTINGS},
    STATUS_COLUMNS_SETTING: {},
    EXCLUDE_EXPORT_SINP_SETTING: False,
}


@dataclass(frozen=True)
class ExportView:
    """Export view setting as displayed in Processing forms."""

    label: str
    relation: str


@dataclass(frozen=True)
class DbSettings:
    """Database-backed settings normalized from QGIS settings."""

    groupe_taxo: List[str]
    regne: List[str]
    phylum: List[str]
    classe: List[str]
    ordre: List[str]
    famille: List[str]
    group1_inpn: List[str]
    group2_inpn: List[str]
    source_data: List[str]
    export_views: List[ExportView]
    status_columns: Dict[str, str]
    exclude_export_sinp: bool

    @classmethod
    def from_qsettings(cls, settings: Optional[QgsSettings] = None) -> "DbSettings":
        """Build typed database settings from QGIS settings."""
        settings = settings or QgsSettings()
        return cls(
            groupe_taxo=_get_list(settings, "groupe_taxo"),
            regne=_get_list(settings, "regne"),
            phylum=_get_list(settings, "phylum"),
            classe=_get_list(settings, "classe"),
            ordre=_get_list(settings, "ordre"),
            famille=_get_list(settings, "famille"),
            group1_inpn=_get_list(settings, "group1_inpn"),
            group2_inpn=_get_list(settings, "group2_inpn"),
            source_data=_get_list(settings, "source_data"),
            export_views=_get_export_views(settings),
            status_columns=_get_status_columns(settings),
            exclude_export_sinp=_get_bool(settings, "exclude_export_sinp"),
        )


def _get_list(settings: QgsSettings, key: str) -> List[str]:
    """Read a setting as a list of strings."""
    value = _get_value(settings, key, [])
    return _as_string_list(value)


def _get_export_views(settings: QgsSettings) -> List[ExportView]:
    """Read export view settings from JSON strings or dictionaries."""
    export_views = []
    for item in _as_list(_get_value(settings, "export_views", [])):
        data = _parse_mapping(item)
        if not data:
            continue

        label = data.get("label")
        relation = data.get("relation")
        if label and relation:
            export_views.append(ExportView(label=str(label), relation=str(relation)))

    return export_views


def _get_status_columns(settings: QgsSettings) -> Dict[str, str]:
    """Read status columns as a string-to-string mapping."""
    value = _get_value(settings, "status_columns", {})
    data = _parse_mapping(value)
    if not data:
        return {}

    return {
        str(key): str(value)
        for key, value in data.items()
        if key is not None and value is not None
    }


def _get_bool(settings: QgsSettings, key: str, default: bool = False) -> bool:
    """Read a setting as a boolean."""
    value = _get_value(settings, key, default)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "t", "yes", "y"}

    return bool(value)


def _get_value(settings: QgsSettings, key: str, default: Any) -> Any:
    """Read a raw setting while tolerating type conversion differences."""
    try:
        return settings.value(key, defaultValue=copy.deepcopy(default))
    except TypeError:
        return settings.value(key, copy.deepcopy(default))


def _as_list(value: Any) -> List[Any]:
    """Normalize common QSettings containers to a Python list."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            return []

        parsed_value = _parse_literal(stripped_value)
        if isinstance(parsed_value, (list, tuple, set)):
            return list(parsed_value)

        return [value]

    return [value]


def _as_string_list(value: Any) -> List[str]:
    """Normalize a setting to a list of non-empty strings."""
    return [
        str(item)
        for item in _as_list(value)
        if item is not None and str(item).strip() != ""
    ]


def _parse_mapping(value: Any) -> Optional[Dict[Any, Any]]:
    """Parse a JSON/Python mapping encoded in a setting."""
    if isinstance(value, dict):
        return value

    if not isinstance(value, str):
        return None

    parsed_value = _parse_literal(value)
    if isinstance(parsed_value, dict):
        return parsed_value

    if isinstance(parsed_value, str):
        parsed_value = _parse_literal(parsed_value)
        if isinstance(parsed_value, dict):
            return parsed_value

    return None


def _parse_literal(value: str) -> Any:
    """Parse JSON first, then Python literals for legacy setting values."""
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        pass

    try:
        return ast.literal_eval(value)
    except (TypeError, ValueError, SyntaxError):
        return value
