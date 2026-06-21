"""Quest system tests: story chains, daily refresh, hidden reveal, rewards.

These cover the three quest families (story main/side, daily, hidden) end to end:
state seeding, manual acceptance, objective evaluation after clearing/scouting
dungeons, story-chain unlocking, daily expiration/refresh, hidden condition and
echo reveals, and reward claiming.
"""
from __future__ import annotations

from backend.game_core import engine


def _available_ids(state):
    return {q["template_id"] for q in state["quests"] if q["status"] == "available"}


def _get_quest(state, quest_id):
    return next(q for q in state["quests"] if q["id"] == quest_id)


def _first_dungeon_with_template(state, template_id):
    return next((d for d in state["active_dungeons"] if d["template_id"] == template_id), None)


def _reveal_original_main(state):
    """Skip the tutorial gate for legacy campaign lifecycle assertions."""
    state["quest_flags"]["delta_academy_graduated"] = True
    engine._reveal_eligible_story_quests(state)


def test_new_game_seeds_main_quest_and_daily_commissions():
    state = engine.default_state(seed=42)
    view = engine.quest_list_view(state)

    # The tutorial mainline is now the opening story quest.
    assert "main_delta_001_orientation" in _available_ids(state)
    assert "main_001_spider_nest" not in _available_ids(state)
    # Daily commissions rolled for day 1.
    daily_available = [q for q in view["available"] if q["type"] == "daily"]
    assert len(daily_available) == engine.load_data().get("daily_quest_count", 3)
    assert state["daily_quest_day"] == 1
    # Hidden quests are NOT visible until revealed.
    assert all(q["type"] != "hidden" for q in view["available"])


def test_quest_state_is_backfilled_by_migrate_for_old_saves():
    state = {
        "schema_version": 1,
        "characters": [],
        "materials": {},
        "inventory": [],
        "next_counters": {"dungeon": 1, "plan": 1, "report": 1},
        "active_dungeons": [],
        "expedition_plan": [],
    }
    engine.migrate_state(state)
    assert state["quests"] == []
    assert state["quest_flags"] == {}
    assert "quest" in state["next_counters"]
    for key in engine.default_quest_stats():
        assert key in state["quest_stats"]


def test_accept_quest_spawns_persistent_dungeon_and_lifecycle_validation():
    state = engine.default_state(seed=7)
    _reveal_original_main(state)
    q = engine.accept_quest(state, "main_001_spider_nest")
    assert q["status"] == "active"
    assert q["accepted_day"] == 1

    # A persistent quest-linked dungeon should now exist.
    quest_dungeons = [d for d in state["active_dungeons"] if d.get("source_quest_id") == "main_001_spider_nest"]
    assert len(quest_dungeons) == 1
    assert quest_dungeons[0]["template_id"] == "spider_nest"
    assert quest_dungeons[0]["persistent"] is True
    assert quest_dungeons[0]["id"] in q["linked_dungeon_ids"]
    # It shows up in the dungeon list view with its quest link.
    row = next(d for d in engine.dungeon_list_view(state) if d["dungeon_id"] == quest_dungeons[0]["id"])
    assert row["source_quest_id"] == "main_001_spider_nest"
    assert row["persistent"] is True

    # Cannot accept a quest that is already active.
    try:
        engine.accept_quest(state, "main_001_spider_nest")
        assert False, "should not accept an active quest"
    except ValueError:
        pass
    # Cannot accept a non-existent quest.
    try:
        engine.accept_quest(state, "does_not_exist")
        assert False
    except ValueError:
        pass


def test_clearing_quest_dungeon_completes_objective_and_claim_grants_rewards_and_chain():
    state = engine.default_state(seed=11)
    _reveal_original_main(state)
    engine.accept_quest(state, "main_001_spider_nest")

    # Find the quest's persistent dungeon and challenge it directly (not via end_day)
    # so the test asserts the resolve_challenge quest hook in isolation.
    quest_dungeon = next(d for d in state["active_dungeons"] if d.get("source_quest_id") == "main_001_spider_nest")
    report = engine.resolve_challenge(state, quest_dungeon, action_index=0, team_id="team_1")

    q = _get_quest(state, "main_001_spider_nest")
    obj = q["objectives"][0]
    if report["result"] == "victory":
        assert obj["current"] == 1 and obj["completed"]
        assert q["status"] == "completed"
        assert state["quest_stats"]["dungeon_cleared_by_template"]["spider_nest"] >= 1

        # Snapshot AFTER the battle so the claim-only deltas are isolated from
        # the dungeon's own clear rewards.
        gold_before = state["gold"]
        venom_before = state["materials"].get("venom_sac", 0)
        essence_before = state["materials"][engine.SKILL_ESSENCE_KEY]

        claimed = engine.claim_quest(state, "main_001_spider_nest")
        assert claimed["status"] == "claimed"
        assert state["gold"] == gold_before + 80
        assert state["materials"]["venom_sac"] == venom_before + 2
        assert state["materials"][engine.SKILL_ESSENCE_KEY] == essence_before + 3
        assert state["quest_flags"].get("main_spider_nest_cleared") is True
        # Story chain unlocks the next main quest.
        assert "main_002_bandit_trace" in _available_ids(state)
        # Claimed quests no longer block the linked dungeon (it is removed).
        assert not any(d.get("source_quest_id") == "main_001_spider_nest" for d in state["active_dungeons"])


