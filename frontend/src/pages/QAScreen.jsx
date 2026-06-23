import { useState, useEffect, useRef, useCallback } from 'react'
import { askQuestion } from '../api'
import { getDemoContext } from '../demo'

const STORAGE_KEY = 'archaeon-conversations'
const ACTIVE_KEY = 'archaeon-active-conversation'

function loadConversations() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}
function saveConversations(convs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convs))
}
function loadActiveId() {
  return localStorage.getItem(ACTIVE_KEY) || null
}
function saveActiveId(id) {
  if (id) localStorage.setItem(ACTIVE_KEY, id)
  else localStorage.removeItem(ACTIVE_KEY)
}
function generateId() {
  return 'conv_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6)
}
function truncate(str, len = 50) {
  if (!str) return 'New conversation'
  return str.length > len ? str.slice(0, len) + '...' : str
}
function formatTime(ts) {
  const d = new Date(ts), now = new Date(), diff = now - d
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago'
  if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago'
  return d.toLocaleDateString()
}

const hoverStyles = `
  .conv-item:hover .delete-btn { opacity: 1 !important; }
  .conv-item:hover { background: #1a1a22 !important; }
  .qa-input:focus { border-color: #0f0f15 !important; background: #fff !important; }
`

export default function QAScreen() {
  const [demo] = useState(localStorage.getItem('archaeon-demo') === 'true')
  const [demoContextCount, setDemoContextCount] = useState(0)
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const listRef = useRef(null)
  const bottomRef = useRef(null)

  const activeConv = conversations.find(c => c.id === activeId) || null

  useEffect(() => {
    if (demo) {
      const ctx = getDemoContext()
      setDemoContextCount(ctx.length)
    }
  }, [demo])

  useEffect(() => {
    const style = document.createElement('style')
    style.textContent = hoverStyles
    document.head.appendChild(style)
    return () => style.remove()
  }, [])

  useEffect(() => {
    setConversations(loadConversations())
    setActiveId(loadActiveId())
  }, [])

  useEffect(() => { saveConversations(conversations) }, [conversations])
  useEffect(() => { saveActiveId(activeId) }, [activeId])

  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: 'smooth' })
  }, [activeConv?.messages, loading])

  function newConversation() {
    const id = generateId()
    setConversations(prev => [{ id, title: 'New conversation', messages: [], createdAt: Date.now() }, ...prev])
    setActiveId(id)
  }

  function deleteConversation(id, e) {
    e.stopPropagation()
    setConversations(prev => {
      const filtered = prev.filter(c => c.id !== id)
      if (activeId === id) setActiveId(filtered.length > 0 ? filtered[0].id : null)
      return filtered
    })
  }

  const handleAsk = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return
    let convId = activeId
    if (!convId) {
      const id = generateId()
      setConversations(prev => [{ id, title: truncate(text, 60), messages: [], createdAt: Date.now() }, ...prev])
      setActiveId(id)
      convId = id
    } else {
      const conv = conversations.find(c => c.id === convId)
      if (conv && conv.messages.length === 0) {
        setConversations(prev => prev.map(c => c.id === convId ? { ...c, title: truncate(text, 60) } : c))
      }
    }
    setInput('')
    setLoading(true)
    setConversations(prev => prev.map(c => c.id !== convId ? c : { ...c, messages: [...c.messages, { id: Date.now(), role: 'user', text }] }))
    try {
      const res = await askQuestion(text)
      setConversations(prev => prev.map(c => c.id !== convId ? c : { ...c, messages: [...c.messages, { id: Date.now() + 1, role: 'assistant', text: res.answer, citations: res.citations || [] }] }))
    } catch {
      setConversations(prev => prev.map(c => c.id !== convId ? c : { ...c, messages: [...c.messages, { id: Date.now() + 1, role: 'assistant', text: 'Could not retrieve an answer.', citations: [] }] }))
    }
    setLoading(false)
  }, [input, loading, activeId, conversations])

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk() }
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.sidebar}>
        <button onClick={newConversation} style={styles.newChatBtn}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          New chat
        </button>
        <div style={styles.convList}>
          {conversations.map(conv => (
            <div key={conv.id} onClick={() => setActiveId(conv.id)} className="conv-item"
              style={{ ...styles.convItem, background: conv.id === activeId ? '#1a1a22' : 'transparent' }}>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div style={styles.convTitle}>{conv.title}</div>
                <div style={styles.convTime}>{formatTime(conv.createdAt)}</div>
              </div>
              <button onClick={(e) => deleteConversation(conv.id, e)} className="delete-btn" style={styles.deleteBtn} title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          ))}
        </div>
      </div>

      <div style={styles.chatArea}>
        <div ref={listRef} style={styles.messageList}>
          <div style={{ maxWidth: '720px', margin: '0 auto', width: '100%', display: 'flex', flexDirection: 'column', minHeight: '100%', paddingBottom: '24px' }}>
            {!activeConv || activeConv.messages.length === 0 ? (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                {demo && demoContextCount > 0 && (
                  <div style={{
                    background: '#f8f8f7', border: '1px solid #e0e0e0', borderRadius: '10px',
                    padding: '12px 16px', marginBottom: '32px', fontSize: '13px', color: '#666',
                    display: 'flex', alignItems: 'center', gap: '8px', maxWidth: '400px'
                  }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    {demoContextCount} answers from interview available. Try asking about auth, billing, or deployment.
                  </div>
                )}
                <div style={{
                  width: '64px', height: '64px', borderRadius: '16px', background: '#0f0f15',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px'
                }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                </div>
                <div style={{ fontSize: '15px', fontWeight: '600', color: '#1a1a1a', marginBottom: '4px' }}>Ask anything</div>
                <div style={{ fontSize: '13px', color: '#888' }}>Knowledge captured from engineer interviews.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingTop: '24px' }}>
                {activeConv.messages.map((msg, i) => (
                  <div key={msg.id} className="message-enter" style={{ animationDelay: `${i * 0.03}s` }}>
                    <div style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                      <div style={{
                        maxWidth: '76%', padding: '12px 18px',
                        borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                        background: msg.role === 'user' ? '#0f0f15' : '#fff',
                        color: msg.role === 'user' ? '#fff' : '#1a1a1a',
                        fontSize: '14px', lineHeight: '1.65',
                        boxShadow: msg.role === 'user' ? '0 2px 8px rgba(15,15,21,0.15)' : '0 1px 4px rgba(0,0,0,0.06)',
                        border: msg.role === 'assistant' ? '1px solid #e8e8e6' : 'none'
                      }}>
                        {msg.text}
                      </div>
                    </div>
                    {msg.citations && msg.citations.length > 0 && (
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px', paddingLeft: '4px' }}>
                        {msg.citations.map((c, i) => (
                          <div key={i} style={styles.citation}>
                            <div style={{ fontWeight: '600', fontSize: '11px', color: '#0f0f15', marginBottom: '2px' }}>{c.source}</div>
                            <div style={{ fontSize: '11px', color: '#888', lineHeight: '1.4' }}>{c.snippet}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="message-enter" style={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <div style={{ padding: '14px 18px', background: '#fff', borderRadius: '16px 16px 16px 4px', boxShadow: '0 1px 4px rgba(0,0,0,0.06)', border: '1px solid #e8e8e6' }}>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        {[0, 1, 2].map(i => (
                          <div key={i} style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#d0d0d0', animation: 'pulse 1.2s infinite', animationDelay: `${i * 0.2}s` }}></div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            )}
          </div>
        </div>

        <div style={styles.inputBar}>
          <div style={{ maxWidth: '720px', margin: '0 auto', width: '100%', display: 'flex', gap: '10px' }}>
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
              disabled={loading} placeholder="Type a message..." className="qa-input" style={styles.input} />
            <button onClick={handleAsk} disabled={loading || !input.trim()} style={{
              ...styles.askBtn,
              background: loading || !input.trim() ? '#d0d0d0' : '#0f0f15',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              boxShadow: loading || !input.trim() ? 'none' : '0 2px 6px rgba(15,15,21,0.15)'
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </div>
          <div style={{ textAlign: 'center', fontSize: '11px', color: '#b0b0b0', marginTop: '8px' }}>Answers sourced from engineer interviews and codebase data.</div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  wrapper: { display: 'flex', flex: 1, background: '#f5f5f4', minHeight: 0 },
  sidebar: { width: '280px', background: '#0f0f15', color: '#fff', display: 'flex', flexDirection: 'column', flexShrink: 0 },
  newChatBtn: {
    display: 'flex', alignItems: 'center', gap: '10px', margin: '14px', padding: '11px 16px',
    borderRadius: '10px', background: 'transparent', border: '1px solid #2a2a36',
    color: '#d0d0d0', fontSize: '13px', fontWeight: '600', cursor: 'pointer',
    transition: 'all 0.15s ease'
  },
  convList: { flex: 1, overflowY: 'auto', padding: '4px 8px' },
  convItem: { display: 'flex', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', cursor: 'pointer', marginBottom: '2px', transition: 'background 0.15s ease' },
  convTitle: { fontSize: '13px', fontWeight: '500', color: '#d0d0d0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '2px' },
  convTime: { fontSize: '11px', color: '#5a5a6a' },
  deleteBtn: { background: 'none', border: 'none', color: '#5a5a6a', cursor: 'pointer', padding: '4px', borderRadius: '4px', opacity: 0, transition: 'opacity 0.15s ease', flexShrink: 0 },
  chatArea: { flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 },
  messageList: { flex: 1, overflowY: 'auto', display: 'flex', justifyContent: 'center', padding: '0 40px' },
  inputBar: { borderTop: '1px solid #e0e0e0', background: '#fff', padding: '16px 40px 12px' },
  input: {
    flex: 1, padding: '12px 16px', borderRadius: '10px', border: '1px solid #e0e0e0',
    fontSize: '14px', outline: 'none', background: '#f8f8f8',
    transition: 'border-color 0.15s ease, background 0.15s ease', boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.04)'
  },
  askBtn: { display: 'flex', alignItems: 'center', justifyContent: 'center', width: '44px', height: '44px', borderRadius: '10px', color: '#fff', border: 'none', cursor: 'pointer', flexShrink: 0, transition: 'all 0.15s ease' },
  citation: { fontSize: '12px', background: '#fff', border: '1px solid #e8e8e6', borderRadius: '8px', padding: '8px 12px', maxWidth: '280px', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }
}
