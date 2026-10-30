import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api, uploadAndComplete, freeUpload, store, downloadUrl } from '../lib/api'
import {
  useTheme, fmtDuration, Center, Prizes, Modal, PhotoNotice, TYPE_COLOR, THEME_EMOJI,
} from '../lib/ui'

const PHONE_TYPE_LABEL = { 1: 'SOLO', 2: 'FIND', 3: 'PAIR' }

export default function Dashboard() {
  const { uuid } = useParams()
  const nav = useNavigate()
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')
  const [viewing, setViewing] = useState(null)
  const [uploadingId, setUploadingId] = useState(null)
  const [progress, setProgress] = useState(0)
  const [freeUploading, setFreeUploading] = useState(false)
  const [winInfo, setWinInfo] = useState(null)
  const fileRef = useRef(null)
  const freeFileRef = useRef(null)
  const pickTargetId = useRef(null)
  const pickSubId = useRef(null)
  const [wildFor, setWildFor] = useState(null)
  const [myMedia, setMyMedia] = useState(null)

  const load = useCallback(async () => {
    try {
      const d = await api.dashboard(uuid)
      store.setPlayer(d.game.code, uuid)
      setData(d)

      const allDone = d.assignments.length > 0 &&
        d.assignments.every((a) => a.status === 'completed')
      if (allDone) {
        try {
          const lb = await api.leaderboard(d.game.code)
          const finishedList = lb.filter((i) => i.finished)
          const myIndex = finishedList.findIndex((i) => i.user_id === d.user_key)
          const me = lb.find((i) => i.user_id === d.user_key)
          if (me) {
            setWinInfo({
              place: myIndex + 1,
              duration_seconds: me.duration_seconds,
              revealed: d.game.places_revealed,
            })
          }
        } catch { /* ignore */ }
      }
    } catch (e) {
      if (e.status === 404) {
        try { localStorage.removeItem('last_player') } catch { /* ignore */ }
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

  useTheme(data?.game.settings.theme)

  if (err && !data) return <Center>{err}</Center>
  if (!data) return <Center>Loading…</Center>

  const game = data.game
  const prizes = game.settings.prizes
  const started = game.started || data.user.is_latecomer
  const done = data.assignments.filter((a) => a.status === 'completed').length
  const allDone = data.assignments.length > 0 && done === data.assignments.length

  function triggerUpload(assignmentId, substituteId = null) {
    if (uploadingId) return   // one upload at a time
    pickTargetId.current = assignmentId
    pickSubId.current = substituteId
    fileRef.current?.click()
  }

  async function openMyMedia() {
    setMyMedia([])
    try { setMyMedia(await api.myMedia(uuid)) } catch (e2) { setErr(e2.message) }
  }

  async function onFiles(e) {
    const files = e.target.files
    const aid = pickTargetId.current
    if (!files?.length || !aid) return
    setUploadingId(aid); setProgress(0); setErr('')
    try {
      await uploadAndComplete(uuid, aid, files, pickSubId.current, setProgress)
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
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center text-cream font-sans px-6 text-center">
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
              : <p className="font-display font-extrabold text-2xl text-cream/30">waiting for reveal…</p>
            }
            {revealed && prizes.find((p) => p.place === String(winInfo.place) && p.title) && (
              <p className="text-mint font-bold mt-2">
                🎁 {prizes.find((p) => p.place === String(winInfo.place)).title}
                <span className="block text-cream/50 text-xs font-normal mt-1">Show this screen to the organizers</span>
              </p>
            )}
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

        {game.settings.gallery === 'public' ? (
          <Link to={`/g/${game.code}/gallery`}
            className="bg-zest text-ink font-display font-bold text-lg px-8 py-4 rounded-2xl active:scale-95 transition-transform">
            📸 See all photos
          </Link>
        ) : (
          <button onClick={openMyMedia}
            className="bg-zest text-ink font-display font-bold text-lg px-8 py-4 rounded-2xl active:scale-95 transition-transform">
            🖼 My photos
          </button>
        )}
        {myMedia && <MyMediaModal items={myMedia} onClose={() => setMyMedia(null)} />}
      </div>
    )
  }

  return (
    <div className="relative z-10 min-h-screen text-cream font-sans px-5 py-6 max-w-lg mx-auto">
      <input ref={fileRef} type="file" accept="image/*,video/*" multiple
        className="hidden" onChange={onFiles} />
      <input ref={freeFileRef} type="file" accept="image/*,video/*" multiple
        className="hidden" onChange={onFreeFiles} />

      <header className="flex items-start justify-between gap-3 mb-5">
        <div className="min-w-0">
          <p className="eyebrow truncate">{THEME_EMOJI[game.settings.theme]} {game.name}</p>
          <h1 className="font-display font-extrabold text-3xl text-zest mt-1">Hi, {data.user.name}!</h1>
        </div>
        <div className="flex gap-2 text-sm shrink-0">
          <button onClick={() => freeFileRef.current?.click()} disabled={freeUploading}
            className="bg-cream/10 px-3 py-2.5 rounded-2xl disabled:opacity-50 leading-tight">
            {freeUploading ? '⏳' : <>📸<br />Share</>}
          </button>
          <button onClick={openMyMedia} className="bg-cream/10 px-3 py-2.5 rounded-2xl leading-tight">🖼<br />Mine</button>
        </div>
      </header>

      {!started ? (
        <div className="text-center py-8">
          <div className="animate-float text-5xl mb-4">⏳</div>
          <p className="font-display font-extrabold text-3xl text-zest mb-2">Waiting to start</p>
          <p className="text-cream/80 text-base mb-8">The game begins when the host says go. Keep this page open!</p>
          <PhotoNotice settings={game.settings} className="text-left mb-8" />
          {prizes.some((p) => p.title) && (
            <div className="text-left mb-8">
              <p className="eyebrow text-mint mb-3">Prizes for the fastest to finish</p>
              <Prizes prizes={prizes} />
            </div>
          )}

          <div className="text-left">
            <p className="eyebrow text-mint mb-3">{data.players.length} {data.players.length === 1 ? 'player' : 'players'} joined</p>
            <div className="flex flex-wrap gap-2">
              {data.players.slice(0, 60).map((p) => (
                <span key={p.key}
                  className={`rounded-full px-3 py-1.5 text-[15px] border ${
                    p.key === data.user_key ? 'bg-zest/15 border-zest/50 text-zest font-bold' : 'bg-cream/5 border-cream/15'
                  }`}>
                  {p.name}{p.key === data.user_key && ' (you)'}
                </span>
              ))}
              {data.players.length > 60 && <span className="px-3 py-1.5 text-cream/70">+{data.players.length - 60} more</span>}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="rounded-2xl border border-zest/35 bg-zest/[0.12] px-4 py-3 text-base leading-snug mb-5">
            Do each task and tap <b>📷 Add photo</b> to prove it. Fastest to finish all {data.assignments.length} wins!
          </div>
          <div className="flex items-center justify-between mb-3">
            <p className="font-display font-bold text-xl">Your tasks</p>
            <span className="font-body font-bold text-mint bg-mint/15 px-3 py-1 rounded-full text-[15px] tabular-nums">
              {done} / {data.assignments.length}
            </span>
          </div>

          <div className="space-y-3">
            {data.assignments.map((a) => {
              const isDone = a.status === 'completed'
              const isUp = uploadingId === a.id
              return (
                <div key={a.id}
                  className={`rounded-[20px] p-4 border-2 space-y-3 ${isDone ? 'bg-mint/[0.08] border-mint/50' : 'bg-cream/5 border-cream/15'}`}>
                  <span className={`inline-block ${TYPE_COLOR[a.type]} text-ink font-body text-xs font-bold px-2 py-0.5 rounded-lg tracking-wide`}>
                    {PHONE_TYPE_LABEL[a.type]}
                  </span>
                  <p className={`text-lg leading-snug font-medium ${isDone ? 'text-cream/75' : ''}`}>{a.description}</p>
                  {a.target_user_name && (
                    <span className="inline-flex items-center gap-1.5 bg-cream/[0.08] rounded-full px-3 py-1.5 text-[15px] text-cream/85">
                      👋 Find <b className="text-zest">{a.target_user_name}</b>{a.target_hint && <> · {a.target_hint}</>}
                    </span>
                  )}
                  {a.is_alcoholic && <p className="text-punch text-sm">🍺 alcoholic</p>}
                  {a.substitute_description && (
                    <p className="text-mint text-[15px]">🃏 Did instead: {a.substitute_description}</p>
                  )}

                  {isUp ? (
                    <div className="space-y-2">
                      <div className="flex justify-between text-[15px]"><span>Uploading…</span>
                        <span className="font-body font-bold text-zest tabular-nums">{Math.round(progress * 100)}%</span></div>
                      <div className="h-2 rounded-full bg-cream/10 overflow-hidden">
                        <div className="h-full bg-zest transition-all" style={{ width: `${Math.max(3, progress * 100)}%` }} />
                      </div>
                    </div>
                  ) : isDone ? (
                    <div className="flex items-center justify-between text-base">
                      <span className="text-mint font-bold">✅ Done</span>
                      <button onClick={() => setViewing(a)} className="underline underline-offset-4 text-cream/85 py-2">View / replace</button>
                    </div>
                  ) : (
                    <>
                      <button onClick={() => triggerUpload(a.id)} disabled={!!uploadingId} className="btn-cta">
                        📷 Add photo or video
                      </button>
                      {data.wildcards.length > 0 && data.wildcards_left > 0 && (
                        <button onClick={() => setWildFor(a)} className="btn-outline">🃏 Can't do it? Use a wildcard</button>
                      )}
                    </>
                  )}
                </div>
              )
            })}
          </div>
          {err && <p className="text-punch text-center text-base mt-4">{err}</p>}
          {data.wildcards.length > 0 && (
            <p className="text-cream/75 text-[15px] text-center mt-4">🃏 Wildcards left: {data.wildcards_left}</p>
          )}
          <PhotoNotice settings={game.settings} className="mt-6" />
          <p className="text-cream/70 text-[15px] text-center mt-4">
            Paired tasks close for both of you when one uploads.
          </p>
        </>
      )}

      {wildFor && (
        <Modal onClose={() => setWildFor(null)}>
          <p className="font-display font-bold text-xl text-zest mb-1">🃏 Use a wildcard</p>
          <p className="text-cream/60 text-sm mb-4">
            Do one of these instead of: <span className="text-cream">{wildFor.description}</span>
            <br />You have {data.wildcards_left} left.
          </p>
          <div className="space-y-2">
            {data.wildcards.map((w) => (
              <button key={w.id} onClick={() => { const id = wildFor.id; setWildFor(null); triggerUpload(id, w.id) }}
                className="w-full text-left card px-4 py-3 hover:border-zest/50">
                {w.description}
                <span className="block text-zest text-xs mt-1">Tap to upload proof →</span>
              </button>
            ))}
          </div>
          <button onClick={() => setWildFor(null)} className="btn-ghost w-full mt-4">Cancel</button>
        </Modal>
      )}

      {myMedia && <MyMediaModal items={myMedia} onClose={() => setMyMedia(null)} />}

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

function MyMediaModal({ items, onClose }) {
  return (
    <Modal wide onClose={onClose}>
      <p className="font-display font-bold text-xl text-zest mb-1">🖼 My photos & videos</p>
      <p className="text-cream/50 text-xs mb-4">Only you can see this list. Tap ⬇ to save.</p>
      {items.length === 0 && <p className="text-cream/50 text-sm">Nothing uploaded yet.</p>}
      <div className="grid grid-cols-2 gap-2">
        {items.map((s) => (
          <div key={s.id} className="relative rounded-xl overflow-hidden bg-black aspect-square">
            {s.media_type === 'video'
              ? <video src={s.file_url} className="w-full h-full object-cover" controls playsInline preload="metadata" />
              : <img src={s.file_url} className="w-full h-full object-cover" loading="lazy" />}
            <a href={downloadUrl(s.file_url)} className="absolute top-2 right-2 bg-black/70 rounded-lg px-2 py-1 text-xs">⬇</a>
          </div>
        ))}
      </div>
      <button onClick={onClose} className="btn-ghost w-full mt-4">Close</button>
    </Modal>
  )
}
