import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import type { CharacterView, DungeonCardView, DungeonDetailView, PartyView, PlanAction, TacticScheme } from '../../types/game'
import { Chip, DangerMeter } from '../Chips'
import { Bar } from '../Bar'
import { themeIcon, themeAccent, AFFIX_ICON } from '../../theme'
import { cx } from '../../lib/format'

export function DungeonsPanel(props: {
  dungeons: DungeonCardView[]
  selected: string
  onSelect: (id: string) => void
  detail: DungeonDetailView | null
  party: PartyView
  plan: PlanAction[]
  onScout: (id: string, teamId: string) => void
  tacticSchemes: TacticScheme[]
  onChallenge: (id: string, tacticSchemeId: string | undefined, teamId: string) => void
  onClear: () => void
  onRemove: (index: number) => void
  busy: boolean
  pointsLeft: number
}) {
  return (
    <div className="dungeonLayout">
      {/* Compact expedition strip — shows today's planned actions as inline chips.
          The "结算远征" button and remaining count already live in the TopBar. */}
      <div className="dungeonStrip">
        <div className="dungeonStrip__label">
          <b>🧭 今日出征</b>
        </div>
        <div className="dungeonStrip__slots">
          {props.plan.length === 0 ? (
            <span className="dungeonStrip__empty">尚未安排，选中副本后侦察或挑战</span>
          ) : props.plan.map((action, i) => (
            <span key={action.id || i} className={cx('dungeonChip', `dungeonChip--${action.type}`)}>
              <span className="dungeonChip__icon">{action.type === 'scout' ? '🔭' : '⚔️'}</span>
              <b>{action.dungeon_name}</b>
              <span className="dungeonChip__team">{action.team_name ?? '队伍'}</span>
              <button className="dungeonChip__x" disabled={props.busy} onClick={() => props.onRemove(i)} title="撤销">✕</button>
            </span>
          ))}
        </div>
        {props.plan.length > 0 && (
          <button className="btn btn--ghost btn--sm dungeonStrip__clear" disabled={props.busy} onClick={props.onClear}>
            清空
          </button>
        )}
      </div>

      {/* Two-column dungeon browser */}
      <section className="panel dungeonList">
        <div className="panel__head"><h2>⚔️ 副本情报</h2><span className="muted">{props.dungeons.length} 个</span></div>
        {props.dungeons.length === 0 && <p className="muted">今日没有可用副本。</p>}
        {props.dungeons.map(d => {
          const accent = themeAccent(d.theme)
          return (
            <button key={d.dungeon_id}
              className={cx('dungeonBtn', props.selected === d.dungeon_id && 'is-selected', d.is_final && 'is-final')}
              style={{ '--accent': accent } as CSSProperties}
              onClick={() => props.onSelect(d.dungeon_id)}>
              <span className="dungeonBtn__icon">{themeIcon(d.theme)}</span>
              <span className="dungeonBtn__body">
                <b>{d.name}{d.is_final && ' 🐉'}</b>
                <span className="muted">{d.theme}</span>
                <span className="dungeonBtn__tags">
                  <DangerMeter level={d.danger_level} />
                  <span className="muted">⏳ {d.remaining_days}</span>
                  {d.scouted && <Chip icon="🔭" tone="info">已侦察</Chip>}
                  {d.cleared && <Chip icon="✓" tone="good">已通关</Chip>}
                  {d.is_final && <Chip icon="🐉" tone="accent">最终</Chip>}
                </span>
              </span>
            </button>
          )
        })}
      </section>

      <section className="panel dungeonDetail">
        <DungeonDetail
          detail={props.detail}
          party={props.party}
          plan={props.plan}
          tacticSchemes={props.tacticSchemes}
          onScout={props.onScout}
          onChallenge={props.onChallenge}
          busy={props.busy}
          pointsLeft={props.pointsLeft}
        />
      </section>
    </div>
  )
}

