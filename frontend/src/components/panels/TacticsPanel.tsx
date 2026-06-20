import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import type { CharacterView, ConsumableOption, ConsumableTacticEntry, PartyView } from '../../types/game'
import { CharacterAvatar } from '../CharacterAvatar'
import { Chip } from '../Chips'
import { attackTypeDescription, attackTypeLabel, classMeta } from '../../theme'

interface CharacterTacticDraft {
  target_priority: string
  initiative_skill: string
  skill_priority: string[]
  opening_skill_priority: string[]
  defense_skill_by_type: Record<string, string>
  consumable_priority: ConsumableTacticEntry[]
}

export function TacticsPanel(props: {
  party: PartyView
  busy: boolean
  onTactics: (payload: any) => void
  onSaveScheme: (payload: any) => void
  onLoadScheme: (schemeId: string) => void
  onDeleteScheme: (schemeId: string) => void
  onInspect: (ch: CharacterView) => void
}) {
  const { party } = props
  const [retreat, setRetreat] = useState(party.retreat_strategy)
  const [selectedLayer, setSelectedLayer] = useState(0)
  const [tacticsByScope, setTacticsByScope] = useState<Record<string, Record<string, CharacterTacticDraft>>>({})
  const [schemeName, setSchemeName] = useState('')
  const [selectedSchemeId, setSelectedSchemeId] = useState('')
  const schemes = party.tactic_schemes ?? []
  const maxSchemes = party.max_tactic_schemes ?? 20
  const selectedScheme = schemes.find(s => s.id === selectedSchemeId)
  const layerOptions = party.tactic_layer_options?.length ? party.tactic_layer_options : DEFAULT_TACTIC_LAYER_OPTIONS
  const scopeKey = tacticScopeKey(selectedLayer)
  const tactics = tacticsByScope[scopeKey] ?? {}
  const isLayerScope = selectedLayer > 0

  useEffect(() => {
    setRetreat(party.retreat_strategy)
    const next: Record<string, Record<string, CharacterTacticDraft>> = {
      default: Object.fromEntries(party.members.map(m => [m.id, tacticDraftFromMember(m)])),
    }
    for (const layer of (party.tactic_layer_options?.length ? party.tactic_layer_options : DEFAULT_TACTIC_LAYER_OPTIONS)) {
      next[tacticScopeKey(layer.index)] = Object.fromEntries(party.members.map(m => [m.id, tacticDraftFromMember(m, party, layer.index)]))
    }
    setTacticsByScope(next)
    setSelectedLayer(prev => prev > 0 && !layerOptions.some(l => l.index === prev) ? 0 : prev)
    setSelectedSchemeId(prev => (prev && (party.tactic_schemes ?? []).some(s => s.id === prev)) ? prev : (party.tactic_schemes?.[0]?.id ?? ''))
  }, [party])

  function patchTactic(characterId: string, patch: Partial<CharacterTacticDraft>) {
    setTacticsByScope(prev => {
      const currentScope = prev[scopeKey] ?? {}
      return {
        ...prev,
        [scopeKey]: {
          ...currentScope,
          [characterId]: { ...(currentScope[characterId] ?? emptyTacticDraft()), ...patch },
        },
      }
    })
  }

  function setTacticArray(characterId: string, key: 'skill_priority' | 'opening_skill_priority', index: number, value: string) {
    setTacticsByScope(prev => {
      const currentScope = prev[scopeKey] ?? {}
      const current = currentScope[characterId] ?? emptyTacticDraft()
      const next = [...(current[key] ?? [])]
      next[index] = value
      return {
        ...prev,
        [scopeKey]: {
          ...currentScope,
          [characterId]: {
            ...current,
            [key]: compactSkillList(next),
          },
        },
      }
    })
  }

  function setDefenseSkill(characterId: string, trigger: string, value: string) {
    setTacticsByScope(prev => {
      const currentScope = prev[scopeKey] ?? {}
      const current = currentScope[characterId] ?? emptyTacticDraft()
      const defense = { ...(current.defense_skill_by_type ?? {}) }
      if (value) defense[trigger] = value
      else delete defense[trigger]
      return {
        ...prev,
        [scopeKey]: {
          ...currentScope,
          [characterId]: { ...current, defense_skill_by_type: defense },
        },
      }
    })
  }

  function setConsumableEntry(characterId: string, index: number, field: 'consumable_id' | 'trigger', value: string) {
    setTacticsByScope(prev => {
      const currentScope = prev[scopeKey] ?? {}
      const current = currentScope[characterId] ?? emptyTacticDraft()
      const list: ConsumableTacticEntry[] = (current.consumable_priority ?? []).map(e => ({ ...e }))
      const entry = list[index] ?? { consumable_id: '', trigger: '' }
      entry[field] = value
      // Clearing the consumable id removes the whole slot.
      if (field === 'consumable_id' && !value) {
        list.splice(index, 1)
      } else {
        list[index] = entry
      }
      // De-dup by consumable_id: a given consumable can only occupy one slot.
      const seen = new Set<string>()
      const deduped = list.filter(e => {
        if (!e.consumable_id || seen.has(e.consumable_id)) return false
        seen.add(e.consumable_id)
        return true
      })
      return {
        ...prev,
        [scopeKey]: {
          ...currentScope,
          [characterId]: { ...current, consumable_priority: deduped },
        },
      }
    })
  }

  function tacticPayload(characterId?: string) {
    const members = characterId ? party.members.filter(m => m.id === characterId) : party.members
    const payload: any = {
      retreat_strategy: retreat,
      characters: members.map(m => ({
        character_id: m.id,
        ...(tactics[m.id] ?? tacticDraftFromMember(m, party, selectedLayer)),
      })),
    }
    if (isLayerScope) payload.layer_index = selectedLayer
    return payload
  }

  function saveTactics() {
    props.onTactics(tacticPayload())
  }

  function allTacticsPayload() {
    const layerTactics: Record<string, Record<string, CharacterTacticDraft>> = {}
    for (const layer of layerOptions) {
      const key = tacticScopeKey(layer.index)
      const rows = tacticsByScope[key] ?? {}
      const layerRows: Record<string, CharacterTacticDraft> = {}
      for (const m of party.members) {
        const draft = rows[m.id] ?? tacticDraftFromMember(m, party, layer.index)
        const base = tacticDraftFromMember(m)
        if (hasLayerOverride(party, layer.index, m.id) || !sameTacticDraft(draft, base)) {
          layerRows[m.id] = draft
        }
      }
      if (Object.keys(layerRows).length) layerTactics[String(layer.index)] = layerRows
    }
    const defaultScope = tacticsByScope.default ?? {}
    return {
      retreat_strategy: retreat,
      characters: party.members.map(m => ({
        character_id: m.id,
        ...(defaultScope[m.id] ?? tacticDraftFromMember(m)),
      })),
      layer_tactics: layerTactics,
    }
  }

  function saveMemberTactics(characterId: string) {
    props.onTactics(tacticPayload(characterId))
  }

  function clearLayerMemberTactics(characterId: string) {
    if (!isLayerScope) return
    props.onTactics({ layer_index: selectedLayer, characters: [{ character_id: characterId, clear_layer_tactic: true }] })
  }

  function saveScheme(overwrite = false) {
    const name = schemeName.trim() || (overwrite ? selectedScheme?.name : '') || `战术方案 ${schemes.length + 1}`
    props.onSaveScheme({
      scheme_id: overwrite ? selectedSchemeId : undefined,
      name,
      tactics: allTacticsPayload(),
    })
    setSchemeName('')
  }

  return (
    <div className="tacticsPage">
      <section className="panel tacticsHero">
        <div className="panel__head">
          <h2>🎯 战术计划</h2>
          <span className="muted">按“总方案库 → 每层 → 每个角色”配置开场、常规出手与受击响应。</span>
        </div>
        <div className="schemeBox">
          <div className="schemeBox__head">
            <b>📚 总方案库</b>
            <span className={schemes.length >= maxSchemes ? 'schemeBox__count is-full' : 'schemeBox__count'}>{schemes.length}/{maxSchemes}</span>
          </div>
          <div className="schemeBox__controls">
            <input
              value={schemeName}
              maxLength={40}
              placeholder={selectedScheme ? `新总方案名称；覆盖留空沿用「${selectedScheme.name}」` : '新总方案名称'}
              onChange={e => setSchemeName(e.target.value)}
            />
            <select value={selectedSchemeId} onChange={e => setSelectedSchemeId(e.target.value)}>
              <option value="">未选择总方案</option>
              {schemes.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <button className="btn btn--accent btn--sm" disabled={props.busy || schemes.length >= maxSchemes} onClick={() => saveScheme(false)}>另存总方案</button>
            <button className="btn btn--ghost btn--sm" disabled={props.busy || !selectedSchemeId} onClick={() => saveScheme(true)}>覆盖总方案</button>
            <button className="btn btn--ghost btn--sm" disabled={props.busy || !selectedSchemeId} onClick={() => props.onLoadScheme(selectedSchemeId)}>读取总方案</button>
            <button className="btn btn--danger btn--sm" disabled={props.busy || !selectedSchemeId} onClick={() => props.onDeleteScheme(selectedSchemeId)}>删除</button>
          </div>
          <p className="schemeBox__hint">
            {selectedScheme
              ? `${schemeSummaryText(selectedScheme)} · 更新 ${formatSchemeTime(selectedScheme.updated_at)}。读取后再编辑“每层 / 每个角色”，出征时可绑定该总方案。`
              : schemes.length >= maxSchemes ? '总方案槽已满，请删除旧方案或覆盖已有总方案。' : '总方案保存默认战术、每层覆盖和每个角色配置；出征时从副本页选择要使用的总方案。'}
          </p>
        </div>
        <div className="tacticsToolbar">
          <label className="fieldRow tacticsToolbar__retreat">
            <span className="fieldRow__label">撤退策略</span>
            <select value={retreat} onChange={e => setRetreat(e.target.value)}>
              {Object.entries(party.retreat_options).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <label className="fieldRow tacticsToolbar__layer">
            <span className="fieldRow__label">每层</span>
            <select value={selectedLayer} onChange={e => setSelectedLayer(Number(e.target.value))}>
              <option value={0}>默认战术</option>
              {layerOptions.map(l => <option key={l.index} value={l.index}>{l.label}</option>)}
            </select>
          </label>
          <button className="btn btn--primary" onClick={saveTactics} disabled={props.busy}>
            💾 保存{isLayerScope ? `第 ${selectedLayer} 层` : '默认'}全部战术
          </button>
        </div>
        <div className="layerTacticBox">
          <b>{isLayerScope ? `当前编辑：第 ${selectedLayer} 层战术` : '当前编辑：默认战术'}</b>
          <span>
            {isLayerScope
              ? '本层保存后只在讨伐进入该层时覆盖对应角色战术；未保存的角色继续继承默认战术。'
              : '默认战术会作为所有层的基础配置；分层战术未保存时会继承这里。'}
          </span>
        </div>
        <div className="tacticsHelp">
          <Chip icon="⚡" tone="accent">先攻：可选一个带先攻标签的技能改写速度公式</Chip>
          <Chip icon="🚀" tone="info">开场技能：每层战斗开场按速度尝试释放</Chip>
          <Chip icon="🏰" tone="accent">分层战术：每层可覆盖每个角色的目标、技能与防御</Chip>
          <Chip icon="🛡️" tone="info">防御响应：被对应攻击方式命中前触发</Chip>
          <Chip icon="📋" tone="muted">技能优先级：覆盖默认职业 AI，无法使用时回落</Chip>
        </div>
      </section>

      <div className="tacticsGrid">
        {party.members.map(m => (
          <TacticsCard
            key={m.id}
            member={m}
            draft={tactics[m.id] ?? tacticDraftFromMember(m, party, selectedLayer)}
            savedDraft={savedTacticDraftForMember(m, party, selectedLayer)}
            layerIndex={selectedLayer}
            hasLayerOverride={hasLayerOverride(party, selectedLayer, m.id)}
            targetOptions={party.target_options}
            defenseOptions={party.defense_trigger_options ?? DEFAULT_DEFENSE_TRIGGER_OPTIONS}
            consumableOptions={party.consumable_options ?? []}
            consumableTriggers={party.consumable_trigger_options ?? {}}
            consumables={party.consumables ?? {}}
            maxConsumableSlots={party.max_consumable_slots ?? 4}
            onPatch={patch => patchTactic(m.id, patch)}
            onPriority={(index, value) => setTacticArray(m.id, 'skill_priority', index, value)}
            onOpening={(index, value) => setTacticArray(m.id, 'opening_skill_priority', index, value)}
            onDefense={(trigger, value) => setDefenseSkill(m.id, trigger, value)}
            onConsumable={(index, field, value) => setConsumableEntry(m.id, index, field, value)}
            onSave={() => saveMemberTactics(m.id)}
            onClearLayer={() => clearLayerMemberTactics(m.id)}
            onInspect={() => props.onInspect(m)}
          />
        ))}
      </div>
    </div>
  )
}

const DEFAULT_DEFENSE_TRIGGER_OPTIONS: Record<string, string> = {
  melee: '近战攻击',
  ranged: '远程攻击',
  magic: '魔法攻击',
  mental: '精神攻击',
  special: '特殊攻击',
}

const DEFAULT_TACTIC_LAYER_OPTIONS = [1, 2, 3, 4, 5].map(index => ({ index, label: `第 ${index} 层` }))

const DEFENSE_TRIGGER_DESCRIPTIONS: Record<string, string> = {
  melee: '近战攻击：剑、斧、爪击、撕咬、撞击等贴身攻击。只有 defense_types 包含 melee 的技能能响应该项。',
  ranged: '远程攻击：弓箭、投射物、远距离点射等攻击方式。只有 defense_types 包含 ranged 的技能能响应该项。',
  magic: '魔法攻击：奥术、火焰、闪电等法术攻击方式。它和火/毒/物理等伤害抗性不是同一层概念。',
  mental: '精神攻击：诅咒、恐惧、挑衅、精神压制等心智/意志攻击方式。',
  special: '特殊攻击：毒雾、影袭、扑杀、地裂等不适合归入近战/远程/魔法/精神的攻击方式。',
}

function emptyTacticDraft(): CharacterTacticDraft {
  return {
    target_priority: 'front',
    initiative_skill: '',
    skill_priority: [],
    opening_skill_priority: [],
    defense_skill_by_type: {},
    consumable_priority: [],
  }
}

function tacticDraftFromTactics(tactics: CharacterView['tactics'] | undefined): CharacterTacticDraft {
  return {
    target_priority: tactics?.target_priority || 'front',
    initiative_skill: tactics?.initiative_skill || '',
    skill_priority: compactSkillList(tactics?.skill_priority ?? []),
    opening_skill_priority: compactSkillList(tactics?.opening_skill_priority ?? []),
    defense_skill_by_type: { ...(tactics?.defense_skill_by_type ?? {}) },
    consumable_priority: (tactics?.consumable_priority ?? []).map(e => ({ consumable_id: e.consumable_id, trigger: e.trigger })),
  }
}

function tacticScopeKey(layerIndex: number): string {
  return layerIndex > 0 ? String(layerIndex) : 'default'
}

function layerTacticForMember(party: PartyView, layerIndex: number, characterId: string): CharacterView['tactics'] | undefined {
  if (layerIndex <= 0) return undefined
  return party.layer_tactics?.[String(layerIndex)]?.[characterId]
}

function tacticDraftFromMember(m: CharacterView, party?: PartyView, layerIndex = 0): CharacterTacticDraft {
  const layerTactic = party ? layerTacticForMember(party, layerIndex, m.id) : undefined
  return tacticDraftFromTactics(layerTactic ?? m.tactics)
}

function savedTacticDraftForMember(m: CharacterView, party: PartyView, layerIndex: number): CharacterTacticDraft {
  return tacticDraftFromMember(m, party, layerIndex)
}

function hasLayerOverride(party: PartyView, layerIndex: number, characterId: string): boolean {
  return layerIndex > 0 && !!party.layer_tactics?.[String(layerIndex)]?.[characterId]
}

function compactSkillList(values: string[]): string[] {
  const out: string[] = []
  for (const v of values) {
    if (v && !out.includes(v)) out.push(v)
  }
  return out
}

function schemeSummaryText(s: { summary?: Record<string, number> }): string {
  const m = s.summary ?? {}
  const bits = [
    `${m.characters ?? 0}人`,
    `${m.layers ?? 0}层`,
    `${m.layer_characters ?? 0}层角色`,
    `${m.initiative ?? 0}先攻`,
    `${m.opening ?? 0}开场`,
    `${m.priority ?? 0}优先级`,
    `${m.defense ?? 0}防御响应`,
    `${m.consumables ?? 0}消耗品`,
  ]
  return bits.join(' · ')
}

function formatSchemeTime(value?: number): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function sameTacticDraft(a: CharacterTacticDraft, b: CharacterTacticDraft): boolean {
  return JSON.stringify(normalizeDraftForCompare(a)) === JSON.stringify(normalizeDraftForCompare(b))
}

function normalizeDraftForCompare(d: CharacterTacticDraft): CharacterTacticDraft {
  return {
    target_priority: d.target_priority || 'front',
    initiative_skill: d.initiative_skill || '',
    skill_priority: compactSkillList(d.skill_priority ?? []),
    opening_skill_priority: compactSkillList(d.opening_skill_priority ?? []),
    defense_skill_by_type: Object.fromEntries(Object.entries(d.defense_skill_by_type ?? {}).filter(([, v]) => !!v).sort(([a], [b]) => a.localeCompare(b))),
    consumable_priority: (d.consumable_priority ?? []).filter(e => e.consumable_id && e.trigger).map(e => ({ consumable_id: e.consumable_id, trigger: e.trigger })),
  }
}

function TacticsCard(props: {
  member: CharacterView
  draft: CharacterTacticDraft
  savedDraft: CharacterTacticDraft
  layerIndex: number
  hasLayerOverride: boolean
  targetOptions: Record<string, string>
  defenseOptions: Record<string, string>
  consumableOptions: ConsumableOption[]
  consumableTriggers: Record<string, string>
  consumables: Record<string, number>
  maxConsumableSlots: number
  onPatch: (patch: Partial<CharacterTacticDraft>) => void
  onPriority: (index: number, value: string) => void
  onOpening: (index: number, value: string) => void
  onDefense: (trigger: string, value: string) => void
  onConsumable: (index: number, field: 'consumable_id' | 'trigger', value: string) => void
  onSave: () => void
  onClearLayer: () => void
  onInspect: () => void
}) {
  const m = props.member
  const cm = classMeta(m.class_id)
  const skills = (m.skill_summary ?? []).filter(s => s.learned !== false && s.id !== 'basic_attack' && !isPassiveOrInitiativeSkill(s))
  const initiativeSkills = (m.skill_summary ?? []).filter(s => s.learned !== false && isInitiativeSkill(s))
  const defenseSkills = skills.filter(s => ['guard', 'buff', 'support'].includes(s.type) && (s.defense_types?.length ?? 0) > 0)
  const defenseSkillsFor = (trigger: string) => defenseSkills.filter(s => (s.defense_types ?? []).includes(trigger))
  const initiative = m.effective_stats?.initiative_skill
  const selectedInitiative = props.draft.initiative_skill ?? ''
  const savedInitiative = props.savedDraft.initiative_skill ?? ''
  const selectedInitiativeSkill = initiativeSkills.find(s => s.id === selectedInitiative)
  const dirty = !sameTacticDraft(props.draft, props.savedDraft)
  return (
    <div className="tacticCard" style={{ '--accent': cm.accent } as CSSProperties}>
      <div className="tacticCard__head">
        <span className="tacticCard__identity">
          <CharacterAvatar ch={m} size={32} />
          <span><b>{m.name}</b><em>{m.class_name}{m.team_name ? ` · ${m.team_name}` : ''}</em></span>
        </span>
        <span className="tacticCard__actions">
          {props.layerIndex > 0 && <em className={props.hasLayerOverride ? 'tacticScopeBadge is-layer' : 'tacticScopeBadge'}>{props.hasLayerOverride ? `第${props.layerIndex}层已保存` : '继承默认'}</em>}
          <button className="btn btn--ghost btn--sm" title={props.layerIndex > 0 ? `只保存 ${m.name} 的第 ${props.layerIndex} 层战术` : `只保存 ${m.name} 的默认战术`} onClick={props.onSave}>保存本角色</button>
          {props.layerIndex > 0 && props.hasLayerOverride && <button className="btn btn--ghost btn--sm" title="清除本角色本层覆盖，恢复继承默认战术" onClick={props.onClearLayer}>继承默认</button>}
          <button className="iconBtn" title="查看详情" onClick={props.onInspect}>📋</button>
        </span>
      </div>
      {dirty && <p className="tacticHint tacticHint--pending">本角色有未保存修改。</p>}
      <div className="tacticCard__row">
        <label>目标</label>
        <select value={props.draft.target_priority} onChange={e => props.onPatch({ target_priority: e.target.value })}>
          {Object.entries(props.targetOptions).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      <div className="tacticBlock tacticBlock--initiative">
        <b>⚡ 先攻技能（速度公式）</b>
        <div className="initiativePicker">
          <select value={selectedInitiative} onChange={e => props.onPatch({ initiative_skill: e.target.value })}>
            <option value="">默认速度公式</option>
            {initiativeSkills.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <p className="tacticHint">
            {initiativeSkills.length > 0
              ? '不选时使用默认常规速度公式；选择后保存才会改写战斗排序用的速度值。'
              : '当前没有已学会的先攻技能，速度使用默认常规公式。'}
          </p>
        </div>
        {initiative ? (
          <div className="initiativeFormula" title={String(initiative.formula ?? '')}>
            <span>{initiative.skill_name ?? '默认速度公式'}</span>
            <strong>速度 {m.effective_stats?.speed ?? 0}</strong>
            <em>常规 {initiative.normal_speed ?? m.effective_stats?.normal_speed ?? m.effective_stats?.speed ?? 0} · {initiative.label ?? '速度公式'}{initiative.is_default ? ' · 未选择先攻技能' : ''}</em>
          </div>
        ) : (
          <p className="tacticHint">未选择先攻技能，速度使用默认常规公式。</p>
        )}
        {selectedInitiative !== savedInitiative && (
          <p className="tacticHint tacticHint--pending">
            待保存：{selectedInitiativeSkill ? `改用「${selectedInitiativeSkill.name}」` : '改用默认速度公式'}。
          </p>
        )}
        {initiativeSkills.length > 0 && (
          <div className="initiativeSkillList">
            {initiativeSkills.map(s => <span key={s.id} title={speedFormulaText(s)}>{s.name}</span>)}
          </div>
        )}
      </div>

      <div className="tacticBlock">
        <b>🚀 开场技能</b>
        <p className="tacticHint">这里是战斗开场主动释放的技能，不是速度公式型先攻技能。</p>
        <div className="tacticSelectGrid tacticSelectGrid--two">
          {[0, 1].map(i => (
            <select key={i} value={props.draft.opening_skill_priority[i] ?? ''} onChange={e => props.onOpening(i, e.target.value)}>
              <option value="">无</option>
              {skills.map(s => <option key={s.id} value={s.id}>{skillOptionLabel(s)}</option>)}
            </select>
          ))}
        </div>
      </div>

      <div className="tacticBlock">
        <b>📋 技能优先级</b>
        <div className="tacticSelectGrid">
          {[0, 1, 2, 3].map(i => (
            <select key={i} value={props.draft.skill_priority[i] ?? ''} onChange={e => props.onPriority(i, e.target.value)}>
              <option value="">优先级 {i + 1}：默认 AI</option>
              {skills.map(s => <option key={s.id} value={s.id}>{skillOptionLabel(s)}</option>)}
            </select>
          ))}
        </div>
      </div>

      <div className="tacticBlock">
        <b>🛡️ 防御响应</b>
        {defenseSkills.length === 0 && <p className="tacticHint">当前等级没有可用的防御响应技能；学习护盾、保护、支援类技能后会出现在这里。</p>}
        <div className="defenseGrid">
          {Object.entries(props.defenseOptions).map(([trigger, label]) => {
            const options = defenseSkillsFor(trigger)
            const selected = props.draft.defense_skill_by_type[trigger] ?? ''
            const value = options.some(s => s.id === selected) ? selected : ''
            return (
              <label key={trigger} className="defenseSelect">
                <span title={DEFENSE_TRIGGER_DESCRIPTIONS[trigger] ?? label}>{label}</span>
                <select value={value} onChange={e => props.onDefense(trigger, e.target.value)} title={defenseSelectTitle(trigger, options.length)}>
                  <option value="">{options.length ? '不响应' : '无可用技能'}</option>
                  {options.map(s => <option key={s.id} value={s.id}>{skillOptionLabel(s)}</option>)}
                </select>
              </label>
            )
          })}
        </div>
      </div>

      <div className="tacticBlock">
        <b>🧪 消耗品</b>
        <p className="tacticHint">满足条件时自动使用一瓶（全队共享库存）。库存可在炼金铺补充。</p>
        <div className="defenseGrid">
          {Array.from({ length: props.maxConsumableSlots }).map((_, i) => {
            const entry = props.draft.consumable_priority[i]
            const cid = entry?.consumable_id ?? ''
            const trigger = entry?.trigger ?? ''
            return (
              <div key={i} className="defenseSelect defenseSelect--consumable">
                <select value={cid} onChange={e => props.onConsumable(i, 'consumable_id', e.target.value)}>
                  <option value="">槽 {i + 1}：不使用</option>
                  {props.consumableOptions.map(o => (
                    <option key={o.id} value={o.id}>{o.name}（库存 {props.consumables[o.id] ?? 0}）</option>
                  ))}
                </select>
                <select value={trigger} onChange={e => props.onConsumable(i, 'trigger', e.target.value)} disabled={!cid}>
                  <option value="">选择触发条件</option>
                  {Object.entries(props.consumableTriggers).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function skillOptionLabel(s: { name: string; type: string; mana_cost?: number; uses_per_dungeon?: number; attack_type?: string; defense_types?: string[] }): string {
  const bits = [s.name]
  if (s.attack_type) bits.push(`攻:${attackTypeLabel(s.attack_type)}`)
  if (s.defense_types?.length) bits.push(`防:${s.defense_types.map(attackTypeLabel).join('/')}`)
  if (s.mana_cost) bits.push(`法力${s.mana_cost}`)
  if (s.uses_per_dungeon && s.uses_per_dungeon !== 999) bits.push(`${s.uses_per_dungeon}次`)
  return bits.join(' · ')
}

function defenseSelectTitle(trigger: string, optionCount: number): string {
  return `${attackTypeDescription(trigger)}\n当前有 ${optionCount} 个已学会技能可响应该攻击方式。`
}

function isInitiativeSkill(s: { tags?: string[]; speed_formula?: Record<string, any> | null; is_initiative_skill?: boolean }): boolean {
  return !!s.is_initiative_skill || !!s.speed_formula || (s.tags ?? []).some(t => t === 'initiative' || t === '先攻')
}

function isPassiveOrInitiativeSkill(s: { type: string; tags?: string[]; speed_formula?: Record<string, any> | null; is_initiative_skill?: boolean }): boolean {
  return s.type === 'passive' || isInitiativeSkill(s)
}

function speedFormulaText(s: { speed_formula?: Record<string, any> | null }): string {
  const f = s.speed_formula
  if (!f) return '在战术页选用后改写速度公式。'
  const parts: string[] = []
  if (f.normal_speed_weight || f.speed_weight) parts.push(`常规速度×${f.normal_speed_weight ?? f.speed_weight}`)
  const attrs = f.attribute_weights ?? f.attributes ?? {}
  const labels: Record<string, string> = { strength: '力量', constitution: '体质', dexterity: '灵巧', agility: '敏捷', intelligence: '智力', willpower: '意志', perception: '感知', charisma: '魅力' }
  for (const [key, value] of Object.entries(attrs)) parts.push(`${labels[key] ?? key}×${value}`)
  if (f.level_weight) parts.push(`等级×${f.level_weight}`)
  if (f.flat || f.base) parts.push(String(f.flat ?? f.base))
  return `${f.label ?? '先攻公式'}：${parts.join(' + ') || '常规速度'}`
}
