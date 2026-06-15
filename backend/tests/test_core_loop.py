from backend.game_core import engine


def test_new_game_has_core_loop_state():
    state = engine.default_state(seed=42)
    assert state["day"] == 1
    assert len(state["characters"]) >= 6
    assert len(state["active_dungeons"]) >= 3
    assert len(state["formation"]) <= 4


def test_scout_and_challenge_advance_day_and_generate_reports():
    state = engine.default_state(seed=123)
    dungeon_id = engine.dungeon_list_view(state)[0]["dungeon_id"]
    engine.add_plan_action(state, "scout", dungeon_id)
    engine.add_plan_action(state, "challenge", dungeon_id)
    result = engine.end_day(state)
    assert state["day"] == 2
    assert len(result["reports"]) == 2
    assert result["reports"][0]["type"] == "scout"
    assert result["reports"][1]["type"] == "challenge"
    assert result["reports"][1]["summary"]
    assert result["reports"][1]["failure_reasons"]
    assert result["reports"][1]["review_metrics"]["rounds_total"] >= 0
    assert "damage_by_type_stats" in result["reports"][1]
    assert result["reports"][1]["layer_results"][0].get("round_details") is not None


def test_formation_validation_changes_party():
    state = engine.default_state(seed=9)
    engine.update_formation(state, {"r0c1": "ch_5", "r2c1": "ch_6"}, team_id="team_2")
    assert state["formations"]["team_2"]["r0c1"] == "ch_5"


def test_initiative_skill_is_optional_tactic_selection():
    state = engine.default_state(seed=9)
    ch = state["characters"][0]
    default_stats = engine.effective_stats(state, ch)
    assert default_stats["initiative_skill"]["is_default"]
    assert default_stats["speed"] == default_stats["normal_speed"]

    initiative_sid = next(
        sid for sid in engine.active_skill_ids_for_character(ch)
        if engine.is_initiative_skill(engine.load_data()["skill_by_id"].get(sid, {}))
    )
    engine.update_tactics(state, {"characters": [{"character_id": ch["id"], "initiative_skill": initiative_sid}]})
    selected_stats = engine.effective_stats(state, ch)
    assert selected_stats["initiative_skill"]["skill_id"] == initiative_sid
    assert not selected_stats["initiative_skill"]["is_default"]

    engine.update_tactics(state, {"characters": [{"character_id": ch["id"], "initiative_skill": ""}]})
    reset_stats = engine.effective_stats(state, ch)
    assert reset_stats["initiative_skill"]["is_default"]
    assert reset_stats["speed"] == reset_stats["normal_speed"]


def test_skills_use_tree_points_instead_of_level_unlocks():
    state = engine.default_state(seed=9)
    warrior = next(ch for ch in state["characters"] if ch["class_id"] == "warrior")
    assert "cleave" not in engine.active_skill_ids_for_character(warrior)

    engine.level_up_character(warrior)
    assert warrior["skill_points"] == 1
    assert "cleave" not in engine.active_skill_ids_for_character(warrior)

    engine.learn_skill(state, warrior["id"], "cleave")
    assert warrior["skill_points"] == 0
    assert "cleave" in engine.active_skill_ids_for_character(warrior)

    try:
        engine.learn_skill(state, warrior["id"], "execute")
        assert False, "should reject missing skill points"
    except ValueError:
        pass


def test_skill_essence_upgrades_skill_levels_and_milestones():
    state = engine.default_state(seed=9)
    warrior = next(ch for ch in state["characters"] if ch["class_id"] == "warrior")
    assert state["materials"][engine.SKILL_ESSENCE_KEY] == engine.STARTING_SKILL_ESSENCE

    base = engine.upgraded_skill_for_character(warrior, "power_strike")
    assert base["power"] == 9

    engine.upgrade_skill(state, warrior["id"], "power_strike")
    assert state["materials"][engine.SKILL_ESSENCE_KEY] == engine.STARTING_SKILL_ESSENCE - 4
    upgraded = engine.upgraded_skill_for_character(warrior, "power_strike")
    assert upgraded["upgrade_level"] == 2
    assert upgraded["power"] == 11

    state["materials"][engine.SKILL_ESSENCE_KEY] += 10
    try:
        engine.upgrade_skill(state, warrior["id"], "power_strike")
        assert False, "level 3 should require a milestone choice"
    except ValueError:
        pass

    engine.upgrade_skill(state, warrior["id"], "power_strike", "force")
    milestone = engine.upgraded_skill_for_character(warrior, "power_strike")
    assert milestone["upgrade_level"] == 3
    assert milestone["power"] == 17
    summary = next(s for s in engine.skill_public_summary(warrior, state) if s["id"] == "power_strike")
    assert summary["skill_selected_upgrade_choices"] == {"3": "force"}
    assert summary["skill_selected_upgrade_choice_names"] == {"3": "威力强化"}


