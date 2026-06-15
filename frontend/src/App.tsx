import { useState } from 'react'
import { useGame } from './state/useGame'
import { TopBar } from './components/TopBar'
import { SideNav, type NavId } from './components/SideNav'
import { Toasts } from './components/Toasts'
import { StartScreen, EndScreen } from './components/Screens'
import { DayResults } from './components/DayResults'
import { CharacterSheet } from './components/CharacterSheet'
import { OverviewPanel } from './components/panels/OverviewPanel'
import { DungeonsPanel } from './components/panels/DungeonsPanel'
import { PartyPanel } from './components/panels/PartyPanel'
import { TacticsPanel } from './components/panels/TacticsPanel'
import { PlanPanel } from './components/panels/PlanPanel'
import { ReportsPanel } from './components/panels/ReportsPanel'
import { ShopPanel } from './components/panels/ShopPanel'
import type { CharacterView } from './types/game'

export default function App() {
  const game = useGame()
  const [nav, setNav] = useState<NavId>('overview')
  const [sheetChar, setSheetChar] = useState<CharacterView | null>(null)

  if (game.phase === 'loading') {
    return <div className="boot"><div className="boot__crest">🏰</div><p>正在集结远征队…</p></div>
  }

  if (game.phase === 'start') {
    return (
      <>
        <StartScreen
          hasSave={!!game.state && !game.state.victory && !game.state.defeat}
          busy={game.busy}
          onStart={(seed) => game.newGame(seed)}
          onContinue={() => game.returnToPlay()}
        />
        <Toasts toasts={game.toasts} onDismiss={game.dismissToast} />
      </>
    )
  }

  if (game.phase === 'ended' && game.state) {
    return (
      <>
        <EndScreen
          victory={game.state.victory}
          state={game.state}
          busy={game.busy}
          onRestart={() => game.gotoStart()}
          onReset={() => game.resetGame()}
        />
        <Toasts toasts={game.toasts} onDismiss={game.dismissToast} />
      </>
    )
  }

  // phase === 'playing' or 'dayResults' (overlay shown during play)
  const state = game.state
  if (!state || !game.party) {
    return <div className="boot"><div className="boot__crest">🏰</div><p>加载中…</p></div>
  }

  const partyMembers = game.party.members
  const sheetCharLive = sheetChar ? (partyMembers.find(m => m.id === sheetChar.id) ?? sheetChar) : null

  return (
    <div className="app">
      <TopBar state={state} planCount={game.plan.length} busy={game.busy} onEndDay={game.endDay} />

      {game.error && <div className="appError">{game.error}</div>}

      <div className="appBody">
        <SideNav
          active={nav}
          onChange={setNav}
          badges={{ dungeons: game.dungeons.filter(d => !d.scouted && !d.cleared).length, reports: game.reports.length, plan: game.plan.length }}
        />
        <main className="appMain">
          {nav === 'overview' && (
            <OverviewPanel
              state={state}
              dungeons={game.dungeons}
              reports={game.reports}
              partySize={partyMembers.length}
              onPickDungeon={(id) => { game.setSelectedDungeon(id); setNav('dungeons') }}
              onPickReport={(id) => { game.setSelectedReport(id); setNav('reports') }}
            />
          )}
          {nav === 'dungeons' && (
            <DungeonsPanel
              dungeons={game.dungeons}
              selected={game.selectedDungeon}
              onSelect={game.setSelectedDungeon}
              detail={game.dungeonDetail}
              tacticSchemes={game.party.tactic_schemes ?? []}
              onScout={(id) => game.act(() => apiPlanScout(id), { toast: () => ({ tone: 'info', text: '已安排侦察。' } as any) })}
              onChallenge={(id, tacticSchemeId) => game.act(() => apiPlanChallenge(id, tacticSchemeId), { toast: (v: any) => ({ tone: 'accent' as any, text: `已安排挑战${v?.tactic_scheme_name ? ` · ${v.tactic_scheme_name}` : ''}。` } as any) })}
              busy={game.busy}
              pointsLeft={state.expedition_points_left}
            />
          )}
          {nav === 'party' && (
            <PartyPanel
              party={game.party}
              busy={game.busy}
              onFormation={(teamId, f) => game.act(() => apiFormation(teamId, f), { toast: () => ({ tone: 'success', text: '阵型已保存。' } as any) })}
              onFormations={(f) => game.act(() => apiFormations(f), { toast: () => ({ tone: 'success', text: '队伍编组已保存。' } as any) })}
              onEquip={(cid, item, slot) => game.act(() => apiEquip(cid, item, slot), { toast: () => ({ tone: 'success', text: '装备已更换。' } as any) })}
              onInspect={setSheetChar}
            />
          )}
          {nav === 'tactics' && (
            <TacticsPanel
              party={game.party}
              busy={game.busy}
              onTactics={(p) => game.act(() => apiTactics(p), { toast: () => ({ tone: 'success', text: '战术已保存。' } as any) })}
              onSaveScheme={(p) => game.act(() => apiSaveTacticScheme(p), { toast: (v: any) => ({ tone: 'success', text: `战术方案「${v?.scheme?.name ?? '方案'}」已保存。` } as any) })}
              onLoadScheme={(id) => game.act(() => apiLoadTacticScheme(id), { toast: (v: any) => ({ tone: 'success', text: `已读取战术方案「${v?.scheme?.name ?? '方案'}」。` } as any) })}
              onDeleteScheme={(id) => game.act(() => apiDeleteTacticScheme(id), { toast: () => ({ tone: 'info', text: '战术方案已删除。' } as any) })}
              onInspect={setSheetChar}
            />
          )}
          {nav === 'plan' && (
            <PlanPanel plan={game.plan} pointsLeft={state.expedition_points_left} onClear={() => game.act(apiClearPlan)} onEndDay={game.endDay} busy={game.busy} />
          )}
          {nav === 'reports' && (
            <ReportsPanel reports={game.reports} selected={game.selectedReport} onSelect={game.setSelectedReport} detail={game.reportDetail} />
          )}
          {nav === 'shop' && (
            <ShopPanel
              shop={game.shop}
              gold={state.gold}
              partySize={partyMembers.length}
              onBuy={(id) => game.act(() => apiBuy(id), { toast: (v: any) => ({ tone: 'success', text: `购得 ${v?.acquired?.name ?? '物品'}。` } as any) })}
              onRecruit={(id) => game.act(() => apiRecruit(id), { toast: (v: any) => ({ tone: 'success', text: `${v?.character?.name ?? '新成员'} 已加入队伍。` } as any) })}
              busy={game.busy}
            />
          )}
        </main>
      </div>

      {game.phase === 'dayResults' && game.lastDayResult && (
        <DayResults
          reports={game.lastDayResult.reports}
          partyMembers={partyMembers}
          day={state.day - 1 /* already advanced */}
          finished={!!(game.lastDayResult.state.victory || game.lastDayResult.state.defeat)}
          onContinue={game.returnToPlay}
        />
      )}

      {sheetCharLive && (
        <CharacterSheet
          ch={sheetCharLive}
          party={game.party}
          skillEssence={state.skill_essence ?? state.materials?.skill_essence ?? 0}
          busy={game.busy}
          onLearnSkill={(cid, sid) => game.act(() => apiLearnSkill(cid, sid), { toast: () => ({ tone: 'success', text: '技能已学习。' } as any) })}
          onUpgradeSkill={(cid, sid, choiceId) => game.act(() => apiUpgradeSkill(cid, sid, choiceId), { toast: () => ({ tone: 'success', text: '技能已精进。' } as any) })}
          onPromote={(cid, targetClassId) => game.act(() => apiPromoteCharacter(cid, targetClassId), { toast: () => ({ tone: 'success', text: '转职完成。' } as any) })}
          onClose={() => setSheetChar(null)}
        />
      )}

      <Toasts toasts={game.toasts} onDismiss={game.dismissToast} />
    </div>
  )
}

