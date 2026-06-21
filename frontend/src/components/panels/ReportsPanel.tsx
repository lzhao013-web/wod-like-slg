import type { ReportView } from '../../types/game'
import { ReportSummaryCard, ReportRewards, ReportLosses } from '../DayResults'
import { Chip, ElementChip, ResultBadge } from '../Chips'
import { Bar } from '../Bar'
import { BattleReplay } from '../BattleReplay'
import { elementMeta, enemyIcon, resultMeta, statusMeta, translateGameText } from '../../theme'
import { parseHpParts, cx } from '../../lib/format'

export function ReportsPanel(props: {
  reports: ReportView[]
  selected: string
  onSelect: (id: string) => void
  detail: ReportView | null
}) {
  return (
    <div className="reportsLayout" data-guide-id="reports-panel">
      <section className="panel reportsList" data-guide-id="reports-list">
        <div className="panel__head"><h2>📊 战报复盘</h2><span className="muted">{props.reports.length} 份</span></div>
        {props.reports.length === 0 && <p className="muted">尚无战报。</p>}
        <div className="reportFeed">
          {props.reports.map(r => <ReportSummaryCard key={r.id} report={r} selected={props.selected === r.id} onClick={() => props.onSelect(r.id)} />)}
        </div>
      </section>

      <section className="panel reportDetail" data-guide-id="reports-detail">
        <ReportDetail detail={props.detail} />
      </section>
    </div>
  )
}

