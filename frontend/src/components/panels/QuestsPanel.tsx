import { useEffect, useMemo, useState } from 'react'
import type { CSSProperties } from 'react'
import type { GameStateView, QuestListView, QuestView, QuestStatus, QuestType } from '../../types/game'
import { Chip } from '../Chips'
import { EquipmentHover } from '../EquipmentTooltip'
import { materialIcon, materialName } from '../../theme'
import { cx, num } from '../../lib/format'

type TabId = 'active' | 'available' | 'daily' | 'completed' | 'expired'
type TypeFilter = 'all' | 'main' | 'side' | 'daily' | 'hidden'

const TABS: Array<{ id: TabId; label: string; icon: string }> = [
  { id: 'active', label: '进行中', icon: '⚔️' },
  { id: 'available', label: '可接受', icon: '❗' },
  { id: 'daily', label: '日常委托', icon: '🗓️' },
  { id: 'completed', label: '已完成', icon: '✅' },
  { id: 'expired', label: '已过期', icon: '⌛' },
]

export function QuestsPanel(props: {
  state: GameStateView
  quests: QuestListView
  onAccept: (id: string) => void
  onCompleteObjective: (questId: string, objectiveId: string) => void
  onStartGuide?: (quest: QuestView) => void
  onClaim: (id: string) => void
  onAbandon: (id: string) => void
  busy: boolean
}) {
  const { quests, state } = props
  const [tab, setTab] = useState<TabId>('active')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const [detailId, setDetailId] = useState<string | null>(null)

  // All quests in one flat list (backend already hides unrevealed hidden ones).
  const allQuests: QuestView[] = useMemo(() => [
    ...quests.available, ...quests.active, ...quests.completed,
    ...quests.claimed, ...quests.expired,
  ], [quests])

  // A quest belongs to a tab by its status (and daily quests have their own tab,
  // so they are pulled out of available/active/completed into the daily tab).
  const tabBuckets = useMemo(() => groupByTab(allQuests), [allQuests])
  const tabCounts = useMemo(() => {
    const c: Record<TabId, number> = { active: 0, available: 0, daily: 0, completed: 0, expired: 0 }
    for (const t of TABS) c[t.id] = tabBuckets[t.id].length
    return c
  }, [tabBuckets])

  // NOTE: we intentionally do NOT auto-redirect away from an empty tab.
  // If a user clicks a tab, that's a deliberate choice and the empty-state
  // hint is the right response. Auto-redirecting (e.g. after claiming the
  // last quest) would also hijack a manual click and bounce them away.

  const visible = tabBuckets[tab].filter(q => matchType(q, typeFilter))
  const detailQuest = detailId ? allQuests.find(q => q.id === detailId) ?? null : null
  const isHistoryTab = tab === 'completed' || tab === 'expired'

  return (
    <div className="questsLayout" data-guide-id="quests-panel">
      <section className="panel">
        <div className="panel__head">
          <h2>📜 委托任务</h2>
          <div className="questsHead__chips">
            {quests.summary.available_count > 0 && <Chip icon="❗" tone="accent">可接 {quests.summary.available_count}</Chip>}
            {quests.summary.active_count > 0 && <Chip icon="⚔️" tone="info">进行中 {quests.summary.active_count}</Chip>}
            {quests.summary.claimable_count > 0 && <Chip icon="🎁" tone="good">可领 {quests.summary.claimable_count}</Chip>}
          </div>
        </div>
        <p className="muted questsHint">
          主线与支线构成固定剧情链；日常委托每日刷新、需手动接受；隐藏任务满足条件后才会显现。点击任务卡片可查看详情。
        </p>

        <div className="questTabs" role="tablist" data-guide-id="quest-tabs">
          {TABS.map(t => (
            <button key={t.id} role="tab" aria-selected={tab === t.id}
              className={cx('questTab', tab === t.id && 'is-active')}
              onClick={() => setTab(t.id)}>
              <span className="questTab__icon">{t.icon}</span>
              <span className="questTab__label">{t.label}</span>
              {tabCounts[t.id] > 0 && <span className="questTab__count">{tabCounts[t.id]}</span>}
            </button>
          ))}
        </div>

        {/* Type filter only matters on the non-history tabs; history is tags. */}
        {!isHistoryTab && visible.length > 0 && (
          <div className="questFilterGroup questFilterGroup--inline">
            <span className="muted questFilterGroup__label">类型</span>
            <div className="questFilterGroup__btns">
              <FilterBtn active={typeFilter === 'all'} onClick={() => setTypeFilter('all')}>全部</FilterBtn>
              <FilterBtn active={typeFilter === 'main'} onClick={() => setTypeFilter('main')}>主线</FilterBtn>
              <FilterBtn active={typeFilter === 'side'} onClick={() => setTypeFilter('side')}>支线</FilterBtn>
              <FilterBtn active={typeFilter === 'daily'} onClick={() => setTypeFilter('daily')}>日常</FilterBtn>
              <FilterBtn active={typeFilter === 'hidden'} onClick={() => setTypeFilter('hidden')}>隐藏</FilterBtn>
            </div>
          </div>
        )}
      </section>

      <section className="panel questTabBody">
        {visible.length === 0 ? (
          <p className="muted">{emptyHint(tab)}</p>
        ) : isHistoryTab ? (
          // History tabs render as a tidy tag cloud; each opens the detail modal.
          <div className="questDoneList">
            {visible.map(q => (
              <button key={q.id} type="button"
                className={cx('questDoneTag', 'is-clickable', q.type === 'hidden' && 'is-hidden')}
                onClick={() => setDetailId(q.id)}>
                {typeIcon(q.type)} {q.title}
              </button>
            ))}
          </div>
        ) : (
          <div className="questList" data-guide-id="quest-list">
            {visible.map(q => (
              <QuestCard key={q.id} q={q} day={state.day} busy={props.busy}
                onOpen={setDetailId} onAccept={props.onAccept} onClaim={props.onClaim} onAbandon={props.onAbandon} />
            ))}
          </div>
        )}
      </section>

      {detailQuest && (
        <QuestDetail
          q={detailQuest}
          day={state.day}
          busy={props.busy}
          onClose={() => setDetailId(null)}
          onAccept={props.onAccept}
          onCompleteObjective={props.onCompleteObjective}
          onStartGuide={q => {
            setDetailId(null)
            props.onStartGuide?.(q)
          }}
          onClaim={props.onClaim}
          onAbandon={props.onAbandon}
        />
      )}
    </div>
  )
}

