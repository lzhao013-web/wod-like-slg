import { useEffect, useState } from 'react'
import type { EquipmentItem, CharacterView } from '../../types/game'
import { EquipmentCard } from '../EquipmentCard'
import { InventoryGrid } from '../InventoryGrid'
import { Chip } from '../Chips'
import { cx } from '../../lib/format'
import { statLabel, materialName, materialIcon, SLOT_LABEL } from '../../theme'
import { api } from '../../api/client'

const ENCHANT_COST: Record<string, number> = { arcane_dust: 3, venom_sac: 1 }
const MAX_ENCHANT_SLOTS = 2

interface AscensionRecipe {
  source: string
  target: string
  target_name: string
  materials: Record<string, number>
  description: string
  preview: EquipmentItem
}

function isSpecial(item: EquipmentItem): boolean {
  return item.item_kind === 'special'
}

function canAffordCost(cost: Record<string, number>, materials: Record<string, number>): boolean {
  return Object.entries(cost).every(([k, v]) => (materials[k] ?? 0) >= v)
}

/** A material cost chip row: icon + label + have/need, red when short. */
function CostRow(props: { cost: Record<string, number>; materials: Record<string, number> }) {
  const entries = Object.entries(props.cost)
  if (entries.length === 0) return <span className="muted">—</span>
  return (
    <span className="costRow">
      {entries.map(([k, v]) => {
        const label = materialName(k)
        const icon = materialIcon(label)
        const have = props.materials[k] ?? 0
        const short = have < v
        return (
          <span key={k} className={cx('costChip', short && 'is-short')}>
            {icon} {label} {have}/{v}
          </span>
        )
      })}
    </span>
  )
}

