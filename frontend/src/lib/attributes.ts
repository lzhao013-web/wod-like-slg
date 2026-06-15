// Local, pure replica of backend `attribute_derived_stats` + `attribute_focus_score`.
// Used for instant client-side preview of attribute allocations WITHOUT a round trip.
// When the backend formula changes, mirror it here — keep these in sync.

export const ATTRIBUTE_KEYS = [
  'strength',
  'constitution',
  'dexterity',
  'agility',
  'intelligence',
  'willpower',
  'perception',
  'charisma',
] as const

export type AttributeKey = (typeof ATTRIBUTE_KEYS)[number]

// Same weights as backend SKILL_FOCUS_WEIGHTS.
export const SKILL_FOCUS_WEIGHTS: Record<string, Record<string, number>> = {
  melee: { strength: 1.35, dexterity: 1.0, agility: 0.35 },
  ranged: { perception: 1.25, dexterity: 1.0, agility: 0.55 },
  finesse: { dexterity: 1.25, agility: 1.05, perception: 0.45 },
  magic: { intelligence: 1.35, willpower: 1.0, perception: 0.35 },
  faith: { willpower: 1.25, charisma: 1.05, intelligence: 0.45 },
  healing: { charisma: 1.25, willpower: 1.05, intelligence: 0.35 },
  guard: { constitution: 1.25, willpower: 0.85, strength: 0.65 },
  tactics: { perception: 1.1, intelligence: 0.9, charisma: 0.65 },
}

function attributeFocusScore(attrs: Record<string, number>, focus: string): number {
  const weights = SKILL_FOCUS_WEIGHTS[focus] || {}
  if (!weights) return 0
  return Object.keys(weights).reduce((sum, k) => sum + (attrs[k] ?? 8) * weights[k], 0)
}

export interface DerivedStatView {
  hp_bonus: number
  attack_bonus: number
  defense_bonus: number
  speed_bonus: number
  accuracy_bonus: number
  evasion_bonus: number
  mana: number
  melee_score: number
  ranged_score: number
  finesse_score: number
  magic_score: number
  faith_score: number
  healing_score: number
  guard_score: number
  tactics_score: number
}

/** Mirrors backend `attribute_derived_stats`. Returns derived stats from raw attributes. */
export function deriveStatsFromAttributes(attributes: Record<string, number>): DerivedStatView {
  const get = (k: string) => Math.floor(Number(attributes[k] ?? 8))
  const strength = get('strength')
  const constitution = get('constitution')
  const dexterity = get('dexterity')
  const agility = get('agility')
  const intelligence = get('intelligence')
  const willpower = get('willpower')
  const perception = get('perception')
  const charisma = get('charisma')
  return {
    hp_bonus: strength + constitution * 2,
    attack_bonus: Math.max(0, Math.floor(strength / 4) + Math.floor(dexterity / 8)),
    defense_bonus: Math.max(0, Math.floor(constitution / 4) + Math.floor(strength / 10)),
    speed_bonus: Math.max(0, Math.floor(agility / 8) + Math.floor(perception / 14)),
    accuracy_bonus: Math.max(0, Math.floor((dexterity + perception) / 6)),
    evasion_bonus: Math.max(0, Math.floor((agility + dexterity) / 8)),
    mana: intelligence * 2 + willpower + Math.floor(charisma / 2),
    melee_score: Math.round(attributeFocusScore(attributes, 'melee')),
    ranged_score: Math.round(attributeFocusScore(attributes, 'ranged')),
    finesse_score: Math.round(attributeFocusScore(attributes, 'finesse')),
    magic_score: Math.round(attributeFocusScore(attributes, 'magic')),
    faith_score: Math.round(attributeFocusScore(attributes, 'faith')),
    healing_score: Math.round(attributeFocusScore(attributes, 'healing')),
    guard_score: Math.round(attributeFocusScore(attributes, 'guard')),
    tactics_score: Math.round(attributeFocusScore(attributes, 'tactics')),
  }
}
