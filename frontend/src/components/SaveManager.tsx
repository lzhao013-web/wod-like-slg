import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { SaveSlotListView, SaveSlotView } from '../types/game'
import { cx, num } from '../lib/format'

export function SaveManager(props: {
  open: boolean
  busy: boolean
  canSave: boolean
  onClose: () => void
  onSaveSlot: (slotId: string) => Promise<unknown>
  onLoadSlot: (slotId: string) => Promise<unknown>
  onDeleteSlot: (slotId: string) => Promise<unknown>
  onNewGame: (seed?: number) => Promise<unknown>
}) {
  const [data, setData] = useState<SaveSlotListView | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [seed, setSeed] = useState('')

  async function refresh() {
    setLoading(true)
    setError(null)
    try {
      setData(await api.saveSlots())
    } catch (err: any) {
      setError(err?.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (props.open) void refresh()
  }, [props.open])

  if (!props.open) return null

  async function save(slot: SaveSlotView) {
    if (slot.exists && !window.confirm(`覆盖「${slot.label}」？`)) return
    await props.onSaveSlot(slot.id)
    await refresh()
  }

  async function load(slot: SaveSlotView) {
    if (!slot.exists) return
    if (!window.confirm(`读取「${slot.label}」？当前自动存档会切换到该进度。`)) return
    await props.onLoadSlot(slot.id)
    props.onClose()
  }

  async function remove(slot: SaveSlotView) {
    if (!slot.exists || slot.kind === 'auto') return
    if (!window.confirm(`清空「${slot.label}」？`)) return
    await props.onDeleteSlot(slot.id)
    await refresh()
  }

  async function startNew() {
    if (!window.confirm('开始新游戏会覆盖当前自动存档。建议先保存到手动槽位。继续？')) return
    await props.onNewGame(seed.trim() ? Number(seed.trim()) : undefined)
    props.onClose()
  }

  return (
    <div className="overlay" onClick={props.onClose}>
      <article className="saveSheet" onClick={e => e.stopPropagation()}>
        <header className="saveSheet__hero">
          <span className="saveSheet__icon">💾</span>
          <div>
            <h2>存档管理</h2>
            <p>自动存档随游戏进度更新；手动槽位可用于备份、回滚和测试不同路线。</p>
          </div>
          <button className="questSheet__close" onClick={props.onClose} aria-label="关闭">✕</button>
        </header>

        <div className="saveSheet__body">
          {error && <p className="appError saveSheet__error">{error}</p>}
          {loading && <p className="muted">正在读取存档列表…</p>}

          <section className="saveNewGame">
            <div>
              <b>开始新游戏</b>
              <p>可指定随机种子，留空则随机。新游戏会成为当前自动存档。</p>
            </div>
            <div className="saveNewGame__controls">
              <input
                inputMode="numeric"
                placeholder="随机种子（可选）"
                value={seed}
                onChange={e => setSeed(e.target.value.replace(/[^0-9]/g, ''))}
              />
              <button className="btn btn--primary btn--sm" disabled={props.busy} onClick={startNew}>开始新游戏</button>
            </div>
          </section>

          <div className="saveSlotList">
            {(data?.slots ?? []).map(slot => (
              <SaveSlotRow
                key={slot.id}
                slot={slot}
                busy={props.busy}
                canSave={props.canSave}
                onSave={() => save(slot)}
                onLoad={() => load(slot)}
                onDelete={() => remove(slot)}
              />
            ))}
          </div>
        </div>
      </article>
    </div>
  )
}

function SaveSlotRow(props: {
  slot: SaveSlotView
  busy: boolean
  canSave: boolean
  onSave: () => void
  onLoad: () => void
  onDelete: () => void
}) {
  const { slot } = props
  const status = slot.corrupt
    ? '损坏'
    : !slot.exists
      ? '空槽'
      : slot.victory
        ? '胜利结局'
        : slot.defeat
          ? '远征失败'
          : '进行中'
  return (
    <section className={cx('saveSlot', slot.kind === 'auto' && 'saveSlot--auto', !slot.exists && 'is-empty', slot.corrupt && 'is-corrupt')}>
      <div className="saveSlot__main">
        <div className="saveSlot__head">
          <b>{slot.kind === 'auto' ? '⚡' : '📦'} {slot.label}</b>
          <span>{status}</span>
        </div>
        {slot.exists && !slot.corrupt ? (
          <div className="saveSlot__meta">
            <span>第 {slot.day ?? '?'} / {slot.max_day ?? '?'} 天</span>
            <span>🪙 {num(slot.gold ?? 0)}</span>
            <span>队员 {slot.party_count ?? 0}</span>
            <span>战报 {slot.report_count ?? 0}</span>
            <span>种子 {slot.run_seed ?? '—'}</span>
            {slot.modified_at && <span>{slot.modified_at.replace('T', ' ')}</span>}
          </div>
        ) : (
          <p className="muted">{slot.corrupt ? `读取失败：${slot.error ?? '未知错误'}` : '尚未保存进度。'}</p>
        )}
      </div>
      <div className="saveSlot__actions">
        <button className="btn btn--accent btn--sm" disabled={props.busy || !props.canSave} onClick={props.onSave}>
          {slot.kind === 'auto' ? '保存当前' : slot.exists ? '覆盖保存' : '保存'}
        </button>
        <button className="btn btn--ghost btn--sm" disabled={props.busy || !slot.exists || slot.corrupt} onClick={props.onLoad}>读取</button>
        {slot.kind !== 'auto' && (
          <button className="btn btn--danger btn--sm" disabled={props.busy || !slot.exists} onClick={props.onDelete}>清空</button>
        )}
      </div>
    </section>
  )
}
