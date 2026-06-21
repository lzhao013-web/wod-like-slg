import type { DungeonCardView, DungeonDetailView, GamePresetView, GameStateView, PartyView, PlanAction, QuestListView, RecruitsView, ReportView, ShopView } from '../types/game'

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      message = body.detail || message
    } catch {}
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export const api = {
  state: () => request<GameStateView>('/game/state'),
  preset: () => request<GamePresetView>('/game/preset'),
  presets: () => request<{ active_preset_id: string; presets: Array<{ id: string; name: string; description?: string; path?: string; active?: boolean }> }>('/game/presets'),
  newGame: (seed?: number) => request<GameStateView>('/game/new', { method: 'POST', body: JSON.stringify({ seed }) }),
  endDay: () => request<{ reports: ReportView[]; state: GameStateView }>('/game/end-day', { method: 'POST' }),
  dungeons: () => request<DungeonCardView[]>('/dungeons'),
  dungeon: (id: string) => request<DungeonDetailView>(`/dungeons/${id}`),
  planScout: (id: string, team_id?: string) => request<PlanAction>(`/dungeons/${id}/scout`, { method: 'POST', body: JSON.stringify({ team_id }) }),
  planChallenge: (id: string, tactic_scheme_id?: string, team_id?: string) => request<PlanAction>(`/dungeons/${id}/challenge`, { method: 'POST', body: JSON.stringify({ team_id, tactic_scheme_id }) }),
  plan: () => request<{ actions: PlanAction[]; expedition_points_left: number }>('/expedition-plan'),
  clearPlan: () => request<{ ok: boolean; plan: PlanAction[] }>('/expedition-plan/clear', { method: 'POST' }),
  removePlan: (index: number) => request<{ actions: PlanAction[]; expedition_points_left: number }>(`/expedition-plan/${index}`, { method: 'DELETE' }),
  party: () => request<PartyView>('/party'),
  formation: (formation: Record<string, string | null>, team_id = 'team_1') => request<PartyView>('/party/formation', { method: 'POST', body: JSON.stringify({ team_id, formation }) }),
  formations: (formations: Record<string, Record<string, string | null>>) => request<PartyView>('/party/formations', { method: 'POST', body: JSON.stringify({ formations }) }),
  tactics: (payload: any) => request<PartyView>('/party/tactics', { method: 'POST', body: JSON.stringify(payload) }),
  learnSkill: (character_id: string, skill_id: string) => request<PartyView>('/party/skills/learn', { method: 'POST', body: JSON.stringify({ character_id, skill_id }) }),
  upgradeSkill: (character_id: string, skill_id: string, choice_id?: string) => request<PartyView>('/party/skills/upgrade', { method: 'POST', body: JSON.stringify({ character_id, skill_id, choice_id }) }),
  promoteCharacter: (character_id: string, target_class_id: string) => request<PartyView>('/party/promote', { method: 'POST', body: JSON.stringify({ character_id, target_class_id }) }),
  allocateAttributes: (character_id: string, allocations: Record<string, number>) => request<PartyView>('/party/attributes/allocate', { method: 'POST', body: JSON.stringify({ character_id, allocations }) }),
  resetAttributes: (character_id: string) => request<PartyView>('/party/attributes/reset', { method: 'POST', body: JSON.stringify({ character_id }) }),
  saveTacticScheme: (payload: any) => request<PartyView>('/party/tactic-schemes', { method: 'POST', body: JSON.stringify(payload) }),
  loadTacticScheme: (id: string) => request<PartyView>(`/party/tactic-schemes/${id}/load`, { method: 'POST' }),
  deleteTacticScheme: (id: string) => request<PartyView>(`/party/tactic-schemes/${id}`, { method: 'DELETE' }),
  equip: (character_id: string, equipment_instance_id: string | null, slot?: string) => request<PartyView>('/party/equipment', { method: 'POST', body: JSON.stringify({ character_id, equipment_instance_id, slot }) }),
  reports: () => request<ReportView[]>('/reports'),
  report: (id: string) => request<ReportView>(`/reports/${id}`),
  shop: () => request<ShopView>('/shop'),
  buy: (shop_id: string) => request<{ ok: boolean; acquired: any; state: GameStateView; shop: ShopView; party: PartyView }>('/shop/buy', { method: 'POST', body: JSON.stringify({ shop_id }) }),
  sell: (item_id: string) => request<{ ok: boolean; result: any; state: GameStateView; party: PartyView }>('/shop/sell', { method: 'POST', body: JSON.stringify({ item_id }) }),
  salvage: (item_id: string) => request<{ ok: boolean; result: any; state: GameStateView; party: PartyView }>('/shop/salvage', { method: 'POST', body: JSON.stringify({ item_id }) }),
  enchantEquipment: (item_id: string) => request<{ ok: boolean; result: any; state: GameStateView; party: PartyView }>('/party/equipment/enchant', { method: 'POST', body: JSON.stringify({ item_id }) }),
  rerollEnchant: (item_id: string, enchant_index: number) => request<{ ok: boolean; result: any; state: GameStateView; party: PartyView }>('/party/equipment/reroll', { method: 'POST', body: JSON.stringify({ item_id, enchant_index }) }),
  ascendEquipment: (item_id: string) => request<{ ok: boolean; result: any; state: GameStateView; party: PartyView }>('/party/equipment/ascend', { method: 'POST', body: JSON.stringify({ item_id }) }),
  ascensionRecipes: () => request<{ recipes: Array<{ source: string; target: string; target_name: string; materials: Record<string, number>; description: string; preview: any }> }>('/equipment/ascension-recipes'),
  recruits: () => request<RecruitsView>('/recruits'),
  recruit: (candidate_id: string) => request<{ ok: boolean; character: any; state: GameStateView; party: PartyView; recruits: RecruitsView }>('/recruits/recruit', { method: 'POST', body: JSON.stringify({ candidate_id }) }),
  dismiss: (character_id: string) => request<{ ok: boolean; result: any; state: GameStateView; party: PartyView }>('/recruits/dismiss', { method: 'POST', body: JSON.stringify({ character_id }) }),
  quests: () => request<QuestListView>('/quests'),
  acceptQuest: (quest_id: string) => request<{ ok: boolean; quests: QuestListView; state: GameStateView }>(`/quests/${quest_id}/accept`, { method: 'POST' }),
  claimQuest: (quest_id: string) => request<{ ok: boolean; quest: any; quests: QuestListView; state: GameStateView }>(`/quests/${quest_id}/claim`, { method: 'POST' }),
  abandonQuest: (quest_id: string) => request<{ ok: boolean; quests: QuestListView; state: GameStateView }>(`/quests/${quest_id}/abandon`, { method: 'POST' }),
  debugState: () => request<any>('/debug/state'),
  reset: () => request<GameStateView>('/debug/reset-save', { method: 'POST' })
}
