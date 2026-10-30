const API = import.meta.env.VITE_API_BASE || '/api'

async function jfetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const t = await res.text().catch(() => '')
    throw new Error(t || `HTTP ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}

function adminHeaders(pin) {
  return { 'Content-Type': 'application/json', 'X-Admin-Pin': pin || '' }
}

export const api = {
  register: (name, is_drinking) =>
    jfetch('/register', { method: 'POST', body: JSON.stringify({ name, is_drinking }) }),
  players: () => jfetch('/players'),
  dashboard: (uuid) => jfetch(`/u/${uuid}`),
  gameStatus: () => jfetch('/game'),
  startGame: (pin) => jfetch('/game/start', { method: 'POST', headers: adminHeaders(pin) }),
  revealPlaces: (pin) => jfetch('/game/reveal', { method: 'POST', headers: adminHeaders(pin) }),
  leaderboard: () => jfetch('/leaderboard'),
  // gameId is optional: omit for legacy unscoped behavior (all media);
  // pass an id to restrict to one game's players.
  slideshow: (gameId) =>
    jfetch(gameId ? `/slideshow?game_id=${encodeURIComponent(gameId)}` : '/slideshow'),
  complete: (uuid, aid, files) =>
    jfetch(`/u/${uuid}/assignments/${aid}/complete`, {
      method: 'POST', body: JSON.stringify({ files }),
    }),
}

export async function uploadFile(uuid, assignmentId, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}/u/${uuid}/assignments/${assignmentId}/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const t = await res.text().catch(() => '')
    throw new Error(t || `Upload failed: HTTP ${res.status}`)
  }
  const { public_url } = await res.json()
  const media_type = (file.type || '').startsWith('video') ? 'video' : 'image'
  return { public_url, media_type }
}

export async function uploadAndComplete(uuid, assignmentId, fileList) {
  const files = []
  for (const f of Array.from(fileList)) {
    files.push(await uploadFile(uuid, assignmentId, f))
  }
  return api.complete(uuid, assignmentId, files)
}

export async function freeUpload(uuid, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}/u/${uuid}/free-upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const t = await res.text().catch(() => '')
    throw new Error(t || `Upload failed: HTTP ${res.status}`)
  }
  return res.json()
}

// Pin the legacy /gallery to the original birthday game.
// Leave as null (or '') to keep showing ALL media (current behavior).
// After running the backfill script, set this to that game's id.
export const BIRTHDAY_GAME_ID = null

// Host PIN for start/reveal; remembered on the host's device only.
export const adminPin = {
  get: () => { try { return localStorage.getItem('admin_pin') || '' } catch { return '' } },
  set: (v) => { try { localStorage.setItem('admin_pin', v) } catch { /* ignore */ } },
  clear: () => { try { localStorage.removeItem('admin_pin') } catch { /* ignore */ } },
}

// Run a host action; ask for the PIN if missing or rejected.
export async function withAdminPin(action) {
  let pin = adminPin.get()
  for (let attempt = 0; attempt < 2; attempt++) {
    if (!pin) {
      pin = window.prompt('Host PIN') || ''
      if (!pin) throw new Error('PIN required')
    }
    try {
      const res = await action(pin)
      adminPin.set(pin)
      return res
    } catch (e) {
      if (!String(e.message).includes('Wrong admin PIN')) throw e
      adminPin.clear(); pin = ''
    }
  }
  throw new Error('Wrong admin PIN')
}

export const store = {
  getUuid: () => localStorage.getItem('player_uuid'),
  setUuid: (u) => localStorage.setItem('player_uuid', u),
  clear: () => localStorage.removeItem('player_uuid'),
}
