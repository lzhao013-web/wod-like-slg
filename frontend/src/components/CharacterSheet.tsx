import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import type { CharacterView, PartyView, SkillSummary, StatBreakdown } from '../types/game'
import { Bar } from './Bar'
import { CharacterAvatar } from './CharacterAvatar'
import { Chip, ResistChip, StatusChip, RarityTag } from './Chips'
import { classMeta, STATS, ATTRIBUTES, ELEMENTS, FOCUS_META, SLOT_ICON, SLOT_LABEL, elementMeta, skillsForClass, SKILL_ICON, statusMeta, focusLabel, focusCompositionLabel, focusScoreKey, targetRuleLabel, rangeLabel, statLabel, specialEffectLabel, attackTypeLabel, attackTypeDescription } from '../theme'
import { cx } from '../lib/format'

export function CharacterSheet(props: {
  ch: CharacterView
  party: PartyView
  busy?: boolean
  onLearnSkill?: (characterId: string, skillId: string) => void
  onClose: () => void
}) {
  const ch = props.ch
  const [skillTreeOpen, setSkillTreeOpen] = useState(false)
  const cm = classMeta(ch.class_id)
  const stats = ch.effective_stats ?? {}
  const resists = stats.resistances ?? {}
  const attrs = ch.attributes ?? stats.attributes ?? {}
  const statBreakdown = ch.stat_breakdown ?? {}
  const attributeBreakdown = ch.attribute_breakdown ?? {}
  const derived = ch.derived_stats ?? stats.derived ?? {}
  const maxHp = Number(stats.max_hp ?? ch.max_hp)
  const hp = Math.max(0, Math.min(maxHp, Number(ch.hp ?? maxHp)))
  const maxMana = Number(stats.max_mana ?? ch.max_mana ?? derived.mana ?? 0)
  const mana = Math.max(0, Math.min(maxMana, Number(ch.mana ?? maxMana)))
  const itemById = (id: string | null) => id ? props.party.inventory.find(i => i.instance_id === id) : undefined
  const skills: SkillSummary[] = ch.skill_summary ?? skillsForClass(ch.class_id).map(s => ({ ...s, uses_per_dungeon: s.uses_per_dungeon ?? s.uses ?? undefined, learned: true }))
  const learnedSkills = skills.filter(s => s.learned !== false)
  const unlockableSkills = skills.filter(s => s.learned === false && s.unlockable)
  const lockedSkills = skills.filter(s => s.learned === false && !s.unlockable)

  return (
    <div className="overlay" onClick={props.onClose}>
      <div className="sheet" onClick={e => e.stopPropagation()} style={{ '--accent': cm.accent } as CSSProperties}>
        <div className="sheet__hero">
          <CharacterAvatar ch={ch} size={64} dimmed={!ch.available} />
          <div className="sheet__title">
            <h2>{ch.name}</h2>
            <p className="muted">{cm.icon} {ch.class_name} · Lv.{ch.level} · {cm.position === 'front' ? '前排' : cm.position === 'mid' ? '中排' : cm.position === 'back' ? '后排' : '灵活'}</p>
          </div>
          <button className="iconBtn iconBtn--lg" onClick={props.onClose}>✕</button>
        </div>

        <div className="sheet__hp">
          <div className="sheet__resources">
            <div className="sheet__resourceBlock sheet__resourceBlock--hp" title="生命是角色的当前生存资源；生命归零会倒下，远征结束后会记录伤势与损耗。">
              <div className="sheet__resourceMeta"><span>❤️ 生命</span><b>{Math.round(hp)} / {maxHp}</b></div>
              <Bar value={hp} max={maxHp || 1} height={10} />
            </div>
            <div className="sheet__resourceBlock" title="法力是类似生命的可消耗资源。部分法术、治疗、净化与祝福技能会消耗法力；法力不足时角色会改用不耗法力的技能或普通攻击。">
              <div className="sheet__resourceMeta"><span>🔮 法力</span><b>{Math.round(mana)} / {maxMana}</b></div>
              <Bar value={mana} max={maxMana || 1} height={10} color="#5c9cff" />
            </div>
          </div>
          <div className="sheet__hpState">
            <Chip tone={ch.injury_state === 'healthy' ? 'good' : ch.injury_state === '重伤' ? 'danger' : 'warn'} icon="❤️">{injuryLabel(ch.injury_state)}</Chip>
            {!ch.available && <Chip tone="muted" icon="💤">不可上阵</Chip>}
            {ch.in_formation && <Chip tone="info" icon="🛡️">已上阵{ch.team_name ? ` · ${ch.team_name}` : ''}</Chip>}
            {ch.status_effects?.map((s, i) => <StatusChip key={i} type={s.type} duration={s.duration} potency={s.potency} />)}
          </div>
          <div className="sheet__exp">
            <span>经验 {ch.exp}/{ch.level * 100}</span>
            <Bar value={ch.exp} max={ch.level * 100} height={6} color="#5c9cff" />
          </div>
        </div>

        <div className="sheet__cols">
          <div className="sheet__col">
            <h3 className="sub">📊 核心属性</h3>
            <p className="hintText">大数字就是最终生效值；下方只显示基础与每级成长。</p>
            <div className="statBreakdownGrid">
              {STATS.map(s => {
                const b = statBreakdown[s.key] ?? fallbackBreakdown(stats[s.key] ?? 0)
                return (
                  <div className="statBreakdownCard" key={s.key} title={statBreakdownTitle(s.label, b)}>
                    <div className="statBreakdownCard__head">
                      <span>{s.icon} {s.label}</span>
                      <strong>{b.final}</strong>
                    </div>
                    <div className="breakdownRows">
                      <span>基础</span><b>{b.raw}</b>
                      <span>每级成长</span><b>{perLevelGrowthLabel(b)}</b>
                    </div>
                  </div>
                )
              })}
            </div>

            <h3 className="sub">📜 WOD 八维</h3>
            <div className="attributeSheetGrid">
              {ATTRIBUTES.map(a => {
                const b = attributeBreakdown[a.key] ?? fallbackBreakdown(attrs[a.key] ?? 0)
                return (
                  <div className="attributeSheetCard" key={a.key} title={attributeBreakdownTitle(a.label, a.desc ?? '', b)}>
                    <div className="attributeSheetCard__head">
                      <span>{a.icon} {a.label}</span>
                      <strong>{b.final}</strong>
                    </div>
                    <div className="attributeSheetCard__meta">
                      <span>基础 {b.raw}</span>
                      <span>每级 {perLevelGrowthLabel(b)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
            <h3 className="sub">🎯 技能焦点</h3>
            <p className="hintText">属性焦点不是第九种属性，而是技能调用八维属性的组合评分。</p>
            <div className="focusGrid">
              {FOCUS_META.map(f => (
                <div className="focusPill" key={f.key} title={`${f.desc} 关联属性：${f.attrs.join(' / ')}`}>
                  <span><b>{f.label}</b><em>{f.attrs.join(' / ')}</em></span>
                  <strong>{derived[f.scoreKey] ?? 0}</strong>
                </div>
              ))}
            </div>

            <h3 className="sub">🛡️ 抗性</h3>
            <div className="resistGrid">
              {(Object.keys(ELEMENTS) as Array<keyof typeof ELEMENTS>).map(k => (
                <ResistChip key={k} type={k} value={resists[k] ?? 0} />
              ))}
            </div>
          </div>

          <div className="sheet__col">
            <h3 className="sub">⚔️ 装备</h3>
            <div className="sheetEquip">
              {(['weapon', 'armor', 'trinket'] as const).map(slot => {
                const item = itemById(ch.equipment?.[slot] ?? null)
                return (
                  <div className="sheetEquip__slot" key={slot}>
                    <div className="sheetEquip__label"><span>{SLOT_ICON[slot]}</span><b>{SLOT_LABEL[slot]}</b></div>
                    {item ? (
                      <div className="sheetEquip__item">
                        <div className="sheetEquip__nameRow"><RarityTag rarity={item.rarity} /><b>{item.name}</b></div>
                        <div className="sheetEquip__stats">
                          {Object.entries(item.stats ?? {}).map(([k, v]) => <span key={k}>+{v} {statLabel(k)}</span>)}
                          {Object.entries(item.resistances ?? {}).filter(([, v]) => v).map(([k, v]) => (
                            <span key={k} style={{ color: (ELEMENTS as any)[k]?.color }}>{(ELEMENTS as any)[k]?.icon} +{v}</span>
                          ))}
                          {(item.special_effects ?? []).map(e => <span key={e}>✦ {specialEffectLabel(e)}</span>)}
                        </div>
                        <span className="muted">耐久 {item.durability}/{item.max_durability}</span>
                      </div>
                    ) : (
                      <span className="muted">— 未装备 —</span>
                    )}
                  </div>
                )
              })}
            </div>

            <h3 className="sub">🌳 技能树</h3>
            <p className="hintText">升级只获得技能点；技能学习、前置关系与消耗在独立技能树里处理。</p>
            <div className="skillTreeSummary">
              <div className="skillPointBar">
                <span>可用技能点</span>
                <b>{ch.skill_points ?? 0}</b>
              </div>
              <div className="skillTreeSummary__stats">
                <span><b>{learnedSkills.length}</b> 已学</span>
                <span><b>{unlockableSkills.length}</b> 可学</span>
                <span><b>{lockedSkills.length}</b> 锁定</span>
              </div>
              <button className="btn btn--accent" onClick={() => setSkillTreeOpen(true)}>打开技能树</button>
            </div>
            <div className="skillPreviewList">
              {learnedSkills.slice(0, 6).map(s => <span key={s.id} title={s.description || s.name}>{SKILL_ICON[s.type] ?? '✨'} {s.name}</span>)}
              {learnedSkills.length > 6 && <span>+{learnedSkills.length - 6}</span>}
            </div>
          </div>
        </div>
      </div>
      {skillTreeOpen && (
        <SkillTreeModal
          ch={ch}
          skills={skills}
          derived={derived}
          mana={mana}
          maxMana={maxMana}
          busy={props.busy}
          onLearnSkill={props.onLearnSkill}
          onClose={() => setSkillTreeOpen(false)}
        />
      )}
    </div>
  )
}

function SkillTreeModal(props: {
  ch: CharacterView
  skills: SkillSummary[]
  derived: Record<string, number>
  mana: number
  maxMana: number
  busy?: boolean
  onLearnSkill?: (characterId: string, skillId: string) => void
  onClose: () => void
}) {
  const rows = useMemo(() => skillTreeRows(props.skills), [props.skills])
  const columnCount = useMemo(() => skillTreeColumnCount(props.skills), [props.skills])
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const handleHover = useCallback((id: string | null) => setHoveredId(id), [])
  const handleSelect = useCallback((id: string) => setSelectedId(prev => prev === id ? null : id), [])
  const setNodeRef = useCallback((id: string, el: HTMLDivElement | null) => {
    if (el) nodeRefs.current[id] = el
    else delete nodeRefs.current[id]
  }, [])
  const focusId = hoveredId ?? selectedId
  const chainIds = useMemo(() => (focusId ? prerequisiteChain(props.skills, focusId) : null), [focusId, props.skills])
  const progress = useMemo(() => skillTreeProgress(props.skills), [props.skills])
  const byId = useMemo(() => new Map(props.skills.map(skill => [skill.id, skill])), [props.skills])
  const detailSkill = byId.get(focusId ?? '') ?? null
  const boardRef = useRef<HTMLDivElement | null>(null)
  const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({})
  const skillsRef = useRef(props.skills)
  skillsRef.current = props.skills
  const [lines, setLines] = useState<SkillTreeLine[]>([])

  // Connector geometry depends only on node layout (tier/x), fixed per class —
  // not on learned/hover state. Computed once on mount + resize; line color is
  // derived at render. No box-shadow / drop-shadow / dashoffset animations, so
  // hover and learning never cause repaint or reflow.
  useEffect(() => {
    const board = boardRef.current
    if (!board) return
    // ref 挂在未缩放的 .talentNode 包装器上；连线端点取它的几何中心。
    // 只有内部 .talentNode__orb 会随 hover 做 transform: scale()，包装器本身不动，
    // 所以用 getBoundingClientRect() 读包装器是稳定的，悬停期间端点不再抖动。
    // orb 在包装器顶部水平居中，故用包装器宽度的 1/2 作为 X、用一个固定 orb 半径
    // 作为 Y 偏移，近似 orb 几何中心；连接线视觉效果与原实现一致。
    const ORB_RADIUS = 31 // = talentNode__orb 宽 62px 的一半
    const update = () => {
      const boardRect = board.getBoundingClientRect()
      const next: SkillTreeLine[] = []
      for (const skill of skillsRef.current) {
        for (const prereq of skill.prerequisites ?? []) {
          const fromWrap = nodeRefs.current[prereq]
          const toWrap = nodeRefs.current[skill.id]
          if (!fromWrap || !toWrap) continue
          const fr = fromWrap.getBoundingClientRect()
          const tr = toWrap.getBoundingClientRect()
          next.push({
            from: prereq,
            to: skill.id,
            x1: fr.left + fr.width / 2 - boardRect.left,
            y1: fr.top + ORB_RADIUS - boardRect.top,
            x2: tr.left + tr.width / 2 - boardRect.left,
            y2: tr.top + ORB_RADIUS - boardRect.top,
          })
        }
      }
      setLines(next)
    }
    update()
    const ro = new ResizeObserver(update)
    ro.observe(board)
    let raf = 0
    const onScroll = () => {
      if (raf) return
      raf = requestAnimationFrame(() => { raf = 0; update() })
    }
    board.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      if (raf) cancelAnimationFrame(raf)
      board.removeEventListener('scroll', onScroll)
      ro.disconnect()
    }
  }, [])

  return (
    <div className="talentLayer" onClick={e => { e.stopPropagation(); props.onClose() }}>
      <div className="talentModal" onClick={e => e.stopPropagation()}>
        <div className="talentModal__head">
          <div>
            <span className="talentModal__eyebrow">天赋盘</span>
            <h2>✦ {props.ch.name} · {props.ch.class_name}</h2>
            <p>升级获得技能点；沿金色链路解锁主动技能、先攻公式与防御响应。</p>
          </div>
          <div className="talentModal__points">
            <span>技能点</span>
            <b>{props.ch.skill_points ?? 0}</b>
          </div>
          <button className="iconBtn iconBtn--lg" onClick={props.onClose}>✕</button>
        </div>

        <div className="talentLegend">
          <div className="talentLegend__dots">
            <span><i className="dot is-learned" />已掌握 <b>{progress.learned}</b></span>
            <span><i className="dot is-unlockable" />可学习 <b>{progress.unlockable}</b></span>
            <span><i className="dot is-locked" />锁定 <b>{progress.total - progress.learned - progress.unlockable}</b></span>
          </div>
          <div className="talentProgress" title={`已掌握 ${progress.learned} / 共 ${progress.total} 个技能`}>
            <span><b>{progress.learned}</b> / {progress.total}</span>
            <Bar value={progress.learned} max={progress.total || 1} height={6} color="#ffc14d" glow />
            {progress.unlockable > 0 && <em>{progress.unlockable} 可学</em>}
          </div>
        </div>

        <div className="talentBoard" ref={boardRef}>
          <svg className="talentLinks" aria-hidden="true">
            <defs>
              {/* 按状态各定义一个箭头 marker：marker 渲染在独立上下文，
                  无法通过 CSS 从引用 path 继承颜色，故每态一个 marker。 */}
              <marker id="talentArrowDefault" markerWidth="6.5" markerHeight="6.5" refX="5.5" refY="3.25" orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0,0 L6,3.25 L0,6.5 Z" fill="rgba(108, 126, 152, 0.5)" /></marker>
              <marker id="talentArrowLearned" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0,0 L6,3.5 L0,7 Z" fill="rgba(255, 193, 77, 0.85)" /></marker>
              <marker id="talentArrowUnlockable" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0,0 L6,3.5 L0,7 Z" fill="rgba(255, 193, 77, 0.7)" /></marker>
              <marker id="talentArrowPath" markerWidth="7.5" markerHeight="7.5" refX="6" refY="3.5" orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0,0 L6,3.5 L0,7 Z" fill="#ffc14d" /></marker>
            </defs>
            {lines.map(line => {
              const d = `M ${line.x1} ${line.y1} L ${line.x2} ${line.y2}`
              const fromSkill = byId.get(line.from)
              const toSkill = byId.get(line.to)
              const learned = !!fromSkill && fromSkill.learned !== false && toSkill?.learned !== false
              const unlockable = toSkill?.learned === false && toSkill?.unlockable === true
              const onPath = !!chainIds && chainIds.has(line.from) && chainIds.has(line.to)
              const dimmed = !!chainIds && !onPath
              const marker = onPath ? 'talentArrowPath'
                : learned ? 'talentArrowLearned'
                : unlockable ? 'talentArrowUnlockable'
                : 'talentArrowDefault'
              return (
                <path
                  key={`${line.from}-${line.to}`}
                  d={d}
                  markerEnd={`url(#${marker})`}
                  className={cx(
                    'talentLink',
                    learned && 'is-learned',
                    unlockable && 'is-unlockable',
                    onPath && 'is-path',
                    dimmed && 'is-dim',
                  )}
                />
              )
            })}
          </svg>
          {rows.map(([tier, rowSkills]) => {
            const tl = tierLabel(tier)
            return (
              <div className="talentTier" key={tier}>
                <div className="talentTier__label" title={tierTooltip(tier)}>
                  <b>{tl.short}</b><span>T{tier}</span>
                </div>
                <div className="talentTier__nodes" style={{ '--tree-cols': columnCount } as CSSProperties}>
                  {rowSkills.map(skill => {
                    const onPath = !chainIds || chainIds.has(skill.id)
                    return (
                      <SkillTreeNode
                        key={skill.id}
                        characterId={props.ch.id}
                        skill={skill}
                        busy={props.busy}
                        dimmed={!onPath}
                        onPath={chainIds ? chainIds.has(skill.id) : false}
                        selected={selectedId === skill.id}
                        onHover={handleHover}
                        onSelect={handleSelect}
                        setNodeRef={setNodeRef}
                      />
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>

        <TalentDetail
          skill={detailSkill}
          derived={props.derived}
          mana={props.mana}
          maxMana={props.maxMana}
          characterId={props.ch.id}
          level={props.ch.level}
          skillPoints={props.ch.skill_points ?? 0}
          skillsById={byId}
          busy={props.busy}
          onLearnSkill={props.onLearnSkill}
        />
      </div>
    </div>
  )
}

interface SkillTreeLine {
  from: string
  to: string
  x1: number
  y1: number
  x2: number
  y2: number
}

const SkillTreeNode = memo(function SkillTreeNode(props: {
  characterId: string
  skill: SkillSummary
  busy?: boolean
  dimmed?: boolean
  onPath?: boolean
  selected?: boolean
  onHover?: (id: string | null) => void
  onSelect?: (id: string) => void
  setNodeRef?: (id: string, el: HTMLDivElement | null) => void
}) {
  const s = props.skill
  const learned = s.learned !== false
  const unlockable = !learned && !!s.unlockable
  const locked = !learned && !unlockable
  const refCallback = useCallback((el: HTMLDivElement | null) => props.setNodeRef?.(s.id, el), [s.id, props.setNodeRef])
  const nodeStyle = { gridColumn: `${skillTreeColumn(s)} / span 1` }
  return (
    <div
      className={cx(
        'talentNode',
        learned && 'is-learned',
        unlockable && 'is-unlockable',
        locked && 'is-locked',
        props.onPath && 'is-path',
        props.dimmed && 'is-dim',
        props.selected && 'is-selected',
      )}
      style={nodeStyle}
      ref={refCallback}
      onMouseEnter={() => props.onHover?.(s.id)}
      onMouseLeave={() => props.onHover?.(null)}
      onClick={() => props.onSelect?.(s.id)}
    >
      <div className="talentNode__orb">
        <span className="talentNode__icon">{locked ? '🔒' : (SKILL_ICON[s.type] ?? '✨')}</span>
        {learned && <i className="talentNode__check" title="已掌握">✓</i>}
        {(s.skill_point_cost ?? 0) > 0 && <em className="talentNode__cost" title={`消耗 ${s.skill_point_cost} 技能点`}>{s.skill_point_cost}</em>}
      </div>
      <span className="talentNode__label">{s.name}</span>
    </div>
  )
})

function TalentDetail(props: {
  skill: SkillSummary | null
  derived: Record<string, number>
  mana: number
  maxMana: number
  characterId: string
  level: number
  skillPoints: number
  skillsById: Map<string, SkillSummary>
  busy?: boolean
  onLearnSkill?: (characterId: string, skillId: string) => void
}) {
  const s = props.skill
  const tags = useMemo(
    () => s ? skillMetaTags(s, props.derived, props.mana, props.maxMana).slice(0, 6) : [],
    [s, props.derived, props.mana, props.maxMana],
  )
  if (!s) {
    return (
      <div className="talentDetail talentDetail--empty">
        <div className="talentDetail__emptyCard">
          <span className="talentDetail__emptyIcon">✦</span>
          <div>
            <b>悬停或点选节点查看技能详情</b>
            <span>金色链路标示出解锁前置；暗色节点表示暂时无关。</span>
          </div>
        </div>
      </div>
    )
  }
  const learned = s.learned !== false
  const unlockable = !learned && !!s.unlockable
  const cost = s.skill_point_cost ?? 0
  const levelReq = Number(s.level_required ?? s.tree_tier ?? 1)
  const levelMet = levelReq <= props.level
  const pointsMet = cost <= props.skillPoints
  // 前置逐项状态：是否已学习
  const prereqStatus = (s.prerequisites ?? []).map(pid => {
    const p = props.skillsById.get(pid)
    return { id: pid, name: p?.name ?? pid, learned: p ? p.learned !== false : false }
  })
  const prereqMet = prereqStatus.every(p => p.learned)
  // 锁定原因细分：优先级 等级 > 技能点 > 前置 > 通用
  const blockReason = !learned && !unlockable
    ? (!levelMet ? `等级不足：需 Lv.${levelReq}（当前 Lv.${props.level}）`
      : !prereqMet ? '前置技能未全部掌握'
      : !pointsMet ? `技能点不足：需要 ${cost} 点（当前 ${props.skillPoints} 点）`
      : (s.unlock_reason ?? '未满足学习条件'))
    : ''
  return (
    <div className="talentDetail">
      <div className="talentDetail__head">
        <span className="talentDetail__icon" title={skillKindLabel(s.type)}>{SKILL_ICON[s.type] ?? '✨'}</span>
        <div className="talentDetail__title">
          <div className="talentDetail__nameRow">
            <b>{s.name}</b>
            {(s.skill_point_cost ?? 0) > 0 && <em className="talentDetail__cost">−{s.skill_point_cost} 点</em>}
            {!learned && <em className="talentDetail__lvlReq">Lv.{levelReq}</em>}
          </div>
          <span className="talentDetail__sub" title={skillHeaderTitle(s)}>
            {skillKindLabel(s.type)}{useLimitText(s)}{s.attribute_focus ? ` · ${focusLabel(s.attribute_focus)}` : ''}
          </span>
        </div>
        <div className="talentDetail__action">
          {learned ? (
            <span className="talentDetail__state is-learned">✓ 已掌握</span>
          ) : unlockable ? (
            <button className="btn btn--primary btn--sm" disabled={props.busy || !props.onLearnSkill} onClick={() => props.onLearnSkill?.(props.characterId, s.id)}>学习</button>
          ) : (
            <span className="talentDetail__state is-locked" title={blockReason}>{blockReason}</span>
          )}
        </div>
      </div>
      {s.description && <p className="talentDetail__desc">{s.description}</p>}
      <div className="talentDetail__tags">
        {tags.map(tag => <span key={tag.text} title={tag.title}>{tag.text}</span>)}
        {s.damage_types?.map(t => <span key={t} className="is-dmg" style={{ color: elementMeta(t).color }} title={damageTypeTitle(t)}>{elementMeta(t).icon} {elementMeta(t).label}</span>)}
      </div>
      {!learned && prereqStatus.length > 0 && (
        <div className="talentDetail__prereqChain" title="学习前需先掌握这些前置技能">
          <span className="talentDetail__prereqHead">⛓ 前置</span>
          <div className="talentDetail__prereqItems">
            {prereqStatus.map(p => (
              <span key={p.id} className={cx('talentDetail__prereqItem', !p.learned && 'is-missing')} title={p.learned ? '已掌握' : '未掌握'}>
                <i>{p.learned ? '✓' : '✗'}</i>{p.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function injuryLabel(state: string): string {
  return state === 'healthy' ? '健康' : state === '重伤' ? '重伤' : state === '轻伤' ? '轻伤' : state
}

function skillTreeRows(skills: SkillSummary[]): Array<[number, SkillSummary[]]> {
  const grouped = new Map<number, SkillSummary[]>()
  for (const skill of skills) {
    const tier = Number(skill.tree_y ?? skill.tree_tier ?? skill.level_required ?? 1)
    grouped.set(tier, [...(grouped.get(tier) ?? []), skill])
  }
  return Array.from(grouped.entries())
    .sort(([a], [b]) => a - b)
    .map(([tier, rows]) => [
      tier,
      rows.sort((a, b) => {
        const colRank = skillTreeColumn(a) - skillTreeColumn(b)
        if (colRank) return colRank
        return a.name.localeCompare(b.name)
      }),
    ])
}

function skillTreeColumn(skill: SkillSummary): number {
  const raw = Number(skill.tree_x)
  return Number.isFinite(raw) ? Math.max(1, Math.floor(raw) + 1) : 1
}

function skillTreeColumnCount(skills: SkillSummary[]): number {
  return Math.max(3, ...skills.map(skillTreeColumn))
}

/** 技能树层级主题名：每层给一个语义化短标签，配合 tooltip 解释定位。 */
function tierLabel(tier: number): { short: string; full: string } {
  const table = [
    { short: '基石', full: '基石层' },
    { short: '入门', full: '入门层' },
    { short: '进阶', full: '进阶层' },
    { short: '精通', full: '精通层' },
    { short: '终极', full: '终极层' },
  ]
  const idx = Math.min(Math.max(tier, 0), table.length - 1)
  return table[idx]
}

function tierTooltip(tier: number): string {
  const tip = [
    '基石层：基础攻击与职业被动，通常自动掌握。',
    '入门层：在基石之上分支出的早期技能。',
    '进阶层：需消耗技能点解锁的核心技能。',
    '精通层：高消耗的强力技能，多数依赖前置。',
    '终极层：技能树顶端的招牌技能。',
  ]
  const idx = Math.min(Math.max(tier, 0), tip.length - 1)
  return `T${tier} · ${tip[idx]}`
}

/** 递归收集某个节点的全部前置依赖（含自身），用于 hover 时高亮整条解锁链路。 */
function prerequisiteChain(skills: SkillSummary[], id: string): Set<string> {
  const byId = new Map(skills.map(s => [s.id, s]))
  const result = new Set<string>()
  const visit = (current: string) => {
    if (result.has(current)) return
    result.add(current)
    for (const p of byId.get(current)?.prerequisites ?? []) visit(p)
  }
  visit(id)
  return result
}

function skillTreeProgress(skills: SkillSummary[]): { learned: number; total: number; unlockable: number } {
  const total = skills.length
  let learned = 0
  let unlockable = 0
  for (const s of skills) {
    if (s.learned !== false) learned++
    else if (s.unlockable) unlockable++
  }
  return { learned, total, unlockable }
}

function fallbackBreakdown(value: number): StatBreakdown {
  const final = Number(value ?? 0)
  return { base: final, level_growth: 0, raw: final, bonus: 0, final, growth_per_level: 0, growth_text: '—' }
}

function signedBonus(value?: number): string {
  const n = Number(value ?? 0)
  if (n > 0) return `+${n}`
  if (n < 0) return String(n)
  return '0'
}

function perLevelGrowthLabel(b: StatBreakdown): string {
  return b.growth_text && b.growth_text !== '—' ? b.growth_text : '—'
}

function statBreakdownTitle(label: string, b: StatBreakdown): string {
  return [
    `${label}：最终 ${b.final}。`,
    `基础 ${b.raw}：当前等级未加成值，来源于 Lv.1 原始 ${b.base} 与累计等级成长 ${signedBonus(b.level_growth)}。`,
    `每级成长：${perLevelGrowthLabel(b)}。`,
    `最终值 ${b.final}：基础 + 装备/八维推导/状态等修正 ${signedBonus(b.bonus)}。`,
    b.raw_adjustment ? `额外基础修正 ${signedBonus(b.raw_adjustment)}。` : '',
  ].filter(Boolean).join('\n')
}

function attributeBreakdownTitle(label: string, desc: string, b: StatBreakdown): string {
  return [
    `${label}：${desc}`,
    `基础 ${b.raw}：当前等级未加成值，来源于 Lv.1 原始 ${b.base} 与累计等级成长 ${signedBonus(b.level_growth)}。`,
    `每级成长：${perLevelGrowthLabel(b)}。`,
    `最终值 ${b.final}：基础 + 额外修正 ${signedBonus(b.bonus)}。`,
  ].join('\n')
}

function skillKindLabel(type: string): string {
  const map: Record<string, string> = { damage: '伤害', heal: '治疗', cleanse: '净化', guard: '护卫', buff: '增益', support: '支援', debuff: '削弱', passive: '被动' }
  return map[type] ?? type
}

function useLimitText(s: SkillSummary): string {
  const uses = s.uses_per_dungeon
  if (uses == null || uses === 999) return ' · 无限制'
  return ` · ${uses} 次/副本`
}

type SkillTag = { text: string; title: string }

function skillMetaTags(s: SkillSummary, derived: Record<string, number>, mana: number, maxMana: number): SkillTag[] {
  const parts: SkillTag[] = []
  if (s.category) {
    parts.push({
      text: `类别：${s.category}`,
      title: `技能类别用于快速理解技能定位。${s.category}类技能通常决定它是输出、治疗、净化、支援还是削弱。`,
    })
  }
  if (s.attack_type) {
    parts.push({
      text: `攻击类型：${attackTypeLabel(s.attack_type)}`,
      title: `${attackTypeDescription(s.attack_type)}\n同一个攻击技能只拥有一种攻击类型；防御响应会按这个类型匹配。`,
    })
  }
  if (s.defense_types && s.defense_types.length > 0) {
    parts.push({
      text: `防御类型：${s.defense_types.map(attackTypeLabel).join('/')}`,
      title: `该技能可作为防御响应，对应这些攻击方式：${s.defense_types.map(t => `${attackTypeLabel(t)}（${attackTypeDescription(t)}）`).join('；')}。防御技能可以覆盖多种攻击类型。`,
    })
  }
  if (s.is_initiative_skill || s.speed_formula || (s.tags ?? []).some(t => t === 'initiative' || t === '先攻')) {
    parts.push({
      text: '标签：先攻',
      title: speedFormulaDescription(s),
    })
  }
  if (s.attribute_focus) {
    const score = derived[focusScoreKey(s.attribute_focus)] ?? 0
    parts.push({
      text: `属性焦点：${focusLabel(s.attribute_focus)}（当前 ${score}）`,
      title: `属性焦点不是单独属性，而是技能使用的八维组合。${focusLabel(s.attribute_focus)}由 ${focusCompositionLabel(s.attribute_focus)} 计算；当前角色该焦点评分为 ${score}。`,
    })
  }
  if (s.attribute_scale != null && s.attribute_scale !== 0) parts.push({
    text: `属性系数：${num(s.attribute_scale)}`,
    title: `属性系数决定“属性焦点评分”转化为技能加成的比例。数值越高，堆对应八维属性的收益越明显。`,
  })
  if (s.mana_cost != null && s.mana_cost > 0) parts.push({
    text: `法力消耗：${s.mana_cost}`,
    title: `释放该技能会消耗 ${s.mana_cost} 法力。当前法力 ${Math.round(mana)}/${maxMana}；法力不足时战斗 AI 会跳过该技能，改用其他可用技能或普通攻击。`,
  })
  if (s.power != null && s.power !== 0) parts.push({
    text: `威力：${signed(s.power)}`,
    title: `技能基础威力。伤害技能会加入伤害公式，治疗技能会加入治疗公式；高威力技能更适合爆发或关键回合。`,
  })
  if (s.accuracy_modifier != null && s.accuracy_modifier !== 0) parts.push({
    text: `命中：${signed(s.accuracy_modifier)}`,
    title: `命中修正会加到命中判定里。正数更稳定，负数代表技能更难命中但通常威力或范围更强。`,
  })
  if (s.target_rule) parts.push({
    text: `目标：${targetRuleLabel(s.target_rule)}`,
    title: targetRuleDescription(s.target_rule),
  })
  if (s.target_count != null) parts.push({
    text: `目标数：${s.target_count}`,
    title: `该技能最多影响 ${s.target_count} 个目标。若可选目标不足，则只影响实际存在的目标。`,
  })
  if (s.range) parts.push({
    text: `范围：${rangeLabel(s.range)}`,
    title: rangeDescription(s.range),
  })
  if (s.ignore_defense) parts.push({
    text: `穿防：${pct(s.ignore_defense)}`,
    title: `穿防表示结算时忽略目标一部分防御。${pct(s.ignore_defense)}穿防意味着目标防御只按剩余部分参与减伤。`,
  })
  if (s.defense_factor != null) parts.push({
    text: `防御系数：${num(s.defense_factor)}`,
    title: `防御系数表示目标防御参与抵消伤害的比例。越低越不怕高护甲，法术和穿甲技能通常较低。`,
  })
  if (s.crit_chance) parts.push({
    text: `暴击：${pct(s.crit_chance)}`,
    title: `技能自带暴击率。实际暴击还会受到属性焦点评分的额外影响；暴击会按暴击倍率放大伤害。`,
  })
  if (s.execute_bonus) parts.push({
    text: `斩杀增伤：${pct(s.execute_bonus)}`,
    title: `当目标生命低于 35% 时触发的额外伤害，适合收割精英或 Boss。`,
  })
  if (s.bonus_vs_status && s.bonus_vs_status.length > 0) parts.push({
    text: `状态增伤：${s.bonus_vs_status.map(t => statusMeta(t).label).join('/')}`,
    title: `目标带有这些状态时，本技能会获得额外伤害：${s.bonus_vs_status.map(t => statusMeta(t).label).join('、')}。适合和标记、破甲、脆弱、中毒等前置技能联动。`,
  })
  return parts
}

function effectTag(effect: { type: string; duration?: number; potency?: number; chance?: number }): SkillTag {
  const meta = statusMeta(effect.type)
  const bits = [meta.label]
  if (effect.duration != null) bits.push(`${effect.duration}回合`)
  if (effect.potency != null) bits.push(`强度${effect.potency}`)
  if (effect.chance != null) bits.push(`${pct(effect.chance)}概率`)
  const chance = effect.chance == null ? '必定尝试生效' : `触发概率 ${pct(effect.chance)}`
  const duration = effect.duration == null ? '即时或默认持续' : `持续 ${effect.duration} 回合`
  const potency = effect.potency == null ? '无强度数值' : `强度 ${effect.potency}`
  return {
    text: bits.join(' · '),
    title: `${meta.label}效果：${duration}，${potency}，${chance}。${statusDescription(effect.type)}`,
  }
}

function skillHeaderTitle(s: SkillSummary): string {
  return [
    `类型：${skillKindLabel(s.type)}。${skillKindDescription(s.type)}`,
    s.attack_type ? `攻击类型：${attackTypeLabel(s.attack_type)}。${attackTypeDescription(s.attack_type)}` : '',
    s.defense_types?.length ? `防御类型：${s.defense_types.map(attackTypeLabel).join('、')}。防御技能允许覆盖多个攻击方式。` : '',
    s.is_initiative_skill ? '先攻技能：在战术页选用后会改写角色速度值计算公式；不选则使用默认速度公式。' : '',
    `使用次数：${s.uses_per_dungeon == null || s.uses_per_dungeon === 999 ? '不限制' : `每个副本 ${s.uses_per_dungeon} 次`}。`,
    s.mana_cost ? `法力消耗：每次释放消耗 ${s.mana_cost}。` : '法力消耗：无。',
    s.attribute_focus ? `属性焦点：${focusLabel(s.attribute_focus)}，由 ${focusCompositionLabel(s.attribute_focus)} 组成。` : '',
  ].filter(Boolean).join('\n')
}

function targetRuleDescription(rule: string): string {
  const map: Record<string, string> = {
    front: '优先选择敌方前排；如果没有前排，则从剩余敌人中选择。',
    rear: '优先选择敌方后排，用于处理弓手、法师、刺客等威胁。',
    lowest_hp: '优先选择当前生命比例最低的目标，适合补刀。',
    highest_attack: '优先选择攻击最高的目标，适合控制或削弱危险敌人。',
    highest_defense: '优先选择防御最高的目标，适合破甲或穿防。',
    elite: '优先选择精英或 Boss；没有精英时退化为普通目标。',
    all: '可影响所有存活目标，实际数量可能被目标数限制。',
    cluster: '选择一组目标，通常最多影响 3 个敌人。',
    all_front: '优先影响前排和中排，适合压制阵线。',
    self: '只作用于施法者自身。',
    ally_all: '作用于所有存活友方，通常用于群体治疗或支援。',
    ally_low_hp: '优先选择生命比例最低的友方。',
    ally_status: '优先选择带有异常状态的友方。',
    ally_backline: '优先选择后排友方，常用于保护。',
  }
  return `目标规则：${targetRuleLabel(rule)}。${map[rule] ?? '按该技能定义的目标逻辑选择目标。'}`
}

function rangeDescription(range: string): string {
  const map: Record<string, string> = {
    melee: '近战技能通常适合前排角色使用，主要受近战焦点和物理防御影响。',
    ranged: '远程技能可打击后排或多个目标，通常更依赖命中和感知。',
    ally: '友方技能不会攻击敌人，用于治疗、净化、保护或增益。',
    self: '自身技能只影响施法者。',
    any: '任意距离技能，对站位限制较少。',
  }
  return `范围：${rangeLabel(range)}。${map[range] ?? '表示该技能可作用的距离/对象范围。'}`
}

function skillKindDescription(type: string): string {
  const map: Record<string, string> = {
    damage: '造成伤害，通常会读取威力、伤害类型、命中、目标与属性焦点。',
    heal: '恢复生命，主要读取威力、治疗焦点、属性系数与目标规则。',
    cleanse: '移除负面状态，优先选择异常友方。',
    guard: '进入护卫姿态，尝试替后排承受攻击。',
    buff: '强化自身，提供专注、强攻、盾墙、闪避等正面状态。',
    support: '支援友方，通常为群体屏障、抗性、再生或其他增益。',
    debuff: '削弱敌人，施加标记、脆弱、虚弱、减速等负面状态。',
    passive: '被动/规则型技能，不作为普通回合主动释放；部分被动需要在战术页选用后才改变公式。',
  }
  return map[type] ?? '特殊技能类型。'
}

function speedFormulaDescription(s: SkillSummary): string {
  const f = s.speed_formula
  if (!f) return '先攻技能：在战术页选用后会改写角色速度值计算公式；不选则使用默认速度公式。'
  const labels: Record<string, string> = { strength: '力量', constitution: '体质', dexterity: '灵巧', agility: '敏捷', intelligence: '智力', willpower: '意志', perception: '感知', charisma: '魅力' }
  const parts: string[] = []
  if (f.normal_speed_weight || f.speed_weight) parts.push(`常规速度×${f.normal_speed_weight ?? f.speed_weight}`)
  const attrs = f.attribute_weights ?? f.attributes ?? {}
  for (const [key, value] of Object.entries(attrs)) parts.push(`${labels[key] ?? key}×${value}`)
  if (f.level_weight) parts.push(`等级×${f.level_weight}`)
  if (f.flat || f.base) parts.push(String(f.flat ?? f.base))
  return `先攻技能：在战术页选用后速度值按「${f.label ?? s.name}」计算：${parts.join(' + ') || '常规速度'}；不选时仍使用默认速度公式。`
}

function statusDescription(type: string): string {
  const map: Record<string, string> = {
    poison: '中毒会造成持续毒伤，受毒抗影响。',
    bleed: '流血会造成持续物理伤害，受物理/流血抗性体系影响。',
    burn: '燃烧会造成持续火焰伤害，受火抗影响。',
    curse: '诅咒会降低行动者命中/表现，也可能放大战斗风险。',
    armor_break: '破甲会降低目标有效防御，提升后续物理输出。',
    stun: '眩晕会让目标跳过一次行动。',
    slow: '减速会降低速度和闪避表现。',
    marked: '标记会降低目标闪避，并让目标受到更多伤害。',
    vulnerable: '脆弱会削弱目标防御并放大后续伤害。',
    enfeeble: '虚弱会降低目标攻击。',
    guarding: '护卫提高保护后排的成功率。',
    shield_wall: '盾墙提高防御并降低受到的伤害。',
    focus: '专注提高命中表现。',
    might: '强攻提高攻击。',
    barrier: '屏障提供伤害吸收和少量抗性收益。',
    ward: '圣佑提高魔法、诅咒、毒与火焰抗性。',
    evasion_up: '闪避提升可提高回避能力。',
    regeneration: '再生会在回合结算时恢复生命。',
  }
  return map[type] ?? ''
}

function damageTypeTitle(type: string): string {
  const meta = elementMeta(type)
  return `${meta.label}伤害：结算时读取目标的${meta.label}抗性；多伤害类型会平均参考对应抗性。`
}

function signed(value: number): string {
  return value > 0 ? `+${value}` : String(value)
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`
}

function num(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
}
