import type { CSSProperties } from 'react'
import type { CharacterView } from '../types/game'
import { classMeta } from '../theme'
import { cx } from '../lib/format'

const INJURY_TONE: Record<string, string> = { healthy: 'good', 轻伤: 'warn', 重伤: 'danger' }

/** A circular class portrait with level badge + injury ring. */
export function CharacterAvatar(props: { ch: Pick<CharacterView, 'class_id' | 'level' | 'injury_state'>; size?: number; dimmed?: boolean }) {
  const m = classMeta(props.ch.class_id)
  const size = props.size ?? 48
  const injured = props.ch.injury_state && props.ch.injury_state !== 'healthy'
  const ring = INJURY_TONE[props.ch.injury_state] ?? 'neutral'
  return (
    <span
      className={cx('avatar', `avatar--${ring}`, injured && 'is-injured', props.dimmed && 'is-dimmed')}
      style={{ width: size, height: size, fontSize: size * 0.5, '--accent': m.accent } as CSSProperties}
      title={`${m.roleShort} Lv.${props.ch.level}`}
    >
      <span className="avatar__icon">{m.icon}</span>
      <span className="avatar__lvl">{props.ch.level}</span>
    </span>
  )
}
