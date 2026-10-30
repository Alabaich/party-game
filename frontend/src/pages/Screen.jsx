import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { useTheme, QRCode, joinUrl, fmtDuration, Prizes, THEME_EMOJI, playVideo, LogoBar, PHOTO_RULE } from '../lib/ui'
import Pumpkin from '../lib/Pumpkin'

const PHOTO_MS = 10000
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

// ─── New-player announcements ──────────────────────────────────────────────
// Polls the player list and plays each newcomer's name once, one at a time.
const ANNOUNCE_MS = 3600
const GAP_MS = 700

function useJoinAnnouncer(code) {
  const [current, setCurrent] = useState(null)
  const seen = useRef(null)
  const queue = useRef([])
  const busy = useRef(false)

  const next = useCallback(() => {
    if (busy.current || !queue.current.length) return
    busy.current = true
    setCurrent(queue.current.shift())
    setTimeout(() => {
      setCurrent(null)
      setTimeout(() => { busy.current = false; next() }, GAP_MS)
    }, ANNOUNCE_MS)
  }, [])

  useEffect(() => {
    let alive = true
    const poll = async () => {
      try {
        const players = await api.players(code)
        if (!alive) return
        if (seen.current === null) {
          seen.current = new Set(players.map((p) => p.key))   // don't announce people already here
          return
        }
        const fresh = players.filter((p) => !seen.current.has(p.key))
        fresh.forEach((p) => seen.current.add(p.key))
        if (fresh.length) { queue.current.push(...fresh.map((p) => p.name)); next() }
      } catch { /* ignore */ }
    }
    poll()
    const t = setInterval(poll, 3000)
    return () => { alive = false; clearInterval(t) }
  }, [code, next])

  return current
}

// ─── Slide media ───────────────────────────────────────────────────────────

