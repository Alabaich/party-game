import { useEffect, useState } from 'react'
import QR from 'qrcode'

export const THEME_EMOJI = { party: '🍻', halloween: '🎃', diwali: '🪔' }
export const TYPE_LABEL = { 1: 'SOLO', 2: 'TARGET', 3: 'PAIR' }
export const TYPE_COLOR = { 1: 'bg-mint', 2: 'bg-zest', 3: 'bg-punch' }

export function useTheme(theme) {
  useEffect(() => {
    document.documentElement.dataset.theme = theme || 'party'
  }, [theme])
}

export function joinUrl(code) {
  return `${window.location.origin}/g/${code}`
}

export function QRCode({ value, size = 220 }) {
  const [src, setSrc] = useState('')
  useEffect(() => {
    QR.toDataURL(value, { width: size * 2, margin: 1 }).then(setSrc).catch(() => setSrc(''))
  }, [value, size])
  return src ? <img src={src} width={size} height={size} alt="QR code" className="rounded-xl" /> : null
}

export function fmtDuration(sec) {
  if (sec == null) return '—'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const pad = (n) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

export function placeLabel(place) {
  return { 1: '🥇 1st', 2: '🥈 2nd', 3: '🥉 3rd' }[place] || `⭐ ${place}`
}

export function Center({ children }) {
  return (
    <div className="relative z-10 min-h-screen flex items-center justify-center text-cream/70 font-body px-6 text-center">
      {children}
    </div>
  )
}

export function Modal({ onClose, children, wide }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4 py-6" onClick={onClose}>
      <div className={`animate-pop bg-ink border-2 border-cream/20 rounded-3xl p-5 w-full ${wide ? 'max-w-2xl' : 'max-w-sm'} max-h-full overflow-auto text-cream`}
        onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  )
}

export function Prizes({ prizes, compact }) {
  const list = (prizes || []).filter((p) => p.title)
  if (!list.length) return null
  return (
    <div className={compact ? 'space-y-1' : 'space-y-2'}>
      {list.map((p, i) => (
        <div key={i} className={`flex justify-between gap-3 ${compact ? 'text-sm' : 'card px-4 py-3'}`}>
          <span className="text-cream/70">{placeLabel(p.place)}</span>
          <span className="font-bold text-zest text-right">{p.title}</span>
        </div>
      ))}
    </div>
  )
}

// Tells players where their photos go, based on the game's gallery setting.
export function PhotoNotice({ settings, className = '' }) {
  const hasEmail = settings.questions.some((q) => q.kind === 'email')
  return (
    <div className={`card px-4 py-3 text-sm text-cream/80 ${className}`}>
      <p>📺 Your photos and videos appear on the <b className="text-cream">big screen</b> during the party.</p>
      {settings.gallery === 'public' ? (
        <p className="mt-1 text-cream/60">Everyone with the game link can also see them in the gallery.</p>
      ) : (
        <p className="mt-1 text-cream/60">
          There's no public gallery.{' '}
          {hasEmail ? 'If you leave your email, we\'ll send you the photos after the event.' : 'You can always see your own uploads under 🖼 Mine.'}
        </p>
      )}
    </div>
  )
}

// Browsers allow muted autoplay always, but sound only after someone has
// clicked the page. Start muted until then; skip videos that never start
// (e.g. a codec this browser can't decode). Returns a cleanup function.
export function playVideo(video, { onMuted, onStuck } = {}) {
  if (!video) return () => {}
  const canSound = navigator.userActivation ? navigator.userActivation.hasBeenActive : false
  video.muted = !canSound
  if (video.muted) onMuted?.()
  video.play().catch(() => {
    if (!video.muted) { video.muted = true; onMuted?.() }
    video.play().catch(() => {})
  })
  const t = setTimeout(() => { if (video.currentTime < 0.2) onStuck?.() }, 8000)
  return () => clearTimeout(t)
}
