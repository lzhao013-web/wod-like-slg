from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.services.game_service import game_service

app = FastAPI(title="WOD-like SLG MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/game/new")
def new_game(payload: dict[str, Any] = Body(default_factory=dict)):
    return call(game_service.new_game, payload.get("seed"))


@app.get("/game/state")
def game_state():
    return game_service.get_state()


@app.get("/game/preset")
def game_preset():
    return game_service.preset()


@app.get("/game/presets")
def game_presets():
    return game_service.presets()


@app.post("/game/save")
def save_game():
    return game_service.save()


@app.post("/game/load")
def load_game():
    return game_service.load()


@app.get("/game/saves")
def save_slots():
    return game_service.save_slots()


@app.post("/game/saves/{slot_id}/save")
def save_to_slot(slot_id: str):
    return call(game_service.save_to_slot, slot_id)


@app.post("/game/saves/{slot_id}/load")
def load_from_slot(slot_id: str):
    return call(game_service.load_from_slot, slot_id)


@app.delete("/game/saves/{slot_id}")
def delete_save_slot_api(slot_id: str):
    return call(game_service.delete_slot, slot_id)


@app.post("/game/end-day")
def end_day():
    return call(game_service.end_day)


@app.get("/dungeons")
def dungeons():
    return game_service.dungeons()


@app.get("/dungeons/{dungeon_id}")
def dungeon_detail(dungeon_id: str):
    return call(game_service.dungeon_detail, dungeon_id)


@app.post("/dungeons/{dungeon_id}/scout")
def plan_scout(dungeon_id: str, payload: dict[str, Any] = Body(default_factory=dict)):
    return call(game_service.add_plan, "scout", dungeon_id, payload.get("team_id"))


@app.post("/dungeons/{dungeon_id}/challenge")
def plan_challenge(dungeon_id: str, payload: dict[str, Any] = Body(default_factory=dict)):
    return call(game_service.add_plan, "challenge", dungeon_id, payload.get("team_id"), payload.get("tactic_scheme_id") or payload.get("scheme_id"))


@app.get("/party")
def party():
    return game_service.party()


@app.post("/party/formation")
def party_formation(payload: dict[str, Any] = Body(...)):
    return call(game_service.update_formation, payload.get("formation", payload), payload.get("team_id", "team_1"))


@app.post("/party/formations")
def party_formations(payload: dict[str, Any] = Body(...)):
    return call(game_service.update_formations, payload.get("formations", payload))


@app.post("/party/equipment")
def party_equipment(payload: dict[str, Any] = Body(...)):
    return call(game_service.equip, payload)


@app.post("/party/tactics")
def party_tactics(payload: dict[str, Any] = Body(...)):
    return call(game_service.update_tactics, payload)


@app.post("/party/skills/learn")
def learn_skill(payload: dict[str, Any] = Body(...)):
    return call(game_service.learn_skill, payload)


@app.post("/party/skills/upgrade")
def upgrade_skill(payload: dict[str, Any] = Body(...)):
    return call(game_service.upgrade_skill, payload)


@app.post("/party/promote")
def promote_character(payload: dict[str, Any] = Body(...)):
    return call(game_service.promote_character, payload)


@app.post("/party/attributes/allocate")
def allocate_attributes(payload: dict[str, Any] = Body(...)):
    return call(game_service.allocate_attributes, payload)


@app.post("/party/attributes/reset")
def reset_attributes(payload: dict[str, Any] = Body(...)):
    return call(game_service.reset_attributes, payload)


@app.post("/party/tactic-schemes")
def save_tactic_scheme(payload: dict[str, Any] = Body(default_factory=dict)):
    return call(game_service.save_tactic_scheme, payload)


@app.post("/party/tactic-schemes/{scheme_id}/load")
def load_tactic_scheme(scheme_id: str):
    return call(game_service.load_tactic_scheme, scheme_id)


