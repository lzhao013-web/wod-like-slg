import type { PlanAction } from '../../types/game'
import { Chip } from '../Chips'
import { cx } from '../../lib/format'

export function PlanPanel(props: {
  plan: PlanAction[]
  pointsLeft: number
  onClear: () => void
  onEndDay: () => void
  busy: boolean
}) {
  const used = props.plan.length
  return (
    <section className="panel planPanel">
      <div className="panel__head"><h2>📜 今日远征计划</h2><span className="muted">剩余次数 {props.pointsLeft} / 2</span></div>

      <div className="planTimeline">
        {[0, 1].map(i => {
          const action = props.plan[i]
          if (!action) {
            return (
              <div className="planSlot planSlot--empty" key={i}>
                <span className="planSlot__idx">{i + 1}</span>
                <span className="planSlot__empty">空位 —— 前往「副本情报」安排侦察或挑战</span>
              </div>
            )
          }
          const tacticText = action.type === 'challenge'
            ? ` · 战术：${action.tactic_scheme_name ?? '当前战术'}`
            : ''
          return (
            <div className={cx('planSlot', `planSlot--${action.type}`)} key={action.id || i}>
              <span className="planSlot__idx">{i + 1}</span>
              <span className="planSlot__icon">{action.type === 'scout' ? '🔭' : '⚔️'}</span>
              <div className="planSlot__body">
                <b>{action.type === 'scout' ? '侦察' : '挑战'} · {action.dungeon_name}</b>
                <span className="muted">{action.team_name ?? '队伍'}出征 · {action.type === 'scout' ? '解锁敌方阵型与层结构' : `正面进攻，按计划自动战斗${tacticText}`}</span>
              </div>
            </div>
          )
        })}
      </div>

      <div className="planHint">
        {props.plan.length === 0 ? (
          <span className="muted">今日未安排任何行动 —— 直接「结束当天」则全队休整并恢复 HP。每支队伍每天最多出征一次。</span>
        ) : (
          <Chip icon="💡" tone="info">结算将按计划顺序执行；每个行动绑定一支队伍，队员不会重复出征。</Chip>
        )}
      </div>

      <div className="detail__actions">
        <button className="btn btn--ghost" onClick={props.onClear} disabled={props.busy || props.plan.length === 0}>🗑 清空计划</button>
        <button className="btn btn--primary" onClick={props.onEndDay} disabled={props.busy}>
          {props.plan.length > 0 ? `⚔️ 结算远征（${used}）` : '🏕️ 结束当天·休整'}
        </button>
      </div>
    </section>
  )
}
