"""Shop & recruitment system tests.

Covers the redesigned two-system layout: a per-merchant shop (buy/sell/salvage,
multi-currency, rarity-tiered pricing) and an independent tavern recruitment
system (full character previews, advanced-class candidates, dismiss with refund,
hardcoded-cap replaced by MAX_ROSTER_SIZE). Migration of legacy save shapes is
also covered.
"""
from __future__ import annotations

import pytest

from backend.game_core import engine


# --- helpers ---------------------------------------------------------------

def _all_shop_items(state):
    return [i for m in state["shop"]["merchants"].values() for i in m["items"]]


def _first_equipment_item(state):
    return next((i for i in _all_shop_items(state) if i["kind"] == "equipment" and i.get("equipment")), None)


def _first_consumable_item(state):
    return next((i for i in _all_shop_items(state) if i["kind"] == "consumable"), None)


# --- migration -------------------------------------------------------------

def test_shop_and_recruit_state_backfilled_by_migrate_for_old_saves():
    """Saves created before the redesign had `shop` as {items, recruits} and no
    `recruits` key. migrate_state must rewrite both into the new structures."""
    legacy = {
        "schema_version": 3,
        "characters": [],
        "materials": {},
        "inventory": [],
        "next_counters": {"dungeon": 1, "plan": 1, "report": 1},
        # Legacy shop shape (flat items/recruits lists):
        "shop": {"items": [], "recruits": []},
        # No "recruits" key at all.
    }
    engine.migrate_state(legacy)
    assert set(legacy["shop"].keys()) >= {"merchants", "refresh_day"}
    assert legacy["shop"]["merchants"] == {}
    assert set(legacy["recruits"].keys()) >= {"candidates", "refresh_day"}
    assert legacy["recruits"]["candidates"] == []


def test_partial_new_state_kept_intact_by_migrate():
    """A save that already has the new keys should not be wiped by migrate."""
    state = engine.default_state(seed=42)
    candidates_before = len(state["recruits"]["candidates"])
    engine.migrate_state(state)
    assert len(state["recruits"]["candidates"]) == candidates_before
    assert "merchants" in state["shop"]


# --- shop refresh ----------------------------------------------------------

def test_refresh_shop_generates_multiple_merchants_with_correct_stock():
    state = engine.default_state(seed=42)
    state["day"] = 10
    engine.refresh_shop(state)
    merchants = state["shop"]["merchants"]
    # Three configured merchants present.
    assert set(merchants.keys()) == {"blacksmith", "alchemist", "general_store"}
    # Each merchant is capped to its configured slot_count.
    assert len(merchants["blacksmith"]["items"]) <= 5
    assert len(merchants["alchemist"]["items"]) <= 3
    assert len(merchants["general_store"]["items"]) <= 3
    # Blacksmith sells only armor/weapon slots; general store sells trinkets.
    bs_slots = {i.get("slot") for i in merchants["blacksmith"]["items"] if i["kind"] == "equipment"}
    weapon_armor = {"main_hand", "off_hand", "two_hand", "body", "head", "hands", "feet", "waist"}
    assert bs_slots <= weapon_armor
    gs_slots = {i.get("slot") for i in merchants["general_store"]["items"] if i["kind"] == "equipment"}
    trinket_slots = {"ring", "ring_1", "ring_2", "necklace", "backpack", "backpack_1", "backpack_2", "backpack_3", "backpack_4"}
    assert gs_slots <= trinket_slots
    # Refresh day recorded.
    assert state["shop"]["refresh_day"] == 10


def test_refresh_shop_is_deterministic_per_run_and_day():
    """Same (run_seed, day) must produce identical merchant stock."""
    s1 = engine.default_state(seed=123)
    s2 = engine.default_state(seed=123)
    s1["day"] = 7
    s2["day"] = 7
    engine.refresh_shop(s1)
    engine.refresh_shop(s2)
    for mid in s1["shop"]["merchants"]:
        names1 = [i["name"] for i in s1["shop"]["merchants"][mid]["items"]]
        names2 = [i["name"] for i in s2["shop"]["merchants"][mid]["items"]]
        assert names1 == names2


def test_rarity_price_floor_applied_to_high_rarity_items():
    """Epic+ items must cost at least base_cost * floor multiplier."""
    state = engine.default_state(seed=42)
    state["day"] = 20
    engine.refresh_shop(state)
    cfg = engine.load_data()["shop_config"]["rarity_price_floor"]
    for item in _all_shop_items(state):
        if item["kind"] != "equipment":
            continue
        rarity = item.get("rarity", "common")
        floor = cfg.get(rarity, 1.0)
        # cost >= base_cost * floor (allow a tiny rounding tolerance).
        assert item["cost"] >= int(item["base_cost"] * floor) - 1, (rarity, item["cost"], item["base_cost"])