@app.delete("/party/tactic-schemes/{scheme_id}")
def delete_tactic_scheme(scheme_id: str):
    return call(game_service.delete_tactic_scheme, scheme_id)


@app.post("/party/retreat-condition")
def retreat_condition(payload: dict[str, Any] = Body(...)):
    return call(game_service.update_tactics, {"retreat_strategy": payload.get("retreat_strategy")})


@app.get("/expedition-plan")
def expedition_plan():
    return game_service.get_plan()


@app.post("/expedition-plan")
def replace_plan(payload: dict[str, Any] = Body(...)):
    return call(game_service.replace_plan, payload.get("actions", []))


@app.post("/expedition-plan/clear")
def clear_plan():
    return game_service.clear_plan()


@app.delete("/expedition-plan/{index}")
def remove_plan_action(index: int):
    return call(game_service.remove_plan, index)


@app.get("/reports")
def reports():
    return game_service.reports()


@app.get("/reports/{report_id}")
def report(report_id: str):
    return call(game_service.report, report_id)


@app.get("/reports/{report_id}/summary")
def report_summary(report_id: str):
    r = call(game_service.report, report_id)
    return {k: r.get(k) for k in ["id", "day", "dungeon_name", "result", "summary", "failure_reasons", "revealed_mechanics"]}


@app.get("/reports/{report_id}/turns")
def report_turns(report_id: str):
    r = call(game_service.report, report_id)
    return {"report_id": report_id, "turn_logs": r.get("turn_logs", [])}


@app.get("/quests")
def quests():
    return game_service.quests()


@app.post("/quests/{quest_id}/accept")
def accept_quest(quest_id: str):
    return call(game_service.accept_quest, quest_id)


@app.post("/quests/{quest_id}/objectives/{objective_id}/complete")
def complete_quest_objective(quest_id: str, objective_id: str):
    return call(game_service.complete_quest_objective, quest_id, objective_id)


@app.post("/quests/{quest_id}/claim")
def claim_quest(quest_id: str):
    return call(game_service.claim_quest, quest_id)


@app.post("/quests/{quest_id}/abandon")
def abandon_quest(quest_id: str):
    return call(game_service.abandon_quest, quest_id)


@app.get("/shop")
def shop():
    return game_service.shop()


@app.post("/shop/buy")
def buy(payload: dict[str, Any] = Body(...)):
    return call(game_service.buy, payload.get("shop_id"))


@app.post("/shop/sell")
def sell(payload: dict[str, Any] = Body(...)):
    return call(game_service.sell, payload.get("item_id"))


@app.post("/shop/salvage")
def salvage(payload: dict[str, Any] = Body(...)):
    return call(game_service.salvage, payload.get("item_id"))


@app.post("/party/equipment/enchant")
def enchant_equipment(payload: dict[str, Any] = Body(...)):
    return call(game_service.enchant_equipment, payload.get("item_id"))


@app.post("/party/equipment/reroll")
def reroll_enchant(payload: dict[str, Any] = Body(...)):
    return call(game_service.reroll_enchant, payload)


@app.post("/party/equipment/ascend")
def ascend_equipment(payload: dict[str, Any] = Body(...)):
    return call(game_service.ascend_equipment, payload.get("item_id"))


@app.get("/recruits")
def recruits():
    return game_service.recruits()


@app.get("/equipment/ascension-recipes")
def ascension_recipes():
    return game_service.ascension_recipes()


@app.post("/recruits/recruit")
def recruit(payload: dict[str, Any] = Body(...)):
    return call(game_service.recruit, payload.get("candidate_id"))


@app.post("/recruits/dismiss")
def dismiss(payload: dict[str, Any] = Body(...)):
    return call(game_service.dismiss, payload.get("character_id"))


@app.post("/debug/reset-save")
def reset_save():
    return game_service.reset_save()


@app.get("/debug/state")
def debug_state():
    return game_service.full_state()


# Optional: serve built frontend from the backend when frontend/dist exists.
ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        index = DIST / "index.html"
        if index.exists():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="frontend not built")
