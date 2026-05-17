import React, { useState, useCallback } from 'react'
import UploadZone from './components/UploadZone.jsx'
import AnalysisProgress from './components/AnalysisProgress.jsx'
import RiskDashboard from './components/RiskDashboard.jsx'
import SplashScreen from './components/SplashScreen.jsx'
import Onboarding from './components/Onboarding.jsx'

/** Application view states */
const VIEWS = { SPLASH: 'splash', ONBOARDING: 'onboarding', UPLOAD: 'upload', ANALYZING: 'analyzing', REPORT: 'report' }

/**
 * LexGuard One — Main Application Component
 * Manages view state transitions: Upload → Analysis → Report
 */
export default function App() {
  const [view, setView] = useState(VIEWS.SPLASH)
  const [clauseResults, setClauseResults] = useState([])
  const [report, setReport] = useState(null)
  const [progress, setProgress] = useState({ stage: '', percent: 0 })
  const [error, setError] = useState(null)

  /** Handle file upload and start SSE streaming analysis */
  const handleAnalyze = useCallback(async (file) => {
    setView(VIEWS.ANALYZING)
    setClauseResults([])
    setReport(null)
    setError(null)
    setProgress({ stage: 'Uploading Document', percent: 5 })

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData?.error?.message || 'Analysis failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            handleSSEEvent(event)
          } catch { /* skip malformed events */ }
        }
      }
    } catch (err) {
      setError(err.message)
      setView(VIEWS.UPLOAD)
    }
  }, [])

  /** Process incoming SSE events */
  const handleSSEEvent = useCallback((event) => {
    switch (event.type) {
      case 'progress':
        setProgress({ stage: event.stage, percent: event.progress_percent })
        break
      case 'clause_result':
        setClauseResults(prev => [...prev, event.clause_report])
        setProgress(prev => ({ ...prev, percent: event.progress_percent }))
        break
      case 'complete':
        setReport(event.report)
        setView(VIEWS.REPORT)
        break
      case 'error':
        setError(event.error?.message || 'Analysis failed')
        setView(VIEWS.UPLOAD)
        break
    }
  }, [])

  /** Reset to upload view */
  const handleReset = useCallback(() => {
    setView(VIEWS.UPLOAD)
    setClauseResults([])
    setReport(null)
    setError(null)
    setProgress({ stage: '', percent: 0 })
  }, [])

  return (
    <div className="min-h-screen bg-lexguard-bg">
      {view === VIEWS.SPLASH && (
        <SplashScreen onComplete={() => setView(VIEWS.ONBOARDING)} />
      )}
      
      {view === VIEWS.ONBOARDING && (
        <Onboarding onComplete={() => setView(VIEWS.UPLOAD)} />
      )}

      {/* Header */}
      <header className="border-b border-lexguard-border/50 bg-lexguard-surface/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <button onClick={handleReset} className="flex items-center gap-3 group" aria-label="Return to home">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-shadow">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">LexGuard One</h1>
              <p className="text-xs text-lexguard-muted">AI Contract Intelligence</p>
            </div>
          </button>
          {view === VIEWS.REPORT && (
            <button
              onClick={handleReset}
              className="px-4 py-2 rounded-lg bg-lexguard-surface-2 border border-lexguard-border text-sm text-lexguard-muted hover:text-lexguard-text hover:border-lexguard-accent transition-all"
            >
              Analyze Another
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8" role="main">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-risk-high/10 border border-risk-high/30 text-risk-high flex items-center gap-3" role="alert">
            <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {view === VIEWS.UPLOAD && (
          <UploadZone onAnalyze={handleAnalyze} />
        )}

        {view === VIEWS.ANALYZING && (
          <AnalysisProgress
            stage={progress.stage}
            percent={progress.percent}
            clauseResults={clauseResults}
          />
        )}

        {view === VIEWS.REPORT && report && (
          <RiskDashboard report={report} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-lexguard-border/30 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 text-center text-sm text-lexguard-muted">
          <p>LexGuard One v1.0.0 — Powered by Google Gemini &amp; Vertex AI</p>
          <p className="mt-1 text-xs opacity-60">Built for PromptWars × Scaler Hackathon 2026</p>
        </div>
      </footer>
    </div>
  )
}
