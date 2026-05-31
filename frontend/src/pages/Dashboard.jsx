import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, uploadAndComplete, store } from '../lib/api'

const TYPE_LABEL = { 1: 'SOLO', 2: 'TARGET', 3: 'PAIR' }
const TYPE_COLOR = { 1: 'bg-mint', 2: 'bg-zest', 3: 'bg-punch' }

export default function Dashboard() {
  const { uuid } = useParams()
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')
  const [viewing, setViewing] = useState(null)
  const [uploadingId, setUploadingId] = useState(null)
  const fileRef = useRef(null)
  const pickTargetId = useRef(null)

  const load = useCallback(async () => {
    try {
      const d = await api.dashboard(uuid)
      store.setUuid(uuid)
      setData(d)
    } catch (e) { setErr(e.message) }
  }, [uuid])

  useEffect(() => {
    load()
    const id = setInterval(load, 7000)
    return () => clearInterval(id)
  }, [load])

  if (err) return <Center>{err}</Center>
  if (!data) return <Center>Loading…</Center>

  const started = data.game_started
  const done = data.assignments.filter((a) => a.status === 'completed').length

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

  return (
    <div className="relative z-10 min-h-screen text-cream font-body px-5 py-6 max-w-lg mx-auto">
      <input ref={fileRef} type="file" accept="image/*,video/*" multiple
        className="hidden" onChange={onFiles} />

      <header className="flex items-center justify-between mb-6">
        <div>
          <p className="text-cream/50 text-xs tracking-widest">PLAYER</p>
          <h1 className="font-display font-extrabold text-2xl text-zest">{data.user.name}</h1>
        </div>
        <div className="flex gap-2 text-xs">
          <Link to="/leaderboard" className="bg-cream/10 px-3 py-2 rounded-xl">🏆 Top</Link>
        </div>
      </header>

      {!started ? (
        <div className="text-center py-12">
          <div className="animate-float text-5xl mb-4">⏳</div>
          <p className="font-display font-extrabold text-3xl text-zest mb-2">Waiting to start</p>
          <p className="text-cream/50 text-sm mb-8">The game will begin when the host gives the go</p>

          <div className="text-left">
            <p className="text-mint tracking-widest text-xs mb-3">
              PLAYERS ({data.players.length})
            </p>
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
                  {isDone && (
                    <p className="text-mint/70 text-xs mt-2">Tap to view / replace</p>
                  )}
                </div>
              )
            })}
          </div>
          {err && <p className="text-punch text-center text-sm mt-4">{err}</p>}
        </>
      )}

      {/* View uploaded media + replace */}
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
