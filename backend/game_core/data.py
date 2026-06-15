from __future__ import annotations

import copy
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PRESETS_DIR = DATA_DIR / "presets"
DEFAULT_PRESET_ID = "wod_default"
PRESET_ENV_VAR = "WOD_PRESET_ID"


def _read_json_path(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_json(name: str) -> Any:
    return _read_json_path(DATA_DIR / name)


def active_preset_id() -> str:
    """Current preset id. Override at process startup with WOD_PRESET_ID."""
    return os.getenv(PRESET_ENV_VAR, DEFAULT_PRESET_ID).strip() or DEFAULT_PRESET_ID


def list_presets() -> list[dict[str, Any]]:
    """Discover preset manifests under backend/data/presets."""
    rows: list[dict[str, Any]] = []
    if not PRESETS_DIR.exists():
        return rows
    candidates = sorted([p for p in PRESETS_DIR.iterdir() if p.is_dir()] + [p for p in PRESETS_DIR.glob("*.json") if p.is_file()])
    for path in candidates:
        manifest = path / "preset.json" if path.is_dir() else path
        if not manifest.exists():
            continue
        try:
            preset = _read_json_path(manifest)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(preset, dict):
            continue
        preset_id = str(preset.get("id") or (path.name if path.is_dir() else path.stem))
        rows.append({
            "id": preset_id,
            "name": preset.get("name", preset_id),
            "description": preset.get("description", ""),
            "path": str(manifest),
            "active": preset_id == active_preset_id(),
        })
    return rows


def _preset_path(preset_id: str) -> Path:
    direct = PRESETS_DIR / preset_id / "preset.json"
    if direct.exists():
        return direct
    flat = PRESETS_DIR / f"{preset_id}.json"
    if flat.exists():
        return flat
    raise FileNotFoundError(f"Unknown data preset: {preset_id}")


def _load_preset(preset_id: str) -> tuple[dict[str, Any], Path]:
    path = _preset_path(preset_id)
    preset = _read_json_path(path)
    if not isinstance(preset, dict):
        raise ValueError(f"Preset must be an object: {path}")
    return preset, path


def _read_preset_file(preset: dict[str, Any], preset_path: Path, key: str, fallback_name: str) -> Any:
    files = preset.get("files", {}) if isinstance(preset.get("files", {}), dict) else {}
    configured = files.get(key, fallback_name)
    path = Path(str(configured))
    if not path.is_absolute():
        path = preset_path.parent / path
    return _read_json_path(path.resolve())


@lru_cache(maxsize=4)
def load_data(preset_id: str | None = None) -> dict[str, Any]:
    """Load static balance data through a preset and expose list/id indexes."""
    preset_id = preset_id or active_preset_id()
    preset, preset_path = _load_preset(preset_id)
    classes = _read_preset_file(preset, preset_path, "classes", "classes.json")
    skills = _read_preset_file(preset, preset_path, "skills", "skills.json")
    equipment = _read_preset_file(preset, preset_path, "equipment", "equipment.json")
    enemies = _read_preset_file(preset, preset_path, "enemies", "enemies.json")
    dungeons = _read_preset_file(preset, preset_path, "dungeon_templates", "dungeon_templates.json")
    affixes = _read_preset_file(preset, preset_path, "affixes", "affixes.json")
    class_ui = preset.get("class_ui", {}) if isinstance(preset.get("class_ui", {}), dict) else {}
    skill_ai = preset.get("skill_ai", {}) if isinstance(preset.get("skill_ai", {}), dict) else {}
    return {
        "preset": copy.deepcopy(preset),
        "preset_id": preset.get("id", preset_id),
        "preset_name": preset.get("name", preset_id),
        "preset_path": str(preset_path),
        "classes": classes,
        "skills": skills,
        "equipment": equipment,
        "enemies": enemies,
        "dungeons": dungeons,
        "affixes": affixes,
        "class_by_id": {x["id"]: x for x in classes},
        "skill_by_id": {x["id"]: x for x in skills},
        "class_ui_by_id": copy.deepcopy(class_ui),
        "skill_ai_by_class_id": copy.deepcopy(skill_ai),
        "equipment_by_id": {x["id"]: x for x in equipment},
        "enemy_by_id": {x["id"]: x for x in enemies},
        "dungeon_by_id": {x["id"]: x for x in dungeons},
        "affix_by_id": {x["id"]: x for x in affixes},
    }


def template_copy(kind: str, item_id: str) -> dict[str, Any]:
    data = load_data()
    return copy.deepcopy(data[f"{kind}_by_id"][item_id])
