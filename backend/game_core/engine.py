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
MAX_ROSTER_SIZE = 8
# Fraction of a recruited character's cost refunded when dismissed/sold.
DISMISS_GOLD_REFUND = 0.3
MAX_TACTIC_SCHEMES = 20
MAX_TACTIC_LAYERS = 12
SKILL_POINTS_PER_LEVEL = 1
# Free attribute points granted each time a character levels up. Configurable per
# preset via `preset.attribute_points_per_level`. A level-1 character has none.
ATTRIBUTE_POINTS_PER_LEVEL = 5
# Hard cap so previews/derived stats stay sane even if a save is edited by hand.
MAX_ATTRIBUTE_VALUE = 99
SKILL_ESSENCE_KEY = "skill_essence"
PROMOTION_BADGE_KEY = "promotion_badge"
STARTING_SKILL_ESSENCE = 10
STARTING_PROMOTION_BADGES = 1
DEFAULT_SKILL_MAX_LEVEL = 5
DEFAULT_SKILL_UPGRADE_COSTS = [4, 8, 14, 22]
DEFAULT_PROMOTION_LEVEL = 6

# --- Quest system ---------------------------------------------------------
# Quest instances live in state["quests"]; their templates come from the
# preset's quests.json table (loaded via load_data()["quests"]). Three quest
# families: "story" (main/side campaign chains), "daily" (refreshed each day),
# and "hidden" (revealed by conditions or by completing them incidentally).
QUEST_TYPE_STORY = "story"
QUEST_TYPE_DAILY = "daily"
QUEST_TYPE_HIDDEN = "hidden"
QUEST_STORY_KIND_MAIN = "main"
QUEST_STORY_KIND_SIDE = "side"
# Quest lifecycle statuses a quest instance moves through.
#   available -> active -> completed -> claimed
#   available/active -> expired (daily only, after end-of-day refresh)
#   hidden (only for unrevealed hidden templates; never serialized as such once revealed)
QUEST_STATUSES = ["available", "active", "completed", "claimed", "expired", "hidden"]
QUEST_STATUS_LABELS = {
    "available": "可接受",
    "active": "进行中",
    "completed": "已完成",
    "claimed": "已领取",
    "expired": "已过期",
    "hidden": "隐藏",
}
# Objective evaluation kinds handled by record_quest_events.
QUEST_OBJ_CLEAR_DUNGEON = "clear_dungeon"
QUEST_OBJ_CLEAR_UNSCOUTED = "clear_unscouted_dungeon"
QUEST_OBJ_SCOUT_DUNGEON = "scout_dungeon"
QUEST_OBJ_SCOUT_ANY = "scout_any_dungeon"
QUEST_OBJ_CLEAR_TWO_ONE_DAY = "clear_two_dungeons_one_day"
QUEST_OBJ_MANUAL_ACK = "manual_ack"
QUEST_OBJECTIVE_KINDS = [
    QUEST_OBJ_CLEAR_DUNGEON,
    QUEST_OBJ_CLEAR_UNSCOUTED,
    QUEST_OBJ_SCOUT_DUNGEON,
    QUEST_OBJ_SCOUT_ANY,
    QUEST_OBJ_CLEAR_TWO_ONE_DAY,
    QUEST_OBJ_MANUAL_ACK,
]
# Reveal-condition evaluators supported in quest template `reveal_conditions`.
QUEST_COND_ALWAYS_TRUE = "always_true"
QUEST_COND_FLAG = "flag"
QUEST_COND_QUEST_COMPLETED = "quest_completed"
QUEST_COND_HIDDEN_COMPLETED_GTE = "hidden_completed_gte"
QUEST_DEFAULT_DAILY_COUNT = 3
QUEST_DEFAULT_DAILY_GOLD_RANGE = (40, 60)
QUEST_DEFAULT_EXPIRY_DAYS = 2  # daily quests remain accept-able for this many days

MATERIAL_NAMES = {
    SKILL_ESSENCE_KEY: "技能精华",
    PROMOTION_BADGE_KEY: "晋升徽记",
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

EQUIPMENT_RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "artifact"]
EQUIPMENT_RARITY_LABELS = {
    "common": "普通",
    "uncommon": "优秀",
    "rare": "精良",
    "epic": "史诗",
    "legendary": "传说",
    "artifact": "神器",
}
EQUIPMENT_RARITY_AFFIX_COUNTS = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
    "artifact": 5,
}
EQUIPMENT_RARITY_COST_MULTIPLIER = {
    "common": 1.0,
    "uncommon": 1.35,
    "rare": 1.9,
    "epic": 2.8,
    "legendary": 4.2,
    "artifact": 6.0,
}
EQUIPMENT_KIND_LABELS = {
    "base": "基础装备",
    "special": "特殊装备",
    "special_base": "特别装备",
}

# --- Equipment enchantment system -------------------------------------------
# Materials acquired from dungeon drops / salvage / quests are spent here to
# upgrade equipment:
#   * enchant: adds a random affix line from the existing equipment affix pool.
#   * reroll:  re-rolls an existing enchant line into a different one.
#   * ascension: a special (fixed-rarity) item + a recipe -> a stronger item.
# Enchant/reroll bonuses are summed straight into the instance's
# stats/resistances so the existing effective_stats data flow picks them up
# unchanged.

# Flat cost for one enchant roll (and one reroll). arcane_dust is the universal
# reagent; venom_sac adds a small throttle.
ENCHANT_COST = {"arcane_dust": 3, "venom_sac": 1}
MAX_ENCHANT_SLOTS = 2


CHARACTER_EQUIPMENT_SLOTS = [
    "head",
    "body",
    "hands",
    "feet",
    "waist",
    "ring_1",
    "ring_2",
    "necklace",
    "backpack_1",
    "backpack_2",
    "backpack_3",
    "backpack_4",
    "main_hand",
    "off_hand",
]
EQUIPMENT_SLOT_LABELS = {
    "head": "头盔",
    "body": "身体",
    "hands": "手套",
    "feet": "鞋子",
    "waist": "腰带",
    "ring": "戒指",
    "ring_1": "戒指 1",
    "ring_2": "戒指 2",
    "necklace": "项链",
    "backpack": "背包",
    "backpack_1": "背包 1",
    "backpack_2": "背包 2",
    "backpack_3": "背包 3",
    "backpack_4": "背包 4",
    "main_hand": "主手",
    "off_hand": "副手",
    "two_hand": "双手",
}
LEGACY_EQUIPMENT_SLOT_MAP = {
    "weapon": "main_hand",
    "armor": "body",
    "trinket": "ring",
}
EQUIPMENT_COMPATIBLE_SLOTS = {
    "head": ["head"],
    "body": ["body"],
    "hands": ["hands"],
    "feet": ["feet"],
    "waist": ["waist"],
    "ring": ["ring_1", "ring_2"],
    "necklace": ["necklace"],
    "backpack": ["backpack_1", "backpack_2", "backpack_3", "backpack_4"],
    "main_hand": ["main_hand"],
    "off_hand": ["off_hand"],
    "two_hand": ["main_hand"],
}
EQUIPMENT_SLOT_FAMILIES = {
    "head": {"armor"},
    "body": {"armor"},
    "hands": {"armor"},
    "feet": {"armor"},
    "waist": {"armor"},
    "ring": {"trinket"},
    "necklace": {"trinket"},
    "backpack": {"trinket"},
    "main_hand": {"weapon", "hand"},
    "off_hand": {"trinket", "shield", "hand"},
    "two_hand": {"weapon", "hand"},
}
DEFAULT_EQUIPMENT_AFFIXES = [
    {"id": "sharp", "name": "锐利", "position": "prefix", "slots": ["weapon"], "tags": ["martial", "melee", "weapon"], "rarity_min": "uncommon", "stats": {"attack": 2}, "weight": 16},
    {"id": "accurate", "name": "精准", "position": "prefix", "slots": ["weapon", "trinket"], "tags": ["ranged", "finesse", "weapon", "trinket"], "rarity_min": "uncommon", "stats": {"accuracy": 6}, "weight": 14},
    {"id": "quick", "name": "迅捷", "position": "prefix", "slots": ["weapon", "armor", "trinket"], "tags": ["finesse", "light", "ranged", "trinket"], "rarity_min": "uncommon", "stats": {"speed": 1}, "weight": 12},
    {"id": "stout", "name": "坚韧", "position": "prefix", "slots": ["armor", "trinket"], "tags": ["armor", "shield", "ward", "trinket"], "rarity_min": "uncommon", "stats": {"defense": 2, "max_hp": 6}, "weight": 15},
    {"id": "vital", "name": "活力", "position": "prefix", "slots": ["armor", "trinket"], "tags": ["armor", "ward", "trinket"], "rarity_min": "uncommon", "stats": {"max_hp": 10}, "weight": 12},
    {"id": "warded", "name": "护法", "position": "suffix", "slots": ["armor", "trinket"], "tags": ["ward", "armor", "trinket"], "rarity_min": "uncommon", "resistances": {"magic": 6, "curse": 6}, "weight": 10},
    {"id": "venomward", "name": "避毒", "position": "suffix", "slots": ["armor", "trinket"], "tags": ["ward", "trinket", "light"], "rarity_min": "uncommon", "resistances": {"poison": 10}, "weight": 10},
    {"id": "flameward", "name": "抗焰", "position": "suffix", "slots": ["armor", "trinket"], "tags": ["ward", "trinket", "armor", "fire"], "rarity_min": "uncommon", "resistances": {"fire": 10}, "weight": 10},
    {"id": "bleedward", "name": "止血", "position": "suffix", "slots": ["armor", "trinket"], "tags": ["ward", "trinket", "light"], "rarity_min": "uncommon", "resistances": {"bleed": 10}, "weight": 9},
    {"id": "durable", "name": "耐用", "position": "prefix", "slots": ["weapon", "armor", "trinket"], "tags": [], "rarity_min": "uncommon", "durability_bonus": 8, "weight": 9},
    {"id": "ember", "name": "余烬", "position": "suffix", "slots": ["weapon", "trinket"], "tags": ["fire", "magic", "weapon"], "rarity_min": "rare", "stats": {"attack": 1}, "resistances": {"fire": 6}, "special_effects": ["fire_bonus_minor"], "weight": 6, "group": "elemental_bonus"},
    {"id": "mender", "name": "抚愈", "position": "suffix", "slots": ["weapon", "trinket"], "tags": ["healing", "faith", "magic", "trinket"], "rarity_min": "rare", "stats": {"max_mana": 4}, "special_effects": ["healing_bonus_minor"], "weight": 6, "group": "support_bonus"},
    {"id": "guardian", "name": "守护", "position": "suffix", "slots": ["armor", "trinket"], "tags": ["shield", "armor", "ward"], "rarity_min": "rare", "stats": {"defense": 3}, "special_effects": ["guard_bonus"], "weight": 5, "group": "support_bonus"},
    {"id": "predator", "name": "猎杀", "position": "suffix", "slots": ["weapon", "trinket"], "tags": ["ranged", "finesse", "melee"], "rarity_min": "rare", "stats": {"attack": 2, "accuracy": 4}, "weight": 7},
    {"id": "arcane", "name": "秘法", "position": "prefix", "slots": ["weapon", "trinket"], "tags": ["magic", "faith", "healing"], "rarity_min": "rare", "stats": {"attack": 2, "max_mana": 6}, "resistances": {"magic": 4}, "weight": 7},
    {"id": "heroic", "name": "英勇", "position": "prefix", "slots": ["weapon", "armor", "trinket"], "tags": [], "rarity_min": "epic", "stats": {"attack": 2, "defense": 2, "max_hp": 8}, "weight": 3, "group": "major"},
]

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

# Consumable auto-use triggers. Each character tactic row carries a
# `consumable_priority` list of {consumable_id, trigger} entries; during its
# turn the first entry whose trigger is satisfied (and whose consumable is in
# stock) fires before skill selection. See `_consumable_trigger_met`.
CONSUMABLE_TRIGGERS = {
    "self_hp_below_50": "自身 HP 低于 50%",
    "self_hp_below_30": "自身 HP 低于 30%",
    "ally_hp_below_30": "任意队友 HP 低于 30%",
    "self_poisoned": "自身中毒 / 流血",
    "ally_poisoned": "任意队友中毒 / 流血",
    "self_cursed": "自身诅咒",
}
MAX_CONSUMABLE_SLOTS = 4

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


def rarity_index(rarity: str | None) -> int:
    try:
        return EQUIPMENT_RARITIES.index(str(rarity or "common"))
    except ValueError:
        return 0


def rarity_at_least(rarity: str | None, minimum: str | None) -> bool:
    return rarity_index(rarity) >= rarity_index(minimum)


def equipment_affix_pool() -> list[dict[str, Any]]:
    preset = load_data().get("preset", {})
    rows = preset.get("equipment_affixes") if isinstance(preset.get("equipment_affixes"), list) else DEFAULT_EQUIPMENT_AFFIXES
    return [copy.deepcopy(row) for row in rows if isinstance(row, dict) and row.get("id")]


def equipment_kind(tpl: dict[str, Any]) -> str:
    return str(tpl.get("item_kind") or tpl.get("kind") or ("special" if tpl.get("fixed_rarity") else "base"))


def canonical_item_slot(slot: str | None) -> str:
    raw = str(slot or "")
    return LEGACY_EQUIPMENT_SLOT_MAP.get(raw, raw or "backpack")


def compatible_equipment_slots(item_slot: str | None) -> list[str]:
    canonical = canonical_item_slot(item_slot)
    return list(EQUIPMENT_COMPATIBLE_SLOTS.get(canonical, [canonical] if canonical in CHARACTER_EQUIPMENT_SLOTS else []))


def equipment_slot_tokens(item_slot: str | None) -> set[str]:
    canonical = canonical_item_slot(item_slot)
    return {canonical, *EQUIPMENT_SLOT_FAMILIES.get(canonical, set())}


def equipment_slot_matches_token(item_slot: str | None, token: str) -> bool:
    token = canonical_item_slot(token)
    return token in equipment_slot_tokens(item_slot)


def equipment_item_occupies_slots(item: dict[str, Any], target_slot: str | None = None) -> list[str]:
    item_slot = canonical_item_slot(item.get("slot"))
    if item_slot == "two_hand":
        return ["main_hand", "off_hand"]
    if target_slot:
        slot = canonical_item_slot(target_slot)
        if slot in compatible_equipment_slots(item_slot):
            return [slot]
    slots = compatible_equipment_slots(item_slot)
    return [slots[0]] if slots else []


def default_character_equipment() -> dict[str, str | None]:
    return {slot: None for slot in CHARACTER_EQUIPMENT_SLOTS}


