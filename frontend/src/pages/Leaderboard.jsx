import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

const PHOTO_MS = 10000
const GAME_URL = 'https://party.enjob.ca'

function fmtDuration(sec) {
  if (sec == null) return '—'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const pad = (n) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

function QRCode({ url, size = 200 }) {
  const canvasRef = useRef(null)
  useEffect(() => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.src = `https://chart.googleapis.com/chart?cht=qr&chs=${size}x${size}&chl=${encodeURIComponent(url)}&choe=UTF-8&chld=M|2`
    img.onload = () => {
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      canvas.width = size
      canvas.height = size
      ctx.fillStyle = '#fff'
      ctx.fillRect(0, 0, size, size)
      ctx.drawImage(img, 0, 0, size, size)
    }
  }, [url, size])
  return <canvas ref={canvasRef} width={size} height={size} className="rounded-2xl" style={{ imageRendering: 'pixelated' }} />
}

// ─── Slideshow hook ────────────────────────────────────────────────────────

function useSlideshow(slides) {
  const [idx, setIdx] = useState(0)
  const [notifQueue, setNotifQueue] = useState([])
  const [currentNotif, setCurrentNotif] = useState(null)

  // refs — updated silently, never cause timer resets
  const slidesRef = useRef(slides)
  const idxRef = useRef(0)
  const seenIdsRef = useRef(null)
  const notifTimerRef = useRef(null)
  const slideTimerRef = useRef(null)
  const currentNotifRef = useRef(null)

  // keep refs in sync
  useEffect(() => { slidesRef.current = slides }, [slides])
  useEffect(() => { currentNotifRef.current = currentNotif }, [currentNotif])

  // ── advance functions ──────────────────────────────────────────────────
  const scheduleSlide = useCallback((ms) => {
    clearTimeout(slideTimerRef.current)
    slideTimerRef.current = setTimeout(() => {
      // only advance if no notif is playing
      if (!currentNotifRef.current) {
        const len = slidesRef.current.length || 1
        const next = (idxRef.current + 1) % len
        idxRef.current = next
        setIdx(next)
      }
      // reschedule after advancing
      const cur = slidesRef.current[idxRef.current % (slidesRef.current.length || 1)]
      scheduleSlide(cur?.media_type === 'image' ? PHOTO_MS : 90000)
    }, ms)
  }, [])

  const scheduleNotif = useCallback((ms) => {
    clearTimeout(notifTimerRef.current)
    notifTimerRef.current = setTimeout(() => {
      setCurrentNotif(null)
      currentNotifRef.current = null
      setNotifQueue(q => q.slice(1))
    }, ms)
  }, [])

  // ── start slide timer once on mount ───────────────────────────────────
  useEffect(() => {
    scheduleSlide(PHOTO_MS)
    return () => {
      clearTimeout(slideTimerRef.current)
      clearTimeout(notifTimerRef.current)
    }
  }, [scheduleSlide])

  // ── detect new slides from polling ────────────────────────────────────
  useEffect(() => {
    if (!slides.length) return
    if (seenIdsRef.current === null) {
      seenIdsRef.current = new Set(slides.map(s => s.id))
      return
    }
    const newSlides = slides.filter(s => !seenIdsRef.current.has(s.id))
    newSlides.forEach(s => seenIdsRef.current.add(s.id))
    if (newSlides.length > 0) setNotifQueue(q => [...q, ...newSlides])
  }, [slides])

  // ── pop next notif when queue has items and nothing playing ───────────
  useEffect(() => {
    if (currentNotif || notifQueue.length === 0) return
    const notif = notifQueue[0]
    setCurrentNotif(notif)
    currentNotifRef.current = notif
    scheduleNotif(notif.media_type === 'image' ? PHOTO_MS : 90000)
  }, [notifQueue, currentNotif, scheduleNotif])

  const advanceNotifNow = useCallback(() => {
    clearTimeout(notifTimerRef.current)
    setCurrentNotif(null)
    currentNotifRef.current = null
    setNotifQueue(q => q.slice(1))
  }, [])

  const advanceSlideNow = useCallback(() => {
    if (currentNotifRef.current) return
    const len = slidesRef.current.length || 1
    const next = (idxRef.current + 1) % len
    idxRef.current = next
    setIdx(next)
    const cur = slidesRef.current[next % len]
    scheduleSlide(cur?.media_type === 'image' ? PHOTO_MS : 90000)
  }, [scheduleSlide])

  return {
    idx,
    currentNotif,
    advanceSlide: advanceSlideNow,
    advanceNotif: advanceNotifNow,
    queueLength: notifQueue.length,
  }
}

// ─── Slide media ───────────────────────────────────────────────────────────

