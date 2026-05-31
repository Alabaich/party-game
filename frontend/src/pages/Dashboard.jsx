import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api, uploadAndComplete, freeUpload, store } from '../lib/api'

const TYPE_LABEL = { 1: 'SOLO', 2: 'TARGET', 3: 'PAIR' }
const TYPE_COLOR = { 1: 'bg-mint', 2: 'bg-zest', 3: 'bg-punch' }

function fmtDuration(sec) {
  if (sec == null) return '—'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const pad = (n) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

export default function Dashboard() {
  const { uuid } = useParams()
  const nav = useNavigate()
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')
  const [viewing, setViewing] = useState(null)
  const [uploadingId, setUploadingId] = useState(null)
  const [freeUploading, setFreeUploading] = useState(false)
  const [winInfo, setWinInfo] = useState(null)
  const fileRef = useRef(null)
  const freeFileRef = useRef(null)
  const pickTargetId = useRef(null)

  const load = useCallback(async () => {
    try {
      const d = await api.dashboard(uuid)
      store.setUuid(uuid)
      setData(d)

      const allDone = d.assignments.length > 0 &&
        d.assignments.every((a) => a.status === 'completed')
      if (allDone) {
        try {
          const lb = await api.leaderboard()
          const finishedList = lb.filter((i) => i.finished)
          const myIndex = finishedList.findIndex((i) => i.user_id === uuid)
          const me = lb.find((i) => i.user_id === uuid)
          if (me) {
            setWinInfo({
              place: myIndex + 1,
              duration_seconds: me.duration_seconds,
              revealed: d.places_revealed,
            })
          }
        } catch { /* ignore */ }
      }
    } catch (e) {
      if (e.message.includes('404') || e.message.includes('not found')) {
        store.clear()
        nav('/')
      } else {
        setErr(e.message)
      }
    }
  }, [uuid, nav])

  useEffect(() => {
    load()
    const id = setInterval(load, 7000)
    return () => clearInterval(id)
  }, [load])

  if (err) return <Center>{err}</Center>
  if (!data) return <Center>Loading…</Center>

  const started = data.game_started
  const done = data.assignments.filter((a) => a.status === 'completed').length
  const allDone = data.assignments.length > 0 && done === data.assignments.length

  function triggerUpload(assignmentId) {
    pickTargetId.current = assignmentId
    fileRef.current?.click()
  }

  async function onFiles(e) {
    const files = e.target.files
    const aid = pickTargetId.current
    if (!files?.length || !aid) return
    setUploadingId(aid); setErr('')
    try {
      await uploadAndComplete(uuid, aid, files)
      await load()
      setViewing(null)
    } catch (e2) {
      setErr(e2.message || 'Upload failed')
    } finally {
      setUploadingId(null)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function onFreeFiles(e) {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    setFreeUploading(true); setErr('')
    try {
      for (const f of files) {
        await freeUpload(uuid, f)
      }
    } catch (e2) {
      setErr(e2.message || 'Upload failed')
    } finally {
      setFreeUploading(false)
      if (freeFileRef.current) freeFileRef.current.value = ''
    }
  }

  // ===== WIN SCREEN =====
  if (allDone && winInfo) {
    const revealed = winInfo.revealed
    const placeEmoji = !revealed ? '🎉'
      : winInfo.place === 1 ? '🥇'
      : winInfo.place === 2 ? '🥈'
      : winInfo.place === 3 ? '🥉' : '🎊'
    const placeLabel = !revealed ? '?'
      : winInfo.place === 1 ? '1st'
      : winInfo.place === 2 ? '2nd'
      : winInfo.place === 3 ? '3rd'
      : `${winInfo.place}th`

    return (
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center text-cream font-body px-6 text-center">
        <div className="animate-float text-8xl mb-6">{placeEmoji}</div>
        <h1 className="font-display font-extrabold text-5xl text-zest mb-2">You finished!</h1>
        <p className="text-cream/60 text-sm tracking-widest mb-8">ALL TASKS COMPLETED</p>

        <div className="w-full max-w-sm space-y-4 mb-8">
          <div className="bg-cream/5 border-2 border-cream/15 rounded-2xl px-6 py-5">
            <p className="text-cream/50 text-xs tracking-widest mb-1">YOUR TIME</p>
            <p className="font-display font-extrabold text-4xl text-mint tabular-nums">
              {fmtDuration(winInfo.duration_seconds)}
            </p>
          </div>
          <div className={`border-2 rounded-2xl px-6 py-5 ${revealed ? 'bg-zest/10 border-zest/40' : 'bg-cream/5 border-cream/15'}`}>
            <p className="text-cream/50 text-xs tracking-widest mb-1">YOUR PLACE</p>
            {revealed
              ? <p className="font-display font-extrabold text-4xl text-zest">{placeLabel}</p>
              : <p className="font-display font-extrabold text-4xl text-cream/30">waiting for reveal…</p>
            }
          </div>
        </div>

        {/* Free upload still available on win screen */}
        <input ref={freeFileRef} type="file" accept="image/*,video/*" multiple
          className="hidden" onChange={onFreeFiles} />
        <button
          onClick={() => freeFileRef.current?.click()}
          disabled={freeUploading}
          className="bg-cream/10 border-2 border-cream/20 text-cream font-bold px-6 py-3 rounded-2xl active:scale-95 transition-transform disabled:opacity-50 mb-4">
          {freeUploading ? '⏳ Uploading…' : '📸 Just Upload'}
        </button>

        <Link to="/leaderboard"
          className="bg-zest text-ink font-display font-bold text-lg px-8 py-4 rounded-2xl active:scale-95 transition-transform">
          🏆 See Leaderboard
        </Link>
      </div>
    )
  }

  return (
    <div className="relative z-10 min-h-screen text-cream font-body px-5 py-6 max-w-lg mx-auto">
      <input ref={fileRef} type="file" accept="image/*,video/*" multiple
        className="hidden" onChange={onFiles} />
      <input ref={freeFileRef} type="file" accept="image/*,video/*" multiple
        className="hidden" onChange={onFreeFiles} />

      <header className="flex items-center justify-between mb-6">
        <div>
          <p className="text-cream/50 text-xs tracking-widest">PLAYER</p>
          <h1 className="font-display font-extrabold text-2xl text-zest">{data.user.name}</h1>
        </div>
        <div className="flex gap-2 text-xs">
          <button
            onClick={() => freeFileRef.current?.click()}
            disabled={freeUploading}
            className="bg-cream/10 px-3 py-2 rounded-xl disabled:opacity-50">
            {freeUploading ? '⏳' : '📸 Just Upload'}
          </button>
        </div>
      </header>

      {!started ? (
        <div className="text-center py-12">
          <div className="animate-float text-5xl mb-4">⏳</div>
          <p className="font-display font-extrabold text-3xl text-zest mb-2">Waiting to start</p>
          <p className="text-cream/50 text-sm mb-8">The game will begin when the host gives the go</p>

          <div className="text-left">
            <p className="text-mint tracking-widest text-xs mb-3">PLAYERS ({data.players.length})</p>
            <div className="space-y-2">
              {data.players.map((p) => (
                <div key={p.id}
                  className={`rounded-xl px-4 py-3 border ${
                    p.id === data.user.id
                      ? 'bg-zest/15 border-zest/50 text-zest font-bold'
                      : 'bg-cream/5 border-cream/15'
                  }`}>
                  {p.name}{p.id === data.user.id && ' (you)'}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="font-display font-bold text-lg">Your tasks</p>
            <span className="bg-cream/10 px-3 py-1 rounded-full text-sm">{done}/{data.assignments.length} ✓</span>
          </div>

          <div className="space-y-3">
            {data.assignments.map((a) => {
              const isDone = a.status === 'completed'
              const isUp = uploadingId === a.id
              return (
                <div key={a.id}
                  onClick={() => isDone ? setViewing(a) : triggerUpload(a.id)}
                  className={`relative rounded-2xl p-4 border-2 transition-all cursor-pointer active:scale-[0.98] ${
                    isDone ? 'bg-mint/10 border-mint/40' : 'bg-cream/5 border-cream/15'
                  }`}>
                  <div className="flex items-start gap-3">
                    <div className={`shrink-0 ${TYPE_COLOR[a.type]} text-ink text-[10px] font-bold px-2 py-1 rounded-md`}>
                      {TYPE_LABEL[a.type]}
                    </div>
                    <div className="flex-1">
                      <p className={`leading-snug ${isDone ? 'line-through text-cream/50' : ''}`}>
                        {a.description}
                      </p>
                      {a.is_alcoholic && <span className="text-punch text-xs">🍺 alcoholic</span>}
                    </div>
                    <div className="shrink-0 text-2xl">
                      {isUp ? '⏳' : isDone ? '✅' : '⬜'}
                    </div>
                  </div>
                  {isDone && <p className="text-mint/70 text-xs mt-2">Tap to view / replace</p>}
                </div>
              )
            })}
          </div>
          {err && <p className="text-punch text-center text-sm mt-4">{err}</p>}
        </>
      )}

      {viewing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 px-4"
          onClick={() => setViewing(null)}>
          <div className="bg-ink border-2 border-cream/20 rounded-3xl p-4 max-w-sm w-full max-h-[85vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}>
            <p className="font-display font-bold mb-3">{viewing.description}</p>
            <div className="space-y-2">
              {viewing.media.map((m) => (
                m.media_type === 'video'
                  ? <video key={m.id} src={m.file_url} controls className="w-full rounded-xl" />
                  : <img key={m.id} src={m.file_url} className="w-full rounded-xl" />
              ))}
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={() => triggerUpload(viewing.id)}
                className="flex-1 bg-zest text-ink font-bold py-3 rounded-xl active:scale-95 transition-transform">
                Replace
              </button>
              <button onClick={() => setViewing(null)}
                className="flex-1 bg-cream/10 py-3 rounded-xl">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Center({ children }) {
  return (
    <div className="relative z-10 min-h-screen flex items-center justify-center text-cream/70 font-body px-6 text-center">
      {children}
    </div>
  )
}