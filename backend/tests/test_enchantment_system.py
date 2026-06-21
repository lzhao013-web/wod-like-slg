"""Equipment enchantment / reroll / ascension system tests.

Covers the material-consuming equipment upgrade loop (enhancement/强化 was
removed; this file is enchant-only):
  * enchant: adds a random compatible affix line, special items excluded,
    capped at MAX_ENCHANT_SLOTS.
  * reroll: re-rolls an existing enchant line (strips its stats, draws a new
    affix that is never the same id); same cost as a fresh enchant.
  * ascension: a special (fixed-rarity) item + a recipe -> a stronger item,
    consuming the recipe's materials; keeps the same instance_id.
Data flow: enchant/reroll bonuses land in item.stats/resistances so
effective_stats picks them up; normalize backfills enchants/enchant_reroll_count.
"""
from __future__ import annotations

import pytest

from backend.game_core import engine


# --- helpers ---------------------------------------------------------------

def _fresh_item(template_id: str = "iron_sword", instance_id: str = "eq_test_1", rarity: str = "rare"):
    """An unequipped, deterministic instance in a clean inventory."""
    state = engine.default_state(seed=42)
    item = engine.instance_equipment(template_id, instance_id, rarity=rarity)
    state["inventory"].append(item)
    return state, item


def _set_materials(state, **amounts):
    mats = state.setdefault("materials", {})
    for key, amount in amounts.items():
        mats[key] = int(amount)


# --- migration / normalize -------------------------------------------------

def test_normalize_backfills_enchant_fields_on_old_items():
    """An item dict lacking the new fields gets defaults via normalize."""
    state = engine.default_state(seed=42)
    legacy_item = {
        "instance_id": "eq_old",
        "template_id": "iron_sword",
        "name": "铁剑",
        "slot": "main_hand",
        "rarity": "common",
        "stats": {"attack": 5},
        "resistances": {},
        "special_effects": [],
        "durability": 36,
        "max_durability": 36,
    }
    state["inventory"].append(legacy_item)
    engine.migrate_state(state)
    assert legacy_item["enchants"] == []
    assert legacy_item["enchant_reroll_count"] == 0


# --- enchant ---------------------------------------------------------------

def test_enchant_adds_affix_and_deducts_reagents():
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="rare")
    _set_materials(state, arcane_dust=10, venom_sac=10)
    affix_ids_before = {a["id"] for a in item.get("affixes", [])}

    result = engine.enchant_equipment(state, item["instance_id"])

    assert state["materials"]["arcane_dust"] == 10 - 3
    assert state["materials"]["venom_sac"] == 10 - 1
    assert len(item["enchants"]) == 1
    assert result["affix"]["id"] == item["enchants"][0]["id"]
    assert item["enchants"][0]["id"] not in affix_ids_before


def test_enchant_sums_bonus_into_stats_consistent_with_affix():
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="rare")
    _set_materials(state, arcane_dust=10, venom_sac=10)
    stats_before = dict(item["stats"])
    engine.enchant_equipment(state, item["instance_id"])
    added = item["enchants"][0].get("stats", {})
    for k, v in added.items():
        assert item["stats"].get(k, 0) == stats_before.get(k, 0) + int(v)


def test_enchant_caps_at_max_slots():
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="rare")
    _set_materials(state, arcane_dust=100, venom_sac=100)
    for _ in range(engine.MAX_ENCHANT_SLOTS):
        engine.enchant_equipment(state, item["instance_id"])
    assert len(item["enchants"]) == engine.MAX_ENCHANT_SLOTS
    with pytest.raises(ValueError, match="已满"):
        engine.enchant_equipment(state, item["instance_id"])


def test_enchant_blocked_on_special_equipment():
    """poison_ring is a fixed-rarity special item and cannot be enchanted."""
    state, item = _fresh_item("poison_ring", "eq_special_1", rarity="rare")
    assert item["item_kind"] == "special"
    _set_materials(state, arcane_dust=10, venom_sac=10)
    with pytest.raises(ValueError, match="特殊装备"):
        engine.enchant_equipment(state, item["instance_id"])


def test_enchant_affix_respects_rarity_floor():
    """Every default affix needs at least uncommon, so a common item has no valid
    candidates; a rare item draws from affixes whose rarity floor it meets."""
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="common")
    _set_materials(state, arcane_dust=10, venom_sac=10)
    with pytest.raises(ValueError, match="没有可附加的词缀"):
        engine.enchant_equipment(state, item["instance_id"])
    assert state["materials"]["arcane_dust"] == 10  # nothing spent

    state2, item2 = _fresh_item("iron_sword", "eq_test_2", rarity="rare")
    _set_materials(state2, arcane_dust=10, venom_sac=10)
    engine.enchant_equipment(state2, item2["instance_id"])
    chosen = item2["enchants"][0]
    valid_ids = [
        a["id"] for a in engine.equipment_affix_pool()
        if engine.rarity_at_least("rare", a.get("rarity_min", "uncommon"))
    ]
    assert chosen["id"] in valid_ids


# --- reroll ----------------------------------------------------------------

