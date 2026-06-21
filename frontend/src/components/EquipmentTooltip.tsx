import { useEffect, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import type { EquipmentItem } from '../types/game'
import { EquipmentCard } from './EquipmentCard'

const SHOW_DELAY = 120   // ms before the tooltip appears (avoids flicker on sweep)
const HIDE_DELAY = 90    // ms before it disappears (lets the cursor cross the gap)
const CURSOR_GAP = 16    // px offset from the cursor so the tip doesn't cover it

/**
 * Wraps any element so that hovering it shows a full-detail equipment tooltip
 * that follows the cursor. The tooltip is rendered into a portal at the
 * document root so it floats above every overlay (CharacterSheet, talent modal,
 * toasts). z-index 90.
 *
 * Positioning is cursor-relative (the wrapper uses `display:inline-block` so it
 * has a real box and hover works), and the tooltip node is moved directly via a
 * ref on mousemove — re-rendering the inner EquipmentCard on every pixel of
 * cursor movement would be wasteful and janky.
 */
export function EquipmentHover(props: { item: EquipmentItem; children: ReactNode; className?: string }) {
  const wrapRef = useRef<HTMLSpanElement>(null)
  const tipRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const showTimer = useRef<number | undefined>(undefined)
  const hideTimer = useRef<number | undefined>(undefined)

  const clearTimers = () => {
    if (showTimer.current) { window.clearTimeout(showTimer.current); showTimer.current = undefined }
    if (hideTimer.current) { window.clearTimeout(hideTimer.current); hideTimer.current = undefined }
  }

  const placeAt = (clientX: number, clientY: number) => {
    const tip = tipRef.current
    if (!tip) return
    const tw = tip.offsetWidth || 280
    const th = tip.offsetHeight || 260
    // Default to the bottom-right of the cursor; flip if it would overflow.
    let left = clientX + CURSOR_GAP
    let top = clientY + CURSOR_GAP
    if (left + tw > window.innerWidth - 8) left = clientX - tw - CURSOR_GAP
    if (top + th > window.innerHeight - 8) top = clientY - th - CURSOR_GAP
    left = Math.max(8, left)
    top = Math.max(8, top)
    tip.style.left = `${left}px`
    tip.style.top = `${top}px`
  }

  const handleEnter = () => {
    if (hideTimer.current) { window.clearTimeout(hideTimer.current); hideTimer.current = undefined }
    if (open) return
    showTimer.current = window.setTimeout(() => setOpen(true), SHOW_DELAY)
  }

  const handleMove = (e: React.MouseEvent) => {
    // Only position once the tooltip is mounted; before that there's no node.
    if (tipRef.current) placeAt(e.clientX, e.clientY)
  }

  const handleLeave = () => {
    if (showTimer.current) { window.clearTimeout(showTimer.current); showTimer.current = undefined }
    hideTimer.current = window.setTimeout(() => setOpen(false), HIDE_DELAY)
  }

  // Once open, reposition at the last known cursor location (the portal mounts
  // on the tick after setOpen(true), so placeAt ran into a null ref the first
  // time). We read the cursor from the wrapper's bounding box as a fallback.
  useEffect(() => {
    if (!open) return
    const onMove = (e: MouseEvent) => placeAt(e.clientX, e.clientY)
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [open])

  useEffect(() => () => clearTimers(), [])

  return (
    <span
      ref={wrapRef}
      className={props.className}
      onMouseEnter={handleEnter}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      style={{ display: 'inline-block' }}
    >
      {props.children}
      {open && createPortal(
        <div
          ref={tipRef}
          className="eqTooltip"
          // initial position fixed up by the effect/mousemove; keep on-screen
          style={{ top: -9999, left: -9999 }}
        >
          <EquipmentCard item={props.item} />
        </div>,
        document.body,
      )}
    </span>
  )
}
