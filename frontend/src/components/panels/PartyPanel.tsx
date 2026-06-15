import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import type { CharacterView, PartyView } from '../../types/game'
import { CharacterAvatar } from '../CharacterAvatar'
import { Bar } from '../Bar'
import { Chip, StatusChip } from '../Chips'
import { EquipmentCard } from '../EquipmentCard'
import { ATTRIBUTES, classMeta, compatibleEquipmentSlots, EQUIPMENT_SLOT_ORDER, itemFitsEquipmentSlot, STATS, SLOT_ICON, SLOT_LABEL } from '../../theme'
import { CELL_LABEL, FRONT_CELLS, MID_CELLS, BACK_CELLS } from '../../state/useGame'
import { cx } from '../../lib/format'

export function PartyPanel(props: {
  party: PartyView
  busy: boolean
  onFormation: (teamId: string, formation: Record<string, string | null>) => void
  onFormations: (formations: Record<string, Record<string, string | null>>) => void
  onEquip: (charId: string, itemId: string | null, slot?: string) => void
  onInspect: (ch: CharacterView) => void
}) {
  const { party } = props
  const teamLabels = party.team_labels ?? { team_1: '一队', team_2: '二队' }
  const teamIds = Object.keys(teamLabels)
  const formations = party.formations ?? { team_1: party.formation ?? {} }
  const [activeTeam, setActiveTeam] = useState<string>(teamIds[0] ?? 'team_1')
  const [drafts, setDrafts] = useState<Record<string, Record<string, string | null>>>(() => normalizeDrafts(teamIds, formations))
  const [selected, setSelected] = useState<string>('')
  const [editingEquipFor, setEditingEquipFor] = useState<string>('')

  useEffect(() => {
    if (!teamIds.includes(activeTeam)) setActiveTeam(teamIds[0] ?? 'team_1')
    setDrafts(normalizeDrafts(teamIds, formations))
  }, [party])

  const memberById: Record<string, CharacterView> = {}
  for (const m of party.members) memberById[m.id] = m
  const draft = drafts[activeTeam] ?? {}
  const formationIds = new Set(Object.values(draft).filter(Boolean))
  const otherTeamIds = new Set(Object.entries(drafts).filter(([tid]) => tid !== activeTeam).flatMap(([, f]) => Object.values(f ?? {})))
  const dirty = JSON.stringify(draft) !== JSON.stringify({ ...(formations[activeTeam] ?? {}) })
  const dirtyAll = JSON.stringify(drafts) !== JSON.stringify(normalizeDrafts(teamIds, formations))
  const inFormation = party.members.filter(m => formationIds.has(m.id))
  const reserves = party.members.filter(m => !formationIds.has(m.id) && !otherTeamIds.has(m.id))
  const otherTeamMembers = party.members.filter(m => otherTeamIds.has(m.id))

  function place(cell: string) {
    if (!selected) return
    setDrafts(prev => {
      const next = normalizeDrafts(teamIds, prev)
      for (const team of teamIds) {
        for (const c of Object.keys(next[team] ?? {})) if (next[team][c] === selected) delete next[team][c]
      }
      next[activeTeam] = { ...(next[activeTeam] ?? {}), [cell]: selected }
      return next
    })
  }
  function clearCell(cell: string) {
    setDrafts(prev => {
      const next = normalizeDrafts(teamIds, prev)
      next[activeTeam] = { ...(next[activeTeam] ?? {}) }
      delete next[activeTeam][cell]
      return next
    })
  }
  function setActiveDraft(nextFormation: Record<string, string | null>) {
    setDrafts(prev => ({ ...normalizeDrafts(teamIds, prev), [activeTeam]: compactFormation(nextFormation) }))
  }
  function autoFillActiveTeam() {
    const taken = assignedMemberIds(drafts, activeTeam)
    let next = { ...draft }
    const candidates = party.members
      .filter(m => m.available && !taken.has(m.id) && !Object.values(next).includes(m.id))
      .sort(memberSort)
    for (const m of candidates) {
      if (Object.values(next).filter(Boolean).length >= (party.max_team_size ?? 4)) break
      next = placeMemberInBestCell(next, m)
    }
    setActiveDraft(next)
  }
  function clearActiveTeam() {
    setSelected('')
    setActiveDraft({})
  }
  function balanceTeams() {
    const max = party.max_team_size ?? 4
    const next = Object.fromEntries(teamIds.map(tid => [tid, {} as Record<string, string | null>]))
    const candidates = party.members.filter(m => m.available).sort(memberSort).slice(0, max * teamIds.length)
    for (const m of candidates) {
      const targetTeam = [...teamIds].sort((a, b) => Object.keys(next[a]).length - Object.keys(next[b]).length)[0]
      if (!targetTeam || Object.values(next[targetTeam]).filter(Boolean).length >= max) continue
      next[targetTeam] = placeMemberInBestCell(next[targetTeam], m)
    }
    setSelected('')
    setDrafts(next)
  }

  return (
    <div className="partyLayout">
      <section className="panel formationPanel">
        <div className="panel__head">
          <h2>🛡️ 双队编成 · 3×3</h2>
          <span className="muted">{teamLabels[activeTeam] ?? activeTeam} 上阵 {inFormation.length} / {party.max_team_size ?? 4} · 队员不能重复</span>
        </div>

        <div className="teamTabs">
          {teamIds.map(tid => {
            const count = Object.values(drafts[tid] ?? {}).filter(Boolean).length
            return (
              <button key={tid} className={cx('teamTab', activeTeam === tid && 'is-active')} onClick={() => { setActiveTeam(tid); setSelected('') }}>
                <b>{teamLabels[tid] ?? tid}</b><span>{count}/{party.max_team_size ?? 4}</span>
              </button>
            )
          })}
        </div>

        <div className="formRows">
          <FormationRow label="前排" cells={Array.from(FRONT_CELLS)} draft={draft} memberById={memberById} selected={selected} onPlace={place} onClear={clearCell} />
          <FormationRow label="中排" cells={Array.from(MID_CELLS)} draft={draft} memberById={memberById} selected={selected} onPlace={place} onClear={clearCell} />
          <FormationRow label="后排" cells={Array.from(BACK_CELLS)} draft={draft} memberById={memberById} selected={selected} onPlace={place} onClear={clearCell} />
        </div>

        <div className="formationActions">
          <button className="btn btn--primary btn--sm" onClick={() => props.onFormation(activeTeam, draft)} disabled={props.busy || !dirty}>
            {dirty ? `💾 保存${teamLabels[activeTeam] ?? ''}阵型` : '✓ 已保存'}
          </button>
          <button className="btn btn--ghost btn--sm" onClick={() => props.onFormations(drafts)} disabled={props.busy || !dirtyAll}>💾 保存全部</button>
          <button className="btn btn--ghost btn--sm" onClick={autoFillActiveTeam} disabled={props.busy}>⚡ 补满当前队</button>
          <button className="btn btn--ghost btn--sm" onClick={balanceTeams} disabled={props.busy}>⚖️ 平均分配</button>
          <button className="btn btn--ghost btn--sm" onClick={clearActiveTeam} disabled={props.busy || inFormation.length === 0}>🧹 清空当前队</button>
          {dirtyAll && <span className="muted">有未保存的编组改动</span>}
          {selected && <Chip icon="👆" tone="accent">选中：{memberById[selected]?.name} · 点击格子放置</Chip>}
        </div>

        <h3 className="sub">💺 预备队</h3>
        <div className="reserveRow">
          {reserves.length === 0 && <span className="muted">全员已上阵。</span>}
          {reserves.map(m => (
            <MemberChip key={m.id} m={m} selected={selected === m.id} onSelect={() => setSelected(selected === m.id ? '' : m.id)} onInspect={() => props.onInspect(m)} />
          ))}
        </div>
        {otherTeamMembers.length > 0 && (
          <>
            <h3 className="sub">🚫 已编入其他队伍</h3>
            <div className="reserveRow reserveRow--locked">
              {otherTeamMembers.map(m => <MemberChip key={m.id} m={m} locked selected={false} onSelect={() => {}} onInspect={() => props.onInspect(m)} />)}
            </div>
          </>
        )}
      </section>

      <section className="panel rosterPanel">
        <div className="panel__head">
          <h2>👥 {teamLabels[activeTeam] ?? '队伍'}成员</h2>
          <span className="muted">{inFormation.length} 人 · 卡片已显示八维/技能构筑</span>
        </div>
        <div className="rosterGrid">
          {inFormation.map(m => (
            <RosterCard key={m.id} m={m} inFormation selected={selected === m.id} onSelect={() => setSelected(selected === m.id ? '' : m.id)} onInspect={() => props.onInspect(m)} />
          ))}
        </div>
      </section>

      <section className="panel equipPanel">
        <div className="panel__head"><h2>⚒️ 配装</h2><span className="muted">选择角色后更换装备</span></div>
        <div className="equipRoster">
          {party.members.map(m => (
            <button key={m.id} className={cx('equipRoster__btn', editingEquipFor === m.id && 'is-active')} onClick={() => setEditingEquipFor(editingEquipFor === m.id ? '' : m.id)}>
              <CharacterAvatar ch={m} size={32} /> <span>{m.name}</span>
            </button>
          ))}
        </div>
        {editingEquipFor ? (
          <EquipEditor member={memberById[editingEquipFor]} party={party} onEquip={props.onEquip} busy={props.busy} />
        ) : (
          <p className="muted equipEmpty">点击上方角色以更换其武器 / 护甲 / 饰品。</p>
        )}
      </section>
    </div>
  )
}