def equipment_level_from_danger(danger_level: int | None = None, day: int | None = None) -> int:
    value = 1
    if danger_level is not None:
        value = max(value, int(danger_level))
    if day is not None:
        value = max(value, int(day) // 4 + 1)
    return max(1, min(8, value))


def equipment_templates_for_level(level: int, *, include_special: bool = True) -> list[dict[str, Any]]:
    data = load_data()
    rows: list[dict[str, Any]] = []
    for tpl in data["equipment"]:
        tier = int(tpl.get("tier", tpl.get("min_level", 1)))
        if tier > level:
            continue
        if not include_special and equipment_kind(tpl) == "special":
            continue
        rows.append(copy.deepcopy(tpl))
    return rows


def roll_equipment_rarity(rng: random.Random, level: int, base_rarity: str = "common", max_rarity: str | None = None) -> str:
    weights = {
        "common": 60,
        "uncommon": 26 + level * 2,
        "rare": max(4, level * 4),
        "epic": max(0, (level - 2) * 2),
        "legendary": max(0, level - 4),
        "artifact": 1 if level >= 7 else 0,
    }
    min_idx = rarity_index(base_rarity)
    max_idx = rarity_index(max_rarity or "artifact")
    rows = [r for r in EQUIPMENT_RARITIES[min_idx:max_idx + 1] if weights.get(r, 0) > 0]
    if not rows:
        return base_rarity if base_rarity in EQUIPMENT_RARITIES else "common"
    return rng.choices(rows, weights=[weights[r] for r in rows], k=1)[0]


def affix_matches_template(affix: dict[str, Any], tpl: dict[str, Any], rarity: str) -> bool:
    if not rarity_at_least(rarity, affix.get("rarity_min", "uncommon")):
        return False
    slots = affix.get("slots") or []
    if slots and not any(equipment_slot_matches_token(tpl.get("slot"), str(slot)) for slot in slots):
        return False
    allowed_tags = set(map(str, tpl.get("affix_tags", [])))
    affix_tags = set(map(str, affix.get("tags", [])))
    if affix_tags and allowed_tags and affix_tags.isdisjoint(allowed_tags):
        return False
    excluded = set(map(str, tpl.get("exclude_affixes", [])))
    if affix.get("id") in excluded:
        return False
    return True


def choose_equipment_affixes(tpl: dict[str, Any], rarity: str, rng: random.Random) -> list[dict[str, Any]]:
    count = int(tpl.get("affix_count", EQUIPMENT_RARITY_AFFIX_COUNTS.get(rarity, 0)))
    if count <= 0 or tpl.get("fixed_rarity") or equipment_kind(tpl) == "special":
        return []
    candidates = [a for a in equipment_affix_pool() if affix_matches_template(a, tpl, rarity)]
    chosen: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    used_groups: set[str] = set()
    while candidates and len(chosen) < count:
        affix = weighted_choice(rng, candidates, lambda row: row.get("weight", 1))
        chosen.append(affix)
        used_ids.add(str(affix.get("id")))
        if affix.get("group"):
            used_groups.add(str(affix["group"]))
        candidates = [
            row for row in candidates
            if row.get("id") not in used_ids and (not row.get("group") or str(row["group"]) not in used_groups)
        ]
    return chosen


def add_number_maps(target: dict[str, int], source: dict[str, Any], multiplier: float = 1.0) -> None:
    for key, value in source.items():
        target[key] = int(target.get(key, 0) + round(float(value) * multiplier))


def subtract_number_maps(target: dict[str, int], source: dict[str, Any]) -> None:
    """Inverse of add_number_maps: subtract a removed affix's contribution back out."""
    for key, value in source.items():
        target[key] = int(target.get(key, 0) - round(float(value)))


def unique_text_list(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = str(value)
        if key and key not in seen:
            out.append(key)
            seen.add(key)
    return out


def format_equipment_name(base_name: str, affixes: list[dict[str, Any]]) -> str:
    prefixes = [a["name"] for a in affixes if a.get("position") == "prefix" and a.get("name")]
    suffixes = [a["name"] for a in affixes if a.get("position") != "prefix" and a.get("name")]
    name = base_name
    if prefixes:
        name = "".join(prefixes[:2]) + name
    if suffixes:
        name = f"{name}·{suffixes[0]}"
    return name


def affix_public_view(affix: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": affix["id"],
        "name": affix.get("name", affix["id"]),
        "stats": copy.deepcopy(affix.get("stats", {})),
        "resistances": copy.deepcopy(affix.get("resistances", {})),
        "special_effects": copy.deepcopy(affix.get("special_effects", [])),
        "durability_bonus": int(affix.get("durability_bonus", 0)),
    }


def instance_equipment(
    template_id: str,
    instance_id: str | None = None,
    *,
    rng: random.Random | None = None,
    level: int = 1,
    rarity: str | None = None,
) -> dict[str, Any]:
    tpl = template_copy("equipment", template_id)
    kind = equipment_kind(tpl)
    if kind == "special":
        final_rarity = str(tpl.get("rarity", "rare"))
        affixes: list[dict[str, Any]] = []
    else:
        final_rarity = rarity or (
            str(tpl.get("rarity", "common")) if rng is None else roll_equipment_rarity(
                rng,
                level,
                str(tpl.get("base_rarity", tpl.get("rarity", "common"))),
                tpl.get("max_rarity"),
            )
        )
        affixes = choose_equipment_affixes(tpl, final_rarity, rng or random.Random(stable_seed(template_id, instance_id or "preview")))

    stats = copy.deepcopy(tpl.get("stats", {}))
    resistances = copy.deepcopy(tpl.get("resistances", {}))
    special_effects = list(tpl.get("special_effects", []))
    durability = int(tpl.get("durability", 30))
    for affix in affixes:
        add_number_maps(stats, affix.get("stats", {}))
        add_number_maps(resistances, affix.get("resistances", {}))
        special_effects.extend(affix.get("special_effects", []))
        durability += int(affix.get("durability_bonus", 0))

    cost = int(round(float(tpl.get("cost", 0)) * EQUIPMENT_RARITY_COST_MULTIPLIER.get(final_rarity, 1.0)))
    affix_views = [affix_public_view(a) for a in affixes]
    return {
        "instance_id": instance_id or make_id("eq"),
        "template_id": tpl["id"],
        "base_name": tpl["name"],
        "name": format_equipment_name(tpl["name"], affixes),
        "slot": canonical_item_slot(tpl["slot"]),
        "rarity": final_rarity,
        "rarity_label": EQUIPMENT_RARITY_LABELS.get(final_rarity, final_rarity),
        "item_kind": kind,
        "item_kind_label": EQUIPMENT_KIND_LABELS.get(kind, kind),
        "item_level": int(tpl.get("tier", level)),
        "cost": cost,
        "stats": {k: v for k, v in stats.items() if v},
        "resistances": {k: v for k, v in resistances.items() if v},
        "special_effects": unique_text_list(special_effects),
        "affixes": affix_views,
        "durability": durability,
        "max_durability": durability,
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


def attribute_points_per_level() -> int:
    """Free attribute points granted per level. Configurable via the active preset."""
    preset = load_data().get("preset", {})
    if not isinstance(preset, dict):
        preset = {}
    raw = preset.get("attribute_points_per_level")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = ATTRIBUTE_POINTS_PER_LEVEL
    return max(0, value)


def attribute_points_earned_for_level(level: int) -> int:
    """Total free points a character has earned from leveling (level 1 => 0)."""
    return max(0, int(level) - 1) * attribute_points_per_level()


def attribute_points_spent(ch: dict[str, Any], class_row: dict[str, Any] | None = None) -> int:
    """How many free points are currently invested above the class baseline.

    `attribute_block_for_class` returns what the attributes would be with only
    level growth applied; the positive surplus on each attribute is a spent point.
    """
    if class_row is None:
        class_row = load_data().get("class_by_id", {}).get(ch.get("class_id"), {}) or {}
    level = int(ch.get("level", 1))
    expected = attribute_block_for_class(class_row, level)
    current = ch.get("attributes", {})
    total = 0
    for key in ATTRIBUTE_KEYS:
        surplus = int(current.get(key, 0)) - int(expected.get(key, 0))
        if surplus > 0:
            total += surplus
    return total


def attribute_points_available(ch: dict[str, Any], class_row: dict[str, Any] | None = None) -> int:
    """Free attribute points a character may still assign right now."""
    class_row = class_row if class_row is not None else load_data().get("class_by_id", {}).get(ch.get("class_id"), {})
    earned = attribute_points_earned_for_level(int(ch.get("level", 1)))
    return max(0, earned - attribute_points_spent(ch, class_row))


def stat_block_for_class(class_row: dict[str, Any], level: int = 1) -> dict[str, int]:
    stats = {k: int(v) for k, v in class_row.get("stats", {}).items()}
    growth = class_row.get("stat_growth", {})
    for _ in range(max(0, int(level) - 1)):
        for k, v in growth.items():
            stats[k] = int(stats.get(k, 0)) + int(v)
    if int(level) >= 2:
        stats["accuracy"] = int(stats.get("accuracy", 80)) + (int(level) - 1) // 2
    return stats


def direct_class_skill_ids(class_row: dict[str, Any]) -> list[str]:
    return [str(sid) for sid in class_row.get("skills", [])]


def base_class_id_for_class(class_id: str | None, data: dict[str, Any] | None = None) -> str:
    if not class_id:
        return ""
    data = data or load_data()
    class_row = data.get("class_by_id", {}).get(class_id or "", {})
    return str(class_row.get("base_class_id") or class_id or "")


def is_advanced_class(class_id: str | None, data: dict[str, Any] | None = None) -> bool:
    if not class_id:
        return False
    data = data or load_data()
    row = data.get("class_by_id", {}).get(class_id or "", {})
    return bool(row.get("base_class_id"))


def class_matches_restriction(class_id: str | None, restriction: list[str] | tuple[str, ...] | set[str]) -> bool:
    if not restriction:
        return True
    allowed = {str(x) for x in restriction}
    if class_id in allowed:
        return True
    base_id = base_class_id_for_class(class_id)
    return bool(base_id and base_id in allowed)


def class_skill_ids(class_row: dict[str, Any]) -> list[str]:
    data = load_data()
    ids: list[str] = []
    base_id = str(class_row.get("base_class_id") or "")
    if base_id:
        base_row = data.get("class_by_id", {}).get(base_id, {})
        ids.extend(class_skill_ids(base_row))
    ids.extend(direct_class_skill_ids(class_row))
    ids = list(dict.fromkeys(ids))
    return ids or ["basic_attack"]


def preset_skill_tree_rows(skill_tree: dict[str, Any], class_id: str | None) -> list[dict[str, Any]]:
    raw_nodes = skill_tree.get(class_id or "", []) if isinstance(skill_tree, dict) else []
    if isinstance(raw_nodes, dict):
        return [{"skill_id": sid, **(row if isinstance(row, dict) else {})} for sid, row in raw_nodes.items()]
    if isinstance(raw_nodes, list):
        return [row for row in raw_nodes if isinstance(row, dict)]
    return []


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
    raw_nodes: list[dict[str, Any]] = []
    base_id = str(class_row.get("base_class_id") or "")
    if base_id:
        raw_nodes.extend(preset_skill_tree_rows(skill_tree, base_id))
    raw_nodes.extend(preset_skill_tree_rows(skill_tree, class_id))
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


def default_skill_upgrade_scaling(skill: dict[str, Any]) -> dict[str, float]:
    stype = str(skill.get("type", "damage"))
    if is_initiative_skill(skill):
        return {"speed_formula_flat": 1, "speed_formula_max": 2}
    if stype == "damage":
        return {"power": 2, "attribute_scale": 0.012}
    if stype == "heal":
        return {"power": 3, "attribute_scale": 0.015}
    if stype == "debuff":
        return {"status_potency": 2, "status_chance": 0.03}
    if stype in {"guard", "buff", "support"}:
        return {"status_potency": 2}
    if stype == "cleanse":
        return {"uses_per_dungeon": 0.25, "mana_cost": -0.25}
    return {}


def default_skill_milestones(skill: dict[str, Any]) -> list[dict[str, Any]]:
    stype = str(skill.get("type", "damage"))
    if is_initiative_skill(skill):
        return [{
            "level": 3,
            "choices": [
                {"id": "quickened", "name": "抢占先机", "description": "速度公式获得更高基础值。", "modifiers": {"speed_formula_flat": 2}},
                {"id": "steady_rhythm", "name": "稳定节奏", "description": "速度公式上限与等级收益提高。", "modifiers": {"speed_formula_max": 4, "speed_formula_level_weight": 0.04}},
            ],
        }]
    if stype == "damage":
        return [
            {
                "level": 3,
                "choices": [
                    {"id": "force", "name": "威力强化", "description": "基础威力提高。", "modifiers": {"power": 4}},
                    {"id": "precision", "name": "精准强化", "description": "命中修正提高。", "modifiers": {"accuracy_modifier": 8}},
                ],
            },
            {
                "level": 5,
                "choices": [
                    {"id": "lethal", "name": "致命手法", "description": "暴击率与属性收益提高。", "modifiers": {"crit_chance": 0.04, "attribute_scale": 0.02}},
                    {"id": "efficient", "name": "熟练运用", "description": "次数型技能多一次使用，法力消耗小幅下降。", "modifiers": {"uses_per_dungeon": 1, "mana_cost": -1}},
                ],
            },
        ]
    if stype == "heal":
        return [
            {
                "level": 3,
                "choices": [
                    {"id": "stronger_heal", "name": "强效治疗", "description": "治疗威力提高。", "modifiers": {"power": 8}},
                    {"id": "efficient_cast", "name": "节制施法", "description": "法力消耗下降，次数型治疗多一次使用。", "modifiers": {"mana_cost": -2, "uses_per_dungeon": 1}},
                ],
            },
            {
                "level": 5,
                "choices": [
                    {"id": "protective_care", "name": "守护余韵", "description": "治疗目标获得短暂护盾。", "modifiers": {"add_status": {"type": "barrier", "duration": 1, "potency": 6}}},
                    {"id": "deep_channel", "name": "深度引导", "description": "属性收益进一步提高。", "modifiers": {"attribute_scale": 0.04}},
                ],
            },
        ]
    if stype == "cleanse":
        return [
            {
                "level": 3,
                "choices": [
                    {"id": "wide_cleanse", "name": "扩散净化", "description": "可额外影响一个目标。", "modifiers": {"target_count": 1}},
                    {"id": "light_ritual", "name": "轻灵仪式", "description": "法力消耗下降，次数型净化多一次使用。", "modifiers": {"mana_cost": -2, "uses_per_dungeon": 1}},
                ],
            },
            {
                "level": 5,
                "choices": [
                    {"id": "renewal", "name": "复苏余辉", "description": "净化后附加短暂再生。", "modifiers": {"add_status": {"type": "regeneration", "duration": 2, "potency": 4}}},
                    {"id": "ritual_mastery", "name": "仪式精通", "description": "使用次数提高。", "modifiers": {"uses_per_dungeon": 2}},
                ],
            },
        ]
    if stype == "debuff":
        return [
            {
                "level": 3,
                "choices": [
                    {"id": "reliable_hex", "name": "稳定压制", "description": "命中与状态成功率提高。", "modifiers": {"accuracy_modifier": 6, "status_chance": 0.15}},
                    {"id": "deep_hex", "name": "深层削弱", "description": "负面状态强度提高。", "modifiers": {"status_potency": 6}},
                ],
            },
            {
                "level": 5,
                "choices": [
                    {"id": "lingering_hex", "name": "延时压制", "description": "状态持续时间提高。", "modifiers": {"status_duration": 1}},
                    {"id": "expose_weakness", "name": "暴露弱点", "description": "额外附加脆弱。", "modifiers": {"add_status": {"type": "vulnerable", "duration": 2, "potency": 10, "chance": 0.7}}},
                ],
            },
        ]
    if stype in {"guard", "buff", "support"}:
        return [
            {
                "level": 3,
                "choices": [
                    {"id": "reinforced", "name": "强化效果", "description": "状态强度提高。", "modifiers": {"status_potency": 6}},
                    {"id": "lasting", "name": "持续效果", "description": "状态持续时间提高。", "modifiers": {"status_duration": 1}},
                ],
            },
            {
                "level": 5,
                "choices": [
                    {"id": "practiced", "name": "熟练应对", "description": "次数型技能多一次使用。", "modifiers": {"uses_per_dungeon": 1}},
                    {"id": "warded", "name": "护佑余波", "description": "额外附加少量护盾。", "modifiers": {"add_status": {"type": "barrier", "duration": 1, "potency": 5}}},
                ],
            },
        ]
    return []


def skill_upgrade_spec(skill: dict[str, Any]) -> dict[str, Any]:
    raw = skill.get("upgrade", {})
    raw = raw if isinstance(raw, dict) else {}
    cost_curve = raw.get("cost_curve", DEFAULT_SKILL_UPGRADE_COSTS)
    if not isinstance(cost_curve, list) or not cost_curve:
        cost_curve = DEFAULT_SKILL_UPGRADE_COSTS
    scaling = raw.get("scaling")
    if not isinstance(scaling, dict):
        scaling = default_skill_upgrade_scaling(skill)
    milestones = raw.get("milestones")
    if not isinstance(milestones, list):
        milestones = default_skill_milestones(skill)
    max_level = max(1, int(raw.get("max_level", DEFAULT_SKILL_MAX_LEVEL)))
    if skill.get("id") == "basic_attack":
        max_level = min(max_level, 3)
    return {
        "max_level": max_level,
        "cost_curve": [max(0, int(x)) for x in cost_curve],
        "scaling": copy.deepcopy(scaling),
        "milestones": copy.deepcopy(milestones),
    }


def skill_upgrade_row(ch: dict[str, Any], skill_id: str) -> dict[str, Any]:
    raw_map = ch.get("skill_upgrades", {})
    raw = raw_map.get(skill_id) if isinstance(raw_map, dict) else None
    if isinstance(raw, dict):
        level = int(raw.get("level", 1))
        choices = raw.get("choices", {})
        if not isinstance(choices, dict):
            choices = {}
    elif isinstance(raw, (int, float)):
        level = int(raw)
        choices = {}
    else:
        level = 1
        choices = {}
    skill = load_data()["skill_by_id"].get(skill_id, {})
    max_level = int(skill_upgrade_spec(skill).get("max_level", DEFAULT_SKILL_MAX_LEVEL))
    clean_choices = {str(k): str(v) for k, v in choices.items() if str(v)}
    return {"level": max(1, min(max_level, level)), "choices": clean_choices}


def normalize_skill_upgrades(ch: dict[str, Any]) -> None:
    learned = set(ch.get("learned_skills", []))
    raw = ch.get("skill_upgrades", {})
    if not isinstance(raw, dict):
        raw = {}
    clean: dict[str, dict[str, Any]] = {}
    for sid in learned:
        row = skill_upgrade_row({**ch, "skill_upgrades": raw}, sid)
        if row["level"] > 1 or row["choices"]:
            clean[sid] = row
    ch["skill_upgrades"] = clean


def skill_level_for_character(ch: dict[str, Any], skill_id: str) -> int:
    return int(skill_upgrade_row(ch, skill_id).get("level", 1))


def skill_upgrade_cost(skill: dict[str, Any], current_level: int) -> int:
    spec = skill_upgrade_spec(skill)
    costs = spec.get("cost_curve", DEFAULT_SKILL_UPGRADE_COSTS)
    if current_level >= int(spec.get("max_level", DEFAULT_SKILL_MAX_LEVEL)):
        return 0
    idx = max(0, current_level - 1)
    if idx < len(costs):
        return int(costs[idx])
    return int(costs[-1]) + (idx - len(costs) + 1) * 8


def skill_milestone_for_level(skill: dict[str, Any], level: int) -> dict[str, Any] | None:
    for raw in skill_upgrade_spec(skill).get("milestones", []):
        if isinstance(raw, dict) and int(raw.get("level", 0)) == level:
            return copy.deepcopy(raw)
    return None


def skill_upgrade_choices_for_level(skill: dict[str, Any], level: int) -> list[dict[str, Any]]:
    milestone = skill_milestone_for_level(skill, level)
    choices = milestone.get("choices", []) if milestone else []
    return [copy.deepcopy(c) for c in choices if isinstance(c, dict) and c.get("id")]


def clamp_float(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def add_skill_modifier(skill: dict[str, Any], field: str, delta: Any) -> None:
    if field == "add_status" and isinstance(delta, dict):
        skill.setdefault("status_effects", [])
        if isinstance(skill["status_effects"], list):
            skill["status_effects"].append(copy.deepcopy(delta))
        return
    if field == "status_potency":
        for st in skill.get("status_effects", []):
            if isinstance(st, dict):
                st["potency"] = max(0, int(round(float(st.get("potency", 0)) + float(delta))))
        return
    if field == "status_duration":
        for st in skill.get("status_effects", []):
            if isinstance(st, dict):
                st["duration"] = max(1, int(round(float(st.get("duration", 1)) + float(delta))))
        return
    if field == "status_chance":
        for st in skill.get("status_effects", []):
            if isinstance(st, dict) and "chance" in st:
                st["chance"] = round(clamp_float(float(st.get("chance", 1.0)) + float(delta), 0.05, 1.0), 3)
        return
    if field.startswith("speed_formula_") and isinstance(skill.get("speed_formula"), dict):
        speed_field = field.replace("speed_formula_", "")
        if speed_field == "flat":
            base_key = "flat" if "flat" in skill["speed_formula"] else "base"
        elif speed_field == "level_weight":
            base_key = "level_weight"
        elif speed_field == "max":
            base_key = "max"
        else:
            base_key = speed_field
        skill["speed_formula"][base_key] = round(float(skill["speed_formula"].get(base_key, 0)) + float(delta), 3)
        return
    if field == "target_count":
        skill[field] = max(1, int(skill.get(field, 1)) + int(delta))
        return
    if field in {"power", "accuracy_modifier", "uses_per_dungeon", "mana_cost"}:
        if field == "uses_per_dungeon" and int(skill.get(field, 999)) >= 999:
            return
        skill[field] = max(0 if field == "mana_cost" else 1, int(round(float(skill.get(field, 0)) + float(delta))))
        return
    if field in {"attribute_scale", "ignore_defense", "defense_factor", "crit_chance", "crit_multiplier", "execute_bonus", "status_bonus"}:
        skill[field] = round(float(skill.get(field, 0)) + float(delta), 3)


def apply_skill_modifiers(skill: dict[str, Any], modifiers: dict[str, Any], multiplier: float = 1.0) -> None:
    for field, delta in modifiers.items():
        if isinstance(delta, (int, float)):
            add_skill_modifier(skill, str(field), float(delta) * multiplier)
        else:
            add_skill_modifier(skill, str(field), delta)


def upgraded_skill_for_character(ch: dict[str, Any], skill_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    data = data or load_data()
    base = copy.deepcopy(data["skill_by_id"].get(skill_id, {}))
    if not base:
        return base
    row = skill_upgrade_row(ch, skill_id)
    level = int(row.get("level", 1))
    spec = skill_upgrade_spec(base)
    if level > 1:
        apply_skill_modifiers(base, spec.get("scaling", {}), level - 1)
    choices = row.get("choices", {})
    if isinstance(choices, dict):
        for raw_level, choice_id in choices.items():
            try:
                milestone_level = int(raw_level)
            except ValueError:
                continue
            if milestone_level > level:
                continue
            choice = next((c for c in skill_upgrade_choices_for_level(base, milestone_level) if str(c.get("id")) == str(choice_id)), None)
            if choice and isinstance(choice.get("modifiers"), dict):
                apply_skill_modifiers(base, choice["modifiers"])
    base["upgrade_level"] = level
    base["upgrade_max_level"] = int(spec.get("max_level", DEFAULT_SKILL_MAX_LEVEL))
    return base


def skill_upgrade_status(state: dict[str, Any], ch: dict[str, Any], skill_id: str) -> dict[str, Any]:
    data = load_data()
    skill = data["skill_by_id"].get(skill_id)
    if not skill:
        return {"upgradeable": False, "reason": "技能不存在"}
    if skill_id not in ch.get("learned_skills", []):
        return {"upgradeable": False, "reason": "需要先学习该技能"}
    row = skill_upgrade_row(ch, skill_id)
    current = int(row.get("level", 1))
    spec = skill_upgrade_spec(skill)
    max_level = int(spec.get("max_level", DEFAULT_SKILL_MAX_LEVEL))
    if current >= max_level:
        return {"upgradeable": False, "reason": "已达最高等级", "level": current, "max_level": max_level}
    cost = skill_upgrade_cost(skill, current)
    essence = int(state.get("materials", {}).get(SKILL_ESSENCE_KEY, 0))
    next_level = current + 1
    choices = skill_upgrade_choices_for_level(skill, next_level)
    if essence < cost:
        return {
            "upgradeable": False,
            "reason": f"技能精华不足：需要 {cost}，当前 {essence}",
            "level": current,
            "max_level": max_level,
            "cost": cost,
            "choices": choices,
        }
    return {
        "upgradeable": True,
        "reason": "可升级",
        "level": current,
        "max_level": max_level,
        "cost": cost,
        "choices": choices,
    }


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
        spent = max(0, final - expected_value)
        out[key] = {
            "base": base,
            "level_growth": expected_value - base,
            "raw": expected_value,
            "bonus": final - expected_value,
            "final": final,
            "spent": spent,
            "growth_per_level": int(class_row.get("attribute_growth", {}).get(key, 0)),
            "growth_text": f"+{int(class_row.get('attribute_growth', {}).get(key, 0))}/级" if int(class_row.get("attribute_growth", {}).get(key, 0)) else "—",
        }
    return out


def class_preset_meta(class_id: str | None) -> dict[str, Any]:
    """UI/tactical metadata supplied by the active preset."""
    if not class_id:
        return {}
    data = load_data()
    meta = data.get("class_ui_by_id", {}).get(class_id, {})
    if isinstance(meta, dict) and meta:
        return meta
    base_id = base_class_id_for_class(class_id, data)
    if base_id and base_id != class_id:
        base_meta = data.get("class_ui_by_id", {}).get(base_id, {})
        return base_meta if isinstance(base_meta, dict) else {}
    return {}


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


def consumable_template(consumable_id: str | None) -> dict[str, Any] | None:
    """Data-driven consumable template (id/name/effect) or None if unknown."""
    if not consumable_id:
        return None
    row = load_data().get("consumable_by_id", {}).get(consumable_id)
    return row if isinstance(row, dict) else None


def consumable_name(consumable_id: str | None) -> str:
    row = consumable_template(consumable_id)
    return row.get("name", consumable_id or "") if row else (consumable_id or "")


def consumable_effect(consumable_id: str | None) -> dict[str, Any] | None:
    """Resolved effect block {heal:int} and/or {cleanse:[status]} or None."""
    row = consumable_template(consumable_id)
    if not row:
        return None
    effect = row.get("effect")
    return effect if isinstance(effect, dict) else None


def consumable_options_view() -> list[dict[str, Any]]:
    """All known consumables as {id, name, summary, effect} for tactic UI dropdowns."""
    out: list[dict[str, Any]] = []
    for cid, row in load_data().get("consumable_by_id", {}).items():
        if not isinstance(row, dict):
            continue
        out.append({
            "id": cid,
            "name": row.get("name", cid),
            "summary": row.get("summary", ""),
            "effect": copy.deepcopy(row.get("effect", {})),
        })
    return out


def clean_consumable_priority(values: Any) -> list[dict[str, str]]:
    """Validate a character's consumable_priority tactic list.

    Drops entries with unknown consumable ids or triggers and de-dupes by
    consumable id (a given consumable can only sit in one slot).
    """
    if not isinstance(values, list):
        return []
    data = load_data()
    known_ids = set(data.get("consumable_by_id", {}).keys())
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in values:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("consumable_id") or "")
        trigger = str(entry.get("trigger") or "")
        if not cid or cid not in known_ids or cid in seen:
            continue
        if trigger not in CONSUMABLE_TRIGGERS:
            continue
        out.append({"consumable_id": cid, "trigger": trigger})
        seen.add(cid)
    return out[:MAX_CONSUMABLE_SLOTS]


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
    consumable_priority = clean_consumable_priority(meta.get("default_consumable_priority") or _default_consumable_priority_for_class(class_id, class_row))
    return {
        "target_priority": default_target_priority_for_class(class_id),
        "initiative_skill": initiative_skill,
        "skill_priority": clean_tactic_skill_list(meta.get("default_skill_priority", []), known_skills, 8),
        "opening_skill_priority": clean_tactic_skill_list(meta.get("default_opening_skill_priority", []), known_skills, 4),
        "defense_skill_by_type": defense,
        "consumable_priority": consumable_priority,
    }


def _default_consumable_priority_for_class(class_id: str | None, class_row: dict[str, Any]) -> list[dict[str, str]]:
    """Sensible auto-use defaults when a preset doesn't configure them.

    Front-liners (warrior/guardian) chug a healing potion when badly hurt; the
    support line (cleric) keeps an antidote handy. Others start with nothing so
    the player opts in deliberately.
    """
    base_id = base_class_id_for_class(class_id)
    if base_id in {"warrior", "guardian"}:
        return [{"consumable_id": "healing_potion", "trigger": "self_hp_below_30"}]
    if base_id in {"cleric", "mage"}:
        return [{"consumable_id": "antidote", "trigger": "self_poisoned"}]
    return []


def normalize_character(ch: dict[str, Any]) -> dict[str, Any]:
    """Migrate older saves in-place to the richer attribute/skill schema."""
    data = load_data()
    class_row = data["class_by_id"].get(ch.get("class_id"))
    if not class_row:
        return ch
    if class_row.get("base_class_id"):
        ch["base_class_id"] = str(class_row.get("base_class_id"))
        ch.setdefault("class_path", [ch["base_class_id"], ch.get("class_id")])
    else:
        ch.setdefault("base_class_id", ch.get("class_id"))
        if not isinstance(ch.get("class_path"), list):
            ch["class_path"] = [ch.get("class_id")]
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
    normalize_skill_upgrades(ch)
    old_equipment = ch.get("equipment", {})
    if not isinstance(old_equipment, dict):
        old_equipment = {}
    equipment = default_character_equipment()
    for slot, item_id in old_equipment.items():
        if slot in CHARACTER_EQUIPMENT_SLOTS:
            equipment[slot] = item_id
        elif slot == "weapon":
            equipment["main_hand"] = item_id
        elif slot == "armor":
            equipment["body"] = item_id
        elif slot == "trinket":
            equipment["ring_1"] = item_id
    ch["equipment"] = equipment
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
    if "consumable_priority" not in ch["tactics"] or not isinstance(ch["tactics"].get("consumable_priority"), list):
        ch["tactics"]["consumable_priority"] = copy.deepcopy(default_tactics["consumable_priority"])
    ch["tactics"]["consumable_priority"] = clean_consumable_priority(ch["tactics"].get("consumable_priority", []))
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


def skill_public_summary(ch: dict[str, Any], state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    normalize_character(ch)
    data = load_data()
    learned = set(ch.get("learned_skills", []))
    tree = class_skill_tree_node_map(ch.get("class_id"))
    rows: list[dict[str, Any]] = []
    for sid in ch.get("skills", []):
        base_skill = data["skill_by_id"].get(sid)
        if not base_skill:
            continue
        skill = upgraded_skill_for_character(ch, sid, data)
        req = skill_level_requirement(base_skill)
        node = tree.get(sid, {})
        prereqs = list(node.get("prerequisites", [])) if isinstance(node.get("prerequisites", []), list) else []
        unlockable, unlock_reason = skill_unlock_status(ch, sid)
        upgrade_status = skill_upgrade_status(state, ch, sid) if state is not None else {}
        upgrade_row = skill_upgrade_row(ch, sid)
        upgrade_level = int(upgrade_row.get("level", 1))
        upgrade_max = int(skill_upgrade_spec(base_skill).get("max_level", DEFAULT_SKILL_MAX_LEVEL))
        upgrade_cost = 0 if upgrade_level >= upgrade_max else skill_upgrade_cost(base_skill, upgrade_level)
        next_level = min(upgrade_max, upgrade_level + 1)
        next_choices = skill_upgrade_choices_for_level(base_skill, next_level) if upgrade_level < upgrade_max else []
        selected_choice_names: dict[str, str] = {}
        for raw_level, choice_id in upgrade_row.get("choices", {}).items():
            try:
                milestone_level = int(raw_level)
            except ValueError:
                milestone_level = 0
            choice = next((c for c in skill_upgrade_choices_for_level(base_skill, milestone_level) if str(c.get("id")) == str(choice_id)), None)
            selected_choice_names[str(raw_level)] = str(choice.get("name", choice_id)) if choice else str(choice_id)
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
            "skill_level": upgrade_level,
            "skill_max_level": upgrade_max,
            "skill_upgrade_cost": upgrade_cost,
            "skill_upgrade_currency": SKILL_ESSENCE_KEY,
            "skill_upgrade_currency_name": MATERIAL_NAMES[SKILL_ESSENCE_KEY],
            "skill_upgradeable": bool(upgrade_status.get("upgradeable")) if upgrade_status else False,
            "skill_upgrade_reason": str(upgrade_status.get("reason", "")) if upgrade_status else "",
            "skill_upgrade_choices": copy.deepcopy(upgrade_status.get("choices", next_choices)) if upgrade_status else next_choices,
            "skill_selected_upgrade_choices": copy.deepcopy(upgrade_row.get("choices", {})),
            "skill_selected_upgrade_choice_names": selected_choice_names,
        })
    return rows


def promotion_cost_rows(costs: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, raw in costs.items():
        amount = max(0, int(raw))
        if amount <= 0:
            continue
        rows.append({"key": key, "name": MATERIAL_NAMES.get(key, key), "amount": amount})
    return rows


def promotion_requirements(class_row: dict[str, Any]) -> tuple[int, dict[str, int], str]:
    promo = class_row.get("promotion", {}) if isinstance(class_row.get("promotion", {}), dict) else {}
    level_required = max(1, int(promo.get("level_required", DEFAULT_PROMOTION_LEVEL)))
    raw_costs = promo.get("materials", {PROMOTION_BADGE_KEY: 1})
    if not isinstance(raw_costs, dict):
        raw_costs = {PROMOTION_BADGE_KEY: 1}
    costs = {str(k): max(0, int(v)) for k, v in raw_costs.items() if int(v) > 0}
    return level_required, costs, str(promo.get("description", ""))


def promotion_options_for_character(state: dict[str, Any], ch: dict[str, Any]) -> list[dict[str, Any]]:
    normalize_character(ch)
    data = load_data()
    current_id = str(ch.get("class_id") or "")
    current_row = data.get("class_by_id", {}).get(current_id, {})
    if not current_row or current_row.get("base_class_id"):
        return []
    materials = state.setdefault("materials", {})
    base_id = current_id
    rows = [
        c for c in data.get("classes", [])
        if str(c.get("base_class_id") or "") == base_id and c.get("is_advanced")
    ]
    rows.sort(key=lambda c: (int(c.get("promotion", {}).get("order", 99)) if isinstance(c.get("promotion"), dict) else 99, str(c.get("name", ""))))

    out: list[dict[str, Any]] = []
    for row in rows:
        target_id = str(row.get("id") or "")
        level_required, costs, description = promotion_requirements(row)
        reasons: list[str] = []
        if int(ch.get("level", 1)) < level_required:
            reasons.append(f"需要 Lv.{level_required}")
        missing = []
        for key, amount in costs.items():
            owned = int(materials.get(key, 0))
            if owned < amount:
                missing.append(f"{MATERIAL_NAMES.get(key, key)} {owned}/{amount}")
        if missing:
            reasons.append("材料不足：" + "、".join(missing))
        skill_ids = direct_class_skill_ids(row)
        out.append({
            "class_id": target_id,
            "name": row.get("name", target_id),
            "role": row.get("role", ""),
            "base_class_id": base_id,
            "description": description,
            "level_required": level_required,
            "cost": costs,
            "cost_rows": promotion_cost_rows(costs),
            "can_promote": not reasons,
            "reason": "；".join(reasons) if reasons else "可转职",
            "skill_ids": skill_ids,
            "skill_names": [data["skill_by_id"].get(sid, {}).get("name", sid) for sid in skill_ids],
            "class_meta": class_preset_meta(target_id),
            "stat_growth": copy.deepcopy(row.get("stat_growth", {})),
            "attribute_growth": copy.deepcopy(row.get("attribute_growth", {})),
        })
    return out


def character_promotion_summary(state: dict[str, Any], ch: dict[str, Any]) -> dict[str, Any]:
    normalize_character(ch)
    data = load_data()
    current_id = str(ch.get("class_id") or "")
    current_row = data.get("class_by_id", {}).get(current_id, {})
    base_id = str(ch.get("base_class_id") or current_row.get("base_class_id") or current_id)
    base_row = data.get("class_by_id", {}).get(base_id, {})
    promoted = bool(current_row.get("base_class_id"))
    path = [{"class_id": base_id, "name": base_row.get("name", base_id)}]
    if promoted:
        path.append({"class_id": current_id, "name": current_row.get("name", current_id)})
    return {
        "promoted": promoted,
        "base_class_id": base_id,
        "base_class_name": base_row.get("name", base_id),
        "current_class_id": current_id,
        "current_class_name": current_row.get("name", ch.get("class_name", current_id)),
        "promotion_level": ch.get("promotion_level") or ch.get("promoted_at_level"),
        "path": path,
        "options": [] if promoted else promotion_options_for_character(state, ch),
    }


def create_character(class_id: str, name: str, char_id: str | None = None) -> dict[str, Any]:
    data = load_data()
    c = copy.deepcopy(data["class_by_id"][class_id])
    stats = stat_block_for_class(c, 1)
    base_id = base_class_id_for_class(class_id, data)
    ch = {
        "id": char_id or make_id("ch"),
        "name": name,
        "class_id": class_id,
        "class_name": c["name"],
        "base_class_id": base_id,
        "class_path": [base_id] + ([class_id] if class_id != base_id else []),
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
        "skill_upgrades": {},
        "equipment": default_character_equipment(),
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
        "materials": {
            SKILL_ESSENCE_KEY: STARTING_SKILL_ESSENCE,
            PROMOTION_BADGE_KEY: STARTING_PROMOTION_BADGES,
            "leather": 2,
            "ore": 2,
            "venom_sac": 0,
            "cloth": 0,
        },
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
        # Shop and recruitment are now independent systems with separate state
        # keys. `shop` holds per-merchant stock (refreshed daily); `recruits`
        # holds the tavern candidate pool (refreshed daily).
        "shop": {"merchants": {}, "refresh_day": 0},
        "recruits": {"candidates": [], "refresh_day": 0},
        "last_result": None,
        "victory": False,
        "defeat": False,
        "defeat_reason": None,
        "final_unlocked": False,
        # Quest system runtime state. Templates live in data; these hold the
        # player's instances, progress counters, story flags, and daily refresh.
        "quests": [],
        "quest_flags": {},
        "quest_stats": default_quest_stats(),
        "daily_quest_day": 0,
        "next_counters": {"dungeon": 1, "plan": 1, "report": 1, "quest": 1},
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
    refresh_recruits(state)
    world_refresh(state, first_day=True)
    init_quests(state)
    return state


def get_character(state: dict[str, Any], char_id: str) -> dict[str, Any] | None:
    return next((c for c in state["characters"] if c["id"] == char_id), None)


def get_item(state: dict[str, Any], item_id: str) -> dict[str, Any] | None:
    return next((i for i in state["inventory"] if i["instance_id"] == item_id), None)


# ===========================================================================
# Quest system
# ===========================================================================
# Quest templates come from the active preset's quests.json (see data.py).
# The engine owns the runtime: instantiating templates into player quests,
# evaluating objectives when dungeons are cleared/scouted, refreshing daily
# quests each day, revealing hidden quests, advancing story chains, and
# granting rewards on claim. Save-state keys: quests / quest_flags /
# quest_stats / daily_quest_day / next_counters["quest"].

def default_quest_stats() -> dict[str, Any]:
    """Zeroed quest progress aggregates backing objective evaluation."""
    return {
        "completed_quests": {},
        "claimed_quests": {},
        "dungeon_cleared_by_template": {},
        "dungeon_scouted_by_template": {},
        "dungeon_challenged_by_template": {},
        "hidden_completed": 0,
    }


def _quest_data() -> dict[str, Any]:
    return load_data().get("quests", {}) or {}


def quest_template_by_id(template_id: str) -> dict[str, Any] | None:
    return load_data().get("quest_template_by_id", {}).get(template_id)


def _next_quest_instance_id(state: dict[str, Any]) -> str:
    counters = state.setdefault("next_counters", {})
    counter = int(counters.get("quest", 1))
    counters["quest"] = counter + 1
    return f"quest_{counter:04d}"


def _instantiate_objective(obj_tpl: dict[str, Any]) -> dict[str, Any]:
    """Copy a template objective into a runtime objective with current=0."""
    obj = copy.deepcopy(obj_tpl)
    obj["current"] = 0
    obj["completed"] = False
    obj.setdefault("required", 1)
    return obj


def _resolve_daily_gold(rng: random.Random, rewards_tpl: dict[str, Any]) -> int:
    gold = rewards_tpl.get("gold", QUEST_DEFAULT_DAILY_GOLD_RANGE[0])
    if isinstance(gold, dict):
        lo = int(gold.get("min", QUEST_DEFAULT_DAILY_GOLD_RANGE[0]))
        hi = int(gold.get("max", QUEST_DEFAULT_DAILY_GOLD_RANGE[1]))
        return rng.randint(lo, hi) if hi >= lo else lo
    return int(gold)


def _resolve_rewards(rewards_tpl: dict[str, Any], rng: random.Random | None = None) -> dict[str, Any]:
    """Resolve a reward template into concrete values (daily gold is randomized)."""
    rewards = copy.deepcopy(rewards_tpl or {})
    rewards.setdefault("gold", 0)
    rewards.setdefault("exp", 0)
    rewards.setdefault("materials", {})
    rewards.setdefault("flags", {})
    rewards.setdefault("equipment", [])
    if rng is not None and isinstance(rewards.get("gold"), dict):
        rewards["gold"] = _resolve_daily_gold(rng, rewards)
    return rewards


def _equipment_reward_id(spec: Any) -> str:
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        return str(spec.get("id") or spec.get("equipment_id") or spec.get("template_id") or "")
    return ""


def _instantiate_equipment_reward(
    spec: Any,
    *,
    rng: random.Random | None = None,
    level: int = 1,
    instance_id: str | None = None,
) -> dict[str, Any] | None:
    """Instantiate one data-driven equipment reward/drop spec.

    Reusable spec forms:
      - "equipment_id"
      - {"id": "equipment_id", "rarity": "rare", "level": 3}
    Unknown ids are ignored by callers, letting custom presets omit optional
    drops without crashing a run.
    """
    equipment_id = _equipment_reward_id(spec)
    if not equipment_id or equipment_id not in load_data().get("equipment_by_id", {}):
        return None
    rarity = str(spec.get("rarity")) if isinstance(spec, dict) and spec.get("rarity") else None
    reward_level = int(spec.get("level", level)) if isinstance(spec, dict) else level
    return instance_equipment(equipment_id, instance_id=instance_id, rng=rng, level=reward_level, rarity=rarity)


def _equipment_reward_public_view(spec: Any, index: int = 0) -> dict[str, Any] | None:
    equipment_id = _equipment_reward_id(spec)
    tpl = load_data().get("equipment_by_id", {}).get(equipment_id)
    if not tpl:
        return None
    rarity = str(spec.get("rarity")) if isinstance(spec, dict) and spec.get("rarity") else None
    level = int(spec.get("level", tpl.get("tier", 1))) if isinstance(spec, dict) else int(tpl.get("tier", 1))
    rng = random.Random(stable_seed("equipment_reward_preview", equipment_id, str(rarity or ""), str(level), str(index)))
    preview = _instantiate_equipment_reward(spec, rng=rng, level=level, instance_id=f"preview_{equipment_id}_{index}")
    return {
        "id": equipment_id,
        "name": tpl.get("name", equipment_id),
        "rarity": rarity or tpl.get("rarity", "common"),
        "preview": preview,
    }


def grant_equipment_rewards(
    state: dict[str, Any],
    specs: list[Any],
    *,
    rng: random.Random | None = None,
    level: int = 1,
) -> list[dict[str, Any]]:
    """Grant a list of fixed equipment rewards/drops and return public snapshots."""
    granted: list[dict[str, Any]] = []
    for spec in specs or []:
        eq = _instantiate_equipment_reward(spec, rng=rng, level=level)
        if not eq:
            continue
        state.setdefault("inventory", []).append(eq)
        granted.append({"name": eq["name"], "item": copy.deepcopy(eq)})
    return granted


def _quest_status_label(status: str) -> str:
    return QUEST_STATUS_LABELS.get(status, status)


def instantiate_story_quest(state: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Story/hidden quests keep their template id as instance id (one per playthrough)."""
    objectives = [_instantiate_objective(o) for o in template.get("objectives", [])]
    return {
        "id": template["id"],
        "template_id": template["id"],
        "type": template.get("type", QUEST_TYPE_STORY),
        "story_kind": template.get("story_kind", ""),
        "chain_id": template.get("chain_id", ""),
        "title": template.get("title", template["id"]),
        "description": template.get("description", ""),
        "status": "available",
        "created_day": state.get("day", 1),
        "accepted_day": None,
        "expires_day": None,
        "objectives": objectives,
        "rewards": _resolve_rewards(template.get("rewards")),
        "next_quests": list(template.get("next_quests", [])),
        "guide_sections": copy.deepcopy(template.get("guide_sections", [])),
        "guide_steps": copy.deepcopy(template.get("guide_steps", [])),
        "dialogue": copy.deepcopy(template.get("dialogue", [])),
        "auto_reveal_on_complete": bool(template.get("auto_reveal_on_complete", False)),
        "revealed_from_hidden": False,
        "sort": int(template.get("sort", 0)),
        "linked_dungeon_ids": [],
    }


def instantiate_daily_quest(state: dict[str, Any], template: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """Daily quests get a fresh instance id each day and randomized gold."""
    objectives = [_instantiate_objective(o) for o in template.get("objectives", [])]
    day = state.get("day", 1)
    return {
        "id": _next_quest_instance_id(state),
        "template_id": template["id"],
        "type": QUEST_TYPE_DAILY,
        "story_kind": "",
        "chain_id": "",
        "title": template.get("title", template["id"]),
        "description": template.get("description", ""),
        "status": "available",
        "created_day": day,
        "accepted_day": None,
        "expires_day": day + QUEST_DEFAULT_EXPIRY_DAYS - 1,
        "objectives": objectives,
        "rewards": _resolve_rewards(template.get("rewards"), rng=rng),
        "next_quests": [],
        "guide_sections": copy.deepcopy(template.get("guide_sections", [])),
        "guide_steps": copy.deepcopy(template.get("guide_steps", [])),
        "dialogue": copy.deepcopy(template.get("dialogue", [])),
        "auto_reveal_on_complete": False,
        "revealed_from_hidden": False,
        "sort": 0,
        "linked_dungeon_ids": [],
    }


def _quest_exists(state: dict[str, Any], quest_id: str) -> bool:
    return any(q.get("id") == quest_id for q in state.get("quests", []))


def _get_quest(state: dict[str, Any], quest_id: str) -> dict[str, Any] | None:
    return next((q for q in state.get("quests", []) if q.get("id") == quest_id), None)


def _eval_condition(state: dict[str, Any], cond: dict[str, Any]) -> bool:
    """Evaluate one reveal/start condition. Unknown types are treated as False."""
    ctype = cond.get("type")
    if ctype in (QUEST_COND_ALWAYS_TRUE, "always", True):
        return True
    if ctype == QUEST_COND_FLAG:
        return bool(state.get("quest_flags", {}).get(cond.get("flag")))
    if ctype == QUEST_COND_QUEST_COMPLETED:
        return _is_quest_template_completed(state, cond.get("quest"))
    if ctype == QUEST_COND_HIDDEN_COMPLETED_GTE:
        return int(state.get("quest_stats", {}).get("hidden_completed", 0)) >= int(cond.get("value", 1))
    return False


def _conditions_met(state: dict[str, Any], conditions: list[dict[str, Any]] | None) -> bool:
    if not conditions:
        return True
    return all(_eval_condition(state, c) for c in conditions)


def _is_quest_template_completed(state: dict[str, Any], template_id: str) -> bool:
    """A template is 'completed' if any of its instances reached completed/claimed."""
    return any(
        q.get("template_id") == template_id and q.get("status") in {"completed", "claimed"}
        for q in state.get("quests", [])
    )


def normalize_quest_instances(state: dict[str, Any]) -> None:
    """Backfill/normalize quest instance fields after loading a save."""
    quests = state.get("quests", [])
    if not isinstance(quests, list):
        state["quests"] = []
        quests = []
    for q in quests:
        if not isinstance(q, dict):
            continue
        q.setdefault("template_id", q.get("id", ""))
        template = quest_template_by_id(q.get("template_id", "")) or {}
        q.setdefault("type", QUEST_TYPE_STORY)
        q.setdefault("story_kind", "")
        q.setdefault("chain_id", "")
        q.setdefault("status", "available")
        q.setdefault("accepted_day", None)
        q.setdefault("expires_day", None)
        q.setdefault("next_quests", [])
        q.setdefault("guide_sections", [])
        q.setdefault("guide_steps", [])
        q.setdefault("dialogue", [])
        if not q.get("guide_sections") and template.get("guide_sections"):
            q["guide_sections"] = copy.deepcopy(template.get("guide_sections", []))
        if not q.get("guide_steps") and template.get("guide_steps"):
            q["guide_steps"] = copy.deepcopy(template.get("guide_steps", []))
        if not q.get("dialogue") and template.get("dialogue"):
            q["dialogue"] = copy.deepcopy(template.get("dialogue", []))
        q.setdefault("auto_reveal_on_complete", False)
        q.setdefault("revealed_from_hidden", False)
        q.setdefault("sort", 0)
        q.setdefault("linked_dungeon_ids", [])
        q.setdefault("rewards", {})
        objectives = q.get("objectives", [])
        for obj in objectives:
            if not isinstance(obj, dict):
                continue
            obj.setdefault("current", 0)
            obj.setdefault("completed", False)
            obj.setdefault("required", 1)
            obj.setdefault("kind", QUEST_OBJ_CLEAR_DUNGEON)
            obj["current"] = int(obj.get("current", 0))
            obj["required"] = max(1, int(obj.get("required", 1)))
            obj["completed"] = bool(obj.get("completed")) or obj["current"] >= obj["required"]
        q["objectives"] = objectives


def init_quests(state: dict[str, Any]) -> None:
    """Seed a fresh run: reveal eligible story quests and roll the first daily set."""
    normalize_quest_instances(state)
    _reveal_eligible_story_quests(state)
    state["daily_quest_day"] = 0  # force a refresh on day 1
    refresh_daily_quests(state)
    check_hidden_reveals(state)


def _reveal_eligible_story_quests(state: dict[str, Any]) -> None:
    """Instantiate story quests whose start_conditions are met and not yet present."""
    for template in load_data().get("story_quests", []):
        if not isinstance(template, dict) or not template.get("id"):
            continue
        if _quest_exists(state, template["id"]):
            continue
        if not _conditions_met(state, template.get("start_conditions")):
            continue
        state["quests"].append(instantiate_story_quest(state, template))


def refresh_daily_quests(state: dict[str, Any]) -> None:
    """Expire old daily quests and roll a fresh set when the day advances."""
    day = state.get("day", 1)
    if state.get("daily_quest_day") == day:
        return
    # Expire any daily quest not yet completed/claimed.
    for q in state.get("quests", []):
        if q.get("type") == QUEST_TYPE_DAILY and q.get("status") in {"available", "active"}:
            q["status"] = "expired"
            q["expires_day"] = day - 1
    daily_templates = list(load_data().get("daily_templates", []))
    count = int(load_data().get("daily_quest_count", QUEST_DEFAULT_DAILY_COUNT))
    if not daily_templates or count <= 0:
        state["daily_quest_day"] = day
        return
    rng = random.Random(stable_seed(state["run_seed"], "daily_quest", day))
    # Sample without replacement when possible, otherwise allow repeats.
    picks = rng.sample(daily_templates, min(count, len(daily_templates)))
    if len(picks) < count:
        picks += [rng.choice(daily_templates) for _ in range(count - len(picks))]
    for template in picks:
        state["quests"].append(instantiate_daily_quest(state, template, rng))
    state["daily_quest_day"] = day


def check_hidden_reveals(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Reveal hidden quests whose reveal_conditions are now satisfied."""
    revealed: list[dict[str, Any]] = []
    for template in load_data().get("hidden_quests", []):
        if not isinstance(template, dict) or not template.get("id"):
            continue
        if _quest_exists(state, template["id"]):
            continue
        if not _conditions_met(state, template.get("reveal_conditions")):
            continue
        instance = instantiate_story_quest(state, template)
        instance["type"] = QUEST_TYPE_HIDDEN
        instance["revealed_from_hidden"] = True
        state["quests"].append(instance)
        revealed.append(instance)
    return revealed


def spawn_quest_dungeon(state: dict[str, Any], quest: dict[str, Any], spawn_tpl: dict[str, Any]) -> dict[str, Any] | None:
    """Spawn a persistent dungeon tied to a quest, marking it for the UI."""
    template_id = spawn_tpl.get("template_id")
    if not template_id or template_id not in load_data().get("dungeon_by_id", {}):
        return None
    # Avoid spawning duplicates if the quest already linked a live dungeon.
    for d in state.get("active_dungeons", []):
        if d.get("source_quest_id") == quest["id"] and not d.get("cleared") and not d.get("expired"):
            quest.setdefault("linked_dungeon_ids", []).append(d["id"])
            return d
    instance = spawn_dungeon_instance(state, template_id)
    instance["source_quest_id"] = quest["id"]
    instance["source_quest_title"] = quest.get("title", "")
    instance["persistent"] = bool(spawn_tpl.get("persistent", True))
    instance["remaining_days"] = 99  # quest dungeons do not rot away
    if instance["id"] not in quest.setdefault("linked_dungeon_ids", []):
        quest["linked_dungeon_ids"].append(instance["id"])
    return instance


def accept_quest(state: dict[str, Any], quest_id: str) -> dict[str, Any]:
    """Move a quest from available -> active. All quests require manual acceptance."""
    quest = _get_quest(state, quest_id)
    if not quest:
        raise ValueError("任务不存在")
    if quest.get("status") != "available":
        raise ValueError(f"当前状态无法接受任务：{_quest_status_label(quest.get('status', ''))}")
    quest["status"] = "active"
    quest["accepted_day"] = state.get("day", 1)
    template = quest_template_by_id(quest.get("template_id", "")) or {}
    spawn_tpl = template.get("spawn_dungeon") if isinstance(template, dict) else None
    if spawn_tpl:
        spawn_quest_dungeon(state, quest, spawn_tpl)
    # Reveal the next batch of hidden quests that may have become eligible.
    check_hidden_reveals(state)
    return quest


def complete_manual_quest_objective(state: dict[str, Any], quest_id: str, objective_id: str) -> dict[str, Any]:
    """Mark a reusable manual acknowledgement objective as complete.

    This powers tutorial/read-only story steps without hard-coding a specific
    UI flow. Presets can use objective kind `manual_ack` for any quest that
    should complete after the player confirms they read a guide or dialogue.
    """
    quest = _get_quest(state, quest_id)
    if not quest:
        raise ValueError("任务不存在")
    if quest.get("status") != "active":
        raise ValueError("任务尚未进行，无法完成教学目标")
    obj = next((o for o in quest.get("objectives", []) if o.get("id") == objective_id), None)
    if not obj:
        raise ValueError("任务目标不存在")
    if obj.get("kind") != QUEST_OBJ_MANUAL_ACK:
        raise ValueError("此目标不能手动标记完成")
    obj["current"] = int(obj.get("required", 1))
    obj["completed"] = True
    _finalize_quest_status(state, quest)
    return quest


def abandon_quest(state: dict[str, Any], quest_id: str) -> dict[str, Any]:
    """Abandon an active quest. Daily quests can be dropped; story quests are merely reset to available."""
    quest = _get_quest(state, quest_id)
    if not quest:
        raise ValueError("任务不存在")
    if quest.get("status") not in {"active", "available"}:
        raise ValueError("当前状态无法放弃任务")
    if quest.get("type") == QUEST_TYPE_DAILY:
        quest["status"] = "expired"
    else:
        # Reset progress and put the story/hidden quest back in the pool.
        quest["status"] = "available"
        quest["accepted_day"] = None
        for obj in quest.get("objectives", []):
            obj["current"] = 0
            obj["completed"] = False
    return quest


def _objective_matches(obj: dict[str, Any], event: dict[str, Any]) -> bool:
    """Does this runtime objective consume the given progress event?"""
    kind = obj.get("kind")
    if event["event"] == "clear_dungeon":
        if kind == QUEST_OBJ_CLEAR_DUNGEON:
            return obj.get("dungeon_template_id") in (None, "", event.get("dungeon_template_id"))
        return False
    if event["event"] == "scout_dungeon":
        if kind == QUEST_OBJ_SCOUT_DUNGEON:
            return obj.get("dungeon_template_id") in (None, "", event.get("dungeon_template_id"))
        if kind == QUEST_OBJ_SCOUT_ANY:
            return True
        return False
    if event["event"] == "clear_unscouted_dungeon":
        if kind == QUEST_OBJ_CLEAR_UNSCOUTED:
            gte = int(obj.get("danger_level_gte", 0) or 0)
            return gte <= int(event.get("danger_level", 0))
        return False
    if event["event"] == "clear_two_dungeons_one_day":
        return kind == QUEST_OBJ_CLEAR_TWO_ONE_DAY
    return False


def _apply_event_to_objective(obj: dict[str, Any], event: dict[str, Any]) -> bool:
    if obj.get("completed"):
        return False
    if not _objective_matches(obj, event):
        return False
    if event["event"] in {"clear_two_dungeons_one_day"} and not event.get("eligible", False):
        return False
    amount = int(event.get("amount", 1))
    obj["current"] = min(int(obj.get("required", 1)), int(obj.get("current", 0)) + amount)
    if obj["current"] >= int(obj.get("required", 1)):
        obj["completed"] = True
    return True


def _finalize_quest_status(state: dict[str, Any], quest: dict[str, Any]) -> bool:
    """If all objectives done, mark completed. Returns True if it just completed."""
    if quest.get("status") != "active":
        return False
    objectives = quest.get("objectives", [])
    if not objectives:
        return False
    if all(o.get("completed") for o in objectives):
        quest["status"] = "completed"
        quest["completed_day"] = state.get("day", 1)
        stats = state.setdefault("quest_stats", default_quest_stats())
        tpl = quest.get("template_id", quest["id"])
        stats.setdefault("completed_quests", {})[tpl] = stats.get("completed_quests", {}).get(tpl, 0) + 1
        if quest.get("type") == QUEST_TYPE_HIDDEN:
            stats["hidden_completed"] = int(stats.get("hidden_completed", 0)) + 1
        # Auto-echo: hidden quests that complete themselves reveal on completion.
        if quest.get("auto_reveal_on_complete") and not quest.get("revealed_from_hidden"):
            quest["revealed_from_hidden"] = True
        return True
    return False


def _record_dungeon_stats(state: dict[str, Any], event: dict[str, Any]) -> None:
    stats = state.setdefault("quest_stats", default_quest_stats())
    template_id = event.get("dungeon_template_id")
    if not template_id:
        return
    if event["event"] == "clear_dungeon" or event["event"] == "clear_unscouted_dungeon":
        bucket = stats.setdefault("dungeon_cleared_by_template", {})
    elif event["event"] == "scout_dungeon":
        bucket = stats.setdefault("dungeon_scouted_by_template", {})
    else:
        return
    bucket[template_id] = bucket.get(template_id, 0) + 1


def record_quest_events(state: dict[str, Any], events: list[dict[str, Any]]) -> None:
    """Apply a batch of dungeon progress events to all active quests.

    Called from resolve_challenge/resolve_scout with one event per report.
    """
    if not events:
        return
    for event in events:
        _record_dungeon_stats(state, event)
    # Hidden quests with auto_reveal_on_complete may be revealed-and-completed
    # by an event (e.g. blind victory) even though they were never accepted.
    for event in events:
        _maybe_reveal_hidden_by_echo(state, event)
    newly_completed: list[dict[str, Any]] = []
    for quest in state.get("quests", []):
        if quest.get("status") != "active":
            continue
        changed = False
        for obj in quest.get("objectives", []):
            for event in events:
                if _apply_event_to_objective(obj, event):
                    changed = True
        if changed and _finalize_quest_status(state, quest):
            newly_completed.append(quest)
    return None


def _maybe_reveal_hidden_by_echo(state: dict[str, Any], event: dict[str, Any]) -> None:
    """For auto_reveal hidden quests not yet present, check if this event satisfies them."""
    for template in load_data().get("hidden_quests", []):
        if not isinstance(template, dict) or not template.get("id"):
            continue
        if not template.get("auto_reveal_on_complete"):
            continue
        if _quest_exists(state, template["id"]):
            continue
        # Build a temporary instance, apply the event, see if it completes.
        instance = instantiate_story_quest(state, template)
        instance["type"] = QUEST_TYPE_HIDDEN
        instance["status"] = "active"
        instance["revealed_from_hidden"] = True
        instance["accepted_day"] = state.get("day", 1)
        for obj in instance["objectives"]:
            _apply_event_to_objective(obj, event)
        if all(o.get("completed") for o in instance["objectives"]) and instance["objectives"]:
            instance["status"] = "completed"
            instance["completed_day"] = state.get("day", 1)
            stats = state.setdefault("quest_stats", default_quest_stats())
            tpl = instance["template_id"]
            stats.setdefault("completed_quests", {})[tpl] = stats.get("completed_quests", {}).get(tpl, 0) + 1
            stats["hidden_completed"] = int(stats.get("hidden_completed", 0)) + 1
            state["quests"].append(instance)


def claim_quest(state: dict[str, Any], quest_id: str) -> dict[str, Any]:
    """Grant rewards for a completed quest, then unlock its story successors."""
    quest = _get_quest(state, quest_id)
    if not quest:
        raise ValueError("任务不存在")
    if quest.get("status") != "completed":
        raise ValueError("任务尚未完成，无法领取")
    rewards = quest.get("rewards", {}) or {}
    state["gold"] = int(state.get("gold", 0)) + int(rewards.get("gold", 0))
    exp_reward = int(rewards.get("exp", 0))
    materials = rewards.get("materials", {}) or {}
    state_materials = state.setdefault("materials", {})
    for key, amount in materials.items():
        if amount:
            state_materials[key] = int(state_materials.get(key, 0)) + int(amount)
    if exp_reward:
        for ch in state.get("characters", []):
            gain_exp(ch, exp_reward)
    for flag, value in (rewards.get("flags", {}) or {}).items():
        state.setdefault("quest_flags", {})[flag] = value
    granted_equipment = grant_equipment_rewards(
        state,
        list(rewards.get("equipment", []) or []),
        rng=random.Random(stable_seed(state.get("run_seed", 0), "quest_equipment", quest_id)),
        level=int(state.get("day", 1)),
    )
    if granted_equipment:
        rewards["granted_equipment"] = granted_equipment
    quest["status"] = "claimed"
    quest["claimed_day"] = state.get("day", 1)
    stats = state.setdefault("quest_stats", default_quest_stats())
    tpl = quest.get("template_id", quest["id"])
    stats.setdefault("claimed_quests", {})[tpl] = stats.get("claimed_quests", {}).get(tpl, 0) + 1
    # Drop this quest's persistent dungeon now that it is resolved.
    if quest.get("linked_dungeon_ids"):
        linked = set(quest["linked_dungeon_ids"])
        state["active_dungeons"] = [
            d for d in state.get("active_dungeons", [])
            if d.get("id") not in linked or not (d.get("persistent") or d.get("source_quest_id"))
        ]
    _advance_quest_chain(state, quest)
    check_hidden_reveals(state)
    return quest


def _advance_quest_chain(state: dict[str, Any], quest: dict[str, Any]) -> None:
    """After claiming a quest, reveal its next_quests whose conditions now hold."""
    for next_id in quest.get("next_quests", []):
        template = quest_template_by_id(next_id)
        if not template:
            continue
        if _quest_exists(state, next_id):
            continue
        if not _conditions_met(state, template.get("start_conditions")):
            continue
        state["quests"].append(instantiate_story_quest(state, template))


def _quest_public_view(quest: dict[str, Any]) -> dict[str, Any]:
    """Frontend-facing projection of a single quest instance."""
    objectives = []
    for obj in quest.get("objectives", []):
        objectives.append({
            "id": obj.get("id"),
            "kind": obj.get("kind"),
            "label": obj.get("label", ""),
            "required": int(obj.get("required", 1)),
            "current": int(obj.get("current", 0)),
            "completed": bool(obj.get("completed", False)),
        })
    rewards = quest.get("rewards", {}) or {}
    equipment_rewards = [
        row for row in (_equipment_reward_public_view(spec, idx) for idx, spec in enumerate(rewards.get("equipment", []) or []))
        if row
    ]
    return {
        "id": quest.get("id"),
        "template_id": quest.get("template_id"),
        "type": quest.get("type", QUEST_TYPE_STORY),
        "story_kind": quest.get("story_kind", ""),
        "chain_id": quest.get("chain_id", ""),
        "title": quest.get("title", ""),
        "description": quest.get("description", ""),
        "status": quest.get("status", "available"),
        "status_label": _quest_status_label(quest.get("status", "available")),
        "created_day": quest.get("created_day"),
        "accepted_day": quest.get("accepted_day"),
        "expires_day": quest.get("expires_day"),
        "completed_day": quest.get("completed_day"),
        "claimed_day": quest.get("claimed_day"),
        "objectives": objectives,
        "all_completed": bool(objectives) and all(o["completed"] for o in objectives),
        "rewards": {
            "gold": int(rewards.get("gold", 0)),
            "exp": int(rewards.get("exp", 0)),
            "materials": rewards.get("materials", {}),
            "flags": rewards.get("flags", {}),
            "equipment": equipment_rewards,
        },
        "next_quests": list(quest.get("next_quests", [])),
        "guide_sections": copy.deepcopy(quest.get("guide_sections", [])),
        "guide_steps": copy.deepcopy(quest.get("guide_steps", [])),
        "dialogue": copy.deepcopy(quest.get("dialogue", [])),
        "revealed_from_hidden": bool(quest.get("revealed_from_hidden", False)),
        "linked_dungeon_ids": list(quest.get("linked_dungeon_ids", [])),
        "sort": int(quest.get("sort", 0)),
    }


def quest_list_view(state: dict[str, Any]) -> dict[str, Any]:
    """Group quests into buckets the UI can render directly.

    Unrevealed hidden quests are excluded entirely so the client never sees them.
    """
    normalize_quest_instances(state)
    buckets: dict[str, list[dict[str, Any]]] = {
        "available": [],
        "active": [],
        "completed": [],
        "claimed": [],
        "expired": [],
    }
    for quest in state.get("quests", []):
        if not isinstance(quest, dict):
            continue
        status = quest.get("status", "available")
        if status not in buckets:
            continue
        buckets[status].append(_quest_public_view(quest))
    for key in buckets:
        buckets[key].sort(key=lambda q: (q.get("sort", 0), q.get("id", "")))
    summary = {
        "available_count": len(buckets["available"]),
        "active_count": len(buckets["active"]),
        "claimable_count": len(buckets["completed"]),
        "daily_day": state.get("daily_quest_day"),
    }
    return {
        "available": buckets["available"],
        "active": buckets["active"],
        "completed": buckets["completed"],
        "claimed": buckets["claimed"],
        "expired": buckets["expired"],
        "summary": summary,
    }


def normalize_equipment_item(item: dict[str, Any]) -> dict[str, Any]:
    tpl = load_data().get("equipment_by_id", {}).get(item.get("template_id"), {})
    rarity = str(item.get("rarity") or tpl.get("rarity", "common"))
    kind = str(item.get("item_kind") or equipment_kind(tpl or item))
    item["slot"] = canonical_item_slot(tpl.get("slot", item.get("slot")))
    item.setdefault("base_name", tpl.get("name", item.get("name", "")))
    item["rarity"] = rarity
    item.setdefault("rarity_label", EQUIPMENT_RARITY_LABELS.get(rarity, rarity))
    item.setdefault("item_kind", kind)
    item.setdefault("item_kind_label", EQUIPMENT_KIND_LABELS.get(kind, kind))
    item.setdefault("item_level", int(tpl.get("tier", 1)) if tpl else 1)
    item.setdefault("affixes", [])
    item.setdefault("enchants", [])
    item.setdefault("enchant_reroll_count", 0)
    item.setdefault("stats", {})
    item.setdefault("resistances", {})
    item.setdefault("special_effects", [])
    item.setdefault("class_restriction", copy.deepcopy(tpl.get("class_restriction", [])))
    item.setdefault("max_durability", int(item.get("durability", tpl.get("durability", 30))))
    item.setdefault("durability", int(item.get("max_durability", tpl.get("durability", 30))))
    item.setdefault("equipped_by", None)
    return item


def equipment_drop_level(state: dict[str, Any], dungeon: dict[str, Any] | None = None) -> int:
    danger = int(dungeon.get("danger_level", 1)) if dungeon else None
    return equipment_level_from_danger(danger, int(state.get("day", 1)))


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
    skill = upgraded_skill_for_character(char, selected, data)
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
    for item_id in dict.fromkeys(x for x in char.get("equipment", {}).values() if x):
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


def clear_equipped_item(state: dict[str, Any], char: dict[str, Any], item_id: str | None) -> None:
    if not item_id:
        return
    for s, equipped_id in list(char.get("equipment", {}).items()):
        if equipped_id == item_id:
            char["equipment"][s] = None
    if item := get_item(state, item_id):
        item["equipped_by"] = None


def unequip_slot(state: dict[str, Any], char: dict[str, Any], slot: str) -> None:
    old_id = char.get("equipment", {}).get(slot)
    clear_equipped_item(state, char, old_id)


def pick_equipment_slot(char: dict[str, Any], item: dict[str, Any], requested_slot: str | None = None) -> str:
    item_slot = canonical_item_slot(item.get("slot"))
    compatible = compatible_equipment_slots(item_slot)
    if not compatible:
        raise ValueError("装备槽位不支持")
    if requested_slot:
        slot = canonical_item_slot(requested_slot)
        if slot not in compatible:
            raise ValueError("装备槽位不匹配")
        return slot
    for slot in compatible:
        if not char.get("equipment", {}).get(slot):
            return slot
    return compatible[0]


def equip_item(state: dict[str, Any], char_id: str, item_id: str | None, slot: str | None = None, validate_class: bool = True) -> None:
    char = get_character(state, char_id)
    if not char:
        raise ValueError("角色不存在")
    normalize_character(char)
    if item_id is None:
        if not slot:
            raise ValueError("卸下装备需要提供 slot")
        unequip_slot(state, char, canonical_item_slot(slot))
        return
    item = get_item(state, item_id)
    if not item:
        raise ValueError("装备不存在")
    normalize_equipment_item(item)
    target_slot = pick_equipment_slot(char, item, slot)
    occupy_slots = equipment_item_occupies_slots(item, target_slot)
    if validate_class:
        restriction = item.get("class_restriction") or []
        if not class_matches_restriction(char.get("class_id"), restriction):
            raise ValueError(f"{char['class_name']} 不能装备 {item['name']}")
    if item.get("equipped_by") and item["equipped_by"] != char_id:
        other = get_character(state, item["equipped_by"])
        if other:
            normalize_character(other)
            clear_equipped_item(state, other, item_id)
    clear_equipped_item(state, char, item_id)
    for occupy_slot in occupy_slots:
        unequip_slot(state, char, occupy_slot)
    for occupy_slot in occupy_slots:
        char["equipment"][occupy_slot] = item_id
    item["equipped_by"] = char_id


def normalize_character_equipment_occupancy(state: dict[str, Any], char: dict[str, Any]) -> None:
    normalize_character(char)
    current = copy.deepcopy(char.get("equipment", {}))
    new_equipment = default_character_equipment()
    item_ids = list(dict.fromkeys(item_id for item_id in current.values() if item_id))
    for item_id in item_ids:
        item = get_item(state, item_id)
        if not item:
            continue
        normalize_equipment_item(item)
        compatible = compatible_equipment_slots(item.get("slot"))
        preferred = next((slot for slot, equipped_id in current.items() if equipped_id == item_id and slot in compatible), None)
        target = preferred or (compatible[0] if compatible else None)
        occupy_slots = equipment_item_occupies_slots(item, target)
        if not occupy_slots:
            continue
        for occupy_slot in occupy_slots:
            old_id = new_equipment.get(occupy_slot)
            if old_id and old_id != item_id and (old := get_item(state, old_id)):
                old["equipped_by"] = None
                for s, equipped_id in list(new_equipment.items()):
                    if equipped_id == old_id:
                        new_equipment[s] = None
        for occupy_slot in occupy_slots:
            new_equipment[occupy_slot] = item_id
        item["equipped_by"] = char["id"]
    char["equipment"] = new_equipment


def refresh_shop(state: dict[str, Any]) -> None:
    """Regenerate every merchant's stock for the current day.

    Each merchant owns an independent, deterministic RNG stream seeded from
    (run_seed, "shop", merchant_id, day) so a given day's shop is reproducible
    for testing and reload. Shop config (merchants, pricing floors, sell/salvage
    tables) comes from the preset's shop.json via load_data()["shop_config"].
    """
    data = load_data()
    shop_config = data.get("shop_config", {})
    level = equipment_level_from_danger(day=state["day"])
    equipment_pool = equipment_templates_for_level(level)
    rarity_floor = shop_config.get("rarity_price_floor", {})
    merchants: dict[str, Any] = {}
    for merchant in shop_config.get("merchants", []):
        mid = merchant.get("id") or make_id("merchant")
        rng = random.Random(stable_seed(state["run_seed"], "shop", mid, state["day"]))
        slot_count = max(0, int(merchant.get("slot_count", 3)))
        currency = merchant.get("currency", "gold")
        jitter_lo, jitter_hi = merchant.get("cost_jitter", [0.9, 1.15])
        sells = merchant.get("sells", [])
        items: list[dict[str, Any]] = []
        if "equipment" in sells:
            slot_groups = (merchant.get("equipment_filter") or {}).get("slot_groups") or []
            pool = [
                tpl for tpl in equipment_pool
                if not slot_groups or any(equipment_slot_matches_token(tpl.get("slot"), g) for g in slot_groups)
            ]
            for _ in range(min(slot_count, len(pool))):
                tpl = weighted_choice(
                    rng,
                    pool,
                    lambda e: max(1, 12 - abs(int(e.get("tier", 1)) - level) * 2) * (0.45 if equipment_kind(e) == "special" else 1.0),
                )
                eq = instance_equipment(tpl["id"], rng=rng, level=level)
                base_cost = int(eq.get("cost", 50))
                # Jitter the price, then enforce a rarity-based floor so high-rarity
                # stock can never be sold below base_cost * floor_multiplier.
                floor = rarity_floor.get(eq.get("rarity"), 1.0)
                jittered = base_cost * (jitter_lo + rng.random() * (jitter_hi - jitter_lo))
                floored = max(jittered, base_cost * floor)
                final_cost = max(1, int(round(floored)))
                eq["cost"] = final_cost
                items.append({
                    "shop_id": make_id("shop"),
                    "merchant_id": mid,
                    "kind": "equipment",
                    "template_id": eq["template_id"],
                    "name": eq["name"],
                    "slot": eq["slot"],
                    "rarity": eq["rarity"],
                    "base_cost": base_cost,
                    "cost": final_cost,
                    "currency": currency,
                    "summary": format_equipment_summary(eq),
                    "equipment": copy.deepcopy(eq),
                })
        if "consumable" in sells:
            for consumable in merchant.get("consumables", [])[:slot_count]:
                if not isinstance(consumable, dict) or not consumable.get("id"):
                    continue
                base = int(consumable.get("cost", 20))
                final_cost = max(1, int(round(base * (jitter_lo + rng.random() * (jitter_hi - jitter_lo)))))
                items.append({
                    "shop_id": make_id("shop"),
                    "merchant_id": mid,
                    "kind": "consumable",
                    "template_id": consumable["id"],
                    "name": consumable.get("name", consumable["id"]),
                    "cost": final_cost,
                    "base_cost": base,
                    "currency": currency,
                    "summary": consumable.get("summary", ""),
                })
        merchants[mid] = {
            "merchant_id": mid,
            "name": merchant.get("name", mid),
            "icon": merchant.get("icon", "🪙"),
            "items": items,
        }
    state["shop"] = {"merchants": merchants, "refresh_day": state["day"]}


def refresh_recruits(state: dict[str, Any]) -> None:
    """Regenerate the tavern candidate pool for the current day.

    Candidates carry a full character snapshot in `preview` generated with the
    real create_character/level_up_character pipeline, so what the player sees
    before hiring is exactly what joins the roster. Rarity scales both cost and
    attributes for flavor. Config from load_data()["recruit_config"].
    """
    data = load_data()
    rcfg = data.get("recruit_config", {})
    preset = data.get("preset", {})
    recruit_pool = rcfg.get("recruit_pool") or preset.get("recruit_pool") or [c["id"] for c in data["classes"]]
    # Split base vs advanced classes so advanced ones only roll by chance.
    base_pool = [cid for cid in recruit_pool if not _class_is_advanced(cid, data)]
    advanced_pool = [cid for cid in recruit_pool if _class_is_advanced(cid, data)]
    if not base_pool:
        base_pool = recruit_pool
    weights = rcfg.get("rarity_weights", {"common": 50, "uncommon": 30, "rare": 15, "epic": 4, "legendary": 1})
    rarity_keys = [k for k in EQUIPMENT_RARITIES if k in weights and k != "artifact"]
    rarity_weights_list = [max(0, int(weights[k])) for k in rarity_keys]
    modifiers = rcfg.get("rarity_modifiers", {})
    name_pools = rcfg.get("name_pools", {}) or {}
    fallback_names = preset.get("recruit_names") or ["伊芙", "莱恩", "卡洛", "薇拉", "塔克", "米娜", "洛特", "珂赛"]
    advanced_chance = clamp(float(rcfg.get("advanced_chance", 0.0)), 0.0, 1.0)
    count = max(0, int(rcfg.get("candidate_count", 3)))
    base_cost = int(rcfg.get("base_cost", 90))
    cost_per_level = int(rcfg.get("cost_per_level", 12))

    rng = random.Random(stable_seed(state["run_seed"], "recruits", state["day"]))
    candidates: list[dict[str, Any]] = []
    for _ in range(count):
        use_advanced = bool(advanced_pool) and rng.random() < advanced_chance
        pool = advanced_pool if use_advanced else base_pool
        cid = rng.choice(pool) if pool else rng.choice(recruit_pool or ["warrior"])
        c = data["class_by_id"].get(cid)
        if not c:
            continue
        rarity = rng.choices(rarity_keys, weights=rarity_weights_list, k=1)[0] if rarity_keys else "common"
        mod = modifiers.get(rarity, {})
        attr_mult = float(mod.get("attr_mult", 1.0))
        cost_mult = float(mod.get("cost_mult", 1.0))
        level = max(1, state["day"] // 8 + rng.randint(0, 1))
        # Build the candidate's name from per-class pool, else advanced pool, else fallback.
        name_pool = name_pools.get(cid) or (name_pools.get("_advanced") if use_advanced else None) or name_pools.get("_default") or fallback_names
        name = rng.choice(name_pool)
        ch = create_character(cid, name, make_id("rec"))
        while ch["level"] < level:
            level_up_character(ch)
        # Apply rarity attribute scaling on top of the grown character.
        if attr_mult != 1.0:
            for k in ch["attributes"]:
                ch["attributes"][k] = max(1, int(round(ch["attributes"][k] * attr_mult)))
            # Recompute hp/mana derived from the scaled attributes.
            derived = attribute_derived_stats(ch["attributes"])
            ch["max_hp"] = int(ch["base_stats"].get("max_hp", 1)) + derived["hp_bonus"]
            ch["hp"] = ch["max_hp"]
            ch["max_mana"] = int(derived.get("mana", 0))
            ch["mana"] = ch["max_mana"]
        cost = max(1, int(round((base_cost + cost_per_level * (level - 1)) * cost_mult)))
        candidates.append({
            "candidate_id": ch["id"],
            "class_id": cid,
            "class_name": c["name"],
            "class_meta": class_preset_meta(cid),
            "name": name,
            "level": level,
            "rarity": rarity,
            "rarity_label": EQUIPMENT_RARITY_LABELS.get(rarity, rarity),
            "cost": cost,
            "role": c.get("role", ""),
            "is_advanced": bool(c.get("is_advanced")),
            "preview": copy.deepcopy(ch),
        })
    state["recruits"] = {"candidates": candidates, "refresh_day": state["day"]}


def _class_is_advanced(class_id: str, data: dict[str, Any]) -> bool:
    row = data.get("class_by_id", {}).get(class_id)
    return bool(row and row.get("is_advanced"))


def format_equipment_summary(e: dict[str, Any]) -> str:
    parts = []
    for k, v in e.get("stats", {}).items():
        parts.append(f"{STAT_NAMES.get(k, k)} {v:+}")
    for k, v in e.get("resistances", {}).items():
        parts.append(f"{DAMAGE_TYPE_NAMES.get(k, k)}抗 {v:+}")
    for effect in e.get("special_effects", []):
        parts.append(SPECIAL_EFFECT_NAMES.get(effect, effect.replace("_", " ")))
    for affix in e.get("affixes", []):
        if affix.get("name"):
            parts.append(f"词缀：{affix['name']}")
        if affix.get("durability_bonus"):
            parts.append(f"耐久 {int(affix['durability_bonus']):+}")
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
            if d.get("is_final") or d.get("cleared") or d.get("persistent") or d.get("source_quest_id"):
                continue
            d["remaining_days"] -= 1
            if d["remaining_days"] <= 0:
                d["expired"] = True
        # Drop expired normal dungeons and fully-drained normal dungeons.
        # Persistent quest dungeons are kept until their quest is claimed,
        # even if cleared, so the player can re-target or re-read the link.
        def _keep_dungeon(d: dict[str, Any]) -> bool:
            if d.get("expired"):
                return False
            if d.get("persistent") or d.get("source_quest_id"):
                return True
            if d.get("cleared") and d.get("reward_charges", 0) <= 0:
                return False
            return True
        state["active_dungeons"] = [d for d in state["active_dungeons"] if _keep_dungeon(d)]
    if state["day"] >= 25 and not state.get("final_unlocked"):
        spawn_dungeon_instance(state, "final_bastion", fixed_final=True)
        state["final_unlocked"] = True
    desired = 3 if state["day"] < 5 else 4
    if state["day"] >= 15:
        desired = 5
    rng = random.Random(stable_seed(state["run_seed"], "world", state["day"], len(state["active_dungeons"])))
    pool = available_template_ids_for_day(state["day"])
    # Only count naturally-spawned dungeons toward the daily desired total;
    # quest-spawned persistent dungeons are additive on top.
    natural = [d for d in state["active_dungeons"] if not d.get("is_final") and not (d.get("persistent") or d.get("source_quest_id"))]
    while len(natural) < desired:
        template_id = rng.choice(pool)
        spawn_dungeon_instance(state, template_id, rng=rng)
        natural = [d for d in state["active_dungeons"] if not d.get("is_final") and not (d.get("persistent") or d.get("source_quest_id"))]
    refresh_shop(state)
    refresh_recruits(state)
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


def remove_plan_action(state: dict[str, Any], index: int) -> dict[str, Any] | None:
    """Remove a single action from today's expedition plan by its position.

    Returns the removed action (or None if the index was out of range). The plan
    is a positional queue, so removing re-indexes the remaining actions — this
    frees up both the expedition slot and the team that action had reserved.
    """
    plan = state.get("expedition_plan", [])
    if not isinstance(plan, list) or index < 0 or index >= len(plan):
        return None
    return plan.pop(index)


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
        "consumable_priority": copy.deepcopy(tactics.get("consumable_priority", [])),
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
    result.setdefault("consumable_priority", copy.deepcopy(defaults["consumable_priority"]))

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
    if "consumable_priority" in row:
        result["consumable_priority"] = clean_consumable_priority(row.get("consumable_priority") or [])
    return {
        "target_priority": result.get("target_priority", defaults["target_priority"]),
        "initiative_skill": result.get("initiative_skill", ""),
        "skill_priority": copy.deepcopy(result.get("skill_priority", [])),
        "opening_skill_priority": copy.deepcopy(result.get("opening_skill_priority", [])),
        "defense_skill_by_type": copy.deepcopy(result.get("defense_skill_by_type", {})),
        "consumable_priority": copy.deepcopy(result.get("consumable_priority", [])),
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
            unit["_layer_tactic_applied"] = True
        else:
            unit["_layer_tactic_applied"] = False
        unit["_layer_index"] = int(layer_key)
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
        "consumables": sum(list_len(row.get("consumable_priority")) for row in rows + layer_rows if isinstance(row, dict)),
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


def upgrade_skill(state: dict[str, Any], character_id: str, skill_id: str, choice_id: str | None = None) -> dict[str, Any]:
    ch = get_character(state, character_id)
    if not ch:
        raise ValueError("角色不存在")
    normalize_character(ch)
    sid = str(skill_id or "")
    data = load_data()
    skill = data["skill_by_id"].get(sid)
    if not skill or sid not in ch.get("skills", []):
        raise ValueError("该技能不在本职业技能树中")
    if sid not in ch.get("learned_skills", []):
        raise ValueError("需要先学习该技能")
    status = skill_upgrade_status(state, ch, sid)
    if not status.get("upgradeable"):
        raise ValueError(str(status.get("reason", "暂时无法升级")))
    row = skill_upgrade_row(ch, sid)
    current = int(row.get("level", 1))
    next_level = current + 1
    choices = skill_upgrade_choices_for_level(skill, next_level)
    chosen = str(choice_id or "")
    if choices:
        allowed = {str(c.get("id")) for c in choices}
        if chosen not in allowed:
            names = "、".join(str(c.get("name", c.get("id"))) for c in choices)
            raise ValueError(f"该等级需要选择一个额外效果：{names}")
    cost = int(status.get("cost", skill_upgrade_cost(skill, current)))
    state.setdefault("materials", {})
    essence = int(state["materials"].get(SKILL_ESSENCE_KEY, 0))
    if essence < cost:
        raise ValueError(f"技能精华不足：需要 {cost}，当前 {essence}")
    state["materials"][SKILL_ESSENCE_KEY] = max(0, essence - cost)
    upgrades = ch.setdefault("skill_upgrades", {})
    if not isinstance(upgrades, dict):
        upgrades = {}
        ch["skill_upgrades"] = upgrades
    row["level"] = next_level
    if choices:
        row.setdefault("choices", {})[str(next_level)] = chosen
    upgrades[sid] = row
    normalize_character(ch)
    return ch


def promote_character(state: dict[str, Any], character_id: str, target_class_id: str) -> dict[str, Any]:
    ch = get_character(state, character_id)
    if not ch:
        raise ValueError("角色不存在")
    normalize_character(ch)
    data = load_data()
    current_id = str(ch.get("class_id") or "")
    current_row = data.get("class_by_id", {}).get(current_id, {})
    if not current_row:
        raise ValueError("当前职业不存在")
    if current_row.get("base_class_id"):
        raise ValueError("该角色已经完成转职")
    target_id = str(target_class_id or "")
    target_row = data.get("class_by_id", {}).get(target_id)
    if not target_row or not target_row.get("is_advanced"):
        raise ValueError("目标进阶职业不存在")
    if str(target_row.get("base_class_id") or "") != current_id:
        raise ValueError("该进阶职业不属于当前基础职业")

    option = next((o for o in promotion_options_for_character(state, ch) if o["class_id"] == target_id), None)
    if not option:
        raise ValueError("无法转职为该职业")
    if not option.get("can_promote"):
        raise ValueError(str(option.get("reason", "暂时无法转职")))

    materials = state.setdefault("materials", {})
    costs = option.get("cost", {})
    for key, amount in costs.items():
        materials[key] = max(0, int(materials.get(key, 0)) - int(amount))

    base_id = current_id
    ch["base_class_id"] = base_id
    ch["class_path"] = [base_id, target_id]
    ch["class_id"] = target_id
    ch["class_name"] = target_row.get("name", target_id)
    ch["role"] = target_row.get("role", ch.get("role", ""))
    ch["promotion_level"] = int(ch.get("level", 1))
    ch["promoted_at_level"] = int(ch.get("level", 1))
    ch["promotion_choice"] = target_id
    ch["skills"] = class_skill_ids(target_row)
    ch["learned_skills"] = clean_learned_skill_ids(target_id, ch.get("learned_skills", []))
    normalize_character(ch)
    return ch


def _reapply_attribute_limits(ch: dict[str, Any], derived: dict[str, int]) -> None:
    """Refresh derived pools (max_hp/max_mana) after attribute changes and clamp current values."""
    ch["max_hp"] = int(ch.get("base_stats", {}).get("max_hp", ch.get("max_hp", 1))) + int(derived.get("hp_bonus", 0))
    ch["max_mana"] = int(derived.get("mana", 0))
    ch["hp"] = min(ch["max_hp"], int(ch.get("hp", ch["max_hp"])))
    ch["mana"] = max(0, min(ch["max_mana"], int(ch.get("mana", ch["max_mana"]))))


def allocate_attributes(state: dict[str, Any], character_id: str, allocations: dict[str, Any] | None) -> dict[str, Any]:
    """Spend free attribute points on the WOD eight attributes.

    `allocations` maps attribute keys to the number of points to add (>= 0). The
    total must not exceed the character's available points. Derived pools (max_hp
    / max_mana) are recomputed and current hp/mana clamped into range.
    """
    ch = get_character(state, character_id)
    if not ch:
        raise ValueError("角色不存在")
    normalize_character(ch)
    data = load_data()
    class_row = data.get("class_by_id", {}).get(ch.get("class_id"), {})
    available = attribute_points_available(ch, class_row)
    if not isinstance(allocations, dict) or not allocations:
        raise ValueError("未指定要分配的属性点")
    deltas: dict[str, int] = {}
    total = 0
    for key, value in allocations.items():
        if key not in ATTRIBUTE_KEYS:
            raise ValueError(f"未知属性：{key}")
        try:
            amount = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"属性点数量无效：{value}")
        if amount < 0:
            raise ValueError("属性点数量不能为负")
        deltas[key] = amount
        total += amount
    if total <= 0:
        raise ValueError("未指定要分配的属性点")
    if total > available:
        raise ValueError(f"属性点不足：需要 {total}，可用 {available}")
    current = ch.get("attributes", {})
    for key, amount in deltas.items():
        new_value = int(current.get(key, 0)) + amount
        if new_value > MAX_ATTRIBUTE_VALUE:
            raise ValueError(f"{ATTRIBUTE_NAMES.get(key, key)}将超过上限 {MAX_ATTRIBUTE_VALUE}")
        current[key] = new_value
    ch["attributes"] = current
    normalize_character(ch)
    derived = attribute_derived_stats(ch["attributes"])
    _reapply_attribute_limits(ch, derived)
    return ch


def reset_attributes(state: dict[str, Any], character_id: str) -> dict[str, Any]:
    """Return all eight attributes to the class baseline (clears invested points)."""
    ch = get_character(state, character_id)
    if not ch:
        raise ValueError("角色不存在")
    normalize_character(ch)
    data = load_data()
    class_row = data.get("class_by_id", {}).get(ch.get("class_id"), {})
    baseline = attribute_block_for_class(class_row, int(ch.get("level", 1)))
    ch["attributes"] = baseline
    normalize_character(ch)
    derived = attribute_derived_stats(ch["attributes"])
    _reapply_attribute_limits(ch, derived)
    return ch


def _find_shop_item(state: dict[str, Any], shop_id: str) -> tuple[dict[str, Any], str] | None:
    """Locate a shop item across all merchants. Returns (item, merchant_id)."""
    for mid, merchant in state.get("shop", {}).get("merchants", {}).items():
        for item in merchant.get("items", []):
            if item.get("shop_id") == shop_id:
                return item, mid
    return None


def _spend_currency(state: dict[str, Any], currency: str, amount: int) -> None:
    """Deduct a purchase price in either gold or a named material currency."""
    if currency == "gold":
        if state["gold"] < amount:
            raise ValueError("金币不足")
        state["gold"] -= amount
    else:
        have = int(state.get("materials", {}).get(currency, 0))
        if have < amount:
            raise ValueError(f"{MATERIAL_NAMES.get(currency, currency)}不足")
        state.setdefault("materials", {})[currency] = have - amount


def buy_shop_item(state: dict[str, Any], shop_id: str) -> dict[str, Any]:
    found = _find_shop_item(state, shop_id)
    if not found:
        raise ValueError("商品不存在")
    item, mid = found
    _spend_currency(state, item.get("currency", "gold"), int(item["cost"]))
    if item["kind"] == "equipment":
        eq = copy.deepcopy(item.get("equipment")) if isinstance(item.get("equipment"), dict) else instance_equipment(item["template_id"])
        eq["instance_id"] = eq.get("instance_id") or make_id("eq")
        eq["equipped_by"] = None
        normalize_equipment_item(eq)
        state["inventory"].append(eq)
        acquired = {"type": "equipment", "item": eq}
    else:
        state["consumables"][item["template_id"]] = state["consumables"].get(item["template_id"], 0) + 1
        acquired = {"type": "consumable", "id": item["template_id"], "name": item["name"]}
    state["shop"]["merchants"][mid]["items"] = [i for i in state["shop"]["merchants"][mid]["items"] if i["shop_id"] != shop_id]
    return acquired


def _estimate_sell_value(state_item: dict[str, Any], shop_config: dict[str, Any]) -> int:
    rarity = state_item.get("rarity", "common")
    multiplier = float(shop_config.get("sell_multipliers", {}).get(rarity, 0.4))
    return max(1, int(round(int(state_item.get("cost", 0)) * multiplier)))


def sell_item(state: dict[str, Any], item_id: str) -> dict[str, Any]:
    """Sell an inventory equipment piece back for gold based on rarity."""
    shop_config = load_data().get("shop_config", {})
    item = get_item(state, item_id)
    if not item:
        raise ValueError("物品不存在")
    if item.get("equipped_by"):
        raise ValueError("请先卸下装备再出售")
    value = _estimate_sell_value(item, shop_config)
    state["gold"] += value
    state["inventory"] = [i for i in state["inventory"] if i.get("instance_id") != item_id]
    return {"type": "sell", "item_id": item_id, "gold": value, "name": item.get("name", "")}


def _salvage_material_yield(class_id: str | None, salvage_cfg: dict[str, Any], rng: random.Random) -> dict[str, int]:
    """Roll salvage material drops for a character class affinity. Returns {material: amount}."""
    yield_map: dict[str, int] = {}
    for key, drops in salvage_cfg.items():
        if class_id and class_id in key.split("|") and isinstance(drops, dict):
            for mat, bounds in drops.items():
                if isinstance(bounds, list) and len(bounds) == 2:
                    low, high = int(bounds[0]), int(bounds[1])
                    if high > low:
                        amount = rng.randint(low, high)
                    else:
                        amount = low
                    if amount > 0:
                        yield_map[mat] = yield_map.get(mat, 0) + amount
    return yield_map


def salvage_item(state: dict[str, Any], item_id: str) -> dict[str, Any]:
    """Break down an inventory equipment piece into gold + class-affinity materials."""
    shop_config = load_data().get("shop_config", {})
    salvage_cfg = shop_config.get("salvage", {})
    item = get_item(state, item_id)
    if not item:
        raise ValueError("物品不存在")
    if item.get("equipped_by"):
        raise ValueError("请先卸下装备再分解")
    rarity = item.get("rarity", "common")
    gold = int(salvage_cfg.get("gold", {}).get(rarity, 5))
    rng = random.Random(stable_seed(state["run_seed"], "salvage", item_id, state["day"]))
    # Class affinity comes from the item's class_restriction, if any.
    affinity = item.get("class_restriction") or []
    affinity_id = affinity[0] if affinity else None
    materials = _salvage_material_yield(affinity_id, salvage_cfg.get("materials", {}), rng)
    state["gold"] += gold
    for mat, amount in materials.items():
        state.setdefault("materials", {})[mat] = state.setdefault("materials", {}).get(mat, 0) + amount
    state["inventory"] = [i for i in state["inventory"] if i.get("instance_id") != item_id]
    return {"type": "salvage", "item_id": item_id, "gold": gold, "materials": materials, "name": item.get("name", "")}


# --- Equipment enchantment / reroll / ascension ----------------------------
def _format_enchanted_name(item: dict[str, Any]) -> str:
    """Rebuild an item's display name from its base name + affixes + enchants."""
    base = item.get("base_name") or item.get("name", "")
    affix_like = list(item.get("affixes", [])) + list(item.get("enchants", []))
    return format_equipment_name(base, affix_like)


def _strip_enchant_from_item(item: dict[str, Any], enchant: dict[str, Any]) -> None:
    """Reverse the stat/resistance/effect contribution of one enchant line,
    removing it cleanly so reroll doesn't leave phantom bonuses behind."""
    subtract_number_maps(item["stats"], enchant.get("stats", {}))
    subtract_number_maps(item["resistances"], enchant.get("resistances", {}))
    # Special effects may be shared by the template, an affix, or another enchant;
    # only drop an effect if no remaining source still provides it.
    remaining_sources = list(item.get("special_effects", []))  # current instance pool
    for source in (item.get("affixes", []) + list(item.get("enchants", []))):
        if isinstance(source, dict):
            remaining_sources += source.get("special_effects", [])
    # `remaining_sources` currently still includes the enchant we're removing (it is
    # still in item["enchants"]); exclude its effects from the "still provided" set.
    removing_effects = set(enchant.get("special_effects", []))
    provided: dict[str, int] = {}
    for eff in remaining_sources:
        if eff in removing_effects:
            continue
        provided[eff] = provided.get(eff, 0) + 1
    # Also count the template's own special_effects (base gear effects).
    tpl = load_data().get("equipment_by_id", {}).get(item.get("template_id"), {})
    for eff in tpl.get("special_effects", []):
        provided[eff] = provided.get(eff, 0) + 1
    item["special_effects"] = [e for e in item.get("special_effects", []) if provided.get(e, 0) > 0]


def _enchant_affix_candidates(item: dict[str, Any], exclude_ids: set[str] | None = None) -> list[dict[str, Any]]:
    """Affixes from the equipment pool compatible with this item at its rarity.
    Re-derives affix_tags from the template because instances do not carry them.
    `exclude_ids` optionally blocks specific affix ids (e.g. the one being rerolled)."""
    tpl = load_data().get("equipment_by_id", {}).get(item.get("template_id"), {})
    compat_tpl = {
        "slot": item.get("slot", tpl.get("slot")),
        "affix_tags": tpl.get("affix_tags", []),
        "exclude_affixes": tpl.get("exclude_affixes", []),
    }
    rarity = item.get("rarity", "common")
    owned_ids = {a.get("id") for a in (list(item.get("affixes", [])) + list(item.get("enchants", []))) if isinstance(a, dict)}
    if exclude_ids:
        owned_ids |= exclude_ids
    return [
        a for a in equipment_affix_pool()
        if affix_matches_template(a, compat_tpl, rarity) and a.get("id") not in owned_ids
    ]


def enchant_equipment(state: dict[str, Any], item_id: str) -> dict[str, Any]:
    """Spend reagents to add one random compatible affix line to an item. Special
    (fixed-rarity) items cannot be enchanted. Up to MAX_ENCHANT_SLOTS lines."""
    item = get_item(state, item_id)
    if not item:
        raise ValueError("装备不存在")
    normalize_equipment_item(item)
    if str(item.get("item_kind")) == "special":
        raise ValueError("特殊装备无法附魔")
    enchants = item.setdefault("enchants", [])
    if len(enchants) >= MAX_ENCHANT_SLOTS:
        raise ValueError("附魔词条已满")
    candidates = _enchant_affix_candidates(item)
    if not candidates:
        raise ValueError("没有可附加的词缀")
    for key, amount in ENCHANT_COST.items():
        _spend_currency(state, key, int(amount))
    rng = random.Random(stable_seed(state["run_seed"], "enchant", item_id, state["day"], str(len(enchants))))
    weights = [max(1, int(a.get("weight", 1))) for a in candidates]
    chosen = copy.deepcopy(rng.choices(candidates, weights=weights, k=1)[0])
    add_number_maps(item["stats"], chosen.get("stats", {}))
    add_number_maps(item["resistances"], chosen.get("resistances", {}))
    for effect in chosen.get("special_effects", []):
        if effect and effect not in item.setdefault("special_effects", []):
            item["special_effects"].append(effect)
    enchants.append(affix_public_view(chosen))
    item["name"] = _format_enchanted_name(item)
    return {"type": "enchant", "item": copy.deepcopy(item), "affix": affix_public_view(chosen)}


def reroll_enchant(state: dict[str, Any], item_id: str, enchant_index: int) -> dict[str, Any]:
    """Re-roll an existing enchant line into a different one. Costs the same as a
    fresh enchant. The old line's stats are stripped first, then a new compatible
    affix (never the same id) is drawn and summed back in."""
    item = get_item(state, item_id)
    if not item:
        raise ValueError("装备不存在")
    normalize_equipment_item(item)
    if str(item.get("item_kind")) == "special":
        raise ValueError("特殊装备无法附魔")
    enchants = item.setdefault("enchants", [])
    idx = int(enchant_index)
    if idx < 0 or idx >= len(enchants):
        raise ValueError("要重掷的词条不存在")
    old = enchants[idx]
    candidates = _enchant_affix_candidates(item, exclude_ids={old.get("id")})
    if not candidates:
        raise ValueError("没有可替换的词缀")
    for key, amount in ENCHANT_COST.items():
        _spend_currency(state, key, int(amount))
    # Strip the old line's contribution, then drop it from the ledger.
    _strip_enchant_from_item(item, old)
    enchants.pop(idx)
    # Seed varies with the reroll counter so in-place rerolls don't repeat.
    reroll_count = int(item.get("enchant_reroll_count", 0)) + 1
    item["enchant_reroll_count"] = reroll_count
    rng = random.Random(stable_seed(state["run_seed"], "reroll", item_id, state["day"], str(reroll_count)))
    weights = [max(1, int(a.get("weight", 1))) for a in candidates]
    chosen = copy.deepcopy(rng.choices(candidates, weights=weights, k=1)[0])
    add_number_maps(item["stats"], chosen.get("stats", {}))
    add_number_maps(item["resistances"], chosen.get("resistances", {}))
    for effect in chosen.get("special_effects", []):
        if effect and effect not in item.setdefault("special_effects", []):
            item["special_effects"].append(effect)
    enchants.insert(idx, affix_public_view(chosen))
    item["name"] = _format_enchanted_name(item)
    return {"type": "reroll", "item": copy.deepcopy(item), "affix": affix_public_view(chosen)}


def ascension_recipes() -> list[dict[str, Any]]:
    """Loaded from preset.json `ascension_recipes`. Each: {source, target, materials}."""
    rows = load_data().get("preset", {}).get("ascension_recipes")
    if not isinstance(rows, list):
        return []
    return [copy.deepcopy(r) for r in rows if isinstance(r, dict) and r.get("source") and r.get("target")]


def ascension_recipe_for(item: dict[str, Any]) -> dict[str, Any] | None:
    """The ascension recipe applicable to this item's template, or None."""
    tid = str(item.get("template_id") or "")
    return next((r for r in ascension_recipes() if str(r.get("source")) == tid), None)


def ascend_equipment(state: dict[str, Any], item_id: str) -> dict[str, Any]:
    """Transform a special item into its ascension target, consuming the recipe's
    materials. The source must be unequipped. The new instance keeps the same
    instance_id so any external references stay valid."""
    item = get_item(state, item_id)
    if not item:
        raise ValueError("装备不存在")
    normalize_equipment_item(item)
    if str(item.get("item_kind")) != "special":
        raise ValueError("此装备无法升华")
    recipe = ascension_recipe_for(item)
    if not recipe:
        raise ValueError("此装备没有升华配方")
    if item.get("equipped_by"):
        raise ValueError("请先卸下装备再升华")
    target_id = str(recipe.get("target"))
    materials = recipe.get("materials", {}) if isinstance(recipe.get("materials"), dict) else {}
    for key, amount in materials.items():
        _spend_currency(state, str(key), int(amount))  # raises localized ValueError if short
    source_name = item.get("name", "")
    source_id = item["instance_id"]
    owner = item.get("equipped_by")
    new_item = instance_equipment(target_id, instance_id=source_id)
    new_item["equipped_by"] = owner
    normalize_equipment_item(new_item)
    state["inventory"] = [i for i in state["inventory"] if i.get("instance_id") != source_id]
    state["inventory"].append(new_item)
    return {"type": "ascend", "item": copy.deepcopy(new_item), "source": source_name, "target": new_item.get("name", "")}


def recruit_character(state: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    candidates = state.get("recruits", {}).get("candidates", [])
    rec = next((r for r in candidates if r.get("candidate_id") == candidate_id), None)
    if not rec:
        raise ValueError("招募对象不存在")
    if state["gold"] < rec["cost"]:
        raise ValueError("金币不足")
    if len(state["characters"]) >= MAX_ROSTER_SIZE:
        raise ValueError("总角色栏位已满")
    state["gold"] -= rec["cost"]
    # The preview is the exact character snapshot shown to the player, so
    # hiring it gives "what you saw is what you get" — no re-roll on join.
    ch = copy.deepcopy(rec.get("preview")) if isinstance(rec.get("preview"), dict) else None
    if not ch:
        ch = create_character(rec["class_id"], rec.get("name", "新成员"))
        while ch["level"] < rec.get("level", 1):
            level_up_character(ch)
    ch["id"] = rec["candidate_id"]
    ch["available"] = True
    ch["recruit_cost"] = int(rec.get("cost", 0))  # powers dismiss refund
    normalize_character(ch)
    state["characters"].append(ch)
    state["recruits"]["candidates"] = [r for r in candidates if r.get("candidate_id") != candidate_id]
    return ch


def dismiss_character(state: dict[str, Any], character_id: str) -> dict[str, Any]:
    """Dismiss a roster character, refunding part of their hire cost as gold.

    The character must not be in any formation and must not be the last remaining
    member of the roster. Refund is DISMISS_GOLD_REFUND of their last known
    recruit cost (best-effort: 0 for starter characters).
    """
    ch = get_character(state, character_id)
    if not ch:
        raise ValueError("角色不存在")
    teams = formation_member_team_map(state)
    if character_id in teams:
        raise ValueError("角色在编队中，请先移出编队")
    if len(state["characters"]) <= 1:
        raise ValueError("至少保留一名角色")
    refund = max(0, int(round(int(ch.get("recruit_cost", 0)) * DISMISS_GOLD_REFUND)))
    state["gold"] += refund
    # Drop any equipment owned by the dismissed character back into inventory.
    for slot, eq_id in (ch.get("equipment") or {}).items():
        if eq_id:
            eq = get_item(state, eq_id)
            if eq:
                eq["equipped_by"] = None
    state["characters"] = [c for c in state["characters"] if c.get("id") != character_id]
    return {"type": "dismiss", "character_id": character_id, "gold": refund, "name": ch.get("name", "")}


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
    quests = quest_list_view(state)
    return {
        "day": state["day"],
        "max_day": state["max_day"],
        "gold": state["gold"],
        "skill_essence": int(state["materials"].get(SKILL_ESSENCE_KEY, 0)),
        "promotion_badges": int(state["materials"].get(PROMOTION_BADGE_KEY, 0)),
        "materials": state["materials"],
        "materials_display": {MATERIAL_NAMES.get(k, k): v for k, v in state["materials"].items()},
        "consumables": state.get("consumables", {}),
        "expedition_points_left": max(0, 2 - len(state["expedition_plan"])),
        "party_summary": party_summary(state),
        "active_dungeons_summary": dungeon_list_view(state),
        "shop_summary": state.get("shop", {}),
        "recruits_summary": state.get("recruits", {}),
        "warnings": daily_warnings(state),
        "victory": state.get("victory", False),
        "defeat": state.get("defeat", False),
        "defeat_reason": state.get("defeat_reason"),
        "final_unlocked": state.get("final_unlocked", False),
        "last_result": state.get("last_result"),
        "retreat_strategy": state.get("retreat_strategy", "standard"),
        "retreat_strategy_label": RETREAT_LABELS.get(state.get("retreat_strategy", "standard"), "标准"),
        "quests": quests,
        "quests_summary": quests["summary"],
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
        "quests": copy.deepcopy(data.get("quests", {})),
        "quest_status_labels": copy.deepcopy(QUEST_STATUS_LABELS),
        "shop_config": copy.deepcopy(data.get("shop_config", {})),
        "recruit_config": copy.deepcopy(data.get("recruit_config", {})),
    }


def preset_list_view() -> dict[str, Any]:
    return {"active_preset_id": load_data().get("preset_id", ""), "presets": list_presets()}


def migrate_state(state: dict[str, Any]) -> dict[str, Any]:
    """Best-effort save migration for data-driven WOD attributes and skills."""
    rebuild_level_scaled_sheet = int(state.get("schema_version", 1)) < 3 or state.get("attribute_system_version") != 1
    state.setdefault("materials", {})
    # Consumable stock is a shared pool {template_id: count}. Old saves predating
    # the battle-consumption feature may lack it entirely; backfill so the pool
    # exists before any challenge tries to read/write it.
    if not isinstance(state.get("consumables"), dict):
        state["consumables"] = {"healing_potion": 3, "antidote": 2}
    state["materials"][SKILL_ESSENCE_KEY] = max(0, int(state["materials"].get(SKILL_ESSENCE_KEY, 0)))
    if PROMOTION_BADGE_KEY not in state["materials"]:
        state["materials"][PROMOTION_BADGE_KEY] = STARTING_PROMOTION_BADGES
    else:
        state["materials"][PROMOTION_BADGE_KEY] = max(0, int(state["materials"].get(PROMOTION_BADGE_KEY, 0)))
    for item in state.get("inventory", []):
        if isinstance(item, dict):
            normalize_equipment_item(item)
    for ch in state.get("characters", []):
        if rebuild_level_scaled_sheet:
            class_row = load_data()["class_by_id"].get(ch.get("class_id"))
            if class_row:
                ch["base_stats"] = stat_block_for_class(class_row, int(ch.get("level", 1)))
                ch["base_resistances"] = copy.deepcopy(class_row.get("resistances", {}))
                ch["attributes"] = attribute_block_for_class(class_row, int(ch.get("level", 1)))
        normalize_character(ch)
        normalize_character_equipment_occupancy(state, ch)
        stats = effective_stats(state, ch)
        ch["max_hp"] = int(stats.get("max_hp", ch.get("max_hp", 1)))
        ch["hp"] = min(int(ch.get("hp", ch["max_hp"])), ch["max_hp"])
        ch["max_mana"] = int(stats.get("max_mana", ch.get("max_mana", 0)))
        ch["mana"] = max(0, min(int(ch.get("mana", ch["max_mana"])), ch["max_mana"]))
    state["schema_version"] = 3
    state["attribute_system_version"] = 1
    # Quest system: backfill runtime fields for saves created before the
    # quest system existed, and normalize the quest instance list.
    state.setdefault("quests", [])
    state.setdefault("quest_flags", {})
    base_stats = default_quest_stats()
    existing_stats = state.get("quest_stats", {})
    if not isinstance(existing_stats, dict):
        existing_stats = {}
    merged_stats = copy.deepcopy(base_stats)
    for key, default_val in base_stats.items():
        merged_stats[key] = existing_stats.get(key, default_val) if isinstance(existing_stats.get(key), type(default_val)) else default_val
    state["quest_stats"] = merged_stats
    state.setdefault("daily_quest_day", 0)
    counters = state.setdefault("next_counters", {})
    if "quest" not in counters:
        counters["quest"] = 1 + sum(1 for q in state["quests"] if str(q.get("id", "")).startswith("quest_"))
    normalize_quest_instances(state)
    # Shop & recruitment migration. Old saves stored shop as {"items", "recruits"}
    # (a flat list) and had no separate recruits key. Replace those legacy shapes
    # with the new per-merchant / candidates structures; the daily refresh will
    # repopulate them on the next world_refresh, so no content is lost.
    shop = state.get("shop")
    if not isinstance(shop, dict) or "merchants" not in shop:
        state["shop"] = {"merchants": {}, "refresh_day": 0}
    else:
        state["shop"].setdefault("merchants", {})
        state["shop"].setdefault("refresh_day", 0)
    recruits = state.get("recruits")
    if not isinstance(recruits, dict) or "candidates" not in recruits:
        state["recruits"] = {"candidates": [], "refresh_day": 0}
    else:
        state["recruits"].setdefault("candidates", [])
        state["recruits"].setdefault("refresh_day", 0)
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
        earned_attr = attribute_points_earned_for_level(int(ch.get("level", 1)))
        spent_attr = attribute_points_spent(ch, class_row)
        members.append({
            "id": ch["id"],
            "name": ch["name"],
            "class_id": ch["class_id"],
            "class_name": ch["class_name"],
            "base_class_id": ch.get("base_class_id"),
            "class_path": copy.deepcopy(ch.get("class_path", [])),
            "class_meta": class_preset_meta(ch["class_id"]),
            "level": ch["level"],
            "exp": ch["exp"],
            "hp": ch["hp"],
            "max_hp": stats.get("max_hp", ch["max_hp"]),
            "mana": max(0, min(int(ch.get("mana", stats.get("max_mana", 0))), int(stats.get("max_mana", 0)))),
            "max_mana": int(stats.get("max_mana", ch.get("max_mana", 0))),
            "skill_points": int(ch.get("skill_points", 0)),
            "skill_upgrades": copy.deepcopy(ch.get("skill_upgrades", {})),
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
            "attribute_points": max(0, earned_attr - spent_attr),
            "attribute_points_per_level": attribute_points_per_level(),
            "attribute_points_earned": earned_attr,
            "attribute_points_spent": spent_attr,
            "derived_stats": copy.deepcopy(stats.get("derived", {})),
            "base_stats": copy.deepcopy(ch.get("base_stats", {})),
            "stat_growth": copy.deepcopy(class_row.get("stat_growth", {})),
            "attribute_growth": copy.deepcopy(class_row.get("attribute_growth", {})),
            "stat_breakdown": stat_breakdown_for_character(ch, class_row, stats),
            "attribute_breakdown": attribute_breakdown_for_character(ch, class_row),
            "skill_summary": skill_public_summary(ch, state),
            "promotion": character_promotion_summary(state, ch),
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
        "consumable_trigger_options": CONSUMABLE_TRIGGERS,
        "consumable_options": consumable_options_view(),
        "max_consumable_slots": MAX_CONSUMABLE_SLOTS,
        "consumables": state.get("consumables", {}),
    }


def dungeon_list_view(state: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for d in state["active_dungeons"]:
        if d.get("expired"):
            continue
        attention = []
        persistent = bool(d.get("persistent") or d.get("source_quest_id"))
        if d["remaining_days"] <= 1 and not d.get("is_final") and not persistent:
            attention.append("即将过期")
        if d["danger_level"] >= 5:
            attention.append("高风险")
        if d.get("scout_info"):
            attention.append("已侦察")
        if d.get("is_final"):
            attention.append("最终挑战")
        if persistent:
            attention.append("任务副本")
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
            "source_quest_id": d.get("source_quest_id"),
            "source_quest_title": d.get("source_quest_title"),
            "persistent": persistent,
        })
    return sorted(rows, key=lambda x: (not x["is_final"], x["persistent"], x["remaining_days"], -x["danger_level"]))


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
    data = load_data()
    formation = ensure_formations(state).get(team_id, {})
    formation_by_id = {cid: cell for cell, cid in formation.items()}
    for ch in ordered_party_members(state, team_id):
        normalize_character(ch)
        stats = effective_stats(state, ch)
        max_hp = int(stats.get("max_hp", ch["max_hp"]))
        hp = min(int(ch.get("hp", max_hp)), max_hp)
        max_mana = int(stats.get("max_mana", ch.get("max_mana", 0)))
        mana = max(0, min(int(ch.get("mana", max_mana)), max_mana))
        active_skills = active_skill_ids_for_character(ch)
        skill_data_by_id = {sid: upgraded_skill_for_character(ch, sid, data) for sid in active_skills}
        unit = Combatant({
            "id": ch["id"], "name": ch["name"], "side": "party", "class_id": ch["class_id"], "class_name": ch["class_name"],
            "team_id": team_id, "team_name": TEAM_LABELS.get(team_id, team_id),
            "level": ch["level"], "hp": hp, "max_hp": max_hp, "mana": mana, "max_mana": max_mana, "attack": int(stats.get("attack", 0)), "defense": int(stats.get("defense", 0)),
            "speed": int(stats.get("speed", 0)), "accuracy": int(stats.get("accuracy", 80)), "evasion": int(stats.get("evasion", 0)),
            "normal_speed": int(stats.get("normal_speed", stats.get("speed", 0))), "initiative_skill": copy.deepcopy(stats.get("initiative_skill")),
            "action_count": int(stats.get("action_count", 1)), "resistances": stats.get("resistances", {}), "special_effects": stats.get("special_effects", []),
            "attributes": copy.deepcopy(ch.get("attributes", {})), "derived_stats": copy.deepcopy(stats.get("derived", {})),
            "skills": active_skills, "skill_data_by_id": skill_data_by_id, "skill_uses": {}, "statuses": copy.deepcopy(ch.get("status_effects", [])),
            "cell": formation_by_id.get(ch["id"], "r2c1"), "tactics": copy.deepcopy(ch.get("tactics", {})), "source": ch, "guarding": False,
        })
        out.append(unit)
    for unit in out:
        for sid in unit["skills"]:
            unit["skill_uses"][sid] = int(unit.get("skill_data_by_id", {}).get(sid, {}).get("uses_per_dungeon", 999))
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


def skill_for_combatant(unit: Combatant, skill_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    if unit.get("side") == "party":
        row = unit.get("skill_data_by_id", {}).get(skill_id)
        if isinstance(row, dict) and row:
            return row
    data = data or load_data()
    return data["skill_by_id"].get(skill_id, {})


def can_combatant_use_skill(unit: Combatant, skill_id: str, data: dict[str, Any]) -> bool:
    if skill_id not in unit.get("skills", []):
        return False
    remaining = int(unit.get("skill_uses", {}).get(skill_id, 0))
    if remaining <= 0:
        return False
    skill = skill_for_combatant(unit, skill_id, data)
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
    skill = copy.deepcopy(skill_for_combatant(actor, sid, data))
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
            skill = skill_for_combatant(unit, sid, data)
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
        skill = skill_for_combatant(target, sid or "", data)
        if not sid or skill.get("type") not in {"guard", "buff", "support"}:
            continue
        if key not in defense_types_for_skill(skill):
            continue
        if not should_use_defense_response_skill(skill, target, party):
            continue
        if execute_player_skill(target, sid, party, [incoming_actor], rng, logs, report, reason=f"防御·{DEFENSE_TRIGGER_LABELS.get(key, key)}", preferred_ally=target):
            return


def skill_ai_rules_for_class(class_id: str | None, data: dict[str, Any]) -> list[dict[str, Any]]:
    by_class = data.get("skill_ai_by_class_id", {})
    own_rules = by_class.get(class_id or "", [])
    out = own_rules if isinstance(own_rules, list) else []
    base_id = base_class_id_for_class(class_id, data)
    if base_id and base_id != class_id:
        base_rules = by_class.get(base_id, [])
        if isinstance(base_rules, list):
            out = out + base_rules
    return out


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
        skill = skill_for_combatant(unit, skill_id, data)
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

    for rule in skill_ai_rules_for_class(class_id, data):
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


def _unit_hp_pct(unit: Combatant) -> float:
    mx = int(unit.get("max_hp", 0) or 0)
    return (int(unit.get("hp", 0)) / mx) if mx > 0 else 0.0


def _consumable_trigger_met(trigger: str, actor: Combatant, party: list[Combatant]) -> bool:
    """Whether a consumable's auto-use trigger currently applies.

    Party members share the consumable stock, so `party` is the full living
    roster the actor can react to.
    """
    living_allies = [u for u in party if u.get("hp", 0) > 0]
    if trigger == "self_hp_below_50":
        return _unit_hp_pct(actor) < 0.50
    if trigger == "self_hp_below_30":
        return _unit_hp_pct(actor) < 0.30
    if trigger == "ally_hp_below_30":
        return any(_unit_hp_pct(u) < 0.30 for u in living_allies)
    if trigger == "self_poisoned":
        return has_status(actor, "poison") or has_status(actor, "bleed")
    if trigger == "ally_poisoned":
        return any(has_status(u, "poison") or has_status(u, "bleed") for u in living_allies)
    if trigger == "self_cursed":
        return has_status(actor, "curse")
    return False


def use_consumable(actor: Combatant, consumable_id: str, report: dict[str, Any], logs: list[str]) -> bool:
    """Consume one charge from the shared pool and apply its effect.

    Returns True when a charge was spent (and an effect applied). The pool and
    a per-consumable usage counter live on the report; `resolve_challenge`
    writes the final tally back into state["consumables"] after the dungeon.
    """
    pool = report.get("_consumables_pool")
    if not isinstance(pool, dict) or pool.get(consumable_id, 0) <= 0:
        return False
    effect = consumable_effect(consumable_id)
    if not effect:
        return False
    pool[consumable_id] = int(pool.get(consumable_id, 0)) - 1
    report["consumables_used"][consumable_id] = int(report.get("consumables_used", {}).get(consumable_id, 0)) + 1
    cname = consumable_name(consumable_id)
    consumed_anything = False

    heal_amount = effect.get("heal")
    if isinstance(heal_amount, (int, float)) and heal_amount:
        before = int(actor["hp"])
        actor["hp"] = min(int(actor["max_hp"]), before + int(heal_amount))
        healed = int(actor["hp"]) - before
        report["healing_done"][actor["id"]] += healed
        consumed_anything = consumed_anything or healed > 0
        text = f"{actor['name']} 使用 {cname}，回复 {healed} HP"
        logs.append(text)
        record_event(report, {
            "type": "consumable", "text": text, "subtype": "heal",
            "actor": event_actor(actor), "target": event_actor(actor),
            "consumable": cname, "amount": healed,
            "target_hp_before": before, "target_hp_after": int(actor["hp"]),
            "target_statuses": copy.deepcopy(actor.get("statuses", [])),
        })

    cleanse_types = effect.get("cleanse")
    if isinstance(cleanse_types, list) and cleanse_types:
        removable = {str(t) for t in cleanse_types if isinstance(t, str)}
        before = list(actor.get("statuses", []))
        actor["statuses"] = [s for s in actor.get("statuses", []) if s["type"] not in removable]
        removed = len(before) - len(actor["statuses"])
        report["skill_usage"][actor["id"]]["cleanse_removed"] += removed
        consumed_anything = consumed_anything or removed > 0
        text = f"{actor['name']} 使用 {cname}，净化 {removed} 个异常状态"
        logs.append(text)
        record_event(report, {
            "type": "consumable", "text": text, "subtype": "cleanse",
            "actor": event_actor(actor), "target": event_actor(actor),
            "consumable": cname, "amount": removed,
            "removed_statuses": copy.deepcopy(before),
            "target_statuses": copy.deepcopy(actor.get("statuses", [])),
        })

    if not consumed_anything:
        # No-op use (e.g. quaffing a potion at full HP): refund the charge so
        # the player isn't charged for nothing and the AI doesn't loop on it.
        pool[consumable_id] = int(pool.get(consumable_id, 0)) + 1
        report["consumables_used"][consumable_id] = int(report["consumables_used"].get(consumable_id, 0)) - 1
        return False
    return True


def maybe_use_consumable(actor: Combatant, party: list[Combatant], report: dict[str, Any], logs: list[str]) -> bool:
    """Try the actor's configured consumable priority in order; one per turn."""
    for entry in actor.get("tactics", {}).get("consumable_priority", []) or []:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("consumable_id") or "")
        trigger = str(entry.get("trigger") or "")
        if not cid or trigger not in CONSUMABLE_TRIGGERS:
            continue
        if _consumable_trigger_met(trigger, actor, party) and use_consumable(actor, cid, report, logs):
            return True
    return False


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
        # Consumable auto-use runs before skill selection and costs the turn's
        # one potion budget; using one does not skip the subsequent skill.
        maybe_use_consumable(actor, party, report, logs)
        if actor["hp"] <= 0:
            return
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


def _unit_matches_tactic_check(unit: Combatant, check: dict[str, Any]) -> bool:
    if unit.get("side") != "party":
        return False
    class_filter = check.get("class_id") or check.get("class_ids")
    if class_filter:
        allowed = [class_filter] if isinstance(class_filter, str) else list(class_filter)
        if not class_matches_restriction(unit.get("class_id"), allowed):
            return False
    character_id = check.get("character_id")
    if character_id and unit.get("id") != character_id:
        return False
    if check.get("layer_override") and not unit.get("_layer_tactic_applied"):
        return False

    tactics = unit.get("tactics", {}) if isinstance(unit.get("tactics"), dict) else {}
    field = str(check.get("field", ""))
    expected = check.get("equals", check.get("value"))
    one_of = check.get("one_of")
    contains = check.get("contains")

    if field == "target_priority":
        if isinstance(one_of, list):
            return str(tactics.get("target_priority", "")) in {str(x) for x in one_of}
        return str(tactics.get("target_priority", "")) == str(expected)
    if field == "initiative_skill":
        if isinstance(one_of, list):
            return str(tactics.get("initiative_skill", "")) in {str(x) for x in one_of}
        return str(tactics.get("initiative_skill", "")) == str(expected)
    if field in {"skill_priority", "opening_skill_priority"}:
        values = [str(x) for x in tactics.get(field, []) if x]
        if contains is not None:
            return str(contains) in values
        if expected is not None:
            return bool(values) and values[0] == str(expected)
        return bool(values)
    if field == "defense_skill_by_type":
        trigger = str(check.get("trigger") or "")
        defense = tactics.get("defense_skill_by_type", {}) if isinstance(tactics.get("defense_skill_by_type"), dict) else {}
        if isinstance(one_of, list):
            return bool(trigger) and str(defense.get(trigger, "")) in {str(x) for x in one_of}
        return bool(trigger) and str(defense.get(trigger, "")) == str(expected)
    if field == "consumable_priority":
        values = tactics.get("consumable_priority", []) if isinstance(tactics.get("consumable_priority"), list) else []
        if contains is None and expected is not None:
            contains = expected
        return any(str(row.get("consumable_id", "")) == str(contains) for row in values if isinstance(row, dict))
    return False


def evaluate_layer_tactic_requirements(layer: dict[str, Any], party: list[Combatant]) -> list[str]:
    """Return unmet data-driven tactic requirements for a dungeon layer.

    A layer can declare `tactic_requirements` with reusable checks against the
    effective tactics active on that layer. Each requirement passes when all of
    its `checks` are satisfied by at least one matching party member.
    """
    failures: list[str] = []
    for req in layer.get("tactic_requirements", []) or []:
        if not isinstance(req, dict):
            continue
        checks = req.get("checks") if isinstance(req.get("checks"), list) else [req]
        ok = True
        for check in checks:
            if not isinstance(check, dict):
                ok = False
                break
            if not any(_unit_matches_tactic_check(unit, check) for unit in party):
                ok = False
                break
        if not ok:
            failures.append(str(req.get("failure") or req.get("label") or "未满足本层战术要求"))
    return failures


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
    tactic_failures = evaluate_layer_tactic_requirements(layer, party)
    if tactic_failures:
        text = f"教官终止第 {layer_index} 层演训：{tactic_failures[0]}"
        logs.append(text)
        for failure in tactic_failures:
            if failure not in report.setdefault("failure_reasons", []):
                report["failure_reasons"].append(failure)
            mechanic = f"第 {layer_index} 层战术要求：{failure}"
            if mechanic not in report.setdefault("revealed_mechanics", []):
                report["revealed_mechanics"].append(mechanic)
        add_critical_event(report, text)
        pre_events.append({
            "type": "tactic_requirement_failed",
            "text": text,
            "layer": layer_index,
            "failures": tactic_failures,
            "party": lineup_snapshot(party),
            "enemies": lineup_snapshot(enemies),
        })
        zero_stats: dict[str, int] = {}
        return {
            "index": layer_index,
            "name": layer.get("name", f"第 {layer_index} 层"),
            "type": layer.get("type", "battle"),
            "result": "retreated",
            "rounds": 0,
            "entry_party": entry_party,
            "party_start": lineup_snapshot(party),
            "enemy_start": lineup_snapshot(enemies),
            "party_end": lineup_snapshot(party),
            "enemy_end": lineup_snapshot(enemies),
            "pre_events": pre_events,
            "round_details": [],
            "party_hp": {u["name"]: hp_text(u) for u in party},
            "enemy_hp": {u["name"]: hp_text(u) for u in enemies},
            "enemy_remaining": [u["name"] for u in alive(enemies)],
            "damage_done": zero_stats,
            "damage_taken": zero_stats,
            "healing_done": zero_stats,
            "damage_by_type": zero_stats,
            "status_stats": zero_stats,
            "misses": zero_stats,
            "key_logs": logs[:80],
        }
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
        "losses": {"hp": {}, "mana": {}, "injuries": [], "durability": {}, "consumables": {}}, "layer_results": [], "damage_stats": {}, "healing_stats": {}, "mana_spent_stats": {}, "damage_taken_stats": {},
        "damage_by_type_stats": {}, "miss_stats": {}, "review_metrics": {}, "battle_recap": [], "critical_events": [],
        "status_stats": Counter(), "skill_usage_stats": {}, "party_skill_usage_stats": {}, "enemy_skill_usage_stats": {},
        "key_events": [], "failure_reasons": [], "revealed_mechanics": [], "turn_logs": [], "unit_names": {}, "initial_party": lineup_snapshot(party),
        "damage_done": defaultdict(float), "damage_taken": defaultdict(float), "healing_done": defaultdict(float), "mana_spent": defaultdict(float), "damage_by_type": defaultdict(float),
        "skill_usage": defaultdict(Counter), "misses": defaultdict(int), "backline_damage": 0, "extra_durability_loss": 0, "affix_mechanics": affix_mechanics,
        "consumables_used": {}, "_consumables_pool": dict(state.get("consumables", {})),
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
    # Write consumable consumption back into the shared stock. The battle ran
    # against tactic_state (a deep copy), so deduct here on the authoritative
    # state, driven by the per-consumable tally accumulated on the report.
    for cid, used in report.get("consumables_used", {}).items():
        used = max(0, int(used))
        if used <= 0:
            continue
        state.setdefault("consumables", {})
        state["consumables"][cid] = max(0, int(state["consumables"].get(cid, 0)) - used)
        report["losses"]["consumables"][consumable_name(cid)] = f"-{used}"
    apply_rewards_for_report(state, dungeon, template, report, rng, party)
    finalize_report(state, dungeon, template, report, party)
    # Feed dungeon outcomes into the quest system: clears advance clear_dungeon
    # objectives, and an unscented victory may complete a blind-victory hidden quest.
    record_quest_events(state, _quest_events_for_challenge(state, dungeon, template, report))
    state["next_counters"]["report"] += 1
    state["reports"].insert(0, sanitize_report(report))
    return state["reports"][0]


def _quest_events_for_challenge(state: dict[str, Any], dungeon: dict[str, Any], template: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    """Translate a challenge report into quest progress events."""
    events: list[dict[str, Any]] = []
    template_id = dungeon.get("template_id") or template.get("id")
    if report.get("result") == "victory":
        events.append({"event": "clear_dungeon", "dungeon_template_id": template_id, "amount": 1})
        if not dungeon.get("scout_info"):
            events.append({
                "event": "clear_unscouted_dungeon",
                "dungeon_template_id": template_id,
                "danger_level": int(dungeon.get("danger_level", 0)),
                "amount": 1,
            })
        # Streak objective: count victorious challenges already recorded today
        # (this report included). Two or more clears on the same day qualify.
        day = state.get("day", 1)
        clears_today = 1 + sum(
            1 for r in state.get("reports", [])
            if r.get("type") == "challenge" and r.get("result") == "victory" and r.get("day") == day
        )
        if clears_today >= 2:
            events.append({"event": "clear_two_dungeons_one_day", "amount": 1, "eligible": True})
    return events



def apply_equipment_durability_loss(state: dict[str, Any], party: list[Combatant], dungeon: dict[str, Any], report: dict[str, Any]) -> None:
    base_loss = 3 + dungeon["danger_level"] // 2 + int(report.get("extra_durability_loss", 0))
    if any(s.get("type") == "burn" for u in party for s in u.get("statuses", [])):
        base_loss += 2
    for unit in party:
        ch = get_character(state, unit["id"])
        if not ch:
            continue
        for item_id in dict.fromkeys(x for x in ch.get("equipment", {}).values() if x):
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
    essence = int(round((3 + int(dungeon.get("danger_level", 1))) * max(0.25, clear_ratio) * multiplier * (1.25 if success else 0.75)))
    state["gold"] += gold
    report["rewards"]["gold"] = gold
    report["rewards"]["exp"] = exp
    if essence > 0:
        state["materials"][SKILL_ESSENCE_KEY] = state["materials"].get(SKILL_ESSENCE_KEY, 0) + essence
        report["rewards"]["materials"][SKILL_ESSENCE_KEY] = essence
    if success and dungeon.get("reward_charges", 0) > 0:
        badges = 1 + (1 if int(dungeon.get("danger_level", 1)) >= 5 else 0)
        state["materials"][PROMOTION_BADGE_KEY] = state["materials"].get(PROMOTION_BADGE_KEY, 0) + badges
        report["rewards"]["materials"][PROMOTION_BADGE_KEY] = badges
    for k, v in base.get("materials", {}).items():
        amount = int(round(v * clear_ratio * multiplier))
        if amount > 0:
            state["materials"][k] = state["materials"].get(k, 0) + amount
            report["rewards"]["materials"][k] = amount
    for unit in party:
        ch = get_character(state, unit["id"])
        if ch:
            gain_exp(ch, exp)
    if success and base.get("guaranteed_equipment") and dungeon.get("reward_charges", 0) > 0:
        report["rewards"]["equipment"].extend(grant_equipment_rewards(
            state,
            list(base.get("guaranteed_equipment", []) or []),
            rng=rng,
            level=equipment_drop_level(state, dungeon),
        ))
    if success and base.get("equipment_pool") and dungeon.get("reward_charges", 0) > 0 and rng.random() < 0.75:
        eq_id = rng.choice(base["equipment_pool"])
        eq = instance_equipment(eq_id, rng=rng, level=equipment_drop_level(state, dungeon))
        state["inventory"].append(eq)
        # Store the full item object (not just the name) so the UI can render a
        # hover tooltip on the drop. `name` is kept for legacy/name-only callers.
        report["rewards"]["equipment"].append({"name": eq["name"], "item": copy.deepcopy(eq)})
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
        eq_names = [e["name"] if isinstance(e, dict) else str(e) for e in report["rewards"]["equipment"]]
        reward_bits.append("装备：" + "、".join(eq_names))
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
        "rewards": {"gold": 0, "exp": 8, "materials": {}, "equipment": []}, "losses": {"hp": {}, "injuries": [], "durability": {}, "consumables": {}},
        "layer_results": [], "damage_stats": {}, "healing_stats": {}, "damage_taken_stats": {}, "status_stats": {}, "skill_usage_stats": {},
        "key_events": lines, "failure_reasons": ["侦察占用一次远征机会，但降低了盲打风险。"], "revealed_mechanics": lines, "turn_logs": lines,
    }
    for ch in ordered_party_members(state, team_id):
        gain_exp(ch, 8)
    # Recon feeds scout_dungeon / scout_any_dungeon quest objectives.
    record_quest_events(state, [{
        "event": "scout_dungeon",
        "dungeon_template_id": dungeon.get("template_id") or template.get("id"),
        "amount": 1,
    }])
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
        "losses": {"hp": {}, "mana": {}, "injuries": [], "durability": {}, "consumables": {}}, "layer_results": [], "damage_stats": {}, "healing_stats": {}, "damage_taken_stats": {}, "status_stats": {}, "skill_usage_stats": {},
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
        # New day: roll fresh daily quests and re-check hidden quest conditions.
        refresh_daily_quests(state)
        check_hidden_reveals(state)


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
