import { useState } from 'react'

export default function Admin() {
  const [activeTab, setActiveTab] = useState('pipelines')
  const [selectedSessionId, setSelectedSessionId] = useState(null)
  const [search, setSearch] = useState('')
  const [sessions, setSessions] = useState([])

  function handleRegister(e) {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    const name = data.get('name')
    const role = data.get('role')
    const team = data.get('team')
    const github = data.get('github')
    const logs = data.get('slackLogs')
    if (!name || !role || !team) return
    const newId = `ARCH-0${sessions.length + 1}`
    setSessions(prev => [{
      id: newId, name, role, team, github: github || 'pending',
      status: logs ? 'Extracting Facts' : 'Awaiting Seeding',
      progress: logs ? 50 : 0, risks: []
    }, ...prev])
    setSelectedSessionId(newId)
    e.currentTarget.reset()
    setActiveTab('pipelines')
  }

  const selectedSession = sessions.find(s => s.id === selectedSessionId)
  const filteredSessions = sessions.filter(s =>
    [s.name, s.role, s.team].some(f => f.toLowerCase().includes(search.toLowerCase()))
  )

  const statusStyle = (status) => {
    if (status === 'Synced to DB') return { bg: '#d4edda', text: '#166534' }
    if (status === 'Ready for Audit') return { bg: '#fef3c7', text: '#92400e' }
    if (status === 'Extracting Facts') return { bg: '#e0e7ff', text: '#3730a3' }
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
              <input type="text" placeholder="Filter..." value={search}
                onChange={e => setSearch(e.target.value)} style={styles.filterInput} />
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
                      <th style={{ padding: '10px 8px', fontWeight: '600' }}>Team</th>
                      <th style={{ padding: '10px 8px', fontWeight: '600' }}>Progress</th>
                      <th style={{ padding: '10px 8px', fontWeight: '600' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSessions.map(session => {
                      const isSelected = session.id === selectedSessionId
                      const sc = statusStyle(session.status)
                      return (
                        <tr key={session.id} onClick={() => setSelectedSessionId(session.id)}
                          style={{
                            borderBottom: '1px solid #f0f0f0', cursor: 'pointer',
                            background: isSelected ? '#f8f8f7' : 'transparent',
                            transition: 'background 0.1s'
                          }}>
                          <td style={{ padding: '12px 8px' }}>
                            <div style={{ fontWeight: '600', color: '#1a1a1a' }}>{session.name}</div>
                            <div style={{ fontSize: '11px', color: '#888' }}>{session.role}</div>
                          </td>
                          <td style={{ padding: '12px 8px', color: '#666' }}>{session.team}</td>
                          <td style={{ padding: '12px 8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <div style={{ width: '60px', height: '4px', background: '#eee', borderRadius: '2px', overflow: 'hidden' }}>
                                <div style={{ width: `${session.progress}%`, height: '100%', background: '#0f0f15', borderRadius: '2px', transition: 'width 0.3s' }} />
                              </div>
                              <span style={{ fontWeight: '600', fontSize: '12px', color: '#666' }}>{session.progress}%</span>
                            </div>
                          </td>
                          <td style={{ padding: '12px 8px' }}>
                            <span style={{ display: 'inline-block', fontSize: '11px', fontWeight: '600', padding: '3px 10px', borderRadius: '5px', background: sc.bg, color: sc.text }}>{session.status}</span>
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
                  <h4 style={{ fontSize: '15px', fontWeight: '700' }}>{selectedSession.name}</h4>
                  <p style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>{selectedSession.role} &bull; {selectedSession.team}</p>
                  <p style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>GitHub: {selectedSession.github}</p>
                </div>
                <div>
                  <h5 style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: '#888', letterSpacing: '0.5px', marginBottom: '8px' }}>Status</h5>
                  <span style={{ display: 'inline-block', fontSize: '12px', fontWeight: '600', padding: '4px 12px', borderRadius: '5px', ...statusStyle(selectedSession.status) }}>{selectedSession.status}</span>
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
          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={styles.inputCol}>
                <label style={styles.label}>Name</label>
                <input type="text" name="name" required style={styles.input} />
              </div>
              <div style={styles.inputCol}>
                <label style={styles.label}>Title</label>
                <input type="text" name="role" required style={styles.input} />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={styles.inputCol}>
                <label style={styles.label}>Team</label>
                <input type="text" name="team" required style={styles.input} />
              </div>
              <div style={styles.inputCol}>
                <label style={styles.label}>GitHub</label>
                <input type="text" name="github" style={styles.input} />
              </div>
            </div>
            <div style={styles.inputCol}>
              <label style={styles.label}>Slack logs (optional)</label>
              <textarea rows={5} name="slackLogs" style={styles.textarea} />
            </div>
            <button type="submit" style={styles.primaryBtn}>Register</button>
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
  textarea: { padding: '12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '13px', resize: 'vertical', outline: 'none', background: '#fafafa' },
  label: { fontSize: '12px', fontWeight: '600', color: '#666' },
  primaryBtn: { padding: '10px 24px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '14px', background: '#0f0f15', color: '#fff', alignSelf: 'flex-start' }
}
