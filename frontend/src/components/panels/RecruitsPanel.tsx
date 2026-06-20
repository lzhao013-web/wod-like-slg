import { useState } from 'react'
import type { CSSProperties } from 'react'
import type { CharacterView, RecruitCandidateView, RecruitsView } from '../../types/game'
import { MAX_ROSTER_SIZE } from '../../types/game'
import { CharacterAvatar } from '../CharacterAvatar'
import { Chip } from '../Chips'
import { classMeta, rarityMeta } from '../../theme'
import { num } from '../../lib/format'

const ATTRIBUTE_LABEL: Record<string, string> = {
  strength: '力量', constitution: '体质', dexterity: '灵巧', agility: '敏捷',
  intelligence: '智力', willpower: '意志', perception: '感知', charisma: '魅力',
}

export function RecruitsPanel(props: {
  recruits: RecruitsView | null
  partyMembers: CharacterView[]
  gold: number
  busy: boolean
  onRecruit: (candidateId: string) => void
  onDismiss: (characterId: string) => void
}) {
  const candidates = props.recruits?.candidates ?? []
  const [expanded, setExpanded] = useState<string | null>(candidates[0]?.candidate_id ?? null)
  const [confirmDismiss, setConfirmDismiss] = useState<string | null>(null)

  if (!props.recruits) {
    return <section className="panel"><p className="muted">酒馆未就绪。</p></section>
  }

  const full = props.partyMembers.length >= MAX_ROSTER_SIZE

  return (
    <div className="shopLayout">
      <section className="panel shopCol">
        <div className="panel__head">
          <h2>🏰 酒馆 · 招募</h2>
          <span className="goldPill">🪙 {num(props.gold)}</span>
        </div>
        {candidates.length === 0 && <p className="muted">今日酒馆没有可招募的冒险者，次日刷新。</p>}
        <div className="recruitList">
          {candidates.map(c => {
            const rm = rarityMeta(c.rarity)
            const cm = classMeta(c.class_id)
            const poor = props.gold < c.cost
            const isOpen = expanded === c.candidate_id
            return (
              <div
                key={c.candidate_id}
                className="recruitCard"
                style={{ '--accent': cm.accent, '--rare': rm.color, '--glow': rm.glow } as CSSProperties}
              >
                <button className="recruitCard__head" onClick={() => setExpanded(isOpen ? null : c.candidate_id)}>
                  <CharacterAvatar ch={{ class_id: c.class_id, level: c.level, injury_state: 'healthy' }} size={48} />
                  <div className="recruitCard__title">
                    <b>{c.name}</b>
                    <span className="muted">
                      {c.rarity_label}{c.is_advanced ? ' · 进阶' : ''} · {c.class_name} · Lv.{c.level}
                    </span>
                  </div>
                  <span className="recruitCard__rarityTag" style={{ color: rm.color }}>{c.rarity_label}</span>
                  <span className="recruitCard__toggle">{isOpen ? '▾' : '▸'}</span>
                </button>

                <p className="recruitCard__role">{c.role}</p>

                {isOpen && <RecruitPreview ch={c.preview} />}

                <button
                  className={poor || full ? 'btn btn--ghost btn--sm' : 'btn btn--accent btn--sm'}
                  disabled={props.busy || poor || full}
                  onClick={() => props.onRecruit(c.candidate_id)}
                >
                  {full ? `队伍已满 (${MAX_ROSTER_SIZE})` : poor ? '💰 金币不足' : `招募 · 🪙${c.cost}`}
                </button>
              </div>
            )
          })}
        </div>
      </section>

      <section className="panel shopCol">
        <div className="panel__head">
          <h2>👥 我的队伍</h2>
          <Chip icon="👥" tone="muted">{props.partyMembers.length}/{MAX_ROSTER_SIZE}</Chip>
        </div>
        <div className="recruitList">
          {props.partyMembers.map(m => {
            const cm = classMeta(m.class_id)
            const inTeam = !!m.team_id
            const isLast = props.partyMembers.length <= 1
            const isConfirming = confirmDismiss === m.id
            return (
              <div key={m.id} className="recruitCard recruitCard--owned" style={{ '--accent': cm.accent } as CSSProperties}>
                <div className="recruitCard__head">
                  <CharacterAvatar ch={m} size={44} />
                  <div className="recruitCard__title">
                    <b>{m.name}</b>
                    <span className="muted">{m.class_name} · Lv.{m.level}{inTeam ? ` · ${m.team_name ?? '在编'}` : ' · 预备'}</span>
                  </div>
                </div>
                {isConfirming ? (
                  <div className="shopItem__recycle">
                    <button
                      className="btn btn--accent btn--sm"
                      disabled={props.busy}
                      onClick={() => { props.onDismiss(m.id); setConfirmDismiss(null) }}
                    >
                      确认解雇（返还 30% 招募金）
                    </button>
                    <button className="btn btn--ghost btn--sm" onClick={() => setConfirmDismiss(null)}>取消</button>
                  </div>
                ) : (
                  <button
                    className="btn btn--ghost btn--sm"
                    disabled={props.busy || inTeam || isLast}
                    title={inTeam ? '请先从编队移出' : isLast ? '至少保留一名角色' : '解雇并返还 30% 招募金'}
                    onClick={() => setConfirmDismiss(m.id)}
                  >
                    {inTeam ? '在编队中' : isLast ? '最后一名' : '🚪 解雇'}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}

/** Read-only attribute/stat snapshot of a candidate, shown pre-hire (WYSIWYG). */
function RecruitPreview({ ch }: { ch: CharacterView }) {
  const attrs = ch.attributes ?? {}
  const stats = ch.effective_stats ?? ch.base_stats ?? {}
  return (
    <div className="recruitCard__preview">
      {Object.keys(attrs).length > 0 && (
        <div className="recruitPreview__row">
          {Object.entries(attrs).map(([k, v]) => (
            <span key={k} className="recruitPreview__attr"><b>{v}</b> {ATTRIBUTE_LABEL[k] ?? k}</span>
          ))}
        </div>
      )}
      <div className="recruitPreview__row">
        <span>❤️ {ch.hp}/{ch.max_hp}</span>
        {ch.max_mana ? <span>🔷 {ch.max_mana}</span> : null}
        {stats.attack ? <span>⚔️ {stats.attack}</span> : null}
        {stats.defense ? <span>🛡️ {stats.defense}</span> : null}
        {stats.speed ? <span>💨 {stats.speed}</span> : null}
      </div>
      {ch.learned_skills && ch.learned_skills.length > 0 && (
        <div className="recruitPreview__skills muted">已知技能：{ch.learned_skills.join('、')}</div>
      )}
    </div>
  )
}