function normalizeDrafts(teamIds: string[], formations: Record<string, Record<string, string | null>>): Record<string, Record<string, string | null>> {
  return Object.fromEntries(teamIds.map(tid => [tid, compactFormation(formations?.[tid] ?? {})]))
}

function compactFormation(formation: Record<string, string | null>): Record<string, string | null> {
  const out: Record<string, string | null> = {}
  for (const [cell, id] of Object.entries(formation ?? {})) {
    if (id) out[cell] = id
  }
  return out
}

function assignedMemberIds(drafts: Record<string, Record<string, string | null>>, exceptTeam?: string): Set<string> {
  const ids = new Set<string>()
  for (const [tid, formation] of Object.entries(drafts)) {
    if (tid === exceptTeam) continue
    for (const id of Object.values(formation ?? {})) if (id) ids.add(id)
  }
  return ids
}

function memberSort(a: CharacterView, b: CharacterView): number {
  const posScore: Record<string, number> = { front: 0, mid: 1, flex: 2, back: 3 }
  const pa = posScore[classMeta(a.class_id).position] ?? 2
  const pb = posScore[classMeta(b.class_id).position] ?? 2
  return pa - pb || b.level - a.level || (b.hp / Math.max(1, b.max_hp)) - (a.hp / Math.max(1, a.max_hp))
}