function SlideMedia({ slide, onEnded }) {
  const videoRef = useRef(null)
  const [muted, setMuted] = useState(false)
  useEffect(() => {
    setMuted(false)
    if (slide?.media_type !== 'video') return
    return playVideo(videoRef.current, { onMuted: () => setMuted(true), onStuck: onEnded })
  }, [slide?.file_url])  // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    // first click anywhere on the TV page turns the sound on
    const unmute = () => { if (videoRef.current) { videoRef.current.muted = false; setMuted(false) } }
    document.addEventListener('click', unmute)
    return () => document.removeEventListener('click', unmute)
  }, [])
  if (!slide) return null
  return (
    <div className="relative w-full h-full flex items-center justify-center bg-black overflow-hidden">
      {slide.media_type === 'video' ? (
        <video
          ref={videoRef}
          key={slide.file_url}
          src={slide.file_url}
          playsInline preload="auto"
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
      {muted && slide.media_type === 'video' && (
        <span className="absolute top-4 right-4 bg-black/70 text-cream/70 text-xs px-3 py-1 rounded-full">🔇 click anywhere for sound</span>
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

export default function Screen() {
  const { code: rawCode } = useParams()
  const code = rawCode.toUpperCase()
  const [items, setItems] = useState([])
  const [game, setGame] = useState(null)
  const [slides, setSlides] = useState([])
  useTheme(game?.settings.theme)

  const { idx, currentNotif, advanceSlide, advanceNotif, queueLength } = useSlideshow(slides)
  const joined = useJoinAnnouncer(code)
  // clicking the pumpkin makes it shout something; a real newcomer always wins
  const [boo, setBoo] = useState(null)
  const booTimer = useRef(null)
  const poke = useCallback(() => {
    if (joined || boo) return
    const lines = ['BOO!', 'Happy Halloween!', 'Trick or treat?', 'Join us!', 'Rawr!']
    setBoo(lines[Math.floor(Math.random() * lines.length)])
    clearTimeout(booTimer.current)
    booTimer.current = setTimeout(() => setBoo(null), 2600)
  }, [joined, boo])
  useEffect(() => () => clearTimeout(booTimer.current), [])
  const pumpkinText = joined || boo
  const pumpkinSub = joined ? 'JUST JOINED!' : 'SCAN ME TO JOIN!'

  const load = useCallback(async () => {
    try {
      const [lb, gs] = await Promise.all([api.leaderboard(code), api.game(code)])
      setItems(lb); setGame(gs)
      // private galleries only load in the host's logged-in browser
      setSlides(await api.slideshow(code).catch(() => []))
    } catch { /* ignore */ }
  }, [code])

  useEffect(() => {
    load()
    const id = setInterval(load, 7000)
    return () => clearInterval(id)
  }, [load])

  const revealed = game?.places_revealed
  const url = joinUrl(code)
  const n = game?.tasks_per_user || 7
  const emoji = THEME_EMOJI[game?.settings.theme] || '🎉'
  const prizes = game?.settings.prizes || []
  const finished = items.filter(i => i.finished)
  const inProgress = items.filter(i => !i.finished)
  const currentSlide = slides.length ? slides[idx % slides.length] : null
  const displaySlide = currentNotif || currentSlide
  const isNotif = !!currentNotif
  const spooky = game?.settings.theme === 'halloween'

  const logos = game?.settings.logos || []

  // ── BIG QR SCREEN: before the start, and after it until the first photo ──
  if (game && (!game.started || slides.length === 0)) {
    const started = game.started
    return (
      <div className="relative z-10 min-h-screen text-cream font-body flex flex-col">
        <LogoBar logos={logos} className="h-14 px-10 pt-5" />
        <div className="flex-1 flex flex-col lg:flex-row">
        <div className="lg:w-1/2 flex flex-col items-center justify-center px-10 py-8 border-r border-cream/10">
          <h1 className="font-display font-extrabold text-4xl xl:text-5xl text-zest text-center mb-2">{emoji} {game.name}</h1>
          <p className="text-mint tracking-widest text-sm mb-2">{started ? 'LATE? SCAN TO JOIN' : 'SCAN TO JOIN'}</p>
          {spooky ? (
            <Pumpkin value={url} announce={pumpkinText} subtitle={pumpkinSub} onClick={poke} className="w-full max-w-[34rem] h-[52vh]" />
          ) : (
            <>
              <div className="bg-white p-3 rounded-2xl mb-2 shadow-2xl"><QRCode value={url} size={260} /></div>
              <p className={`h-8 font-display font-bold text-xl text-zest transition-opacity ${joined ? 'opacity-100 animate-pop' : 'opacity-0'}`}>
                {joined && `👋 ${joined} just joined!`}
              </p>
            </>
          )}
          <p className="text-cream/60 text-lg mt-2">{url.replace(/^https?:\/\//, '')} · code <span className="text-zest font-bold tracking-widest">{code}</span></p>
          <div className="text-center mt-4">
            <p className="font-display font-extrabold text-7xl text-zest leading-none tabular-nums">{game.player_count}</p>
            <p className="text-cream/70 tracking-widest text-sm mt-1">{game.player_count === 1 ? 'NEIGHBOUR' : 'NEIGHBOURS'} JOINED</p>
            <p className="text-cream/40 text-sm mt-2">
              {started ? 'The game is on!' : game.is_draft ? 'Registration opens soon…' : 'The game starts soon…'}
            </p>
          </div>
        </div>
        {started ? (
          <div className="lg:w-1/2 flex flex-col px-10 py-8 min-h-0">
            <p className="font-display font-extrabold text-5xl text-zest leading-tight">{emoji} The game has started!</p>
            <p className="text-cream/70 text-xl mt-3">📸 Waiting for the first photos… Complete a task to be first on the big screen!</p>
            <p className="text-cream/80 text-lg mt-3 mb-8">🙋 {PHOTO_RULE}</p>
            <p className="text-mint tracking-widest text-sm mb-3">PLAYERS</p>
            <div className="grid grid-cols-2 xl:grid-cols-3 gap-2 overflow-hidden">
              {items.map((it) => (
                <div key={it.user_id} className="card px-3 py-2 flex justify-between gap-2">
                  <span className="font-bold truncate">{it.name}</span>
                  <span className="text-zest tabular-nums shrink-0">{it.completed_count}/{it.total || n}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
        <div className="lg:w-1/2 flex flex-col justify-center px-10 py-8">
          <p className="text-mint tracking-widest text-sm mb-4">HOW TO PLAY</p>
          <div className="space-y-5">
            {prizes.some((p) => p.title) && (
              <div className="mb-2"><p className="font-display font-bold text-cream mb-2">🏆 Prizes for the fastest</p><Prizes prizes={prizes} /></div>
            )}
            <Rule emoji="🎯" title={`Complete ${n} tasks`}>Each player gets {n} challenges — solo, finding another player, or paired with a partner. A great way to meet your neighbours!</Rule>
            <Rule emoji="📸" title="Upload proof">Every completed task needs photo or video evidence. Tap 📷 Add photo under the task.</Rule>
            <Rule emoji="🙋" title="Ask before you snap">Only photograph people who are playing, and no photos of kids unless they're yours.</Rule>
            <Rule emoji="⚡" title="Fastest wins">The timer starts when the game begins. Finish all {n} tasks as fast as possible.</Rule>
            <Rule emoji="🤝" title="Paired tasks">When one partner uploads proof — the task closes for both automatically.</Rule>
            <Rule emoji="🃏" title="Can't do a task?">Tap <span className="text-zest font-bold">Can't do this one?</span> under the task and complete a wildcard instead.</Rule>
            <Rule emoji="📱" title="Just want to share?">Use the <span className="text-zest font-bold">📸 Just Upload</span> button to post any photo or video to the big screen without completing a task.</Rule>
          </div>
        </div>
        )}
        </div>
      </div>
    )
  }

  // ── IN-GAME SCREEN ───────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 text-cream font-body flex">

      {/* Left: leaderboard */}
      <div className="w-1/2 flex-shrink-0 h-screen overflow-y-auto px-5 py-6 border-r border-cream/10 bg-ink">
        <LogoBar logos={logos} className="h-10 mb-4" />
        <header className="flex items-center justify-between mb-4">
          <h1 className="font-display font-extrabold text-2xl text-zest">🏆 {game?.name || 'Leaderboard'}</h1>
          <Link to={`/g/${code}/slideshow`} className="bg-cream/10 px-3 py-2 rounded-xl text-xs">📺 Full</Link>
        </header>

        <div className="flex items-center gap-4 mb-4 card p-3">
          {spooky
            ? <Pumpkin value={url} announce={pumpkinText} subtitle={pumpkinSub} onClick={poke} className="w-72 h-72 shrink-0" />
            : <div className="bg-white p-2 rounded-xl shrink-0"><QRCode value={url} size={150} /></div>}
          <div>
            <p className="text-mint tracking-widest text-xs">GAME IN PROGRESS ▶</p>
            <p className="font-display font-extrabold text-3xl mt-1">Late?<br />Scan to join!</p>
            <p className="text-cream/60 text-sm mt-1">code <span className="text-zest font-bold tracking-widest">{code}</span> · {game?.player_count} players</p>
            {!spooky && joined && <p className="text-zest font-bold mt-2 animate-pop">👋 {joined} just joined!</p>}
          </div>
        </div>

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
                  <p className="text-zest font-bold text-xs tabular-nums">{it.completed_count}/{it.total || n}</p>
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