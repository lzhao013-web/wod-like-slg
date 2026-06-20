import { useState } from 'react'
import type { CSSProperties } from 'react'
import type { EquipmentItem, MerchantView, ShopItemView, ShopView } from '../../types/game'
import { EquipmentCard } from '../EquipmentCard'
import { Chip } from '../Chips'
import { num } from '../../lib/format'

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
  busy: boolean
  onBuy: (id: string) => void
  onSell: (itemId: string) => void
  onSalvage: (itemId: string) => void
}) {
  const merchantList: MerchantView[] = props.shop ? Object.values(props.shop.merchants) : []
  const [activeMid, setActiveMid] = useState<string>(merchantList[0]?.merchant_id ?? '')
  const active = merchantList.find(m => m.merchant_id === activeMid) ?? merchantList[0]
  // Sellable inventory: only unequipped items.
  const sellable = props.inventory.filter(i => !i.equipped_by)

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
              onClick={() => setActiveMid(m.merchant_id)}
            >
              <span className="merchantTab__icon">{m.icon ?? '🪙'}</span>
              <span>{m.name}</span>
              <span className="muted">({m.items.length})</span>
            </button>
          ))}
        </div>

        {active.items.length === 0 && <p className="muted">今日货架已售罄，次日刷新。</p>}
        <div className="shopGrid">
          {active.items.map(i => {
            const poor = !canAfford(i, props.gold, props.materials)
            return (
              <div className="shopItem" key={i.shop_id}>
                <EquipmentCard
                  item={toEquipment(i)}
                  compact
                  affordable={!poor}
                  cost={i.cost}
                  showCost
                />
                <p className="shopItem__summary">{i.summary}</p>
                <button
                  className={poor ? 'btn btn--ghost btn--sm' : 'btn btn--accent btn--sm'}
                  disabled={props.busy || poor}
                  onClick={() => props.onBuy(i.shop_id)}
                >
                  {poor ? `${currencyLabel(i.currency ?? 'gold')} 不足` : `购买 · ${currencyLabel(i.currency ?? 'gold')}${i.cost}`}
                </button>
              </div>
            )
          })}
        </div>
      </section>

      <section className="panel shopCol">
        <div className="panel__head">
          <h2>🎒 我的背包</h2>
          <Chip icon="📦" tone="muted">{sellable.length} 件</Chip>
        </div>
        {sellable.length === 0 && <p className="muted">背包没有可出售/分解的装备（已装备的需先卸下）。</p>}
        <div className="shopGrid">
          {sellable.map(item => {
            const sellValue = max(1, Math.round((item.cost ?? 0) * (SELL_MULTIPLIERS[item.rarity] ?? 0.4)))
            const salGold = SALVAGE_GOLD[item.rarity] ?? 5
            return (
              <div className="shopItem" key={item.instance_id}>
                <EquipmentCard item={item} compact />
                <div className="shopItem__recycle">
                  <button
                    className="btn btn--ghost btn--sm"
                    disabled={props.busy}
                    onClick={() => props.onSell(item.instance_id)}
                    title={`出售换 ${sellValue} 金币`}
                  >
                    💰 出售 · 🪙{sellValue}
                  </button>
                  <button
                    className="btn btn--ghost btn--sm"
                    disabled={props.busy}
                    onClick={() => props.onSalvage(item.instance_id)}
                    title={`分解换 ${salGold}+ 金币与材料`}
                  >
                    ⚙️ 分解
                  </button>
                </div>
              </div>
            )
          })}
        </div>
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
