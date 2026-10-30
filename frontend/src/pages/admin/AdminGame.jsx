import { useCallback, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { host } from '../../lib/api'
import {
  useTheme, QRCode, joinUrl, fmtDuration, placeLabel, Modal,
  THEME_EMOJI, TYPE_LABEL, TYPE_COLOR,
} from '../../lib/ui'
import { useHostGuard, StatusBadge } from './AdminGames'

const TABS = [
  ['control', '🎛 Control'], ['settings', '⚙️ Settings'], ['tasks', '🎯 Tasks'],
  ['players', '👥 Players'], ['photos', '📸 Photos'],
]

export default function AdminGame() {
  const { id } = useParams()
  const me = useHostGuard()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'control'
  const [game, setGame] = useState(null)
  const [err, setErr] = useState('')
  useTheme(game?.settings.theme)

  const reload = useCallback(() => host.game(id).then(setGame).catch((e) => setErr(e.message)), [id])
  useEffect(() => { if (me) reload() }, [me, reload])

  if (!me) return null
  if (!game) return <p className="text-cream/60 p-8 font-body">{err || 'Loading…'}</p>

  return (
    <div className="relative z-10 min-h-screen text-cream font-body px-4 py-6 max-w-4xl mx-auto">
      <header className="mb-5">
        <Link to="/admin/games" className="text-cream/40 text-xs">← My games</Link>
        <h1 className="font-display font-extrabold text-2xl sm:text-3xl text-zest mt-1">
          {THEME_EMOJI[game.settings.theme]} {game.name}
        </h1>
        <p className="text-cream/50 text-xs mt-1">
          code <span className="text-zest font-bold tracking-widest">{game.code}</span> · {game.player_count} players{' '}
          <StatusBadge game={game} />
        </p>
      </header>
      <nav className="flex gap-1 overflow-x-auto mb-6 -mx-1 px-1">
        {TABS.map(([k, l]) => (
          <button key={k} onClick={() => setParams({ tab: k })}
            className={`shrink-0 px-3 py-2 rounded-xl text-sm ${tab === k ? 'bg-zest text-ink font-bold' : 'bg-cream/5 text-cream/70'}`}>
            {l}
          </button>
        ))}
      </nav>
      {tab === 'control' && <Control game={game} reload={reload} />}
      {tab === 'settings' && <Settings game={game} onSaved={setGame} />}
      {tab === 'tasks' && <Tasks game={game} reload={reload} />}
      {tab === 'players' && <Players game={game} />}
      {tab === 'photos' && <Photos game={game} />}
    </div>
  )
}

// ─── Control ────────────────────────────────────────────────────────────────

function Control({ game, reload }) {
  const [lb, setLb] = useState([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const url = joinUrl(game.code)
  const prizes = game.settings.prizes.filter((p) => p.title)

  useEffect(() => {
    const load = () => { host.leaderboard(game.id).then(setLb).catch(() => {}); reload() }
    const t = setInterval(load, 7000)
    host.leaderboard(game.id).then(setLb).catch(() => {})
    return () => clearInterval(t)
  }, [game.id, reload])

  async function act(fn, question) {
    if (!confirm(question)) return
    setBusy(true); setErr('')
    try { await fn(game.id); await reload(); setLb(await host.leaderboard(game.id)) }
    catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const finished = lb.filter((i) => i.finished)
  return (
    <div className="space-y-6">
      <StorageStatus />
      <div className="card p-5 flex flex-col sm:flex-row gap-5 items-center">
        <div className="bg-white p-2 rounded-xl"><QRCode value={url} size={150} /></div>
        <div className="flex-1 space-y-2 text-center sm:text-left">
          <p className="label">Join link</p>
          <p className="font-bold break-all">{url}</p>
          <div className="flex flex-wrap gap-2 justify-center sm:justify-start pt-2">
            <a href={`/g/${game.code}/screen`} target="_blank" rel="noreferrer" className="btn-ghost text-sm py-2">📺 TV screen</a>
            <a href={`/g/${game.code}/slideshow`} target="_blank" rel="noreferrer" className="btn-ghost text-sm py-2">🎞 Slideshow</a>
            <a href={`/g/${game.code}/gallery`} target="_blank" rel="noreferrer" className="btn-ghost text-sm py-2">🖼 Gallery</a>
            <button onClick={() => navigator.clipboard?.writeText(url)} className="btn-ghost text-sm py-2">📋 Copy link</button>
          </div>
        </div>
      </div>

      <div className="card p-5 space-y-3">
        <p className="label">Game</p>
        {game.is_draft ? (
          <>
            <p className="text-cream/70 text-sm">
              📝 <b className="text-cream">Draft.</b> Set everything up in Settings and Tasks. Nobody can join until you publish;
              the link shows "not open yet".
            </p>
            <button disabled={busy} onClick={() => act(host.publish, 'Publish the game? People will be able to sign up with the link / QR.')}
              className="btn-primary w-full text-lg">📣 Publish — open sign-up</button>
          </>
        ) : !game.started ? (
          <>
            <p className="text-cream/70 text-sm">
              {game.player_count} players joined. Starting assigns {game.tasks_per_user} tasks to everyone and starts the clock.
              {game.settings.allow_late_join ? ' Late players can still join and get tasks right away.' : ' After the start nobody else can join.'}
            </p>
            <button disabled={busy || game.player_count === 0}
              onClick={() => act(host.start, 'Start the game now? Everyone gets their tasks and the timer starts.')}
              className="w-full bg-punch text-cream font-display font-extrabold text-2xl py-4 rounded-2xl active:scale-95 transition-transform disabled:opacity-50">
              🚀 START GAME
            </button>
            <button disabled={busy} onClick={() => act(host.unpublish, 'Close sign-up and go back to draft? Players who already joined stay.')}
              className="text-cream/40 text-xs underline underline-offset-2 w-full">Back to draft</button>
          </>
        ) : !game.places_revealed ? (
          <>
            <p className="text-mint">▶ Live since {new Date(game.started_at + 'Z').toLocaleTimeString()}</p>
            <button disabled={busy} onClick={() => act(host.reveal, 'Reveal places to everyone? This cannot be undone.')}
              className="btn-primary w-full text-lg">🏆 Reveal places & winners</button>
          </>
        ) : <p className="text-mint">🎉 Places revealed</p>}
        {err && <p className="text-punch text-sm">{err}</p>}
      </div>

      {game.started && (
        <div className="card p-5">
          <p className="label mb-3">Leaderboard (host view)</p>
          {finished.length > 0 && (
            <div className="space-y-2 mb-4">
              {finished.map((i, n) => {
                const prize = prizes.find((p) => p.place === String(n + 1))
                return (
                  <div key={i.user_id} className={`flex items-center gap-3 rounded-xl px-3 py-2 ${prize ? 'bg-zest/15 border border-zest/40' : 'bg-cream/5'}`}>
                    <span className="w-14 font-bold">{placeLabel(String(n + 1)).split(' ')[0]} #{n + 1}</span>
                    <span className="flex-1 font-bold">{i.name}</span>
                    <span className="text-mint tabular-nums text-sm">{fmtDuration(i.duration_seconds)}</span>
                    {prize && <span className="text-zest text-xs">{prize.title}</span>}
                  </div>
                )
              })}
            </div>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {lb.filter((i) => !i.finished).map((i) => (
              <div key={i.user_id} className="bg-cream/5 rounded-xl px-3 py-2 text-sm flex justify-between">
                <span className="truncate">{i.name}</span><span className="text-zest">{i.completed_count}/{i.total}</span>
              </div>
            ))}
          </div>
          <p className="text-cream/40 text-xs mt-3">Units of winners are in the Players tab.</p>
        </div>
      )}
    </div>
  )
}

function StorageStatus() {
  const [s, setS] = useState(null)
  const check = useCallback(() => { setS(null); host.storageCheck().then(setS).catch((e) => setS({ ok: false, message: e.message })) }, [])
  useEffect(() => { check() }, [check])
  return (
    <div className={`rounded-2xl px-4 py-3 text-sm flex items-center gap-3 border-2 ${
      !s ? 'border-cream/15 text-cream/50' : s.ok ? 'border-mint/30 text-mint' : 'border-punch/60 bg-punch/10 text-cream'}`}>
      <span className="flex-1">
        {!s ? 'Checking photo storage…' : s.ok ? '✅ Photo storage works' : <>❌ <b>Uploads will fail:</b> {s.message}</>}
      </span>
      <button onClick={check} className="text-xs underline shrink-0">re-check</button>
    </div>
  )
}

// ─── Settings ───────────────────────────────────────────────────────────────

const QUESTION_PRESETS = [
  ['Building (dropdown)', { kind: 'choice', text: 'Your building', options: ['80 Bond', '100 Bond'], required: true }],
  ['Unit number', { kind: 'text', text: 'Unit number', numeric: true, private: true, required: true }],
  ['Email for photos (optional)', { kind: 'email', text: 'Want your photos from tonight? Leave your email and we\'ll send them (optional)', private: true, required: false }],
  ['Yes / No', { kind: 'yesno', text: 'New question?', required: true }],
  ['Text', { kind: 'text', text: 'New question?', required: false }],
  ['Drinking alcohol?', { kind: 'alcohol', text: 'Will you be drinking alcohol tonight?', required: true }],
]

function slug(text, taken) {
  const base = (text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'q').slice(0, 30)
  let id = base, n = 2
  while (taken.includes(id)) id = `${base}_${n++}`
  return id
}

function Settings({ game, onSaved }) {
  const [name, setName] = useState(game.name)
  const [perUser, setPerUser] = useState(game.tasks_per_user)
  const [s, setS] = useState(game.settings)
  const [saved, setSaved] = useState('')
  const [err, setErr] = useState('')
  const [preview, setPreview] = useState(false)
  const set = (patch) => { setS((x) => ({ ...x, ...patch })); setSaved('') }
  const setConsent = (patch) => set({ consent: { ...s.consent, ...patch } })
  const setQ = (i, patch) => set({ questions: s.questions.map((q, j) => (j === i ? { ...q, ...patch } : q)) })
  const setPrize = (i, patch) => set({ prizes: s.prizes.map((p, j) => (j === i ? { ...p, ...patch } : p)) })

  function addQuestion(preset) {
    const id = slug(preset.text, s.questions.map((q) => q.id))
    set({ questions: [...s.questions, { options: [], numeric: false, private: false, ...preset, id }] })
  }
  function moveQ(i, d) {
    const qs = [...s.questions]; const j = i + d
    if (j < 0 || j >= qs.length) return
    ;[qs[i], qs[j]] = [qs[j], qs[i]]; set({ questions: qs })
  }

  async function save() {
    setErr('')
    try {
      const g = await host.updateGame(game.id, { name, tasks_per_user: Number(perUser), settings: s })
      onSaved(g); setSaved('Saved ✓')
    } catch (e) { setErr(e.message) }
  }

  return (
    <div className="space-y-6 pb-24">
      <Section title="Basics">
        <Field label="Game name"><input value={name} onChange={(e) => { setName(e.target.value); setSaved('') }} className="field" /></Field>
        <Field label="Theme">
          <div className="grid grid-cols-3 gap-2">
            {['halloween', 'diwali', 'party'].map((t) => (
              <button key={t} onClick={() => set({ theme: t })}
                className={`py-3 rounded-xl border-2 capitalize ${s.theme === t ? 'border-zest bg-zest/15' : 'border-cream/15'}`}>
                {THEME_EMOJI[t]} {t}
              </button>
            ))}
          </div>
        </Field>
        <Field label="Welcome message (shown on the join page)">
          <textarea rows={3} value={s.welcome} onChange={(e) => set({ welcome: e.target.value })} className="field"
            placeholder="Welcome, neighbours! Complete fun challenges, meet people from both buildings and win rent credit." />
        </Field>
      </Section>

      <Section title="Photo & media release" hint="Players must read and accept this before they can sign up. Every version they accept is stored with a timestamp.">
        <Toggle checked={s.consent.enabled} onChange={(v) => setConsent({ enabled: v })} label="Require consent before joining" />
        {s.consent.enabled && (
          <>
            <Field label="Title"><input value={s.consent.title} onChange={(e) => setConsent({ title: e.target.value })} className="field" /></Field>
            <Field label="Short summary (shown above the checkbox)">
              <textarea rows={3} value={s.consent.summary} onChange={(e) => setConsent({ summary: e.target.value })} className="field" />
            </Field>
            <Field label="Checkbox text"><input value={s.consent.checkbox_label} onChange={(e) => setConsent({ checkbox_label: e.target.value })} className="field" /></Field>
            <Field label="Full document">
              <textarea rows={12} value={s.consent.body} onChange={(e) => setConsent({ body: e.target.value })} className="field text-xs font-body" />
            </Field>
            <p className="text-cream/40 text-xs">⚠️ This is a draft. Have it reviewed by the property management team before the event.</p>
          </>
        )}
      </Section>

      <Section title="Sign-up questions" hint="Asked together with the name. Dropdown answers (like building) are shown to players who need to find each other; private answers (like unit) only to you.">
        {s.questions.map((q, i) => (
          <div key={q.id} className="bg-cream/5 rounded-xl p-3 space-y-2">
            <div className="flex gap-2">
              <input value={q.text} onChange={(e) => setQ(i, { text: e.target.value })} className="field py-2" />
              <button onClick={() => moveQ(i, -1)} className="btn-ghost px-3 py-2">↑</button>
              <button onClick={() => moveQ(i, 1)} className="btn-ghost px-3 py-2">↓</button>
              <button onClick={() => set({ questions: s.questions.filter((_, j) => j !== i) })} className="btn-ghost px-3 py-2 text-punch">✕</button>
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-2 items-center text-sm">
              <select value={q.kind} onChange={(e) => setQ(i, { kind: e.target.value })} className="bg-ink border border-cream/25 rounded-lg px-2 py-1">
                <option value="choice">Dropdown</option>
                <option value="text">Text / number</option>
                <option value="email">Email</option>
                <option value="yesno">Yes / No</option>
                <option value="alcohol">Alcohol (No = no alcohol tasks)</option>
              </select>
              <Check checked={q.required} onChange={(v) => setQ(i, { required: v })} label="required" />
              {q.kind === 'text' && <Check checked={q.numeric} onChange={(v) => setQ(i, { numeric: v })} label="numbers only" />}
              <Check checked={q.private} onChange={(v) => setQ(i, { private: v })} label="private (host only)" />
            </div>
            {q.kind === 'choice' && (
              <input value={q.options.join(', ')} placeholder="Options, comma separated"
                onChange={(e) => setQ(i, { options: e.target.value.split(',').map((o) => o.trim()).filter(Boolean) })}
                className="field py-2 text-sm" />
            )}
          </div>
        ))}
        <div className="flex flex-wrap gap-2">
          {QUESTION_PRESETS.map(([label, preset]) => (
            <button key={label} onClick={() => addQuestion(preset)} className="btn-ghost text-xs py-2">+ {label}</button>
          ))}
        </div>
      </Section>

      <Section title="Rules">
        <Field label="Tasks per player">
          <input type="number" min={1} max={20} value={perUser} disabled={game.started}
            onChange={(e) => { setPerUser(e.target.value); setSaved('') }} className="field w-28" />
        </Field>
        <Toggle checked={s.allow_late_join} onChange={(v) => set({ allow_late_join: v })} label="People can join after the game has started" />
        <Toggle checked={s.alcohol_tasks} onChange={(v) => set({ alcohol_tasks: v })} label="Allow alcohol tasks in this game" />
        <Field label="Wildcards per player (tasks marked 🃏 can replace any task)">
          <input type="number" min={0} max={20} value={s.max_wildcards}
            onChange={(e) => set({ max_wildcards: Number(e.target.value) })} className="field w-28" />
        </Field>
      </Section>

      <Section title="Who can see photos" hint="Players can always see and download the photos they uploaded themselves.">
        <label className="flex items-start gap-3 cursor-pointer">
          <input type="radio" checked={s.gallery === 'host_only'} onChange={() => set({ gallery: 'host_only' })} className="mt-1 accent-[rgb(var(--c-zest))]" />
          <span className="text-sm"><b>Host only</b> — the TV screen and slideshow work only in your logged-in browser. No public gallery. Recommended for big or public events, especially with children.</span>
        </label>
        <label className="flex items-start gap-3 cursor-pointer">
          <input type="radio" checked={s.gallery === 'public'} onChange={() => set({ gallery: 'public' })} className="mt-1 accent-[rgb(var(--c-zest))]" />
          <span className="text-sm"><b>Anyone with the game code</b> — gallery and slideshow open to everyone who has the link. Fine for private parties.</span>
        </label>
      </Section>

      <Section title="Prizes" hint="1, 2, 3 = places by finishing time. Any other label is a special prize you award yourself.">
        {s.prizes.map((p, i) => (
          <div key={i} className="flex gap-2">
            <input value={p.place} onChange={(e) => setPrize(i, { place: e.target.value })} className="field w-24 py-2" placeholder="1" />
            <input value={p.title} onChange={(e) => setPrize(i, { title: e.target.value })} className="field py-2" placeholder="$75 rent credit" />
            <button onClick={() => set({ prizes: s.prizes.filter((_, j) => j !== i) })} className="btn-ghost px-3 py-2 text-punch">✕</button>
          </div>
        ))}
        <button onClick={() => set({ prizes: [...s.prizes, { place: String(s.prizes.length + 1), title: '' }] })} className="btn-ghost text-xs py-2">+ Prize</button>
      </Section>

      <div className="fixed bottom-0 inset-x-0 z-20 bg-ink/95 border-t border-cream/10 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <button onClick={save} className="btn-primary">Save settings</button>
          <button onClick={() => setPreview(true)} className="btn-ghost">👁 Preview consent</button>
          <span className="text-mint text-sm">{saved}</span>
          {err && <span className="text-punch text-sm">{err}</span>}
        </div>
      </div>

      {preview && (
        <Modal wide onClose={() => setPreview(false)}>
          <h2 className="font-display font-bold text-2xl text-zest mb-2">{s.consent.title}</h2>
          <p className="text-cream/80 text-sm mb-4">{s.consent.summary}</p>
          <div className="text-sm whitespace-pre-wrap text-cream/90 border-t border-cream/10 pt-4">{s.consent.body}</div>
          <p className="mt-4 text-sm">☐ {s.consent.checkbox_label}</p>
          <button onClick={() => setPreview(false)} className="btn-ghost w-full mt-4">Close</button>
        </Modal>
      )}
    </div>
  )
}

function Section({ title, hint, children }) {
  return (
    <section className="card p-5 space-y-3">
      <p className="font-display font-bold text-lg">{title}</p>
      {hint && <p className="text-cream/50 text-xs -mt-2">{hint}</p>}
      {children}
    </section>
  )
}
function Field({ label, children }) {
  return <label className="block space-y-1"><span className="label">{label}</span>{children}</label>
}
function Toggle({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="w-5 h-5 accent-[rgb(var(--c-zest))]" />
      <span className="text-sm">{label}</span>
    </label>
  )
}
function Check({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-1.5 cursor-pointer select-none text-cream/70">
      <input type="checkbox" checked={!!checked} onChange={(e) => onChange(e.target.checked)} className="accent-[rgb(var(--c-zest))]" />
      {label}
    </label>
  )
}

// ─── Tasks ──────────────────────────────────────────────────────────────────

function Tasks({ game, reload }) {
  const [tasks, setTasks] = useState([])
  const [packs, setPacks] = useState([])
  const [draft, setDraft] = useState({ description: '', type: 1, is_alcoholic: false, is_universal: false })
  const [editing, setEditing] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    host.tasks(game.id).then(setTasks).catch((e) => setErr(e.message))
    host.packs().then(setPacks).catch(() => {})
  }, [game.id])

  async function run(p) {
    setErr('')
    try { setTasks(await p); reload() } catch (e) { setErr(e.message) }
  }

  const regular = tasks.filter((x) => !x.is_universal)
  const counts = [1, 2, 3].map((t) => regular.filter((x) => x.type === t).length)
  const wild = tasks.length - regular.length
  return (
    <div className="space-y-5">
      <div className="card p-4 text-sm text-cream/70 space-y-1">
        <p><b className="text-cream">{regular.length} tasks</b>: {counts[0]} solo · {counts[1]} find-a-person · {counts[2]} paired · plus {wild} 🃏 wildcards. Each player gets {game.tasks_per_user}.</p>
        <p className="text-xs text-cream/50">🃏 Wildcards are never handed out; a player can do one instead of a task they can't complete ({game.settings.max_wildcards} per player, set in Settings).</p>
        <p className="text-xs text-cream/50">Use <code className="text-zest">{'{target}'}</code> for the other person's name in find-a-person and paired tasks. Have at least {game.tasks_per_user + 2} solo + find-a-person tasks.</p>
      </div>

      <div className="card p-4 space-y-2">
        <p className="label">Add task</p>
        <textarea rows={2} value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })}
          placeholder="Find {target} and ask them…" className="field" />
        <div className="flex flex-wrap gap-2 items-center">
          <TypeSelect value={draft.type} onChange={(type) => setDraft({ ...draft, type })} />
          {game.settings.alcohol_tasks && <Check checked={draft.is_alcoholic} onChange={(v) => setDraft({ ...draft, is_alcoholic: v })} label="alcohol" />}
          <Check checked={draft.is_universal} onChange={(v) => setDraft({ ...draft, is_universal: v, type: 1 })} label="🃏 wildcard" />
          <button disabled={draft.description.trim().length < 3}
            onClick={() => run(host.addTask(game.id, draft)).then(() => setDraft({ ...draft, description: '' }))}
            className="btn-primary py-2 ml-auto">Add</button>
        </div>
      </div>

      {err && <p className="text-punch text-sm">{err}</p>}

      <div className="space-y-2">
        {tasks.map((t) => editing?.id === t.id ? (
          <div key={t.id} className="card p-3 space-y-2">
            <textarea rows={2} value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} className="field" />
            <div className="flex gap-2 items-center">
              <TypeSelect value={editing.type} onChange={(type) => setEditing({ ...editing, type })} disabled={game.started || editing.is_universal} />
              <Check checked={editing.is_universal} onChange={(v) => setEditing({ ...editing, is_universal: v, type: 1 })} label="🃏 wildcard" />
              <button onClick={() => run(host.editTask(game.id, t.id, editing)).then(() => setEditing(null))} className="btn-primary py-2 ml-auto">Save</button>
              <button onClick={() => setEditing(null)} className="btn-ghost py-2">Cancel</button>
            </div>
          </div>
        ) : (
          <div key={t.id} className="card p-3 flex items-start gap-3">
            {t.is_universal
              ? <span className="shrink-0 bg-cream text-ink text-[10px] font-bold px-2 py-1 rounded-md">🃏 WILD</span>
              : <span className={`shrink-0 ${TYPE_COLOR[t.type]} text-ink text-[10px] font-bold px-2 py-1 rounded-md`}>{TYPE_LABEL[t.type]}</span>}
            <p className="flex-1 text-sm">{t.description}{t.is_alcoholic && ' 🍺'}</p>
            {t.assigned_count > 0 && <span className="text-cream/40 text-xs shrink-0">×{t.assigned_count}</span>}
            <button onClick={() => setEditing({ description: t.description, type: t.type, is_alcoholic: t.is_alcoholic, is_universal: t.is_universal, id: t.id })} className="text-cream/50 shrink-0">✎</button>
            {t.assigned_count === 0 && (
              <button onClick={() => confirm('Delete this task?') && run(host.deleteTask(game.id, t.id))} className="text-punch shrink-0">🗑</button>
            )}
          </div>
        ))}
      </div>

      <div className="card p-4 space-y-2">
        <p className="label">Task packs</p>
        {packs.map((p) => (
          <div key={p.id} className="flex flex-wrap items-center gap-2 text-sm">
            <span className="flex-1">{p.title} ({p.task_count})</span>
            <button onClick={() => run(host.loadPack(game.id, p.id, false))} className="btn-ghost py-1.5 text-xs">+ Add</button>
            {!game.started && (
              <button onClick={() => confirm('Replace ALL current tasks with this pack?') && run(host.loadPack(game.id, p.id, true))}
                className="btn-ghost py-1.5 text-xs text-punch">Replace all</button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function TypeSelect({ value, onChange, disabled }) {
  return (
    <select value={value} disabled={disabled} onChange={(e) => onChange(Number(e.target.value))}
      className="bg-ink border border-cream/25 rounded-lg px-2 py-2 text-sm">
      <option value={1}>Solo</option>
      <option value={2}>Find a person ({'{target}'})</option>
      <option value={3}>Paired ({'{target}'})</option>
    </select>
  )
}

// ─── Players ────────────────────────────────────────────────────────────────

function Players({ game }) {
  const [players, setPlayers] = useState([])
  useEffect(() => {
    const load = () => host.players(game.id).then(setPlayers).catch(() => {})
    load()
    const t = setInterval(load, 10000)
    return () => clearInterval(t)
  }, [game.id])
  const qs = game.settings.questions
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center justify-between">
        <p className="text-cream/60 text-sm">{players.length} players</p>
        <a href={host.consentsCsvUrl(game.id)} className="btn-ghost text-sm py-2">⬇ Consent records (CSV)</a>
      </div>
      <div className="overflow-x-auto card">
        <table className="w-full text-sm">
          <thead className="text-cream/50 text-xs text-left">
            <tr>
              <th className="p-3">Name</th>
              {qs.map((q) => <th key={q.id} className="p-3">{q.text}</th>)}
              <th className="p-3">Tasks</th>
              <th className="p-3">Consent</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody>
            {players.map((p) => (
              <tr key={p.id} className="border-t border-cream/10">
                <td className="p-3 font-bold">{p.name}{p.is_latecomer && <span className="text-cream/40 text-xs"> late</span>}</td>
                {qs.map((q) => <td key={q.id} className="p-3">{String(p.answers?.[q.id] ?? '')}</td>)}
                <td className="p-3 tabular-nums">{p.completed_count}/{p.total}</td>
                <td className="p-3 text-xs text-cream/60">{p.consent_accepted_at ? new Date(p.consent_accepted_at + 'Z').toLocaleString() : '—'}</td>
                <td className="p-3"><PlayerLink id={p.id} name={p.name} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function PlayerLink({ id, name }) {
  const [show, setShow] = useState(false)
  const url = `${window.location.origin}/u/${id}`
  return (
    <>
      <button onClick={() => setShow(true)} className="text-xs text-zest underline whitespace-nowrap">🔗 link</button>
      {show && (
        <Modal onClose={() => setShow(false)}>
          <p className="font-display font-bold text-lg text-zest mb-1">{name}'s personal link</p>
          <p className="text-cream/50 text-xs mb-4">Opens their game on a new phone. Only give it to {name}.</p>
          <div className="bg-white p-2 rounded-xl w-fit mx-auto"><QRCode value={url} size={200} /></div>
          <button onClick={() => navigator.clipboard?.writeText(url)} className="btn-ghost w-full mt-4 text-sm">📋 Copy link</button>
          <button onClick={() => setShow(false)} className="btn-ghost w-full mt-2">Close</button>
        </Modal>
      )}
    </>
  )
}

// ─── Photos ─────────────────────────────────────────────────────────────────

function Photos({ game }) {
  const [items, setItems] = useState([])
  const load = useCallback(() => host.media(game.id).then(setItems).catch(() => {}), [game.id])
  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t) }, [load])

  async function toggle(s) {
    await host.setHidden(game.id, s.is_free ? 'free' : 'task', s.media_id, !s.hidden)
    load()
  }
  return (
    <div>
      <p className="text-cream/60 text-sm mb-3">{items.length} uploads · hidden ones never show on the TV, slideshow or gallery.</p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[...items].reverse().map((s) => (
          <div key={s.id} className={`relative rounded-xl overflow-hidden aspect-square bg-black ${s.hidden ? 'opacity-40' : ''}`}>
            {s.media_type === 'video'
              ? <video src={s.file_url} className="w-full h-full object-cover" muted playsInline preload="metadata" />
              : <img src={s.file_url} className="w-full h-full object-cover" loading="lazy" />}
            <div className="absolute inset-x-0 bottom-0 p-2 bg-gradient-to-t from-black/90 to-transparent text-xs">
              <p className="font-bold text-zest truncate">{s.user_name}{s.media_type === 'video' && ' ▶'}</p>
            </div>
            <button onClick={() => toggle(s)}
              className={`absolute top-2 right-2 text-xs px-2 py-1 rounded-lg ${s.hidden ? 'bg-mint text-ink' : 'bg-black/70 text-cream'}`}>
              {s.hidden ? 'Show' : 'Hide'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
