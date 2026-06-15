import { hpColor } from '../lib/format'
import { cx } from '../lib/format'

/** A horizontal bar (HP / stat / progress). Color can be derived or explicit. */
export function Bar(props: {
  value: number
  max?: number
  fraction?: number
  height?: number
  color?: string
  track?: string
  glow?: boolean
  className?: string
  animate?: boolean
}) {
  const frac = props.fraction ?? Math.max(0, Math.min(1, props.value / Math.max(1, props.max ?? 1)))
  const color = props.color ?? hpColor(frac)
  return (
    <div className={cx('bar', props.className)} style={{ height: props.height ?? 10, background: props.track }}>
      <div
        className="bar__fill"
        style={{
          width: `${frac * 100}%`,
          background: `linear-gradient(180deg, ${color}, ${shade(color, -18)})`,
          boxShadow: props.glow ? `0 0 10px ${color}66` : undefined,
          transition: props.animate === false ? 'none' : 'width .55s cubic-bezier(.22,.61,.36,1), background .4s',
        }}
      />
    </div>
  )
}

/** Health bar with current/max text overlay. */
export function HpBar(props: { cur: number; max: number; height?: number; showText?: boolean; animate?: boolean }) {
  const frac = props.max > 0 ? props.cur / props.max : 0
  const dead = props.cur <= 0
  return (
    <div className="hp">
      <div className="hp__bar">
        <Bar value={props.cur} max={props.max} height={props.height ?? 12} glow animate={props.animate} />
        {!dead && props.showText !== false && (
          <span className="hp__text">{Math.round(props.cur)}<span className="hp__max">/{props.max}</span></span>
        )}
        {dead && <span className="hp__text hp__text--dead">已倒下</span>}
      </div>
    </div>
  )
}

// Darken/lighten a hex color by a percentage (-100..100).
function shade(hex: string, amt: number): string {
  const h = hex.replace('#', '')
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h
  const num = parseInt(full, 16)
  if (!Number.isFinite(num)) return hex
  let r = (num >> 16) & 0xff, g = (num >> 8) & 0xff, b = num & 0xff
  const adj = (c: number) => Math.max(0, Math.min(255, Math.round(c + (amt / 100) * 255)))
  r = adj(r); g = adj(g); b = adj(b)
  return `rgb(${r},${g},${b})`
}
