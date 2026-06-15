import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import type { CharacterView, ReportView } from '../types/game'
import { HpBar } from './Bar'
import { BattleReplay } from './BattleReplay'
import { CharacterAvatar } from './CharacterAvatar'
import { Chip, ResultBadge } from './Chips'
import { resultMeta, enemyIcon, materialIcon, materialName, translateGameText } from '../theme'
import { parseHpParts, cx } from '../lib/format'

/** Full-screen theatre that plays out the day's expeditions one report at a time. */
export function DayResults(props: {
  reports: ReportView[]
  partyMembers: CharacterView[]
  day: number
  finished: boolean // whether the run has reached victory/defeat after this day
  onContinue: () => void
}) {
  const [index, setIndex] = useState(0)
  const [skippedAll, setSkippedAll] = useState(false)
  const report = props.reports[index]
  const memberByName = useMemo(() => {
    const m: Record<string, CharacterView> = {}
    for (const ch of props.partyMembers) m[ch.name] = ch
    return m
  }, [props.partyMembers])

  const isLast = index >= props.reports.length - 1

  return (
    <div className="overlay overlay--results">
      <div className="results">
        <div className="results__head">
          <span className="results__title">⚔️ 第 {props.day} 天 · 远征结算</span>
          <span className="results__progress">{index + 1} / {props.reports.length} 份战报</span>
          {!skippedAll && <button className="btn btn--ghost btn--sm" onClick={() => setSkippedAll(true)}>⏩ 全部跳过</button>}
        </div>

        {report ? (
          <ReportPlayback
            key={report.id}
            report={report}
            memberByName={memberByName}
            skippedAll={skippedAll}
            onSettled={() => {}}
          />
        ) : (
          <div className="results__card">没有产生战报。</div>
        )}

        <div className="results__foot">
          <button className="btn btn--ghost" onClick={() => { setSkippedAll(true); setIndex(i => Math.max(0, i - 1)) }} disabled={index === 0}>← 上一份</button>
          {isLast ? (
            <button className="btn btn--primary" onClick={props.onContinue}>
              {props.finished ? '查看结局 →' : '返回指挥台 →'}
            </button>
          ) : (
            <button className="btn btn--primary" onClick={() => { setIndex(i => i + 1); setSkippedAll(false) }}>下一份战报 →</button>
          )}
        </div>
      </div>
    </div>
  )
}