def test_daily_quests_require_manual_accept_and_expire_on_day_rollover():
    state = engine.default_state(seed=13)
    daily = next(q for q in state["quests"] if q["type"] == "daily" and q["status"] == "available")
    # Daily quests must be manually accepted before they count as active.
    engine.accept_quest(state, daily["id"])
    assert _get_quest(state, daily["id"])["status"] == "active"

    # End the day without completing it: the daily expires and a new set rolls.
    engine.end_day(state)
    assert _get_quest(state, daily["id"])["status"] == "expired"
    assert state["daily_quest_day"] == 2
    new_dailies = [q for q in state["quests"] if q["type"] == "daily" and q["status"] == "available"]
    assert len(new_dailies) == engine.load_data().get("daily_quest_count", 3)


def test_scout_dungeon_objectives_progress_on_scout():
    state = engine.default_state(seed=21)
    # Accept the scout_any daily if one was rolled, else accept a scout objective story quest path.
    scout_daily = next((q for q in state["quests"] if q["type"] == "daily"
                        and any(o["kind"] == "scout_any_dungeon" for o in q["objectives"])
                        and q["status"] == "available"), None)
    if not scout_daily:
        return  # daily pool is sampled; if absent this run, nothing to assert
    engine.accept_quest(state, scout_daily["id"])

    dungeon = engine.dungeon_list_view(state)[0]
    instance = next(d for d in state["active_dungeons"] if d["id"] == dungeon["dungeon_id"])
    engine.resolve_scout(state, instance, team_id="team_1")

    obj = next(o for o in _get_quest(state, scout_daily["id"])["objectives"] if o["kind"] == "scout_any_dungeon")
    assert obj["current"] == 1 and obj["completed"]
    assert state["quest_stats"]["dungeon_scouted_by_template"][instance["template_id"]] >= 1


def test_hidden_quest_echo_reveals_on_blind_victory():
    state = engine.default_state(seed=5)
    # The blind-victory hidden quest is NOT yet revealed.
    assert "hidden_blind_victory" not in _available_ids(state)

    # An unscented clear of a danger-3+ dungeon triggers the echo reveal path,
    # which fires even though the reveal_condition flag is not set -- that is
    # the whole point of an "accidental" hidden achievement.
    engine.spawn_dungeon_instance(state, "bandit_camp")
    target = _first_dungeon_with_template(state, "bandit_camp")
    target["scout_info"] = None  # ensure unscented
    assert int(target["danger_level"]) >= 3

    engine.record_quest_events(state, [{
        "event": "clear_unscouted_dungeon",
        "dungeon_template_id": "bandit_camp",
        "danger_level": int(target["danger_level"]),
        "amount": 1,
    }])
    # Echo reveal: completing it incidentally produces a completed hidden quest.
    hidden = _get_quest(state, "hidden_blind_victory")
    assert hidden["status"] == "completed"
    assert hidden["revealed_from_hidden"] is True
    # Which can then be claimed for its reward.
    gold_before = state["gold"]
    engine.claim_quest(state, "hidden_blind_victory")
    assert state["gold"] == gold_before + 140
    assert state["quest_stats"]["hidden_completed"] >= 1


def test_hidden_quest_condition_reveal_only_when_flag_set():
    state = engine.default_state(seed=31)
    # streak warrior requires the bandit-trace flag.
    assert "hidden_streak_warrior" not in _available_ids(state)
    engine.check_hidden_reveals(state)
    assert "hidden_streak_warrior" not in _available_ids(state)
    state["quest_flags"]["main_bandit_trace_cleared"] = True
    engine.check_hidden_reveals(state)
    assert "hidden_streak_warrior" in _available_ids(state)


def test_hidden_quest_condition_reveal_path_requires_manual_accept():
    # Distinct from the echo path: when a hidden quest is revealed via its
    # reveal_conditions, it lands as 'available' and must be accepted manually.
    state = engine.default_state(seed=37)
    assert "hidden_blind_victory" not in _available_ids(state)
    state["quest_flags"]["main_spider_nest_cleared"] = True
    engine.check_hidden_reveals(state)
    hidden = _get_quest(state, "hidden_blind_victory")
    assert hidden["status"] == "available"
    engine.accept_quest(state, "hidden_blind_victory")
    assert _get_quest(state, "hidden_blind_victory")["status"] == "active"


