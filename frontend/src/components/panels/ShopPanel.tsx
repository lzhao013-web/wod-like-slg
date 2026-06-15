import type { CSSProperties } from 'react'
import type { ShopView } from '../../types/game'
import { EquipmentCard } from '../EquipmentCard'
import { CharacterAvatar } from '../CharacterAvatar'
import { Chip } from '../Chips'
import { classMeta } from '../../theme'
import { num } from '../../lib/format'

export function ShopPanel(props: {
  shop: ShopView | null
  gold: number
  partySize: number
  onBuy: (id: string) => void
  onRecruit: (id: string) => void
  busy: boolean
}) {
  if (!props.shop) return <section className="panel"><p className="muted">集市未就绪。</p></section>
  const items = props.shop.items ?? []
  const recruits = props.shop.recruits ?? []

  return (
    <div className="shopLayout">
      <section className="panel shopCol">
        <div className="panel__head"><h2>⚒️ 铁匠 · 商人</h2><span className="goldPill">🪙 {num(props.gold)}</span></div>
        {items.length === 0 && <p className="muted">今日商品已售罄或刷新中。</p>}
        <div className="shopGrid">
          {items.map(i => {
            const poor = props.gold < i.cost
            return (
              <div className="shopItem" key={i.shop_id}>
                <EquipmentCard
                  item={toEquipment(i)}
                  compact
                  affordable={!poor}
                  cost={i.cost}
                  showCost
                />
                <p className="shopItem__summary">{translateSummary(i.summary)}</p>
                <button className={poor ? 'btn btn--ghost btn--sm' : 'btn btn--accent btn--sm'} disabled={props.busy || poor} onClick={() => props.onBuy(i.shop_id)}>
                  {poor ? '💰 金币不足' : `购买 · 🪙${i.cost}`}
                </button>
              </div>
            )
          })}
        </div>
      </section>

      <section className="panel shopCol">
        <div className="panel__head"><h2>🏰 酒馆 · 招募</h2><Chip icon="👥" tone="muted">队伍 {props.partySize}/8</Chip></div>
        {recruits.length === 0 && <p className="muted">今日没有可招募的冒险者。</p>}
        <div className="shopGrid">
          {recruits.map(r => {
            const poor = props.gold < r.cost
            const full = props.partySize >= 8
            const cm = classMeta(r.class_id)
            return (
              <div className="recruitCard" key={r.candidate_id} style={{ '--accent': cm.accent } as CSSProperties}>
                <div className="recruitCard__head">
                  <CharacterAvatar ch={{ class_id: r.class_id, level: r.level, injury_state: 'healthy' }} size={46} />
                  <div>
                    <b>{r.name}</b>
                    <span className="muted">{r.class_name} · Lv.{r.level}</span>
                  </div>
                </div>
                <p className="recruitCard__role">{r.role}</p>
                <button className={poor || full ? 'btn btn--ghost btn--sm' : 'btn btn--accent btn--sm'} disabled={props.busy || poor || full} onClick={() => props.onRecruit(r.candidate_id)}>
                  {full ? '队伍已满' : poor ? '💰 金币不足' : `招募 · 🪙${r.cost}`}
                </button>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}

function translateSummary(text: string): string {
  const map: Record<string, string> = {
    max_hp: '生命上限',
    attack: '攻击',
    defense: '防御',
    speed: '速度',
    accuracy: '命中',
    evasion: '闪避',
    physical: '物理',
    poison: '毒',
    magic: '魔法',
    curse: '诅咒',
    fire: '火焰',
    bleed: '流血',
  }
  let out = text || ''
  for (const [key, label] of Object.entries(map)) {
    out = out.replace(new RegExp(`\\b${key}\\b`, 'g'), label)
  }
  return out
}

// Shop items use a lighter schema than inventory items; adapt to EquipmentCard props.
function toEquipment(i: ShopView['items'][number]) {
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
