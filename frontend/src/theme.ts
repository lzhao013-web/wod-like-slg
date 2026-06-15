// Central theming: icons, colors, and labels for every game concept.
// Icons use emoji to stay dependency-free and render cross-platform.

import wodDefaultPreset from './presets/wodDefaultPreset.json'

export type ElementKey = 'physical' | 'poison' | 'magic' | 'curse' | 'fire' | 'bleed'

export interface ElementMeta { key: ElementKey; label: string; icon: string; color: string }

export const ELEMENTS: Record<ElementKey, ElementMeta> = {
  physical: { key: 'physical', label: '物理', icon: '🥊', color: '#c7d0dc' },
  poison: { key: 'poison', label: '毒', icon: '☠️', color: '#7cb342' },
  magic: { key: 'magic', label: '魔法', icon: '🔮', color: '#5c9cff' },
  curse: { key: 'curse', label: '诅咒', icon: '👁️', color: '#b388ff' },
  fire: { key: 'fire', label: '火焰', icon: '🔥', color: '#ff7043' },
  bleed: { key: 'bleed', label: '流血', icon: '🩸', color: '#ef5350' },
}

export function elementMeta(key: string): ElementMeta {
  return (ELEMENTS as Record<string, ElementMeta>)[key] ?? { key, label: key, icon: '•', color: '#9fb1ca' }
}

export type RarityKey = 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary'

export interface RarityMeta { key: RarityKey; label: string; color: string; glow: string }

export const RARITY: Record<string, RarityMeta> = {
  common: { key: 'common', label: '普通', color: '#9fb1ca', glow: 'rgba(159,177,202,0.25)' },
  uncommon: { key: 'uncommon', label: '优质', color: '#66bb6a', glow: 'rgba(102,187,106,0.30)' },
  rare: { key: 'rare', label: '稀有', color: '#42a5f5', glow: 'rgba(66,165,245,0.40)' },
  epic: { key: 'epic', label: '史诗', color: '#ab47bc', glow: 'rgba(171,71,188,0.45)' },
  legendary: { key: 'legendary', label: '传说', color: '#ffb300', glow: 'rgba(255,179,0,0.55)' },
}

export function rarityMeta(key?: string): RarityMeta {
  return (key && RARITY[key]) || RARITY.common
}

export interface ClassMeta {
  id: string
  icon: string
  accent: string
  roleShort: string
  position: 'front' | 'mid' | 'back' | 'flex'
  defaultTargetPriority?: string
  defaultSkillMode?: string
  defaultOpeningSkillPriority?: string[]
  defaultSkillPriority?: string[]
  defaultDefenseSkillByType?: Record<string, string>
}

export const ACTIVE_PRESET = wodDefaultPreset
export const CLASS_META = wodDefaultPreset.classMeta as Record<string, ClassMeta>

export function classMeta(id: string): ClassMeta {
  return CLASS_META[id] ?? { id, icon: '❔', accent: '#9fb1ca', roleShort: '?', position: 'flex' }
}

export interface StatMeta { key: string; label: string; icon: string; max: number; desc?: string }

// Tuned "max" values for bar normalization (purely visual scaling).
export const STATS: StatMeta[] = [
  { key: 'attack', label: '攻击', icon: '🗡️', max: 40 },
  { key: 'defense', label: '防御', icon: '🛡️', max: 30 },
  { key: 'speed', label: '速度', icon: '💨', max: 24 },
  { key: 'accuracy', label: '命中', icon: '🎯', max: 120 },
  { key: 'evasion', label: '闪避', icon: '🍃', max: 40 },
]

export const STAT_LABELS: Record<string, string> = {
  max_hp: '生命上限',
  max_mana: '法力上限',
  hp_bonus: '生命加成',
  attack: '攻击',
  attack_bonus: '攻击加成',
  defense: '防御',
  defense_bonus: '防御加成',
  speed: '速度',
  speed_bonus: '速度加成',
  accuracy: '命中',
  accuracy_bonus: '命中加成',
  evasion: '闪避',
  evasion_bonus: '闪避加成',
  action_count: '行动次数',
  mana: '法力上限',
  melee_score: '近战评分',
  ranged_score: '射击评分',
  finesse_score: '技巧评分',
  magic_score: '奥术评分',
  faith_score: '信仰评分',
  healing_score: '治疗评分',
  guard_score: '防护评分',
  tactics_score: '战术评分',
}

