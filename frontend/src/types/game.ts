export type Dict<T = unknown> = Record<string, T>

export interface GameStateView {
  day: number
  max_day: number
  gold: number
  skill_essence?: number
  promotion_badges?: number
  materials: Record<string, number>
  materials_display: Record<string, number>
  consumables: Record<string, number>
  expedition_points_left: number
  party_summary: PartySummary
  active_dungeons_summary: DungeonCardView[]
  shop_summary: ShopView
  recruits_summary: RecruitsView
  warnings: string[]
  victory: boolean
  defeat: boolean
  defeat_reason?: string | null
  final_unlocked: boolean
  retreat_strategy: string
  retreat_strategy_label: string
  last_result?: unknown
  quests?: QuestListView
  quests_summary?: QuestListSummary
}

export type QuestType = 'story' | 'daily' | 'hidden'
export type QuestStatus = 'available' | 'active' | 'completed' | 'claimed' | 'expired' | 'hidden'

export interface QuestObjective {
  id: string
  kind: string
  label: string
  required: number
  current: number
  completed: boolean
}

export interface QuestRewards {
  gold: number
  exp: number
  materials: Record<string, number>
  flags?: Record<string, boolean>
}

export interface QuestView {
  id: string
  template_id: string
  type: QuestType
  story_kind: string
  chain_id: string
  title: string
  description: string
  status: QuestStatus
  status_label: string
  created_day: number | null
  accepted_day: number | null
  expires_day: number | null
  completed_day: number | null
  claimed_day: number | null
  objectives: QuestObjective[]
  all_completed: boolean
  rewards: QuestRewards
  next_quests: string[]
  revealed_from_hidden: boolean
  linked_dungeon_ids: string[]
  sort: number
}

export interface QuestListSummary {
  available_count: number
  active_count: number
  claimable_count: number
  daily_day: number | null
}

export interface QuestListView {
  available: QuestView[]
  active: QuestView[]
  completed: QuestView[]
  claimed: QuestView[]
  expired: QuestView[]
  summary: QuestListSummary
}

export interface GamePresetView {
  id: string
  name: string
  description: string
  path?: string
  files?: Record<string, string>
  class_ui: Record<string, CharacterView['class_meta']>
  starter_roster?: Array<Record<string, any>>
  starter_formations?: Record<string, Record<string, string>>
  starter_equipment?: Array<Record<string, any>>
  recruit_pool?: string[]
  recruit_names?: string[]
  skill_tree?: Record<string, Array<Record<string, any>>>
  classes: Array<Record<string, any>>
  skills: SkillSummary[]
  equipment: Array<Record<string, any>>
  enemies: Array<Record<string, any>>
  dungeons: Array<Record<string, any>>
  affixes: Array<Record<string, any>>
  skill_ai: Record<string, Array<Record<string, any>>>
}

export interface CharacterView {
  id: string
  name: string
  class_id: string
  class_name: string
  base_class_id?: string
  class_path?: string[]
  class_meta?: {
    icon?: string
    accent?: string
    role_short?: string
    position?: 'front' | 'mid' | 'back' | 'flex'
    default_target_priority?: string
  }
  level: number
  exp: number
  hp: number
  max_hp: number
  mana?: number
  max_mana?: number
  skill_points?: number
  skill_upgrades?: Record<string, { level: number; choices?: Record<string, string> }>
  learned_skills?: string[]
  injury_state: string
  available: boolean
  status_effects: Array<{ type: string; duration: number; potency: number }>
  tactics: {
    target_priority: string
    initiative_skill?: string
    skill_priority?: string[]
    opening_skill_priority?: string[]
    defense_skill_by_type?: Record<string, string>
    consumable_priority?: ConsumableTacticEntry[]
  }
  equipment: Record<string, string | null>
  effective_stats: Record<string, any>
  base_stats?: Record<string, number>
  stat_growth?: Record<string, number>
  stat_breakdown?: Record<string, StatBreakdown>
  attributes?: Record<string, number>
  attribute_growth?: Record<string, number>
  attribute_breakdown?: Record<string, StatBreakdown>
  attribute_names?: Record<string, string>
  attribute_icons?: Record<string, string>
  attribute_points?: number
  attribute_points_per_level?: number
  attribute_points_earned?: number
  attribute_points_spent?: number
  derived_stats?: Record<string, number>
  skill_summary?: SkillSummary[]
  promotion?: CharacterPromotion
  in_formation: boolean
  team_id?: string | null
  team_name?: string | null
}

export interface CharacterTactics {
  target_priority: string
  initiative_skill?: string
  skill_priority?: string[]
  opening_skill_priority?: string[]
  defense_skill_by_type?: Record<string, string>
  consumable_priority?: ConsumableTacticEntry[]
}