def test_challenge_rewards_skill_essence():
    state = engine.default_state(seed=123)
    before = state["materials"][engine.SKILL_ESSENCE_KEY]
    dungeon_id = engine.dungeon_list_view(state)[0]["dungeon_id"]
    engine.add_plan_action(state, "challenge", dungeon_id)
    result = engine.end_day(state)
    report = result["reports"][0]
    gained = report["rewards"]["materials"].get(engine.SKILL_ESSENCE_KEY, 0)
    assert gained > 0
    assert state["materials"][engine.SKILL_ESSENCE_KEY] == before + gained


def test_character_can_promote_into_advanced_class_branch():
    state = engine.default_state(seed=9)
    warrior = next(ch for ch in state["characters"] if ch["class_id"] == "warrior")
    locked = engine.promotion_options_for_character(state, warrior)
    assert {row["class_id"] for row in locked} == {"berserker", "sword_commander"}
    assert not any(row["can_promote"] for row in locked)

    while warrior["level"] < 6:
        engine.level_up_character(warrior)
    engine.upgrade_skill(state, warrior["id"], "power_strike")
    before_attack = int(warrior["base_stats"]["attack"])

    promoted = engine.promote_character(state, warrior["id"], "berserker")
    assert promoted["class_id"] == "berserker"
    assert promoted["base_class_id"] == "warrior"
    assert promoted["class_path"] == ["warrior", "berserker"]
    assert state["materials"][engine.PROMOTION_BADGE_KEY] == engine.STARTING_PROMOTION_BADGES - 1
    assert "power_strike" in promoted["skills"]
    assert "blood_frenzy" in promoted["learned_skills"]
    assert promoted["skill_upgrades"]["power_strike"]["level"] == 2
    assert engine.character_promotion_summary(state, promoted)["promoted"]
    engine.equip_item(state, promoted["id"], promoted["equipment"]["weapon"])

    engine.level_up_character(promoted)
    assert int(promoted["base_stats"]["attack"]) == before_attack + 2


def test_attack_and_defense_skill_taxonomy():
    data = engine.load_data()
    attack_types = set(engine.ATTACK_TYPES)

    for skill in data["skills"]:
        if skill.get("type") in {"damage", "debuff"}:
            assert isinstance(skill.get("attack_type"), str)
            assert skill["attack_type"] in attack_types
            assert not isinstance(skill.get("attack_type"), list)
        for defense_type in skill.get("defense_types", []):
            assert defense_type in attack_types

    for enemy in data["enemies"]:
        for skill in enemy.get("skills", []):
            assert engine.attack_type_for_skill(skill) in attack_types

    state = engine.default_state(seed=9)
    warrior = next(ch for ch in state["characters"] if ch["class_id"] == "warrior")
    assert set(warrior["tactics"]["defense_skill_by_type"]) == {"melee", "ranged"}

    engine.update_tactics(state, {
        "characters": [{
            "character_id": warrior["id"],
            "defense_skill_by_type": {"melee": "guard", "magic": "guard"},
        }]
    })
    assert warrior["tactics"]["defense_skill_by_type"] == {"melee": "guard"}


def test_tactic_schemes_save_load_and_limit():
    state = engine.default_state(seed=9)
    first = state["characters"][0]
    initiative_sid = next(
        sid for sid in engine.active_skill_ids_for_character(first)
        if engine.is_initiative_skill(engine.load_data()["skill_by_id"].get(sid, {}))
    )
    payload = engine.current_tactics_payload(state)
    payload["retreat_strategy"] = "conservative"
    payload["characters"][0]["initiative_skill"] = initiative_sid
    scheme = engine.save_tactic_scheme(state, {"name": "保守先手", "tactics": payload})
    assert len(engine.tactic_schemes_view(state)) == 1
    assert scheme["name"] == "保守先手"

    engine.update_tactics(state, {"retreat_strategy": "death_or_glory", "characters": [{"character_id": first["id"], "initiative_skill": ""}]})
    assert state["retreat_strategy"] == "death_or_glory"
    assert engine.effective_stats(state, first)["initiative_skill"]["is_default"]

    engine.load_tactic_scheme(state, scheme["id"])
    assert state["retreat_strategy"] == "conservative"
    assert engine.effective_stats(state, first)["initiative_skill"]["skill_id"] == initiative_sid

    for idx in range(engine.MAX_TACTIC_SCHEMES - 1):
        engine.save_tactic_scheme(state, {"name": f"方案{idx}", "tactics": engine.current_tactics_payload(state)})
    try:
        engine.save_tactic_scheme(state, {"name": "溢出", "tactics": engine.current_tactics_payload(state)})
        assert False, "should reject more than max tactic schemes"
    except ValueError:
        pass


