import type { CSSProperties } from "react"
import type { DungeonCardView, GameStateView, ReportView } from '../../types/game'
import { DangerMeter, PointPips } from '../Chips'
import { ReportSummaryCard } from '../DayResults'
import { themeIcon, themeAccent, materialIcon } from '../../theme'
import { num, cx } from '../../lib/format'

export function OverviewPanel(props: {
  state: GameStateView
  dungeons: DungeonCardView[]
  reports: ReportView[]
  partySize: number
  onPickDungeon: (id: string) => void
  onPickReport: (id: string) => void
}) {
  const { state } = props
  const activeFinal = props.dungeons.find(d => d.is_final)
  return (
    <div className="panelGrid">
      <section className="panel panel--vibe">
        <div className="panel__head"><h2>🗺️ 今日局势</h2><span className="muted">第 {state.day} 天</span></div>
        <div className="overviewMetrics">
          <Metric icon="🪙" label="金币" value={num(state.gold)} />
          <Metric icon="⚔️" label="远征次数" value={<PointPips left={state.expedition_points_left} />} />
          <Metric icon="🏰" label="可用副本" value={props.dungeons.length} />
          <Metric icon={state.final_unlocked ? '🔓' : '🔒'} label="最终挑战" value={state.final_unlocked ? '已解锁' : '锁定中'} tone={state.final_unlocked ? 'good' : 'muted'} />
        </div>

        {Object.keys(state.materials_display).length > 0 && (
          <>
            <h3 className="sub">📦 物资</h3>
            <div className="matRow">
              {Object.entries(state.materials_display).map(([k, v]) => (
                <span className="matPill" key={k}><span className="matPill__icon">{materialIcon(k)}</span>{k} <b>{v}</b></span>
              ))}
            </div>
          </>
        )}

        <h3 className="sub">⚠️ 今日关注</h3>
        {state.warnings.length ? (
          <ul className="warnList">{state.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
        ) : (
          <p className="muted">暂无明显风险，适合推进或休整备战。</p>
        )}

        {activeFinal && (
          <div className="finalCallout">
            <span className="finalCallout__icon">🐉</span>
            <div><b>最终挑战：{activeFinal.name}</b><p>{activeFinal.theme}</p></div>
            <DangerMeter level={activeFinal.danger_level} />
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel__head"><h2>⚔️ 可选目标</h2><span className="muted">{props.dungeons.length} 个</span></div>
        <div className="dungeonRail">
          {props.dungeons.slice(0, 4).map(d => (
            <button key={d.dungeon_id} className={cx('dungeonTile')} onClick={() => props.onPickDungeon(d.dungeon_id)}
              style={{ '--accent': themeAccent(d.theme) } as CSSProperties}>
              <div className="dungeonTile__icon">{themeIcon(d.theme)}</div>
              <div className="dungeonTile__body">
                <b>{d.name}{d.is_final && ' 🐉'}</b>
                <span className="muted">{d.theme}</span>
              </div>
              <div className="dungeonTile__meta">
                <DangerMeter level={d.danger_level} />
                <span className="muted">⏳ {d.remaining_days}天</span>
              </div>
            </button>
          ))}
        </div>

        <div className="panel__head" style={{ marginTop: 18 }}><h2>📊 最近战报</h2></div>
        {props.reports.length === 0 ? (
          <p className="muted">尚无战报 —— 安排一次远征试试。</p>
        ) : (
          <div className="reportRail">{props.reports.slice(0, 3).map(r => <ReportSummaryCard key={r.id} report={r} onClick={() => props.onPickReport(r.id)} />)}</div>
        )}
      </section>
    </div>
  )
}

function Metric(props: { icon: string; label: string; value: any; tone?: string }) {
  return (
    <div className={cx('metric', props.tone && `metric--${props.tone}`)}>
      <span className="metric__icon">{props.icon}</span>
      <span className="metric__label">{props.label}</span>
      <span className="metric__value">{props.value}</span>
    </div>
  )
}
