import { useState } from 'react'
import InterviewConsole from './pages/InterviewConsole'
import QAScreen from './pages/QAScreen'
import Admin from './pages/Admin'

const navLinkStyle = (active) => ({
  fontSize: '13px', fontWeight: '600', padding: '6px 14px', borderRadius: '6px',
  background: active ? '#1a1a22' : 'transparent', color: active ? '#fff' : '#7a7a8a',
  transition: 'all 0.15s ease', textDecoration: 'none'
})

function DemoToggle() {
  const [demo, setDemo] = useState(localStorage.getItem('archaeon-demo') === 'true')
  function toggle() {
    const next = !demo
    setDemo(next)
    localStorage.setItem('archaeon-demo', next ? 'true' : 'false')
    window.location.reload()
  }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <div onClick={toggle} style={{
        width: '34px', height: '18px', borderRadius: '10px', cursor: 'pointer',
        position: 'relative', background: demo ? '#f59e0b' : '#2a2a36',
        transition: 'background 0.2s'
      }}>
        <div style={{
          width: '14px', height: '14px', borderRadius: '50%', background: '#fff',
          position: 'absolute', top: '2px', left: demo ? '18px' : '2px',
          transition: 'left 0.2s ease'
        }} />
      </div>
      <span style={{ fontSize: '10px', fontWeight: '700', color: demo ? '#f59e0b' : '#5a5a6a', letterSpacing: '0.5px', transition: 'color 0.2s' }}>
        {demo ? 'DEMO' : 'LIVE'}
      </span>
    </div>
  )
}

function TopNav() {
  const path = window.location.pathname
  return (
    <div style={{
      height: '48px', background: '#0f0f15', display: 'flex', alignItems: 'center',
      padding: '0 24px', justifyContent: 'space-between', flexShrink: 0,
      borderBottom: '1px solid #1a1a22'
    }}>
      <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff', letterSpacing: '-0.3px' }}>
        Archaeon
      </div>
      <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
        <a href="/admin" style={navLinkStyle(path === '/admin' || (!path.startsWith('/interview/') && path !== '/qa'))}>Admin</a>
        <a href="/interview/demo-1" style={navLinkStyle(path.startsWith('/interview/'))}>Interview</a>
        <a href="/qa" style={navLinkStyle(path === '/qa')}>Q&A</a>
      </div>
      <DemoToggle />
    </div>
  )
}

export default function App() {
  const [path] = useState(window.location.pathname)

  let page
  if (path.startsWith('/interview/')) {
    page = <InterviewConsole />
  } else if (path === '/qa') {
    page = <QAScreen />
  } else {
    page = <Admin />
  }

  return (
    <>
      <TopNav />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        {page}
      </div>
    </>
  )
}
