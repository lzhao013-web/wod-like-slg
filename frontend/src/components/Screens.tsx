import { useState } from 'react'

export function StartScreen(props: { hasSave: boolean; onStart: (seed?: number) => void; onContinue: () => void; onOpenSaveManager?: () => void; busy: boolean }) {
  const [seed, setSeed] = useState('')
  const [showSeed, setShowSeed] = useState(false)

  return (
    <div className="screen screen--start">
      <div className="screen__bg" />
      <div className="screen__card">
        <div className="screen__crest">🏰</div>
        <p className="screen__eyebrow">单机 · 战术经营 · 30 天局制</p>
        <h1 className="screen__title">暗影远征</h1>
        <p className="screen__subtitle">
          组建你的六人冒险小队，在 30 天内侦察、配阵、征战，<br />
          攻克最终 Boss —— 或在消耗战中倒下。
        </p>

        <div className="screen__features">
          <Feature icon="🔍" title="侦察 → 决策" text="先摸清敌人阵型与词缀，再决定配装与站位" />
          <Feature icon="⚔️" title="自动回合战斗" text="速度排序、状态、抗性、破甲 —— 谋定而后战" />
          <Feature icon="📊" title="逐层战报复盘" text="每一层、每一回合都可回看与归因" />
        </div>

        <div className="screen__actions">
          {props.hasSave && (
            <button className="btn btn--ghost" onClick={props.onContinue} disabled={props.busy}>继续上一局</button>
          )}
          <button className="btn btn--ghost" onClick={props.onOpenSaveManager} disabled={props.busy || !props.onOpenSaveManager}>读取/管理存档</button>
          <button className="btn btn--primary" onClick={() => props.onStart(seed ? Number(seed) : undefined)} disabled={props.busy}>
            {props.busy ? '准备中…' : props.hasSave ? '开启新局' : '开始游戏'}
          </button>
        </div>

        <button className="screen__seedToggle" onClick={() => setShowSeed(s => !s)}>
          {showSeed ? '收起随机种子' : '↳ 指定随机种子（可复现）'}
        </button>
        {showSeed && (
          <input className="screen__seedInput" inputMode="numeric" placeholder="留空则随机" value={seed}
            onChange={e => setSeed(e.target.value.replace(/[^0-9]/g, ''))} />
        )}
      </div>
    </div>
  )
}

function Feature(props: { icon: string; title: string; text: string }) {
  return (
    <div className="screen__feature">
      <span className="screen__featureIcon">{props.icon}</span>
      <div>
        <b>{props.title}</b>
        <p>{props.text}</p>
      </div>
    </div>
  )
}

export function EndScreen(props: { victory: boolean; state: any; onRestart: () => void; onReset: () => void; busy: boolean }) {
  const { state } = props
  return (
    <div className={`screen screen--end ${props.victory ? 'is-victory' : 'is-defeat'}`}>
      <div className="screen__bg" />
      <div className="screen__card">
        <div className="screen__crest">{props.victory ? '🏆' : '💀'}</div>
        <h1 className="screen__title">{props.victory ? '远征胜利' : '远征终结'}</h1>
        <p className="screen__subtitle">
          {props.victory
            ? '你的小队在最终巢室击溃了黑暗。故事将被传颂。'
            : state?.defeat_reason || '队伍在远征中力竭。下次会更好。'}
        </p>

        <div className="screen__summary">
          <Summary label="坚持天数" value={`${state?.day ?? '?'} / ${state?.max_day ?? 30}`} />
          <Summary label="剩余金币" value={state?.gold ?? 0} />
          <Summary label="战报数量" value={Array.isArray(state?.reports) ? state.reports.length : '?'} />
        </div>

        <div className="screen__actions">
          <button className="btn btn--primary" onClick={props.onRestart} disabled={props.busy}>返回标题</button>
          <button className="btn btn--ghost" onClick={props.onReset} disabled={props.busy}>重置存档</button>
        </div>
      </div>
    </div>
  )
}

function Summary(props: { label: string; value: any }) {
  return (
    <div className="screen__summaryItem">
      <span>{props.label}</span>
      <b>{props.value}</b>
    </div>
  )
}
