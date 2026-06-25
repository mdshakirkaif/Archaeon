import { useState, useEffect, useRef } from 'react'
import { getNextQuestion, uploadAnswer } from '../api'
import { getDemoTranscriptionPhrases, storeDemoAnswer, resetDemoQuestions } from '../demo'

export default function InterviewConsole() {
  const [question, setQuestion] = useState(null)
  const [index, setIndex] = useState(0)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [recording, setRecording] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')
  const [demo] = useState(localStorage.getItem('archaeon-demo') === 'true')
  const [transcript, setTranscript] = useState('')
  const [transcriptComplete, setTranscriptComplete] = useState('')
  const mediaRecorder = useRef(null)
  const chunks = useRef([])
  const transcriptTimer = useRef(null)
  const transcriptChunks = useRef([])
  const transcriptIdx = useRef(0)
  const sessionId = window.location.pathname.split('/interview/')[1]
  const didReset = useRef(false)
  const didLoad = useRef(false)
  const recognitionRef = useRef(null)
  const speechFinalRef = useRef('')

  useEffect(() => {
    if (demo && !didReset.current) {
      didReset.current = true
      resetDemoQuestions()
    }
    if (!didLoad.current) {
      didLoad.current = true
      loadQuestion()
    }
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
        recognitionRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, demo])

  function clearTranscript() {
    if (transcriptTimer.current) clearInterval(transcriptTimer.current)
    setTranscript('')
    setTranscriptComplete('')
    transcriptChunks.current = []
    transcriptIdx.current = 0
  }

  async function loadQuestion(retries = 8) {
    setLoading(true)
    setError('')
    clearTranscript()
    try {
      const res = await getNextQuestion(sessionId)
      if (res.done) {
        setDone(true)
        return
      }
      setQuestion(res.question)
      setIndex(res.index)
      setTotal(res.total)
    } catch (err) {
      console.error('loadQuestion failed:', err)
      if (err.message && err.message.includes('400') && retries > 0) {
        setLoading(true)
        await new Promise(r => setTimeout(r, 2000))
        return loadQuestion(retries - 1)
      }
      setError(`Failed to load question: ${err.message || 'Unknown error'}`)
    }
    setLoading(false)
  }

  function startSimulatedTranscription(questionText) {
    const phrases = getDemoTranscriptionPhrases(questionText)
    transcriptChunks.current = phrases
    transcriptIdx.current = 0
    setTranscript('')
    let words = []
    transcriptTimer.current = setInterval(() => {
      if (transcriptIdx.current >= phrases.length) {
        clearInterval(transcriptTimer.current)
        return
      }
      words = words.concat(phrases[transcriptIdx.current].split(' '))
      transcriptIdx.current++
      setTranscript(words.join(' '))
    }, 1800 + Math.random() * 1200)
  }

  async function startRecording() {
    chunks.current = []
    setError('')
    setTranscript('')
    setTranscriptComplete('')
    if (demo) {
      setRecording(true)
      startSimulatedTranscription(question)
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Speech recognition is not supported in this browser. Try Chrome.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data)
      }
      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop())
      }
      mediaRecorder.current = recorder
      recorder.start()

      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      speechFinalRef.current = ''
      recognition.onresult = (event) => {
        let interim = ''
        let final = speechFinalRef.current
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const text = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            final += (final ? ' ' : '') + text
            speechFinalRef.current = final
          } else {
            interim += text
          }
        }
        setTranscript(final + (interim ? ' ' + interim : ''))
      }
      recognition.onerror = (e) => {
        console.error('Speech recognition error:', e.error)
      }

      recognitionRef.current = recognition
      recognition.start()
      setRecording(true)
    } catch {
      setError('Microphone access denied.')
    }
  }

  function stopRecording() {
    if (demo) {
      if (transcriptTimer.current) clearInterval(transcriptTimer.current)
      setRecording(false)
      const full = transcript
      setTranscriptComplete(full)
      if (question) storeDemoAnswer(question, full)
      setTimeout(() => loadQuestion(), 600)
      return
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop()
    }
    setRecording(false)

    const finalText = speechFinalRef.current || transcript
    setTranscriptComplete(finalText)

    if (finalText.trim()) {
      setUploading(true)
      uploadAnswer(sessionId, finalText.trim())
        .then(() => loadQuestion())
        .catch((err) => {
          console.error('uploadAnswer failed:', err)
          setError(`Upload failed: ${err.message || 'Unknown error'}`)
        })
        .finally(() => setUploading(false))
    } else {
      loadQuestion()
    }
  }

  if (done) {
    return (
      <div style={styles.wrapper}>
        <Sidebar index={index} total={total} done />
        <div style={styles.main}>
          <div style={styles.doneCard}>
            <div style={styles.checkCircle}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: '600', color: '#1a1a1a', marginBottom: '8px' }}>Interview complete</h2>
            <p style={{ color: '#888', fontSize: '14px', lineHeight: '1.6' }}>All responses have been recorded.<br />Head over to Q&A to explore what was captured.</p>
            <a href="/qa" style={{
              marginTop: '24px', display: 'inline-flex', alignItems: 'center', gap: '8px',
              padding: '10px 24px', borderRadius: '8px', background: '#0f0f15', color: '#fff',
              fontSize: '14px', fontWeight: '600', textDecoration: 'none'
            }}>
              Go to Q&A
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.wrapper}>
      <Sidebar index={index} total={total} done={false} />
      <div style={styles.main}>
        <div style={styles.mainInner}>
          {loading && (
            <div style={{ color: '#888', fontSize: '14px' }}>Loading...</div>
          )}

          {error && (
            <div style={{ textAlign: 'center' }}>
              <p style={{ color: '#dc2626', fontSize: '14px', marginBottom: '16px' }}>{error}</p>
              <button onClick={loadQuestion} style={styles.retryBtn}>Retry</button>
            </div>
          )}

          {!loading && !error && question && (
            <div style={styles.questionContainer}>
              <div style={styles.progressBadge}>
                Q{index} of {total}
              </div>
              <div style={styles.questionText}>
                <span style={styles.questionAccent} />
                {question}
              </div>

              {(transcript || transcriptComplete) && (
                <div style={styles.transcriptCard}>
                  <div style={styles.transcriptCardInner}>
                    {transcriptComplete && (
                      <div style={styles.transcriptLabel}>Transcribed answer</div>
                    )}
                    {transcriptComplete || transcript}
                    {!transcriptComplete && recording && (
                      <span style={{ display: 'inline-block', width: '6px', height: '14px', background: '#dc2626', marginLeft: '4px', animation: 'blink 0.8s step-end infinite', verticalAlign: 'middle' }}></span>
                    )}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '48px' }}>
                {!recording && !uploading && (
                  <button onClick={startRecording} style={styles.recordBtn}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
                    Record answer
                  </button>
                )}
                {recording && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={styles.waveformGroup}>
                        {[12, 18, 10, 22, 8, 16, 14, 20].map((h, i) => (
                          <div key={i} style={{ width: '3px', height: `${h}px`, background: '#dc2626', borderRadius: '2px', animation: 'waveform 0.5s ease infinite alternate', animationDelay: `${i * 0.07}s` }}></div>
                        ))}
                      </div>
                      <span style={{ color: '#dc2626', fontSize: '14px', fontWeight: '600' }}>Recording...</span>
                    </div>
                    <button onClick={stopRecording} style={styles.stopBtn}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
                      Stop & send
                    </button>
                  </div>
                )}
                {uploading && (
                  <div style={styles.processing}>
                    <div style={styles.spinner}></div>
                    Saving answer...
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Sidebar({ index, total, done }) {
  return (
    <div style={styles.sidebar}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '32px' }}>
        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: done ? '#10b981' : '#f59e0b' }} />
        <div style={{ fontSize: '12px', fontWeight: '600', color: '#7a7a8a', letterSpacing: '0.3px' }}>
          {done ? 'COMPLETED' : 'IN PROGRESS'}
        </div>
      </div>
      {!done && total > 0 && (
        <div>
          <div style={{ height: '4px', background: '#1e1e2a', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${((index - 1) / total) * 100}%`, background: '#f5f5f4', borderRadius: '4px', transition: 'width 0.4s ease' }}></div>
          </div>
          <div style={{ marginTop: '12px' }}>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#fff', letterSpacing: '-0.5px' }}>{index - 1}/{total}</div>
            <div style={{ fontSize: '12px', color: '#5a5a6a', marginTop: '2px' }}>questions answered</div>
          </div>
        </div>
      )}
    </div>
  )
}

const styles = {
  wrapper: {
    display: 'flex', flex: 1, background: '#f5f5f4', minHeight: 0
  },
  sidebar: {
    width: '220px', background: '#0f0f15', color: '#fff',
    display: 'flex', flexDirection: 'column', padding: '28px 20px', flexShrink: 0
  },
  main: {
    flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', padding: '40px', position: 'relative',
    background: 'radial-gradient(ellipse at 50% 40%, rgba(15,15,21,0.03) 0%, transparent 60%)'
  },
  mainInner: {
    width: '100%', maxWidth: '680px', display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center', minHeight: '400px'
  },
  questionContainer: {
    width: '100%', animation: 'fadeIn 0.3s ease'
  },
  progressBadge: {
    display: 'inline-flex', alignItems: 'center', fontSize: '12px', fontWeight: '700',
    color: '#fff', background: '#0f0f15', padding: '4px 12px', borderRadius: '6px',
    marginBottom: '20px', letterSpacing: '0.3px'
  },
  questionText: {
    fontSize: '26px', lineHeight: '1.5', fontWeight: '500', color: '#1a1a1a',
    letterSpacing: '-0.2px', display: 'flex', gap: '16px', position: 'relative',
    paddingLeft: '20px'
  },
  questionAccent: {
    position: 'absolute', left: '0', top: '4px', bottom: '4px', width: '3px',
    background: '#0f0f15', borderRadius: '2px', flexShrink: 0
  },
  transcriptCard: {
    marginTop: '28px', animation: 'slideUp 0.25s ease'
  },
  transcriptCardInner: {
    padding: '16px 20px', background: '#fff', borderRadius: '10px',
    border: '1px solid #e0e0e0', fontSize: '14px', lineHeight: '1.7', color: '#444',
    boxShadow: '0 2px 8px rgba(0,0,0,0.04)'
  },
  transcriptLabel: {
    fontSize: '11px', fontWeight: '600', color: '#166534', marginBottom: '8px',
    textTransform: 'uppercase', letterSpacing: '0.5px',
    borderBottom: '1px solid #e8e8e6', paddingBottom: '8px'
  },
  recordBtn: {
    display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 32px',
    borderRadius: '10px', fontSize: '15px', fontWeight: '600',
    background: '#0f0f15', color: '#fff', border: 'none', cursor: 'pointer',
    transition: 'all 0.15s ease', boxShadow: '0 2px 8px rgba(15,15,21,0.15)'
  },
  stopBtn: {
    display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 32px',
    borderRadius: '10px', fontSize: '15px', fontWeight: '600',
    background: '#dc2626', color: '#fff', border: 'none', cursor: 'pointer',
    transition: 'all 0.15s ease', animation: 'recordPulse 1.5s infinite'
  },
  waveformGroup: {
    display: 'flex', gap: '3px', alignItems: 'center', height: '24px'
  },
  processing: {
    display: 'flex', alignItems: 'center', gap: '12px', color: '#888',
    fontSize: '14px', fontWeight: '500'
  },
  spinner: {
    width: '18px', height: '18px', border: '2px solid #e0e0e0',
    borderTop: '2px solid #0f0f15', borderRadius: '50%',
    animation: 'spin 0.8s linear infinite'
  },
  retryBtn: {
    padding: '10px 20px', borderRadius: '8px', background: '#0f0f15',
    color: '#fff', fontSize: '14px', fontWeight: '600', border: 'none', cursor: 'pointer'
  },
  doneCard: {
    textAlign: 'center', animation: 'slideUp 0.35s ease',
    background: '#fff', padding: '48px', borderRadius: '16px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.06)'
  },
  checkCircle: {
    width: '56px', height: '56px', borderRadius: '50%',
    background: '#d4edda', color: '#166534',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    margin: '0 auto 24px'
  }
}
