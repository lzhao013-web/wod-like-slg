"""Consumable battle system tests.

The consumable system lets players buy potions/antidotes and configure per-
character auto-use triggers. These tests cover: data-driven effects, the
tactic-slot plumbing (defaults/normalize/clean/migration), and battle
consumption with shared-pool deduction written back to state.
"""
from __future__ import annotations

import pytest

from backend.game_core import engine


# --- helpers ---------------------------------------------------------------

def _challenge_first_dungeon(state, team_id: str = "team_1") -> dict:
    """Run a single challenge against the first available dungeon and return the report."""
    view = engine.dungeon_list_view(state)
    assert view, "no dungeons available"
    dungeon = engine.get_dungeon(state, view[0]["dungeon_id"])
    return engine.resolve_challenge(state, dungeon, 0, team_id)


def _set_member_tactic(state, class_id: str, consumable_priority: list) -> None:
    """Force a consumable_priority config on the first character of a class."""
    ch = next(c for c in state["characters"] if c["class_id"] == class_id)
    engine.normalize_character(ch)
    ch["tactics"]["consumable_priority"] = engine.clean_consumable_priority(consumable_priority)


# --- data-driven effects ---------------------------------------------------

def test_consumable_effects_loaded_from_shop_data():
    data = engine.load_data()
    assert "healing_potion" in data["consumable_by_id"]
    assert "antidote" in data["consumable_by_id"]
    heal = engine.consumable_effect("healing_potion")
    assert heal and "heal" in heal and int(heal["heal"]) > 0
    cleanse = engine.consumable_effect("antidote")
    assert cleanse and "cleanse" in cleanse and "poison" in cleanse["cleanse"]


def test_unknown_consumable_has_no_effect():
    assert engine.consumable_effect("does_not_exist") is None
    assert engine.consumable_template("does_not_exist") is None
    assert engine.consumable_name("does_not_exist") == "does_not_exist"


# --- tactic slot plumbing --------------------------------------------------

def test_default_tactics_carry_consumable_priority():
    state = engine.default_state(seed=1)
    for ch in state["characters"]:
        engine.normalize_character(ch)
        assert "consumable_priority" in ch["tactics"]
        assert isinstance(ch["tactics"]["consumable_priority"], list)


def test_frontline_defaults_to_healing_potion():
    state = engine.default_state(seed=1)
    warrior = next(c for c in state["characters"] if c["base_class_id"] == "warrior")
    engine.normalize_character(warrior)
    pri = warrior["tactics"]["consumable_priority"]
    assert pri and pri[0]["consumable_id"] == "healing_potion"
    assert pri[0]["trigger"] == "self_hp_below_30"


def test_clean_consumable_priority_drops_unknown_entries():
    raw = [
        {"consumable_id": "healing_potion", "trigger": "self_hp_below_30"},
        {"consumable_id": "phantom_potion", "trigger": "self_hp_below_30"},  # unknown id
        {"consumable_id": "antidote", "trigger": "never_happens"},           # unknown trigger
        {"consumable_id": "healing_potion", "trigger": "self_hp_below_50"},  # duplicate id
    ]
    cleaned = engine.clean_consumable_priority(raw)
    ids = [e["consumable_id"] for e in cleaned]
    assert ids == ["healing_potion"]  # dedup keeps the first; unknowns dropped


def test_update_tactics_persists_consumable_priority():
    state = engine.default_state(seed=2)
    ch = state["characters"][0]
    engine.update_tactics(state, {"characters": [{
        "character_id": ch["id"],
        "consumable_priority": [{"consumable_id": "antidote", "trigger": "self_cursed"}],
    }]})
    assert ch["tactics"]["consumable_priority"] == [{"consumable_id": "antidote", "trigger": "self_cursed"}]
    # The serialized tactic row also surfaces it.
    row = engine.tactic_row_from_character(ch)
    assert row["consumable_priority"] == [{"consumable_id": "antidote", "trigger": "self_cursed"}]