def test_reroll_replaces_enchant_with_a_different_affix():
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="rare")
    _set_materials(state, arcane_dust=100, venom_sac=100)
    engine.enchant_equipment(state, item["instance_id"])
    old_id = item["enchants"][0]["id"]
    old_stats_snapshot = dict(item["enchants"][0].get("stats", {}))

    result = engine.reroll_enchant(state, item["instance_id"], 0)

    assert len(item["enchants"]) == 1  # still one line, replaced in place
    assert item["enchants"][0]["id"] != old_id
    assert result["affix"]["id"] == item["enchants"][0]["id"]
    # Slot count unchanged, but reroll counter advanced.
    assert item["enchant_reroll_count"] == 1
    # Cost deducted.
    assert state["materials"]["arcane_dust"] == 100 - 3 - 3


def test_reroll_strips_old_bonus_before_applying_new_one():
    """The replaced affix's stat contribution must be removed, not stacked."""
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="rare")
    _set_materials(state, arcane_dust=100, venom_sac=100)
    engine.enchant_equipment(state, item["instance_id"])
    stats_after_enchant = dict(item["stats"])
    old_affix_stats = dict(item["enchants"][0].get("stats", {}))

    engine.reroll_enchant(state, item["instance_id"], 0)

    new_affix_stats = dict(item["enchants"][0].get("stats", {}))
    for k in set(old_affix_stats) | set(new_affix_stats):
        expected = stats_after_enchant.get(k, 0) - old_affix_stats.get(k, 0) + new_affix_stats.get(k, 0)
        assert item["stats"].get(k, 0) == expected, f"stat {k} not correctly swapped"


def test_reroll_repeated_times_yields_varied_results():
    """With the reroll counter in the seed, repeated rerolls shouldn't loop on
    one affix (the counter changes the draw)."""
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="rare")
    _set_materials(state, arcane_dust=1000, venom_sac=1000)
    engine.enchant_equipment(state, item["instance_id"])
    seen = {item["enchants"][0]["id"]}
    for _ in range(4):
        engine.reroll_enchant(state, item["instance_id"], 0)
        seen.add(item["enchants"][0]["id"])
    assert len(seen) >= 2  # at least two distinct affixes over 5 draws


def test_reroll_rejects_invalid_index():
    state, item = _fresh_item("iron_sword", "eq_test_1", rarity="rare")
    _set_materials(state, arcane_dust=100, venom_sac=100)
    with pytest.raises(ValueError, match="不存在"):
        engine.reroll_enchant(state, item["instance_id"], 0)  # no enchants yet


# --- ascension -------------------------------------------------------------

def _fresh_special(template_id: str, instance_id: str = "eq_asc_1"):
    state = engine.default_state(seed=42)
    item = engine.instance_equipment(template_id, instance_id)
    state["inventory"].append(item)
    return state, item


def test_ascend_transforms_special_into_target_consuming_materials():
    state, item = _fresh_special("poison_ring", "eq_asc_1")
    recipe = engine.ascension_recipe_for(item)
    assert recipe is not None
    assert recipe["target"] == "serpent_ring"
    _set_materials(state, arcane_dust=10, venom_sac=10)

    result = engine.ascend_equipment(state, item["instance_id"])

    assert result["type"] == "ascend"
    # Materials consumed per recipe (arcane_dust:4, venom_sac:3).
    assert state["materials"]["arcane_dust"] == 10 - 4
    assert state["materials"]["venom_sac"] == 10 - 3
    # The old item is replaced in place; the new one keeps the same instance_id.
    new_item = engine.get_item(state, "eq_asc_1")
    assert new_item is not None
    assert new_item is not item  # different object (old removed, new appended)
    assert new_item["template_id"] == "serpent_ring"
    assert new_item["item_kind"] == "special"
    # No leftover duplicate of the instance_id.
    assert sum(1 for i in state["inventory"] if i.get("instance_id") == "eq_asc_1") == 1


def test_ascend_raises_when_materials_short():
    state, item = _fresh_special("poison_ring", "eq_asc_1")
    _set_materials(state, arcane_dust=2, venom_sac=10)  # need 4 arcane_dust
    with pytest.raises(ValueError, match="奥术尘"):
        engine.ascend_equipment(state, item["instance_id"])
    # Nothing changed on failure: the source item is still poison_ring.
    assert engine.get_item(state, "eq_asc_1")["template_id"] == "poison_ring"


def test_ascend_rejects_non_special_equipment():
    state, item = _fresh_item("iron_sword", "eq_base_1", rarity="rare")
    _set_materials(state, arcane_dust=100, venom_sac=100)
    with pytest.raises(ValueError, match="无法升华"):
        engine.ascend_equipment(state, item["instance_id"])


def test_ascend_rejects_equipped_items():
    state, item = _fresh_special("poison_ring", "eq_asc_1")
    _set_materials(state, arcane_dust=100, venom_sac=100)
    item["equipped_by"] = "ch_1"
    with pytest.raises(ValueError, match="卸下"):
        engine.ascend_equipment(state, item["instance_id"])


def test_ascension_recipes_cover_all_special_sources():
    """Every fixed-rarity special item should have an ascension recipe."""
    recipes = engine.ascension_recipes()
    sources = {r["source"] for r in recipes}
    data = engine.load_data()
    specials = [e["id"] for e in data["equipment"] if e.get("item_kind") == "special" and e.get("fixed_rarity")]
    # The 6 ascension targets are also fixed-rarity specials, but they are NOT
    # sources; only the original 6 base specials need recipes.
    targets = {r["target"] for r in recipes}
    base_specials = [s for s in specials if s not in targets]
    for s in base_specials:
        assert s in sources, f"special {s} has no ascension recipe"
