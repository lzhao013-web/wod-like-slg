import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import type { CharacterView, PartyView } from '../types/game'
import { classMeta, compatibleEquipmentSlots, itemFitsEquipmentSlot, rarityMeta, SLOT_ICON, SLOT_LABEL } from '../theme'
import { cx } from '../lib/format'
import { EquipmentCard } from './EquipmentCard'
import { EquipmentHover } from './EquipmentTooltip'

// Body-worn slots laid out around the silhouette (backpack handled separately in the tray).
const TRAY_SLOTS = ['backpack_1', 'backpack_2', 'backpack_3', 'backpack_4'] as const

/**
 * Diablo-style paperdoll: a dark class-tinted silhouette ringed by equipment
 * slots, with a backpack tray underneath. Pass `onEquip` for the interactive
 * editor (selecting a slot reveals swap/unequip options); omit it for a
 * read-only display.
 */
export function Paperdoll(props: {
  member: CharacterView
  party: PartyView
  onEquip?: (charId: string, itemId: string | null, slot?: string) => void
  busy?: boolean
  readOnly?: boolean
  /** Hide the built-in swap-detail panel (use when the parent renders its own
   * equip source, e.g. an InventoryGrid beside the paperdoll). */
  hideDetail?: boolean
  /** Controlled selected slot for parent-rendered equipment libraries. */
  activeSlot?: string
  onActiveSlotChange?: (slot: string) => void
}) {
  const m = props.member
  const cm = classMeta(m.class_id)
  const editable = !!props.onEquip && !props.readOnly
  const [innerActiveSlot, setInnerActiveSlot] = useState<string>('')
  const activeSlot = props.activeSlot ?? innerActiveSlot

  useEffect(() => {
    if (props.activeSlot === undefined) setInnerActiveSlot('')
  }, [m.id, props.activeSlot])

  function setActiveSlot(next: string) {
    setInnerActiveSlot(next)
    props.onActiveSlotChange?.(next)
  }

  const itemById = (id: string | null) => (id ? props.party.inventory.find(i => i.instance_id === id) : undefined)

  function renderSlot(slot: string) {
    const equippedId = m.equipment?.[slot] ?? null
    const item = itemById(equippedId)
    const rm = item ? rarityMeta(item.rarity) : null
    const active = activeSlot === slot
    const occupiedByTwoHand = slot === 'off_hand' && itemById(m.equipment?.main_hand ?? null)?.slot === 'two_hand'
    const slotBtn = (
      <button
        type="button"
        key={slot}
        className={cx(
          'pdSlot',
          item && `pdSlot--${rm!.key}`,
          item && 'is-filled',
          active && 'is-active',
          occupiedByTwoHand && 'is-blocked',
        )}
        style={(item ? { '--rare': rm!.color, '--glow': rm!.glow } : {}) as CSSProperties}
        onClick={() => editable && setActiveSlot(active ? '' : slot)}
        title={occupiedByTwoHand ? `${SLOT_LABEL[slot]}（双手占用）` : item ? item.name : SLOT_LABEL[slot]}
        disabled={!editable}
      >
        <span className="pdSlot__icon">{SLOT_ICON[slot] ?? '✦'}</span>
        <span className="pdSlot__name">{item ? item.name : SLOT_LABEL[slot]}</span>
        {occupiedByTwoHand && <span className="pdSlot__note">双手占用</span>}
      </button>
    )
    // Wrap filled slots in a hover tooltip (read-only in CharacterSheet too).
    return item ? <EquipmentHover key={slot} item={item}>{slotBtn}</EquipmentHover> : slotBtn
  }

  // Active slot detail panel (interactive mode only).
  const active = editable && activeSlot
  const activeEquippedId = active ? (m.equipment?.[activeSlot] ?? null) : null
  const activeItem = active ? itemById(activeEquippedId) : undefined
  const activeOptions = active
    ? props.party.inventory.filter(
        (i) => itemFitsEquipmentSlot(i.slot, activeSlot) && (!i.equipped_by || i.equipped_by === m.id) && i.instance_id !== activeEquippedId,
      )
    : []

  return (
    <div className={cx('paperdoll', props.readOnly && 'is-readonly', props.hideDetail && 'is-detail-hidden')}>
      <div className="paperdoll__stage">
        <div className="paperdoll__cols">
          <div className="paperdoll__left">
            {['main_hand', 'hands', 'waist', 'ring_1'].map(renderSlot)}
          </div>

          <div className="paperdoll__center">
            <div className="paperdoll__headRow">{renderSlot('head')}</div>
            <div className="paperdoll__figure" style={{ '--accent': cm.accent } as CSSProperties}>
              <span className="paperdoll__figureGlow" />
              <span className="paperdoll__silhouette">
                <span className="pdSilhouette__head" />
                <span className="pdSilhouette__torso" />
                <span className="pdSilhouette__armL" />
                <span className="pdSilhouette__armR" />
                <span className="pdSilhouette__legL" />
                <span className="pdSilhouette__legR" />
              </span>
              <span className="paperdoll__badge">{cm.icon}</span>
              <span className="paperdoll__className">{cm.roleShort}</span>
            </div>
            <div className="paperdoll__neckRow">{renderSlot('necklace')}</div>
          </div>

          <div className="paperdoll__right">
            {['body', 'off_hand', 'feet', 'ring_2'].map(renderSlot)}
          </div>
        </div>

        <div className="paperdoll__tray">
          <span className="paperdoll__trayLabel">🎒 背包</span>
          <div className="paperdoll__traySlots">{TRAY_SLOTS.map(renderSlot)}</div>
        </div>
      </div>

      {editable && !props.hideDetail && (
        <div className="paperdoll__detail">
          {!active && <p className="paperdoll__hint muted">点击左侧槽位查看与更换装备</p>}
          {active && (
            <>
              <div className="paperdoll__detailHead">
                <span className="paperdoll__detailIcon">{SLOT_ICON[activeSlot]}</span>
                <b>{SLOT_LABEL[activeSlot]}</b>
              </div>
              {activeItem ? (
                <EquipmentCard
                  item={activeItem}
                  compact
                  actionLabel="卸下"
                  actionIcon="↩"
                  onClick={() => {
                    props.onEquip!(m.id, null, activeSlot)
                    setActiveSlot('')
                  }}
                />
              ) : (
                <div className="paperdoll__detailEmpty muted">{activeSlot === 'off_hand' && itemById(m.equipment?.main_hand ?? null)?.slot === 'two_hand' ? '主手为双手武器，副手已占用' : '该槽位未装备'}</div>
              )}
              {activeOptions.length > 0 && (
                <div className="paperdoll__swap">
                  <span className="muted">可替换：</span>
                  {activeOptions.map((i) => (
                    <EquipmentCard
                      key={i.instance_id}
                      item={i}
                      compact
                      actionLabel="装备"
                      actionIcon="⬆"
                      onClick={() => {
                        const targetSlot = compatibleEquipmentSlots(i.slot).includes(activeSlot) ? activeSlot : undefined
                        props.onEquip!(m.id, i.instance_id, targetSlot)
                      }}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