export interface ConsumableTacticEntry {
  consumable_id: string
  trigger: string
}

export interface ConsumableOption {
  id: string
  name: string
  summary: string
  effect: { heal?: number; cleanse?: string[] }
}

export interface StatBreakdown {
  base: number
  level_growth: number
  raw: number
  raw_adjustment?: number
  bonus: number
  final: number
  spent?: number
  growth_per_level?: number
  growth_text?: string
}

export interface SkillSummary {
  id: string
  name: string
  type: string
  category?: string
  tags?: string[]
  discipline?: string
  description?: string
  damage_types?: string[]
  attack_type?: string
  defense_types?: string[]
  status_effects?: Array<{ type: string; duration?: number; potency?: number; chance?: number }>
  uses_per_dungeon?: number
  level_required?: number
  tree_tier?: number
  tree_x?: number | null
  tree_y?: number | null
  skill_point_cost?: number
  prerequisites?: string[]
  prerequisite_names?: string[]
  unlockable?: boolean
  unlock_reason?: string
  learned?: boolean
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
  mana_cost?: number
  speed_formula?: Record<string, any> | null
  is_initiative_skill?: boolean
  skill_level?: number
  skill_max_level?: number
  skill_upgrade_cost?: number
  skill_upgrade_currency?: string
  skill_upgrade_currency_name?: string
  skill_upgradeable?: boolean
  skill_upgrade_reason?: string
  skill_upgrade_choices?: SkillUpgradeChoice[]
  skill_selected_upgrade_choices?: Record<string, string>
  skill_selected_upgrade_choice_names?: Record<string, string>
}

export interface CharacterPromotion {
  promoted: boolean
  base_class_id: string
  base_class_name: string
  current_class_id: string
  current_class_name: string
  promotion_level?: number | null
  path: Array<{ class_id: string; name: string }>
  options: PromotionOption[]
}

export interface PromotionOption {
  class_id: string
  name: string
  role: string
  base_class_id: string
  description?: string
  level_required: number
  cost: Record<string, number>
  cost_rows: Array<{ key: string; name: string; amount: number }>
  can_promote: boolean
  reason: string
  skill_ids: string[]
  skill_names: string[]
  class_meta?: CharacterView['class_meta']
  stat_growth?: Record<string, number>
  attribute_growth?: Record<string, number>
}

export interface SkillUpgradeChoice {
  id: string
  name: string
  description?: string
  modifiers?: Record<string, any>
}

export interface PartySummary {
  members: CharacterView[]
  formation: Record<string, string>
  formations: Record<string, Record<string, string>>
  team_labels: Record<string, string>
  member_team: Record<string, string>
  max_team_size: number
  retreat_strategy: string
  layer_tactics?: Record<string, Record<string, CharacterTactics>>
  tactic_layer_options?: Array<{ index: number; label: string }>
}

export interface EquipmentItem {
  instance_id: string
  template_id: string
  base_name?: string
  name: string
  slot: string
  rarity: string
  rarity_label?: string
  item_kind?: string
  item_kind_label?: string
  item_level?: number
  cost: number
  stats: Record<string, number>
  resistances: Record<string, number>
  special_effects: string[]
  affixes?: Array<{
    id: string
    name: string
    stats?: Record<string, number>
    resistances?: Record<string, number>
    special_effects?: string[]
    durability_bonus?: number
  }>
  durability: number
  max_durability: number
  class_restriction: string[]
  equipped_by?: string | null
}

export interface PartyView extends PartySummary {
  inventory: EquipmentItem[]
  target_options: Record<string, string>
  retreat_options: Record<string, string>
  defense_trigger_options?: Record<string, string>
  consumable_trigger_options?: Record<string, string>
  consumable_options?: ConsumableOption[]
  max_consumable_slots?: number
  consumables?: Record<string, number>
  tactic_schemes?: TacticScheme[]
  max_tactic_schemes?: number
  max_tactic_layers?: number
}

export interface TacticScheme {
  id: string
  name: string
  created_at?: number
  updated_at?: number
  summary?: {
    characters?: number
    initiative?: number
    opening?: number
    priority?: number
    defense?: number
    layers?: number
    layer_characters?: number
  }
}

export interface DungeonCardView {
  dungeon_id: string
  name: string
  theme: string
  danger_level: number
  remaining_days: number
  reward_charges: number
  estimated_layers: number
  main_rewards: string[]
  public_threats: string[]
  affixes: Array<{ id: string; name: string; description: string; mechanics: string[] }>
  scouted: boolean
  challenged: boolean
  cleared: boolean
  recommended_attention: string[]
  is_final: boolean
  source_quest_id?: string | null
  source_quest_title?: string | null
  persistent?: boolean
}

