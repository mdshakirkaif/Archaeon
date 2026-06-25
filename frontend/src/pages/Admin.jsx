import { useState, useEffect } from 'react'
import { createSession, listSessions } from '../api'

export default function Admin() {
  const [activeTab, setActiveTab] = useState('pipelines')
  const [selectedSessionId, setSelectedSessionId] = useState(null)
  const [search, setSearch] = useState('')
  const [sessions, setSessions] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadSessions()
  }, [])

  function loadSessions() {
    listSessions()
      .then(data => setSessions(data))
      .catch(() => {})
  }

  async function handleRegister(e) {
    e.preventDefault()
    setError('')
    const form = e.currentTarget
    const data = new FormData(form)
    const name = data.get('name')
    const github = data.get('github')
    const token = data.get('githubToken')
    if (!name) return

    setSubmitting(true)
    try {
      const res = await createSession({
        engineer_name: name,
        github_username: github || '',
        github_token: token || ''
      })
      setSessions(prev => [res, ...prev])
      setSelectedSessionId(res.id)
      form.reset()
      setActiveTab('pipelines')
      window.location.href = `/interview/${res.id}`
    } catch (err) {
      console.error('createSession failed:', err)
      setError(`Failed to create session: ${err.message || 'Unknown error'}`)
    }
    setSubmitting(false)
  }

  const selectedSession = sessions.find(s => s.id === selectedSessionId)
  const filteredSessions = sessions.filter(s =>
    [s.engineer_name, s.github_username, s.status].some(f =>
      f && f.toLowerCase().includes(search.toLowerCase())
    )
  )

  const statusStyle = (status) => {
    if (status === 'completed') return { bg: '#d4edda', text: '#166534' }
    if (status === 'interviewing') return { bg: '#e0e7ff', text: '#3730a3' }
    if (status === 'pending') return { bg: '#fef3c7', text: '#92400e' }
    return { bg: '#f1f5f9', text: '#475569' }
  }

  return (
    <div style={styles.page}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '28px' }}>
        {['pipelines', 'register'].map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            style={{
              padding: '8px 20px', borderRadius: '8px', border: 'none', cursor: 'pointer',
              fontWeight: '600', fontSize: '13px',
              background: activeTab === t ? '#0f0f15' : '#fff',
              color: activeTab === t ? '#fff' : '#666',
              boxShadow: activeTab === t ? 'none' : '0 1px 3px rgba(0,0,0,0.04)',
              transition: 'all 0.15s ease'
            }}
          >{t === 'pipelines' ? 'Pipelines' : 'Register'}</button>
        ))}
      </div>

      {activeTab === 'pipelines' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={styles.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: '700' }}>Active Pipelines</h3>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button onClick={loadSessions} style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #ddd', background: '#fff', cursor: 'pointer', fontSize: '12px', fontWeight: '600', color: '#666' }}>Refresh</button>
                <input type="text" placeholder="Filter..." value={search}
                  onChange={e => setSearch(e.target.value)} style={styles.filterInput} />
              </div>
            </div>
            <div style={{ overflowX: 'auto' }}>
              {filteredSessions.length === 0 ? (
                <div style={{ padding: '40px 8px', color: '#888', textAlign: 'center', fontSize: '13px', lineHeight: '1.6' }}>
                  No pipelines yet.<br />Register a departing engineer to start.
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #eee', textAlign: 'left', color: '#888' }}>
                      <th style={{ padding: '10px 8px', fontWeight: '600' }}>Engineer</th>
                      <th style={{ padding: '10px 8px', fontWeight: '600' }}>GitHub</th>
                      <th style={{ padding: '10px 8px', fontWeight: '600' }}>Status</th>
                      <th style={{ padding: '10px 8px', fontWeight: '600' }}>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSessions.map(session => {
                      const isSelected = session.id === selectedSessionId
                      return (
                        <tr key={session.id} onClick={() => setSelectedSessionId(session.id)}
                          style={{
                            borderBottom: '1px solid #f0f0f0', cursor: 'pointer',
                            background: isSelected ? '#f8f8f7' : 'transparent',
                            transition: 'background 0.1s'
                          }}>
                          <td style={{ padding: '12px 8px' }}>
                            <div style={{ fontWeight: '600', color: '#1a1a1a' }}>{session.engineer_name}</div>
                          </td>
                          <td style={{ padding: '12px 8px', color: '#666' }}>{session.github_username || '—'}</td>
                          <td style={{ padding: '12px 8px' }}>
                            <span style={{ display: 'inline-block', fontSize: '11px', fontWeight: '600', padding: '3px 10px', borderRadius: '5px', ...statusStyle(session.status) }}>{session.status}</span>
                          </td>
                          <td style={{ padding: '12px 8px', color: '#888', fontSize: '12px' }}>
                            {session.created_at ? new Date(session.created_at).toLocaleString() : '—'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          <div style={styles.card}>
            {!selectedSession ? (
              <div style={{ padding: '40px 8px', color: '#888', textAlign: 'center', fontSize: '13px', lineHeight: '1.6' }}>
                Select a pipeline to view details.
              </div>
            ) : (
              <div>
                <div style={{ borderBottom: '1px solid #eee', paddingBottom: '16px', marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '15px', fontWeight: '700' }}>{selectedSession.engineer_name}</h4>
                  <p style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>GitHub: {selectedSession.github_username || '—'}</p>
                  <p style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>ID: <code>{selectedSession.id}</code></p>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <span style={{ display: 'inline-block', fontSize: '12px', fontWeight: '600', padding: '4px 12px', borderRadius: '5px', ...statusStyle(selectedSession.status) }}>{selectedSession.status}</span>
                  <a href={`/interview/${selectedSession.id}`} style={{ fontSize: '13px', fontWeight: '600', color: '#0f0f15', textDecoration: 'none' }}>Open Interview &rarr;</a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'register' && (
        <div style={styles.card}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px' }}>Register Engineer</h3>
          <p style={{ fontSize: '13px', color: '#888', marginBottom: '24px' }}>Create a knowledge capture pipeline for a departing engineer.</p>
          {error && (
            <div style={{ padding: '10px 14px', borderRadius: '8px', background: '#fef2f2', color: '#991b1b', fontSize: '13px', marginBottom: '16px' }}>{error}</div>
          )}
          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={styles.inputCol}>
                <label style={styles.label}>Name</label>
                <input type="text" name="name" required style={styles.input} placeholder="e.g. Abhay Jithendra" />
              </div>
              <div style={styles.inputCol}>
                <label style={styles.label}>GitHub Username</label>
                <input type="text" name="github" style={styles.input} placeholder="e.g. AbhayXplor" />
              </div>
            </div>
            <div style={styles.inputCol}>
              <label style={styles.label}>GitHub Token (optional — enables PR analysis)</label>
              <input type="password" name="githubToken" style={styles.input} placeholder="ghp_..." />
            </div>
            <button type="submit" disabled={submitting} style={{ ...styles.primaryBtn, opacity: submitting ? 0.6 : 1 }}>
              {submitting ? 'Creating...' : 'Register & Start Interview'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

const styles = {
  page: { maxWidth: '1100px', margin: '0 auto', padding: '32px 24px', width: '100%', flex: 1 },
  card: { background: '#fff', borderRadius: '12px', padding: '24px 28px', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' },
  inputCol: { display: 'flex', flexDirection: 'column', gap: '6px' },
  input: { padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', outline: 'none', background: '#fafafa' },
  filterInput: { padding: '8px 12px', border: '1px solid #eee', borderRadius: '6px', fontSize: '13px', outline: 'none', width: '180px', background: '#fafafa' },
  label: { fontSize: '12px', fontWeight: '600', color: '#666' },
  primaryBtn: { padding: '10px 24px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '14px', background: '#0f0f15', color: '#fff', alignSelf: 'flex-start' }
}
