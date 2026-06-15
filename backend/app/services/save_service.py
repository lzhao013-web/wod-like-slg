from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SAVE_DIR = Path(__file__).resolve().parents[2] / "saves"
SAVE_PATH = SAVE_DIR / "save_001.json"


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
