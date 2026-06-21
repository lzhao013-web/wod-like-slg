import { useState } from 'react'
import type { CSSProperties } from 'react'
import type { EquipmentItem, MerchantView, ShopItemView, ShopView, CharacterView } from '../../types/game'
import { EquipmentCard } from '../EquipmentCard'
import { InventoryGrid } from '../InventoryGrid'
import { EquipmentHover } from '../EquipmentTooltip'
import { Chip } from '../Chips'
import { cx, num } from '../../lib/format'

/** Currency display: gold is shown with the coin pill, materials by their label. */
const MATERIAL_LABEL: Record<string, string> = {
  leather: '皮革',
  ore: '矿石',
  cloth: '布料',
  venom_sac: '毒囊',
  beast_fang: '野兽牙',
  arcane_dust: '奥术尘',
}

function currencyLabel(cur: string): string {
  if (cur === 'gold') return '🪙'
  return MATERIAL_LABEL[cur] ?? cur
}

/** Sell value estimate mirrors backend _estimate_sell_value (sell_multipliers). */
const SELL_MULTIPLIERS: Record<string, number> = {
  common: 0.4, uncommon: 0.45, rare: 0.5, epic: 0.55, legendary: 0.6, artifact: 0.65,
}
const SALVAGE_GOLD: Record<string, number> = {
  common: 5, uncommon: 8, rare: 15, epic: 25, legendary: 40, artifact: 60,
}

export function ShopPanel(props: {
  shop: ShopView | null
  gold: number
  materials: Record<string, number>
  inventory: EquipmentItem[]
  members: CharacterView[]
  busy: boolean
  onBuy: (id: string) => void
  onBuyMany: (ids: string[]) => void
  onSell: (itemId: string) => void
  onSalvage: (itemId: string) => void
}) {
  const merchantList: MerchantView[] = props.shop ? Object.values(props.shop.merchants) : []
  const [activeMid, setActiveMid] = useState<string>(merchantList[0]?.merchant_id ?? '')
  const active = merchantList.find(m => m.merchant_id === activeMid) ?? merchantList[0]
  // Multi-select for batch buying. Reset selection when switching merchants.
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const toggleSelected = (shopId: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(shopId)) next.delete(shopId)
      else next.add(shopId)
      return next
    })
  }
  const switchMerchant = (mid: string) => {
    setActiveMid(mid)
    setSelected(new Set())
  }

  if (!props.shop || !active) {
    return <section className="panel"><p className="muted">集市未就绪。</p></section>
  }

  return (
    <div className="shopLayout">
      <section className="panel shopCol">
        <div className="panel__head">
          <h2>🪙 集市 · 商店</h2>
          <span className="goldPill">🪙 {num(props.gold)}</span>
        </div>

        {/* Merchant tabs */}
        <div className="merchantTabs">
          {merchantList.map(m => (
            <button
              key={m.merchant_id}
              className={m.merchant_id === active.merchant_id ? 'merchantTab is-active' : 'merchantTab'}
              onClick={() => switchMerchant(m.merchant_id)}
            >
              <span className="merchantTab__icon">{m.icon ?? '🪙'}</span>
              <span>{m.name}</span>
              <span className="muted">({m.items.length})</span>
            </button>
          ))}
        </div>

        {/* Batch select toolbar: toggle individual items, then buy all selected. */}
        {(() => {
          const selectable = active.items.filter(i =>
            canAfford(i, props.gold, props.materials) && canAnyMemberEquip(i, props.members),
          )
          const selectableIds = selectable.map(i => i.shop_id)
          const allSelected = selectableIds.length > 0 && selectableIds.every(id => selected.has(id))
          const selectedBuyable = selectableIds.filter(id => selected.has(id))
          const totalCost = active.items
            .filter(i => selected.has(i.shop_id))
            .reduce((sum, i) => sum + i.cost, 0)
          return (
            <div className="shopBatchBar">
              <button
                type="button"
                className="btn btn--ghost btn--sm"
                disabled={selectableIds.length === 0}
                onClick={() => setSelected(allSelected ? new Set() : new Set(selectableIds))}
              >
                {allSelected ? '取消全选' : `全选可买（${selectableIds.length}）`}
              </button>
              <span className="muted" style={{ fontSize: 12 }}>
                已选 {selectedBuyable.length} 件{selectedBuyable.length > 0 ? ` · 合计 🪙${num(totalCost)}` : ''}
              </span>
              <button
                type="button"
                className="btn btn--accent btn--sm"
                disabled={props.busy || selectedBuyable.length === 0}
                onClick={() => {
                  props.onBuyMany(selectedBuyable)
                  setSelected(new Set())
                }}
              >
                🛒 购买选中（{selectedBuyable.length}）
              </button>
            </div>
          )
        })()}

        {active.items.length === 0 && <p className="muted">今日货架已售罄，次日刷新。</p>}
        <div className="shopBuyGrid">
          {active.items.map(i => {
            const poor = !canAfford(i, props.gold, props.materials)
            const equippable = canAnyMemberEquip(i, props.members)
            const blocked = poor || !equippable
            const selectable = !blocked
            const isSel = selected.has(i.shop_id)
            const hint = equipHint(i, props.members)
            const eqItem = toEquipment(i)
            const card = (
              <div className={cx('shopBuyCell', isSel && 'is-selected')} key={i.shop_id}>
                {selectable && (
                  <label className="shopCheck" title={isSel ? '取消选择' : '加入批量购买'}>
                    <input
                      type="checkbox"
                      checked={isSel}
                      onChange={() => toggleSelected(i.shop_id)}
                      onClick={e => e.stopPropagation()}
                      disabled={props.busy}
                    />
                  </label>
                )}
                <EquipmentCard
                  item={eqItem}
                  compact
                  affordable={!poor}
                  cost={i.cost}
                  showCost
                />
                {i.summary && <p className="shopItem__summary">{i.summary}</p>}
                {hint && <p className="shopItem__hint">{hint}</p>}
                <button
                  className={blocked ? 'btn btn--ghost btn--sm' : 'btn btn--accent btn--sm'}
                  disabled={props.busy || blocked}
                  onClick={() => props.onBuy(i.shop_id)}
                >
                  {poor
                    ? `${currencyLabel(i.currency ?? 'gold')} 不足`
                    : !equippable
                      ? '无人可装备'
                      : `购买 · ${currencyLabel(i.currency ?? 'gold')}${i.cost}`}
                </button>
              </div>
            )
            // Hover for full details (consumables have no equipment, so only wrap equipment).
            return i.kind === 'equipment' ? <EquipmentHover key={i.shop_id} item={eqItem}>{card}</EquipmentHover> : card
          })}
        </div>
      </section>

      <section className="panel shopCol">
        <div className="panel__head">
          <h2>🎒 我的背包</h2>
          <Chip icon="📦" tone="muted">{props.inventory.length} 件</Chip>
        </div>
        <InventoryGrid
          items={props.inventory}
          members={props.members}
          defaultFilter="stash"
          showStatusFilter
          emptyHint="背包没有装备。已装备的需先在「队伍编成」卸下再出售/分解。"
          busy={props.busy}
          actions={item => {
            if (item.equipped_by) {
              return <span className="muted" style={{ fontSize: 12 }}>需先卸下</span>
            }
            const sellValue = max(1, Math.round((item.cost ?? 0) * (SELL_MULTIPLIERS[item.rarity] ?? 0.4)))
            const salGold = SALVAGE_GOLD[item.rarity] ?? 5
            return (
              <>
                <button className="btn btn--ghost btn--sm" disabled={props.busy} onClick={() => props.onSell(item.instance_id)} title={`出售换 ${sellValue} 金币`}>
                  💰 🪙{sellValue}
                </button>
                <button className="btn btn--ghost btn--sm" disabled={props.busy} onClick={() => props.onSalvage(item.instance_id)} title={`分解换 ${salGold}+ 金币与材料`}>
                  ⚙️ 分解
                </button>
              </>
            )
          }}
        />
      </section>
    </div>
  )
}