/** Plays a single report: intro → layer-by-layer → settled result. */
function ReportPlayback(props: {
  report: ReportView
  memberByName: Record<string, CharacterView>
  skippedAll: boolean
  onSettled: () => void
}) {
  const { report } = props
  const layers: any[] = report.layer_results ?? []
  const isBattle = report.type === 'challenge' && layers.length > 0
  const isScout = report.type === 'scout'
  const isRest = report.type === 'rest'

  // battle member names (in combat order) from layer snapshots
  const battleNames = useMemo(() => {
    if (!isBattle) return []
    const order: string[] = []
    const seen = new Set<string>()
    for (const l of layers) {
      for (const name of Object.keys(l?.party_hp ?? {})) {
        if (!seen.has(name)) { seen.add(name); order.push(name) }
      }
    }
    return order
  }, [isBattle, layers])

  const totalSteps = layers.length + 2 // intro, layers..., settle
  const [step, setStep] = useState(0)
  const [speed, setSpeed] = useState(1)
  const settled = step >= totalSteps - 1
  const revealedLayerCount = Math.max(0, step - 1)

  const timer = useRef<number | null>(null)
  useEffect(() => {
    if (props.skippedAll) { setStep(totalSteps - 1); return }
    if (settled) return
    const delay = (isBattle ? 1150 : 950) / speed
    timer.current = window.setTimeout(() => setStep(s => Math.min(totalSteps - 1, s + 1)), delay)
    return () => { if (timer.current) window.clearTimeout(timer.current) }
  }, [step, settled, speed, props.skippedAll, totalSteps, isBattle])

  const prevHpRef = useRef<Record<string, number>>({})
  const currentSnapshot = (name: string): { cur: number; max: number } => {
    for (let i = revealedLayerCount - 1; i >= 0; i--) {
      const hp = layers[i]?.party_hp?.[name]
      if (hp !== undefined) return parseHpParts(hp)
    }
    const ch = props.memberByName[name]
    const max = ch?.effective_stats?.max_hp ?? ch?.max_hp ?? 100
    return { cur: max, max }
  }

  if (isScout) return <ScoutReport report={report} skippedAll={props.skippedAll} />
  if (isRest) return <RestReport report={report} />

  const res = resultMeta(report.result)
  const settledLayer = layers[revealedLayerCount - 1]
  const hasReplay = layers.some((l: any) => (l.round_details ?? []).length > 0 || (l.pre_events ?? []).length > 0)

  return (
    <div className="results__card">
      <div className="battle">
        <div className="battle__banner" style={{ '--res': res.color } as CSSProperties}>
          <span className="battle__name">{report.dungeon_name}{report.team_name ? ` · ${report.team_name}` : ''}</span>
          {settled && <ResultBadge result={report.result} size="lg" />}
          {!settled && <span className="battle__live">{revealedLayerCount === 0 ? '部署中…' : `第 ${revealedLayerCount} 层交战`}<span className="blink">▍</span></span>}
        </div>

        {hasReplay && <BattleReplay report={report} compact autoPlay={!props.skippedAll} />}

        {/* Party line-up with draining HP */}
        <div className="battle__party">
          {battleNames.map(name => {
            const snap = currentSnapshot(name)
            const ch = props.memberByName[name]
            const prev = prevHpRef.current[name] ?? snap.cur
            const took = snap.cur < prev && step > 1
            prevHpRef.current[name] = snap.cur
            return (
              <div className={cx('battle__unit', took && 'is-hit')} key={name}>
                {ch ? <CharacterAvatar ch={ch} size={42} dimmed={snap.cur <= 0} /> : <span className="avatar avatar--neutral">{name[0]}</span>}
                <div className="battle__unitBody">
                  <b className="battle__unitName">{name}{ch && <span className="battle__cls">{ch.class_name}</span>}</b>
                  <HpBar cur={snap.cur} max={snap.max} height={10} />
                </div>
              </div>
            )
          })}
        </div>

        {/* Layer progression */}
        <div className="battle__layers">
          {layers.map((layer, i) => {
            const r = i + 1
            const state: 'done' | 'active' | 'pending' = revealedLayerCount >= r ? 'done' : revealedLayerCount + 1 === r && !settled ? 'active' : 'pending'
            const lr = layer
            return (
              <div className={cx('layer', `layer--${state}`)} key={i}>
                <div className="layer__head">
                  <span className="layer__idx">{r}</span>
                  <span className="layer__icon">{layerTypeIcon(lr?.type)}</span>
                  <b className="layer__name">{lr?.name ?? `第 ${r} 层`}</b>
                  <span className="layer__rounds">{lr?.rounds ? `${lr.rounds} 回合` : ''}</span>
                  {state !== 'pending' && <ResultBadge result={lr?.result ?? 'victory'} size="sm" />}
                </div>
                {state !== 'pending' && (
                  <div className="layer__detail">
                    {(lr?.enemy_remaining ?? []).length > 0 && state === 'done' && (
                      <div className="layer__enemies">
                        <span className="muted">残敌：</span>
                        {lr.enemy_remaining.map((e: string, j: number) => (
                          <span className="enemyChip" key={j}><span>{enemyIcon([], e)}</span>{e}</span>
                        ))}
                      </div>
                    )}
                    {state === 'done' && (lr?.enemy_remaining ?? []).length === 0 && <span className="layer__clear">✓ 全歼</span>}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Live log tail */}
        {!settled && (
          <div className="battle__log">
            {(settledLayer?.key_logs ?? layers[revealedLayerCount - 1]?.key_logs ?? []).slice(-3).map((line: string, i: number) => (
              <p key={i} className="battle__logLine">{translateGameText(line)}</p>
            ))}
          </div>
        )}

        {/* Settled: rewards + losses + review */}
        {settled && (
          <div className="battle__outcome">
            <div className="battle__rewards">
              <ReportRewards report={report} />
            </div>
            <ReportLosses report={report} memberByName={props.memberByName} />
            {(report.failure_reasons ?? []).length > 0 && (
              <div className="battle__review">
                <h4>📋 复盘 · 归因</h4>
                <ul>{report.failure_reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
              </div>
            )}
            <details className="battle__fullLog">
              <summary>完整回合日志（{report.turn_logs?.length ?? 0} 条）</summary>
              <ol className="logList">{(report.turn_logs ?? []).map((l, i) => <li key={i}>{translateGameText(l)}</li>)}</ol>
            </details>
          </div>
        )}

        {!settled && (
          <div className="battle__controls">
            <button className="btn btn--ghost btn--sm" onClick={() => setStep(totalSteps - 1)}>⏭ 跳到结算</button>
            <button className="btn btn--ghost btn--sm" onClick={() => setSpeed(s => (s >= 4 ? 1 : s * 2))}>速度 ×{speed}</button>
          </div>
        )}
      </div>
    </div>
  )
}

function layerTypeIcon(type?: string) {
  switch (type) {
    case 'trap': return '🪤'
    case 'battle': return '⚔️'
    default: return '⚔️'
  }
}

function ScoutReport(props: { report: ReportView; skippedAll: boolean }) {
  const lines = (props.report.revealed_mechanics ?? props.report.turn_logs ?? [])
  const [n, setN] = useState(props.skippedAll ? lines.length : 0)
  useEffect(() => {
    if (props.skippedAll) { setN(lines.length); return }
    if (n >= lines.length) return
    const t = window.setTimeout(() => setN(x => x + 1), 650)
    return () => window.clearTimeout(t)
  }, [n, lines.length, props.skippedAll])
  return (
    <div className="results__card">
      <div className="battle battle--scout">
        <div className="battle__banner" style={{ '--res': '#5c9cff' } as CSSProperties}>
          <span className="battle__name">🔭 侦察 · {props.report.dungeon_name}</span>
          <ResultBadge result="scouted" size="lg" />
        </div>
        <div className="scout__lines">
          {lines.slice(0, n).map((l, i) => <p key={i} className="scout__line">{l}</p>)}
          {n < lines.length && <p className="scout__line muted">▍ 分析中…</p>}
        </div>
        <div className="battle__outcome">
          <div className="battle__rewards"><ReportRewards report={props.report} /></div>
          <ReportLosses report={props.report} memberByName={{}} />
        </div>
      </div>
    </div>
  )
}

function RestReport(props: { report: ReportView }) {
  return (
    <div className="results__card">
      <div className="battle battle--rest">
        <div className="battle__banner" style={{ '--res': '#81d4fa' } as CSSProperties}>
          <span className="battle__name">🏕️ 休整日</span>
          <ResultBadge result="rested" size="lg" />
        </div>
        <div className="rest__body">
          <span className="rest__emoji">🔥</span>
          <p>没有安排远征 —— 全队围炉休整、治疗伤势、清除异常状态，并进行轻量训练。</p>
        </div>
        <div className="battle__outcome">
          <div className="battle__rewards"><ReportRewards report={props.report} /></div>
        </div>
      </div>
    </div>
  )
}

/** Rewards block reused by all report types. */
export function ReportRewards(props: { report: ReportView }) {
  const r = props.report.rewards ?? {}
  const mats = r.materials ?? {}
  const eq = r.equipment ?? []
  const empty = !r.gold && !r.exp && Object.keys(mats).length === 0 && eq.length === 0
  return (
    <div className="rewards">
      <h4>🎁 收获</h4>
      {empty && <p className="muted">无奖励。</p>}
      <div className="rewards__chips">
        {!!r.gold && <Chip icon="🪙" tone="accent">金币 +{r.gold}</Chip>}
        {!!r.exp && <Chip icon="✨" tone="info">经验 +{r.exp}</Chip>}
        {Object.entries(mats).map(([k, v]) => <Chip key={k} icon={materialIcon(materialName(k))} tone="muted">{materialName(k)} +{v as number}</Chip>)}
        {eq.map((name: string, i: number) => <Chip key={i} icon="✦" tone="accent">{name}</Chip>)}
      </div>
    </div>
  )
}

export function ReportLosses(props: { report: ReportView; memberByName: Record<string, CharacterView> }) {
  const losses = props.report.losses ?? {}
  const injuries = losses.injuries ?? []
  const dur = losses.durability ?? {}
  const mana = losses.mana ?? {}
  const empty = injuries.length === 0 && Object.keys(dur).length === 0 && Object.keys(mana).length === 0
  return (
    <div className="losses">
      <h4>🩹 损耗</h4>
      {empty && <p className="muted">无明显损失。</p>}
      {injuries.length > 0 && (
        <div className="losses__row">
          {injuries.map((s: string, i: number) => <Chip key={i} icon="💢" tone="danger">{s}</Chip>)}
        </div>
      )}
      {Object.keys(dur).length > 0 && (
        <div className="losses__dur">
          <span className="muted">装备耐久：</span>
          {Object.entries(dur).map(([k, v]) => <span key={k} className="durChip">{k} <em>{v as string}</em></span>)}
        </div>
      )}
      {Object.keys(mana).length > 0 && (
        <div className="losses__dur">
          <span className="muted">剩余法力：</span>
          {Object.entries(mana).map(([k, v]) => <span key={k} className="durChip">{k} <em>{v as string}</em></span>)}
        </div>
      )}
    </div>
  )
}

/** Reusable compact report summary card (for overview / reports list). */
export function ReportSummaryCard(props: { report: ReportView; onClick?: () => void; selected?: boolean }) {
  const r = props.report
  const res = resultMeta(r.result)
  return (
    <button className={cx('reportCard', props.selected && 'is-selected')} onClick={props.onClick}>
      <div className="reportCard__head">
        <ResultBadge result={r.result} size="sm" />
        <b>{r.dungeon_name}</b>
        <span className="muted">第 {r.day} 天{r.team_name ? ` · ${r.team_name}` : ''}</span>
      </div>
      <p className="reportCard__summary">{r.summary}</p>
      <div className="reportCard__meta">
        {r.type === 'challenge' && <Chip icon="⚔️" tone="muted">推进 {r.cleared_layers} 层</Chip>}
        {(r.rewards?.gold ?? 0) > 0 && <Chip icon="🪙" tone="accent">+{r.rewards.gold}</Chip>}
        {(r.rewards?.exp ?? 0) > 0 && <Chip icon="✨" tone="info">+{r.rewards.exp}</Chip>}
      </div>
    </button>
  )
}
