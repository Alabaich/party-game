import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, store } from '../lib/api'

export default function Register() {
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [showPopup, setShowPopup] = useState(false)
  const [pendingDrinking, setPendingDrinking] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [showLogin, setShowLogin] = useState(false)
  const [players, setPlayers] = useState([])

  // Re-entry: if UUID is in localStorage — go straight to dashboard.
  useEffect(() => {
    const u = store.getUuid()
    if (u) nav(`/u/${u}`)
  }, [nav])

  async function submit(isDrinking) {
    if (!name.trim()) { setErr('Enter your name'); return }
    setBusy(true); setErr('')
    try {
      const user = await api.register(name.trim(), isDrinking)
      store.setUuid(user.id)
      nav(`/u/${user.id}`)
    } catch (e) {
      setErr(e.message || 'Registration error')
    } finally { setBusy(false) }
  }

  function onChoose(isDrinking) {
    if (!name.trim()) { setErr('Enter your name first'); return }
    if (isDrinking) { submit(true) }
    else { setPendingDrinking(false); setShowPopup(true) }
  }

  async function openLogin() {
    setShowLogin(true)
    try { setPlayers(await api.players()) } catch { /* ignore */ }
  }

  return (
    <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 text-cream font-body">
      <div className="animate-float mb-2 text-6xl">🍻</div>
      <h1 className="font-display font-extrabold text-5xl sm:text-6xl text-zest text-center leading-none mb-1">
        PARTY
      </h1>
      <p className="text-mint mb-10 tracking-widest text-sm">QUEST · CHALLENGE · CHAOS</p>

      <div className="w-full max-w-sm space-y-5">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your name"
          className="w-full bg-ink border-2 border-cream/30 focus:border-zest rounded-2xl px-5 py-4 text-lg outline-none transition-colors placeholder:text-cream/40"
        />

        <p className="text-center text-cream/80 pt-2">Will you be drinking alcohol tonight?</p>
        <div className="grid grid-cols-2 gap-3">
          <button disabled={busy} onClick={() => onChoose(true)}
            className="bg-mint text-ink font-display font-bold text-xl py-4 rounded-2xl active:scale-95 transition-transform disabled:opacity-50">
            YES 🍷
          </button>
          <button disabled={busy} onClick={() => onChoose(false)}
            className="bg-cream/10 border-2 border-cream/30 text-cream font-display font-bold text-xl py-4 rounded-2xl active:scale-95 transition-transform disabled:opacity-50">
            NO 🙅
          </button>
        </div>

        {err && <p className="text-punch text-center text-sm">{err}</p>}

        <button onClick={openLogin}
          className="w-full text-cream/50 text-sm underline underline-offset-4 pt-4">
          Already registered — log back in
        </button>
      </div>

      {/* Fun popup for those who chose "No" */}
      {showPopup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-6">
          <div className="animate-pop bg-punch text-cream rounded-3xl p-8 max-w-sm text-center shadow-2xl border-4 border-zest">
            <div className="text-6xl mb-4">🍻</div>
            <p className="font-display font-extrabold text-2xl leading-tight mb-6">
              Too bad, but you'll still have to drink!
            </p>
            <button
              disabled={busy}
              onClick={() => { setShowPopup(false); submit(false) }}
              className="w-full bg-zest text-ink font-display font-bold text-lg py-3 rounded-2xl active:scale-95 transition-transform disabled:opacity-50">
              Fine 😅
            </button>
          </div>
        </div>
      )}

      {/* Log in as existing player */}
      {showLogin && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/70 px-4 pb-4">
          <div className="animate-pop bg-ink border-2 border-cream/20 rounded-3xl p-6 max-w-sm w-full max-h-[70vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-display font-bold text-xl text-zest">Pick yourself</h2>
              <button onClick={() => setShowLogin(false)} className="text-cream/50 text-2xl">×</button>
            </div>
            {players.length === 0 && <p className="text-cream/50 text-sm">No players yet</p>}
            <div className="space-y-2">
              {players.map((p) => (
                <button key={p.id}
                  onClick={() => { store.setUuid(p.id); nav(`/u/${p.id}`) }}
                  className="w-full text-left bg-cream/5 hover:bg-cream/10 rounded-xl px-4 py-3 text-cream">
                  {p.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
