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

export const api = {
  register: (name, is_drinking) =>
    jfetch('/register', { method: 'POST', body: JSON.stringify({ name, is_drinking }) }),
  players: () => jfetch('/players'),
  dashboard: (uuid) => jfetch(`/u/${uuid}`),
  gameStatus: () => jfetch('/game'),
  startGame: () => jfetch('/game/start', { method: 'POST' }),
  revealPlaces: () => jfetch('/game/reveal', { method: 'POST' }),
  leaderboard: () => jfetch('/leaderboard'),
  slideshow: () => jfetch('/slideshow'),
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

export const store = {
  getUuid: () => localStorage.getItem('player_uuid'),
  setUuid: (u) => localStorage.setItem('player_uuid', u),
  clear: () => localStorage.removeItem('player_uuid'),
}