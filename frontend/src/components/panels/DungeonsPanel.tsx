import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import type { DungeonCardView, DungeonDetailView, TacticScheme } from '../../types/game'
import { Chip, DangerMeter, ResultBadge } from '../Chips'
import { Bar } from '../Bar'
import { themeIcon, themeAccent, AFFIX_ICON, enemyIcon } from '../../theme'
import { cx } from '../../lib/format'

export function DungeonsPanel(props: {
  dungeons: DungeonCardView[]
  selected: string
  onSelect: (id: string) => void
  detail: DungeonDetailView | null
  onScout: (id: string) => void
  tacticSchemes: TacticScheme[]
  onChallenge: (id: string, tacticSchemeId?: string) => void
  busy: boolean
  pointsLeft: number
}) {
  return (
    <div className="dungeonLayout">
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
  tacticSchemes: TacticScheme[]
  onScout: (id: string) => void
  onChallenge: (id: string, tacticSchemeId?: string) => void
  busy: boolean
  pointsLeft: number
}) {
  const [selectedSchemeId, setSelectedSchemeId] = useState('')
  const selectedScheme = props.tacticSchemes.find(s => s.id === selectedSchemeId)

  useEffect(() => {
    setSelectedSchemeId(prev => (
      prev && props.tacticSchemes.some(s => s.id === prev)
        ? prev
        : (props.tacticSchemes[0]?.id ?? '')
    ))
  }, [props.tacticSchemes])

  const { detail } = props
  if (!detail) return <div className="empty"><span className="empty__icon">🗺️</span><p>从左侧选择一个副本，查看公开情报、侦察结果与风险提示。</p></div>
  const accent = themeAccent(detail.template_theme || detail.theme)
  const scouted = !!detail.scout_info
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
              <ul className="warnList">{detail.risk_warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
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
        <button className="btn btn--ghost" onClick={() => props.onScout(detail.dungeon_id)} disabled={props.busy || scouted}>
          🔭 {scouted ? '已侦察' : '安排侦察（下一可用队伍）'}
        </button>
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
        <button className="btn btn--primary" onClick={() => props.onChallenge(detail.dungeon_id, selectedSchemeId || undefined)} disabled={props.busy}>
          ⚔️ 安排挑战（{selectedScheme?.name ?? '当前战术'}）
        </button>
        {props.pointsLeft <= 0 && <span className="muted">今日远征次数已用完，需结束当天后恢复。</span>}
      </div>
    </div>
  )
}