export function EnchantPanel(props: {
  inventory: EquipmentItem[]
  members: CharacterView[]
  materials: Record<string, number>
  busy: boolean
  onEnchant: (itemId: string) => void
  onReroll: (itemId: string, enchantIndex: number) => void
  onAscend: (itemId: string) => void
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [tab, setTab] = useState<'enchant' | 'ascend'>('enchant')
  const [recipes, setRecipes] = useState<AscensionRecipe[]>([])

  // Ascension recipes are static config; fetch once on mount.
  useEffect(() => {
    let alive = true
    api.ascensionRecipes().then(r => { if (alive) setRecipes(r.recipes) }).catch(() => {})
    return () => { alive = false }
  }, [])

  const items = props.inventory
  const selected = items.find(i => i.instance_id === selectedId) ?? items[0] ?? null

  if (items.length === 0) {
    return <section className="panel"><p className="muted">背包里还没有装备，先去副本或商店获取吧。</p></section>
  }

  return (
    <div className="shopLayout">
      {/* Left: grid inventory (pick a target) */}
      <section className="panel shopCol">
        <div className="panel__head">
          <h2>🌀 附魔 · 升华工坊</h2>
          <Chip icon="📦" tone="muted">{items.length} 件</Chip>
        </div>
        <p className="muted">选择一件装备，右侧进行附魔 / 重掷 / 升华。</p>
        <InventoryGrid
          items={items}
          members={props.members}
          selectedId={selected?.instance_id}
          showStatusFilter
          emptyHint="没有装备。"
          onSelect={item => setSelectedId(item.instance_id)}
        />
      </section>

      {/* Right: detail with tabs */}
      <section className="panel shopCol">
        <div className="panel__head"><h2>🔧 改造详情</h2></div>
        {!selected ? (
          <p className="muted">从左侧选择一件装备。</p>
        ) : (
          <>
            <EquipmentCard item={selected} />
            {selected.equipped_by && <div className="muted">提示：附魔/升华无需卸下即可进行（升华除外）。</div>}
            <div className="enchTabs">
              <button className={cx('enchTab', tab === 'enchant' && 'is-active')} onClick={() => setTab('enchant')}>🌀 附魔</button>
              <button className={cx('enchTab', tab === 'ascend' && 'is-active')} onClick={() => setTab('ascend')}>✨ 升华</button>
            </div>
            {tab === 'enchant'
              ? <EnchantTab item={selected} materials={props.materials} busy={props.busy} onEnchant={props.onEnchant} onReroll={props.onReroll} />
              : <AscendTab item={selected} materials={props.materials} busy={props.busy} recipes={recipes} onAscend={props.onAscend} />}
          </>
        )}
      </section>
    </div>
  )
}

function EnchantTab(props: {
  item: EquipmentItem
  materials: Record<string, number>
  busy: boolean
  onEnchant: (itemId: string) => void
  onReroll: (itemId: string, enchantIndex: number) => void
}) {
  const { item, materials } = props
  const affixes = item.affixes ?? []
  const enchants = item.enchants ?? []
  const special = isSpecial(item)
  const full = enchants.length >= MAX_ENCHANT_SLOTS
  const afford = !special && canAffordCost(ENCHANT_COST, materials)

  return (
    <div className="enchDetail">
      {/* Built-in affixes rolled at creation time (immutable, shown for context). */}
      {affixes.length > 0 && (
        <div className="enchBlock">
          <div className="enchBlock__head">
            <h3>◆ 自带词缀</h3>
            <span className="enchCount">{affixes.length} 条</span>
          </div>
          <p className="muted">装备生成时随机获得，不可更改。属性已计入下方数值。</p>
          <div className="enchList" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 7 }}>
            {affixes.map(a => (
              <div className="enchLine enchLine--affix" key={a.id}>
                <span className="eqEffect">◆ {a.name}</span>
                <span className="muted" style={{ fontSize: 11 }}>
                  {Object.entries(a.stats ?? {}).map(([k, v]) => `+${v} ${statLabel(k, true)}`).join(' ')
                    || Object.entries(a.resistances ?? {}).map(([k, v]) => `抗 ${k} +${v}`).join(' ')
                    || (a.special_effects?.length ? a.special_effects.join('、') : '')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="enchBlock">
        <div className="enchBlock__head">
          <h3>🌀 附魔</h3>
          <span className={cx('enchCount', full && 'is-max')}>{enchants.length} / {MAX_ENCHANT_SLOTS} 槽</span>
        </div>
        <p className="muted">消耗材料附加一条随机词缀。已有附魔可单独重掷（同成本）。</p>

        {special ? (
          <p className="muted">特殊装备无法附魔——可在「升华」页用配方升级。</p>
        ) : (
          <>
            {enchants.length > 0 && (
              <div className="enchList" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 7 }}>
                {enchants.map((a, idx) => {
                  const canReroll = canAffordCost(ENCHANT_COST, materials)
                  return (
                    <div className="enchLine" key={a.id}>
                      <span className="eqEffect eqEffect--ench">🌀 {a.name}</span>
                      <span className="muted" style={{ fontSize: 11 }}>
                        {Object.entries(a.stats ?? {}).map(([k, v]) => `+${v} ${statLabel(k, true)}`).join(' ')
                          || Object.entries(a.resistances ?? {}).map(([k, v]) => `抗 ${k} +${v}`).join(' ')
                          || (a.special_effects?.length ? a.special_effects.join('、') : '')}
                      </span>
                      <button
                        className="btn btn--ghost btn--sm"
                        style={{ marginLeft: 'auto' }}
                        disabled={props.busy || !canReroll}
                        onClick={() => props.onReroll(item.instance_id, idx)}
                        title={canReroll ? '重掷此附魔（随机替换为另一条）' : '材料不足'}
                      >
                        🎲 重掷
                      </button>
                    </div>
                  )
                })}
              </div>
            )}

            {full ? (
              <p className="muted">附魔词条已满。可对已有词条「重掷」。</p>
            ) : (
              <>
                <div className="enchCost">
                  <span className="muted">耗材：</span>
                  <CostRow cost={ENCHANT_COST} materials={materials} />
                </div>
                <button
                  className={cx('btn btn--sm', afford && !props.busy ? 'btn--accent' : 'btn--ghost')}
                  disabled={props.busy || !afford}
                  onClick={() => props.onEnchant(item.instance_id)}
                >
                  {afford ? '附魔（随机词缀）' : '材料不足'}
                </button>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function AscendTab(props: {
  item: EquipmentItem
  materials: Record<string, number>
  busy: boolean
  recipes: AscensionRecipe[]
  onAscend: (itemId: string) => void
}) {
  const { item, materials, recipes } = props
  const recipe = recipes.find(r => r.source === item.template_id) ?? null
  const nonSpecial = !isSpecial(item)

  if (nonSpecial) {
    return (
      <div className="enchBlock">
        <div className="enchBlock__head"><h3>✨ 升华</h3></div>
        <p className="muted">普通装备无法升华。只有特定特殊装备（如毒抗戒指、圣徽等）可通过配方升级为更强的装备。</p>
      </div>
    )
  }
  if (!recipe) {
    return (
      <div className="enchBlock">
        <div className="enchBlock__head"><h3>✨ 升华</h3></div>
        <p className="muted">此装备暂无升华配方。</p>
      </div>
    )
  }

  const equipped = !!item.equipped_by
  const afford = canAffordCost(recipe.materials, materials)
  const can = afford && !equipped

  return (
    <div className="enchBlock">
      <div className="enchBlock__head"><h3>✨ 升华</h3></div>
      {recipe.description && <p className="muted">{recipe.description}</p>}

      <div className="ascPreview">
        <span>{item.name}</span>
        <span className="ascArrow">→</span>
        <span style={{ color: 'var(--gold)', fontWeight: 700 }}>{recipe.target_name}</span>
        <span className="muted" style={{ fontSize: 11 }}>({SLOT_LABEL[recipe.preview?.slot ?? ''] ?? ''})</span>
      </div>

      {recipe.preview && (
        <EquipmentCard item={recipe.preview} compact />
      )}

      {equipped && <p className="muted" style={{ color: 'var(--warn)' }}>请先在「队伍编成」卸下装备再升华。</p>}

      <div className="enchCost">
        <span className="muted">耗材：</span>
        <CostRow cost={recipe.materials} materials={materials} />
      </div>
      <button
        className={cx('btn btn--sm', can && !props.busy ? 'btn--accent' : 'btn--ghost')}
        disabled={props.busy || !can}
        onClick={() => props.onAscend(item.instance_id)}
      >
        {equipped ? '请先卸下' : afford ? `升华为 ${recipe.target_name}` : '材料不足'}
      </button>
    </div>
  )
}
