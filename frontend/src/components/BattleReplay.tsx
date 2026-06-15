import { useEffect, useMemo, useState } from 'react'
import type { CSSProperties } from 'react'
import type { CombatEvent, CombatRoundDetail, CombatUnitSnapshot, ReportView } from '../types/game'
import { Bar, HpBar } from './Bar'
import { StatusChip } from './Chips'
import { classMeta, elementMeta, enemyIcon, resultMeta, translateGameText } from '../theme'
import { cx } from '../lib/format'

interface ReplayFrame {
  key: string
  layerIndex: number
  layerName: string
  layerResult?: string
  round?: number
  event?: CombatEvent | null
  party: CombatUnitSnapshot[]
  enemies: CombatUnitSnapshot[]
  text: string
}

export function BattleReplay(props: { report: ReportView; compact?: boolean; autoPlay?: boolean }) {
  const frames = useMemo(() => buildReplayFrames(props.report), [props.report])
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(!!props.autoPlay)
  const [speed, setSpeed] = useState(1)

  useEffect(() => {
    setIndex(0)
    setPlaying(!!props.autoPlay)
  }, [props.report.id, props.autoPlay])

  useEffect(() => {
    if (!playing || frames.length <= 1) return
    const t = window.setTimeout(() => {
      setIndex(i => {
        if (i >= frames.length - 1) {
          setPlaying(false)
          return i
        }
        return i + 1
      })
    }, Math.max(260, (props.compact ? 620 : 820) / speed))
    return () => window.clearTimeout(t)
  }, [frames.length, index, playing, props.compact, speed])

  if (frames.length === 0) {
    return null
  }

  const frame = frames[Math.min(index, frames.length - 1)]
  const res = resultMeta(frame.layerResult || props.report.result)
  const event = frame.event ?? undefined
  const isLast = index >= frames.length - 1

  return (
    <div className={cx('replay', props.compact && 'replay--compact')} style={{ '--res': res.color } as CSSProperties}>
      <div className="replay__top">
        <div className="replay__title">
          <span className="replay__pulse">●</span>
          <b>战斗回放</b>
          <span className="muted">第 {frame.layerIndex} 层 · {frame.layerName}{frame.round ? ` · R${frame.round}` : ''}</span>
        </div>
        <div className="replay__controls">
          <button className="btn btn--ghost btn--sm" onClick={() => setIndex(i => Math.max(0, i - 1))} disabled={index === 0}>←</button>
          <button
            className="btn btn--ghost btn--sm"
            onClick={() => {
              if (isLast) setIndex(0)
              setPlaying(p => !p || isLast)
            }}
            disabled={frames.length <= 1}
          >
            {playing ? '暂停' : isLast ? '重播' : '播放'}
          </button>
          <button className="btn btn--ghost btn--sm" onClick={() => setSpeed(s => (s >= 4 ? 1 : s * 2))}>×{speed}</button>
          <button className="btn btn--ghost btn--sm" onClick={() => setIndex(i => Math.min(frames.length - 1, i + 1))} disabled={isLast}>→</button>
        </div>
      </div>

      <div className="replay__scrub">
        <input
          aria-label="战斗回放进度"
          type="range"
          min={0}
          max={Math.max(0, frames.length - 1)}
          value={index}
          onChange={(e) => { setIndex(Number(e.currentTarget.value)); setPlaying(false) }}
        />
        <span>{index + 1}/{frames.length}</span>
      </div>

      <div className="replay__stage">
        <ReplaySide title="我方" side="party" units={frame.party} event={event} />
        <div className="replay__lane">
          {event && <span key={frame.key} className={cx('replay__projectile', projectileClass(event))}>{eventIcon(event)}</span>}
          <span className="replay__vs">VS</span>
        </div>
        <ReplaySide title="敌方" side="enemy" units={frame.enemies} event={event} />
      </div>

      <div key={frame.key + ':text'} className={cx('replay__event', eventTone(event))}>
        <span className="replay__eventIcon">{event ? eventIcon(event) : '⚔️'}</span>
        <span>{translateGameText(frame.text)}</span>
      </div>
    </div>
  )
}

function ReplaySide(props: { title: string; side: 'party' | 'enemy'; units: CombatUnitSnapshot[]; event?: CombatEvent }) {
  return (
    <div className={cx('replaySide', `replaySide--${props.side}`)}>
      <div className="replaySide__label">{props.title}</div>
      <div className="replayGrid">
        {props.units.map(unit => <ReplayUnit key={unit.id} unit={unit} event={props.event} />)}
      </div>
    </div>
  )
}