// Thin wrappers so App reads cleanly; the api module is imported lazily to avoid an unused warning.
import { api } from './api/client'
const apiPlanScout = (id: string) => api.planScout(id)
const apiPlanChallenge = (id: string, tacticSchemeId?: string) => api.planChallenge(id, tacticSchemeId)
const apiFormation = (teamId: string, f: Record<string, string | null>) => api.formation(f, teamId)
const apiFormations = (f: Record<string, Record<string, string | null>>) => api.formations(f)
const apiTactics = (p: any) => api.tactics(p)
const apiLearnSkill = (cid: string, sid: string) => api.learnSkill(cid, sid)
const apiUpgradeSkill = (cid: string, sid: string, choiceId?: string) => api.upgradeSkill(cid, sid, choiceId)
const apiPromoteCharacter = (cid: string, targetClassId: string) => api.promoteCharacter(cid, targetClassId)
const apiSaveTacticScheme = (p: any) => apiJson('/party/tactic-schemes', { method: 'POST', body: JSON.stringify(p) })
const apiLoadTacticScheme = (id: string) => apiJson(`/party/tactic-schemes/${id}/load`, { method: 'POST' })
const apiDeleteTacticScheme = (id: string) => apiJson(`/party/tactic-schemes/${id}`, { method: 'DELETE' })
const apiEquip = (cid: string, item: string | null, slot?: string) => api.equip(cid, item, slot)
const apiClearPlan = () => api.clearPlan()
const apiBuy = (id: string) => api.buy(id)
const apiRecruit = (id: string) => api.recruit(id)

async function apiJson(url: string, options: RequestInit = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      message = body.detail || message
    } catch {}
    throw new Error(message)
  }
  return res.json()
}