export const STAT_SHORT_LABELS: Record<string, string> = {
  max_hp: '生命',
  attack: '攻',
  defense: '防',
  speed: '速',
  accuracy: '命',
  evasion: '闪',
}

export function statLabel(key: string, short = false): string {
  return (short ? STAT_SHORT_LABELS[key] : undefined) ?? STAT_LABELS[key] ?? key
}

export const ATTRIBUTES: StatMeta[] = [
  { key: 'strength', label: '力量', icon: '💪', max: 28, desc: '提高生命、攻击、防御，并强化近战类技能。' },
  { key: 'constitution', label: '体质', icon: '❤️', max: 28, desc: '提高生命、防御，并强化防护/守卫类技能。' },
  { key: 'dexterity', label: '灵巧', icon: '🤲', max: 28, desc: '提高命中、闪避，并强化射击与技巧类技能。' },
  { key: 'agility', label: '敏捷', icon: '💨', max: 28, desc: '提高速度、闪避，并强化盗贼/游侠的行动类技能。' },
  { key: 'intelligence', label: '智力', icon: '📘', max: 28, desc: '提高奥术法术、法力与战术理解。' },
  { key: 'willpower', label: '意志', icon: '🧠', max: 28, desc: '提高法力、信仰与防护稳定性。' },
  { key: 'perception', label: '感知', icon: '👁️', max: 28, desc: '提高命中、射击与战术技能表现。' },
  { key: 'charisma', label: '魅力', icon: '✨', max: 28, desc: '提高治疗、祝福与信仰支援技能。' },
]

export interface StatusMeta { icon: string; label: string; tone: 'bad' | 'good' | 'neutral' }

// Maps status effect type -> display. Falls back gracefully.
const STATUS_MAP: Record<string, StatusMeta> = {
  poison: { icon: '☠️', label: '中毒', tone: 'bad' },
  bleed: { icon: '🩸', label: '流血', tone: 'bad' },
  burn: { icon: '🔥', label: '燃烧', tone: 'bad' },
  curse: { icon: '👁️', label: '诅咒', tone: 'bad' },
  armor_break: { icon: '📉', label: '破甲', tone: 'bad' },
  stun: { icon: '💫', label: '眩晕', tone: 'bad' },
  slow: { icon: '🕸️', label: '减速', tone: 'bad' },
  marked: { icon: '🎯', label: '标记', tone: 'bad' },
  vulnerable: { icon: '🪓', label: '脆弱', tone: 'bad' },
  enfeeble: { icon: '🥀', label: '虚弱', tone: 'bad' },
  guarding: { icon: '🛡️', label: '护卫', tone: 'good' },
  shield_wall: { icon: '🧱', label: '盾墙', tone: 'good' },
  protected: { icon: '✨', label: '受护', tone: 'good' },
  focus: { icon: '🎯', label: '专注', tone: 'good' },
  might: { icon: '💪', label: '强攻', tone: 'good' },
  barrier: { icon: '🫧', label: '屏障', tone: 'good' },
  ward: { icon: '🔆', label: '圣佑', tone: 'good' },
  evasion_up: { icon: '🌫️', label: '闪避', tone: 'good' },
  regeneration: { icon: '🌿', label: '再生', tone: 'good' },
  haste: { icon: '⚡', label: '加速', tone: 'good' },
}

export function statusMeta(type: string): StatusMeta {
  return STATUS_MAP[type] ?? { icon: '▪', label: type, tone: 'neutral' }
}

export const FOCUS_LABELS: Record<string, string> = {
  melee: '近战',
  ranged: '射击',
  finesse: '技巧',
  magic: '奥术',
  faith: '信仰',
  healing: '治疗',
  guard: '防护',
  tactics: '战术',
}

export interface FocusMeta { key: string; label: string; scoreKey: string; attrs: string[]; desc: string }

