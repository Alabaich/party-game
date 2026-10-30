import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { store } from '../lib/api'
import { useTheme } from '../lib/ui'

export default function Home() {
  const nav = useNavigate()
  const [code, setCode] = useState('')
  useTheme('party')

  useEffect(() => {
    const last = store.lastPlayer()
    if (last) nav(`/u/${last}`, { replace: true })
  }, [nav])

  function go(e) {
    e.preventDefault()
    const c = code.trim().toUpperCase()
    if (c) nav(`/g/${c}`)
  }

  return (
    <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 text-cream font-sans">
      <div className="animate-float mb-2 text-6xl">🎉</div>
      <h1 className="font-display font-extrabold text-5xl text-zest text-center leading-none mb-1">PARTY QUEST</h1>
      <p className="text-mint mb-10 tracking-widest text-sm">QUEST · CHALLENGE · MEET</p>
      <form onSubmit={go} className="w-full max-w-xs space-y-3">
        <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Game code"
          maxLength={8} autoCapitalize="characters"
          className="field text-center text-2xl tracking-[0.3em] uppercase" />
        <button className="btn-primary w-full text-lg">Join game</button>
      </form>
      <p className="text-cream/40 text-sm mt-6 text-center">Scan the QR code at the party<br />or enter the code from the screen.</p>
      <Link to="/admin" className="text-cream/30 text-xs underline underline-offset-4 mt-16">Host login</Link>
    </div>
  )
}
