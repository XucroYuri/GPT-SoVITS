from dataclasses import dataclass


@dataclass(frozen=True)
class WeightSelection:
    display_value: str
    resolved_path: str


def _is_blank(value):
    return value is None or str(value).strip() == ""


def _normalize_path(value):
    return str(value or "").replace("\\", "/").strip().lstrip("./")


def _display_name_for_path(path_value, name_map, preferred_label=None):
    if _is_blank(path_value):
        return ""
    if path_value in name_map:
        return path_value

    normalized = _normalize_path(path_value)
    if preferred_label in name_map and _normalize_path(name_map[preferred_label]) == normalized:
        return preferred_label
    for label, mapped_path in name_map.items():
        if _normalize_path(mapped_path) == normalized:
            return label
    return str(path_value)


def resolve_weight_selection(env_value, stored_value, fallback_choice, default_label, name_map):
    raw_value = env_value if not _is_blank(env_value) else stored_value
    if _is_blank(raw_value):
        raw_value = default_label if default_label in name_map else fallback_choice

    display_value = _display_name_for_path(raw_value, name_map, default_label)
    resolved_path = name_map.get(display_value, raw_value)
    return WeightSelection(display_value=str(display_value), resolved_path=str(resolved_path))