function QuestCard(props: {
  q: QuestView
  day: number
  busy: boolean
  onOpen: (id: string) => void
  onAccept?: (id: string) => void
  onClaim?: (id: string) => void
  onAbandon?: (id: string) => void
}) {
  const { q, day } = props
  const accent = questAccent(q)
  const expiring = q.type === 'daily' && q.status !== 'claimed' && q.expires_day != null && q.expires_day <= day

  return (
    <article className="questCard" style={{ '--accent': accent } as CSSProperties} data-guide-id={`quest-card-${q.template_id}`}>
      <button type="button" className="questCard__main" onClick={() => props.onOpen(q.id)}>
        <header className="questCard__head">
          <b>{q.title}</b>
          <span className="questCard__tags">
            <Tag tone={q.type}>{typeLabel(q.type, q.story_kind)}</Tag>
            <Tag tone="status">{q.status_label}</Tag>
            {q.revealed_from_hidden && <Tag tone="hidden">隐藏揭示</Tag>}
            {expiring && <Tablert tone="warn">今日截止</Tablert>}
          </span>
        </header>
        {q.description && <p className="questCard__desc">{q.description}</p>}
        <ul className="questCard__objs">
          {q.objectives.map(o => (
            <li key={o.id} className={cx('questObj', o.completed && 'is-done')}>
              <span className="questObj__check">{o.completed ? '✔' : '○'}</span>
              <span className="questObj__label">{o.label}</span>
              <span className="questObj__count">{Math.min(o.current, o.required)}/{o.required}</span>
            </li>
          ))}
        </ul>
        <RewardLine q={q} compact />
      </button>
      <div className="questCard__actions">
        {q.status === 'available' && props.onAccept && (
          <button className="btn btn--accent btn--sm" data-guide-id={`quest-accept-${q.template_id}`} disabled={props.busy} onClick={() => props.onAccept?.(q.id)}>接受任务</button>
        )}
        {q.status === 'completed' && props.onClaim && (
          <button className="btn btn--accent btn--sm" data-guide-id={`quest-claim-${q.template_id}`} disabled={props.busy} onClick={() => props.onClaim?.(q.id)}>🎁 领取奖励</button>
        )}
        {q.status === 'active' && props.onAbandon && (
          <button className="btn btn--ghost btn--sm" disabled={props.busy} onClick={() => props.onAbandon?.(q.id)}>
            {q.type === 'daily' ? '放弃' : '重置进度'}
          </button>
        )}
        <button className="btn btn--ghost btn--sm" onClick={() => props.onOpen(q.id)}>详情</button>
      </div>
    </article>
  )
}

