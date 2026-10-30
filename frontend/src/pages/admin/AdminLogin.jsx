import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { host } from '../../lib/api'
import { useTheme } from '../../lib/ui'

export default function AdminLogin() {
  const nav = useNavigate()
  const [mode, setMode] = useState('login')
  const [signupOpen, setSignupOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  useTheme('party')

  useEffect(() => {
    host.me().then(() => nav('/admin/games', { replace: true })).catch(() => {})
    host.status().then((s) => { setSignupOpen(s.signup_open); if (s.signup_open) setMode('signup') }).catch(() => {})
  }, [nav])

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      if (mode === 'signup') await host.signup({ email, password })
      else await host.login({ email, password })
      nav('/admin/games')
    } catch (e2) { setErr(e2.message) } finally { setBusy(false) }
  }

  return (
    <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 text-cream font-body">
      <h1 className="font-display font-extrabold text-4xl text-zest mb-1">Host</h1>
      <p className="text-cream/50 text-sm mb-8">{mode === 'signup' ? 'Create the owner account' : 'Log in to manage your games'}</p>
      <form onSubmit={submit} className="w-full max-w-xs space-y-3">
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="field" autoComplete="email" />
        <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)}
          placeholder={mode === 'signup' ? 'Password (8+ characters)' : 'Password'} className="field"
          autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} />
        {err && <p className="text-punch text-sm text-center">{err}</p>}
        <button disabled={busy} className="btn-primary w-full">{busy ? '…' : mode === 'signup' ? 'Create account' : 'Log in'}</button>
      </form>
      {signupOpen && (
        <button onClick={() => setMode(mode === 'login' ? 'signup' : 'login')} className="text-cream/40 text-xs underline mt-6">
          {mode === 'login' ? 'Create an account' : 'I already have an account'}
        </button>
      )}
    </div>
  )
}