function SlideMedia({ slide, onEnded }) {
  const videoRef = useRef(null)
  useEffect(() => {
    if (videoRef.current) videoRef.current.play().catch(() => {})
  }, [slide?.file_url])
  if (!slide) return null
  return (
    <div className="relative w-full h-full flex items-center justify-center bg-black overflow-hidden">
      {slide.media_type === 'video' ? (
        <video
          ref={videoRef}
          key={slide.file_url}
          src={slide.file_url}
          autoPlay playsInline muted={false}
          onEnded={onEnded} onError={onEnded}
          style={{ maxWidth: "100%", maxHeight: "100vh", objectFit: "contain" }}
        />
      ) : (
        <img
          key={slide.file_url}
          src={slide.file_url}
          style={{ maxWidth: "100%", maxHeight: "100vh", objectFit: "contain" }}
        />
      )}
      <div className="absolute bottom-0 inset-x-0 p-4 bg-gradient-to-t from-black/90 via-black/50 to-transparent">
        <p className="font-display font-extrabold text-2xl text-zest">{slide.user_name}</p>
        {slide.task_description
          ? <p className="text-cream/80 text-sm mt-1 line-clamp-2">{slide.task_description}</p>
          : <p className="text-cream/50 text-sm italic">just sharing 📸</p>}
      </div>
    </div>
  )
}

// ─── Main ──────────────────────────────────────────────────────────────────