export const FOCUS_META: FocusMeta[] = [
  { key: 'melee', label: '近战', scoreKey: 'melee_score', attrs: ['力量', '灵巧', '敏捷'], desc: '用于重击、顺劈、斩杀等近战技能。' },
  { key: 'ranged', label: '射击', scoreKey: 'ranged_score', attrs: ['感知', '灵巧', '敏捷'], desc: '用于瞄准射击、标记、穿甲箭等远程技能。' },
  { key: 'finesse', label: '技巧', scoreKey: 'finesse_score', attrs: ['灵巧', '敏捷', '感知'], desc: '用于背刺、破甲、毒刃、肾击等盗贼技能。' },
  { key: 'magic', label: '奥术', scoreKey: 'magic_score', attrs: ['智力', '意志', '感知'], desc: '用于奥术箭、火球、诅咒、陨火雨等法术。' },
  { key: 'faith', label: '信仰', scoreKey: 'faith_score', attrs: ['意志', '魅力', '智力'], desc: '用于圣佑、驱邪、群体净化等神术。' },
  { key: 'healing', label: '治疗', scoreKey: 'healing_score', attrs: ['魅力', '意志', '智力'], desc: '用于治疗术、群体治疗、神圣庇护等恢复技能。' },
  { key: 'guard', label: '防护', scoreKey: 'guard_score', attrs: ['体质', '意志', '力量'], desc: '用于保护、盾墙、盾击、壁垒类技能。' },
  { key: 'tactics', label: '战术', scoreKey: 'tactics_score', attrs: ['感知', '智力', '魅力'], desc: '用于战斗专注、挑衅与队伍战术类效果。' },
]

export function focusMeta(focus: string): FocusMeta {
  return FOCUS_META.find(f => f.key === focus) ?? { key: focus, label: focusLabel(focus), scoreKey: `${focus}_score`, attrs: [], desc: '' }
}

export function focusLabel(focus: string): string {
  return FOCUS_LABELS[focus] ?? focus
}

export function focusCompositionLabel(focus: string): string {
  const meta = focusMeta(focus)
  return meta.attrs.length > 0 ? meta.attrs.join(' / ') : focusLabel(focus)
}

export function focusScoreKey(focus: string): string {
  return focusMeta(focus).scoreKey
}

export const TARGET_RULE_LABELS: Record<string, string> = {
  front: '前排',
  rear: '后排',
  lowest_hp: '最低生命',
  highest_attack: '最高攻击',
  highest_defense: '最高防御',
  elite: '精英/Boss',
  all: '全体',
  cluster: '集群',
  all_front: '前/中排',
  melee: '近战目标',
  self: '自身',
  ally_all: '全体友方',
  ally_low_hp: '低血友方',
  ally_status: '异常友方',
  ally_backline: '后排友方',
  ally_front: '前排友方',
  ally_back: '后排友方',
}

export function targetRuleLabel(rule: string): string {
  return TARGET_RULE_LABELS[rule] ?? rule
}

export const RANGE_LABELS: Record<string, string> = {
  melee: '近战',
  ranged: '远程',
  ally: '友方',
  self: '自身',
  any: '任意',
}

export function rangeLabel(range: string): string {
  return RANGE_LABELS[range] ?? range
}

export const ATTACK_TYPE_LABELS: Record<string, string> = {
  melee: '近战',
  ranged: '远程',
  magic: '魔法',
  mental: '精神',
  special: '特殊',
}

export const ATTACK_TYPE_DESCRIPTIONS: Record<string, string> = {
  melee: '近战攻击：剑、斧、爪、撞击等贴身攻击；只会触发可防御“近战”的防御技能。',
  ranged: '远程攻击：弓箭、投射物、远距离射击等攻击方式；只会触发可防御“远程”的防御技能。',
  magic: '魔法攻击：奥术、火焰、闪电等法术攻击方式；伤害抗性仍按具体伤害类型结算。',
  mental: '精神攻击：诅咒、恐惧、挑衅、心智压制等影响意志/精神的攻击方式。',
  special: '特殊攻击：毒雾、影袭、位移扑杀、地裂等不适合归入前四类的攻击方式。',
}

export function attackTypeLabel(type?: string): string {
  return type ? ATTACK_TYPE_LABELS[type] ?? type : ''
}