def test_party_summary_exposes_consumable_options():
    state = engine.default_state(seed=3)
    summary = engine.party_summary(state)
    assert "consumable_trigger_options" in summary
    assert "self_hp_below_30" in summary["consumable_trigger_options"]
    assert isinstance(summary["consumable_options"], list)
    assert any(o["id"] == "healing_potion" for o in summary["consumable_options"])
    assert summary["consumables"] == state["consumables"]


# --- migration -------------------------------------------------------------

def test_old_save_without_consumables_pool_is_backfilled():
    state = engine.default_state(seed=4)
    # Simulate a pre-consumable save: drop the pool entirely.
    state.pop("consumables", None)
    engine.migrate_state(state)
    assert isinstance(state["consumables"], dict)
    assert state["consumables"]["healing_potion"] > 0


def test_old_character_tactics_get_consumable_priority():
    state = engine.default_state(seed=5)
    ch = state["characters"][0]
    # Strip the key to mimic a legacy character save.
    ch["tactics"].pop("consumable_priority", None)
    engine.normalize_character(ch)
    assert "consumable_priority" in ch["tactics"]


# --- battle consumption ----------------------------------------------------

def test_antidote_consumed_when_poisoned():
    state = engine.default_state(seed=11)
    state["consumables"]["antidote"] = 5
    cleric = next(c for c in state["characters"] if c["class_id"] == "cleric")
    # Poison the cleric so its default self_poisoned antidote trigger fires.
    cleric["status_effects"] = [{"type": "poison", "duration": 5, "potency": 4}]
    before = state["consumables"]["antidote"]
    report = _challenge_first_dungeon(state)
    assert report["consumables_used"].get("antidote", 0) >= 1
    assert report["losses"]["consumables"].get("解毒剂")
    assert state["consumables"]["antidote"] == before - report["consumables_used"]["antidote"]
    # A consumable event should appear somewhere in the turn logs.
    assert any("解毒剂" in line for line in report["turn_logs"])


def test_healing_potion_consumed_on_low_hp():
    state = engine.default_state(seed=12)
    state["consumables"]["healing_potion"] = 10
    # Crank the trigger high (50%) on every party member so at least one fires
    # before native healing tops everyone off.
    for ch in state["characters"]:
        engine.normalize_character(ch)
        ch["tactics"]["consumable_priority"] = [
            {"consumable_id": "healing_potion", "trigger": "self_hp_below_50"}
        ]
    # Drop everyone's HP well under 50% so the trigger is live on round 1.
    for ch in state["characters"]:
        ch["hp"] = max(1, int(ch["max_hp"] * 0.2))
    before = state["consumables"]["healing_potion"]
    report = _challenge_first_dungeon(state)
    used = report["consumables_used"].get("healing_potion", 0)
    assert used >= 1
    assert report["losses"]["consumables"].get("治疗药水")
    assert state["consumables"]["healing_potion"] == before - used


def test_shared_pool_does_not_overspend_when_empty():
    state = engine.default_state(seed=13)
    # Only one potion in stock, but several members are configured to want it.
    state["consumables"]["healing_potion"] = 1
    for ch in state["characters"]:
        engine.normalize_character(ch)
        ch["tactics"]["consumable_priority"] = [
            {"consumable_id": "healing_potion", "trigger": "self_hp_below_50"}
        ]
        ch["hp"] = max(1, int(ch["max_hp"] * 0.2))
    report = _challenge_first_dungeon(state)
    assert report["consumables_used"].get("healing_potion", 0) >= 1
    # Pool cannot go negative, and at most the starting charge was spent here.
    assert state["consumables"]["healing_potion"] == 0


def test_no_trigger_means_no_consumption():
    state = engine.default_state(seed=14)
    state["consumables"]["healing_potion"] = 3
    state["consumables"]["antidote"] = 3
    # Clear every consumable trigger so nothing should auto-fire.
    for ch in state["characters"]:
        engine.normalize_character(ch)
        ch["tactics"]["consumable_priority"] = []
    report = _challenge_first_dungeon(state)
    assert report["consumables_used"] == {}
    assert state["consumables"]["healing_potion"] == 3
    assert state["consumables"]["antidote"] == 3
