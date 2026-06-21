from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

SAVE_DIR = Path(__file__).resolve().parents[2] / "saves"
SAVE_PATH = SAVE_DIR / "save_001.json"
MANUAL_SAVE_SLOTS = tuple(f"slot_{i}" for i in range(1, 6))
SAVE_SLOT_LABELS = {"auto": "自动存档"} | {slot: f"手动存档 {slot.split('_')[-1]}" for slot in MANUAL_SAVE_SLOTS}


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    target = path or SAVE_PATH
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(path: Path | None = None) -> dict[str, Any] | None:
    target = path or SAVE_PATH
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding="utf-8"))


def delete_save(path: Path | None = None) -> None:
    target = path or SAVE_PATH
    if target.exists():
        target.unlink()


def save_slot_path(slot_id: str) -> Path:
    """Resolve a known save slot id to a file path.

    The slot id is intentionally allow-listed so API callers cannot use a
    crafted path to read/write arbitrary files.
    """
    if slot_id == "auto":
        return SAVE_PATH
    if slot_id not in MANUAL_SAVE_SLOTS:
        raise ValueError("存档槽不存在")
    return SAVE_DIR / f"{slot_id}.json"


def list_save_slots() -> list[dict[str, Any]]:
    return [save_slot_summary("auto")] + [save_slot_summary(slot_id) for slot_id in MANUAL_SAVE_SLOTS]


def save_slot_summary(slot_id: str) -> dict[str, Any]:
    path = save_slot_path(slot_id)
    row: dict[str, Any] = {
        "id": slot_id,
        "label": SAVE_SLOT_LABELS.get(slot_id, slot_id),
        "kind": "auto" if slot_id == "auto" else "manual",
        "exists": path.exists(),
    }
    if not path.exists():
        return row
    row["modified_at"] = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    try:
        data = load_state(path) or {}
    except Exception as exc:  # keep slot list usable even if one file is corrupt
        row["corrupt"] = True
        row["error"] = str(exc)
        return row
    row.update({
        "day": data.get("day"),
        "max_day": data.get("max_day"),
        "run_seed": data.get("run_seed"),
        "gold": data.get("gold"),
        "victory": bool(data.get("victory", False)),
        "defeat": bool(data.get("defeat", False)),
        "party_count": len(data.get("characters", []) or []),
        "report_count": len(data.get("reports", []) or []),
    })
    return row


def save_state_to_slot(state: dict[str, Any], slot_id: str) -> dict[str, Any]:
    save_state(state, save_slot_path(slot_id))
    return save_slot_summary(slot_id)


def load_state_from_slot(slot_id: str) -> dict[str, Any] | None:
    return load_state(save_slot_path(slot_id))


def delete_save_slot(slot_id: str) -> None:
    delete_save(save_slot_path(slot_id))