export function attackTypeDescription(type?: string): string {
  return type ? ATTACK_TYPE_DESCRIPTIONS[type] ?? `攻击方式：${attackTypeLabel(type)}` : ''
}

export const SPECIAL_EFFECT_LABELS: Record<string, string> = {
  healing_bonus_minor: '小幅治疗加成',
  healing_bonus: '治疗加成',
  fire_bonus_minor: '小幅火焰加成',
  guard_bonus: '护卫加成',
}

export function specialEffectLabel(key: string): string {
  return SPECIAL_EFFECT_LABELS[key] ?? key.replace(/_/g, ' ')
}

export function translateGameText(text: string): string {
  if (!text) return text
  const terms: Record<string, string> = {
    armor_break: statusMeta('armor_break').label,
    shield_wall: statusMeta('shield_wall').label,
    guarding: statusMeta('guarding').label,
    evasion_up: statusMeta('evasion_up').label,
    marked: statusMeta('marked').label,
    vulnerable: statusMeta('vulnerable').label,
    enfeeble: statusMeta('enfeeble').label,
    regeneration: statusMeta('regeneration').label,
    poison: statusMeta('poison').label,
    bleed: statusMeta('bleed').label,
    burn: statusMeta('burn').label,
    curse: statusMeta('curse').label,
    stun: statusMeta('stun').label,
    slow: statusMeta('slow').label,
    focus: statusMeta('focus').label,
    might: statusMeta('might').label,
    barrier: statusMeta('barrier').label,
    ward: statusMeta('ward').label,
    physical: ELEMENTS.physical.label,
    melee: ATTACK_TYPE_LABELS.melee,
    ranged: ATTACK_TYPE_LABELS.ranged,
    mental: ATTACK_TYPE_LABELS.mental,
    special: ATTACK_TYPE_LABELS.special,
    magic: ELEMENTS.magic.label,
    fire: ELEMENTS.fire.label,
    attack: STAT_LABELS.attack,
    defense: STAT_LABELS.defense,
    speed: STAT_LABELS.speed,
    accuracy: STAT_LABELS.accuracy,
    evasion: STAT_LABELS.evasion,
    max_hp: STAT_LABELS.max_hp,
  }
  let out = text
  for (const [key, label] of Object.entries(terms)) {
    out = out.replace(new RegExp(`\\b${key}\\b`, 'g'), label)
  }
  return out
}

export interface ResultMeta { label: string; icon: string; color: string }

export const RESULT_META: Record<string, ResultMeta> = {
  victory: { label: '胜利', icon: '🏆', color: '#66bb6a' },
  retreated: { label: '撤退', icon: '🏳️', color: '#ffb74d' },
  defeat: { label: '失败', icon: '💀', color: '#ef5350' },
  scouted: { label: '侦察完成', icon: '🔭', color: '#5c9cff' },
  rested: { label: '休整', icon: '🏕️', color: '#81d4fa' },
}

export function resultMeta(result: string): ResultMeta {
  return RESULT_META[result] ?? { label: result || '未知', icon: '•', color: '#9fb1ca' }
}

// Dungeon themes -> ambient icon + accent for atmosphere.
const THEME_ICONS: Record<string, string> = {
  '蜘蛛': '🕷️', '毒': '☠️', '盗贼': '🗡️', '刺客': '🗡️', '弓': '🏹',
  '矿洞': '⛏️', '岩': '🪨', '石': '🗿', '野兽': '🐻', '狼': '🐺', '熊': '🐻',
  '墓穴': '⚰️', '亡灵': '💀', '古代': '🏛️', '圣殿': '⛩️', '诅咒': '👁️',
  '火焰': '🔥', '熔岩': '🌋', '冰': '❄️', '森林': '🌲', '深海': '🌊', '龙': '🐉',
}
const THEME_ACCENTS: Record<string, string> = {
  '毒': '#7cb342', '火': '#ff7043', '熔岩': '#ff5252', '冰': '#4fc3f7',
  '诅咒': '#b388ff', '亡灵': '#9e9e9e', '墓穴': '#8d86c5', '龙': '#ffb300',
}

export function themeIcon(theme: string): string {
  for (const key of Object.keys(THEME_ICONS)) {
    if (theme.includes(key)) return THEME_ICONS[key]
  }
  return '🏰'
}

