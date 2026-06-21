import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import type { QuestGuideAction, QuestGuidePlacement, QuestGuideStep } from '../types/game'
import { cx } from '../lib/format'

export interface ActiveGuide {
  id: string
  title: string
  subtitle?: string
  questId?: string
  completeObjectiveId?: string
  steps: QuestGuideStep[]
}

interface SpotlightBox {
  left: number
  top: number
  width: number
  height: number
}

const SPOTLIGHT_PAD = 8
const MIN_SPOTLIGHT_SIZE = 24
const MAX_SPOTLIGHT_WIDTH = 520
const MAX_SPOTLIGHT_HEIGHT = 280
const POPOVER_WIDTH = 380
const VIEWPORT_GAP = 16

export function GuidedTour(props: {
  guide: ActiveGuide | null
  onClose: () => void
  onNavigate?: (nav: string) => void
  onCompleteObjective?: (questId: string, objectiveId: string) => Promise<void> | void
}) {
  const { guide } = props
  const [index, setIndex] = useState(0)
  const [box, setBox] = useState<SpotlightBox | null>(null)
  const [targetMissing, setTargetMissing] = useState(false)
  const [runningAction, setRunningAction] = useState(false)
  const completedObjective = useRef(false)

  const steps = guide?.steps ?? []
  const step = steps[index]
  const total = steps.length
  const canBack = index > 0
  const isLast = index >= total - 1

  const targetSelector = step?.target
  const popoverStyle = useMemo(() => getPopoverStyle(box, step?.placement ?? 'auto'), [box, step?.placement])

  useEffect(() => {
    setIndex(0)
    completedObjective.current = false
  }, [guide?.id])

  useLayoutEffect(() => {
    if (!guide || !step) return
    let cancelled = false
    const measure = () => {
      if (cancelled) return
      const nextBox = measureTarget(step.target)
      if (!cancelled) {
        setBox(nextBox)
        setTargetMissing(!!step.target && !nextBox)
      }
    }
    const target = getTargetElement(step.target)
    target?.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' })
    measure()
    const timers = [window.setTimeout(measure, 80), window.setTimeout(measure, 280)]
    return () => {
      cancelled = true
      timers.forEach(window.clearTimeout)
    }
  }, [guide, step, targetSelector])

  useEffect(() => {
    if (!guide || !step) return
    const update = () => {
      const nextBox = measureTarget(step.target)
      setBox(nextBox)
      setTargetMissing(!!step.target && !nextBox)
    }
    window.addEventListener('resize', update)
    window.addEventListener('scroll', update, true)
    return () => {
      window.removeEventListener('resize', update)
      window.removeEventListener('scroll', update, true)
    }
  }, [guide, step])

  useEffect(() => {
    if (!guide) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') props.onClose()
      if (e.key === 'ArrowLeft' && canBack) setIndex(i => Math.max(0, i - 1))
      if (e.key === 'ArrowRight' && !runningAction) void next()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [guide, canBack, runningAction])

  if (!guide || !step || total === 0) return null

  async function completeObjectiveIfNeeded() {
    if (!guide?.questId || !guide.completeObjectiveId || completedObjective.current) return
    completedObjective.current = true
    await props.onCompleteObjective?.(guide.questId, guide.completeObjectiveId)
  }

  async function finish() {
    setRunningAction(true)
    try {
      await completeObjectiveIfNeeded()
      props.onClose()
    } finally {
      setRunningAction(false)
    }
  }

  async function next() {
    if (isLast) return finish()
    setIndex(i => Math.min(total - 1, i + 1))
  }

  async function runAction(action: QuestGuideAction) {
    setRunningAction(true)
    try {
      if (action.type === 'navigate' && action.nav) {
        props.onNavigate?.(action.nav)
      } else if (action.type === 'click_target') {
        const el = getTargetElement(action.target || step.target)
        el?.click()
      } else if (action.type === 'complete_objective') {
        const objectiveId = action.objective_id || guide?.completeObjectiveId
        if (guide?.questId && objectiveId) {
          completedObjective.current = true
          await props.onCompleteObjective?.(guide.questId, objectiveId)
        }
      }
      if (action.advance !== false) {
        window.setTimeout(() => { void next() }, 220)
      }
    } finally {
      window.setTimeout(() => setRunningAction(false), 240)
    }
  }

  const primaryLabel = isLast
    ? (guide.completeObjectiveId ? '完成导览并标记已读' : '完成导览')
    : (step.action ? '不操作，下一步' : '下一步')

  return (
    <div className="guideLayer" role="dialog" aria-modal="true" aria-label={guide.title}>
      <GuideMasks box={box} />
      {box && <div className="guideSpotlight" style={boxStyle(box)} />}

      <article className={cx('guidePopover', !box && 'guidePopover--center')} style={popoverStyle}>
        <header className="guidePopover__head">
          <span className="guidePopover__kicker">德尔塔战术学院</span>
          <button className="guidePopover__close" type="button" onClick={props.onClose} aria-label="关闭导览">✕</button>
        </header>

        <div className="guidePopover__progress">
          <b>{guide.title}</b>
          <span>{index + 1}/{total}</span>
        </div>
        {guide.subtitle && <p className="guidePopover__subtitle">{guide.subtitle}</p>}

        <h3>{step.title}</h3>
        <p>{step.body}</p>
        {targetMissing && (
          <p className="guidePopover__missing">
            当前目标暂未出现在界面上；你可以先点击下方动作按钮，或切换到对应界面后继续。
          </p>
        )}
        {(step.tips?.length ?? 0) > 0 && (
          <ul className="guidePopover__tips">
            {step.tips!.map((tip, i) => <li key={i}>{tip}</li>)}
          </ul>
        )}

        <footer className="guidePopover__foot">
          <button className="btn btn--ghost btn--sm" type="button" onClick={props.onClose}>跳过</button>
          <button className="btn btn--ghost btn--sm" type="button" disabled={!canBack || runningAction} onClick={() => setIndex(i => Math.max(0, i - 1))}>上一步</button>
          {step.action && (
            <button className="btn btn--accent btn--sm" type="button" disabled={runningAction} onClick={() => void runAction(step.action!)}>
              {step.action.label ?? actionLabel(step.action)}
            </button>
          )}
          <button className="btn btn--primary btn--sm" type="button" disabled={runningAction} onClick={() => void next()}>
            {primaryLabel}
          </button>
        </footer>
      </article>
    </div>
  )
}

function GuideMasks({ box }: { box: SpotlightBox | null }) {
  if (!box) return <div className="guideMask guideMask--full" />
  const right = Math.max(0, window.innerWidth - box.left - box.width)
  const bottom = Math.max(0, window.innerHeight - box.top - box.height)
  return (
    <>
      <div className="guideMask" style={{ left: 0, top: 0, width: '100%', height: box.top }} />
      <div className="guideMask" style={{ left: 0, top: box.top, width: box.left, height: box.height }} />
      <div className="guideMask" style={{ right: 0, top: box.top, width: right, height: box.height }} />
      <div className="guideMask" style={{ left: 0, bottom: 0, width: '100%', height: bottom }} />
    </>
  )
}

function getTargetElement(selector?: string): HTMLElement | null {
  if (!selector) return null
  try {
    return document.querySelector<HTMLElement>(selector)
  } catch {
    return null
  }
}

function measureTarget(selector?: string): SpotlightBox | null {
  const el = getTargetElement(selector)
  if (!el) return null
  const rect = el.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) return null

  // Use the visible portion of the target and cap very large containers.
  // Some guide anchors intentionally point at whole panels/layouts; without a
  // cap the spotlight can grow to nearly the full viewport and feel like a bug.
  const viewportLeft = VIEWPORT_GAP / 2
  const viewportTop = VIEWPORT_GAP / 2
  const viewportRight = window.innerWidth - VIEWPORT_GAP / 2
  const viewportBottom = window.innerHeight - VIEWPORT_GAP / 2
  const visibleLeft = clamp(rect.left - SPOTLIGHT_PAD, viewportLeft, viewportRight)
  const visibleTop = clamp(rect.top - SPOTLIGHT_PAD, viewportTop, viewportBottom)
  const visibleRight = clamp(rect.right + SPOTLIGHT_PAD, viewportLeft, viewportRight)
  const visibleBottom = clamp(rect.bottom + SPOTLIGHT_PAD, viewportTop, viewportBottom)
  const visibleWidth = Math.max(MIN_SPOTLIGHT_SIZE, visibleRight - visibleLeft)
  const visibleHeight = Math.max(MIN_SPOTLIGHT_SIZE, visibleBottom - visibleTop)
  const maxWidth = Math.max(MIN_SPOTLIGHT_SIZE, Math.min(MAX_SPOTLIGHT_WIDTH, window.innerWidth - VIEWPORT_GAP * 2))
  const maxHeight = Math.max(MIN_SPOTLIGHT_SIZE, Math.min(MAX_SPOTLIGHT_HEIGHT, window.innerHeight - VIEWPORT_GAP * 2))
  const width = Math.min(visibleWidth, maxWidth)
  const height = Math.min(visibleHeight, maxHeight)
  const centerX = clamp(
    (visibleLeft + visibleRight) / 2,
    viewportLeft + width / 2,
    viewportRight - width / 2,
  )
  const centerY = clamp(
    (visibleTop + visibleBottom) / 2,
    viewportTop + height / 2,
    viewportBottom - height / 2,
  )
  return {
    left: centerX - width / 2,
    top: centerY - height / 2,
    width,
    height,
  }
}

