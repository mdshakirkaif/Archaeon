import {
  demoGetNextQuestion, demoUploadAnswer, demoAskQuestion
} from './demo'

function isDemo() {
  return localStorage.getItem('archaeon-demo') === 'true'
}

const BASE = import.meta.env.VITE_API_URL || ''

// ---------------------------------------------------------------------------
// Response shape mapping
// ---------------------------------------------------------------------------
// Backend ChatResponse = { reply: string, done: boolean }
// Frontend expects     = { question: string, index: number, total: number, done: boolean }
//
// Backend AskResponse  = { answer: string, sources: string[] }
// Frontend expects     = { answer: string, citations: Array<{source, snippet}> }
//
// These mappings bridge the gap so both sides can evolve independently.

const TOTAL_QUESTIONS = 5
const _sessionIndex = {}

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

  if (!_sessionIndex[sessionId]) _sessionIndex[sessionId] = 0

  return request(`/api/sessions/${sessionId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message: '' })
  }).then(res => {
    if (res.done) return { done: true }
    _sessionIndex[sessionId]++
    return {
      question: res.reply,
      index: _sessionIndex[sessionId],
      total: TOTAL_QUESTIONS,
      done: false
    }
  })
}

export function uploadAnswer(sessionId, text) {
  if (isDemo()) return demoUploadAnswer(sessionId, text)
  return request(`/api/sessions/${sessionId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message: text })
  }).then(res => {
    if (res.done) return { done: true }
    return { ok: true }
  })
}

export function getSessionStatus(sessionId) {
  if (isDemo()) return Promise.resolve({ status: 'interviewing' })
  return request('/api/sessions').then(sessions => {
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
  }).then(res => ({
    answer: res.answer,
    citations: (res.sources || []).map(s =>
      typeof s === 'string' ? { source: s, snippet: '' } : s
    )
  }))
}

export function getQaHistory() {
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

export function getSessionRepos(sessionId) {
  if (isDemo()) return Promise.resolve([
    { name: 'repo-1', description: 'Demo repo', language: 'Python', stargazers_count: 10, topics: ['demo'] }
  ])
  return request(`/api/sessions/${sessionId}/repos`)
}

export function startInterview(sessionId, selectedRepos) {
  return request(`/api/sessions/${sessionId}/start-interview`, {
    method: 'POST',
    body: JSON.stringify({ selected_repos: selectedRepos })
  })
}