export default function Leaderboard() {
  const [items, setItems] = useState([])
  const [game, setGame] = useState(null)
  const [slides, setSlides] = useState([])
  const [starting, setStarting] = useState(false)
  const [revealing, setRevealing] = useState(false)
  const [err, setErr] = useState('')

  const { idx, currentNotif, advanceSlide, advanceNotif, queueLength } = useSlideshow(slides)

  const load = useCallback(async () => {
    try {
      const [lb, gs, sl] = await Promise.all([api.leaderboard(), api.gameStatus(), api.slideshow()])
      setItems(lb); setGame(gs); setSlides(sl)
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

  async function onReveal() {
    if (!confirm('Reveal places to all players? This cannot be undone.')) return
    setRevealing(true); setErr('')
    try { await api.revealPlaces(); await load() }
    catch (e) { setErr(e.message || 'Failed to reveal') }
    finally { setRevealing(false) }
  }

  const revealed = game?.places_revealed
  const totalTasks = items.length ? Math.max(...items.map(i => i.completed_count), 7) : 7
  const finished = items.filter(i => i.finished)
  const inProgress = items.filter(i => !i.finished)
  const currentSlide = slides.length ? slides[idx % slides.length] : null
  const displaySlide = currentNotif || currentSlide
  const isNotif = !!currentNotif

  // ── PRE-GAME SCREEN ──────────────────────────────────────────────────────
  if (game && !game.started) {
    return (
      <div className="relative z-10 min-h-screen text-cream font-body flex flex-col lg:flex-row">
        <div className="lg:w-1/2 flex flex-col items-center justify-center px-10 py-12 border-r border-cream/10">
          <p className="text-mint tracking-widest text-sm mb-2">SCAN TO JOIN</p>
          <h1 className="font-display font-extrabold text-5xl text-zest text-center mb-6">PARTY<br/>QUEST</h1>
          <div className="bg-white p-3 rounded-2xl mb-4 shadow-2xl">
            <QRCode url={GAME_URL} size={220} />
          </div>
          <p className="text-cream/50 text-sm mb-8">{GAME_URL}</p>
          <div className="w-full max-w-xs text-center">
            <p className="text-cream/80 mb-2">Players joined: <span className="text-zest font-bold text-xl">{game.player_count}</span></p>
            <button onClick={onStart} disabled={starting || game.player_count === 0}
              className="w-full bg-punch text-cream font-display font-extrabold text-2xl py-4 rounded-2xl active:scale-95 transition-transform disabled:opacity-50 mt-4">
              {starting ? 'STARTING…' : '🚀 START GAME'}
            </button>
            {err && <p className="text-punch text-sm mt-3">{err}</p>}
          </div>
        </div>
        <div className="lg:w-1/2 flex flex-col justify-center px-10 py-12">
          <p className="text-mint tracking-widest text-sm mb-4">HOW TO PLAY</p>
          <div className="space-y-5">
            <Rule emoji="🎯" title="Complete 7 tasks">Each player gets 7 unique challenges — solo, targeted at another player, or paired with a partner.</Rule>
            <Rule emoji="📸" title="Upload proof">Every completed task needs photo or video evidence. Tap the task to upload.</Rule>
            <Rule emoji="⚡" title="Fastest wins">The timer starts when the game begins. Finish all 7 tasks as fast as possible.</Rule>
            <Rule emoji="🤝" title="Paired tasks">When one partner uploads proof — the task closes for both automatically.</Rule>
            <Rule emoji="🙈" title="Want to skip a task?">Take a <span className="text-zest font-bold">unique group photo</span> with several people all looking at the camera and upload it as proof. Each skip needs its own new group photo — no reusing!</Rule>
            <Rule emoji="📱" title="Just want to share?">Use the <span className="text-zest font-bold">📸 Just Upload</span> button to post any photo or video to the big screen without completing a task.</Rule>
          </div>
        </div>
      </div>
    )
  }

  // ── IN-GAME SCREEN ───────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 text-cream font-body flex">

      {/* Left: leaderboard */}
      <div className="w-1/2 flex-shrink-0 h-screen overflow-y-auto px-5 py-6 border-r border-cream/10 bg-ink">
        <header className="flex items-center justify-between mb-4">
          <h1 className="font-display font-extrabold text-2xl text-zest">🏆 Leaderboard</h1>
          <Link to="/slideshow" className="bg-cream/10 px-3 py-2 rounded-xl text-xs">📺 Full</Link>
        </header>

        <p className="text-mint text-center text-xs mb-4 tracking-widest">GAME IN PROGRESS ▶</p>

        {/* Reveal — subtle */}
        {!revealed && (
          <div className="mb-4 text-center">
            <button onClick={onReveal} disabled={revealing}
              className="text-cream/30 text-xs underline underline-offset-2 hover:text-cream/60 transition-colors disabled:opacity-50">
              {revealing ? 'revealing…' : 'reveal places'}
            </button>
          </div>
        )}

        {revealed && (
          <div className="mb-4 bg-mint/10 border border-mint/30 rounded-xl px-3 py-2 text-center">
            <p className="text-mint text-xs tracking-widest">🎉 PLACES REVEALED</p>
          </div>
        )}

        {finished.length > 0 && (
          <>
            <p className="text-cream/50 text-xs tracking-widest mb-2">FINISHED</p>
            <div className="grid grid-cols-3 gap-1.5 mb-4">
              {finished.map((it, i) => (
                <div key={it.user_id} className="bg-zest/10 border border-zest/40 rounded-xl p-2 text-center">
                  <p className="font-display font-extrabold text-base text-zest mb-0.5">
                    {revealed ? (i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i+1}`) : '✓'}
                  </p>
                  <p className="font-bold text-xs leading-tight truncate">{it.name}</p>
                  {revealed && <p className="text-mint text-xs tabular-nums mt-0.5">{fmtDuration(it.duration_seconds)}</p>}
                </div>
              ))}
            </div>
          </>
        )}

        {inProgress.length > 0 && (
          <>
            <p className="text-cream/50 text-xs tracking-widest mb-2">IN PROGRESS</p>
            <div className="grid grid-cols-3 gap-1.5">
              {inProgress.map((it) => (
                <div key={it.user_id} className="bg-cream/5 border border-cream/15 rounded-xl p-2 text-center">
                  <p className="font-bold text-xs leading-tight truncate mb-0.5">{it.name}</p>
                  <p className="text-zest font-bold text-xs tabular-nums">{it.completed_count}/{totalTasks}</p>
                </div>
              ))}
            </div>
          </>
        )}

        {items.length === 0 && <p className="text-cream/40 text-center py-10 text-sm">Nothing here yet</p>}
      </div>

      {/* Right: slideshow — fills remaining space */}
      <div className="w-1/2 relative bg-black h-screen flex items-center justify-center">
        {displaySlide ? (
          <>
            {isNotif && (
              <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
                <span className="bg-punch text-cream text-xs font-bold px-3 py-1 rounded-full animate-pulse">
                  🔔 JUST COMPLETED
                </span>
                {queueLength > 1 && (
                  <span className="bg-cream/20 text-cream text-xs px-2 py-1 rounded-full">+{queueLength - 1} more</span>
                )}
              </div>
            )}
            <SlideMedia slide={displaySlide} onEnded={isNotif ? advanceNotif : advanceSlide} />
          </>
        ) : (
          <div className="text-cream/30 font-body text-center px-6">
            <p className="text-5xl mb-4">📸</p>
            <p>Waiting for first uploads…</p>
          </div>
        )}
      </div>
    </div>
  )
}

function Rule({ emoji, title, children }) {
  return (
    <div className="flex gap-4 items-start">
      <span className="text-2xl flex-shrink-0 mt-0.5">{emoji}</span>
      <div>
        <p className="font-display font-bold text-cream">{title}</p>
        <p className="text-cream/60 text-sm leading-relaxed">{children}</p>
      </div>
    </div>
  )
}