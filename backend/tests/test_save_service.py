from __future__ import annotations

import pytest

from backend.app.services import save_service
from backend.game_core import engine


def test_manual_save_slots_are_allowlisted_and_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(save_service, "SAVE_DIR", tmp_path)
    monkeypatch.setattr(save_service, "SAVE_PATH", tmp_path / "save_001.json")
    state = engine.default_state(seed=20260621)

    slot = save_service.save_state_to_slot(state, "slot_1")
    assert slot["id"] == "slot_1"
    assert slot["exists"] is True
    assert slot["day"] == 1
    assert slot["run_seed"] == 20260621

    loaded = save_service.load_state_from_slot("slot_1")
    assert loaded is not None
    assert loaded["run_seed"] == 20260621

    slots = save_service.list_save_slots()
    assert [row["id"] for row in slots[:2]] == ["auto", "slot_1"]
    assert next(row for row in slots if row["id"] == "slot_1")["exists"] is True

    save_service.delete_save_slot("slot_1")
    assert save_service.save_slot_summary("slot_1")["exists"] is False

    with pytest.raises(ValueError):
        save_service.save_slot_path("../escape")