export interface DungeonDetailView extends DungeonCardView {
  template_theme: string
  public_info: any
  scout_info?: { lines: string[]; recommended_response: string[]; enemy_formation_hint: string } | null
  post_battle_info: string[]
  known_layers: Array<{ index: number; name: string; type: string; hint: string }>
  known_enemies: string[]
  known_rewards: any
  risk_warnings: string[]
  available_actions: string[]
}

export interface PlanAction {
  id: string
  type: 'scout' | 'challenge'
  dungeon_id: string
  dungeon_name: string
  team_id?: string
  team_name?: string
  tactic_scheme_id?: string
  tactic_scheme_name?: string
}

export interface ReportView {
  id: string
  day: number
  type: string
  dungeon_id?: string | null
  dungeon_name: string
  team_id?: string
  team_name?: string
  tactic_scheme_id?: string
  tactic_scheme_name?: string
  result: string
  cleared_layers: number
  summary: string
  rewards: any
  losses: any
  layer_results: any[]
  damage_stats: Record<string, number>
  healing_stats: Record<string, number>
  mana_spent_stats?: Record<string, number>
  damage_taken_stats: Record<string, number>
  damage_by_type_stats?: Record<string, number>
  miss_stats?: Record<string, number>
  status_stats: Record<string, number>
  skill_usage_stats: Record<string, Record<string, number>>
  party_skill_usage_stats?: Record<string, Record<string, number>>
  enemy_skill_usage_stats?: Record<string, Record<string, number>>
  review_metrics?: Record<string, any>
  battle_recap?: string[]
  critical_events?: string[]
  unit_names?: Record<string, string>
  initial_party?: CombatUnitSnapshot[]
  key_events: string[]
  failure_reasons: string[]
  revealed_mechanics: string[]
  turn_logs: string[]
}

export interface CombatUnitSnapshot {
  id: string
  name: string
  side: 'party' | 'enemy'
  team_id?: string
  team_name?: string
  class_id?: string
  class_name?: string
  enemy_id?: string
  tags?: string[]
  cell?: string
  hp: number
  max_hp: number
  hp_text?: string
  mana?: number
  max_mana?: number
  attack?: number
  defense?: number
  speed?: number
  normal_speed?: number
  initiative_skill?: Record<string, any> | null
  statuses?: Array<{ type: string; duration?: number; potency?: number }>
}

export interface CombatEvent {
  seq?: number
  type: string
  text: string
  actor?: Partial<CombatUnitSnapshot>
  target?: Partial<CombatUnitSnapshot>
  redirect_to?: Partial<CombatUnitSnapshot>
  skill?: string
  amount?: number
  damage_types?: string[]
  damage_type?: string
  attack_type?: string
  status?: any
  statuses?: any[]
  target_hp_before?: number
  target_hp_after?: number
  target_statuses?: Array<{ type: string; duration?: number; potency?: number }>
  actor_statuses?: Array<{ type: string; duration?: number; potency?: number }>
  actor_mana_before?: number
  actor_mana_after?: number
}

export interface CombatRoundDetail {
  round: number
  actor_order: Array<Partial<CombatUnitSnapshot>>
  start: { party: CombatUnitSnapshot[]; enemies: CombatUnitSnapshot[] }
  end: { party: CombatUnitSnapshot[]; enemies: CombatUnitSnapshot[] }
  events: CombatEvent[]
  logs: string[]
}

/** Max number of characters a player can hold (mirrors backend MAX_ROSTER_SIZE). */
export const MAX_ROSTER_SIZE = 8

export interface ShopItemView {
  shop_id: string
  merchant_id?: string
  kind: 'equipment' | 'consumable'
  template_id: string
  name: string
  slot?: string
  rarity?: string
  base_cost?: number
  cost: number
  currency?: string
  summary: string
  equipment?: EquipmentItem
}

export interface MerchantView {
  merchant_id: string
  name: string
  icon?: string
  items: ShopItemView[]
}

export interface ShopView {
  merchants: Record<string, MerchantView>
  refresh_day: number
}

export interface RecruitCandidateView {
  candidate_id: string
  class_id: string
  class_name: string
  class_meta?: CharacterView['class_meta']
  name: string
  level: number
  rarity: string
  rarity_label: string
  cost: number
  role: string
  is_advanced?: boolean
  /** Full character snapshot shown pre-hire; hiring reproduces it exactly. */
  preview: CharacterView
}

export interface RecruitsView {
  candidates: RecruitCandidateView[]
  refresh_day: number
}