function getPopoverStyle(box: SpotlightBox | null, placement: QuestGuidePlacement): CSSProperties {
  const width = Math.min(POPOVER_WIDTH, window.innerWidth - VIEWPORT_GAP * 2)
  if (!box || placement === 'center') {
    return {
      width,
      left: Math.max(VIEWPORT_GAP, (window.innerWidth - width) / 2),
      top: Math.max(VIEWPORT_GAP, Math.min(window.innerHeight - 320, (window.innerHeight - 280) / 2)),
    }
  }

  const autoPlacement = box.top < 260 ? 'bottom' : box.left > window.innerWidth * 0.58 ? 'left' : 'right'
  const p = placement === 'auto' ? autoPlacement : placement
  const centerX = box.left + box.width / 2
  const centerY = box.top + box.height / 2
  let left = centerX - width / 2
  let top = box.top + box.height + VIEWPORT_GAP

  if (p === 'top') top = box.top - 250 - VIEWPORT_GAP
  if (p === 'left') {
    left = box.left - width - VIEWPORT_GAP
    top = centerY - 130
  }
  if (p === 'right') {
    left = box.left + box.width + VIEWPORT_GAP
    top = centerY - 130
  }
  if (p === 'bottom') top = box.top + box.height + VIEWPORT_GAP

  return {
    width,
    left: clamp(left, VIEWPORT_GAP, window.innerWidth - width - VIEWPORT_GAP),
    top: clamp(top, VIEWPORT_GAP, Math.max(VIEWPORT_GAP, window.innerHeight - 300)),
  }
}

function boxStyle(box: SpotlightBox): CSSProperties {
  return {
    left: box.left,
    top: box.top,
    width: box.width,
    height: box.height,
  }
}

function actionLabel(action: QuestGuideAction): string {
  if (action.type === 'navigate') return '打开对应界面'
  if (action.type === 'click_target') return '帮我点击'
  if (action.type === 'complete_objective') return '完成目标'
  return '执行'
}

function clamp(value: number, min: number, max: number): number {
  if (max < min) return min
  return Math.max(min, Math.min(max, value))
}
