import { useMemo, useState, type ReactNode } from 'react'
import type { EquipmentItem, CharacterView } from '../types/game'
import { EquipmentCard } from './EquipmentCard'
import { Chip } from './Chips'
import { cx } from '../lib/format'

type StatusFilter = 'all' | 'stash' | 'equipped'

/**
 * A reusable grid of equipment cells. Each cell shows a compact EquipmentCard
 * (hover for full details) plus a status line that distinguishes items sitting
 * in the stash from items currently worn — solving the "equipped vs inventory"
 * ambiguity that existed across the app. Callers supply their own per-item
 * action buttons via `actions`, so the same grid serves the party equip screen
 * (装备/卸下), the shop (出售/分解) and the enchant screen (selection only).
 */
export function InventoryGrid(props: {
  items: EquipmentItem[]
  members: CharacterView[]
  selectedId?: string
  onSelect?: (item: EquipmentItem) => void
  actions?: (item: EquipmentItem) => ReactNode
  defaultFilter?: StatusFilter
  showStatusFilter?: boolean
  showNameFilter?: boolean
  emptyHint?: string
  busy?: boolean
}) {
  const showName = props.showNameFilter !== false
  const [nameFilter, setNameFilter] = useState('')
  const [status, setStatus] = useState<StatusFilter>(props.defaultFilter ?? 'all')

  const memberName = (id: string | null | undefined): string => {
    if (!id) return ''
    const m = props.members.find(x => x.id === id)
    return m ? `${m.class_name}·${m.name}` : '未知角色'
  }

  const filtered = useMemo(() => {
    const q = nameFilter.trim().toLowerCase()
    return props.items.filter(i => {
      if (showName && q && !i.name.toLowerCase().includes(q)) return false
      if (status === 'stash' && i.equipped_by) return false
      if (status === 'equipped' && !i.equipped_by) return false
      return true
    })
  }, [props.items, nameFilter, status, showName])

  if (props.items.length === 0) {
    return <p className="muted">{props.emptyHint ?? '背包里还没有装备。'}</p>
  }

  return (
    <div>
      <div className="invFilterRow">
        {showName && (
          <input
            className="enchFilter"
            style={{ flex: '1 1 160px', marginBottom: 0 }}
            placeholder="筛选装备名称…"
            value={nameFilter}
            onChange={e => setNameFilter(e.target.value)}
          />
        )}
        {props.showStatusFilter && (
          <div className="invStatusChips">
            {(['all', 'stash', 'equipped'] as StatusFilter[]).map(s => (
              <button
                key={s}
                className={cx('enchTab', status === s && 'is-active')}
                onClick={() => setStatus(s)}
                type="button"
              >
                {s === 'all' ? '全部' : s === 'stash' ? '📦 库存' : '🛡️ 已装备'}
              </button>
            ))}
          </div>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className="muted">没有符合条件的装备。</p>
      ) : (
        <div className="invGrid">
          {filtered.map(item => {
            const owner = item.equipped_by ?? null
            const isEquipped = !!owner
            const isSel = props.selectedId === item.instance_id
            const selectable = !!props.onSelect
            return (
              <div
                key={item.instance_id}
                className={cx('invCell', isEquipped && 'is-equipped', isSel && 'is-active')}
              >
                <EquipmentCard
                  item={item}
                  compact
                  selected={isSel}
                  onClick={selectable ? () => props.onSelect!(item) : undefined}
                />
                <div className={cx('invStatus', isEquipped ? 'invStatus--equipped' : 'invStatus--stash')}>
                  {isEquipped ? <>🛡️ 装备于 {memberName(owner)}</> : <>📦 库存中</>}
                </div>
                {props.actions && <div className="invActions">{props.actions(item)}</div>}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