function preferredCells(ch: CharacterView): string[] {
  const pos = classMeta(ch.class_id).position
  if (pos === 'front') return ['r0c1', 'r0c0', 'r0c2', 'r1c1', 'r1c0', 'r1c2', 'r2c1', 'r2c0', 'r2c2']
  if (pos === 'mid' || pos === 'flex') return ['r1c1', 'r1c0', 'r1c2', 'r0c1', 'r2c1', 'r0c0', 'r0c2', 'r2c0', 'r2c2']
  return ['r2c1', 'r2c0', 'r2c2', 'r1c1', 'r1c0', 'r1c2', 'r0c1', 'r0c0', 'r0c2']
}

function placeMemberInBestCell(formation: Record<string, string | null>, ch: CharacterView): Record<string, string | null> {
  const next = compactFormation(formation)
  for (const cell of preferredCells(ch)) {
    if (!next[cell]) {
      next[cell] = ch.id
      return next
    }
  }
  return next
}

function FormationRow(props: { label: string; cells: string[]; draft: Record<string, string | null>; memberById: Record<string, CharacterView>; selected: string; onPlace: (c: string) => void; onClear: (c: string) => void }) {
  return (
    <div className="formRow">
      <span className="formRow__label">{props.label}</span>
      <div className="formRow__cells">
        {props.cells.map(cell => {
          const id = props.draft[cell]
          const m = id ? props.memberById[id] : null
          const cm = m ? classMeta(m.class_id) : null
          return (
            <button key={cell} className={cx('formCell', m && 'is-filled', props.selected && !m && 'is-target')}
              style={cm ? ({ '--accent': cm.accent } as CSSProperties) : undefined}
              onClick={() => (m && props.selected === id ? props.onClear(cell) : props.onPlace(cell))}
              onDoubleClick={() => props.onClear(cell)}
              title={CELL_LABEL[cell]}>
              <span className="formCell__pos">{CELL_LABEL[cell]}</span>
              {m ? (
                <div className="formCell__unit">
                  <CharacterAvatar ch={m} size={36} dimmed={m.hp <= 0} />
                  <b>{m.name}</b>
                  <span className="muted">{m.class_name}</span>
                </div>
              ) : (
                <span className="formCell__empty">{props.selected ? '＋ 放置' : '空位'}</span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function RosterCard(props: { m: CharacterView; inFormation: boolean; selected: boolean; onSelect: () => void; onInspect: () => void }) {
  const m = props.m
  const topAttrs = topAttributes(m)
  const learnedSkills = (m.skill_summary ?? []).filter(s => s.learned !== false)
  const lockedCount = (m.skill_summary ?? []).filter(s => s.learned === false).length
  const maxHp = Number(m.effective_stats?.max_hp ?? m.max_hp)
  const hp = Math.max(0, Math.min(maxHp, Number(m.hp ?? maxHp)))
  const maxMana = Number(m.effective_stats?.max_mana ?? m.max_mana ?? m.derived_stats?.mana ?? 0)
  const mana = Math.max(0, Math.min(maxMana, Number(m.mana ?? maxMana)))
  return (
    <div className={cx('rosterCard', props.selected && 'is-selected')} onClick={props.onSelect}>
      <div className="rosterCard__head">
        <CharacterAvatar ch={m} size={44} dimmed={!m.available || m.hp <= 0} />
        <div className="rosterCard__id">
          <b>{m.name}</b>
          <span className="muted">{m.class_name} · Lv.{m.level}</span>
        </div>
        <button className="iconBtn" title="查看详情" onClick={(e) => { e.stopPropagation(); props.onInspect() }}>📋</button>
      </div>
      <div className="rosterCard__resources">
        <div className="rosterCard__resource" title="生命：当前生存资源，归零会倒下。">
          <Bar value={hp} max={maxHp || 1} height={6} />
          <span>❤️ {Math.round(hp)}/{maxHp}</span>
        </div>
        {maxMana > 0 && (
          <div className="rosterCard__resource" title="法力：部分法术、治疗、净化与祝福技能会消耗。">
            <Bar value={mana} max={maxMana} height={6} color="#5c9cff" />
            <span>🔮 {Math.round(mana)}/{maxMana}</span>
          </div>
        )}
      </div>
      <div className="rosterCard__stats">
        {STATS.slice(0, 3).map(s => (
          <span key={s.key} className="statPill"><span>{s.icon}</span><b>{m.effective_stats?.[s.key] ?? 0}</b></span>
        ))}
      </div>
      <div className="rosterCard__attrs" title="WOD 八维最高项">
        {topAttrs.map(a => (
          <span key={a.key} className="attrMini"><span>{a.icon}</span>{a.label}<b>{a.value}</b></span>
        ))}
      </div>
      <div className="rosterCard__skills">
        {learnedSkills.slice(0, 4).map(s => (
          <span key={s.id} className="skillMini" title={s.description || s.name}>{s.name}</span>
        ))}
        {learnedSkills.length > 4 && <span className="skillMini skillMini--more">+{learnedSkills.length - 4}</span>}
        {(m.skill_points ?? 0) > 0 && <span className="skillMini skillMini--point">技能点 {m.skill_points}</span>}
        {lockedCount > 0 && <span className="skillMini skillMini--locked">未解锁 {lockedCount}</span>}
      </div>
      {m.status_effects?.length > 0 && (
        <div className="rosterCard__status">{m.status_effects.map((s, i) => <StatusChip key={i} type={s.type} duration={s.duration} potency={s.potency} />)}</div>
      )}
    </div>
  )
}

function topAttributes(m: CharacterView): Array<{ key: string; label: string; icon: string; value: number }> {
  const attrs = m.attributes ?? m.effective_stats?.attributes ?? {}
  return ATTRIBUTES
    .map(a => ({ ...a, value: Number(attrs[a.key] ?? 0) }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 4)
}

function MemberChip(props: { m: CharacterView; selected: boolean; locked?: boolean; onSelect: () => void; onInspect: () => void }) {
  return (
    <div className={cx('memberChip', props.selected && 'is-selected', props.locked && 'is-locked')} onClick={props.locked ? undefined : props.onSelect}>
      <CharacterAvatar ch={props.m} size={30} />
      <span>{props.m.name}</span>
      {props.locked && <span className="muted">{props.m.team_name}</span>}
      <button className="iconBtn" onClick={(e) => { e.stopPropagation(); props.onInspect() }}>📋</button>
    </div>
  )
}

function EquipEditor(props: { member: CharacterView; party: PartyView; onEquip: (id: string, item: string | null, slot?: string) => void; busy: boolean }) {
  const m = props.member
  return (
    <div className="equipEditor">
      <div className="equipEditor__head">
        <CharacterAvatar ch={m} size={40} />
        <div><b>{m.name}</b><span className="muted">{m.class_name}</span></div>
      </div>
      {EQUIPMENT_SLOT_ORDER.map(slot => {
        const equippedId = m.equipment?.[slot] ?? null
        const options = props.party.inventory.filter(i => itemFitsEquipmentSlot(i.slot, slot) && (!i.equipped_by || i.equipped_by === m.id))
        const occupiedByTwoHand = slot === 'off_hand' && equippedId && props.party.inventory.find(i => i.instance_id === equippedId)?.slot === 'two_hand'
        return (
          <div className="equipSlot" key={slot}>
            <div className="equipSlot__label">
              <span className="equipSlot__icon">{SLOT_ICON[slot]}</span>
              <b>{SLOT_LABEL[slot]}</b>
              {occupiedByTwoHand && <span className="muted">双手占用</span>}
            </div>
            {equippedId ? (
              <EquipmentCard item={props.party.inventory.find(i => i.instance_id === equippedId)!} compact
                actionLabel="卸下" actionIcon="↩" onClick={() => props.onEquip(m.id, null, slot)} />
            ) : (
              <div className="equipSlot__empty">未装备</div>
            )}
            {options.length > 0 && (
              <div className="equipSlot__options">
                <span className="muted">可替换：</span>
                <div className="equipSlot__grid">
                  {options.filter(i => i.instance_id !== equippedId).map(i => (
                    <EquipmentCard key={i.instance_id} item={i} compact selected={equippedId === i.instance_id}
                      actionLabel="装备" actionIcon="⬆"
                      onClick={() => props.onEquip(m.id, i.instance_id, compatibleEquipmentSlots(i.slot).includes(slot) ? slot : undefined)} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
