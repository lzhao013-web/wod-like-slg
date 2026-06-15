from __future__ import annotations

import copy
import hashlib
import random
import time
import uuid
from collections import Counter, defaultdict
from typing import Any, Iterable

from .data import list_presets, load_data, template_copy

DAMAGE_TYPES = ["physical", "poison", "magic", "curse", "fire", "bleed"]
DAMAGE_TYPE_NAMES = {
    "physical": "物理",
    "poison": "毒",
    "magic": "魔法",
    "curse": "诅咒",
    "fire": "火焰",
    "bleed": "流血",
}

ATTACK_TYPES = ["melee", "ranged", "magic", "mental", "special"]
ATTACK_TYPE_LABELS = {
    "melee": "近战攻击",
    "ranged": "远程攻击",
    "magic": "魔法攻击",
    "mental": "精神攻击",
    "special": "特殊攻击",
}
LEGACY_DEFENSE_TRIGGER_ALIASES = {
    "physical": ["melee"],
    "bleed": ["melee"],
    "fire": ["magic"],
    "poison": ["special"],
    "curse": ["mental"],
}
FORMATION_CELLS = [f"r{r}c{c}" for r in range(3) for c in range(3)]
FRONT_CELLS = {"r0c0", "r0c1", "r0c2"}
MID_CELLS = {"r1c0", "r1c1", "r1c2"}
BACK_CELLS = {"r2c0", "r2c1", "r2c2"}
TEAM_IDS = ["team_1", "team_2"]
TEAM_LABELS = {"team_1": "一队", "team_2": "二队"}
MAX_TEAM_SIZE = 4
MAX_TACTIC_SCHEMES = 20
MAX_TACTIC_LAYERS = 12
SKILL_POINTS_PER_LEVEL = 1

MATERIAL_NAMES = {
    "leather": "皮革",
    "venom_sac": "毒囊",
    "cloth": "布料",
    "ore": "矿石",
    "shield_parts": "盾牌材料",
    "beast_fang": "野兽牙",
    "arcane_dust": "奥术尘",
    "relic": "古代遗物",
    "fire_core": "火焰核心",
    "glory": "胜利徽记",
}

STAT_NAMES = {
    "max_hp": "生命上限",
    "max_mana": "法力上限",
    "attack": "攻击",
    "defense": "防御",
    "speed": "速度",
    "accuracy": "命中",
    "evasion": "闪避",
    "action_count": "行动次数",
}

SPECIAL_EFFECT_NAMES = {
    "healing_bonus_minor": "小幅治疗加成",
    "healing_bonus": "治疗加成",
    "fire_bonus_minor": "小幅火焰加成",
    "guard_bonus": "护卫加成",
}

RETREAT_THRESHOLDS = {
    "conservative": 0.35,
    "standard": 0.20,
    "aggressive": 0.08,
    "death_or_glory": -1.0,
}

RETREAT_LABELS = {
    "conservative": "保守：任意角色 HP < 35% 撤退",
    "standard": "标准：任意角色 HP < 20% 撤退",
    "aggressive": "激进：濒危或关键角色倒下才撤退",
    "death_or_glory": "死战：不主动撤退",
}

TARGET_LABELS = {
    "front": "优先前排",
    "lowest_hp": "优先低 HP",
    "rear": "优先后排",
    "highest_attack": "优先高攻击",
    "highest_defense": "优先高防御",
    "elite": "优先精英 / Boss",
}

DEFENSE_TRIGGER_LABELS = ATTACK_TYPE_LABELS

ATTRIBUTE_KEYS = [
    "strength",
    "constitution",
    "dexterity",
    "agility",
    "intelligence",
    "willpower",
    "perception",
    "charisma",
]

ATTRIBUTE_NAMES = {
    "strength": "力量",
    "constitution": "体质",
    "dexterity": "灵巧",
    "agility": "敏捷",
    "intelligence": "智力",
    "willpower": "意志",
    "perception": "感知",
    "charisma": "魅力",
}

ATTRIBUTE_ICONS = {
    "strength": "💪",
    "constitution": "❤️",
    "dexterity": "🤲",
    "agility": "💨",
    "intelligence": "📘",
    "willpower": "🧠",
    "perception": "👁️",
    "charisma": "✨",
}

SKILL_FOCUS_WEIGHTS = {
    "melee": {"strength": 1.35, "dexterity": 1.0, "agility": 0.35},
    "ranged": {"perception": 1.25, "dexterity": 1.0, "agility": 0.55},
    "finesse": {"dexterity": 1.25, "agility": 1.05, "perception": 0.45},
    "magic": {"intelligence": 1.35, "willpower": 1.0, "perception": 0.35},
    "faith": {"willpower": 1.25, "charisma": 1.05, "intelligence": 0.45},
    "healing": {"charisma": 1.25, "willpower": 1.05, "intelligence": 0.35},
    "guard": {"constitution": 1.25, "willpower": 0.85, "strength": 0.65},
    "tactics": {"perception": 1.1, "intelligence": 0.9, "charisma": 0.65},
}


def now_ms() -> int:
    return int(time.time() * 1000)


def stable_seed(*parts: Any) -> int:
    h = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def weighted_choice(rng: random.Random, rows: list[dict[str, Any]], weight_fn) -> dict[str, Any]:
    weights = [max(1, int(weight_fn(r))) for r in rows]
    return copy.deepcopy(rng.choices(rows, weights=weights, k=1)[0])


def instance_equipment(template_id: str, instance_id: str | None = None) -> dict[str, Any]:
    tpl = template_copy("equipment", template_id)
    return {
        "instance_id": instance_id or make_id("eq"),
        "template_id": tpl["id"],
        "name": tpl["name"],
        "slot": tpl["slot"],
        "rarity": tpl.get("rarity", "common"),
        "cost": tpl.get("cost", 0),
        "stats": copy.deepcopy(tpl.get("stats", {})),
        "resistances": copy.deepcopy(tpl.get("resistances", {})),
        "special_effects": copy.deepcopy(tpl.get("special_effects", [])),
        "durability": int(tpl.get("durability", 30)),
        "max_durability": int(tpl.get("durability", 30)),
        "class_restriction": copy.deepcopy(tpl.get("class_restriction", [])),
        "equipped_by": None,
    }


def attribute_block_for_class(class_row: dict[str, Any], level: int = 1) -> dict[str, int]:
    """Return WOD-like attributes at a given level.

    The data table owns level-1 attributes plus deterministic per-level growth.
    Runtime character records store their current attributes so future systems can
    support training/respec without rewriting class tables.
    """
    base = {k: int(class_row.get("attributes", {}).get(k, 8)) for k in ATTRIBUTE_KEYS}
    growth = class_row.get("attribute_growth", {})
    for _ in range(max(0, int(level) - 1)):
        for k, v in growth.items():
            if k in base:
                base[k] += int(v)
    return base


def stat_block_for_class(class_row: dict[str, Any], level: int = 1) -> dict[str, int]:
    stats = {k: int(v) for k, v in class_row.get("stats", {}).items()}
    growth = class_row.get("stat_growth", {})
    for _ in range(max(0, int(level) - 1)):
        for k, v in growth.items():
            stats[k] = int(stats.get(k, 0)) + int(v)
    if int(level) >= 2:
        stats["accuracy"] = int(stats.get("accuracy", 80)) + (int(level) - 1) // 2
    return stats


def class_skill_ids(class_row: dict[str, Any]) -> list[str]:
    ids = list(class_row.get("skills", []))
    return ids or ["basic_attack"]


def class_skill_tree_nodes(class_id: str | None) -> list[dict[str, Any]]:
    """Normalize preset skill-tree nodes for one class.

    Skill acquisition is point/prerequisite based. `level_required` on skill data
    is kept only as legacy tier metadata and no longer unlocks skills by itself.
    """
    data = load_data()
    class_row = data.get("class_by_id", {}).get(class_id or "")
    if not class_row:
        return [{"skill_id": "basic_attack", "cost": 0, "prerequisites": [], "tier": 0, "auto_learn": True}]

    class_skills = class_skill_ids(class_row)
    skill_tree = data.get("preset", {}).get("skill_tree", {})
    raw_nodes = skill_tree.get(class_id or "", []) if isinstance(skill_tree, dict) else []
    if isinstance(raw_nodes, dict):
        raw_nodes = [{"skill_id": sid, **(row if isinstance(row, dict) else {})} for sid, row in raw_nodes.items()]
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raw_nodes = generated_skill_tree_nodes(class_skills, data)

    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            continue
        sid = str(raw.get("skill_id") or raw.get("skill") or "")
        if sid not in class_skills or sid in seen or sid not in data["skill_by_id"]:
            continue
        prereq_raw = raw.get("prerequisites", raw.get("requires", []))
        if isinstance(prereq_raw, str):
            prereqs = [prereq_raw]
        elif isinstance(prereq_raw, list):
            prereqs = [str(x) for x in prereq_raw if str(x) in class_skills and str(x) != sid]
        else:
            prereqs = []
        skill = data["skill_by_id"].get(sid, {})
        tier = int(raw.get("tier", skill.get("level_required", 1) if sid != "basic_attack" else 0))
        cost = int(raw.get("cost", 0 if sid == "basic_attack" or raw.get("auto_learn") else 1))
        nodes.append({
            "skill_id": sid,
            "cost": max(0, cost),
            "prerequisites": prereqs,
            "tier": max(0, tier),
            "auto_learn": bool(raw.get("auto_learn") or sid == "basic_attack"),
            "x": raw.get("x"),
            "y": raw.get("y"),
        })
        seen.add(sid)

    # Basic attack must always be available even if a custom preset forgot it.
    if "basic_attack" in class_skills and "basic_attack" not in seen:
        nodes.insert(0, {"skill_id": "basic_attack", "cost": 0, "prerequisites": [], "tier": 0, "auto_learn": True, "x": 0, "y": 0})
        seen.add("basic_attack")
    for sid in class_skills:
        if sid in seen or sid not in data["skill_by_id"]:
            continue
        skill = data["skill_by_id"].get(sid, {})
        nodes.append({
            "skill_id": sid,
            "cost": 1,
            "prerequisites": ["basic_attack"] if sid != "basic_attack" else [],
            "tier": int(skill.get("level_required", 1)),
            "auto_learn": False,
            "x": None,
            "y": None,
        })
    return nodes


def generated_skill_tree_nodes(class_skills: list[str], data: dict[str, Any]) -> list[dict[str, Any]]:
    """Fallback tree for custom presets that list skills but omit skill_tree."""
    nodes: list[dict[str, Any]] = []
    previous_by_kind: dict[str, str] = {}
    for idx, sid in enumerate(class_skills):
        skill = data["skill_by_id"].get(sid, {})
        tier = 0 if sid == "basic_attack" else int(skill.get("level_required", 1))
        kind = str(skill.get("category") or skill.get("type") or "skill")
        auto = sid == "basic_attack" or (tier <= 1 and (skill.get("type") == "passive" or "initiative" in set(skill.get("tags", []))))
        prereq = []
        if sid != "basic_attack" and not auto:
            prereq_skill = previous_by_kind.get(kind) or previous_by_kind.get("basic") or "basic_attack"
            if prereq_skill != sid:
                prereq = [prereq_skill]
        nodes.append({
            "skill_id": sid,
            "cost": 0 if auto else (1 if tier <= 4 else 2),
            "prerequisites": prereq,
            "tier": tier,
            "auto_learn": auto,
            "x": idx % 3,
            "y": tier,
        })
        if sid == "basic_attack":
            previous_by_kind["basic"] = sid
        else:
            previous_by_kind[kind] = sid
    return nodes


def class_skill_tree_node_map(class_id: str | None) -> dict[str, dict[str, Any]]:
    return {node["skill_id"]: node for node in class_skill_tree_nodes(class_id)}


def class_auto_learn_skill_ids(class_id: str | None) -> list[str]:
    return [node["skill_id"] for node in class_skill_tree_nodes(class_id) if node.get("auto_learn")]


def clean_learned_skill_ids(class_id: str | None, values: Any) -> list[str]:
    data = load_data()
    class_row = data.get("class_by_id", {}).get(class_id or "", {})
    class_skills = class_skill_ids(class_row) if class_row else ["basic_attack"]
    allowed = set(class_skills)
    out: list[str] = []
    for sid in class_auto_learn_skill_ids(class_id):
        if sid in allowed and sid not in out:
            out.append(sid)
    if isinstance(values, list):
        for raw in values:
            sid = str(raw)
            if sid in allowed and sid in data["skill_by_id"] and sid not in out:
                out.append(sid)
    return out or ["basic_attack"]


def legacy_level_unlocked_skill_ids(ch: dict[str, Any], class_row: dict[str, Any], data: dict[str, Any]) -> list[str]:
    level = int(ch.get("level", 1))
    out: list[str] = []
    for sid in class_skill_ids(class_row):
        skill = data["skill_by_id"].get(sid, {})
        if sid == "basic_attack" or int(skill.get("level_required", 1)) <= level:
            out.append(sid)
    return out or ["basic_attack"]


def stat_growth_text(class_row: dict[str, Any], key: str) -> str:
    parts: list[str] = []
    stat_growth = class_row.get("stat_growth", {})
    if key in stat_growth:
        parts.append(f"+{int(stat_growth.get(key, 0))}/级")
    if key == "accuracy":
        parts.append("通用 +1/2级")
    return "；".join(parts) or "—"


