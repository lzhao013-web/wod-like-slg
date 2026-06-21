import type { GameStateView } from '../types/game'
import { materialIcon } from '../theme'
import { PointPips } from './Chips'
import { Bar } from './Bar'
import { num, cx } from '../lib/format'

export function TopBar(props: {
  state: GameStateView
  planCount: number
  busy: boolean
  onEndDay: () => void
  onOpenSaveManager?: () => void
}) {
  const { state } = props
  const dayFrac = Math.min(1, (state.day - 1) / Math.max(1, state.max_day))
  const canEnd = !state.victory && !state.defeat && !props.busy

  return (
    <header className="hud">
      <div className="hud__brand">
        <span className="hud__logo">🏰</span>
        <div className="hud__brandText">
          <b>暗影远征</b>
          <span>类 WOD 战术经营</span>
        </div>
      </div>

      <div className="hud__center">
        <div className="hud__dayBlock" data-guide-id="hud-day">
          <div className="hud__dayHead">
            <span className="hud__dayLabel">第 <b>{state.day}</b> / {state.max_day} 天</span>
            <span className="hud__dayHint">{state.final_unlocked ? '最终挑战已解锁' : `${Math.max(0, state.max_day - state.day)} 天后结束`}</span>
          </div>
          <Bar value={state.day - 1} max={state.max_day} fraction={dayFrac} height={8} color="#ffb300" />
        </div>

        <div className="hud__resources" data-guide-id="hud-resources">
          <div className="res" title="金币">
            <span className="res__icon">🪙</span>
            <b>{num(state.gold)}</b>
          </div>
          <div className="res res--mat" title="技能精华">
            <span className="res__icon">{materialIcon('技能精华')}</span>
            <b>{num(state.skill_essence ?? state.materials?.skill_essence ?? 0)}</b>
          </div>
          <div className="res res--points" title="远征次数">
            <span className="res__icon">⚔️</span>
            <PointPips left={state.expedition_points_left} total={2} />
          </div>
          {Object.entries(state.materials_display).filter(([k]) => k !== '技能精华').slice(0, 4).map(([k, v]) => (
            <div className="res res--mat" key={k} title={k}>
              <span className="res__icon">{materialIcon(k)}</span>
              <b>{v}</b>
            </div>
          ))}
        </div>
      </div>

      <div className="hud__actions">
        <button className="hud__saveBtn" type="button" onClick={props.onOpenSaveManager} disabled={props.busy || !props.onOpenSaveManager}>
          💾 存档
        </button>
        <button className={cx('hud__endBtn', props.planCount > 0 && 'is-active')} data-guide-id="hud-end-day" onClick={props.onEndDay} disabled={!canEnd}>
          <span className="hud__endIcon">{props.planCount > 0 ? '⚔️' : '🏕️'}</span>
          <span>{props.planCount > 0 ? `结算远征 ×${props.planCount}` : '结束当天·休整'}</span>
        </button>
      </div>
    </header>
  )
}