export function themeAccent(theme: string): string {
  for (const key of Object.keys(THEME_ACCENTS)) {
    if (theme.includes(key)) return THEME_ACCENTS[key]
  }
  return '#6f8caf'
}

// Enemy tags -> a representative icon.
const TAG_ICONS: Record<string, string> = {
  boss: '👑', final: '🐉', elite: '🎖️', beast: '🐾', small: '🐭', spider: '🕷️',
  human: '🧑', ranged: '🏹', caster: '🔮', magic: '🔮', poison: '☠️', fire: '🔥',
  undead: '💀', construct: '🤖', elemental: '🌋', armored: '🛡️',
}

export function enemyIcon(tags: string[] = [], name = ''): string {
  for (const tag of tags) if (TAG_ICONS[tag]) return TAG_ICONS[tag]
  const map: Record<string, string> = { '蜘蛛': '🕷️', '盗贼': '🥷', '弓手': '🏹', '熊': '🐻', '狼': '🐺', '鼠': '🐭', '虫': '🪲', '怪': '👹', '王': '👑', '后': '👑', '兽': '🐾' }
  for (const k of Object.keys(map)) if (name.includes(k)) return map[k]
  return '👾'
}

export const AFFIX_ICON = '🌀'
export const SLOT_ICON: Record<string, string> = { weapon: '⚔️', armor: '🥋', trinket: '💍' }
export const SLOT_LABEL: Record<string, string> = { weapon: '武器', armor: '护甲', trinket: '饰品' }

export const MATERIAL_ICON: Record<string, string> = {
  皮革: '🟫', 毒囊: '🟢', 布料: '🧵', 矿石: '🪨', 盾牌材料: '🛡️',
  野兽牙: '🦷', 奥术尘: '✨', 古代遗物: '🏺', 火焰核心: '🔴', 胜利徽记: '🎖️',
}

// English material key (as used in report rewards) -> Chinese display name.
export const MATERIAL_LABEL_EN: Record<string, string> = {
  leather: '皮革', venom_sac: '毒囊', cloth: '布料', ore: '矿石', shield_parts: '盾牌材料',
  beast_fang: '野兽牙', arcane_dust: '奥术尘', relic: '古代遗物', fire_core: '火焰核心', glory: '胜利徽记',
}

export function materialName(key: string): string {
  return MATERIAL_LABEL_EN[key] ?? key
}

export function materialIcon(name: string): string {
  return MATERIAL_ICON[name] ?? '📦'
}

// Skills/class skill lists are supplied by the active preset instead of being
// duplicated in components.
export interface SkillMeta {
  id: string
  name: string
  type: string
  uses?: number | null
  uses_per_dungeon?: number | null
  mana_cost?: number
  category?: string
  tags?: string[]
  discipline?: string
  description?: string
  damage_types?: string[]
  attack_type?: string
  defense_types?: string[]
  status_effects?: { type: string; duration?: number; potency?: number; chance?: number }[]
  status?: { type: string; potency?: number }[]
  level_required?: number
  attribute_focus?: string
  attribute_scale?: number
  power?: number
  accuracy_modifier?: number
  target_rule?: string
  range?: string
  target_count?: number | null
  ignore_defense?: number
  defense_factor?: number | null
  crit_chance?: number
  crit_multiplier?: number
  execute_bonus?: number
  bonus_vs_status?: string[]
  status_bonus?: number
  cleanse_statuses?: string[]
  speed_formula?: Record<string, any> | null
  is_initiative_skill?: boolean
}
export const SKILLS = wodDefaultPreset.skills as Record<string, SkillMeta>

export const CLASS_SKILLS = wodDefaultPreset.classSkills as Record<string, string[]>

export function skillsForClass(classId: string): SkillMeta[] {
  return (CLASS_SKILLS[classId] ?? []).map(id => SKILLS[id]).filter(Boolean)
}

export const SKILL_ICON: Record<string, string> = {
  damage: '🗡️', heal: '💚', cleanse: '✨', guard: '🛡️', buff: '⬆️', support: '🔆', debuff: '📉', passive: '⚡',
}