function DungeonDetail(props: {
  detail: DungeonDetailView | null
  party: PartyView
  plan: PlanAction[]
  tacticSchemes: TacticScheme[]
  onScout: (id: string, teamId: string) => void
  onChallenge: (id: string, tacticSchemeId: string | undefined, teamId: string) => void
  busy: boolean
  pointsLeft: number
}) {
  const [selectedSchemeId, setSelectedSchemeId] = useState('')
  const [selectedTeamId, setSelectedTeamId] = useState('')
  const selectedScheme = props.tacticSchemes.find(s => s.id === selectedSchemeId)

  useEffect(() => {
    setSelectedSchemeId(prev => (
      prev && props.tacticSchemes.some(s => s.id === prev)
        ? prev
        : (props.tacticSchemes[0]?.id ?? '')
    ))
  }, [props.tacticSchemes])

  // Teams already committed to today's expedition plan (cannot deploy twice).
  const deployedTeams = new Set(props.plan.map(a => a.team_id).filter(Boolean) as string[])
  const teamRows = buildTeamRows(props.party).map(t => ({ ...t, deployed: deployedTeams.has(t.id) }))
  // Default to the first deployable team whenever the selection is taken or unset.
  useEffect(() => {
    const chosen = teamRows.find(t => t.id === selectedTeamId)
    if (!chosen || chosen.deployed || chosen.empty) {
      const fallback = teamRows.find(t => !t.deployed && !t.empty)
      setSelectedTeamId(fallback?.id ?? teamRows[0]?.id ?? '')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTeamId, props.party, props.plan])

  const { detail } = props
  if (!detail) return <div className="empty"><span className="empty__icon">🗺️</span><p>从左侧选择一个副本，查看公开情报、侦察结果与风险提示。</p></div>
  const accent = themeAccent(detail.template_theme || detail.theme)
  const scouted = !!detail.scout_info
  const chosenTeam = teamRows.find(t => t.id === selectedTeamId)
  const noTeamAvailable = !chosenTeam || chosenTeam.deployed || chosenTeam.empty
  return (
    <div className="detail" style={{ '--accent': accent } as CSSProperties}>
      <div className="detail__hero">
        <span className="detail__crest">{themeIcon(detail.template_theme)}</span>
        <div>
          <h2 className="detail__name">{detail.name}{detail.is_final && ' 🐉'}</h2>
          <p className="detail__theme">{detail.template_theme}</p>
        </div>
        <div className="detail__badges">
          <Chip icon="⚠" tone="danger"><DangerMeter level={detail.danger_level} /></Chip>
          <Chip icon="⏳" tone={detail.remaining_days <= 1 ? 'danger' : 'muted'}>{detail.remaining_days} 天后过期</Chip>
          <Chip icon="🎁" tone="accent">奖励 ×{detail.reward_charges}</Chip>
        </div>
      </div>

      <div className="detail__cols">
        <div className="detail__col">
          <h3 className="sub">🪧 公开情报</h3>
          <ul className="threatList">{detail.public_info?.threats?.map((t: string, i: number) => <li key={i}>{t}</li>)}</ul>
          {detail.public_info?.main_rewards?.length > 0 && (
            <p className="muted">主要奖励：{detail.public_info.main_rewards.join('、')}</p>
          )}

          {(detail.affixes ?? []).length > 0 && (
            <>
              <h3 className="sub">{AFFIX_ICON} 词缀</h3>
              <div className="affixList">
                {detail.affixes.map(a => (
                  <div className="affix" key={a.id}><b>{a.name}</b><p>{a.description}</p></div>
                ))}
              </div>
            </>
          )}

          {detail.risk_warnings?.length > 0 && (
            <>
              <h3 className="sub">⚠️ 风险提示</h3>
              <ul className="warnList">{detail.risk_warnings.map((w, i: number) => <li key={i}>{w}</li>)}</ul>
            </>
          )}
        </div>

        <div className="detail__col">
          <h3 className="sub">{scouted ? '🔭 侦察情报' : '🚫 未侦察'}</h3>
          {scouted ? (
            <div className="scoutIntel">
              <ul className="intelList">{detail.scout_info?.lines?.map((l: string, i: number) => <li key={i}>{l}</li>)}</ul>
              {(detail.scout_info?.recommended_response ?? []).length > 0 && (
                <div className="recList">
                  <b>💡 建议应对：</b>
                  <ul>{detail.scout_info!.recommended_response.map((r: string, i: number) => <li key={i}>{r}</li>)}</ul>
                </div>
              )}
            </div>
          ) : (
            <p className="muted">敌方阵型、层结构与 Boss 技能仍未知 —— 建议先安排一次侦察。</p>
          )}

          {detail.known_layers?.length > 0 && (
            <>
              <h3 className="sub">📜 已知层结构</h3>
              <div className="layerPreview">
                {detail.known_layers.map(l => (
                  <div className="layerPreview__item" key={l.index}>
                    <span className="layerPreview__idx">{l.index}</span>
                    <span className="layerPreview__icon">{l.type === 'trap' ? '🪤' : '⚔️'}</span>
                    <div><b>{l.name}</b><span className="muted">{l.type}{l.hint ? ` · ${l.hint}` : ''}</span></div>
                  </div>
                ))}
              </div>
            </>
          )}

          {detail.post_battle_info?.length > 0 && (
            <>
              <h3 className="sub">🩹 战后复盘情报</h3>
              <ul className="intelList">{detail.post_battle_info.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
            </>
          )}
        </div>
      </div>

      <div className="detail__actions">
        {/* Expedition target — pick which team deploys here. */}
        <div className="teamPicker">
          <span className="fieldRow__label">出征队伍</span>
          <div className="teamPicker__options">
            {teamRows.map(t => {
              const selected = t.id === selectedTeamId
              return (
                <button key={t.id} type="button"
                  className={cx('teamCard', selected && 'is-selected', t.deployed && 'is-deployed', t.empty && 'is-empty')}
                  onClick={() => setSelectedTeamId(t.id)}
                  disabled={t.deployed || t.empty}
                  title={t.deployed ? `${t.label}今日已出征` : t.empty ? `${t.label}没有上阵角色` : t.summary}
                >
                  <span className="teamCard__label">{t.icon} {t.label}</span>
                  <span className="teamCard__members">{t.summary}</span>
                  {t.deployed && <span className="teamCard__state">已出征</span>}
                  {t.empty && !t.deployed && <span className="teamCard__state">空队</span>}
                </button>
              )
            })}
          </div>
        </div>

        <label className="fieldRow schemePicker">
          <span className="fieldRow__label">总方案</span>
          <select
            value={selectedSchemeId}
            onChange={e => setSelectedSchemeId(e.target.value)}
            title="挑战会绑定这里选择的总方案；不选则使用当前已保存的活动战术。"
          >
            <option value="">当前战术（未绑定总方案）</option>
            {props.tacticSchemes.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>

        <div className="detail__btnRow">
          <button className="btn btn--ghost" onClick={() => props.onScout(detail.dungeon_id, selectedTeamId)} disabled={props.busy || scouted || noTeamAvailable}>
            🔭 {scouted ? '已侦察' : `安排侦察（${chosenTeam?.label ?? '无队伍'}）`}
          </button>
          <button className="btn btn--primary" onClick={() => props.onChallenge(detail.dungeon_id, selectedSchemeId || undefined, selectedTeamId)} disabled={props.busy || noTeamAvailable}>
            ⚔️ 安排挑战（{chosenTeam?.label ?? '无队伍'} · {selectedScheme?.name ?? '当前战术'}）
          </button>
        </div>
        {noTeamAvailable && <span className="muted">没有可出征的队伍——所有队伍今日都已出征，或对应队伍没有上阵角色。</span>}
        {!noTeamAvailable && props.pointsLeft <= 0 && <span className="muted">今日远征次数已用完，需结束当天后恢复。</span>}
      </div>
    </div>
  )
}

/** Build a renderable summary of each team from the party formations. */
function buildTeamRows(party: PartyView): Array<{ id: string; label: string; icon: string; summary: string; deployed: boolean; empty: boolean }> {
  const teamIds = Object.keys(party.team_labels)
  const memberById = new Map<string, CharacterView>(party.members.map(m => [m.id, m]))
  return teamIds.map(id => {
    const formation = party.formations?.[id] ?? {}
    const memberIds = Object.values(formation).filter(Boolean) as string[]
    const names = memberIds.map(mid => memberById.get(mid)?.name).filter(Boolean) as string[]
    const summary = names.length > 0 ? names.join('、') : '未上阵'
    return {
      id,
      label: party.team_labels[id] ?? id,
      icon: id === 'team_1' ? '🛡️' : '🚩',
      summary,
      deployed: false, // filled per-call by caller (deployedTeams), see below
      empty: memberIds.length === 0,
    }
  })
}
