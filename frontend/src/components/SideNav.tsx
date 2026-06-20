import { cx } from '../lib/format'

export type NavId = 'overview' | 'dungeons' | 'party' | 'tactics' | 'reports' | 'shop' | 'recruits' | 'quests'

const NAV: Array<{ id: NavId; label: string; icon: string; hint: string }> = [
  { id: 'overview', label: '指挥台', icon: '🗺️', hint: '每日总览' },
  { id: 'dungeons', label: '副本情报', icon: '⚔️', hint: '侦察·挑战·出征' },
  { id: 'quests', label: '委托·任务', icon: '📜', hint: '主线·日常·隐藏' },
  { id: 'party', label: '队伍编成', icon: '🛡️', hint: '阵型·配装' },
  { id: 'tactics', label: '战术计划', icon: '🎯', hint: '先攻·开场·防御' },
  { id: 'reports', label: '战报复盘', icon: '📊', hint: '历史战报' },
  { id: 'shop', label: '集市·商店', icon: '🪙', hint: '买·卖·分解' },
  { id: 'recruits', label: '酒馆·招募', icon: '🏰', hint: '招募·解雇' },
]

export function SideNav(props: {
  active: NavId
  onChange: (id: NavId) => void
  badges?: Partial<Record<NavId, number>>
}) {
  return (
    <nav className="sideNav">
      {NAV.map(item => {
        const badge = props.badges?.[item.id] ?? 0
        return (
          <button
            key={item.id}
            className={cx('sideNav__item', props.active === item.id && 'is-active')}
            onClick={() => props.onChange(item.id)}
          >
            <span className="sideNav__icon">{item.icon}</span>
            <span className="sideNav__text">
              <b>{item.label}</b>
              <span>{item.hint}</span>
            </span>
            {badge > 0 && <span className="sideNav__badge">{badge}</span>}
          </button>
        )
      })}
    </nav>
  )
}
