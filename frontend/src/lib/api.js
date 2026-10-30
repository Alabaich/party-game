const API = import.meta.env.VITE_API_BASE || '/api'

async function jfetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    credentials: 'same-origin',
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try {
      const body = await res.json()
      msg = typeof body.detail === 'string' ? body.detail
        : Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join('; ') : msg
    } catch { /* not json */ }
    const err = new Error(msg)
    err.status = res.status
    throw err
  }
  return res.status === 204 ? null : res.json()
}

const post = (path, body) => jfetch(path, { method: 'POST', body: JSON.stringify(body ?? {}) })

export const api = {
  // players & TV
  game: (code) => jfetch(`/g/${code}`),
  register: (code, body) => post(`/g/${code}/register`, body),
  players: (code) => jfetch(`/g/${code}/players`),
  leaderboard: (code) => jfetch(`/g/${code}/leaderboard`),
  slideshow: (code) => jfetch(`/g/${code}/slideshow`),
  dashboard: (uuid) => jfetch(`/u/${uuid}`),
  complete: (uuid, aid, files, substitute_task_id) =>
    post(`/u/${uuid}/assignments/${aid}/complete`, { files, substitute_task_id: substitute_task_id || null }),
  myMedia: (uuid) => jfetch(`/u/${uuid}/media`),
}

export const host = {
  status: () => jfetch('/auth/status'),
  signup: (body) => post('/auth/signup', body),
  login: (body) => post('/auth/login', body),
  logout: () => post('/auth/logout'),
  me: () => jfetch('/auth/me'),
  games: () => jfetch('/admin/games'),
  createGame: (body) => post('/admin/games', body),
  game: (id) => jfetch(`/admin/games/${id}`),
  updateGame: (id, body) => jfetch(`/admin/games/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  publish: (id) => post(`/admin/games/${id}/publish`),
  unpublish: (id) => post(`/admin/games/${id}/unpublish`),
  start: (id) => post(`/admin/games/${id}/start`),
  reveal: (id) => post(`/admin/games/${id}/reveal`),
  players: (id) => jfetch(`/admin/games/${id}/players`),
  leaderboard: (id) => jfetch(`/admin/games/${id}/leaderboard`),
  packs: () => jfetch('/admin/packs'),
  tasks: (id) => jfetch(`/admin/games/${id}/tasks`),
  addTask: (id, t) => post(`/admin/games/${id}/tasks`, t),
  editTask: (id, tid, t) => jfetch(`/admin/games/${id}/tasks/${tid}`, { method: 'PUT', body: JSON.stringify(t) }),
  deleteTask: (id, tid) => jfetch(`/admin/games/${id}/tasks/${tid}`, { method: 'DELETE' }),
  loadPack: (id, pack, replace) => post(`/admin/games/${id}/tasks/load-pack?pack=${pack}&replace=${!!replace}`),
  media: (id) => jfetch(`/admin/games/${id}/media`),
  setHidden: (id, kind, mid, hidden) => post(`/admin/games/${id}/media/${kind}/${mid}/hidden?hidden=${hidden}`),
  consentsCsvUrl: (id) => `${API}/admin/games/${id}/consents.csv`,
}

async function uploadForm(path, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}${path}`, { method: 'POST', body: form })
  if (!res.ok) {
    let msg = `Upload failed: HTTP ${res.status}`
    try { msg = (await res.json()).detail || msg } catch { /* ignore */ }
    throw new Error(msg)
  }
  return res.json()
}

export async function uploadFile(uuid, assignmentId, file) {
  const { public_url } = await uploadForm(`/u/${uuid}/assignments/${assignmentId}/upload`, file)
  const media_type = (file.type || '').startsWith('video') ? 'video' : 'image'
  return { public_url, media_type }
}

export async function uploadAndComplete(uuid, assignmentId, fileList, substituteTaskId) {
  const files = []
  for (const f of Array.from(fileList)) files.push(await uploadFile(uuid, assignmentId, f))
  return api.complete(uuid, assignmentId, files, substituteTaskId)
}

export const freeUpload = (uuid, file) => uploadForm(`/u/${uuid}/free-upload`, file)

export const downloadUrl = (fileUrl) => `${API}/download?url=${encodeURIComponent(fileUrl)}`

// One player per game per device: { [code]: uuid }
function readMap() {
  try { return JSON.parse(localStorage.getItem('players_by_game') || '{}') } catch { return {} }
}
export const store = {
  playerFor: (code) => readMap()[code] || null,
  setPlayer: (code, uuid) => {
    try {
      localStorage.setItem('players_by_game', JSON.stringify({ ...readMap(), [code]: uuid }))
      localStorage.setItem('last_player', uuid)
    } catch { /* ignore */ }
  },
  forget: (code) => {
    try {
      const m = readMap(); delete m[code]
      localStorage.setItem('players_by_game', JSON.stringify(m))
      localStorage.removeItem('last_player')
    } catch { /* ignore */ }
  },
  lastPlayer: () => { try { return localStorage.getItem('last_player') } catch { return null } },
}
