import type { ReactNode } from 'react'
import { cx } from '../lib/format'
import { elementMeta, rarityMeta, resultMeta, statusMeta, type ElementKey } from '../theme'

/** A rounded pill with optional icon + tone coloring. */
export function Chip(props: { children: ReactNode; icon?: string; tone?: 'default' | 'accent' | 'danger' | 'good' | 'warn' | 'info' | 'muted'; className?: string; title?: string }) {
  const tone = props.tone ?? 'default'
  return (
    <span className={cx('chip', `chip--${tone}`, props.className)} title={props.title}>
      {props.icon && <span className="chip__icon">{props.icon}</span>}
      <span>{props.children}</span>
    </span>
  )
}

/** A single element/damage-type chip. */
export function ElementChip(props: { type: string; value?: number | string; title?: string }) {
  const m = elementMeta(props.type)
  return (
    <span className="chip chip--element" title={props.title ?? m.label} style={{ borderColor: m.color + '66', color: m.color }}>
      <span className="chip__icon">{m.icon}</span>
      <span>{m.label}{props.value !== undefined ? ` ${props.value}` : ''}</span>
    </span>
  )
}

/** Resistance chip (e.g. physical +8, poison 30%). */
export function ResistChip(props: { type: ElementKey; value: number }) {
  const m = elementMeta(props.type)
  const v = props.value
  const tone = v > 0 ? 'good' : v < 0 ? 'danger' : 'muted'
  return (
    <span className={`chip chip--resist chip--${tone}`} title={`${m.label}抗性`}>
      <span className="chip__icon">{m.icon}</span>
      <span>{m.label}</span>
      <b>{v > 0 ? '+' : ''}{v}</b>
    </span>
  )
}

/** Rarity-gated label/border color used on equipment. */
export function RarityTag(props: { rarity?: string }) {
  const m = rarityMeta(props.rarity)
  return <span className="chip chip--rarity" style={{ borderColor: m.color + '88', color: m.color }}>{m.label}</span>
}

export function StatusChip(props: { type: string; duration?: number; potency?: number }) {
  const m = statusMeta(props.type)
  const tone = m.tone === 'good' ? 'good' : m.tone === 'bad' ? 'danger' : 'muted'
  return (
    <span className={`chip chip--${tone}`} title={`${m.label}${props.potency ? ` · 强度 ${props.potency}` : ''}`}>
      <span className="chip__icon">{m.icon}</span>
      <span>{m.label}{props.duration ? ` ${props.duration}` : ''}</span>
    </span>
  )
}

export function ResultBadge(props: { result: string; size?: 'sm' | 'md' | 'lg' }) {
  const m = resultMeta(props.result)
  return (
    <span className={cx('resultBadge', `resultBadge--${props.size ?? 'md'}`)} style={{ color: m.color, borderColor: m.color + '66', background: m.color + '1a' }}>
      <span>{m.icon}</span>
      <span>{m.label}</span>
    </span>
  )
}

/** Danger level shown as skull pips + numeric. */
export function DangerMeter(props: { level: number }) {
  const n = Math.max(0, Math.min(8, props.level))
  return (
    <span className="danger" title={`危险等级 ${props.level}`}>
      {Array.from({ length: n }).map((_, i) => <span key={i} className="danger__pip">⚠</span>)}
      {!n && <span className="muted">—</span>}
      <b className="danger__num">{props.level}</b>
    </span>
  )
}

/** Expedition points rendered as filled/empty pips. */
export function PointPips(props: { left: number; total?: number }) {
  const total = props.total ?? 2
  return (
    <span className="pips" title={`剩余远征次数 ${props.left}/${total}`}>
      {Array.from({ length: total }).map((_, i) => (
        <span key={i} className={cx('pips__pip', i < props.left && 'is-filled')}>◆</span>
      ))}
    </span>
  )
}