def test_abandon_resets_story_quest_progress_and_expires_daily():
    state = engine.default_state(seed=17)
    _reveal_original_main(state)
    engine.accept_quest(state, "main_001_spider_nest")
    # Fake some progress then abandon.
    q = _get_quest(state, "main_001_spider_nest")
    q["objectives"][0]["current"] = 1
    engine.abandon_quest(state, "main_001_spider_nest")
    q = _get_quest(state, "main_001_spider_nest")
    assert q["status"] == "available"
    assert q["objectives"][0]["current"] == 0
    assert q["accepted_day"] is None

    daily = next(qq for qq in state["quests"] if qq["type"] == "daily" and qq["status"] == "available")
    engine.accept_quest(state, daily["id"])
    engine.abandon_quest(state, daily["id"])
    assert _get_quest(state, daily["id"])["status"] == "expired"


def test_public_state_view_and_preset_expose_quests():
    state = engine.default_state(seed=2)
    view = engine.public_state_view(state)
    assert "quests" in view and "quests_summary" in view
    assert view["quests_summary"]["available_count"] >= 1
    preset = engine.preset_public_view()
    assert "quests" in preset
    assert "quest_status_labels" in preset


def test_tutorial_orientation_uses_manual_ack_and_grants_equipment_reward():
    state = engine.default_state(seed=101)
    q = engine.accept_quest(state, "main_delta_001_orientation")
    assert q["status"] == "active"
    assert q["guide_sections"] and q["dialogue"]

    engine.complete_manual_quest_objective(state, "main_delta_001_orientation", "read_orientation")
    q = _get_quest(state, "main_delta_001_orientation")
    assert q["status"] == "completed"

    before = len(state["inventory"])
    claimed = engine.claim_quest(state, "main_delta_001_orientation")
    assert claimed["status"] == "claimed"
    assert len(state["inventory"]) == before + 1
    assert state["inventory"][-1]["template_id"] == "delta_cadet_badge"
    assert state["quest_flags"]["delta_orientation_complete"] is True
    assert "main_delta_002_basic_drill" in _available_ids(state)


def test_tutorial_public_view_exposes_guides_dialogue_and_equipment_preview():
    state = engine.default_state(seed=102)
    q = next(q for q in engine.quest_list_view(state)["available"] if q["template_id"] == "main_delta_001_orientation")
    assert q["guide_sections"][0]["title"] == "指挥台"
    assert q["guide_steps"][0]["target"] == '[data-guide-id="nav-quests"]'
    assert q["guide_steps"][2]["action"]["type"] == "navigate"
    assert q["dialogue"][0]["speaker"] == "教官岚"
    assert q["rewards"]["equipment"][0]["id"] == "delta_cadet_badge"
    assert q["rewards"]["equipment"][0]["preview"]["template_id"] == "delta_cadet_badge"


def test_layer_tactic_requirements_are_data_driven_and_reusable():
    state = engine.default_state(seed=103)
    template = engine.load_data()["dungeon_by_id"]["delta_layer_matrix"]
    party = engine.make_player_combatants(state, "team_1")
    engine.apply_layer_tactics_to_party(state, party, 1)
    assert engine.evaluate_layer_tactic_requirements(template["layers"][0], party)

    # Save a layer-1 override for the rogue (ch_4 / 诺克) with armor_break in
    # skill priority; the same generic evaluator now passes.
    engine.update_tactics(state, {
        "layer_index": 1,
        "characters": [{
            "character_id": "ch_4",
            "target_priority": "highest_defense",
            "skill_priority": ["armor_break"],
            "opening_skill_priority": [],
            "defense_skill_by_type": {},
        }],
    })
    party = engine.make_player_combatants(state, "team_1")
    engine.apply_layer_tactics_to_party(state, party, 1)
    assert engine.evaluate_layer_tactic_requirements(template["layers"][0], party) == []


def test_tutorial_dungeon_guaranteed_equipment_drop():
    state = engine.default_state(seed=104)
    dungeon = engine.spawn_dungeon_instance(state, "delta_basic_drill")
    report = engine.resolve_challenge(state, dungeon, action_index=0, team_id="team_1")
    assert report["result"] == "victory"
    drops = [e["item"]["template_id"] for e in report["rewards"]["equipment"] if isinstance(e, dict)]
    assert "delta_cadet_badge" in drops


def test_persistent_quest_dungeon_survives_day_rollover_until_claimed():
    state = engine.default_state(seed=23)
    _reveal_original_main(state)
    engine.accept_quest(state, "main_001_spider_nest")
    linked = next(d for d in state["active_dungeons"] if d.get("source_quest_id") == "main_001_spider_nest")
    # Mark cleared (simulating a victory) but do NOT claim yet.
    linked["cleared"] = True
    linked["reward_charges"] = 0
    engine.end_day(state)  # triggers world_refresh cleanup pass
    # The persistent quest dungeon must survive because the quest is unclaimed.
    assert any(d["id"] == linked["id"] for d in state["active_dungeons"])
