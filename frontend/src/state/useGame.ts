import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { DungeonCardView, DungeonDetailView, GameStateView, PartyView, PlanAction, ReportView, ShopView } from '../types/game'

export type Phase = 'loading' | 'start' | 'playing' | 'dayResults' | 'ended'

export interface Toast {
  id: number
  tone: 'info' | 'success' | 'warn' | 'error'
  text: string
}

export interface DayResult {
  reports: ReportView[]
  state: GameStateView
}

const FORMATION_CELLS = [
  'r0c0', 'r0c1', 'r0c2',
  'r1c0', 'r1c1', 'r1c2',
  'r2c0', 'r2c1', 'r2c2',
]

export interface GameApi {
  phase: Phase
  state: GameStateView | null
  dungeons: DungeonCardView[]
  party: PartyView | null
  plan: PlanAction[]
  reports: ReportView[]
  shop: ShopView | null
  formationCells: string[]
  lastDayResult: DayResult | null
  selectedDungeon: string
  selectedReport: string
  dungeonDetail: DungeonDetailView | null
  reportDetail: ReportView | null
  loading: boolean
  toasts: Toast[]
  busy: boolean
  error: string | null
  setSelectedDungeon: (id: string) => void
  setSelectedReport: (id: string) => void
  pushToast: (tone: Toast['tone'], text: string) => void
  dismissToast: (id: number) => void
  act: <T,>(fn: () => Promise<T>, opts?: ActOpts<T>) => Promise<T | undefined>
  endDay: () => Promise<void>
  newGame: (seed?: number) => Promise<void>
  resetGame: () => Promise<void>
  returnToPlay: () => void
  gotoStart: () => void
}

interface ActOpts<T> {
  after?: (value: T) => void
  reload?: boolean
  toast?: (value: T) => Toast | Omit<Toast, 'id'> | null
}

let toastSeq = 1

