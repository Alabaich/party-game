import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, store } from '../lib/api'
import { useTheme, THEME_EMOJI, Center, Modal, Prizes } from '../lib/ui'

export default function Join() {
  const { code: rawCode } = useParams()
  const code = rawCode.toUpperCase()
  const nav = useNavigate()
  const [game, setGame] = useState(null)
  const [err, setErr] = useState('')
  const [step, setStep] = useState('consent')
  const [agreed, setAgreed] = useState(false)
  const [showDoc, setShowDoc] = useState(false)
  const [name, setName] = useState('')
  const [answers, setAnswers] = useState({})
  const [busy, setBusy] = useState(false)
  const [showPick, setShowPick] = useState(false)
  const [players, setPlayers] = useState([])
  useTheme(game?.settings.theme)

  useEffect(() => {
    const mine = store.playerFor(code)
    if (mine) { nav(`/u/${mine}`, { replace: true }); return }
    api.game(code)
      .then((g) => { setGame(g); if (!g.settings.consent.enabled) setStep('details') })
      .catch((e) => setErr(e.status === 404 ? 'Game not found. Check the code.' : e.message))
  }, [code, nav])

  if (err && !game) return <Center>{err}</Center>
  if (!game) return <Center>Loading…</Center>

  const s = game.settings
  const emoji = THEME_EMOJI[s.theme] || '🎉'

  if (!game.can_join) {
    return (
      <Center>
        <div>
          <div className="text-6xl mb-4">{emoji}</div>
          <p className="font-display font-bold text-2xl text-zest mb-2">{game.name}</p>
          <p>This game has already started and isn't accepting new players.</p>
        </div>
      </Center>
    )
  }

  function setAnswer(id, v) { setAnswers((a) => ({ ...a, [id]: v })); setErr('') }

  async function submit(e) {
    e.preventDefault()
    if (!name.trim()) { setErr('Enter your name'); return }
    for (const q of s.questions) {
      const v = answers[q.id]
      if (q.required && (v === undefined || v === '')) { setErr(`Please answer: ${q.text}`); return }
    }
    setBusy(true); setErr('')
    try {
      const user = await api.register(code, {
        name: name.trim(), answers, consent_sha256: game.consent_sha256,
      })
      store.setPlayer(code, user.id)
      nav(`/u/${user.id}`)
    } catch (e2) {
      if (e2.message.includes('Photo & Media Release')) {
        // the host changed the text meanwhile: show the new version
        const g = await api.game(code); setGame(g); setAgreed(false); setStep('consent')
      }
      setErr(e2.message)
    } finally { setBusy(false) }
  }

  async function openPick() {
    setShowPick(true)
    try { setPlayers(await api.players(code)) } catch { /* ignore */ }
  }

  return (
    <div className="relative z-10 min-h-screen flex flex-col items-center px-6 py-10 text-cream font-body">
      <div className="animate-float text-6xl mb-2">{emoji}</div>
      <h1 className="font-display font-extrabold text-4xl text-zest text-center leading-tight mb-2">{game.name}</h1>
      {s.welcome && <p className="text-cream/70 text-center max-w-sm mb-6 whitespace-pre-line">{s.welcome}</p>}

      <div className="w-full max-w-sm space-y-5 mt-2">
        {step === 'consent' ? (
          <>
            <div className="card p-5 space-y-4">
              <p className="label">Step 1 of 2</p>
              <p className="font-display font-bold text-xl">{s.consent.title}</p>
              <p className="text-cream/80 text-sm leading-relaxed">{s.consent.summary}</p>
              <button type="button" onClick={() => setShowDoc(true)}
                className="text-zest underline underline-offset-4 text-sm">
                📄 Read the full document
              </button>
              <label className="flex items-start gap-3 cursor-pointer select-none">
                <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)}
                  className="mt-1 w-5 h-5 accent-[rgb(var(--c-zest))] shrink-0" />
                <span className="text-sm">{s.consent.checkbox_label}</span>
              </label>
            </div>
            <button disabled={!agreed} onClick={() => { setStep('details'); setErr('') }}
              className="btn-primary w-full text-lg">Continue</button>
          </>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            {s.consent.enabled && <p className="label">Step 2 of 2</p>}
            <div>
              <p className="label mb-2">Your name</p>
              <input value={name} onChange={(e) => { setName(e.target.value); setErr('') }}
                placeholder="First name" maxLength={40} className="field text-lg" />
            </div>
            {s.questions.map((q) => (
              <QuestionField key={q.id} q={q} value={answers[q.id]} onChange={(v) => setAnswer(q.id, v)} />
            ))}
            {err && <p className="text-punch text-center text-sm">{err}</p>}
            <button disabled={busy} className="btn-primary w-full text-lg">
              {busy ? 'Joining…' : `Join the game ${emoji}`}
            </button>
            {s.consent.enabled && (
              <button type="button" onClick={() => setStep('consent')}
                className="w-full text-cream/40 text-xs underline underline-offset-4">Back</button>
            )}
          </form>
        )}

        {step === 'consent' && err && <p className="text-punch text-center text-sm">{err}</p>}

        {s.prizes.some((p) => p.title) && (
          <div className="pt-4">
            <p className="label mb-2 text-center">Prizes</p>
            <Prizes prizes={s.prizes} />
          </div>
        )}

        <button onClick={openPick} className="w-full text-cream/40 text-sm underline underline-offset-4 pt-2">
          Already joined on another phone?
        </button>
      </div>

      {showDoc && (
        <Modal wide onClose={() => setShowDoc(false)}>
          <h2 className="font-display font-bold text-2xl text-zest mb-4">{s.consent.title}</h2>
          <div className="text-sm leading-relaxed whitespace-pre-wrap text-cream/90">{s.consent.body}</div>
          <button onClick={() => { setAgreed(true); setShowDoc(false) }} className="btn-primary w-full mt-6">
            I have read it and agree
          </button>
          <button onClick={() => setShowDoc(false)} className="btn-ghost w-full mt-2">Close</button>
        </Modal>
      )}

      {showPick && (
        <Modal onClose={() => setShowPick(false)}>
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-display font-bold text-xl text-zest">Pick yourself</h2>
            <button onClick={() => setShowPick(false)} className="text-cream/50 text-2xl">×</button>
          </div>
          {players.length === 0 && <p className="text-cream/50 text-sm">No players yet</p>}
          <div className="space-y-2">
            {players.map((p) => (
              <button key={p.id} onClick={() => { store.setPlayer(code, p.id); nav(`/u/${p.id}`) }}
                className="w-full text-left bg-cream/5 hover:bg-cream/10 rounded-xl px-4 py-3">{p.name}</button>
            ))}
          </div>
        </Modal>
      )}
    </div>
  )
}

function QuestionField({ q, value, onChange }) {
  return (
    <div>
      <p className="label mb-2">{q.text}{!q.required && ' (optional)'}</p>
      {q.kind === 'choice' && (
        <select value={value ?? ''} onChange={(e) => onChange(e.target.value)} className="field text-lg">
          <option value="" disabled>Choose…</option>
          {q.options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      )}
      {q.kind === 'text' && (
        <input value={value ?? ''} maxLength={q.numeric ? 6 : 100}
          inputMode={q.numeric ? 'numeric' : 'text'} pattern={q.numeric ? '[0-9]*' : undefined}
          onChange={(e) => onChange(q.numeric ? e.target.value.replace(/\D/g, '') : e.target.value)}
          className="field text-lg" />
      )}
      {(q.kind === 'yesno' || q.kind === 'alcohol') && (
        <div className="grid grid-cols-2 gap-3">
          {[[true, 'Yes'], [false, 'No']].map(([v, l]) => (
            <button type="button" key={l} onClick={() => onChange(v)}
              className={`py-3 rounded-2xl font-bold border-2 ${value === v ? 'bg-zest text-ink border-zest' : 'border-cream/25'}`}>
              {l}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