function ReportDetail(props: { detail: ReportView | null }) {
  const { detail } = props
  if (!detail) return <div className="empty"><span className="empty__icon">📊</span><p>选择左侧任一战报，查看逐层复盘、伤害统计与回合详情。</p></div>
  const res = resultMeta(detail.result)
  const hasReplay = detail.type === 'challenge' && (detail.layer_results ?? []).some((l: any) => (l.round_details ?? []).length > 0 || (l.pre_events ?? []).length > 0)

  return (
    <div className="rpDetail">
      <div className="rpDetail__hero" style={{ '--res': res.color } as any}>
        <span className="rpDetail__crest">{res.icon}</span>
        <div>
          <h2>{detail.dungeon_name}</h2>
          <span className="muted">
            第 {detail.day} 天 · {detail.type === 'scout' ? '侦察' : detail.type === 'rest' ? '休整' : '挑战'}
            {detail.team_name ? ` · ${detail.team_name}` : ''}
            {detail.type === 'challenge' ? ` · 战术：${detail.tactic_scheme_name ?? '当前战术'}` : ''}
          </span>
        </div>
        <ResultBadge result={detail.result} size="lg" />
      </div>
      <p className="rpDetail__summary">{detail.summary}</p>

      {detail.type === 'challenge' && (
        <>
          <h3 className="sub">🧭 战斗总览</h3>
          <ReviewMetrics report={detail} />
          {(detail.battle_recap ?? []).length > 0 && (
            <ul className="recapList">{detail.battle_recap!.map((x, i) => <li key={i}>{x}</li>)}</ul>
          )}
          {hasReplay && <BattleReplay report={detail} autoPlay />}
        </>
      )}

      {(detail.layer_results ?? []).length > 0 && (
        <>
          <h3 className="sub">📜 逐层战况</h3>
          <div className="rpLayers">
            {detail.layer_results.map((l: any, i: number) => {
              const dead = (l.enemy_remaining ?? []).length === 0
              return (
                <div className="rpLayer" key={i}>
                  <div className="rpLayer__head">
                    <span className="rpLayer__idx">{l.index}</span>
                    <span className="rpLayer__icon">{l.type === 'trap' ? '🪤' : '⚔️'}</span>
                    <b>{l.name}</b>
                    <span className="muted">{l.rounds} 回合</span>
                    <ResultBadge result={l.result} size="sm" />
                  </div>
                  <div className="rpLayer__hp">
                    {Object.entries(l.party_hp ?? {}).map(([name, hp]: [string, any]) => {
                      const { cur, max } = parseHpParts(hp)
                      return (
                        <div className="rpLayerHp" key={name}>
                          <span className="rpLayerHp__name">{name}</span>
                          <Bar value={cur} max={max} height={8} glow />
                          <span className="rpLayerHp__num">{cur}/{max}</span>
                        </div>
                      )
                    })}
                  </div>
                  {(l.damage_done && Object.keys(l.damage_done).length > 0) && (
                    <div className="rpLayer__stats">
                      <MiniStat title="输出" stats={l.damage_done} />
                      <MiniStat title="承伤" stats={l.damage_taken ?? {}} />
                      <MiniStat title="治疗" stats={l.healing_done ?? {}} />
                    </div>
                  )}
                  {!dead && (
                    <div className="rpLayer__enemies">
                      <span className="muted">残敌：</span>
                      {(l.enemy_remaining ?? []).map((e: string, j: number) => (
                        <span className="enemyChip" key={j}><span>{enemyIcon([], e)}</span>{e}</span>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}

      <div className="rpDetail__cols">
        <div className="rpDetail__col">
          <ReportRewards report={detail} />
          <ReportLosses report={detail} memberByName={{}} />
        </div>
        <div className="rpDetail__col">
          <StatBlock title="🗡️ 输出" stats={detail.damage_stats ?? {}} tone="accent" />
          <StatBlock title="🩸 承伤" stats={detail.damage_taken_stats ?? {}} tone="danger" />
          <StatBlock title="💚 治疗" stats={detail.healing_stats ?? {}} tone="good" />
          <StatBlock title="🔮 法力消耗" stats={detail.mana_spent_stats ?? {}} tone="info" />
          <StatBlock title="🎯 未命中" stats={detail.miss_stats ?? {}} tone="warn" />
        </div>
      </div>

      {Object.keys(detail.damage_by_type_stats ?? {}).length > 0 && (
        <>
          <h3 className="sub">🌈 伤害类型构成</h3>
          <div className="statChips">{Object.entries(detail.damage_by_type_stats ?? {}).map(([k, v]) => <ElementChip key={k} type={k} value={v as number} />)}</div>
        </>
      )}

      {(detail.critical_events ?? []).length > 0 && (
        <>
          <h3 className="sub">⚡ 关键节点</h3>
          <ol className="timelineList">{detail.critical_events!.map((r, i) => <li key={i}>{translateGameText(r)}</li>)}</ol>
        </>
      )}

      {Object.keys(detail.party_skill_usage_stats ?? detail.skill_usage_stats ?? {}).length > 0 && (
        <>
          <h3 className="sub">🧪 技能使用</h3>
          <SkillUsageGrid title="我方" stats={detail.party_skill_usage_stats ?? detail.skill_usage_stats ?? {}} />
          {Object.keys(detail.enemy_skill_usage_stats ?? {}).length > 0 && <SkillUsageGrid title="敌方" stats={detail.enemy_skill_usage_stats ?? {}} compact />}
        </>
      )}

      {Object.keys(detail.status_stats ?? {}).length > 0 && (
        <>
          <h3 className="sub">🌀 状态触发</h3>
          <div className="statChips">{Object.entries(detail.status_stats).map(([k, v]) => {
            const meta = statusMeta(k)
            return <Chip key={k} tone="warn" icon={meta.icon}>{meta.label} ×{v as number}</Chip>
          })}</div>
        </>
      )}

      {(detail.failure_reasons ?? []).length > 0 && (
        <>
          <h3 className="sub">📋 复盘 · 归因</h3>
          <ul className="warnList">{detail.failure_reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </>
      )}

      {(detail.revealed_mechanics ?? []).length > 0 && (
        <>
          <h3 className="sub">🔍 机制发现</h3>
          <ul className="intelList">{detail.revealed_mechanics.map((x, i) => <li key={i}>{x}</li>)}</ul>
        </>
      )}

      {(detail.turn_logs ?? []).length > 0 && (
        <details className="rpDetail__log">
          <summary>完整回合日志（{detail.turn_logs.length} 条）</summary>
          <ol className="logList">{detail.turn_logs.map((l, i) => <li key={i}>{translateGameText(l)}</li>)}</ol>
        </details>
      )}
    </div>
  )
}

function ReviewMetrics(props: { report: ReportView }) {
  const m = props.report.review_metrics ?? {}
  const mainType = m.main_damage_type
  const cards = [
    { label: '总回合', value: m.rounds_total ?? 0, icon: '⏱️' },
    { label: '总输出', value: m.total_damage_done ?? 0, icon: '🗡️' },
    { label: '总承伤', value: m.total_damage_taken ?? 0, icon: '🩸' },
    { label: '总治疗', value: m.total_healing ?? 0, icon: '💚' },
    { label: '法力消耗', value: m.total_mana_spent ?? 0, icon: '🔮' },
    { label: '后排承伤', value: m.backline_damage ?? 0, icon: '🎯' },
    { label: '未命中', value: m.misses_total ?? 0, icon: '💨' },
  ]
  return (
    <div className="metricGrid">
      {cards.map(c => (
        <div className="metricCard" key={c.label}>
          <span>{c.icon}</span>
          <b>{c.value}</b>
          <em>{c.label}</em>
        </div>
      ))}
      {m.top_damage && <div className="metricCard metricCard--wide"><span>🏅</span><b>{m.top_damage.name}</b><em>最高输出 {m.top_damage.value}</em></div>}
      {m.top_taken && <div className="metricCard metricCard--wide"><span>🛡️</span><b>{m.top_taken.name}</b><em>最大承伤 {m.top_taken.value}</em></div>}
      {mainType && <div className="metricCard metricCard--wide"><span>🌈</span><b>{mainType.value}</b><em>主要类型 {elementMeta(mainType.type).label}</em></div>}
    </div>
  )
}

function MiniStat(props: { title: string; stats: Record<string, number> }) {
  const entries = Object.entries(props.stats ?? {}).filter(([, v]) => v).sort((a, b) => (b[1] as number) - (a[1] as number)).slice(0, 3)
  if (entries.length === 0) return null
  return (
    <div className="miniStat">
      <b>{props.title}</b>
      {entries.map(([name, value]) => <span key={name}>{name} <em>{value as number}</em></span>)}
    </div>
  )
}

function SkillUsageGrid(props: { title: string; stats: Record<string, Record<string, number>>; compact?: boolean }) {
  const rows = Object.entries(props.stats ?? {}).filter(([, skills]) => Object.keys(skills ?? {}).length > 0)
  if (rows.length === 0) return null
  return (
    <div className={cx('skillUsage', props.compact && 'skillUsage--compact')}>
      <b className="skillUsage__title">{props.title}</b>
      {rows.slice(0, props.compact ? 6 : 10).map(([actor, skills]) => (
        <div className="skillUsage__row" key={actor}>
          <span className="skillUsage__actor">{actor}</span>
          <div className="skillUsage__chips">
            {Object.entries(skills).sort((a, b) => (b[1] as number) - (a[1] as number)).slice(0, 5).map(([skill, n]) => (
              <Chip key={skill} tone={props.compact ? 'muted' : 'info'}>{skill} ×{n as number}</Chip>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function StatBlock(props: { title: string; stats: Record<string, number>; tone: 'accent' | 'danger' | 'good' | 'warn' | 'info' }) {
  const entries = Object.entries(props.stats).filter(([, v]) => v)
  const max = Math.max(1, ...entries.map(([, v]) => v as number))
  return (
    <div className={cx('statBlock', `statBlock--${props.tone}`)}>
      <h4>{props.title}</h4>
      {entries.length === 0 ? <span className="muted">无</span> : entries.map(([k, v]) => (
        <div className="statBlock__row" key={k}>
          <span className="statBlock__name">{k}</span>
          <Bar value={v as number} max={max} height={8} />
          <b>{v as number}</b>
        </div>
      ))}
    </div>
  )
}
