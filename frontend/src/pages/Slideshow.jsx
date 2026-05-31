import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../lib/api'

const PHOTO_MS = 10000

// Розгортаємо у плоский список слайдів: кожне медіа = окремий слайд.
function flatten(items) {
  const slides = []
  for (const it of items) {
    for (const m of it.media) {
      slides.push({
        key: `${it.assignment_id}-${m.id}`,
        user_name: it.user_name,
        task: it.task_description,
        url: m.file_url,
        type: m.media_type,
      })
    }
  }
  return slides
}

export default function Slideshow() {
  const [slides, setSlides] = useState([])
  const [idx, setIdx] = useState(0)
  const videoRef = useRef(null)
  const timerRef = useRef(null)
  const slidesRef = useRef([])

  // Періодично підтягуємо нові completed.
  const load = useCallback(async () => {
    try {
      const items = await api.slideshow()
      const next = flatten(items)
      slidesRef.current = next
      setSlides(next)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 15000)
    return () => clearInterval(id)
  }, [load])

  const advance = useCallback(() => {
    setIdx((i) => {
      const len = slidesRef.current.length || 1
      return (i + 1) % len
    })
  }, [])

  // Керування таймінгом поточного слайда.
  useEffect(() => {
    clearTimeout(timerRef.current)
    const cur = slides[idx]
    if (!cur) return
    if (cur.type === 'image') {
      timerRef.current = setTimeout(advance, PHOTO_MS)
    }
    // для відео — перехід по onEnded (нижче). Підстраховка від битого відео:
    else {
      timerRef.current = setTimeout(advance, 60000) // максимум хвилина якщо щось зламалось
    }
    return () => clearTimeout(timerRef.current)
  }, [idx, slides, advance])

  if (slides.length === 0) {
    return (
      <div className="relative z-10 min-h-screen flex items-center justify-center text-cream/60 font-body text-center px-6">
        Очікуємо перших виконаних завдань… 📸
      </div>
    )
  }

  const cur = slides[idx % slides.length]

  return (
    <div className="fixed inset-0 z-20 bg-black flex flex-col items-center justify-center">
      <div className="absolute inset-0 flex items-center justify-center p-4">
        {cur.type === 'video' ? (
          <video
            ref={videoRef}
            key={cur.key}
            src={cur.url}
            autoPlay
            muted={false}
            playsInline
            onEnded={advance}
            onError={advance}
            className="max-h-full max-w-full object-contain rounded-xl"
          />
        ) : (
          <img key={cur.key} src={cur.url}
            className="max-h-full max-w-full object-contain rounded-xl animate-pop" />
        )}
      </div>

      {/* Підпис */}
      <div className="absolute bottom-0 inset-x-0 p-8 bg-gradient-to-t from-black via-black/80 to-transparent">
        <p className="font-display font-extrabold text-4xl sm:text-5xl text-zest leading-none mb-2">
          {cur.user_name}
        </p>
        <p className="font-body text-cream/90 text-lg sm:text-2xl max-w-4xl">{cur.task}</p>
      </div>

      {/* Прогрес-крапки */}
      <div className="absolute top-6 right-8 font-body text-cream/40 text-sm tabular-nums">
        {(idx % slides.length) + 1} / {slides.length}
      </div>
    </div>
  )
}