function ReplayUnit(props: { unit: CombatUnitSnapshot; event?: CombatEvent }) {
  const { unit, event } = props
  const activeActor = !!event?.actor?.id && event.actor.id === unit.id
  const activeTarget = (!!event?.target?.id && event.target.id === unit.id) || (!!event?.redirect_to?.id && event.redirect_to.id === unit.id)
  const dead = (unit.hp ?? 0) <= 0
  const icon = unit.side === 'party' ? classMeta(unit.class_id || '').icon : enemyIcon(unit.tags ?? [], unit.name)
  const style = cellStyle(unit.cell)
  const amount = activeTarget ? event?.amount : undefined
  const floatTone = event?.type === 'heal' ? 'good' : event?.type?.includes('miss') ? 'muted' : 'danger'
  const maxMana = Number(unit.max_mana ?? 0)
  const mana = Math.max(0, Math.min(maxMana, Number(unit.mana ?? maxMana)))
  return (
    <div
      className={cx('replayUnit', activeActor && 'is-acting', activeTarget && 'is-target', dead && 'is-dead')}
      style={style}
      title={`${unit.name} · 生命 ${unit.hp}/${unit.max_hp}${maxMana > 0 ? ` · 法力 ${mana}/${maxMana}` : ''}`}
    >
      <span className="replayUnit__icon">{icon}</span>
      <div className="replayUnit__body">
        <div className="replayUnit__name">
          <b>{unit.name}</b>
          {unit.class_name && <span>{unit.class_name}</span>}
        </div>
        <HpBar cur={unit.hp} max={unit.max_hp} height={8} showText={false} />
        <div className="replayUnit__hp">{unit.hp}/{unit.max_hp}</div>
        {maxMana > 0 && (
          <div className="replayUnit__mana" title={`法力 ${mana}/${maxMana}`}>
            <Bar value={mana} max={maxMana} height={4} color="#5c9cff" />
          </div>
        )}
        {(unit.statuses ?? []).length > 0 && (
          <div className="replayUnit__statuses">
            {(unit.statuses ?? []).slice(0, 3).map((s, i) => <StatusChip key={`${s.type}-${i}`} type={s.type} duration={s.duration} potency={s.potency} />)}
          </div>
        )}
      </div>
      {activeTarget && (
        <span key={`${event?.seq}-${unit.id}`} className={cx('replayFloat', `replayFloat--${floatTone}`)}>
          {event?.type === 'miss' ? 'MISS' : amount ? `${event?.type === 'heal' ? '+' : '-'}${amount}` : eventIcon(event)}
        </span>
      )}
    </div>
  )
}

function buildReplayFrames(report: ReportView): ReplayFrame[] {
  const frames: ReplayFrame[] = []
  const layers = report.layer_results ?? []
  for (const layer of layers) {
    const rounds: CombatRoundDetail[] = layer.round_details ?? []
    let party = cloneUnits(layer.entry_party ?? layer.party_start ?? rounds[0]?.start?.party ?? report.initial_party ?? [])
    let enemies = cloneUnits(layer.enemy_start ?? rounds[0]?.start?.enemies ?? [])
    frames.push({
      key: `l${layer.index}-start`,
      layerIndex: layer.index ?? frames.length + 1,
      layerName: layer.name ?? `第 ${layer.index ?? frames.length + 1} 层`,
      layerResult: layer.result,
      party: cloneUnits(party),
      enemies: cloneUnits(enemies),
      text: `进入 ${layer.name ?? '未知层'}，队伍展开阵型。`,
    })
    for (const event of (layer.pre_events ?? []) as CombatEvent[]) {
      applyEvent(party, enemies, event)
      frames.push({
        key: `l${layer.index}-pre-${event.seq ?? frames.length}`,
        layerIndex: layer.index,
        layerName: layer.name,
        layerResult: layer.result,
        event,
        party: cloneUnits(party),
        enemies: cloneUnits(enemies),
        text: event.text,
      })
    }
    for (const round of rounds) {
      party = cloneUnits(round.start?.party ?? party)
      enemies = cloneUnits(round.start?.enemies ?? enemies)
      if ((round.events ?? []).length === 0) {
        frames.push({
          key: `l${layer.index}-r${round.round}-empty`,
          layerIndex: layer.index,
          layerName: layer.name,
          layerResult: layer.result,
          round: round.round,
          party: cloneUnits(round.end?.party ?? party),
          enemies: cloneUnits(round.end?.enemies ?? enemies),
          text: `第 ${round.round} 回合结束。`,
        })
        continue
      }
      for (const event of round.events ?? []) {
        applyEvent(party, enemies, event)
        frames.push({
          key: `l${layer.index}-r${round.round}-e${event.seq ?? frames.length}`,
          layerIndex: layer.index,
          layerName: layer.name,
          layerResult: layer.result,
          round: round.round,
          event,
          party: cloneUnits(party),
          enemies: cloneUnits(enemies),
          text: event.text,
        })
      }
      party = cloneUnits(round.end?.party ?? party)
      enemies = cloneUnits(round.end?.enemies ?? enemies)
      frames.push({
        key: `l${layer.index}-r${round.round}-end`,
        layerIndex: layer.index,
        layerName: layer.name,
        layerResult: layer.result,
        round: round.round,
        party: cloneUnits(party),
        enemies: cloneUnits(enemies),
        text: `第 ${round.round} 回合结束：我方 ${aliveCount(party)} 人可行动，敌方 ${aliveCount(enemies)} 个目标存活。`,
      })
    }
    if (rounds.length === 0 && (layer.party_end || layer.enemy_end)) {
      frames.push({
        key: `l${layer.index}-end`,
        layerIndex: layer.index,
        layerName: layer.name,
        layerResult: layer.result,
        party: cloneUnits(layer.party_end ?? party),
        enemies: cloneUnits(layer.enemy_end ?? enemies),
        text: `${layer.name ?? '本层'} 结算：${resultMeta(layer.result).label}。`,
      })
    }
  }
  return frames
}