export function useGame(): GameApi {
  const [phase, setPhase] = useState<Phase>('loading')
  const [state, setState] = useState<GameStateView | null>(null)
  const [dungeons, setDungeons] = useState<DungeonCardView[]>([])
  const [party, setParty] = useState<PartyView | null>(null)
  const [plan, setPlan] = useState<PlanAction[]>([])
  const [reports, setReports] = useState<ReportView[]>([])
  const [shop, setShop] = useState<ShopView | null>(null)
  const [lastDayResult, setLastDayResult] = useState<DayResult | null>(null)
  const [selectedDungeon, setSelectedDungeon] = useState('')
  const [selectedReport, setSelectedReport] = useState('')
  const [dungeonDetail, setDungeonDetail] = useState<DungeonDetailView | null>(null)
  const [reportDetail, setReportDetail] = useState<ReportView | null>(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [error, setError] = useState<string | null>(null)

  const pushToast = useCallback((tone: Toast['tone'], text: string) => {
    const id = toastSeq++
    setToasts(prev => [...prev, { id, tone, text }])
    window.setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4200)
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const loadAll = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true)
    try {
      const [s, ds, p, pl, rs, sh] = await Promise.all([
        api.state(), api.dungeons(), api.party(), api.plan(), api.reports(), api.shop(),
      ])
      setState(s)
      setDungeons(ds)
      setParty(p)
      setPlan(pl.actions)
      setReports(rs)
      setShop(sh)
      setError(null)
      return { state: s, dungeons: ds, party: p }
    } catch (err: any) {
      setError(err?.message || String(err))
      return null
    } finally {
      if (showLoading) setLoading(false)
    }
  }, [])

  // Initial load: decide whether we resume an in-progress run or show the start screen.
  useEffect(() => {
    (async () => {
      const loaded = await loadAll(false)
      if (!loaded || !loaded.state) {
        setPhase('start')
        return
      }
      const s = loaded.state
      if (s.victory || s.defeat) {
        setState(s)
        setPhase('ended')
      } else {
        setPhase('playing')
      }
    })()
  }, [loadAll])

  // Detail loaders track the current selection.
  useEffect(() => {
    if (!selectedDungeon) { setDungeonDetail(null); return }
    api.dungeon(selectedDungeon).then(setDungeonDetail).catch(e => setError(e?.message || String(e)))
  }, [selectedDungeon, dungeons.length])

  useEffect(() => {
    if (!selectedReport) { setReportDetail(null); return }
    api.report(selectedReport).then(setReportDetail).catch(e => setError(e?.message || String(e)))
  }, [selectedReport, reports.length])

  // Keep a valid selection: if the current pick disappears, fall back to the first item.
  useEffect(() => {
    if (!dungeons.some(d => d.dungeon_id === selectedDungeon)) {
      setSelectedDungeon(dungeons[0]?.dungeon_id ?? '')
    }
  }, [dungeons, selectedDungeon])

  useEffect(() => {
    if (!reports.some(r => r.id === selectedReport)) {
      setSelectedReport(reports[0]?.id ?? '')
    }
  }, [reports, selectedReport])

  const act = useCallback(async function act<T>(fn: () => Promise<T>, opts: ActOpts<T> = {}): Promise<T | undefined> {
    setBusy(true)
    setError(null)
    try {
      const value = await fn()
      opts.after?.(value)
      if (opts.toast) {
        const t = opts.toast(value)
        if (t) pushToast((t as Toast).tone, t.text)
      }
      if (opts.reload !== false) await loadAll(false)
      return value
    } catch (err: any) {
      const msg = err?.message || String(err)
      setError(msg)
      pushToast('error', msg)
      return undefined
    } finally {
      setBusy(false)
    }
  }, [loadAll, pushToast])

  const endDay = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const result = await api.endDay()
      // Refresh the underlying state but go straight into the results theatre.
      const [s, ds, p, pl, rs, sh] = await Promise.all([
        api.state(), api.dungeons(), api.party(), api.plan(), api.reports(), api.shop(),
      ])
      setState(s)
      setDungeons(ds)
      setParty(p)
      setPlan(pl.actions)
      setReports(rs)
      setShop(sh)
      setLastDayResult({ reports: result.reports, state: result.state })
      if (s.victory || s.defeat) {
        // Defer the ended screen until the player has watched the results.
        setPhase('dayResults')
      } else {
        setPhase('dayResults')
      }
      return undefined
    } catch (err: any) {
      const msg = err?.message || String(err)
      setError(msg)
      pushToast('error', msg)
    } finally {
      setBusy(false)
    }
  }, [pushToast])

  const newGame = useCallback(async (seed?: number) => {
    await act(() => api.newGame(seed), {
      reload: false,
      after: () => { setSelectedDungeon(''); setSelectedReport('') },
      toast: () => ({ tone: 'success', text: '新一局开始：祝好运。' } as Omit<Toast, 'id'>),
    })
    await loadAll(false)
    setPhase('playing')
  }, [act, loadAll])

  const resetGame = useCallback(async () => {
    await act(() => api.reset(), {
      reload: false,
      toast: () => ({ tone: 'info', text: '存档已重置。' } as Omit<Toast, 'id'>),
    })
    await loadAll(false)
    setPhase('start')
  }, [act, loadAll])

  const returnToPlay = useCallback(() => {
    if (state && (state.victory || state.defeat)) {
      setPhase('ended')
    } else {
      setPhase('playing')
    }
  }, [state])

  const gotoStart = useCallback(() => setPhase('start'), [])

  return {
    phase, state, dungeons, party, plan, reports, shop,
    formationCells: FORMATION_CELLS,
    lastDayResult, selectedDungeon, selectedReport, dungeonDetail, reportDetail,
    loading, toasts, busy, error,
    setSelectedDungeon, setSelectedReport, pushToast, dismissToast,
    act, endDay, newGame, resetGame, returnToPlay, gotoStart,
  } as GameApi
}

/** Cell -> friendly grid label. */
export const CELL_LABEL: Record<string, string> = {
  r0c0: '前左', r0c1: '前中', r0c2: '前右',
  r1c0: '中左', r1c1: '中中', r1c2: '中右',
  r2c0: '后左', r2c1: '后中', r2c2: '后右',
}

export const FRONT_CELLS = new Set(['r0c0', 'r0c1', 'r0c2'])
export const MID_CELLS = new Set(['r1c0', 'r1c1', 'r1c2'])
export const BACK_CELLS = new Set(['r2c0', 'r2c1', 'r2c2'])