function canAfford(item: ShopItemView, gold: number, materials: Record<string, number>): boolean {
  const cur = item.currency ?? 'gold'
  if (cur === 'gold') return gold >= item.cost
  return (materials[cur] ?? 0) >= item.cost
}

function max(a: number, b: number): number {
  return a > b ? a : b
}

/** Can at least one party member equip this equipment shop item? Consumables
 * are usable by anyone. Returns true if the item is not equipment-typed. */
function canAnyMemberEquip(item: ShopItemView, members: CharacterView[]): boolean {
  if (item.kind !== 'equipment') return true
  const restriction = item.equipment?.class_restriction ?? []
  if (!restriction || restriction.length === 0) return true
  return members.some(m =>
    restriction.includes(m.class_id) || (m.base_class_id && restriction.includes(m.base_class_id)),
  )
}

/** All distinct class names that can equip this item, for the "no one can use" hint. */
function equipHint(item: ShopItemView, members: CharacterView[]): string {
  if (item.kind !== 'equipment') return ''
  const restriction = item.equipment?.class_restriction ?? []
  if (!restriction || restriction.length === 0) return ''
  if (canAnyMemberEquip(item, members)) return ''
  return `无人可装备（限 ${restriction.join('/')}）`
}

// Shop items use a lighter schema than inventory items; adapt to EquipmentCard props.
function toEquipment(i: ShopItemView): EquipmentItem {
  if (i.equipment) return { ...i.equipment, cost: i.cost }
  return {
    instance_id: i.shop_id,
    template_id: i.template_id,
    name: i.name,
    slot: i.slot ?? 'backpack',
    rarity: i.rarity ?? 'common',
    cost: i.cost,
    stats: {},
    resistances: {},
    special_effects: [],
    affixes: [],
    durability: 0,
    max_durability: 0,
    class_restriction: [],
    equipped_by: null,
  }
}
