import type { CSSProperties } from 'react'
import type { EquipmentItem } from '../types/game'
import { rarityMeta, SLOT_ICON, SLOT_LABEL, ELEMENTS, statLabel, specialEffectLabel } from '../theme'
import { cx, num } from '../lib/format'
import { RarityTag } from './Chips'
import { EquipmentHover } from './EquipmentTooltip'

/** Renders an equipment item as a rarity-gated card. In compact mode (or when
 * `tooltip` is set), hovering shows a full-detail tooltip via a portal. */
export function EquipmentCard(props: {
  item: EquipmentItem
  onClick?: () => void
  actionLabel?: string
  actionIcon?: string
  disabled?: boolean
  selected?: boolean
  equippedName?: string
  affordable?: boolean
  cost?: number
  showCost?: boolean
  compact?: boolean
  /** Force the hover tooltip on even for non-compact cards. */
  tooltip?: boolean
}) {
  const m = rarityMeta(props.item.rarity)
  const stats = props.item.stats ?? {}
  const resists = props.item.resistances ?? {}
  const affixes = props.item.affixes ?? []
  const enchants = props.item.enchants ?? []
  const kind = props.item.item_kind_label ?? (props.item.item_kind === 'special' ? '特殊装备' : props.item.item_kind === 'special_base' ? '特别装备' : '基础装备')
  const level = props.item.item_level ? ` · Lv.${props.item.item_level}` : ''
  const showTooltip = props.tooltip || props.compact
  const card = (
    <div
      className={cx('eqCard', `eqCard--${m.key}`, props.selected && 'is-selected', props.compact && 'is-compact')}
      style={{ '--rare': m.color, '--glow': m.glow } as CSSProperties}
      onClick={props.onClick}
      role={props.onClick ? 'button' : undefined}
    >
      <div className="eqCard__head">
        <span className="eqCard__slot" title={SLOT_LABEL[props.item.slot]}>{SLOT_ICON[props.item.slot] ?? '✦'}</span>
        <div className="eqCard__title">
          <b>{props.item.name}</b>
          <span className="eqCard__sub"><RarityTag rarity={props.item.rarity} /> {kind} · {SLOT_LABEL[props.item.slot] ?? props.item.slot}{level}</span>
        </div>
        {props.showCost && props.cost !== undefined && (
          <span className={cx('eqCard__cost', props.affordable === false && 'is-poor')}>🪙 {num(props.cost)}</span>
        )}
      </div>

      {!props.compact && (
        <div className="eqCard__body">
          {Object.keys(stats).length > 0 && (
            <div className="eqCard__stats">
              {Object.entries(stats).map(([k, v]) => (
                <span key={k} className="eqStat"><b>+{v}</b> {statLabel(k, true)}</span>
              ))}
            </div>
          )}
          {Object.keys(resists).some(k => resists[k]) && (
            <div className="eqCard__resists">
              {Object.entries(resists).filter(([, v]) => v).map(([k, v]) => {
                const em = ELEMENTS[k as keyof typeof ELEMENTS]
                return <span key={k} className="eqResist" style={{ color: em?.color }}>{em?.icon} {em?.label ?? k} +{v}</span>
              })}
            </div>
          )}
          {(props.item.special_effects ?? []).length > 0 && (
            <div className="eqCard__effects">
              {props.item.special_effects.map(e => <span key={e} className="eqEffect">✦ {specialEffectLabel(e)}</span>)}
            </div>
          )}
          {affixes.length > 0 && (
            <div className="eqCard__effects">
              {affixes.map(a => <span key={a.id} className="eqEffect">◆ {a.name}</span>)}
            </div>
          )}
          {enchants.length > 0 && (
            <div className="eqCard__effects">
              {enchants.map(a => <span key={a.id} className="eqEffect eqEffect--ench">🌀 {a.name}</span>)}
            </div>
          )}
          {props.item.durability !== undefined && (
            <div className="eqCard__dur">耐久 {props.item.durability}/{props.item.max_durability}</div>
          )}
          {props.equippedName && <div className="eqCard__equipped">已装备 · {props.equippedName}</div>}
        </div>
      )}

      {props.actionLabel && (
        <button className={cx('btn btn--sm', props.disabled ? 'btn--ghost' : 'btn--accent')} onClick={(e) => { e.stopPropagation(); props.onClick?.() }} disabled={props.disabled}>
          {props.actionIcon} {props.actionLabel}
        </button>
      )}
    </div>
  )
  if (showTooltip) {
    return <EquipmentHover item={props.item}>{card}</EquipmentHover>
  }
  return card
}
