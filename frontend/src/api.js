import {
  demoGetNextQuestion, demoUploadAnswer, demoAskQuestion,
  resetDemoQuestions
} from './demo'

function isDemo() {
  return localStorage.getItem('archaeon-demo') === 'true'
}

const BASE = import.meta.env.VITE_API_URL || ''

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Sessions (Admin)
// ---------------------------------------------------------------------------

export function createSession(data) {
  if (isDemo()) return Promise.resolve({ id: 'demo-session-id', engineer_name: data.engineer_name, status: 'pending', created_at: new Date().toISOString() })
  return request('/api/sessions', {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

export function listSessions() {
  if (isDemo()) return Promise.resolve([])
  return request('/api/sessions')
}

// ---------------------------------------------------------------------------
// Interview
// ---------------------------------------------------------------------------

export function getNextQuestion(sessionId) {
  if (isDemo()) return demoGetNextQuestion(sessionId)
  return request(`/api/sessions/${sessionId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message: '' })
  })
}

export function uploadAnswer(sessionId, text) {
  if (isDemo()) return demoUploadAnswer(sessionId, text)
  return request(`/api/sessions/${sessionId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message: text })
  })
}

export function getSessionStatus(sessionId) {
  if (isDemo()) return Promise.resolve({ status: 'interviewing' })
  return request(`/api/sessions`).then(sessions => {
    const s = sessions.find(s => s.id === sessionId)
    return s || { status: 'unknown' }
  })
}

// ---------------------------------------------------------------------------
// Q&A
// ---------------------------------------------------------------------------

export function askQuestion(text) {
  if (isDemo()) return demoAskQuestion(text)
  return request('/api/ask', {
    method: 'POST',
    body: JSON.stringify({ question: text })
  })
}

export function getQaHistory(sessionId) {
  if (isDemo()) return Promise.resolve([])
  return request('/api/ask', {
    method: 'POST',
    body: JSON.stringify({ question: '' })
  }).catch(() => [])
}

// ---------------------------------------------------------------------------
// Slack Ingest (Admin)
// ---------------------------------------------------------------------------

export function ingestSlack(sessionId, text) {
  if (isDemo()) return Promise.resolve({ stored_chunks: 0 })
  return request(`/api/sessions/${sessionId}/slack`, {
    method: 'POST',
    body: JSON.stringify({ text })
  })
}