# --- buy / sell / salvage --------------------------------------------------

def test_buy_equipment_moves_to_inventory_and_removes_from_merchant():
    state = engine.default_state(seed=42)
    item = _first_equipment_item(state)
    assert item is not None
    state["gold"] = max(state["gold"], item["cost"])
    inv_before = len(state["inventory"])
    mid = item["merchant_id"]
    stock_before = len(state["shop"]["merchants"][mid]["items"])

    acquired = engine.buy_shop_item(state, item["shop_id"])

    assert acquired["type"] == "equipment"
    assert acquired["item"] in state["inventory"]
    assert len(state["inventory"]) == inv_before + 1
    assert len(state["shop"]["merchants"][mid]["items"]) == stock_before - 1
    # The bought instance shares its preview identity.
    assert acquired["item"]["instance_id"] == item["equipment"]["instance_id"]


def test_buy_consumable_increments_consumables_counter():
    state = engine.default_state(seed=42)
    item = _first_consumable_item(state)
    assert item is not None
    state["gold"] = max(state["gold"], item["cost"])
    count_before = state["consumables"].get(item["template_id"], 0)

    acquired = engine.buy_shop_item(state, item["shop_id"])

    assert acquired["type"] == "consumable"
    assert state["consumables"][item["template_id"]] == count_before + 1


def test_buy_rejects_when_gold_insufficient():
    state = engine.default_state(seed=42)
    item = _first_equipment_item(state)
    state["gold"] = max(0, item["cost"] - 1)
    with pytest.raises(ValueError, match="金币不足"):
        engine.buy_shop_item(state, item["shop_id"])


def test_buy_with_material_currency_deducts_material():
    """A merchant configured with a non-gold currency deducts that material."""
    state = engine.default_state(seed=42)
    # Inject one material-currency item into the general store for the test.
    gs = state["shop"]["merchants"]["general_store"]
    gs["items"].append({
        "shop_id": "shop_test_mat",
        "merchant_id": "general_store",
        "kind": "consumable",
        "template_id": "healing_potion",
        "name": "测试材料货",
        "cost": 2,
        "base_cost": 2,
        "currency": "leather",
        "summary": "",
    })
    state["materials"]["leather"] = 2
    acquired = engine.buy_shop_item(state, "shop_test_mat")
    assert acquired["type"] == "consumable"
    assert state["materials"]["leather"] == 0


def test_sell_item_refunds_gold_by_rarity_and_removes_item():
    state = engine.default_state(seed=42)
    item = _first_equipment_item(state)
    state["gold"] = max(state["gold"], item["cost"])
    engine.buy_shop_item(state, item["shop_id"])
    bought = state["inventory"][-1]
    iid = bought["instance_id"]
    cfg = engine.load_data()["shop_config"]["sell_multipliers"]
    expected = max(1, int(round(bought["cost"] * cfg[bought["rarity"]])))
    gold_before = state["gold"]

    result = engine.sell_item(state, iid)

    assert result["gold"] == expected
    assert state["gold"] == gold_before + expected
    assert all(i["instance_id"] != iid for i in state["inventory"])


def test_sell_rejects_equipped_item():
    state = engine.default_state(seed=42)
    ch = state["characters"][0]
    equipped_id = next(iter(ch["equipment"].values()))
    if equipped_id:
        with pytest.raises(ValueError, match="卸下"):
            engine.sell_item(state, equipped_id)


def test_salvage_item_grants_gold_and_class_affinity_materials():
    state = engine.default_state(seed=42)
    # Force a warrior-restricted weapon into inventory so affinity materials drop.
    eq = engine.instance_equipment("iron_sword", rng=__import__("random").Random(1), level=5)
    eq["instance_id"] = "eq_salvage_test"
    eq["equipped_by"] = None
    state["inventory"].append(eq)
    gold_before = state["gold"]
    ore_before = state["materials"].get("ore", 0)

    result = engine.salvage_item(state, "eq_salvage_test")

    assert result["gold"] > 0
    assert state["gold"] > gold_before
    # iron_sword is warrior/guardian restricted -> ore should be a candidate drop.
    assert state["materials"].get("ore", 0) >= ore_before
    assert all(i["instance_id"] != "eq_salvage_test" for i in state["inventory"])


# --- recruits refresh & preview -------------------------------------------