/** Full-detail overlay modal for any quest, including claimed/expired history. */
function QuestDetail(props: {
  q: QuestView
  day: number
  busy: boolean
  onClose: () => void
  onAccept?: (id: string) => void
  onCompleteObjective?: (questId: string, objectiveId: string) => void
  onStartGuide?: (quest: QuestView) => void
  onClaim?: (id: string) => void
  onAbandon?: (id: string) => void
}) {
  const { q } = props
  const accent = questAccent(q)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') props.onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [props])

  return (
    <div className="overlay" onClick={props.onClose}>
      <article className="questSheet" style={{ '--accent': accent } as CSSProperties} onClick={e => e.stopPropagation()}>
        <header className="questSheet__hero">
          <span className="questSheet__icon">{typeIcon(q.type)}</span>
          <div className="questSheet__title">
            <h2>{q.title}</h2>
            <div className="questCard__tags">
              <Tag tone={q.type}>{typeLabel(q.type, q.story_kind)}</Tag>
              <Tag tone="status">{q.status_label}</Tag>
              {q.revealed_from_hidden && <Tag tone="hidden">隐藏揭示</Tag>}
              {q.chain_id && <Tag tone="muted">剧情链 · {chainLabel(q.chain_id)}</Tag>}
            </div>
          </div>
          <button className="questSheet__close" onClick={props.onClose} aria-label="关闭">✕</button>
        </header>

        <div className="questSheet__body">
          {q.description && <p className="questSheet__desc">{q.description}</p>}

          {(q.dialogue?.length ?? 0) > 0 && (
            <>
              <h4>剧情对话</h4>
              <div className="questDialogue">
                {q.dialogue!.map((line, i) => (
                  <div className="questDialogue__line" key={i}>
                    <b>{line.speaker}</b>
                    <span>{line.text}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {(q.guide_sections?.length ?? 0) > 0 && (
            <>
              <div className="questGuideTitleRow">
                <h4>学院导览</h4>
                {(q.guide_steps?.length ?? 0) > 0 && props.onStartGuide && (
                  <button
                    className="btn btn--accent btn--sm"
                    data-guide-id={`quest-start-guide-${q.template_id}`}
                    disabled={props.busy}
                    title={q.status === 'active' ? '启动聚焦高亮与引导点击；完成后会标记教学目标' : '启动聚焦高亮与引导点击；仅进行中的手动目标会自动完成'}
                    onClick={() => props.onStartGuide?.(q)}
                  >
                    🎓 开始交互导览
                  </button>
                )}
              </div>
              <div className="questGuideGrid">
                {q.guide_sections!.map((g, i) => (
                  <section className="questGuide" key={i}>
                    <div className="questGuide__head">
                      <b>{g.title}</b>
                      {g.nav_hint && <span>{g.nav_hint}</span>}
                    </div>
                    {g.body && <p>{g.body}</p>}
                    {(g.bullets?.length ?? 0) > 0 && (
                      <ul>{g.bullets!.map((b, bi) => <li key={bi}>{b}</li>)}</ul>
                    )}
                  </section>
                ))}
              </div>
            </>
          )}

          <div className="questSheet__meta">
            <MetaRow label="创建" value={dayLabel(q.created_day)} />
            <MetaRow label="接受" value={dayLabel(q.accepted_day)} />
            <MetaRow label="完成" value={dayLabel(q.completed_day)} />
            <MetaRow label="领取" value={dayLabel(q.claimed_day)} />
            {q.expires_day != null && <MetaRow label="截止" value={dayLabel(q.expires_day)} />}
          </div>

          <h4>目标</h4>
          <ul className="questSheet__objs">
            {q.objectives.map(o => (
              <li key={o.id} className={cx('questObj', 'questObj--big', o.completed && 'is-done')}>
                <span className="questObj__check">{o.completed ? '✔' : '○'}</span>
                <span className="questObj__label">{o.label}</span>
                <span className="questObj__count">{Math.min(o.current, o.required)}/{o.required}</span>
                {q.status === 'active' && o.kind === 'manual_ack' && !o.completed && props.onCompleteObjective && (
                  <button className="btn btn--accent btn--sm questObj__action" data-guide-id={`quest-manual-ack-${o.id}`} disabled={props.busy} onClick={() => props.onCompleteObjective?.(q.id, o.id)}>
                    标记已读
                  </button>
                )}
              </li>
            ))}
          </ul>

          <h4>奖励</h4>
          <RewardLine q={q} />

          {q.next_quests.length > 0 && (
            <>
              <h4>解锁后续</h4>
              <p className="muted questSheet__note">领取后将揭示：{q.next_quests.map(id => `「${questIdLabel(id)}」`).join('、')}</p>
            </>
          )}
          {q.linked_dungeon_ids.length > 0 && (
            <>
              <h4>关联副本</h4>
              <p className="muted questSheet__note">接受任务后生成的专属副本（persistent）：{q.linked_dungeon_ids.join('、')}</p>
            </>
          )}
        </div>

        {(q.status === 'available' || q.status === 'completed' || q.status === 'active') && (
          <footer className="questSheet__foot">
            {q.status === 'available' && props.onAccept && (
              <button className="btn btn--accent" disabled={props.busy} onClick={() => props.onAccept?.(q.id)}>接受任务</button>
            )}
            {q.status === 'completed' && props.onClaim && (
              <button className="btn btn--accent" disabled={props.busy} onClick={() => props.onClaim?.(q.id)}>🎁 领取奖励</button>
            )}
            {q.status === 'active' && props.onAbandon && (
              <button className="btn btn--ghost" disabled={props.busy} onClick={() => props.onAbandon?.(q.id)}>
                {q.type === 'daily' ? '放弃' : '重置进度'}
              </button>
            )}
            <button className="btn btn--ghost" onClick={props.onClose}>关闭</button>
          </footer>
        )}
      </article>
    </div>
  )
}

function MetaRow(props: { label: string; value: string }) {
  if (props.value === '—') return null
  return (
    <div className="questSheet__metaRow">
      <span className="muted">{props.label}</span>
      <span>{props.value}</span>
    </div>
  )
}

function FilterBtn(props: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" className={cx('questFilterBtn', props.active && 'is-active')} onClick={props.onClick}>
      {props.children}
    </button>
  )
}

function RewardLine({ q, compact }: { q: QuestView; compact?: boolean }) {
  const r = q.rewards
  const equipment = r.equipment ?? []
  if (!r.gold && !r.exp && Object.keys(r.materials || {}).length === 0 && equipment.length === 0) {
    return <p className="muted questCard__rewards">奖励：无</p>
  }
  return (
    <div className="questCard__rewards">
      {!compact && <span className="muted">奖励：</span>}
      {r.gold > 0 && <span className="rewardPill">🪙 {num(r.gold)}</span>}
      {r.exp > 0 && <span className="rewardPill">✨ 经验 {num(r.exp)}</span>}
      {Object.entries(r.materials || {}).map(([k, v]) => v > 0 && (
        <span className="rewardPill" key={k}>{materialIcon(k)} {materialName(k)} ×{v}</span>
      ))}
      {equipment.map((e, i) => {
        const pill = <span className="rewardPill" key={`${e.id}-${i}`}>🎖️ {e.name}</span>
        return e.preview ? <EquipmentHover key={`${e.id}-${i}`} item={e.preview}>{pill}</EquipmentHover> : pill
      })}
    </div>
  )
}

function Tag(props: { tone: string; children: React.ReactNode }) {
  return <span className={cx('questTag', `is-${props.tone}`)}>{props.children}</span>
}
// Small inline tag variant (kept name distinct from Tag to avoid confusion).
function Tablert(props: { tone: string; children: React.ReactNode }) {
  return <span className={cx('questTag', `is-${props.tone}`)}>{props.children}</span>
}

// --- grouping / labels ---

function groupByTab(quests: QuestView[]): Record<TabId, QuestView[]> {
  const buckets: Record<TabId, QuestView[]> = { active: [], available: [], daily: [], completed: [], expired: [] }
  for (const q of quests) {
    // Daily quests have their own dedicated tab regardless of status, so the
    // player always sees today's commissions in one place.
    if (q.type === 'daily' && q.status !== 'expired') {
      buckets.daily.push(q)
      continue
    }
    if (q.status === 'active') buckets.active.push(q)
    else if (q.status === 'available') buckets.available.push(q)
    else if (q.status === 'completed') buckets.active.push(q) // claimable shows under 进行中
    else if (q.status === 'claimed') buckets.completed.push(q)
    else if (q.status === 'expired') buckets.expired.push(q)
  }
  for (const key of Object.keys(buckets) as TabId[]) {
    buckets[key].sort((a, b) => sortRank(a) - sortRank(b) || a.id.localeCompare(b.id))
  }
  return buckets
}

// Rank so claimable (completed) quests float to the top of the active tab,
// then active story quests, etc.
function sortRank(q: QuestView): number {
  if (q.status === 'completed') return 0 // 待领取 first
  if (q.status === 'active' && q.type !== 'daily') return 1
  if (q.status === 'active') return 2
  if (q.status === 'available' && q.type === 'story') return 1
  if (q.status === 'available') return 2
  return 3
}

function matchType(q: QuestView, f: TypeFilter): boolean {
  if (f === 'all') return true
  if (f === 'daily' || f === 'hidden') return q.type === f
  if (f === 'main') return q.type === 'story' && q.story_kind !== 'side'
  if (f === 'side') return q.type === 'story' && q.story_kind === 'side'
  return true
}

function emptyHint(tab: TabId): string {
  switch (tab) {
    case 'active': return '暂无进行中的任务，去「可接受」接一单吧。'
    case 'available': return '当前没有可接受的新任务。推进剧情或等到次日刷新日常委托。'
    case 'daily': return '今日的日常委托已全部处理，明天见。'
    case 'completed': return '还没有完成的任务记录。'
    case 'expired': return '没有过期任务，保持得不错。'
  }
}

function dayLabel(day: number | null): string {
  return day == null ? '—' : `第 ${day} 天`
}

function chainLabel(chainId: string): string {
  if (chainId === 'delta_tactical_academy') return '德尔塔战术学院'
  if (chainId === 'main_campaign') return '主线战役'
  if (chainId === 'local_contracts') return '本地委托'
  return chainId
}

function questIdLabel(id: string): string {
  return id.replace(/_/g, ' ')
}

function typeLabel(type: QuestType | string, storyKind: string): string {
  if (type === 'story') return storyKind === 'side' ? '支线' : '主线'
  if (type === 'daily') return '日常'
  if (type === 'hidden') return '隐藏'
  return type
}

function typeIcon(type: QuestType | string): string {
  if (type === 'hidden') return '✨'
  if (type === 'daily') return '🗓️'
  return '📜'
}

function questAccent(q: QuestView): string {
  if (q.type === 'hidden') return '#b388ff'
  if (q.type === 'daily') return '#4dd0e1'
  if (q.story_kind === 'side') return '#81c784'
  return '#ffb74d'
}