def test_layer_tactics_are_saved_per_character_and_applied_per_layer():
    state = engine.default_state(seed=9)
    ch = state["characters"][0]
    initiative_sid = next(
        sid for sid in engine.active_skill_ids_for_character(ch)
        if engine.is_initiative_skill(engine.load_data()["skill_by_id"].get(sid, {}))
    )

    assert not ch["tactics"].get("initiative_skill")
    engine.update_tactics(state, {
        "layer_index": 2,
        "characters": [{"character_id": ch["id"], "initiative_skill": initiative_sid}],
    })
    assert not ch["tactics"].get("initiative_skill")
    assert state["layer_tactics"]["2"][ch["id"]]["initiative_skill"] == initiative_sid

    party = engine.make_player_combatants(state)
    unit = next(u for u in party if u["id"] == ch["id"])
    assert unit["initiative_skill"]["is_default"]

    applied = engine.apply_layer_tactics_to_party(state, party, 2)
    assert ch["name"] in applied
    assert unit["tactics"]["initiative_skill"] == initiative_sid
    assert unit["initiative_skill"]["skill_id"] == initiative_sid

    applied = engine.apply_layer_tactics_to_party(state, party, 3)
    assert ch["name"] not in applied
    assert unit["tactics"].get("initiative_skill", "") == ""
    assert unit["initiative_skill"]["is_default"]

    engine.update_tactics(state, {
        "layer_index": 2,
        "characters": [{"character_id": ch["id"], "clear_layer_tactic": True}],
    })
    assert state.get("layer_tactics", {}) == {}


def test_challenge_plan_can_bind_total_tactic_scheme():
    state = engine.default_state(seed=9)
    ch = state["characters"][0]
    initiative_sid = next(
        sid for sid in engine.active_skill_ids_for_character(ch)
        if engine.is_initiative_skill(engine.load_data()["skill_by_id"].get(sid, {}))
    )
    payload = engine.current_tactics_payload(state)
    payload["layer_tactics"] = {
        "1": {
            ch["id"]: {
                **engine.tactic_row_from_character(ch),
                "initiative_skill": initiative_sid,
            }
        }
    }
    scheme = engine.save_tactic_scheme(state, {"name": "一层先手", "tactics": payload})
    dungeon_id = engine.dungeon_list_view(state)[0]["dungeon_id"]

    action = engine.add_plan_action(state, "challenge", dungeon_id, tactic_scheme_id=scheme["id"])
    assert action["tactic_scheme_id"] == scheme["id"]
    assert action["tactic_scheme_name"] == "一层先手"

    result = engine.end_day(state)
    report = result["reports"][0]
    assert report["tactic_scheme_id"] == scheme["id"]
    assert report["tactic_scheme_name"] == "一层先手"
    assert any(e.get("type") == "layer_tactics" for e in report["layer_results"][0].get("pre_events", []))


def test_two_expeditions_use_distinct_teams_and_members():
    state = engine.default_state(seed=123)
    dungeons = engine.dungeon_list_view(state)
    first, second = dungeons[0]["dungeon_id"], dungeons[1]["dungeon_id"]
    a1 = engine.add_plan_action(state, "challenge", first)
    a2 = engine.add_plan_action(state, "scout", second)
    assert a1["team_id"] == "team_1"
    assert a2["team_id"] == "team_2"
    try:
        engine.add_plan_action(state, "scout", first, team_id="team_1")
        assert False, "same team should not be able to depart twice"
    except ValueError:
        pass
    result = engine.end_day(state)
    assert {r["team_id"] for r in result["reports"]} == {"team_1", "team_2"}


def test_batch_formations_allow_swaps_and_prevent_duplicate_members():
    state = engine.default_state(seed=9)
    engine.update_formations(state, {
        "team_1": {"r0c1": "ch_5", "r2c1": "ch_6"},
        "team_2": {"r0c1": "ch_1", "r1c1": "ch_2"},
    })
    assert state["formations"]["team_1"]["r0c1"] == "ch_5"
    assert state["formations"]["team_2"]["r0c1"] == "ch_1"
    try:
        engine.update_formations(state, {
            "team_1": {"r0c1": "ch_1"},
            "team_2": {"r0c1": "ch_1"},
        })
        assert False, "same character must not be assigned to two teams"
    except ValueError:
        pass


def test_day_25_unlocks_final_boss():
    state = engine.default_state(seed=7)
    state["day"] = 25
    state["active_dungeons"] = []
    engine.world_refresh(state)
    assert any(d.get("is_final") for d in state["active_dungeons"])