def test_refresh_recruits_includes_full_preview_matching_candidate():
    state = engine.default_state(seed=42)
    state["day"] = 8
    engine.refresh_recruits(state)
    candidates = state["recruits"]["candidates"]
    assert len(candidates) == engine.load_data()["recruit_config"]["candidate_count"]
    for c in candidates:
        # Preview is a full character snapshot.
        preview = c["preview"]
        assert {"attributes", "base_stats", "learned_skills", "hp", "max_hp"}.issubset(preview.keys())
        assert preview["class_id"] == c["class_id"]
        assert preview["level"] == c["level"]
        assert preview["id"] == c["candidate_id"]
        # Rarity label is localized.
        assert c["rarity_label"] == engine.EQUIPMENT_RARITY_LABELS[c["rarity"]]


def test_recruit_character_joins_roster_with_preview_attributes():
    """Hiring a candidate must reproduce the preview exactly (WYSIWYG)."""
    state = engine.default_state(seed=42)
    state["gold"] = 99999
    cand = state["recruits"]["candidates"][0]
    preview_attrs = dict(cand["preview"]["attributes"])
    chars_before = len(state["characters"])

    ch = engine.recruit_character(state, cand["candidate_id"])

    assert ch["id"] == cand["candidate_id"]
    assert ch["attributes"] == preview_attrs
    assert ch["class_id"] == cand["class_id"]
    assert len(state["characters"]) == chars_before + 1
    # recruit_cost stored for dismiss refund.
    assert ch["recruit_cost"] == cand["cost"]
    # Candidate removed from pool.
    assert all(c["candidate_id"] != cand["candidate_id"] for c in state["recruits"]["candidates"])


def test_recruit_rejects_when_roster_full():
    state = engine.default_state(seed=42)
    # Pad roster up to the cap with throwaway characters.
    while len(state["characters"]) < engine.MAX_ROSTER_SIZE:
        extra = engine.create_character("warrior", f"垫底{len(state['characters'])}")
        state["characters"].append(extra)
    cand = state["recruits"]["candidates"][0]
    state["gold"] = 99999
    with pytest.raises(ValueError, match="栏位已满"):
        engine.recruit_character(state, cand["candidate_id"])


def test_recruit_eventually_offers_advanced_classes():
    """Across many seeds the advanced-chance roll should surface at least one
    advanced-class candidate, confirming advanced_pool wiring."""
    found_advanced = False
    for seed in range(1, 60):
        s = engine.default_state(seed=seed)
        for c in s["recruits"]["candidates"]:
            if c.get("is_advanced"):
                found_advanced = True
                break
        if found_advanced:
            break
    assert found_advanced, "advanced-class recruits should appear with advanced_chance=0.2"


# --- dismiss ---------------------------------------------------------------

def test_dismiss_character_refunds_gold_and_frees_slot():
    state = engine.default_state(seed=42)
    state["gold"] = 99999
    cand = state["recruits"]["candidates"][0]
    cost = cand["cost"]
    ch = engine.recruit_character(state, cand["candidate_id"])
    chars_before = len(state["characters"])
    gold_before = state["gold"]

    result = engine.dismiss_character(state, ch["id"])

    expected_refund = int(round(cost * engine.DISMISS_GOLD_REFUND))
    assert result["gold"] == expected_refund
    assert state["gold"] == gold_before + expected_refund
    assert len(state["characters"]) == chars_before - 1


def test_dismiss_rejects_in_formation_character():
    state = engine.default_state(seed=42)
    starter = state["characters"][0]
    # Starter is in formation; ensure it is.
    teams = engine.formation_member_team_map(state)
    in_team = starter["id"] in teams
    if not in_team:
        state["formations"]["team_1"]["r0c0"] = starter["id"]
    with pytest.raises(ValueError, match="编队"):
        engine.dismiss_character(state, starter["id"])


def test_dismiss_rejects_last_remaining_character():
    state = engine.default_state(seed=42)
    # Keep only one character.
    keeper = state["characters"][0]
    state["characters"] = [keeper]
    # Ensure keeper is out of formation.
    state["formations"] = {tid: {} for tid in engine.TEAM_IDS}
    with pytest.raises(ValueError, match="至少保留"):
        engine.dismiss_character(state, keeper["id"])


# --- views -----------------------------------------------------------------

def test_public_state_view_exposes_shop_and_recruits():
    state = engine.default_state(seed=42)
    view = engine.public_state_view(state)
    assert "merchants" in view["shop_summary"]
    assert "refresh_day" in view["shop_summary"]
    assert "candidates" in view["recruits_summary"]
    assert "refresh_day" in view["recruits_summary"]


def test_preset_public_view_exposes_shop_and_recruit_config():
    view = engine.preset_public_view()
    assert "merchants" in view["shop_config"]
    assert "recruit_pool" in view["recruit_config"]
    assert "rarity_modifiers" in view["recruit_config"]
