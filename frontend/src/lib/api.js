// Базовий префікс API. У проді Caddy віддає /api → backend.
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
  leaderboard: () => jfetch('/leaderboard'),
  slideshow: () => jfetch('/slideshow'),
  presign: (uuid, aid, filename, content_type) =>
    jfetch(`/u/${uuid}/assignments/${aid}/presign`, {
      method: 'POST', body: JSON.stringify({ filename, content_type }),
    }),
  complete: (uuid, aid, files) =>
    jfetch(`/u/${uuid}/assignments/${aid}/complete`, {
      method: 'POST', body: JSON.stringify({ files }),
    }),
}

// Завантаження одного файлу: presign -> PUT у R2 -> повертаємо публічний URL.
export async function uploadFile(uuid, assignmentId, file) {
  const { upload_url, public_url } = await api.presign(
    uuid, assignmentId, file.name, file.type || 'application/octet-stream'
  )
  const put = await fetch(upload_url, {
    method: 'PUT',
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
    body: file,
  })
  if (!put.ok) throw new Error('Не вдалося завантажити файл у сховище')
  const media_type = (file.type || '').startsWith('video') ? 'video' : 'image'
  return { public_url, media_type }
}

// Завантаження кількох файлів і фіналізація завдання.
export async function uploadAndComplete(uuid, assignmentId, fileList) {
  const files = []
  for (const f of Array.from(fileList)) {
    files.push(await uploadFile(uuid, assignmentId, f))
  }
  return api.complete(uuid, assignmentId, files)
}

// localStorage helpers для re-entry.
export const store = {
  getUuid: () => localStorage.getItem('player_uuid'),
  setUuid: (u) => localStorage.setItem('player_uuid', u),
  clear: () => localStorage.removeItem('player_uuid'),
}
