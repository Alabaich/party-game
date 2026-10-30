import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { host } from '../../lib/api'
import { useTheme, THEME_EMOJI } from '../../lib/ui'

export function useHostGuard() {
  const nav = useNavigate()
  const [me, setMe] = useState(null)
  useEffect(() => {
    host.me().then(setMe).catch(() => nav('/admin', { replace: true }))
  }, [nav])
  return me
}

export function gameStatus(g) {
  if (g.is_draft) return ['draft', 'bg-cream/10 text-cream/60']
  if (!g.started) return ['open for sign-up', 'bg-zest/20 text-zest']
  if (!g.places_revealed) return ['live', 'bg-mint/20 text-mint']
  return ['finished', 'bg-cream/10 text-cream/60']
}

export function StatusBadge({ game }) {
  const [label, cls] = gameStatus(game)
  return <span className={`shrink-0 text-xs px-2 py-1 rounded-lg ${cls}`}>{label}</span>
}

export default function AdminGames() {
  const nav = useNavigate()
  const me = useHostGuard()
  const [games, setGames] = useState([])
  const [packs, setPacks] = useState([])
  const [name, setName] = useState('')
  const [theme, setTheme] = useState('halloween')
  const [pack, setPack] = useState('halloween')
  const [err, setErr] = useState('')
  useTheme('party')

  useEffect(() => {
    if (!me) return
    host.games().then(setGames).catch((e) => setErr(e.message))
    host.packs().then(setPacks).catch(() => {})
  }, [me])

  async function create(e) {
    e.preventDefault()
    setErr('')
    try {
      const g = await host.createGame({ name, theme, pack })
      nav(`/admin/games/${g.id}?tab=settings`)
    } catch (e2) { setErr(e2.message) }
  }

  async function logout() { await host.logout().catch(() => {}); nav('/admin') }

  if (!me) return null
  return (
    <div className="relative z-10 min-h-screen text-cream font-body px-5 py-8 max-w-3xl mx-auto">
      <header className="flex items-center justify-between mb-8">
        <h1 className="font-display font-extrabold text-3xl text-zest">My games</h1>
        <div className="flex items-center gap-3 text-xs text-cream/50">
          <span className="hidden sm:inline">{me.email}</span>
          <button onClick={logout} className="btn-ghost py-2 text-xs">Log out</button>
        </div>
      </header>

      <form onSubmit={create} className="card p-5 mb-8 space-y-3">
        <p className="label">New game</p>
        <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Prism Halloween @ 80 & 100 Bond" className="field" />
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="block"><span className="label">Theme</span>
            <select value={theme} onChange={(e) => { setTheme(e.target.value); if (packs.some((p) => p.id === e.target.value)) setPack(e.target.value) }} className="field mt-1">
              <option value="halloween">🎃 Halloween</option>
              <option value="diwali">🪔 Diwali</option>
              <option value="party">🍻 Party</option>
            </select>
          </label>
          <label className="block"><span className="label">Starter tasks</span>
            <select value={pack} onChange={(e) => setPack(e.target.value)} className="field mt-1">
              {packs.map((p) => <option key={p.id} value={p.id}>{p.title} ({p.task_count})</option>)}
            </select>
          </label>
        </div>
        {err && <p className="text-punch text-sm">{err}</p>}
        <button className="btn-primary">Create game</button>
      </form>

      <div className="space-y-3">
        {games.map((g) => (
          <Link key={g.id} to={`/admin/games/${g.id}${g.is_draft ? "?tab=settings" : ""}`} className="card p-4 flex items-center gap-4 hover:border-zest/50 transition-colors">
            <span className="text-3xl">{THEME_EMOJI[g.settings.theme]}</span>
            <div className="flex-1 min-w-0">
              <p className="font-display font-bold text-lg truncate">{g.name}</p>
              <p className="text-cream/50 text-xs">
                code <span className="text-zest font-bold tracking-widest">{g.code}</span> · {g.player_count} players · {g.task_count} tasks
              </p>
            </div>
            <StatusBadge game={g} />
          </Link>
        ))}
        {games.length === 0 && <p className="text-cream/40 text-center py-6">No games yet</p>}
      </div>
    </div>
  )
}