def stat_breakdown_for_character(ch: dict[str, Any], class_row: dict[str, Any], final_stats: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Expose raw-vs-final core stat numbers for the character sheet."""
    level = int(ch.get("level", 1))
    expected_raw = stat_block_for_class(class_row, level)
    raw_stats = {k: int(v) for k, v in ch.get("base_stats", expected_raw).items() if isinstance(v, (int, float))}
    keys = sorted(set(class_row.get("stats", {}).keys()) | set(raw_stats.keys()) | {"max_mana"})
    out: dict[str, dict[str, Any]] = {}
    for key in keys:
        base = int(class_row.get("stats", {}).get(key, 0))
        expected = int(expected_raw.get(key, base))
        raw = int(raw_stats.get(key, expected))
        final = int(final_stats.get(key, raw if key != "max_mana" else final_stats.get("max_mana", 0)))
        out[key] = {
            "base": base,
            "level_growth": expected - base,
            "raw": raw,
            "raw_adjustment": raw - expected,
            "bonus": final - raw,
            "final": final,
            "growth_per_level": int(class_row.get("stat_growth", {}).get(key, 0)),
            "growth_text": stat_growth_text(class_row, key),
        }
    return out


def attribute_breakdown_for_character(ch: dict[str, Any], class_row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Expose WOD eight-attribute base/growth/bonus/final numbers."""
    level = int(ch.get("level", 1))
    expected = attribute_block_for_class(class_row, level)
    current = ch.get("attributes", {})
    out: dict[str, dict[str, Any]] = {}
    for key in ATTRIBUTE_KEYS:
        base = int(class_row.get("attributes", {}).get(key, 8))
        expected_value = int(expected.get(key, base))
        final = int(current.get(key, expected_value))
        growth_per_level = int(class_row.get("attribute_growth", {}).get(key, 0))
        out[key] = {
            "base": base,
            "level_growth": expected_value - base,
            "raw": expected_value,
            "bonus": final - expected_value,
            "final": final,
            "growth_per_level": growth_per_level,
            "growth_text": f"+{growth_per_level}/级" if growth_per_level else "—",
        }
    return out


def class_preset_meta(class_id: str | None) -> dict[str, Any]:
    """UI/tactical metadata supplied by the active preset."""
    if not class_id:
        return {}
    data = load_data()
    meta = data.get("class_ui_by_id", {}).get(class_id, {})
    return meta if isinstance(meta, dict) else {}


def default_target_priority_for_class(class_id: str | None) -> str:
    target = str(class_preset_meta(class_id).get("default_target_priority") or "lowest_hp")
    return target if target in TARGET_LABELS else "lowest_hp"


def clean_tactic_skill_list(values: Any, known_skills: set[str], limit: int) -> list[str]:
    out: list[str] = []
    if not isinstance(values, list):
        return out
    for sid in values:
        if sid and sid in known_skills and sid != "basic_attack" and sid not in out:
            out.append(str(sid))
    return out[:limit]


def attack_type_for_skill(skill: dict[str, Any]) -> str:
    """Return the one tactical attack type for an offensive skill.

    `damage_types` remain elemental/resistance channels. `attack_type` is the
    single WOD-like attack method used by defense-response tactics.
    """
    raw = skill.get("attack_type")
    if isinstance(raw, str) and raw in ATTACK_TYPES:
        return raw
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item in ATTACK_TYPES:
                return item
    if skill.get("type") not in {"damage", "debuff"} and not skill.get("damage_types"):
        return ""
    damage_types = set(skill.get("damage_types") or [])
    if skill.get("range") == "melee":
        return "melee"
    if skill.get("range") == "ranged" and damage_types and damage_types.issubset({"physical", "poison", "bleed"}):
        return "ranged"
    if "curse" in damage_types:
        return "mental"
    if damage_types.intersection({"magic", "fire"}):
        return "magic"
    if skill.get("range") == "ranged":
        return "ranged"
    if damage_types:
        return "melee" if damage_types.issubset({"physical", "bleed"}) else "special"
    return "special"


def defense_types_for_skill(skill: dict[str, Any]) -> list[str]:
    """Return tactical attack types that a defensive response can answer."""
    raw = skill.get("defense_types")
    out: list[str] = []
    if isinstance(raw, str):
        raw = [raw]
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item in DEFENSE_TRIGGER_LABELS and item not in out:
                out.append(item)
    if out:
        return out

    # Compatibility fallback for old custom presets/saves that predate
    # defense_types. New preset data should be explicit.
    skill_type = skill.get("type")
    status_types = {str(st.get("type")) for st in skill.get("status_effects", []) if isinstance(st, dict)}
    if skill_type == "guard":
        return ["melee", "ranged"]
    if skill_type == "buff":
        if status_types.intersection({"shield_wall", "evasion_up", "barrier"}):
            return ["melee", "ranged", "special"]
        return []
    if skill_type == "support":
        if status_types.intersection({"ward", "barrier"}):
            return ["magic", "mental", "special"]
        if status_types.intersection({"guarding", "shield_wall"}):
            return ["melee", "ranged"]
    return []


def defense_trigger_keys(raw_key: Any) -> list[str]:
    key = str(raw_key)
    if key in DEFENSE_TRIGGER_LABELS:
        return [key]
    return copy.deepcopy(LEGACY_DEFENSE_TRIGGER_ALIASES.get(key, []))


def clean_defense_skill_map(raw: Any, known_skills: set[str], data: dict[str, Any]) -> dict[str, str]:
    defense: dict[str, str] = {}
    if not isinstance(raw, dict):
        return defense
    for raw_key, raw_sid in raw.items():
        sid = str(raw_sid or "")
        if not sid:
            continue
        skill = data["skill_by_id"].get(sid, {})
        if sid not in known_skills or sid == "basic_attack" or skill.get("type") not in {"guard", "buff", "support"}:
            continue
        supported = set(defense_types_for_skill(skill))
        for key in defense_trigger_keys(raw_key):
            if key in supported and key not in defense:
                defense[key] = sid
    return defense


def default_tactics_for_class(class_id: str | None) -> dict[str, Any]:
    """Preset-driven tactical defaults for newly created characters."""
    data = load_data()
    class_row = data.get("class_by_id", {}).get(class_id or "", {})
    meta = class_preset_meta(class_id)
    known_skills = set(class_skill_ids(class_row)) if class_row else {"basic_attack"}
    initiative_skill = str(meta.get("default_initiative_skill") or "")
    if initiative_skill:
        skill = data["skill_by_id"].get(initiative_skill, {})
        if initiative_skill not in known_skills or not is_initiative_skill(skill):
            initiative_skill = ""
    defense = clean_defense_skill_map(meta.get("default_defense_skill_by_type") or {}, known_skills, data)
    return {
        "target_priority": default_target_priority_for_class(class_id),
        "initiative_skill": initiative_skill,
        "skill_priority": clean_tactic_skill_list(meta.get("default_skill_priority", []), known_skills, 8),
        "opening_skill_priority": clean_tactic_skill_list(meta.get("default_opening_skill_priority", []), known_skills, 4),
        "defense_skill_by_type": defense,
    }


def normalize_character(ch: dict[str, Any]) -> dict[str, Any]:
    """Migrate older saves in-place to the richer attribute/skill schema."""
    data = load_data()
    class_row = data["class_by_id"].get(ch.get("class_id"))
    if not class_row:
        return ch
    legacy_without_attributes = not isinstance(ch.get("attributes"), dict)
    ch.setdefault("class_name", class_row.get("name", ch.get("class_id", "")))
    ch.setdefault("role", class_row.get("role", ""))
    if legacy_without_attributes:
        ch["base_stats"] = stat_block_for_class(class_row, int(ch.get("level", 1)))
        ch["base_resistances"] = copy.deepcopy(class_row.get("resistances", {}))
        ch["attributes"] = attribute_block_for_class(class_row, int(ch.get("level", 1)))
    else:
        ch.setdefault("base_stats", copy.deepcopy(class_row.get("stats", {})))
        ch.setdefault("base_resistances", copy.deepcopy(class_row.get("resistances", {})))
        level_attrs = attribute_block_for_class(class_row, 1)
        for key in ATTRIBUTE_KEYS:
            ch["attributes"][key] = int(ch["attributes"].get(key, level_attrs.get(key, 8)))
    ch["skills"] = class_skill_ids(class_row)
    if not isinstance(ch.get("learned_skills"), list):
        ch["learned_skills"] = legacy_level_unlocked_skill_ids(ch, class_row, data)
    ch["learned_skills"] = clean_learned_skill_ids(ch.get("class_id"), ch.get("learned_skills"))
    ch["skill_points"] = max(0, int(ch.get("skill_points", 0)))
    ch.setdefault("equipment", {"weapon": None, "armor": None, "trinket": None})
    ch.setdefault("status_effects", [])
    ch.setdefault("injury_state", "healthy")
    ch.setdefault("available", True)
    ch.setdefault("tactics", {})
    # 技能模式已废弃；迁移旧存档时直接清除，后续通过更细粒度规则表达资源策略。
    ch["tactics"].pop("skill_mode", None)
    default_tactics = default_tactics_for_class(ch.get("class_id"))
    if "target_priority" not in ch["tactics"]:
        ch["tactics"]["target_priority"] = default_tactics["target_priority"]
    initiative_skill = ch["tactics"].get("initiative_skill", default_tactics["initiative_skill"])
    if not isinstance(initiative_skill, str):
        initiative_skill = ""
    if initiative_skill:
        skill = data["skill_by_id"].get(initiative_skill, {})
        if initiative_skill not in ch.get("learned_skills", []) or not is_initiative_skill(skill):
            initiative_skill = ""
    ch["tactics"]["initiative_skill"] = initiative_skill
    if "skill_priority" not in ch["tactics"] or not isinstance(ch["tactics"].get("skill_priority"), list):
        ch["tactics"]["skill_priority"] = copy.deepcopy(default_tactics["skill_priority"])
    ch["tactics"]["skill_priority"] = clean_tactic_skill_list(ch["tactics"].get("skill_priority", []), set(ch.get("learned_skills", [])), 8)
    if "opening_skill_priority" not in ch["tactics"] or not isinstance(ch["tactics"].get("opening_skill_priority"), list):
        ch["tactics"]["opening_skill_priority"] = copy.deepcopy(default_tactics["opening_skill_priority"])
    ch["tactics"]["opening_skill_priority"] = clean_tactic_skill_list(ch["tactics"].get("opening_skill_priority", []), set(ch.get("learned_skills", [])), 4)
    if "defense_skill_by_type" not in ch["tactics"] or not isinstance(ch["tactics"].get("defense_skill_by_type"), dict):
        ch["tactics"]["defense_skill_by_type"] = copy.deepcopy(default_tactics["defense_skill_by_type"])
    ch["tactics"]["defense_skill_by_type"] = clean_defense_skill_map(
        ch["tactics"].get("defense_skill_by_type", {}),
        set(ch.get("learned_skills", [])),
        data,
    )
    max_mana = int(attribute_derived_stats(ch["attributes"]).get("mana", 0))
    ch["max_mana"] = max_mana
    ch["mana"] = max(0, min(max_mana, int(ch.get("mana", max_mana))))
    ch["attribute_names"] = ATTRIBUTE_NAMES
    return ch


def attribute_derived_stats(attributes: dict[str, int]) -> dict[str, int]:
    strength = int(attributes.get("strength", 8))
    constitution = int(attributes.get("constitution", 8))
    dexterity = int(attributes.get("dexterity", 8))
    agility = int(attributes.get("agility", 8))
    intelligence = int(attributes.get("intelligence", 8))
    willpower = int(attributes.get("willpower", 8))
    perception = int(attributes.get("perception", 8))
    charisma = int(attributes.get("charisma", 8))
    return {
        "hp_bonus": strength + constitution * 2,
        "attack_bonus": max(0, strength // 4 + dexterity // 8),
        "defense_bonus": max(0, constitution // 4 + strength // 10),
        "speed_bonus": max(0, agility // 8 + perception // 14),
        "accuracy_bonus": max(0, (dexterity + perception) // 6),
        "evasion_bonus": max(0, (agility + dexterity) // 8),
        "mana": intelligence * 2 + willpower + charisma // 2,
        "melee_score": int(round(attribute_focus_score(attributes, "melee"))),
        "ranged_score": int(round(attribute_focus_score(attributes, "ranged"))),
        "finesse_score": int(round(attribute_focus_score(attributes, "finesse"))),
        "magic_score": int(round(attribute_focus_score(attributes, "magic"))),
        "faith_score": int(round(attribute_focus_score(attributes, "faith"))),
        "healing_score": int(round(attribute_focus_score(attributes, "healing"))),
        "guard_score": int(round(attribute_focus_score(attributes, "guard"))),
        "tactics_score": int(round(attribute_focus_score(attributes, "tactics"))),
    }


def attribute_focus_score(attributes: dict[str, int], focus: str | None) -> float:
    weights = SKILL_FOCUS_WEIGHTS.get(focus or "", {})
    if not weights:
        return 0.0
    return sum(float(attributes.get(k, 8)) * w for k, w in weights.items())


def skill_level_requirement(skill: dict[str, Any]) -> int:
    return int(skill.get("level_required", 1))


def active_skill_ids_for_character(ch: dict[str, Any]) -> list[str]:
    normalize_character(ch)
    learned = set(ch.get("learned_skills", []))
    return [sid for sid in ch.get("skills", []) if sid in learned] or ["basic_attack"]


def skill_unlock_status(ch: dict[str, Any], skill_id: str) -> tuple[bool, str]:
    learned = set(ch.get("learned_skills", []))
    if skill_id in learned:
        return False, "已学会"
    node = class_skill_tree_node_map(ch.get("class_id")).get(skill_id)
    if not node:
        return False, "不在本职业技能树中"
    missing = [sid for sid in node.get("prerequisites", []) if sid not in learned]
    if missing:
        data = load_data()
        names = [data["skill_by_id"].get(sid, {}).get("name", sid) for sid in missing]
        return False, f"需要先学习：{'、'.join(names)}"
    cost = int(node.get("cost", 1))
    if int(ch.get("skill_points", 0)) < cost:
        return False, f"技能点不足：需要 {cost} 点"
    return True, "可学习"


def skill_public_summary(ch: dict[str, Any]) -> list[dict[str, Any]]:
    normalize_character(ch)
    data = load_data()
    learned = set(ch.get("learned_skills", []))
    tree = class_skill_tree_node_map(ch.get("class_id"))
    rows: list[dict[str, Any]] = []
    for sid in ch.get("skills", []):
        skill = data["skill_by_id"].get(sid)
        if not skill:
            continue
        req = skill_level_requirement(skill)
        node = tree.get(sid, {})
        prereqs = list(node.get("prerequisites", [])) if isinstance(node.get("prerequisites", []), list) else []
        unlockable, unlock_reason = skill_unlock_status(ch, sid)
        rows.append({
            "id": sid,
            "name": skill.get("name", sid),
            "type": skill.get("type", "damage"),
            "category": skill.get("category", ""),
            "tags": copy.deepcopy(skill.get("tags", [])),
            "discipline": skill.get("discipline", ""),
            "description": skill.get("description", ""),
            "damage_types": copy.deepcopy(skill.get("damage_types", [])),
            "attack_type": attack_type_for_skill(skill),
            "defense_types": defense_types_for_skill(skill),
            "status_effects": copy.deepcopy(skill.get("status_effects", [])),
            "uses_per_dungeon": int(skill.get("uses_per_dungeon", 999)),
            "level_required": req,
            "tree_tier": int(node.get("tier", req)),
            "tree_x": node.get("x"),
            "tree_y": node.get("y"),
            "skill_point_cost": int(node.get("cost", 0 if sid == "basic_attack" else 1)),
            "prerequisites": prereqs,
            "prerequisite_names": [data["skill_by_id"].get(x, {}).get("name", x) for x in prereqs],
            "learned": sid in learned,
            "unlockable": unlockable,
            "unlock_reason": unlock_reason,
            "attribute_focus": skill.get("attribute_focus", ""),
            "attribute_scale": skill.get("attribute_scale", 0),
            "power": skill.get("power", 0),
            "accuracy_modifier": skill.get("accuracy_modifier", 0),
            "target_rule": skill.get("target_rule", ""),
            "range": skill.get("range", ""),
            "target_count": skill.get("target_count"),
            "ignore_defense": skill.get("ignore_defense", 0),
            "defense_factor": skill.get("defense_factor"),
            "crit_chance": skill.get("crit_chance", 0),
            "crit_multiplier": skill.get("crit_multiplier", 1.35),
            "execute_bonus": skill.get("execute_bonus", 0),
            "bonus_vs_status": copy.deepcopy(skill.get("bonus_vs_status", [])),
            "status_bonus": skill.get("status_bonus", 0),
            "cleanse_statuses": copy.deepcopy(skill.get("cleanse_statuses", [])),
            "mana_cost": int(skill.get("mana_cost", 0)),
            "speed_formula": copy.deepcopy(skill.get("speed_formula")) if isinstance(skill.get("speed_formula"), dict) else None,
            "is_initiative_skill": is_initiative_skill(skill),
        })
    return rows


def create_character(class_id: str, name: str, char_id: str | None = None) -> dict[str, Any]:
    data = load_data()
    c = copy.deepcopy(data["class_by_id"][class_id])
    stats = stat_block_for_class(c, 1)
    ch = {
        "id": char_id or make_id("ch"),
        "name": name,
        "class_id": class_id,
        "class_name": c["name"],
        "role": c.get("role", ""),
        "level": 1,
        "exp": 0,
        "attributes": attribute_block_for_class(c, 1),
        "hp": stats["max_hp"],
        "max_hp": stats["max_hp"],
        "base_stats": stats,
        "base_resistances": copy.deepcopy(c.get("resistances", {})),
        "skills": class_skill_ids(c),
        "learned_skills": clean_learned_skill_ids(class_id, class_auto_learn_skill_ids(class_id)),
        "skill_points": 0,
        "equipment": {"weapon": None, "armor": None, "trinket": None},
        "status_effects": [],
        "injury_state": "healthy",
        "available": True,
        "tactics": default_tactics_for_class(class_id),
    }
    derived = attribute_derived_stats(ch["attributes"])
    ch["max_hp"] = int(ch["base_stats"].get("max_hp", 1)) + derived["hp_bonus"]
    ch["hp"] = ch["max_hp"]
    ch["max_mana"] = int(derived.get("mana", 0))
    ch["mana"] = ch["max_mana"]
    return ch


def default_state(seed: int | None = None) -> dict[str, Any]:
    data = load_data()
    run_seed = seed if seed is not None else random.randint(100000, 99999999)
    state: dict[str, Any] = {
        "schema_version": 3,
        "attribute_system_version": 1,
        "run_seed": run_seed,
        "day": 1,
        "max_day": 30,
        "gold": 160,
        "materials": {"leather": 2, "ore": 2, "venom_sac": 0, "cloth": 0},
        "consumables": {"healing_potion": 3, "antidote": 2},
        "characters": [],
        "formation": {},  # legacy alias for team_1; kept for older saves/API clients
        "formations": {tid: {} for tid in TEAM_IDS},
        "retreat_strategy": "standard",
        "tactic_schemes": [],
        "layer_tactics": {},
        "inventory": [],
        "active_dungeons": [],
        "expedition_plan": [],
        "reports": [],
        "shop": {"items": [], "recruits": []},
        "last_result": None,
        "victory": False,
        "defeat": False,
        "defeat_reason": None,
        "final_unlocked": False,
        "next_counters": {"dungeon": 1, "plan": 1, "report": 1},
        "debug_log": [],
    }
    preset = data.get("preset", {})
    fallback_names = ["队员一", "队员二", "队员三", "队员四", "队员五", "队员六"]
    roster = preset.get("starter_roster") or [
        {"class_id": c["id"], "name": fallback_names[idx] if idx < len(fallback_names) else c.get("name", c["id"])}
        for idx, c in enumerate(data["classes"][:6])
    ]
    for idx, row in enumerate(roster):
        cid = row["class_id"] if isinstance(row, dict) else row[0]
        name = row["name"] if isinstance(row, dict) else row[1]
        ch = create_character(cid, name, f"ch_{idx+1}")
        if idx >= 4:
            ch["available"] = True
        state["characters"].append(ch)
    starter_equipment = preset.get("starter_equipment") or [
        {"owner": "ch_1", "equipment_id": "iron_sword"},
        {"owner": "ch_1", "equipment_id": "chainmail"},
        {"owner": "ch_2", "equipment_id": "oak_staff"},
        {"owner": "ch_2", "equipment_id": "leather_armor"},
        {"owner": "ch_3", "equipment_id": "hunting_bow"},
        {"owner": "ch_3", "equipment_id": "leather_armor"},
        {"owner": "ch_4", "equipment_id": "balanced_dagger"},
        {"owner": "ch_4", "equipment_id": "leather_armor"},
        {"owner": "ch_5", "equipment_id": "heavy_shield"},
        {"owner": "ch_6", "equipment_id": "fire_wand"},
        {"owner": None, "equipment_id": "poison_ring"},
        {"owner": None, "equipment_id": "eagle_eye"},
    ]
    for row in starter_equipment:
        owner = row.get("owner") if isinstance(row, dict) else row[0]
        eq_id = row.get("equipment_id") if isinstance(row, dict) else row[1]
        if not eq_id:
            continue
        item = instance_equipment(eq_id)
        state["inventory"].append(item)
        if owner:
            equip_item(state, owner, item["instance_id"], validate_class=False)
    starter_formations = preset.get("starter_formations") or {
        "team_1": {
            "r0c1": "ch_1",
            "r1c1": "ch_2",
            "r2c0": "ch_3",
            "r2c2": "ch_4",
        },
        "team_2": {
            "r0c1": "ch_5",
            "r2c1": "ch_6",
        },
    }
    for tid in TEAM_IDS:
        state["formations"][tid] = copy.deepcopy(starter_formations.get(tid, {}))
    state["formation"] = copy.deepcopy(state["formations"]["team_1"])
    refresh_shop(state)
    world_refresh(state, first_day=True)
    return state


def get_character(state: dict[str, Any], char_id: str) -> dict[str, Any] | None:
    return next((c for c in state["characters"] if c["id"] == char_id), None)


def get_item(state: dict[str, Any], item_id: str) -> dict[str, Any] | None:
    return next((i for i in state["inventory"] if i["instance_id"] == item_id), None)


def get_dungeon(state: dict[str, Any], dungeon_id: str) -> dict[str, Any] | None:
    return next((d for d in state["active_dungeons"] if d["id"] == dungeon_id and not d.get("expired")), None)


def skill_tags(skill: dict[str, Any]) -> list[str]:
    tags = skill.get("tags", [])
    if isinstance(tags, list):
        return [str(t) for t in tags]
    return []


def is_initiative_skill(skill: dict[str, Any]) -> bool:
    tags = set(skill_tags(skill))
    return bool({"initiative", "先攻"} & tags) or isinstance(skill.get("speed_formula"), dict)


def speed_formula_text(formula: dict[str, Any]) -> str:
    parts: list[str] = []
    normal_weight = float(formula.get("normal_speed_weight", formula.get("speed_weight", 0)))
    if normal_weight:
        parts.append(f"常规速度×{normal_weight:g}")
    attr_weights = formula.get("attribute_weights") or formula.get("attributes") or {}
    if isinstance(attr_weights, dict):
        for key, weight in attr_weights.items():
            label = ATTRIBUTE_NAMES.get(str(key), str(key))
            parts.append(f"{label}×{float(weight):g}")
    derived_weights = formula.get("derived_weights") or formula.get("derived") or {}
    if isinstance(derived_weights, dict):
        for key, weight in derived_weights.items():
            label = STAT_LABELS.get(str(key), str(key))
            parts.append(f"{label}×{float(weight):g}")
    level_weight = float(formula.get("level_weight", 0))
    if level_weight:
        parts.append(f"等级×{level_weight:g}")
    flat = float(formula.get("flat", formula.get("base", 0)))
    if flat:
        parts.append(f"{flat:g}")
    return " + ".join(parts) or "常规速度"


def calculate_speed_formula(skill: dict[str, Any], normal_speed: int, attributes: dict[str, int], derived: dict[str, int], level: int) -> dict[str, Any] | None:
    formula = skill.get("speed_formula")
    if not isinstance(formula, dict):
        return None
    value = float(formula.get("flat", formula.get("base", 0)))
    value += normal_speed * float(formula.get("normal_speed_weight", formula.get("speed_weight", 0)))
    value += level * float(formula.get("level_weight", 0))
    attr_weights = formula.get("attribute_weights") or formula.get("attributes") or {}
    if isinstance(attr_weights, dict):
        for key, weight in attr_weights.items():
            value += float(attributes.get(str(key), 0)) * float(weight)
    derived_weights = formula.get("derived_weights") or formula.get("derived") or {}
    if isinstance(derived_weights, dict):
        for key, weight in derived_weights.items():
            value += float(derived.get(str(key), 0)) * float(weight)
    value = clamp(value, float(formula.get("min", 1)), float(formula.get("max", 99)))
    return {
        "skill_id": skill.get("id"),
        "skill_name": skill.get("name", skill.get("id", "先攻技能")),
        "label": formula.get("label") or skill.get("name", "先攻公式"),
        "value": int(round(value)),
        "raw_value": round(value, 2),
        "normal_speed": int(normal_speed),
        "formula": speed_formula_text(formula),
        "is_default": False,
    }


def default_speed_formula_result(normal_speed: int) -> dict[str, Any]:
    return {
        "skill_id": "default_speed_formula",
        "skill_name": "默认速度公式",
        "label": "常规速度",
        "value": int(normal_speed),
        "raw_value": int(normal_speed),
        "normal_speed": int(normal_speed),
        "formula": "常规速度",
        "is_default": True,
    }


def initiative_speed_for_character(char: dict[str, Any], normal_speed: int, attributes: dict[str, int], derived: dict[str, int]) -> dict[str, Any]:
    data = load_data()
    selected = str(char.get("tactics", {}).get("initiative_skill") or "")
    if not selected:
        return default_speed_formula_result(normal_speed)
    if selected not in active_skill_ids_for_character(char):
        return default_speed_formula_result(normal_speed)
    skill = data["skill_by_id"].get(selected, {})
    if not is_initiative_skill(skill):
        return default_speed_formula_result(normal_speed)
    result = calculate_speed_formula(skill, normal_speed, attributes, derived, int(char.get("level", 1)))
    return result or default_speed_formula_result(normal_speed)


def effective_stats(state: dict[str, Any], char: dict[str, Any]) -> dict[str, Any]:
    normalize_character(char)
    stats = copy.deepcopy(char.get("base_stats", {}))
    attributes = {k: int(char.get("attributes", {}).get(k, 8)) for k in ATTRIBUTE_KEYS}
    derived = attribute_derived_stats(attributes)
    stats["max_hp"] = int(stats.get("max_hp", char.get("max_hp", 1))) + derived["hp_bonus"]
    stats["max_mana"] = int(derived.get("mana", 0))
    stats["attack"] = int(stats.get("attack", 0)) + derived["attack_bonus"]
    stats["defense"] = int(stats.get("defense", 0)) + derived["defense_bonus"]
    stats["speed"] = int(stats.get("speed", 0)) + derived["speed_bonus"]
    stats["accuracy"] = int(stats.get("accuracy", 80)) + derived["accuracy_bonus"]
    stats["evasion"] = int(stats.get("evasion", 0)) + derived["evasion_bonus"]
    resistances = {k: int(v) for k, v in char.get("base_resistances", {}).items()}
    special_effects: list[str] = []
    for item_id in char.get("equipment", {}).values():
        if not item_id:
            continue
        item = get_item(state, item_id)
        if not item:
            continue
        durability_ratio = item.get("durability", 0) / max(1, item.get("max_durability", 1))
        if durability_ratio <= 0:
            continue
        factor = 1.0 if durability_ratio > 0.25 else 0.5
        for k, v in item.get("stats", {}).items():
            stats[k] = stats.get(k, 0) + int(round(v * factor))
        for k, v in item.get("resistances", {}).items():
            resistances[k] = resistances.get(k, 0) + int(round(v * factor))
        special_effects.extend(item.get("special_effects", []))
    normal_speed = int(stats.get("speed", 0))
    initiative_skill = initiative_speed_for_character(char, normal_speed, attributes, derived)
    stats["speed"] = initiative_skill["value"]
    stats["initiative_skill"] = initiative_skill
    stats["normal_speed"] = normal_speed
    for key in DAMAGE_TYPES:
        resistances[key] = int(clamp(resistances.get(key, 0), -75, 100))
    stats["resistances"] = resistances
    stats["special_effects"] = special_effects
    stats["attributes"] = attributes
    stats["attribute_names"] = ATTRIBUTE_NAMES
    stats["attribute_icons"] = ATTRIBUTE_ICONS
    stats["derived"] = derived
    return stats


def equip_item(state: dict[str, Any], char_id: str, item_id: str | None, slot: str | None = None, validate_class: bool = True) -> None:
    char = get_character(state, char_id)
    if not char:
        raise ValueError("角色不存在")
    if item_id is None:
        if not slot:
            raise ValueError("卸下装备需要提供 slot")
        old = char["equipment"].get(slot)
        if old and (old_item := get_item(state, old)):
            old_item["equipped_by"] = None
        char["equipment"][slot] = None
        return
    item = get_item(state, item_id)
    if not item:
        raise ValueError("装备不存在")
    slot = slot or item["slot"]
    if slot != item["slot"]:
        raise ValueError("装备槽位不匹配")
    if validate_class:
        restriction = item.get("class_restriction") or []
        if restriction and char["class_id"] not in restriction:
            raise ValueError(f"{char['class_name']} 不能装备 {item['name']}")
    if item.get("equipped_by") and item["equipped_by"] != char_id:
        other = get_character(state, item["equipped_by"])
        if other:
            other["equipment"][slot] = None
    old_id = char["equipment"].get(slot)
    if old_id and (old := get_item(state, old_id)):
        old["equipped_by"] = None
    char["equipment"][slot] = item_id
    item["equipped_by"] = char_id


def refresh_shop(state: dict[str, Any]) -> None:
    data = load_data()
    rng = random.Random(stable_seed(state["run_seed"], "shop", state["day"]))
    equipment_pool = data["equipment"]
    weighted = []
    for e in equipment_pool:
        tier = 1
        if e.get("rarity") == "uncommon":
            tier = 4
        if e.get("rarity") == "rare":
            tier = 8
        if tier <= max(2, state["day"] // 4 + 1):
            weighted.append(e)
    items = []
    for e in rng.sample(weighted, k=min(5, len(weighted))):
        items.append({"shop_id": make_id("shop"), "kind": "equipment", "template_id": e["id"], "name": e["name"], "slot": e["slot"], "cost": int(e.get("cost", 50) * (0.9 + rng.random() * 0.25)), "summary": format_equipment_summary(e)})
    consumables = [
        {"shop_id": make_id("shop"), "kind": "consumable", "template_id": "healing_potion", "name": "治疗药水", "cost": 25, "summary": "挑战中低血量时自动回复少量 HP（MVP 简化为库存资源）"},
        {"shop_id": make_id("shop"), "kind": "consumable", "template_id": "antidote", "name": "解毒剂", "cost": 18, "summary": "用于补充解毒准备（MVP 简化为库存资源）"},
    ]
    items.extend(consumables)
    preset = data.get("preset", {})
    recruit_classes = preset.get("recruit_pool") or [c["id"] for c in data["classes"]]
    recruits = []
    names = preset.get("recruit_names") or ["伊芙", "莱恩", "卡洛", "薇拉", "塔克", "米娜", "洛特", "珂赛"]
    for i in range(3):
        cid = rng.choice(recruit_classes)
        c = data["class_by_id"][cid]
        recruits.append({
            "candidate_id": make_id("rec"),
            "class_id": cid,
            "class_name": c["name"],
            "class_meta": class_preset_meta(cid),
            "name": rng.choice(names),
            "level": max(1, state["day"] // 8 + rng.randint(0, 1)),
            "cost": 85 + 25 * max(0, state["day"] // 7),
            "role": c.get("role", ""),
        })
    state["shop"] = {"items": items, "recruits": recruits}


def format_equipment_summary(e: dict[str, Any]) -> str:
    parts = []
    for k, v in e.get("stats", {}).items():
        parts.append(f"{STAT_NAMES.get(k, k)} {v:+}")
    for k, v in e.get("resistances", {}).items():
        parts.append(f"{DAMAGE_TYPE_NAMES.get(k, k)}抗 {v:+}")
    for effect in e.get("special_effects", []):
        parts.append(SPECIAL_EFFECT_NAMES.get(effect, effect.replace("_", " ")))
    return "，".join(parts) or "基础装备"


def spawn_dungeon_instance(state: dict[str, Any], template_id: str, rng: random.Random | None = None, fixed_final: bool = False) -> dict[str, Any]:
    data = load_data()
    template = copy.deepcopy(data["dungeon_by_id"][template_id])
    rng = rng or random.Random(stable_seed(state["run_seed"], "spawn", state["day"], state["next_counters"]["dungeon"]))
    affix_ids: list[str] = []
    if not template.get("is_final") and template.get("possible_affixes"):
        if rng.random() < 0.62:
            affix_ids.append(rng.choice(template["possible_affixes"]))
        if state["day"] >= 15 and rng.random() < 0.18:
            extra = rng.choice(template["possible_affixes"])
            if extra not in affix_ids:
                affix_ids.append(extra)
    affixes = [data["affix_by_id"][a] for a in affix_ids]
    danger = template["base_danger"] + sum(a.get("danger_delta", 0) for a in affixes)
    life_days = template.get("life_days", 3)
    if any("short_life" in a.get("mechanics", []) for a in affixes):
        life_days = max(1, life_days - 1)
    instance_number = state["next_counters"]["dungeon"]
    state["next_counters"]["dungeon"] += 1
    instance = {
        "id": f"dg_{instance_number:03d}",
        "template_id": template_id,
        "name": template["name"],
        "theme": template["theme"],
        "spawn_day": state["day"],
        "remaining_days": life_days if not fixed_final else 99,
        "reward_charges": 1,
        "danger_level": danger,
        "layer_count": template["layer_count"],
        "affixes": [{"id": a["id"], "name": a["name"], "description": a["description"], "mechanics": a.get("mechanics", [])} for a in affixes],
        "public_info": {"threats": template["public_threats"], "main_rewards": template["main_rewards"], "recommended_level": template["recommended_level"], "estimated_layers": template["layer_count"]},
        "scout_info": None,
        "revealed_info": [],
        "challenged": False,
        "cleared": False,
        "expired": False,
        "is_final": bool(template.get("is_final")),
    }
    state["active_dungeons"].append(instance)
    return instance


def available_template_ids_for_day(day: int) -> list[str]:
    ids = ["spider_nest", "abandoned_mine"]
    if day >= 4:
        ids += ["bandit_camp"]
    if day >= 7:
        ids += ["beast_den"]
    if day >= 11:
        ids += ["ancient_tomb"]
    if day >= 16:
        ids += ["lava_rift"]
    return ids


def world_refresh(state: dict[str, Any], first_day: bool = False) -> None:
    if not first_day:
        for d in state["active_dungeons"]:
            if d.get("is_final") or d.get("cleared"):
                continue
            d["remaining_days"] -= 1
            if d["remaining_days"] <= 0:
                d["expired"] = True
        state["active_dungeons"] = [d for d in state["active_dungeons"] if not d.get("expired") and not (d.get("cleared") and d.get("reward_charges", 0) <= 0)]
    if state["day"] >= 25 and not state.get("final_unlocked"):
        spawn_dungeon_instance(state, "final_bastion", fixed_final=True)
        state["final_unlocked"] = True
    desired = 3 if state["day"] < 5 else 4
    if state["day"] >= 15:
        desired = 5
    rng = random.Random(stable_seed(state["run_seed"], "world", state["day"], len(state["active_dungeons"])))
    pool = available_template_ids_for_day(state["day"])
    while len([d for d in state["active_dungeons"] if not d.get("is_final")]) < desired:
        template_id = rng.choice(pool)
        spawn_dungeon_instance(state, template_id, rng=rng)
    refresh_shop(state)
    state["expedition_plan"] = []


def ensure_formations(state: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Migrate/normalize old single-party saves into two independent teams."""
    formations = state.get("formations")
    if not isinstance(formations, dict):
        formations = {}
    legacy = state.get("formation") if isinstance(state.get("formation"), dict) else {}
    normalized: dict[str, dict[str, str]] = {}
    for tid in TEAM_IDS:
        raw = formations.get(tid)
        if not isinstance(raw, dict):
            raw = legacy if tid == "team_1" else {}
        normalized[tid] = {cell: cid for cell, cid in raw.items() if cell in FORMATION_CELLS and cid}
    state["formations"] = normalized
    state["formation"] = copy.deepcopy(normalized["team_1"])
    return normalized


def formation_member_team_map(state: dict[str, Any]) -> dict[str, str]:
    formations = ensure_formations(state)
    out: dict[str, str] = {}
    for tid, formation in formations.items():
        for cid in formation.values():
            out[cid] = tid
    return out


def clean_formation(state: dict[str, Any], team_id: str, formation: dict[str, str | None], *, allow_empty: bool = True) -> dict[str, str]:
    if team_id not in TEAM_IDS:
        raise ValueError("未知队伍")
    cleaned: dict[str, str] = {}
    seen: set[str] = set()
    other_members = {
        cid
        for tid, f in ensure_formations(state).items()
        if tid != team_id
        for cid in f.values()
    }
    for cell, char_id in formation.items():
        if not char_id:
            continue
        if cell not in FORMATION_CELLS:
            raise ValueError(f"非法阵型格：{cell}")
        if char_id in seen:
            raise ValueError("同一角色不能占用多个格子")
        if char_id in other_members:
            other_tid = formation_member_team_map(state).get(char_id, "")
            other_ch = get_character(state, char_id)
            name = other_ch["name"] if other_ch else char_id
            raise ValueError(f"同一角色不能同时加入两支队伍：{name} 已在 {TEAM_LABELS.get(other_tid, other_tid)}")
        ch = get_character(state, char_id)
        if not ch:
            raise ValueError("角色不存在")
        if not ch.get("available", True):
            raise ValueError(f"{ch['name']} 当前不可出战")
        cleaned[cell] = char_id
        seen.add(char_id)
    if len(cleaned) > MAX_TEAM_SIZE:
        raise ValueError(f"每队最多上阵 {MAX_TEAM_SIZE} 人")
    if len(cleaned) == 0 and not allow_empty:
        raise ValueError("每支出征队至少需要 1 名角色")
    return cleaned


def clean_all_formations(state: dict[str, Any], formations_payload: dict[str, dict[str, str | None]]) -> dict[str, dict[str, str]]:
    """Validate a multi-team edit atomically so swaps between teams are allowed."""
    ensure_formations(state)
    cleaned: dict[str, dict[str, str]] = {}
    used_by_char: dict[str, str] = {}
    for tid in TEAM_IDS:
        raw = formations_payload.get(tid, state["formations"].get(tid, {}))
        if not isinstance(raw, dict):
            raise ValueError("阵型数据格式错误")
        team_cleaned: dict[str, str] = {}
        seen_in_team: set[str] = set()
        for cell, char_id in raw.items():
            if not char_id:
                continue
            if cell not in FORMATION_CELLS:
                raise ValueError(f"非法阵型格：{cell}")
            if char_id in seen_in_team:
                raise ValueError("同一角色不能占用多个格子")
            if char_id in used_by_char:
                ch = get_character(state, char_id)
                name = ch["name"] if ch else char_id
                raise ValueError(f"同一角色不能同时加入两支队伍：{name} 已在 {TEAM_LABELS.get(used_by_char[char_id], used_by_char[char_id])}")
            ch = get_character(state, char_id)
            if not ch:
                raise ValueError("角色不存在")
            if not ch.get("available", True):
                raise ValueError(f"{ch['name']} 当前不可出战")
            team_cleaned[cell] = char_id
            seen_in_team.add(char_id)
            used_by_char[char_id] = tid
        if len(team_cleaned) > MAX_TEAM_SIZE:
            raise ValueError(f"每队最多上阵 {MAX_TEAM_SIZE} 人")
        cleaned[tid] = team_cleaned
    return cleaned


def validate_team_ready(state: dict[str, Any], team_id: str) -> None:
    formation = ensure_formations(state).get(team_id, {})
    if not formation:
        raise ValueError(f"{TEAM_LABELS.get(team_id, team_id)} 尚未编队")
    for cid in formation.values():
        ch = get_character(state, cid)
        if not ch or not ch.get("available", True):
            raise ValueError(f"{TEAM_LABELS.get(team_id, team_id)} 包含不可出战成员")


def next_available_team_for_plan(state: dict[str, Any]) -> str | None:
    used = {a.get("team_id") for a in state.get("expedition_plan", [])}
    for tid in TEAM_IDS:
        if tid not in used:
            return tid
    return None


def tactic_scheme_by_id(state: dict[str, Any], scheme_id: str | None) -> dict[str, Any] | None:
    if not scheme_id:
        return None
    return next((row for row in ensure_tactic_schemes(state) if row["id"] == scheme_id), None)


def tactic_state_for_scheme(state: dict[str, Any], scheme_id: str | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return a combat-only state view with a saved tactic scheme applied.

    The selected scheme must affect combat calculations (default tactics, layer
    overrides, retreat policy), but it must not mutate the live save just because
    the player picked it for one expedition action.
    """
    if not scheme_id:
        return state, None
    scheme = tactic_scheme_by_id(state, scheme_id)
    if not scheme:
        raise ValueError("战术总方案不存在")
    scratch = copy.deepcopy(state)
    update_tactics(scratch, copy.deepcopy(scheme.get("tactics", {})))
    return scratch, scheme


def add_plan_action(state: dict[str, Any], action_type: str, dungeon_id: str, team_id: str | None = None, tactic_scheme_id: str | None = None) -> dict[str, Any]:
    if state.get("victory") or state.get("defeat"):
        raise ValueError("本局已经结束")
    if action_type not in {"scout", "challenge"}:
        raise ValueError("未知远征类型")
    ensure_formations(state)
    if len(state["expedition_plan"]) >= 2:
        raise ValueError("今日远征次数已用完")
    team_id = team_id or next_available_team_for_plan(state)
    if not team_id:
        raise ValueError("没有可用队伍：每支队伍每天只能出征一次")
    if team_id not in TEAM_IDS:
        raise ValueError("未知队伍")
    if any(a.get("team_id") == team_id for a in state.get("expedition_plan", [])):
        raise ValueError(f"{TEAM_LABELS[team_id]} 今日已经安排出征，不能重复出征")
    validate_team_ready(state, team_id)
    dungeon = get_dungeon(state, dungeon_id)
    if not dungeon:
        raise ValueError("副本不存在或已过期")
    scheme = None
    if action_type == "challenge":
        tactic_scheme_id = str(tactic_scheme_id or "")
        if tactic_scheme_id:
            scheme = tactic_scheme_by_id(state, tactic_scheme_id)
            if not scheme:
                raise ValueError("战术总方案不存在")
    action_id = f"plan_{state['next_counters']['plan']:03d}"
    state["next_counters"]["plan"] += 1
    action = {
        "id": action_id, "type": action_type, "dungeon_id": dungeon_id, "dungeon_name": dungeon["name"],
        "team_id": team_id, "team_name": TEAM_LABELS[team_id],
    }
    if scheme:
        action["tactic_scheme_id"] = scheme["id"]
        action["tactic_scheme_name"] = scheme["name"]
    state["expedition_plan"].append(action)
    return action


def clear_plan(state: dict[str, Any]) -> None:
    state["expedition_plan"] = []


def update_formation(state: dict[str, Any], formation: dict[str, str | None], team_id: str = "team_1") -> None:
    cleaned = clean_formation(state, team_id, formation)
    formations = ensure_formations(state)
    formations[team_id] = cleaned
    state["formations"] = formations
    state["formation"] = copy.deepcopy(formations["team_1"])


def update_formations(state: dict[str, Any], formations: dict[str, dict[str, str | None]]) -> None:
    cleaned = clean_all_formations(state, formations)
    state["formations"] = cleaned
    state["formation"] = copy.deepcopy(cleaned["team_1"])


def tactic_row_from_character(ch: dict[str, Any], tactics: dict[str, Any] | None = None) -> dict[str, Any]:
    normalize_character(ch)
    tactics = tactics if isinstance(tactics, dict) else ch.get("tactics", {})
    return {
        "character_id": ch["id"],
        "character_name": ch.get("name", ch["id"]),
        "class_id": ch.get("class_id", ""),
        "class_name": ch.get("class_name", ""),
        "target_priority": tactics.get("target_priority", default_target_priority_for_class(ch.get("class_id"))),
        "initiative_skill": tactics.get("initiative_skill", ""),
        "skill_priority": copy.deepcopy(tactics.get("skill_priority", [])),
        "opening_skill_priority": copy.deepcopy(tactics.get("opening_skill_priority", [])),
        "defense_skill_by_type": copy.deepcopy(tactics.get("defense_skill_by_type", {})),
    }


def tactic_layer_index(value: Any) -> int:
    try:
        idx = int(value)
    except (TypeError, ValueError):
        return 0
    return idx if 1 <= idx <= MAX_TACTIC_LAYERS else 0


def tactic_layer_options(state: dict[str, Any]) -> list[dict[str, Any]]:
    data = load_data()
    layer_counts = [int(d.get("layer_count", 0)) for d in data.get("dungeons", []) if isinstance(d, dict)]
    layer_counts.extend(int(d.get("layer_count", 0)) for d in state.get("active_dungeons", []) if isinstance(d, dict))
    max_layers = max(1, min(MAX_TACTIC_LAYERS, max(layer_counts or [5])))
    return [{"index": i, "label": f"第 {i} 层"} for i in range(1, max_layers + 1)]


def clean_tactic_row_for_character(ch: dict[str, Any], row: dict[str, Any], data: dict[str, Any], base: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate a character tactic row without necessarily mutating the character."""
    normalize_character(ch)
    known_skills = set(active_skill_ids_for_character(ch))
    result = copy.deepcopy(base if isinstance(base, dict) else ch.get("tactics", {}))
    result.pop("skill_mode", None)
    defaults = default_tactics_for_class(ch.get("class_id"))
    result.setdefault("target_priority", defaults["target_priority"])
    result.setdefault("initiative_skill", defaults["initiative_skill"])
    result.setdefault("skill_priority", copy.deepcopy(defaults["skill_priority"]))
    result.setdefault("opening_skill_priority", copy.deepcopy(defaults["opening_skill_priority"]))
    result.setdefault("defense_skill_by_type", copy.deepcopy(defaults["defense_skill_by_type"]))

    target = row.get("target_priority")
    if target:
        if target not in TARGET_LABELS:
            raise ValueError("未知目标优先级")
        result["target_priority"] = str(target)
    if "initiative_skill" in row:
        sid = str(row.get("initiative_skill") or "")
        if not sid:
            result["initiative_skill"] = ""
        else:
            skill = data["skill_by_id"].get(sid, {})
            active_skills = set(active_skill_ids_for_character(ch))
            if sid not in active_skills or sid == "basic_attack" or not is_initiative_skill(skill):
                raise ValueError("未知或未学会的先攻技能")
            result["initiative_skill"] = sid
    if "skill_priority" in row:
        result["skill_priority"] = clean_tactic_skill_list(row.get("skill_priority") or [], known_skills, 8)
    if "opening_skill_priority" in row:
        result["opening_skill_priority"] = clean_tactic_skill_list(row.get("opening_skill_priority") or [], known_skills, 4)
    if "defense_skill_by_type" in row:
        raw = row.get("defense_skill_by_type") or {}
        if not isinstance(raw, dict):
            raise ValueError("防御技能配置格式错误")
        result["defense_skill_by_type"] = clean_defense_skill_map(raw, known_skills, data)
    return {
        "target_priority": result.get("target_priority", defaults["target_priority"]),
        "initiative_skill": result.get("initiative_skill", ""),
        "skill_priority": copy.deepcopy(result.get("skill_priority", [])),
        "opening_skill_priority": copy.deepcopy(result.get("opening_skill_priority", [])),
        "defense_skill_by_type": copy.deepcopy(result.get("defense_skill_by_type", {})),
    }


def ensure_layer_tactics(state: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    raw = state.get("layer_tactics")
    if not isinstance(raw, dict):
        raw = {}
    data = load_data()
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for layer_key, rows in raw.items():
        idx = tactic_layer_index(layer_key)
        if not idx or not isinstance(rows, dict):
            continue
        clean_rows: dict[str, dict[str, Any]] = {}
        for cid, row in rows.items():
            ch = get_character(state, str(cid))
            if not ch or not isinstance(row, dict):
                continue
            clean_rows[ch["id"]] = clean_tactic_row_for_character(ch, row, data)
        if clean_rows:
            out[str(idx)] = clean_rows
    state["layer_tactics"] = out
    return out


def layer_tactics_view(state: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return copy.deepcopy(ensure_layer_tactics(state))


def effective_tactics_for_layer(state: dict[str, Any], ch: dict[str, Any], layer_index: int) -> dict[str, Any]:
    normalize_character(ch)
    base = copy.deepcopy(ch.get("tactics", {}))
    layer_index = tactic_layer_index(layer_index)
    if not layer_index:
        return base
    row = ensure_layer_tactics(state).get(str(layer_index), {}).get(ch["id"])
    if not isinstance(row, dict):
        return base
    return clean_tactic_row_for_character(ch, row, load_data(), base=base)


def effective_stats_with_tactics(state: dict[str, Any], ch: dict[str, Any], tactics: dict[str, Any]) -> dict[str, Any]:
    temp = copy.deepcopy(ch)
    temp["tactics"] = copy.deepcopy(tactics)
    return effective_stats(state, temp)


def apply_layer_tactics_to_party(state: dict[str, Any], party: list[Combatant], layer_index: int) -> list[str]:
    applied: list[str] = []
    layer_key = str(tactic_layer_index(layer_index))
    saved_rows = ensure_layer_tactics(state).get(layer_key, {}) if layer_key != "0" else {}
    for unit in party:
        if unit.get("side") != "party":
            continue
        ch = unit.get("source") or get_character(state, unit.get("id"))
        if not ch:
            continue
        tactics = effective_tactics_for_layer(state, ch, layer_index)
        if ch["id"] in saved_rows:
            applied.append(unit.get("name", unit.get("id", "")))
        stats = effective_stats_with_tactics(state, ch, tactics)
        unit["tactics"] = copy.deepcopy(tactics)
        unit["speed"] = int(stats.get("speed", unit.get("speed", 0)))
        unit["normal_speed"] = int(stats.get("normal_speed", unit.get("normal_speed", unit.get("speed", 0))))
        unit["initiative_skill"] = copy.deepcopy(stats.get("initiative_skill"))
    return [name for name in applied if name]


def current_tactics_payload(state: dict[str, Any]) -> dict[str, Any]:
    """Full team-level tactics payload suitable for saving as a scheme."""
    return {
        "retreat_strategy": state.get("retreat_strategy", "standard"),
        "characters": [tactic_row_from_character(ch) for ch in state.get("characters", [])],
        "layer_tactics": layer_tactics_view(state),
    }


def tactic_scheme_summary(tactics: dict[str, Any]) -> dict[str, int]:
    rows = tactics.get("characters", []) if isinstance(tactics, dict) else []
    if not isinstance(rows, list):
        rows = []
    layer_rows = []
    raw_layers = tactics.get("layer_tactics", {}) if isinstance(tactics, dict) else {}
    if isinstance(raw_layers, dict):
        for row_map in raw_layers.values():
            if isinstance(row_map, dict):
                layer_rows.extend(row for row in row_map.values() if isinstance(row, dict))
    def list_len(value: Any) -> int:
        return len(value) if isinstance(value, list) else 0
    def dict_len(value: Any) -> int:
        return len(value) if isinstance(value, dict) else 0
    return {
        "characters": len(rows),
        "layers": len(raw_layers) if isinstance(raw_layers, dict) else 0,
        "layer_characters": len(layer_rows),
        "initiative": sum(1 for row in rows + layer_rows if isinstance(row, dict) and row.get("initiative_skill")),
        "opening": sum(list_len(row.get("opening_skill_priority")) for row in rows + layer_rows if isinstance(row, dict)),
        "priority": sum(list_len(row.get("skill_priority")) for row in rows + layer_rows if isinstance(row, dict)),
        "defense": sum(dict_len(row.get("defense_skill_by_type")) for row in rows + layer_rows if isinstance(row, dict)),
    }


def ensure_tactic_schemes(state: dict[str, Any]) -> list[dict[str, Any]]:
    raw = state.get("tactic_schemes")
    if not isinstance(raw, list):
        raw = []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, row in enumerate(raw[:MAX_TACTIC_SCHEMES]):
        if not isinstance(row, dict):
            continue
        tactics = row.get("tactics")
        if not isinstance(tactics, dict):
            continue
        scheme_id = str(row.get("id") or f"tactic_{idx+1:02d}")
        if scheme_id in seen:
            scheme_id = make_id("tactic")
        seen.add(scheme_id)
        name = str(row.get("name") or f"战术方案 {idx+1}").strip()[:40] or f"战术方案 {idx+1}"
        created_at = int(row.get("created_at") or now_ms())
        updated_at = int(row.get("updated_at") or created_at)
        out.append({
            "id": scheme_id,
            "name": name,
            "created_at": created_at,
            "updated_at": updated_at,
            "tactics": copy.deepcopy(tactics),
        })
    state["tactic_schemes"] = out
    return out


def tactic_schemes_view(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "summary": tactic_scheme_summary(row.get("tactics", {})),
        }
        for row in ensure_tactic_schemes(state)
    ]


def save_tactic_scheme(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    schemes = ensure_tactic_schemes(state)
    scheme_id = str(payload.get("scheme_id") or payload.get("id") or "")
    tactic_payload = payload.get("tactics") if isinstance(payload.get("tactics"), dict) else current_tactics_payload(state)

    # Validate and normalize through the same path as active tactics, but on a copy so
    # saving a draft scheme does not silently change the currently active plan.
    scratch = copy.deepcopy(state)
    update_tactics(scratch, tactic_payload)
    clean_tactics = current_tactics_payload(scratch)

    existing = next((row for row in schemes if row["id"] == scheme_id), None) if scheme_id else None
    if not existing and len(schemes) >= MAX_TACTIC_SCHEMES:
        raise ValueError(f"战术方案最多保存 {MAX_TACTIC_SCHEMES} 个")
    default_name = f"战术方案 {len(schemes) + 1}"
    name = str(payload.get("name") or (existing or {}).get("name") or default_name).strip()[:40] or default_name
    timestamp = now_ms()
    if existing:
        existing["name"] = name
        existing["updated_at"] = timestamp
        existing["tactics"] = clean_tactics
        return copy.deepcopy(existing)
    row = {
        "id": make_id("tactic"),
        "name": name,
        "created_at": timestamp,
        "updated_at": timestamp,
        "tactics": clean_tactics,
    }
    schemes.append(row)
    return copy.deepcopy(row)


def load_tactic_scheme(state: dict[str, Any], scheme_id: str) -> dict[str, Any]:
    scheme = next((row for row in ensure_tactic_schemes(state) if row["id"] == scheme_id), None)
    if not scheme:
        raise ValueError("战术方案不存在")
    update_tactics(state, copy.deepcopy(scheme.get("tactics", {})))
    return copy.deepcopy(scheme)


def delete_tactic_scheme(state: dict[str, Any], scheme_id: str) -> None:
    schemes = ensure_tactic_schemes(state)
    before = len(schemes)
    state["tactic_schemes"] = [row for row in schemes if row["id"] != scheme_id]
    if len(state["tactic_schemes"]) == before:
        raise ValueError("战术方案不存在")


def update_tactics(state: dict[str, Any], payload: dict[str, Any]) -> None:
    data = load_data()
    if "retreat_strategy" in payload:
        strategy = payload["retreat_strategy"]
        if strategy not in RETREAT_THRESHOLDS:
            raise ValueError("未知撤退策略")
        state["retreat_strategy"] = strategy
    if "layer_tactics" in payload:
        raw_layers = payload.get("layer_tactics") or {}
        if not isinstance(raw_layers, dict):
            raise ValueError("分层战术配置格式错误")
        cleaned_layers: dict[str, dict[str, dict[str, Any]]] = {}
        for raw_layer, rows in raw_layers.items():
            idx = tactic_layer_index(raw_layer)
            if not idx:
                continue
            if not isinstance(rows, dict):
                raise ValueError("分层战术配置格式错误")
            layer_rows: dict[str, dict[str, Any]] = {}
            for cid, row in rows.items():
                ch = get_character(state, str(cid))
                if not ch:
                    continue
                if not isinstance(row, dict):
                    raise ValueError("角色分层战术配置格式错误")
                layer_rows[ch["id"]] = clean_tactic_row_for_character(ch, row, data)
            if layer_rows:
                cleaned_layers[str(idx)] = layer_rows
        state["layer_tactics"] = cleaned_layers
    layer_index = tactic_layer_index(payload.get("layer_index", payload.get("layer")))
    layer_rows = ensure_layer_tactics(state) if layer_index else None
    for row in payload.get("characters", []):
        ch = get_character(state, row.get("character_id"))
        if not ch:
            raise ValueError("角色不存在")
        normalize_character(ch)
        if layer_index:
            layer_key = str(layer_index)
            if row.get("clear_layer_tactic") or row.get("clear_layer_tactics"):
                if isinstance(layer_rows, dict):
                    layer_rows.get(layer_key, {}).pop(ch["id"], None)
                    if not layer_rows.get(layer_key):
                        layer_rows.pop(layer_key, None)
                continue
            current_layer = (layer_rows or {}).get(layer_key, {}).get(ch["id"], ch.get("tactics", {}))
            clean = clean_tactic_row_for_character(ch, row, data, base=current_layer)
            state.setdefault("layer_tactics", {}).setdefault(layer_key, {})[ch["id"]] = clean
        else:
            ch["tactics"] = clean_tactic_row_for_character(ch, row, data, base=ch.get("tactics", {}))
    if layer_index:
        ensure_layer_tactics(state)


def learn_skill(state: dict[str, Any], character_id: str, skill_id: str) -> dict[str, Any]:
    ch = get_character(state, character_id)
    if not ch:
        raise ValueError("角色不存在")
    normalize_character(ch)
    sid = str(skill_id or "")
    node = class_skill_tree_node_map(ch.get("class_id")).get(sid)
    if not node or sid not in ch.get("skills", []):
        raise ValueError("该技能不在本职业技能树中")
    if sid in ch.get("learned_skills", []):
        raise ValueError("技能已经学会")
    unlockable, reason = skill_unlock_status(ch, sid)
    if not unlockable:
        raise ValueError(reason)
    cost = int(node.get("cost", 1))
    ch["skill_points"] = max(0, int(ch.get("skill_points", 0)) - cost)
    ch["learned_skills"].append(sid)
    ch["learned_skills"] = clean_learned_skill_ids(ch.get("class_id"), ch["learned_skills"])
    normalize_character(ch)
    return ch


def buy_shop_item(state: dict[str, Any], shop_id: str) -> dict[str, Any]:
    item = next((i for i in state["shop"]["items"] if i["shop_id"] == shop_id), None)
    if not item:
        raise ValueError("商品不存在")
    if state["gold"] < item["cost"]:
        raise ValueError("金币不足")
    state["gold"] -= item["cost"]
    if item["kind"] == "equipment":
        eq = instance_equipment(item["template_id"])
        state["inventory"].append(eq)
        acquired = {"type": "equipment", "item": eq}
    else:
        state["consumables"][item["template_id"]] = state["consumables"].get(item["template_id"], 0) + 1
        acquired = {"type": "consumable", "id": item["template_id"], "name": item["name"]}
    state["shop"]["items"] = [i for i in state["shop"]["items"] if i["shop_id"] != shop_id]
    return acquired


def recruit_character(state: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    rec = next((r for r in state["shop"]["recruits"] if r["candidate_id"] == candidate_id), None)
    if not rec:
        raise ValueError("招募对象不存在")
    if state["gold"] < rec["cost"]:
        raise ValueError("金币不足")
    if len(state["characters"]) >= 8:
        raise ValueError("总角色栏位已满")
    state["gold"] -= rec["cost"]
    ch = create_character(rec["class_id"], rec["name"])
    while ch["level"] < rec.get("level", 1):
        level_up_character(ch)
    state["characters"].append(ch)
    state["shop"]["recruits"] = [r for r in state["shop"]["recruits"] if r["candidate_id"] != candidate_id]
    return ch


def ordered_party_members(state: dict[str, Any], team_id: str = "team_1") -> list[dict[str, Any]]:
    rows = []
    formation = ensure_formations(state).get(team_id, {})
    for cell, cid in formation.items():
        ch = get_character(state, cid)
        if ch and ch.get("available", True):
            rows.append((cell, ch))
    rows.sort(key=lambda x: x[0])
    return [ch for _, ch in rows]


def public_state_view(state: dict[str, Any]) -> dict[str, Any]:
    migrate_state(state)
    ensure_formations(state)
    return {
        "day": state["day"],
        "max_day": state["max_day"],
        "gold": state["gold"],
        "materials": state["materials"],
        "materials_display": {MATERIAL_NAMES.get(k, k): v for k, v in state["materials"].items()},
        "consumables": state.get("consumables", {}),
        "expedition_points_left": max(0, 2 - len(state["expedition_plan"])),
        "party_summary": party_summary(state),
        "active_dungeons_summary": dungeon_list_view(state),
        "shop_summary": state.get("shop", {}),
        "warnings": daily_warnings(state),
        "victory": state.get("victory", False),
        "defeat": state.get("defeat", False),
        "defeat_reason": state.get("defeat_reason"),
        "final_unlocked": state.get("final_unlocked", False),
        "last_result": state.get("last_result"),
        "retreat_strategy": state.get("retreat_strategy", "standard"),
        "retreat_strategy_label": RETREAT_LABELS.get(state.get("retreat_strategy", "standard"), "标准"),
    }


def preset_public_view() -> dict[str, Any]:
    """Frontend/admin friendly view of the active content preset."""
    data = load_data()
    preset = copy.deepcopy(data.get("preset", {}))
    return {
        "id": data.get("preset_id", preset.get("id", "")),
        "name": data.get("preset_name", preset.get("name", "")),
        "description": preset.get("description", ""),
        "path": data.get("preset_path", ""),
        "files": copy.deepcopy(preset.get("files", {})),
        "class_ui": copy.deepcopy(data.get("class_ui_by_id", {})),
        "starter_roster": copy.deepcopy(preset.get("starter_roster", [])),
        "starter_formations": copy.deepcopy(preset.get("starter_formations", {})),
        "starter_equipment": copy.deepcopy(preset.get("starter_equipment", [])),
        "recruit_pool": copy.deepcopy(preset.get("recruit_pool", [])),
        "recruit_names": copy.deepcopy(preset.get("recruit_names", [])),
        "skill_tree": copy.deepcopy(preset.get("skill_tree", {})),
        "classes": copy.deepcopy(data.get("classes", [])),
        "skills": copy.deepcopy(data.get("skills", [])),
        "equipment": copy.deepcopy(data.get("equipment", [])),
        "enemies": copy.deepcopy(data.get("enemies", [])),
        "dungeons": copy.deepcopy(data.get("dungeons", [])),
        "affixes": copy.deepcopy(data.get("affixes", [])),
        "skill_ai": copy.deepcopy(data.get("skill_ai_by_class_id", {})),
    }


def preset_list_view() -> dict[str, Any]:
    return {"active_preset_id": load_data().get("preset_id", ""), "presets": list_presets()}


def migrate_state(state: dict[str, Any]) -> dict[str, Any]:
    """Best-effort save migration for data-driven WOD attributes and skills."""
    rebuild_level_scaled_sheet = int(state.get("schema_version", 1)) < 3 or state.get("attribute_system_version") != 1
    for ch in state.get("characters", []):
        if rebuild_level_scaled_sheet:
            class_row = load_data()["class_by_id"].get(ch.get("class_id"))
            if class_row:
                ch["base_stats"] = stat_block_for_class(class_row, int(ch.get("level", 1)))
                ch["base_resistances"] = copy.deepcopy(class_row.get("resistances", {}))
                ch["attributes"] = attribute_block_for_class(class_row, int(ch.get("level", 1)))
        normalize_character(ch)
        stats = effective_stats(state, ch)
        ch["max_hp"] = int(stats.get("max_hp", ch.get("max_hp", 1)))
        ch["hp"] = min(int(ch.get("hp", ch["max_hp"])), ch["max_hp"])
        ch["max_mana"] = int(stats.get("max_mana", ch.get("max_mana", 0)))
        ch["mana"] = max(0, min(int(ch.get("mana", ch["max_mana"])), ch["max_mana"]))
    state["schema_version"] = 3
    state["attribute_system_version"] = 1
    ensure_formations(state)
    ensure_tactic_schemes(state)
    ensure_layer_tactics(state)
    return state


def party_summary(state: dict[str, Any]) -> dict[str, Any]:
    formations = ensure_formations(state)
    member_team = formation_member_team_map(state)
    members = []
    for ch in state["characters"]:
        normalize_character(ch)
        stats = effective_stats(state, ch)
        class_row = load_data()["class_by_id"].get(ch.get("class_id"), {})
        members.append({
            "id": ch["id"],
            "name": ch["name"],
            "class_id": ch["class_id"],
            "class_name": ch["class_name"],
            "class_meta": class_preset_meta(ch["class_id"]),
            "level": ch["level"],
            "exp": ch["exp"],
            "hp": ch["hp"],
            "max_hp": stats.get("max_hp", ch["max_hp"]),
            "mana": max(0, min(int(ch.get("mana", stats.get("max_mana", 0))), int(stats.get("max_mana", 0)))),
            "max_mana": int(stats.get("max_mana", ch.get("max_mana", 0))),
            "skill_points": int(ch.get("skill_points", 0)),
            "learned_skills": copy.deepcopy(ch.get("learned_skills", [])),
            "injury_state": ch.get("injury_state", "healthy"),
            "available": ch.get("available", True),
            "status_effects": ch.get("status_effects", []),
            "tactics": ch.get("tactics", {}),
            "equipment": ch.get("equipment", {}),
            "effective_stats": stats,
            "attributes": copy.deepcopy(ch.get("attributes", {})),
            "attribute_names": ATTRIBUTE_NAMES,
            "attribute_icons": ATTRIBUTE_ICONS,
            "derived_stats": copy.deepcopy(stats.get("derived", {})),
            "base_stats": copy.deepcopy(ch.get("base_stats", {})),
            "stat_growth": copy.deepcopy(class_row.get("stat_growth", {})),
            "attribute_growth": copy.deepcopy(class_row.get("attribute_growth", {})),
            "stat_breakdown": stat_breakdown_for_character(ch, class_row, stats),
            "attribute_breakdown": attribute_breakdown_for_character(ch, class_row),
            "skill_summary": skill_public_summary(ch),
            "in_formation": ch["id"] in member_team,
            "team_id": member_team.get(ch["id"]),
            "team_name": TEAM_LABELS.get(member_team.get(ch["id"], ""), ""),
        })
    return {
        "members": members,
        "formation": formations["team_1"],
        "formations": formations,
        "team_labels": TEAM_LABELS,
        "member_team": member_team,
        "max_team_size": MAX_TEAM_SIZE,
        "retreat_strategy": state.get("retreat_strategy", "standard"),
        "layer_tactics": layer_tactics_view(state),
        "tactic_layer_options": tactic_layer_options(state),
    }


def dungeon_list_view(state: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for d in state["active_dungeons"]:
        if d.get("expired"):
            continue
        attention = []
        if d["remaining_days"] <= 1 and not d.get("is_final"):
            attention.append("即将过期")
        if d["danger_level"] >= 5:
            attention.append("高风险")
        if d.get("scout_info"):
            attention.append("已侦察")
        if d.get("is_final"):
            attention.append("最终挑战")
        rows.append({
            "dungeon_id": d["id"],
            "name": d["name"],
            "theme": d["theme"],
            "danger_level": d["danger_level"],
            "remaining_days": d["remaining_days"],
            "reward_charges": d["reward_charges"],
            "estimated_layers": d["layer_count"],
            "main_rewards": d["public_info"]["main_rewards"],
            "public_threats": d["public_info"]["threats"],
            "affixes": d.get("affixes", []),
            "scouted": bool(d.get("scout_info")),
            "challenged": bool(d.get("challenged")),
            "cleared": bool(d.get("cleared")),
            "recommended_attention": attention,
            "is_final": bool(d.get("is_final")),
        })
    return sorted(rows, key=lambda x: (not x["is_final"], x["remaining_days"], -x["danger_level"]))


def dungeon_detail_view(state: dict[str, Any], dungeon_id: str) -> dict[str, Any]:
    d = get_dungeon(state, dungeon_id)
    if not d:
        raise ValueError("副本不存在")
    template = load_data()["dungeon_by_id"][d["template_id"]]
    known_layers = []
    if d.get("scout_info"):
        for i, layer in enumerate(template["layers"], start=1):
            known_layers.append({"index": i, "name": layer["name"], "type": layer["type"], "hint": layer.get("effect") or ", ".join(layer.get("enemies", layer.get("then_enemies", [])))})
    return {
        "dungeon_id": d["id"],
        "name": d["name"],
        "template_theme": d["theme"],
        "remaining_days": d["remaining_days"],
        "reward_charges": d["reward_charges"],
        "danger_level": d["danger_level"],
        "public_info": d["public_info"],
        "scout_info": d.get("scout_info"),
        "post_battle_info": d.get("revealed_info", []),
        "known_layers": known_layers,
        "known_enemies": sorted({eid for layer in template["layers"] for eid in layer.get("enemies", []) + layer.get("then_enemies", [])}) if d.get("scout_info") else [],
        "known_rewards": template["rewards"],
        "affixes": d.get("affixes", []),
        "risk_warnings": risk_warnings_for_dungeon(state, d),
        "available_actions": ["scout", "challenge"],
        "is_final": bool(d.get("is_final")),
    }


def risk_warnings_for_dungeon(state: dict[str, Any], d: dict[str, Any]) -> list[str]:
    warnings = []
    party = ordered_party_members(state)
    avg_level = sum(ch["level"] for ch in party) / max(1, len(party))
    if d["danger_level"] > avg_level + 2:
        warnings.append("危险等级明显高于当前平均等级，建议先侦察或准备装备。")
    theme = d["theme"]
    equipment_names = " ".join(i["name"] for i in state["inventory"] if i.get("equipped_by"))
    data = load_data()

    def party_skill_rows() -> Iterable[dict[str, Any]]:
        for ch in party:
            for sid in ch.get("skills", []):
                skill = data["skill_by_id"].get(sid)
                if skill:
                    yield skill

    has_cleanse = any(skill.get("type") == "cleanse" for skill in party_skill_rows())
    has_frontline = any(class_preset_meta(ch.get("class_id")).get("position") == "front" for ch in party)
    has_armor_answer = any(
        float(skill.get("ignore_defense", 0) or 0) > 0
        or "magic" in skill.get("damage_types", [])
        or any(s.get("type") in {"armor_break", "vulnerable"} for s in skill.get("status_effects", []))
        for skill in party_skill_rows()
    )
    if "毒" in theme and "毒抗" not in equipment_names and not has_cleanse:
        warnings.append("毒威胁明显，但当前上阵队伍缺少净化技能或毒抗装备。")
    if "后排" in theme and not has_frontline:
        warnings.append("后排威胁明显，但当前缺少保护型前排。")
    if "护甲" in theme and not has_armor_answer:
        warnings.append("高护甲敌人需要破甲或魔法输出。")
    if d["remaining_days"] <= 1 and not d.get("is_final"):
        warnings.append("副本即将过期：今天不处理就会消失。")
    return warnings


def daily_warnings(state: dict[str, Any]) -> list[str]:
    warnings = []
    if state["day"] >= 25 and not state.get("victory"):
        warnings.append("最终 Boss 已进入倒计时，建议开始针对毒 / 诅咒 / 后排威胁做准备。")
    expiring = [d["name"] for d in state["active_dungeons"] if d["remaining_days"] <= 1 and not d.get("is_final")]
    if expiring:
        warnings.append("即将过期副本：" + "、".join(expiring[:3]))
    active_ids = set(formation_member_team_map(state).keys())
    low_hp = [c["name"] for c in state["characters"] if c["id"] in active_ids and c["hp"] / max(1, c["max_hp"]) < 0.45]
    if low_hp:
        warnings.append("上阵成员 HP 偏低：" + "、".join(low_hp))
    return warnings

class Combatant(dict):
    pass


def make_player_combatants(state: dict[str, Any], team_id: str = "team_1") -> list[Combatant]:
    out: list[Combatant] = []
    formation = ensure_formations(state).get(team_id, {})
    formation_by_id = {cid: cell for cell, cid in formation.items()}
    for ch in ordered_party_members(state, team_id):
        normalize_character(ch)
        stats = effective_stats(state, ch)
        max_hp = int(stats.get("max_hp", ch["max_hp"]))
        hp = min(int(ch.get("hp", max_hp)), max_hp)
        max_mana = int(stats.get("max_mana", ch.get("max_mana", 0)))
        mana = max(0, min(int(ch.get("mana", max_mana)), max_mana))
        unit = Combatant({
            "id": ch["id"], "name": ch["name"], "side": "party", "class_id": ch["class_id"], "class_name": ch["class_name"],
            "team_id": team_id, "team_name": TEAM_LABELS.get(team_id, team_id),
            "level": ch["level"], "hp": hp, "max_hp": max_hp, "mana": mana, "max_mana": max_mana, "attack": int(stats.get("attack", 0)), "defense": int(stats.get("defense", 0)),
            "speed": int(stats.get("speed", 0)), "accuracy": int(stats.get("accuracy", 80)), "evasion": int(stats.get("evasion", 0)),
            "normal_speed": int(stats.get("normal_speed", stats.get("speed", 0))), "initiative_skill": copy.deepcopy(stats.get("initiative_skill")),
            "action_count": int(stats.get("action_count", 1)), "resistances": stats.get("resistances", {}), "special_effects": stats.get("special_effects", []),
            "attributes": copy.deepcopy(ch.get("attributes", {})), "derived_stats": copy.deepcopy(stats.get("derived", {})),
            "skills": active_skill_ids_for_character(ch), "skill_uses": {}, "statuses": copy.deepcopy(ch.get("status_effects", [])),
            "cell": formation_by_id.get(ch["id"], "r2c1"), "tactics": copy.deepcopy(ch.get("tactics", {})), "source": ch, "guarding": False,
        })
        out.append(unit)
    data = load_data()
    for unit in out:
        for sid in unit["skills"]:
            unit["skill_uses"][sid] = int(data["skill_by_id"].get(sid, {}).get("uses_per_dungeon", 999))
    return out


def make_enemy_combatants(enemy_ids: list[str], affix_mechanics: list[str], layer_index: int) -> list[Combatant]:
    data = load_data()
    out: list[Combatant] = []
    for idx, eid in enumerate(enemy_ids):
        e = copy.deepcopy(data["enemy_by_id"][eid])
        stats = e["stats"]
        if "armor_bonus" in affix_mechanics:
            stats["defense"] += 2
            stats["max_hp"] += 8
        if "boss_bonus" in affix_mechanics and ("boss" in e.get("tags", []) or idx == 0):
            stats["attack"] += 2
            stats["max_hp"] += 18
        cell = ["r0c1", "r1c0", "r1c2", "r2c1", "r0c0", "r0c2"][idx % 6]
        out.append(Combatant({
            "id": f"en_{layer_index}_{idx}_{eid}", "name": e["name"], "side": "enemy", "enemy_id": eid, "tags": e.get("tags", []),
            "hp": stats["max_hp"], "max_hp": stats["max_hp"], "attack": stats["attack"], "defense": stats["defense"],
            "speed": stats["speed"], "accuracy": stats["accuracy"], "evasion": stats["evasion"], "action_count": 1,
            "resistances": e.get("resistances", {}), "skills": copy.deepcopy(e.get("skills", [])), "statuses": [], "cell": cell, "guarding": False,
        }))
    if "extra_elite" in affix_mechanics and layer_index > 1 and out:
        base = copy.deepcopy(out[0])
        base["id"] += "_elite"
        base["name"] = "精英" + base["name"]
        base["hp"] = base["max_hp"] = int(base["max_hp"] * 1.35)
        base["attack"] += 2
        base["defense"] += 2
        base.setdefault("tags", []).append("elite")
        out.append(base)
    return out


def alive(units: Iterable[Combatant]) -> list[Combatant]:
    return [u for u in units if u.get("hp", 0) > 0]


def is_backline(unit: Combatant) -> bool:
    return unit.get("cell") in BACK_CELLS


def status_value(unit: Combatant, status_type: str) -> int:
    return sum(int(s.get("potency", 0)) for s in unit.get("statuses", []) if s.get("type") == status_type and s.get("duration", 0) > 0)


def has_status(unit: Combatant, status_type: str) -> bool:
    return status_value(unit, status_type) > 0


def hp_text(unit: Combatant) -> str:
    return f"{max(0, int(unit.get('hp', 0)))}/{int(unit.get('max_hp', 0))}"


def unit_snapshot(unit: Combatant) -> dict[str, Any]:
    """Compact, frontend-friendly combatant snapshot for battle replays."""
    return {
        "id": unit.get("id"),
        "name": unit.get("name"),
        "side": unit.get("side"),
        "team_id": unit.get("team_id"),
        "team_name": unit.get("team_name"),
        "class_id": unit.get("class_id"),
        "class_name": unit.get("class_name"),
        "enemy_id": unit.get("enemy_id"),
        "tags": copy.deepcopy(unit.get("tags", [])),
        "cell": unit.get("cell", ""),
        "hp": max(0, int(unit.get("hp", 0))),
        "max_hp": int(unit.get("max_hp", 0)),
        "hp_text": hp_text(unit),
        "mana": max(0, int(unit.get("mana", 0))),
        "max_mana": int(unit.get("max_mana", 0)),
        "attack": int(unit.get("attack", 0)),
        "defense": int(unit.get("defense", 0)),
        "speed": int(unit.get("speed", 0)),
        "normal_speed": int(unit.get("normal_speed", unit.get("speed", 0))),
        "initiative_skill": copy.deepcopy(unit.get("initiative_skill")),
        "statuses": copy.deepcopy(unit.get("statuses", [])),
    }


def lineup_snapshot(units: Iterable[Combatant]) -> list[dict[str, Any]]:
    return [unit_snapshot(u) for u in units]


def register_unit_names(report: dict[str, Any], units: Iterable[Combatant]) -> None:
    names = report.setdefault("unit_names", {})
    for unit in units:
        if unit.get("id"):
            names[unit["id"]] = unit.get("name", unit["id"])


def event_actor(unit: Combatant) -> dict[str, Any]:
    out = {
        "id": unit.get("id"),
        "name": unit.get("name"),
        "side": unit.get("side"),
        "cell": unit.get("cell", ""),
        "speed": int(unit.get("speed", 0)),
    }
    if "mana" in unit or "max_mana" in unit:
        out["mana"] = max(0, int(unit.get("mana", 0)))
        out["max_mana"] = int(unit.get("max_mana", 0))
    return out


def add_critical_event(report: dict[str, Any], text: str) -> None:
    if not text:
        return
    events = report.setdefault("critical_events", [])
    if text not in events and len(events) < 14:
        events.append(text)


def record_event(report: dict[str, Any], event: dict[str, Any]) -> None:
    """Append a structured event to the currently active round/pre-round sink."""
    if not event:
        return
    report["_event_seq"] = int(report.get("_event_seq", 0)) + 1
    event.setdefault("seq", report["_event_seq"])
    sink = report.get("_event_sink")
    if isinstance(sink, list):
        sink.append(copy.deepcopy(event))


def add_status(unit: Combatant, status: dict[str, Any]) -> None:
    existing = next((s for s in unit["statuses"] if s["type"] == status["type"]), None)
    new_status = {"type": status["type"], "duration": int(status.get("duration", 1)), "potency": int(status.get("potency", 0))}
    if existing:
        existing["duration"] = max(existing["duration"], new_status["duration"])
        existing["potency"] = max(existing.get("potency", 0), new_status["potency"])
    else:
        unit["statuses"].append(new_status)


def tick_statuses(unit: Combatant, stats: dict[str, Any], logs: list[str], report: dict[str, Any], phase: str = "round") -> None:
    if unit["hp"] <= 0:
        return
    for s in list(unit.get("statuses", [])):
        st = s.get("type")
        potency = int(s.get("potency", 0))
        if st in {"poison", "bleed", "burn"}:
            dtype = {"poison": "poison", "bleed": "physical", "burn": "fire"}[st]
            resist = effective_resistances(unit).get(dtype, 0)
            dmg = max(1, int(round(potency * (1 - resist / 100))))
            before_hp = int(unit["hp"])
            unit["hp"] = max(0, unit["hp"] - dmg)
            report["damage_by_type"][dtype] += dmg
            if unit["side"] == "party":
                report["damage_taken"][unit["id"]] += dmg
                report["status_stats"][st] += 1
            text = f"{unit['name']} 受到 {st} 持续伤害 {dmg}"
            logs.append(text)
            record_event(report, {
                "type": "dot",
                "text": text,
                "status": st,
                "damage_type": dtype,
                "amount": dmg,
                "target": event_actor(unit),
                "target_hp_before": before_hp,
                "target_hp_after": int(unit["hp"]),
                "target_statuses": copy.deepcopy(unit.get("statuses", [])),
            })
        elif st == "regeneration":
            before_hp = int(unit["hp"])
            unit["hp"] = min(unit["max_hp"], unit["hp"] + max(1, potency))
            healed = int(unit["hp"] - before_hp)
            if healed > 0:
                if unit["side"] == "party":
                    report["healing_done"][unit["id"]] += healed
                text = f"{unit['name']} 的再生恢复 {healed} HP"
                logs.append(text)
                record_event(report, {
                    "type": "hot",
                    "text": text,
                    "status": st,
                    "amount": healed,
                    "target": event_actor(unit),
                    "target_hp_before": before_hp,
                    "target_hp_after": int(unit["hp"]),
                    "target_statuses": copy.deepcopy(unit.get("statuses", [])),
                })
        if phase == "round":
            s["duration"] = int(s.get("duration", 1)) - 1
    unit["statuses"] = [s for s in unit.get("statuses", []) if s.get("duration", 0) > 0]
    if unit["hp"] <= 0:
        text = f"{unit['name']} 因持续伤害倒下"
        logs.append(text)
        record_event(report, {"type": "down", "text": text, "target": event_actor(unit), "target_hp_after": 0})
        add_critical_event(report, text)


def skill_mana_cost(skill: dict[str, Any]) -> int:
    return max(0, int(skill.get("mana_cost", 0)))


def has_mana_for_skill(unit: Combatant, skill: dict[str, Any]) -> bool:
    cost = skill_mana_cost(skill)
    return cost <= 0 or int(unit.get("mana", 0)) >= cost


def spend_skill_mana(actor: Combatant, skill: dict[str, Any], report: dict[str, Any]) -> bool:
    cost = skill_mana_cost(skill)
    if cost <= 0:
        return True
    before = int(actor.get("mana", 0))
    if before < cost:
        return False
    actor["mana"] = max(0, before - cost)
    report["mana_spent"][actor["id"]] += cost
    record_event(report, {
        "type": "mana_spend",
        "text": f"{actor['name']} 消耗 {cost} 法力施放 {skill.get('name', '技能')}（{actor['mana']}/{actor.get('max_mana', 0)}）",
        "actor": event_actor(actor),
        "skill": skill.get("name", "技能"),
        "amount": cost,
        "actor_mana_before": before,
        "actor_mana_after": int(actor["mana"]),
    })
    return True


def can_combatant_use_skill(unit: Combatant, skill_id: str, data: dict[str, Any]) -> bool:
    if skill_id not in unit.get("skills", []):
        return False
    remaining = int(unit.get("skill_uses", {}).get(skill_id, 0))
    if remaining <= 0:
        return False
    skill = data["skill_by_id"].get(skill_id, {})
    if skill.get("type") == "passive":
        return False
    if not has_mana_for_skill(unit, skill):
        return False
    return True


def should_use_priority_skill(skill: dict[str, Any], actor: Combatant, party: list[Combatant], enemies: list[Combatant]) -> bool:
    stype = skill.get("type")
    living_allies = alive(party)
    living_enemies = alive(enemies)

    def hp_pct(u: Combatant) -> float:
        return u["hp"] / max(1, u["max_hp"])

    if stype in {"damage", "debuff"}:
        return bool(living_enemies)
    if stype == "heal":
        return any(hp_pct(a) < 0.85 for a in living_allies)
    if stype == "cleanse":
        removable = set(skill.get("cleanse_statuses", ["poison", "curse", "burn", "bleed", "armor_break", "marked", "vulnerable", "slow", "enfeeble"]))
        return any(any(s.get("type") in removable for s in a.get("statuses", [])) for a in living_allies)
    if stype in {"guard", "buff", "support"}:
        statuses = [s.get("type") for s in skill.get("status_effects", [])]
        target_rule = skill.get("target_rule")
        if target_rule == "ally_low_hp":
            return any(hp_pct(a) < 0.85 for a in living_allies)
        if target_rule == "ally_status":
            return any(a.get("statuses") for a in living_allies)
        if target_rule == "ally_all" and statuses:
            return any(not all(has_status(a, st) for st in statuses if st) for a in living_allies)
        if skill.get("target_rule") == "self" and statuses:
            return not all(has_status(actor, st) for st in statuses if st)
        return True
    return True


def should_use_defense_response_skill(skill: dict[str, Any], actor: Combatant, party: list[Combatant]) -> bool:
    statuses = [s.get("type") for s in skill.get("status_effects", []) if s.get("type")]
    if skill.get("target_rule") == "self" and statuses:
        return not all(has_status(actor, st) for st in statuses)
    if skill.get("target_rule") == "ally_all" and statuses:
        return any(not all(has_status(a, st) for st in statuses) for a in alive(party))
    return True


def prioritize_preferred_target(targets: list[Combatant], preferred: Combatant | None) -> list[Combatant]:
    if not preferred:
        return targets
    return [t for t in targets if t is preferred] + [t for t in targets if t is not preferred]


def execute_player_skill(actor: Combatant, sid: str, party: list[Combatant], enemies: list[Combatant], rng: random.Random, logs: list[str], report: dict[str, Any], *, reason: str = "", preferred_ally: Combatant | None = None) -> bool:
    data = load_data()
    if not can_combatant_use_skill(actor, sid, data):
        return False
    skill = copy.deepcopy(data["skill_by_id"].get(sid))
    if not skill:
        return False
    if not spend_skill_mana(actor, skill, report):
        return False
    if sid != "basic_attack":
        actor["skill_uses"][sid] -= 1
    report["skill_usage"][actor["id"]][skill["name"]] += 1
    if reason:
        record_event(report, {
            "type": "tactic_trigger",
            "text": f"{actor['name']} 触发战术：{reason} → {skill['name']}",
            "actor": event_actor(actor),
            "skill": skill.get("name", sid),
            "reason": reason,
        })
    stype = skill.get("type")
    if stype == "heal":
        targets = prioritize_preferred_target(candidate_targets(party, skill.get("target_rule", "ally_low_hp"), actor), preferred_ally)
        for target in targets[:target_count_for_skill(skill, targets)]:
            apply_heal(actor, target, skill, logs, report)
    elif stype == "cleanse":
        targets = prioritize_preferred_target(candidate_targets(party, skill.get("target_rule", "ally_status"), actor), preferred_ally)
        for target in targets[:target_count_for_skill(skill, targets)]:
            apply_cleanse(actor, target, skill, logs, report)
    elif stype == "guard":
        apply_guard(actor, skill, logs, report)
    elif stype == "buff":
        apply_buff(actor, skill, logs, report)
    elif stype == "support":
        targets = prioritize_preferred_target(candidate_targets(party, skill.get("target_rule", "ally_all"), actor), preferred_ally)
        apply_support(actor, targets[:target_count_for_skill(skill, targets)], skill, logs, report)
    elif stype == "debuff":
        targets = candidate_targets(enemies, skill.get("target_rule", "highest_attack"), actor)
        if not targets:
            return False
        apply_debuff(actor, targets[:target_count_for_skill(skill, targets)], skill, rng, logs, report)
    else:
        tactic_rule = actor.get("tactics", {}).get("target_priority", "front")
        rule = tactic_rule if sid == "basic_attack" else (skill.get("target_rule") or tactic_rule)
        targets = candidate_targets(enemies, rule, actor)
        if not targets:
            return False
        for t in targets[:target_count_for_skill(skill, targets)]:
            resolve_damage(actor, t, skill, rng, logs, report)
    return True


def opening_skill_candidates(unit: Combatant) -> list[str]:
    return [sid for sid in unit.get("tactics", {}).get("opening_skill_priority", []) if sid]


def use_opening_skills(party: list[Combatant], enemies: list[Combatant], rng: random.Random, logs: list[str], report: dict[str, Any]) -> None:
    data = load_data()
    for unit in sorted(alive(party), key=lambda u: (-u.get("speed", 0), u.get("name", ""))):
        for sid in opening_skill_candidates(unit):
            skill = data["skill_by_id"].get(sid, {})
            if skill.get("type") == "heal" and not should_use_priority_skill(skill, unit, party, enemies):
                continue
            if skill.get("type") == "cleanse" and not should_use_priority_skill(skill, unit, party, enemies):
                continue
            if execute_player_skill(unit, sid, party, enemies, rng, logs, report, reason="开场技能"):
                break


def record_initiative_skill_events(party: list[Combatant], logs: list[str], report: dict[str, Any]) -> None:
    for unit in party:
        info = unit.get("initiative_skill")
        if not isinstance(info, dict) or info.get("is_default"):
            continue
        text = f"{unit['name']} 选择先攻技能 {info.get('skill_name')}，速度按「{info.get('label')}」计算为 {unit.get('speed', 0)}（常规 {info.get('normal_speed', unit.get('normal_speed', 0))}）"
        logs.append(text)
        record_event(report, {
            "type": "initiative_skill",
            "text": text,
            "actor": event_actor(unit),
            "skill": info.get("skill_name"),
            "speed": int(unit.get("speed", 0)),
            "normal_speed": int(info.get("normal_speed", unit.get("normal_speed", 0))),
            "formula": info.get("formula"),
        })


def incoming_defense_keys(skill: dict[str, Any]) -> list[str]:
    attack_type = attack_type_for_skill(skill)
    return [attack_type] if attack_type in DEFENSE_TRIGGER_LABELS else []


def maybe_use_defense_skill(target: Combatant, incoming_actor: Combatant, incoming_skill: dict[str, Any], rng: random.Random, logs: list[str], report: dict[str, Any]) -> None:
    if target.get("side") != "party" or target.get("hp", 0) <= 0:
        return
    defense_map = target.get("tactics", {}).get("defense_skill_by_type", {})
    if not isinstance(defense_map, dict) or not defense_map:
        return
    data = load_data()
    party = report.get("current_party", [])
    for key in incoming_defense_keys(incoming_skill):
        sid = defense_map.get(key)
        skill = data["skill_by_id"].get(sid or "", {})
        if not sid or skill.get("type") not in {"guard", "buff", "support"}:
            continue
        if key not in defense_types_for_skill(skill):
            continue
        if not should_use_defense_response_skill(skill, target, party):
            continue
        if execute_player_skill(target, sid, party, [incoming_actor], rng, logs, report, reason=f"防御·{DEFENSE_TRIGGER_LABELS.get(key, key)}", preferred_ally=target):
            return


def choose_player_skill(unit: Combatant, party: list[Combatant], enemies: list[Combatant]) -> str:
    data = load_data()
    skills = unit.get("skills", [])
    uses = unit.get("skill_uses", {})
    class_id = unit.get("class_id")
    living_allies = alive(party)
    living_enemies = alive(enemies)
    if not living_enemies:
        return "basic_attack"

    def can(skill_id: str) -> bool:
        return can_combatant_use_skill(unit, skill_id, data)

    def hp_pct(u: Combatant) -> float:
        return u["hp"] / max(1, u["max_hp"])

    def count_low(threshold: float) -> int:
        return sum(1 for a in living_allies if hp_pct(a) < threshold)

    def has_bad_status(u: Combatant) -> bool:
        return any(s["type"] in {"poison", "curse", "burn", "bleed", "armor_break", "marked", "vulnerable", "slow"} for s in u.get("statuses", []))

    def unstunned(targets: list[Combatant]) -> list[Combatant]:
        return [e for e in targets if not has_status(e, "stun")]

    def dangerous_enemies() -> list[Combatant]:
        return [e for e in living_enemies if e.get("attack", 0) >= 14 or "boss" in e.get("tags", []) or "elite" in e.get("tags", [])]

    def priority_enemies() -> list[Combatant]:
        return [e for e in living_enemies if "boss" in e.get("tags", []) or "elite" in e.get("tags", []) or e.get("attack", 0) >= 14]

    for skill_id in unit.get("tactics", {}).get("skill_priority", []):
        skill = data["skill_by_id"].get(skill_id, {})
        if can(skill_id) and should_use_priority_skill(skill, unit, party, enemies):
            return skill_id

    def hp_threshold(rule: dict[str, Any], fallback: float) -> float:
        return float(rule.get("hp_below", rule.get("threshold", fallback)))

    def rule_matches(rule: dict[str, Any]) -> bool:
        when = str(rule.get("when", "always"))
        if when == "always":
            return True
        if when == "setup":
            return True
        if when == "party_status_count_gte":
            return sum(1 for a in living_allies if has_bad_status(a)) >= int(rule.get("threshold", 1))
        if when == "party_low_count_gte":
            return count_low(float(rule.get("hp_below", 0.5))) >= int(rule.get("threshold", 1))
        if when == "lowest_ally_hp_below":
            if not living_allies:
                return False
            return hp_pct(min(living_allies, key=hp_pct)) < hp_threshold(rule, 0.5)
        if when == "self_hp_below":
            return hp_pct(unit) < float(rule.get("hp_below", rule.get("threshold", 0.5)))
        if when == "self_without_status":
            return not has_status(unit, str(rule.get("status", "")))
        if when == "self_hp_below_without_status":
            return hp_pct(unit) < float(rule.get("hp_below", 0.5)) and not has_status(unit, str(rule.get("status", "")))
        if when == "ally_backline_hp_below":
            return any(a.get("cell") in BACK_CELLS and hp_pct(a) < float(rule.get("hp_below", 0.78)) for a in living_allies)
        if when == "dangerous_enemy_unstunned":
            targets = dangerous_enemies()
            return bool(targets and unstunned(targets))
        if when == "enemy_tags_any":
            tags = set(rule.get("tags", []))
            return any(tags.intersection(e.get("tags", [])) for e in living_enemies)
        if when == "enemies_count_gte":
            return len(living_enemies) >= int(rule.get("threshold", 1))
        if when == "enemy_defense_gte":
            return any(e.get("defense", 0) >= int(rule.get("defense_gte", rule.get("threshold", 0))) for e in living_enemies)
        if when == "enemy_defense_gte_without_status":
            status = str(rule.get("status", ""))
            return any(e.get("defense", 0) >= int(rule.get("defense_gte", rule.get("threshold", 0))) and not has_status(e, status) for e in living_enemies)
        if when == "priority_enemy_without_status":
            targets = priority_enemies()
            status = str(rule.get("status", ""))
            return bool(targets and not any(has_status(e, status) for e in targets))
        if when == "armored_enemy_without_status":
            status = str(rule.get("status", "armor_break"))
            return any(e.get("defense", 0) >= int(rule.get("defense_gte", rule.get("threshold", 7))) and not has_status(e, status) for e in living_enemies)
        if when == "enemy_without_status_hp_above":
            status = str(rule.get("status", ""))
            return any(not has_status(e, status) and hp_pct(e) > float(rule.get("hp_above", 0.45)) for e in living_enemies)
        if when == "enemy_without_status":
            status = str(rule.get("status", ""))
            return any(not has_status(e, status) for e in living_enemies)
        if when == "enemy_hp_below":
            return any(hp_pct(e) < float(rule.get("hp_below", rule.get("threshold", 0.35))) for e in living_enemies)
        return False

    rules = data.get("skill_ai_by_class_id", {}).get(class_id, [])
    for rule in (rules if isinstance(rules, list) else []):
        if not isinstance(rule, dict):
            continue
        skill_id = str(rule.get("skill", ""))
        if skill_id and can(skill_id) and rule_matches(rule):
            return skill_id

    for skill_id in skills:
        if skill_id != "basic_attack" and can(skill_id):
            return skill_id
    return "basic_attack"


def candidate_targets(targets: list[Combatant], rule: str, actor: Combatant | None = None) -> list[Combatant]:
    living = alive(targets)
    if not living:
        return []
    if rule == "self" and actor is not None and actor.get("hp", 0) > 0:
        return [actor]
    if rule == "ally_all":
        return living
    if rule == "ally_front":
        front = [t for t in living if t.get("cell") in FRONT_CELLS]
        return front or living
    if rule == "ally_back":
        back = [t for t in living if t.get("cell") in BACK_CELLS]
        return back or living
    if rule in {"all", "cluster"}:
        return living
    if rule == "all_front":
        front = [t for t in living if t.get("cell") in FRONT_CELLS or t.get("cell") in MID_CELLS]
        return front or living
    if rule in {"front", "melee"}:
        front = [t for t in living if t.get("cell") in FRONT_CELLS]
        return sorted(front or living, key=lambda t: (t.get("cell", ""), t["hp"]))
    if rule == "rear":
        rear = [t for t in living if t.get("cell") in BACK_CELLS]
        return sorted(rear or living, key=lambda t: t["hp"])
    if rule == "lowest_hp":
        return sorted(living, key=lambda t: (t["hp"] / max(1, t["max_hp"]), t["hp"]))
    if rule == "highest_attack":
        return sorted(living, key=lambda t: -t.get("attack", 0))
    if rule == "highest_defense":
        return sorted(living, key=lambda t: -t.get("defense", 0))
    if rule == "elite":
        elite = [t for t in living if "elite" in t.get("tags", []) or "boss" in t.get("tags", [])]
        return elite or living
    if rule == "ally_low_hp":
        return sorted(living, key=lambda t: (t["hp"] / max(1, t["max_hp"]), t["hp"]))
    if rule == "ally_status":
        status = [t for t in living if any(s["type"] in {"poison", "curse", "burn", "bleed", "armor_break", "marked", "vulnerable", "slow"} for s in t.get("statuses", []))]
        return status or candidate_targets(living, "ally_low_hp")
    if rule == "ally_backline":
        back = [t for t in living if t.get("cell") in BACK_CELLS]
        return sorted(back or living, key=lambda t: t["hp"] / max(1, t["max_hp"]))
    return living


def combat_attack_value(unit: Combatant) -> int:
    return max(1, int(unit.get("attack", 0)) + status_value(unit, "might") - status_value(unit, "enfeeble"))


def combat_evasion_value(unit: Combatant) -> int:
    return max(0, int(unit.get("evasion", 0)) + status_value(unit, "evasion_up") + status_value(unit, "haste") - status_value(unit, "marked") - status_value(unit, "slow"))


def combat_defense_value(unit: Combatant, skill: dict[str, Any] | None = None) -> int:
    defense = int(unit.get("defense", 0))
    defense -= status_value(unit, "armor_break")
    defense -= status_value(unit, "vulnerable") // 2
    defense += status_value(unit, "barrier") // 4
    if has_status(unit, "shield_wall"):
        defense += status_value(unit, "shield_wall") // 4
    ignore = float((skill or {}).get("ignore_defense", 0))
    if ignore:
        defense = int(round(defense * (1 - clamp(ignore, 0, 0.85))))
    return max(0, defense)


def effective_resistances(unit: Combatant) -> dict[str, int]:
    res = {k: int(v) for k, v in unit.get("resistances", {}).items()}
    ward = status_value(unit, "ward")
    if ward:
        for key in ("magic", "curse", "poison", "fire"):
            res[key] = res.get(key, 0) + ward
    if status_value(unit, "barrier"):
        for key in DAMAGE_TYPES:
            res[key] = res.get(key, 0) + status_value(unit, "barrier") // 3
    return {k: int(clamp(res.get(k, 0), -75, 100)) for k in DAMAGE_TYPES}


def skill_focus_bonus(unit: Combatant, skill: dict[str, Any]) -> int:
    focus = skill.get("attribute_focus")
    if not focus:
        return 0
    score = attribute_focus_score(unit.get("attributes", {}), focus)
    return int(round(score * float(skill.get("attribute_scale", 0.11))))


def target_count_for_skill(skill: dict[str, Any], targets: list[Combatant]) -> int:
    if not targets:
        return 0
    if "target_count" in skill:
        return max(1, min(len(targets), int(skill.get("target_count", 1))))
    if skill.get("target_rule") in {"all", "ally_all"}:
        return len(targets)
    if skill.get("target_rule") in {"cluster", "all_front"}:
        return min(3, len(targets))
    return 1


def resolve_damage(actor: Combatant, target: Combatant, skill: dict[str, Any], rng: random.Random, logs: list[str], report: dict[str, Any]) -> int:
    if target["hp"] <= 0:
        return 0
    attack_type = attack_type_for_skill(skill)
    original_target = target
    if target["side"] == "party" and is_backline(target):
        guard = next((u for u in report.get("current_party", []) if u["side"] == "party" and u.get("guarding") and u["hp"] > 0), None)
        guard_chance = 0.70 + (0.12 if guard and "guard_bonus" in guard.get("special_effects", []) else 0) + (status_value(guard, "guarding") / 350 if guard else 0)
        if guard and rng.random() < clamp(guard_chance, 0.55, 0.92):
            text = f"{guard['name']} 保护 {target['name']}，改为承受攻击"
            logs.append(text)
            record_event(report, {
                "type": "guard_redirect",
                "text": text,
                "actor": event_actor(guard),
                "target": event_actor(target),
                "redirect_to": event_actor(guard),
            })
            target = guard
    if target["side"] == "party":
        maybe_use_defense_skill(target, actor, skill, rng, logs, report)
    acc = int(actor.get("accuracy", 80)) + int(skill.get("accuracy_modifier", 0)) + status_value(actor, "focus") - combat_evasion_value(target) - status_value(actor, "curse")
    hit_chance = clamp(acc / 100, 0.30, 0.96)
    if rng.random() > hit_chance:
        text = f"{actor['name']} 使用 {skill['name']} 但被 {target['name']} 闪避"
        logs.append(text)
        report["misses"][actor["id"]] += 1
        record_event(report, {
            "type": "miss",
            "text": text,
            "actor": event_actor(actor),
            "target": event_actor(target),
            "skill": skill.get("name", "攻击"),
            "hit_chance": round(hit_chance, 2),
            "attack_type": attack_type,
        })
        return 0
    defense = combat_defense_value(target, skill)
    defense_factor = float(skill.get("defense_factor", 1.0 if "physical" in skill.get("damage_types", ["physical"]) else 0.62))
    base = max(1, combat_attack_value(actor) + int(skill.get("power", 0)) + skill_focus_bonus(actor, skill) - int(round(defense * defense_factor)))
    dtypes = skill.get("damage_types", ["physical"])
    resists = effective_resistances(target)
    resist = sum(resists.get(dt, 0) for dt in dtypes) / max(1, len(dtypes))
    multiplier = 1.0
    if has_status(target, "marked"):
        multiplier += status_value(target, "marked") / 100
    if has_status(target, "vulnerable"):
        multiplier += status_value(target, "vulnerable") / 120
    if target["hp"] / max(1, target["max_hp"]) <= 0.35:
        multiplier += float(skill.get("execute_bonus", 0))
    if "fire" in dtypes and "fire_bonus_minor" in actor.get("special_effects", []):
        multiplier += 0.10
    if skill.get("bonus_vs_status") and any(has_status(target, st) for st in skill.get("bonus_vs_status", [])):
        multiplier += float(skill.get("status_bonus", 0.18))
    crit_chance = float(skill.get("crit_chance", 0)) + (attribute_focus_score(actor.get("attributes", {}), skill.get("attribute_focus")) / 700)
    critical = rng.random() < clamp(crit_chance, 0, 0.35)
    if critical:
        multiplier *= float(skill.get("crit_multiplier", 1.35))
    damage = max(1, int(round(base * (1 - resist / 100) * multiplier * rng.uniform(0.88, 1.12))))
    if target.get("guarding") or has_status(target, "shield_wall"):
        damage = max(1, int(damage * 0.78))
    if has_status(target, "barrier"):
        damage = max(1, damage - max(1, status_value(target, "barrier") // 2))
    before_hp = int(target["hp"])
    target["hp"] = max(0, target["hp"] - damage)
    text = f"{actor['name']} 使用 {skill['name']} {'暴击' if critical else '命中'} {target['name']}，造成 {damage} 伤害"
    logs.append(text)
    if actor["side"] == "party":
        report["damage_done"][actor["id"]] += damage
    if target["side"] == "party":
        report["damage_taken"][target["id"]] += damage
        if is_backline(target):
            report["backline_damage"] += damage
    for dt in dtypes:
        report["damage_by_type"][dt] += damage / len(dtypes)
    record_event(report, {
        "type": "damage",
        "text": text,
        "actor": event_actor(actor),
        "target": event_actor(target),
        "original_target": event_actor(original_target) if original_target is not target else None,
        "skill": skill.get("name", "攻击"),
        "amount": damage,
        "damage_types": dtypes,
        "attack_type": attack_type,
        "resist": int(round(resist)),
        "critical": critical,
        "attribute_focus": skill.get("attribute_focus"),
        "target_hp_before": before_hp,
        "target_hp_after": int(target["hp"]),
        "target_statuses": copy.deepcopy(target.get("statuses", [])),
    })
    if critical and actor["side"] == "party":
        add_critical_event(report, f"{actor['name']} 的 {skill['name']} 暴击 {target['name']}（{damage}）")
    if target["side"] == "party" and before_hp / max(1, target["max_hp"]) > 0.30 and target["hp"] / max(1, target["max_hp"]) <= 0.30 and target["hp"] > 0:
        add_critical_event(report, f"{target['name']} 被 {actor['name']} 的 {skill['name']} 打至危险血线（{hp_text(target)}）")
    for st in skill.get("status_effects", []):
        if rng.random() < float(st.get("chance", 1.0)):
            add_status(target, st)
            text = f"{target['name']} 获得状态：{st['type']}"
            logs.append(text)
            if target["side"] == "party":
                report["status_stats"][st["type"]] += 1
            record_event(report, {
                "type": "status",
                "text": text,
                "actor": event_actor(actor),
                "target": event_actor(target),
                "skill": skill.get("name", "攻击"),
                "status": copy.deepcopy(st),
                "attack_type": attack_type,
                "target_statuses": copy.deepcopy(target.get("statuses", [])),
            })
    if target["hp"] <= 0:
        text = f"{target['name']} 倒下"
        logs.append(text)
        record_event(report, {"type": "down", "text": text, "actor": event_actor(actor), "target": event_actor(target), "target_hp_after": 0})
        add_critical_event(report, text)
    return damage


def apply_heal(actor: Combatant, target: Combatant, skill: dict[str, Any], logs: list[str], report: dict[str, Any]) -> None:
    bonus = 1.12 if "healing_bonus_minor" in actor.get("special_effects", []) else 1.0
    if has_status(actor, "curse"):
        bonus *= 0.8
    focus = attribute_focus_score(actor.get("attributes", {}), skill.get("attribute_focus", "healing"))
    amount = int((skill.get("power", 25) + combat_attack_value(actor) * 0.45 + focus * float(skill.get("attribute_scale", 0.22))) * bonus)
    before = target["hp"]
    target["hp"] = min(target["max_hp"], target["hp"] + amount)
    healed = target["hp"] - before
    report["healing_done"][actor["id"]] += healed
    text = f"{actor['name']} 使用 {skill['name']} 治疗 {target['name']} {healed} HP"
    logs.append(text)
    record_event(report, {
        "type": "heal",
        "text": text,
        "actor": event_actor(actor),
        "target": event_actor(target),
        "skill": skill.get("name", "治疗"),
        "amount": healed,
        "target_hp_before": int(before),
        "target_hp_after": int(target["hp"]),
        "target_statuses": copy.deepcopy(target.get("statuses", [])),
    })
    for st in skill.get("status_effects", []):
        add_status(target, st)


def apply_cleanse(actor: Combatant, target: Combatant, skill: dict[str, Any], logs: list[str], report: dict[str, Any]) -> None:
    before = list(target.get("statuses", []))
    removable = set(skill.get("cleanse_statuses", ["poison", "curse", "burn", "bleed", "armor_break", "marked", "vulnerable", "slow", "enfeeble"]))
    target["statuses"] = [s for s in target.get("statuses", []) if s["type"] not in removable]
    removed = len(before) - len(target["statuses"])
    report["skill_usage"][actor["id"]]["cleanse_removed"] += removed
    text = f"{actor['name']} 净化 {target['name']}，移除 {removed} 个异常状态"
    logs.append(text)
    record_event(report, {
        "type": "cleanse",
        "text": text,
        "actor": event_actor(actor),
        "target": event_actor(target),
        "amount": removed,
        "removed_statuses": copy.deepcopy(before),
        "target_statuses": copy.deepcopy(target.get("statuses", [])),
    })


def apply_guard(actor: Combatant, skill: dict[str, Any], logs: list[str], report: dict[str, Any]) -> None:
    actor["guarding"] = True
    for st in skill.get("status_effects", []):
        add_status(actor, st)
    text = f"{actor['name']} 进入保护姿态，尝试替后排承受攻击"
    logs.append(text)
    record_event(report, {
        "type": "guard",
        "text": text,
        "actor": event_actor(actor),
        "actor_statuses": copy.deepcopy(actor.get("statuses", [])) + [{"type": "guarding", "duration": 1, "potency": 35}],
    })


def apply_buff(actor: Combatant, skill: dict[str, Any], logs: list[str], report: dict[str, Any]) -> None:
    for st in skill.get("status_effects", []):
        add_status(actor, st)
    text = f"{actor['name']} 使用 {skill['name']} 强化自身"
    logs.append(text)
    record_event(report, {
        "type": "buff",
        "text": text,
        "actor": event_actor(actor),
        "skill": skill.get("name", "强化"),
        "statuses": copy.deepcopy(skill.get("status_effects", [])),
        "actor_statuses": copy.deepcopy(actor.get("statuses", [])),
    })


def apply_support(actor: Combatant, targets: list[Combatant], skill: dict[str, Any], logs: list[str], report: dict[str, Any]) -> None:
    affected: list[str] = []
    for target in targets:
        for st in skill.get("status_effects", []):
            add_status(target, st)
            if st.get("type") == "guarding" and target is actor:
                target["guarding"] = True
        affected.append(target["name"])
    text = f"{actor['name']} 使用 {skill['name']} 支援 {', '.join(affected) if affected else '队伍'}"
    logs.append(text)
    record_event(report, {
        "type": "support",
        "text": text,
        "actor": event_actor(actor),
        "skill": skill.get("name", "支援"),
        "targets": [event_actor(t) for t in targets],
        "statuses": copy.deepcopy(skill.get("status_effects", [])),
    })


def apply_debuff(actor: Combatant, targets: list[Combatant], skill: dict[str, Any], rng: random.Random, logs: list[str], report: dict[str, Any]) -> None:
    affected: list[str] = []
    for target in targets:
        for st in skill.get("status_effects", []):
            if rng.random() < float(st.get("chance", 1.0)):
                add_status(target, st)
                affected.append(f"{target['name']}:{st['type']}")
                if target["side"] == "party":
                    report["status_stats"][st["type"]] += 1
    text = f"{actor['name']} 使用 {skill['name']} 施加压制" + (f"（{', '.join(affected)}）" if affected else "，但未生效")
    logs.append(text)
    record_event(report, {
        "type": "debuff",
        "text": text,
        "actor": event_actor(actor),
        "skill": skill.get("name", "削弱"),
        "attack_type": attack_type_for_skill(skill),
        "targets": [event_actor(t) for t in targets],
        "statuses": copy.deepcopy(skill.get("status_effects", [])),
    })


def actor_take_turn(actor: Combatant, party: list[Combatant], enemies: list[Combatant], rng: random.Random, logs: list[str], report: dict[str, Any]) -> None:
    if actor["hp"] <= 0:
        return
    if has_status(actor, "stun"):
        text = f"{actor['name']} 被眩晕，跳过行动"
        logs.append(text)
        record_event(report, {"type": "skip", "text": text, "actor": event_actor(actor), "reason": "stun"})
        actor["statuses"] = [s for s in actor.get("statuses", []) if s["type"] != "stun"]
        return
    data = load_data()
    if actor["side"] == "party":
        sid = choose_player_skill(actor, party, enemies)
        if not execute_player_skill(actor, sid, party, enemies, rng, logs, report):
            execute_player_skill(actor, "basic_attack", party, enemies, rng, logs, report)
    else:
        skill = copy.deepcopy(rng.choice(actor.get("skills", [])))
        if "rear_threat" in report.get("affix_mechanics", []) and rng.random() < 0.35:
            skill["target_rule"] = "rear"
        report["skill_usage"][actor["id"]][skill["name"]] += 1
        targets = candidate_targets(party, skill.get("target_rule", "front"), actor)
        if not targets:
            return
        for t in targets[:target_count_for_skill(skill, targets)]:
            resolve_damage(actor, t, skill, rng, logs, report)


def apply_trap(effect: str, party: list[Combatant], rng: random.Random, logs: list[str], report: dict[str, Any]) -> None:
    living = alive(party)
    if effect == "web":
        for unit in living:
            if rng.random() < 0.55:
                add_status(unit, {"type": "slow", "duration": 2, "potency": 3})
                unit["speed"] = max(1, unit["speed"] - 3)
                text = f"蛛网陷阱缠住 {unit['name']}，速度下降"
                logs.append(text)
                record_event(report, {
                    "type": "trap_status",
                    "text": text,
                    "trap": effect,
                    "target": event_actor(unit),
                    "status": {"type": "slow", "duration": 2, "potency": 3},
                    "target_statuses": copy.deepcopy(unit.get("statuses", [])),
                })
    elif effect == "ambush":
        back = [u for u in living if is_backline(u)] or living
        for unit in back[:2]:
            dmg = rng.randint(6, 14)
            before_hp = int(unit["hp"])
            unit["hp"] = max(0, unit["hp"] - dmg)
            report["damage_taken"][unit["id"]] += dmg
            report["backline_damage"] += dmg if is_backline(unit) else 0
            text = f"伏击造成 {unit['name']} {dmg} 伤害"
            logs.append(text)
            record_event(report, {
                "type": "trap_damage",
                "text": text,
                "trap": effect,
                "target": event_actor(unit),
                "amount": dmg,
                "damage_types": ["physical"],
                "target_hp_before": before_hp,
                "target_hp_after": int(unit["hp"]),
                "target_statuses": copy.deepcopy(unit.get("statuses", [])),
            })
            if unit["hp"] <= 0:
                down = f"{unit['name']} 被伏击击倒"
                record_event(report, {"type": "down", "text": down, "target": event_actor(unit), "target_hp_after": 0})
                add_critical_event(report, down)
    elif effect == "curse":
        for unit in living:
            if rng.random() < 0.5:
                add_status(unit, {"type": "curse", "duration": 3, "potency": 10})
                report["status_stats"]["curse"] += 1
                text = f"诅咒墓碑影响 {unit['name']}"
                logs.append(text)
                record_event(report, {
                    "type": "trap_status",
                    "text": text,
                    "trap": effect,
                    "target": event_actor(unit),
                    "status": {"type": "curse", "duration": 3, "potency": 10},
                    "target_statuses": copy.deepcopy(unit.get("statuses", [])),
                })
    elif effect == "burn":
        for unit in living:
            dmg = rng.randint(4, 9)
            before_hp = int(unit["hp"])
            unit["hp"] = max(0, unit["hp"] - dmg)
            add_status(unit, {"type": "burn", "duration": 2, "potency": 4})
            report["damage_taken"][unit["id"]] += dmg
            report["damage_by_type"]["fire"] += dmg
            text = f"灼热地面造成 {unit['name']} {dmg} 火焰伤害"
            logs.append(text)
            record_event(report, {
                "type": "trap_damage",
                "text": text,
                "trap": effect,
                "target": event_actor(unit),
                "amount": dmg,
                "damage_types": ["fire"],
                "target_hp_before": before_hp,
                "target_hp_after": int(unit["hp"]),
                "target_statuses": copy.deepcopy(unit.get("statuses", [])),
            })
    elif effect == "durability":
        report["extra_durability_loss"] += 4
        text = "裂谷深处让装备额外损耗耐久"
        logs.append(text)
        record_event(report, {"type": "durability_pressure", "text": text, "trap": effect})


def numeric_counter_snapshot(counter: dict[str, Any]) -> dict[str, float]:
    return {str(k): float(v) for k, v in counter.items()}


def numeric_counter_delta(after: dict[str, Any], before: dict[str, float]) -> dict[str, float]:
    keys = set(after.keys()) | set(before.keys())
    return {str(k): float(after.get(k, 0)) - float(before.get(k, 0)) for k in keys if abs(float(after.get(k, 0)) - float(before.get(k, 0))) > 0.001}


def report_display_name(state: dict[str, Any], report: dict[str, Any], uid: str) -> str:
    ch = get_character(state, uid)
    if ch:
        return ch["name"]
    return report.get("unit_names", {}).get(uid, uid)


def named_report_stats(state: dict[str, Any], report: dict[str, Any], stats: dict[str, float]) -> dict[str, int]:
    return {report_display_name(state, report, k): int(round(v)) for k, v in stats.items() if v}


def should_retreat(state: dict[str, Any], party: list[Combatant], report: dict[str, Any]) -> str | None:
    strategy = state.get("retreat_strategy", "standard")
    if strategy == "death_or_glory":
        return None
    living = alive(party)
    if not living:
        return "全队被击溃"
    threshold = RETREAT_THRESHOLDS.get(strategy, 0.2)
    low = [u for u in living if u["hp"] / max(1, u["max_hp"]) < threshold]
    if low:
        return f"撤退策略触发：{low[0]['name']} HP 低于 {int(threshold*100)}%"
    if strategy == "aggressive":
        down = [u for u in party if u["hp"] <= 0]
        data = load_data()
        key_support_down = any(
            u["hp"] <= 0
            and any(data["skill_by_id"].get(sid, {}).get("type") in {"heal", "cleanse"} for sid in u.get("skills", []))
            for u in party
        )
        if len(down) >= 2 or key_support_down:
            return "激进策略触发：关键角色倒下或多人倒下"
    if strategy == "standard":
        down = [u for u in party if u["hp"] <= 0]
        if down:
            return "标准策略触发：已有队员倒下"
    return None


def resolve_layer(state: dict[str, Any], dungeon: dict[str, Any], layer: dict[str, Any], layer_index: int, party: list[Combatant], rng: random.Random, report: dict[str, Any]) -> dict[str, Any]:
    logs: list[str] = []
    pre_events: list[dict[str, Any]] = []
    round_details: list[dict[str, Any]] = []
    layer_tactic_names = apply_layer_tactics_to_party(state, party, layer_index)
    entry_party = lineup_snapshot(party)
    stats_before = {
        "damage_done": numeric_counter_snapshot(report["damage_done"]),
        "damage_taken": numeric_counter_snapshot(report["damage_taken"]),
        "healing_done": numeric_counter_snapshot(report["healing_done"]),
        "damage_by_type": numeric_counter_snapshot(report["damage_by_type"]),
        "misses": numeric_counter_snapshot(report["misses"]),
    }
    status_before = numeric_counter_snapshot(report["status_stats"])
    affix_mechanics = report["affix_mechanics"]
    report["_event_sink"] = pre_events
    if layer_tactic_names:
        text = f"第 {layer_index} 层套用分层战术：{'、'.join(layer_tactic_names[:4])}"
        logs.append(text)
        record_event(report, {
            "type": "layer_tactics",
            "text": text,
            "layer": layer_index,
            "characters": layer_tactic_names,
        })
    if "poison_pressure" in affix_mechanics:
        for unit in alive(party):
            if rng.random() < 0.28:
                add_status(unit, {"type": "poison", "duration": 2, "potency": 4})
                text = f"毒雾使 {unit['name']} 中毒"
                logs.append(text)
                record_event(report, {
                    "type": "hazard_status",
                    "text": text,
                    "hazard": "poison_pressure",
                    "target": event_actor(unit),
                    "status": {"type": "poison", "duration": 2, "potency": 4},
                    "target_statuses": copy.deepcopy(unit.get("statuses", [])),
                })
    if "fire_pressure" in affix_mechanics:
        for unit in alive(party):
            dmg = rng.randint(2, 6)
            before_hp = int(unit["hp"])
            unit["hp"] = max(0, unit["hp"] - dmg)
            report["damage_taken"][unit["id"]] += dmg
            report["damage_by_type"]["fire"] += dmg
            text = f"灼热空气造成 {unit['name']} {dmg} 火焰伤害"
            logs.append(text)
            record_event(report, {
                "type": "hazard_damage",
                "text": text,
                "hazard": "fire_pressure",
                "target": event_actor(unit),
                "amount": dmg,
                "damage_types": ["fire"],
                "target_hp_before": before_hp,
                "target_hp_after": int(unit["hp"]),
                "target_statuses": copy.deepcopy(unit.get("statuses", [])),
            })
        report["extra_durability_loss"] += 2
    if layer.get("type") == "trap":
        apply_trap(layer.get("effect", ""), party, rng, logs, report)
        enemy_ids = layer.get("then_enemies", [])
    else:
        enemy_ids = layer.get("enemies", [])
    enemies = make_enemy_combatants(enemy_ids, affix_mechanics, layer_index)
    register_unit_names(report, party)
    register_unit_names(report, enemies)
    report["current_party"] = party
    report["_event_sink"] = pre_events
    record_initiative_skill_events(party, logs, report)
    use_opening_skills(party, enemies, rng, logs, report)
    report["_event_sink"] = None
    party_after_opening = lineup_snapshot(party)
    enemy_start = lineup_snapshot(enemies)
    rounds = 0
    result = "victory"
    while alive(party) and alive(enemies) and rounds < 14:
        rounds += 1
        report["current_party"] = party
        for u in party + enemies:
            u["guarding"] = False
        round_logs: list[str] = []
        round_events: list[dict[str, Any]] = []
        round_start_party = lineup_snapshot(party)
        round_start_enemies = lineup_snapshot(enemies)
        actors = sorted(alive(party) + alive(enemies), key=lambda x: (-x.get("speed", 0), x.get("name", "")))
        report["_event_sink"] = round_events
        for u in actors:
            tick_statuses(u, {}, round_logs, report)
            if u["hp"] <= 0:
                continue
            actor_take_turn(u, party, enemies, rng, round_logs, report)
            if not alive(party) or not alive(enemies):
                break
        report["_event_sink"] = None
        logs.extend([f"R{rounds}: {line}" for line in round_logs[:14]])
        reason = should_retreat(state, party, report)
        if reason and alive(enemies):
            result = "retreated"
            logs.append(reason)
            event = {"type": "retreat", "text": reason, "party": lineup_snapshot(party), "enemies": lineup_snapshot(enemies)}
            round_events.append(event)
            add_critical_event(report, reason)
        round_details.append({
            "round": rounds,
            "actor_order": [event_actor(u) for u in actors],
            "start": {"party": round_start_party, "enemies": round_start_enemies},
            "end": {"party": lineup_snapshot(party), "enemies": lineup_snapshot(enemies)},
            "events": round_events,
            "logs": round_logs[:24],
            "party_hp": {u["name"]: hp_text(u) for u in party},
            "enemy_hp": {u["name"]: hp_text(u) for u in enemies},
        })
        if reason and alive(enemies):
            break
    if not alive(party):
        result = "defeat"
    elif alive(enemies) and result != "retreated":
        result = "retreated"
        text = "战斗超过 14 回合仍未结束，队伍选择撤退"
        logs.append(text)
        add_critical_event(report, text)
        if round_details:
            round_details[-1]["events"].append({"type": "retreat", "text": text, "party": lineup_snapshot(party), "enemies": lineup_snapshot(enemies)})
    stats_after = {
        "damage_done": numeric_counter_snapshot(report["damage_done"]),
        "damage_taken": numeric_counter_snapshot(report["damage_taken"]),
        "healing_done": numeric_counter_snapshot(report["healing_done"]),
        "damage_by_type": numeric_counter_snapshot(report["damage_by_type"]),
        "misses": numeric_counter_snapshot(report["misses"]),
    }
    status_delta = numeric_counter_delta(report["status_stats"], status_before)
    damage_done_delta = numeric_counter_delta(stats_after["damage_done"], stats_before["damage_done"])
    damage_taken_delta = numeric_counter_delta(stats_after["damage_taken"], stats_before["damage_taken"])
    healing_delta = numeric_counter_delta(stats_after["healing_done"], stats_before["healing_done"])
    damage_type_delta = numeric_counter_delta(stats_after["damage_by_type"], stats_before["damage_by_type"])
    misses_delta = numeric_counter_delta(stats_after["misses"], stats_before["misses"])
    return {
        "index": layer_index,
        "name": layer.get("name", f"第 {layer_index} 层"),
        "type": layer.get("type", "battle"),
        "result": result,
        "rounds": rounds,
        "entry_party": entry_party,
        "party_start": party_after_opening,
        "enemy_start": enemy_start,
        "party_end": lineup_snapshot(party),
        "enemy_end": lineup_snapshot(enemies),
        "pre_events": pre_events,
        "round_details": round_details,
        "party_hp": {u["name"]: hp_text(u) for u in party},
        "enemy_hp": {u["name"]: hp_text(u) for u in enemies},
        "enemy_remaining": [u["name"] for u in alive(enemies)],
        "damage_done": named_report_stats(state, report, damage_done_delta),
        "damage_taken": named_report_stats(state, report, damage_taken_delta),
        "healing_done": named_report_stats(state, report, healing_delta),
        "damage_by_type": {k: int(round(v)) for k, v in damage_type_delta.items() if v},
        "status_stats": {k: int(round(v)) for k, v in status_delta.items() if v},
        "misses": named_report_stats(state, report, misses_delta),
        "key_logs": logs[:80],
    }


def resolve_challenge(state: dict[str, Any], dungeon: dict[str, Any], action_index: int, team_id: str = "team_1", tactic_scheme_id: str | None = None) -> dict[str, Any]:
    data = load_data()
    template = data["dungeon_by_id"][dungeon["template_id"]]
    rng = random.Random(stable_seed(state["run_seed"], "battle", state["day"], dungeon["id"], action_index, dungeon.get("challenged")))
    tactic_state, tactic_scheme = tactic_state_for_scheme(state, tactic_scheme_id)
    party = make_player_combatants(tactic_state, team_id)
    if not party:
        raise ValueError("没有上阵角色")
    affix_mechanics = [m for a in dungeon.get("affixes", []) for m in a.get("mechanics", [])]
    report: dict[str, Any] = {
        "id": f"rp_{state['next_counters']['report']:04d}", "day": state["day"], "type": "challenge",
        "dungeon_id": dungeon["id"], "dungeon_name": dungeon["name"], "team_id": team_id, "team_name": TEAM_LABELS.get(team_id, team_id),
        "tactic_scheme_id": tactic_scheme["id"] if tactic_scheme else "",
        "tactic_scheme_name": tactic_scheme["name"] if tactic_scheme else "当前战术",
        "result": "unknown", "cleared_layers": 0,
        "summary": "", "rewards": {"gold": 0, "exp": 0, "materials": {}, "equipment": []},
        "losses": {"hp": {}, "mana": {}, "injuries": [], "durability": {}}, "layer_results": [], "damage_stats": {}, "healing_stats": {}, "mana_spent_stats": {}, "damage_taken_stats": {},
        "damage_by_type_stats": {}, "miss_stats": {}, "review_metrics": {}, "battle_recap": [], "critical_events": [],
        "status_stats": Counter(), "skill_usage_stats": {}, "party_skill_usage_stats": {}, "enemy_skill_usage_stats": {},
        "key_events": [], "failure_reasons": [], "revealed_mechanics": [], "turn_logs": [], "unit_names": {}, "initial_party": lineup_snapshot(party),
        "damage_done": defaultdict(float), "damage_taken": defaultdict(float), "healing_done": defaultdict(float), "mana_spent": defaultdict(float), "damage_by_type": defaultdict(float),
        "skill_usage": defaultdict(Counter), "misses": defaultdict(int), "backline_damage": 0, "extra_durability_loss": 0, "affix_mechanics": affix_mechanics,
    }
    register_unit_names(report, party)
    dungeon["challenged"] = True
    for idx, layer in enumerate(template["layers"], start=1):
        lr = resolve_layer(tactic_state, dungeon, layer, idx, party, rng, report)
        report["layer_results"].append(lr)
        report["turn_logs"].extend([f"第 {idx} 层 / {x}" for x in lr["key_logs"]])
        if lr["result"] == "victory":
            report["cleared_layers"] = idx
            for unit in alive(party):
                tick_statuses(unit, {}, report["turn_logs"], report, phase="between")
            continue
        report["result"] = lr["result"]
        break
    else:
        report["result"] = "victory"
    for unit in party:
        ch = get_character(state, unit["id"])
        if not ch:
            continue
        ch["max_hp"] = int(unit["max_hp"])
        ch["hp"] = max(1 if report["result"] != "defeat" else 0, min(unit["hp"], unit["max_hp"]))
        ch["max_mana"] = int(unit.get("max_mana", ch.get("max_mana", 0)))
        ch["mana"] = max(0, min(int(unit.get("mana", ch.get("mana", ch["max_mana"]))), ch["max_mana"]))
        ch["status_effects"] = copy.deepcopy(unit.get("statuses", []))
        report["losses"]["hp"][ch["name"]] = f"{ch['hp']}/{unit['max_hp']}"
        report["losses"]["mana"][ch["name"]] = f"{ch['mana']}/{ch['max_mana']}"
        if unit["hp"] <= 0:
            injury = "重伤" if report["result"] == "defeat" else "轻伤"
            ch["injury_state"] = injury
            report["losses"]["injuries"].append(f"{ch['name']}：{injury}")
    apply_equipment_durability_loss(state, party, dungeon, report)
    apply_rewards_for_report(state, dungeon, template, report, rng, party)
    finalize_report(state, dungeon, template, report, party)
    state["next_counters"]["report"] += 1
    state["reports"].insert(0, sanitize_report(report))
    return state["reports"][0]


def apply_equipment_durability_loss(state: dict[str, Any], party: list[Combatant], dungeon: dict[str, Any], report: dict[str, Any]) -> None:
    base_loss = 3 + dungeon["danger_level"] // 2 + int(report.get("extra_durability_loss", 0))
    if any(s.get("type") == "burn" for u in party for s in u.get("statuses", [])):
        base_loss += 2
    for unit in party:
        ch = get_character(state, unit["id"])
        if not ch:
            continue
        for item_id in ch.get("equipment", {}).values():
            item = get_item(state, item_id) if item_id else None
            if not item:
                continue
            before = item["durability"]
            item["durability"] = max(0, before - base_loss)
            report["losses"]["durability"][item["name"]] = f"-{before - item['durability']} ({item['durability']}/{item['max_durability']})"


def apply_rewards_for_report(state: dict[str, Any], dungeon: dict[str, Any], template: dict[str, Any], report: dict[str, Any], rng: random.Random, party: list[Combatant]) -> None:
    clear_ratio = report["cleared_layers"] / max(1, template["layer_count"])
    success = report["result"] == "victory"
    if report["result"] == "defeat":
        clear_ratio *= 0.35
    elif report["result"] == "retreated":
        clear_ratio *= 0.65
    multiplier = 1.0
    for affix in dungeon.get("affixes", []):
        multiplier *= load_data()["affix_by_id"].get(affix["id"], {}).get("reward_multiplier", 1.0)
    if dungeon.get("reward_charges", 0) <= 0:
        multiplier *= 0.25
    base = template["rewards"]
    gold = int(base.get("gold", 0) * clear_ratio * multiplier)
    exp = int(base.get("exp", 0) * max(0.25, clear_ratio) * (1.15 if success else 0.8))
    state["gold"] += gold
    report["rewards"]["gold"] = gold
    report["rewards"]["exp"] = exp
    for k, v in base.get("materials", {}).items():
        amount = int(round(v * clear_ratio * multiplier))
        if amount > 0:
            state["materials"][k] = state["materials"].get(k, 0) + amount
            report["rewards"]["materials"][k] = amount
    for unit in party:
        ch = get_character(state, unit["id"])
        if ch:
            gain_exp(ch, exp)
    if success and base.get("equipment_pool") and dungeon.get("reward_charges", 0) > 0 and rng.random() < 0.75:
        eq_id = rng.choice(base["equipment_pool"])
        eq = instance_equipment(eq_id)
        state["inventory"].append(eq)
        report["rewards"]["equipment"].append(eq["name"])
    if success:
        dungeon["reward_charges"] = max(0, dungeon.get("reward_charges", 1) - 1)
        dungeon["cleared"] = dungeon["reward_charges"] <= 0
        if dungeon.get("is_final"):
            state["victory"] = True


def gain_exp(ch: dict[str, Any], exp: int) -> None:
    ch["exp"] += exp
    while ch["exp"] >= ch["level"] * 100:
        ch["exp"] -= ch["level"] * 100
        level_up_character(ch)


def level_up_character(ch: dict[str, Any]) -> None:
    normalize_character(ch)
    class_row = load_data()["class_by_id"].get(ch.get("class_id"), {})
    ch["level"] += 1
    ch["skill_points"] = max(0, int(ch.get("skill_points", 0))) + SKILL_POINTS_PER_LEVEL
    for key, inc in class_row.get("attribute_growth", {}).items():
        if key in ATTRIBUTE_KEYS:
            ch["attributes"][key] = int(ch["attributes"].get(key, 8)) + int(inc)
    for key, inc in class_row.get("stat_growth", {}).items():
        ch["base_stats"][key] = int(ch["base_stats"].get(key, 0)) + int(inc)
    # Universal adventurer improvement: a little accuracy every other level.
    if ch["level"] % 2 == 0:
        ch["base_stats"]["accuracy"] = int(ch["base_stats"].get("accuracy", 80)) + 1
    ch["skills"] = class_skill_ids(class_row)
    derived = attribute_derived_stats(ch["attributes"])
    old_max_mana = int(ch.get("max_mana", derived.get("mana", 0)))
    ch["max_hp"] = int(ch["base_stats"].get("max_hp", 1)) + derived["hp_bonus"]
    ch["hp"] = min(ch["max_hp"], int(ch.get("hp", ch["max_hp"])) + 12 + int(ch["attributes"].get("constitution", 8)) // 2)
    ch["max_mana"] = int(derived.get("mana", 0))
    ch["mana"] = min(ch["max_mana"], int(ch.get("mana", ch["max_mana"])) + max(3, ch["max_mana"] - old_max_mana + 4))


def finalize_report(state: dict[str, Any], dungeon: dict[str, Any], template: dict[str, Any], report: dict[str, Any], party: list[Combatant]) -> None:
    total_taken_raw = sum(report["damage_taken"].values())
    total_taken = total_taken_raw or 1
    total_done = sum(report["damage_done"].values())
    total_healing = sum(report["healing_done"].values())
    total_mana_spent = sum(report.get("mana_spent", {}).values())
    total_by_type = max(1, sum(report["damage_by_type"].values()))
    poison_share = report["damage_by_type"].get("poison", 0) / total_by_type
    fire_share = report["damage_by_type"].get("fire", 0) / total_by_type
    curse_events = report["status_stats"].get("curse", 0)
    if poison_share > 0.28:
        report["failure_reasons"].append("毒伤占比较高：建议携带牧师、解毒或毒抗装备。")
    if fire_share > 0.25:
        report["failure_reasons"].append("火焰消耗明显：火抗与装备修理准备不足会放大损失。")
    if curse_events >= 3:
        report["failure_reasons"].append("诅咒频繁出现：净化或诅咒抗性不足。")
    if report.get("backline_damage", 0) / total_taken > 0.25:
        report["failure_reasons"].append("后排承伤过高：需要调整站位或使用保护型前排。")
    if sum(report["misses"].values()) >= 4:
        report["failure_reasons"].append("未命中次数偏多：命中装备或目标优先级可能更合适。")
    if report["result"] != "victory" and total_healing < total_taken * 0.12:
        report["failure_reasons"].append("治疗覆盖不足：低血线阶段缺少有效抬血或治疗技能次数耗尽。")
    living_party = alive(party)
    if living_party and report["result"] != "victory":
        avg_hp_pct = sum(u["hp"] / max(1, u["max_hp"]) for u in living_party) / len(living_party)
        if avg_hp_pct < 0.35:
            report["failure_reasons"].append("撤退前平均血线偏低：建议降低推进层数预期或先休整修装。")
    if report["result"] == "retreated" and not report["failure_reasons"]:
        report["failure_reasons"].append("撤退条件触发较早，可以在准备充分时改用更激进策略。")
    if report["result"] == "defeat" and not report["failure_reasons"]:
        report["failure_reasons"].append("队伍综合承伤过高，建议先刷资源、升级或调整装备。")
    if report["result"] == "victory" and not report["failure_reasons"]:
        report["failure_reasons"].append("配置有效：当前阵型和技能足以应对该副本。")
    for line in template.get("post_battle_lines", []):
        if line not in dungeon["revealed_info"]:
            dungeon["revealed_info"].append(line)
        report["revealed_mechanics"].append(line)
    result_label = {"victory": "胜利", "retreated": "撤退", "defeat": "失败"}.get(report["result"], report["result"])
    reward_bits = []
    if report["rewards"].get("gold"):
        reward_bits.append(f"金币 +{report['rewards']['gold']}")
    if report["rewards"].get("exp"):
        reward_bits.append(f"经验 +{report['rewards']['exp']}")
    for k, v in report["rewards"].get("materials", {}).items():
        reward_bits.append(f"{MATERIAL_NAMES.get(k,k)} +{v}")
    if report["rewards"].get("equipment"):
        reward_bits.append("装备：" + "、".join(report["rewards"]["equipment"]))
    report["summary"] = f"{result_label}：推进 {report['cleared_layers']}/{template['layer_count']} 层。" + (" 获得 " + "，".join(reward_bits) if reward_bits else "")
    report["damage_stats"] = named_report_stats(state, report, report["damage_done"])
    report["damage_taken_stats"] = named_report_stats(state, report, report["damage_taken"])
    report["healing_stats"] = named_report_stats(state, report, report["healing_done"])
    report["mana_spent_stats"] = named_report_stats(state, report, report.get("mana_spent", {}))
    report["damage_by_type_stats"] = {k: int(round(v)) for k, v in report["damage_by_type"].items() if v}
    report["miss_stats"] = named_report_stats(state, report, report["misses"])
    report["status_stats"] = dict(report["status_stats"])
    party_ids = {u["id"] for u in party}
    all_usage: dict[str, Counter] = defaultdict(Counter)
    party_usage: dict[str, Counter] = defaultdict(Counter)
    enemy_usage: dict[str, Counter] = defaultdict(Counter)
    for uid, counter in report["skill_usage"].items():
        name = report_display_name(state, report, uid)
        all_usage[name].update(counter)
        if uid in party_ids:
            party_usage[name].update(counter)
        else:
            enemy_usage[name].update(counter)
    report["skill_usage_stats"] = {name: dict(counter) for name, counter in all_usage.items()}
    report["party_skill_usage_stats"] = {name: dict(counter) for name, counter in party_usage.items()}
    report["enemy_skill_usage_stats"] = {name: dict(counter) for name, counter in enemy_usage.items()}

    rounds_total = sum(int(l.get("rounds", 0)) for l in report.get("layer_results", []))
    end_hp = {u["name"]: hp_text(u) for u in party}
    end_hp_pct = {u["name"]: round(u["hp"] / max(1, u["max_hp"]), 2) for u in party}
    def top_entry(stats: dict[str, int]) -> tuple[str, int] | None:
        entries = [(k, v) for k, v in stats.items() if v]
        return max(entries, key=lambda kv: kv[1]) if entries else None
    top_damage = top_entry(report["damage_stats"])
    top_taken = top_entry(report["damage_taken_stats"])
    top_heal = top_entry(report["healing_stats"])
    main_dtype = top_entry(report["damage_by_type_stats"])
    report["review_metrics"] = {
        "rounds_total": rounds_total,
        "total_damage_done": int(round(total_done)),
        "total_damage_taken": int(round(total_taken_raw)),
        "total_healing": int(round(total_healing)),
        "total_mana_spent": int(round(total_mana_spent)),
        "backline_damage": int(round(report.get("backline_damage", 0))),
        "misses_total": int(sum(report["misses"].values())),
        "end_hp": end_hp,
        "end_hp_pct": end_hp_pct,
        "top_damage": {"name": top_damage[0], "value": top_damage[1]} if top_damage else None,
        "top_taken": {"name": top_taken[0], "value": top_taken[1]} if top_taken else None,
        "top_heal": {"name": top_heal[0], "value": top_heal[1]} if top_heal else None,
        "main_damage_type": {"type": main_dtype[0], "value": main_dtype[1]} if main_dtype else None,
    }
    recap = [
        f"总计 {rounds_total} 回合：造成 {int(round(total_done))} 伤害，承受 {int(round(total_taken_raw))} 伤害，治疗 {int(round(total_healing))} HP，消耗 {int(round(total_mana_spent))} 法力。",
    ]
    if top_damage:
        recap.append(f"主要输出：{top_damage[0]}（{top_damage[1]}）。")
    if top_taken:
        recap.append(f"最大承伤：{top_taken[0]}（{top_taken[1]}）。")
    if top_heal:
        recap.append(f"治疗贡献：{top_heal[0]}（{top_heal[1]}）。")
    if main_dtype:
        recap.append(f"主要伤害类型：{DAMAGE_TYPE_NAMES.get(main_dtype[0], main_dtype[0])}（{main_dtype[1]}）。")
    if report.get("critical_events"):
        recap.append("关键节点：" + "；".join(report["critical_events"][:3]))
    report["battle_recap"] = recap
    report["key_events"] = (report.get("critical_events") or report["turn_logs"])[:12]


def resolve_name(state: dict[str, Any], uid: str) -> str:
    ch = get_character(state, uid)
    if ch:
        return ch["name"]
    return uid


def named_stats(state: dict[str, Any], stats: dict[str, float]) -> dict[str, int]:
    return {resolve_name(state, k): int(round(v)) for k, v in stats.items() if v}


def sanitize_report(report: dict[str, Any]) -> dict[str, Any]:
    banned = {"damage_done", "damage_taken", "healing_done", "mana_spent", "damage_by_type", "skill_usage", "misses", "affix_mechanics", "current_party"}
    out = {}
    for k, v in report.items():
        if k in banned or k.startswith("_"):
            continue
        if isinstance(v, defaultdict):
            out[k] = dict(v)
        elif isinstance(v, Counter):
            out[k] = dict(v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def recommended_response(template: dict[str, Any]) -> list[str]:
    theme = template.get("theme", "")
    rec = []
    if "毒" in theme:
        rec.append("携带牧师/解毒，或装备毒抗戒指。")
    if "后排" in theme:
        rec.append("保护后排，优先击杀弓手/刺客。")
    if "护甲" in theme:
        rec.append("使用盗贼破甲或法师魔法输出。")
    if "诅咒" in theme:
        rec.append("准备净化与诅咒抗性。")
    if "火焰" in theme:
        rec.append("火抗装备和修理资源优先。")
    if "流血" in theme:
        rec.append("提升前排防御，快速减员狼群。")
    return rec or ["根据公开威胁调整阵型、装备和撤退条件。"]


def resolve_scout(state: dict[str, Any], dungeon: dict[str, Any], team_id: str = "team_1") -> dict[str, Any]:
    template = load_data()["dungeon_by_id"][dungeon["template_id"]]
    lines = list(template.get("scout_lines", []))
    for affix in dungeon.get("affixes", []):
        lines.append(f"词缀【{affix['name']}】：{affix.get('description','')}")
    dungeon["scout_info"] = {
        "scouted_day": state["day"],
        "lines": lines,
        "enemy_formation_hint": "前排承压，中后排存在关键输出或 Boss；根据副本主题调整站位。",
        "recommended_response": recommended_response(template),
    }
    report = {
        "id": f"rp_{state['next_counters']['report']:04d}", "day": state["day"], "type": "scout",
        "dungeon_id": dungeon["id"], "dungeon_name": dungeon["name"], "team_id": team_id, "team_name": TEAM_LABELS.get(team_id, team_id),
        "result": "scouted", "cleared_layers": 0,
        "summary": f"{TEAM_LABELS.get(team_id, team_id)}侦察完成：{dungeon['name']} 的关键机制已解锁。",
        "rewards": {"gold": 0, "exp": 8, "materials": {}, "equipment": []}, "losses": {"hp": {}, "injuries": [], "durability": {}},
        "layer_results": [], "damage_stats": {}, "healing_stats": {}, "damage_taken_stats": {}, "status_stats": {}, "skill_usage_stats": {},
        "key_events": lines, "failure_reasons": ["侦察占用一次远征机会，但降低了盲打风险。"], "revealed_mechanics": lines, "turn_logs": lines,
    }
    for ch in ordered_party_members(state, team_id):
        gain_exp(ch, 8)
    state["next_counters"]["report"] += 1
    state["reports"].insert(0, report)
    return report


def apply_rest_day(state: dict[str, Any]) -> dict[str, Any]:
    for ch in state["characters"]:
        normalize_character(ch)
        stats = effective_stats(state, ch)
        max_hp = stats.get("max_hp", ch["max_hp"])
        max_mana = int(stats.get("max_mana", ch.get("max_mana", 0)))
        ch["max_hp"] = int(max_hp)
        ch["hp"] = min(max_hp, ch.get("hp", max_hp) + int(max_hp * 0.35))
        ch["max_mana"] = max_mana
        ch["mana"] = max_mana
        if ch.get("injury_state") in {"轻伤", "重伤"}:
            ch["injury_state"] = "healthy"
        ch["status_effects"] = []
        gain_exp(ch, 6)
    report = {
        "id": f"rp_{state['next_counters']['report']:04d}", "day": state["day"], "type": "rest", "dungeon_id": None, "dungeon_name": "休整日", "result": "rested", "cleared_layers": 0,
        "summary": "没有安排远征：全队休整、治疗、恢复法力并进行轻量训练。", "rewards": {"gold": 0, "exp": 6, "materials": {}, "equipment": []},
        "losses": {"hp": {}, "mana": {}, "injuries": [], "durability": {}}, "layer_results": [], "damage_stats": {}, "healing_stats": {}, "damage_taken_stats": {}, "status_stats": {}, "skill_usage_stats": {},
        "key_events": ["全队恢复 HP 与法力，清除临时异常状态。"], "failure_reasons": ["休整牺牲当天远征收益，但能恢复长期推进能力。"], "revealed_mechanics": [], "turn_logs": []
    }
    state["next_counters"]["report"] += 1
    state["reports"].insert(0, report)
    return report


def advance_day(state: dict[str, Any]) -> None:
    for ch in state["characters"]:
        normalize_character(ch)
        stats = effective_stats(state, ch)
        max_hp = stats.get("max_hp", ch["max_hp"])
        max_mana = int(stats.get("max_mana", ch.get("max_mana", 0)))
        ch["max_hp"] = int(max_hp)
        ch["max_mana"] = max_mana
        recovery = int(max_hp * (0.22 if ch.get("injury_state") == "重伤" else 0.28))
        if ch.get("hp", 0) <= 0:
            ch["hp"] = max(1, int(max_hp * 0.25))
        else:
            ch["hp"] = min(max_hp, ch["hp"] + recovery)
        mana_recovery = max(4, int(max_mana * (0.28 if ch.get("injury_state") == "重伤" else 0.35)))
        ch["mana"] = min(max_mana, int(ch.get("mana", max_mana)) + mana_recovery)
        new_status = []
        for s in ch.get("status_effects", []):
            s = copy.deepcopy(s)
            s["duration"] = max(0, int(s.get("duration", 1)) - 1)
            if s["duration"] > 0:
                new_status.append(s)
        ch["status_effects"] = new_status
        if ch.get("injury_state") == "轻伤":
            ch["injury_state"] = "healthy"
        elif ch.get("injury_state") == "重伤" and state["day"] % 2 == 0:
            ch["injury_state"] = "轻伤"
    state["day"] += 1
    if state["day"] > state["max_day"] and not state.get("victory"):
        state["defeat"] = True
        state["defeat_reason"] = "第 30 天结束时未能通关最终 Boss。"
    else:
        world_refresh(state)


def end_day(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("victory") or state.get("defeat"):
        raise ValueError("本局已经结束")
    ensure_formations(state)
    reports = []
    plan = list(state.get("expedition_plan", []))
    used_teams: set[str] = set()
    for idx, action in enumerate(plan):
        team_id = action.get("team_id") or (TEAM_IDS[idx] if idx < len(TEAM_IDS) else "team_1")
        if team_id in used_teams:
            raise ValueError(f"{TEAM_LABELS.get(team_id, team_id)} 今日已经安排出征，不能重复出征")
        used_teams.add(team_id)
        validate_team_ready(state, team_id)
        dungeon = get_dungeon(state, action["dungeon_id"])
        if not dungeon:
            continue
        if action["type"] == "scout":
            reports.append(resolve_scout(state, dungeon, team_id))
        elif action["type"] == "challenge":
            reports.append(resolve_challenge(state, dungeon, idx, team_id, action.get("tactic_scheme_id")))
    if not plan:
        reports.append(apply_rest_day(state))
    advance_day(state)
    state["last_result"] = {"reports": [r["id"] for r in reports], "message": f"第 {state['day']-1} 天结算完成"}
    return {"reports": reports, "state": public_state_view(state)}


def full_debug_state(state: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(state)
