import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

function fmtDur(sec) {
  if (sec == null) return ''
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function VideoCard({ slide, onClick }) {
  const [duration, setDuration] = useState(null)
  const vidRef = useRef(null)
  return (
    <div
      onClick={onClick}
      className="relative cursor-pointer rounded-xl overflow-hidden bg-cream/5 border border-cream/10 hover:border-cream/30 transition-all active:scale-95 aspect-square"
    >
      <video
        ref={vidRef}
        src={slide.file_url}
        className="w-full h-full object-cover"
        preload="metadata"
        muted
        onLoadedMetadata={() => setDuration(vidRef.current?.duration)}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="bg-black/50 rounded-full w-10 h-10 flex items-center justify-center">
          <span className="text-white text-lg ml-0.5">▶</span>
        </div>
      </div>
      {duration != null && (
        <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
          {fmtDur(duration)}
        </span>
      )}
      <div className="absolute bottom-0 inset-x-0 p-2 bg-gradient-to-t from-black/80 to-transparent">
        <p className="text-zest text-xs font-bold truncate">{slide.user_name}</p>
      </div>
    </div>
  )
}

function ImageCard({ slide, onClick }) {
  return (
    <div
      onClick={onClick}
      className="relative cursor-pointer rounded-xl overflow-hidden bg-cream/5 border border-cream/10 hover:border-cream/30 transition-all active:scale-95 aspect-square"
    >
      <img src={slide.file_url} className="w-full h-full object-cover" />
      <div className="absolute bottom-0 inset-x-0 p-2 bg-gradient-to-t from-black/80 to-transparent">
        <p className="text-zest text-xs font-bold truncate">{slide.user_name}</p>
      </div>
    </div>
  )
}

function FullscreenView({ slide, onClose }) {
  const videoRef = useRef(null)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  async function handleDownload() {
    const API = import.meta.env.VITE_API_BASE || '/api'
    const proxyUrl = `${API}/download?url=${encodeURIComponent(slide.file_url)}`
    const a = document.createElement('a')
    a.href = proxyUrl
    const ext = slide.media_type === 'video' ? 'mp4' : 'jpg'
    a.download = `${slide.user_name}-${slide.id}.${ext}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex flex-col"
      onClick={onClose}
    >
      {/* top bar */}
      <div
        className="flex items-center justify-between px-4 py-3 flex-shrink-0"
        onClick={e => e.stopPropagation()}
      >
        <div>
          <p className="font-display font-bold text-zest">{slide.user_name}</p>
          {slide.task_description
            ? <p className="text-cream/60 text-xs mt-0.5">{slide.task_description}</p>
            : <p className="text-cream/40 text-xs italic">just sharing 📸</p>}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={e => { e.stopPropagation(); handleDownload() }}
            className="bg-cream/10 hover:bg-cream/20 text-cream px-4 py-2 rounded-xl text-sm font-bold transition-colors"
          >
            ⬇ Download
          </button>
          <button
            onClick={onClose}
            className="bg-cream/10 hover:bg-punch/60 text-cream w-10 h-10 rounded-full flex items-center justify-center text-xl transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      {/* media */}
      <div
        className="flex-1 flex items-center justify-center p-4 min-h-0"
        onClick={e => e.stopPropagation()}
      >
        {slide.media_type === 'video' ? (
          <video
            ref={videoRef}
            src={slide.file_url}
            controls
            autoPlay
            playsInline
            className="max-w-full max-h-full rounded-xl"
            style={{ maxHeight: 'calc(100vh - 100px)' }}
          />
        ) : (
          <img
            src={slide.file_url}
            className="max-w-full max-h-full rounded-xl object-contain"
            style={{ maxHeight: 'calc(100vh - 100px)' }}
          />
        )}
      </div>
    </div>
  )
}

export default function Gallery() {
  const [slides, setSlides] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const items = await api.slideshow()
      setSlides(items)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="relative z-10 min-h-screen text-cream font-body px-4 py-6 max-w-4xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <h1 className="font-display font-extrabold text-3xl text-zest">📷 Gallery</h1>
        <Link to="/leaderboard" className="bg-cream/10 px-3 py-2 rounded-xl text-xs">🏆 Leaderboard</Link>
      </header>

      {loading && <p className="text-cream/40 text-center py-20">Loading…</p>}

      {!loading && slides.length === 0 && (
        <p className="text-cream/40 text-center py-20">No media yet 📭</p>
      )}

      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
        {slides.map(slide => (
          slide.media_type === 'video'
            ? <VideoCard key={slide.id} slide={slide} onClick={() => setSelected(slide)} />
            : <ImageCard key={slide.id} slide={slide} onClick={() => setSelected(slide)} />
        ))}
      </div>

      {selected && (
        <FullscreenView slide={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}