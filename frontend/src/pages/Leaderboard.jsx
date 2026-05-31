import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

function fmtDuration(sec) {
  if (sec == null) return '—'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const pad = (n) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

export default function Leaderboard() {
  const [items, setItems] = useState([])
  const [game, setGame] = useState(null)
  const [starting, setStarting] = useState(false)
  const [err, setErr] = useState('')

  const load = useCallback(async () => {
    try {
      const [lb, gs] = await Promise.all([api.leaderboard(), api.gameStatus()])
      setItems(lb); setGame(gs)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 7000)
    return () => clearInterval(id)
  }, [load])

  async function onStart() {
    if (!confirm('Start the game? All players will be assigned tasks and the timer will begin.')) return
    setStarting(true); setErr('')
    try { await api.startGame(); await load() }
    catch (e) { setErr(e.message || 'Failed to start') }
    finally { setStarting(false) }
  }

  const totalTasks = items.length
    ? Math.max(...items.map((i) => i.completed_count), 7)
    : 7

  return (
    <div className="relative z-10 min-h-screen text-cream font-body px-5 py-6 max-w-lg mx-auto">
      <header className="flex items-center justify-between mb-6">
        <h1 className="font-display font-extrabold text-3xl text-zest">🏆 Leaderboard</h1>
        <Link to="/slideshow" className="bg-cream/10 px-3 py-2 rounded-xl text-xs">📺 Slideshow</Link>
      </header>

      {/* START button — shown while game hasn't started */}
      {game && !game.started && (
        <div className="mb-6 bg-punch/15 border-2 border-punch/40 rounded-2xl p-5 text-center">
          <p className="text-cream/80 mb-1">Players registered: <b className="text-zest">{game.player_count}</b></p>
          <p className="text-cream/50 text-sm mb-4">Press when everyone is ready</p>
          <button onClick={onStart} disabled={starting || game.player_count === 0}
            className="w-full bg-punch text-cream font-display font-extrabold text-2xl py-4 rounded-2xl active:scale-95 transition-transform disabled:opacity-50">
            {starting ? 'STARTING…' : '🚀 START GAME'}
          </button>
          {err && <p className="text-punch text-sm mt-3">{err}</p>}
        </div>
      )}

      {game && game.started && (
        <p className="text-mint text-center text-sm mb-4 tracking-widest">GAME IN PROGRESS ▶</p>
      )}

      <div className="space-y-2">
        {items.map((it, idx) => (
          <div key={it.user_id}
            className={`flex items-center gap-3 rounded-2xl p-4 border-2 ${
              it.finished ? 'bg-zest/10 border-zest/40' : 'bg-cream/5 border-cream/15'
            }`}>
            <div className="font-display font-extrabold text-xl w-7 text-center text-cream/60">
              {idx + 1}
            </div>
            <div className="flex-1">
              <p className="font-display font-bold text-lg">
                {it.is_winner && '👑 '}{it.name}
              </p>
            </div>
            {it.finished ? (
              <div className="text-right">
                <p className="text-mint font-bold tabular-nums">{fmtDuration(it.duration_seconds)}</p>
                <p className="text-cream/40 text-xs">time</p>
              </div>
            ) : (
              <div className="text-right">
                <p className="text-zest font-bold tabular-nums">{it.completed_count}/{totalTasks}</p>
                <p className="text-cream/40 text-xs">done</p>
              </div>
            )}
          </div>
        ))}
        {items.length === 0 && <p className="text-cream/40 text-center py-10">Nothing here yet</p>}
      </div>

      <Link to="/" className="block text-center text-cream/40 text-sm mt-8 underline underline-offset-4">
        Back to home
      </Link>
    </div>
  )
}