function cloneUnits(units: CombatUnitSnapshot[]): CombatUnitSnapshot[] {
  return (units ?? []).map(u => ({ ...u, statuses: (u.statuses ?? []).map(s => ({ ...s })), tags: [...(u.tags ?? [])] }))
}

function applyEvent(party: CombatUnitSnapshot[], enemies: CombatUnitSnapshot[], event: CombatEvent) {
  const units = [...party, ...enemies]
  const target = event.target?.id ? units.find(u => u.id === event.target?.id) : undefined
  const actor = event.actor?.id ? units.find(u => u.id === event.actor?.id) : undefined
  if (target) {
    if (typeof event.target_hp_after === 'number') target.hp = Math.max(0, event.target_hp_after)
    if (event.type === 'down') target.hp = 0
    if (event.target_statuses) target.statuses = event.target_statuses.map(s => ({ ...s }))
  }
  if (actor && event.actor_statuses) actor.statuses = event.actor_statuses.map(s => ({ ...s }))
  if (actor && typeof event.actor_mana_after === 'number') actor.mana = Math.max(0, event.actor_mana_after)
}

function aliveCount(units: CombatUnitSnapshot[]): number {
  return units.filter(u => u.hp > 0).length
}

function cellStyle(cell?: string): CSSProperties {
  const m = /^r(\d)c(\d)$/.exec(cell ?? '')
  if (!m) return {}
  return { gridRow: Number(m[1]) + 1, gridColumn: Number(m[2]) + 1 }
}

function eventIcon(event?: CombatEvent) {
  if (!event) return '⚔️'
  if (event.type === 'heal') return '💚'
  if (event.type === 'mana_spend') return '🔮'
  if (event.type === 'cleanse') return '✨'
  if (event.type === 'guard' || event.type === 'guard_redirect') return '🛡️'
  if (event.type === 'miss') return '💨'
  if (event.type === 'down') return '💀'
  if (event.type === 'retreat') return '🏳️'
  if (event.type.includes('status')) return '🌀'
  const dt = event.damage_types?.[0] ?? event.damage_type
  return dt ? elementMeta(dt).icon : '⚔️'
}

function projectileClass(event: CombatEvent) {
  const fromEnemy = event.actor?.side === 'enemy'
  return cx(fromEnemy ? 'from-enemy' : 'from-party', (event.type === 'heal' || event.type === 'mana_spend') && 'is-heal', event.type === 'miss' && 'is-miss')
}

function eventTone(event?: CombatEvent) {
  if (!event) return ''
  if (event.type === 'heal' || event.type === 'cleanse' || event.type === 'guard') return 'is-good'
  if (event.type === 'miss' || event.type === 'mana_spend') return 'is-muted'
  if (event.type === 'retreat' || event.type === 'down') return 'is-warn'
  return 'is-danger'
}
