from __future__ import annotations

from typing import Any

from backend.app.services.save_service import delete_save, load_state, save_state
from backend.game_core import engine


class GameService:
    def __init__(self) -> None:
        self.state = load_state() or engine.default_state()
        engine.migrate_state(self.state)
        save_state(self.state)

    def new_game(self, seed: int | None = None) -> dict[str, Any]:
        self.state = engine.default_state(seed=seed)
        save_state(self.state)
        return engine.public_state_view(self.state)

    def save(self) -> dict[str, Any]:
        save_state(self.state)
        return {"ok": True}

    def load(self) -> dict[str, Any]:
        loaded = load_state()
        if loaded is None:
            self.state = engine.default_state()
        else:
            self.state = loaded
        engine.migrate_state(self.state)
        save_state(self.state)
        return engine.public_state_view(self.state)

    def reset_save(self) -> dict[str, Any]:
        delete_save()
        self.state = engine.default_state()
        save_state(self.state)
        return engine.public_state_view(self.state)

    def get_state(self) -> dict[str, Any]:
        engine.migrate_state(self.state)
        return engine.public_state_view(self.state)

    def preset(self) -> dict[str, Any]:
        return engine.preset_public_view()

    def presets(self) -> dict[str, Any]:
        return engine.preset_list_view()

    def full_state(self) -> dict[str, Any]:
        return engine.full_debug_state(self.state)

    def dungeons(self) -> list[dict[str, Any]]:
        return engine.dungeon_list_view(self.state)

    def dungeon_detail(self, dungeon_id: str) -> dict[str, Any]:
        return engine.dungeon_detail_view(self.state, dungeon_id)

    def add_plan(self, action_type: str, dungeon_id: str, team_id: str | None = None, tactic_scheme_id: str | None = None) -> dict[str, Any]:
        action = engine.add_plan_action(self.state, action_type, dungeon_id, team_id, tactic_scheme_id)
        save_state(self.state)
        return action

    def clear_plan(self) -> dict[str, Any]:
        engine.clear_plan(self.state)
        save_state(self.state)
        return {"ok": True, "plan": self.state["expedition_plan"]}

    def get_plan(self) -> dict[str, Any]:
        actions = []
        for idx, action in enumerate(self.state.get("expedition_plan", [])):
            row = dict(action)
            team_id = row.get("team_id") or (engine.TEAM_IDS[idx] if idx < len(engine.TEAM_IDS) else "team_1")
            row["team_id"] = team_id
            row["team_name"] = engine.TEAM_LABELS.get(team_id, team_id)
            if row.get("type") == "challenge" and row.get("tactic_scheme_id") and not row.get("tactic_scheme_name"):
                scheme = engine.tactic_scheme_by_id(self.state, row.get("tactic_scheme_id"))
                row["tactic_scheme_name"] = scheme["name"] if scheme else "已删除方案"
            actions.append(row)
        return {"actions": actions, "expedition_points_left": max(0, 2 - len(actions))}

    def replace_plan(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        engine.clear_plan(self.state)
        for action in actions[:2]:
            engine.add_plan_action(self.state, action["type"], action["dungeon_id"], action.get("team_id"), action.get("tactic_scheme_id"))
        save_state(self.state)
        return self.get_plan()

    def end_day(self) -> dict[str, Any]:
        result = engine.end_day(self.state)
        save_state(self.state)
        return result

    def party(self) -> dict[str, Any]:
        engine.migrate_state(self.state)
        return engine.party_summary(self.state) | {
            "inventory": self.state.get("inventory", []),
            "target_options": engine.TARGET_LABELS,
            "retreat_options": engine.RETREAT_LABELS,
            "defense_trigger_options": engine.DEFENSE_TRIGGER_LABELS,
            "tactic_schemes": engine.tactic_schemes_view(self.state),
            "max_tactic_schemes": engine.MAX_TACTIC_SCHEMES,
            "max_tactic_layers": engine.MAX_TACTIC_LAYERS,
        }

    def update_formation(self, formation: dict[str, str | None], team_id: str = "team_1") -> dict[str, Any]:
        engine.update_formation(self.state, formation, team_id)
        save_state(self.state)
        return self.party()

    def update_formations(self, formations: dict[str, dict[str, str | None]]) -> dict[str, Any]:
        engine.update_formations(self.state, formations)
        save_state(self.state)
        return self.party()

    def update_tactics(self, payload: dict[str, Any]) -> dict[str, Any]:
        engine.update_tactics(self.state, payload)
        save_state(self.state)
        return self.party()

    def learn_skill(self, payload: dict[str, Any]) -> dict[str, Any]:
        ch = engine.learn_skill(self.state, payload.get("character_id"), payload.get("skill_id"))
        save_state(self.state)
        return self.party() | {"character": ch}

    def upgrade_skill(self, payload: dict[str, Any]) -> dict[str, Any]:
        ch = engine.upgrade_skill(self.state, payload.get("character_id"), payload.get("skill_id"), payload.get("choice_id"))
        save_state(self.state)
        return self.party() | {"character": ch, "state": self.get_state()}

    def promote_character(self, payload: dict[str, Any]) -> dict[str, Any]:
        ch = engine.promote_character(self.state, payload.get("character_id"), payload.get("target_class_id"))
        save_state(self.state)
        return self.party() | {"character": ch, "state": self.get_state()}

    def save_tactic_scheme(self, payload: dict[str, Any]) -> dict[str, Any]:
        scheme = engine.save_tactic_scheme(self.state, payload)
        save_state(self.state)
        return self.party() | {"scheme": scheme}

    def load_tactic_scheme(self, scheme_id: str) -> dict[str, Any]:
        scheme = engine.load_tactic_scheme(self.state, scheme_id)
        save_state(self.state)
        return self.party() | {"scheme": scheme}

    def delete_tactic_scheme(self, scheme_id: str) -> dict[str, Any]:
        engine.delete_tactic_scheme(self.state, scheme_id)
        save_state(self.state)
        return self.party()

    def equip(self, payload: dict[str, Any]) -> dict[str, Any]:
        engine.equip_item(self.state, payload.get("character_id"), payload.get("equipment_instance_id"), payload.get("slot"))
        save_state(self.state)
        return self.party()

    def shop(self) -> dict[str, Any]:
        return self.state.get("shop", {"items": [], "recruits": []})

    def buy(self, shop_id: str) -> dict[str, Any]:
        item = engine.buy_shop_item(self.state, shop_id)
        save_state(self.state)
        return {"ok": True, "acquired": item, "state": self.get_state(), "shop": self.shop()}

    def recruit(self, candidate_id: str) -> dict[str, Any]:
        ch = engine.recruit_character(self.state, candidate_id)
        save_state(self.state)
        return {"ok": True, "character": ch, "state": self.get_state(), "party": self.party()}

    def reports(self) -> list[dict[str, Any]]:
        return self.state.get("reports", [])

    def report(self, report_id: str) -> dict[str, Any]:
        report = next((r for r in self.state.get("reports", []) if r["id"] == report_id), None)
        if not report:
            raise ValueError("战报不存在")
        return report


game_service = GameService()
