import React, { useState, useCallback } from 'react'
import UploadZone from './components/UploadZone.jsx'
import AnalysisProgress from './components/AnalysisProgress.jsx'
import RiskDashboard from './components/RiskDashboard.jsx'
import SplashScreen from './components/SplashScreen.jsx'
import Onboarding from './components/Onboarding.jsx'
import AgentDebate from './components/AgentDebate.jsx'

/** Application view states */
const VIEWS = { SPLASH: 'splash', ONBOARDING: 'onboarding', UPLOAD: 'upload', ANALYZING: 'analyzing', REPORT: 'report' }

/**
 * LexGuard One — Enhanced Main Application Component
 * Manages view state transitions with multi-agent debate visualization
 */
export default function App() {
  const [view, setView] = useState(VIEWS.SPLASH)
  const [clauseResults, setClauseResults] = useState([])
  const [report, setReport] = useState(null)
  const [progress, setProgress] = useState({ stage: '', percent: 0 })
  const [error, setError] = useState(null)
  const [userProfile, setUserProfile] = useState(null)
  const [activeDebate, setActiveDebate] = useState(null)

  /** Handle file upload and start enhanced SSE streaming analysis */
  const handleAnalyze = useCallback(async (file) => {
    setView(VIEWS.ANALYZING)
    setClauseResults([])
    setReport(null)
    setError(null)
    setProgress({ stage: 'Uploading Document', percent: 5 })
    setActiveDebate(null)

    const formData = new FormData()
    formData.append('file', file)

    // Prepare headers with user profile
    const headers = {}
    if (userProfile) {
      headers['X-User-Profile'] = JSON.stringify(userProfile)
    }

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
        headers: headers,
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
  }, [userProfile])

  /** Process incoming SSE events with debate data */
  const handleSSEEvent = useCallback((event) => {
    switch (event.type) {
      case 'progress':
        setProgress({ stage: event.stage, percent: event.progress_percent })
        break
      case 'clause_result':
        const clauseReport = event.clause_report
        setClauseResults(prev => [...prev, clauseReport])
        setProgress(prev => ({ ...prev, percent: event.progress_percent }))
        
        // If this clause has debate data, set it as active for visualization
        if (clauseReport.debate_data && clauseReport.severity === 'HIGH') {
          setActiveDebate({
            clauseId: clauseReport.clause.id,
            debateData: clauseReport.debate_data
          })
        }
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

  /** Handle onboarding completion */
  const handleOnboardingComplete = useCallback((profile) => {
    setUserProfile(profile)
    setView(VIEWS.UPLOAD)
  }, [])

  /** Reset to upload view */
  const handleReset = useCallback(() => {
    setView(VIEWS.UPLOAD)
    setClauseResults([])
    setReport(null)
    setError(null)
    setProgress({ stage: '', percent: 0 })
    setActiveDebate(null)
  }, [])

  return (
    <div className="min-h-screen bg-lexguard-bg">
      {view === VIEWS.SPLASH && (
        <SplashScreen onComplete={() => setView(VIEWS.ONBOARDING)} />
      )}
      
      {view === VIEWS.ONBOARDING && (
        <Onboarding onComplete={handleOnboardingComplete} />
      )}

      {view !== VIEWS.SPLASH && view !== VIEWS.ONBOARDING && (
        <>
          {/* Enhanced Header with User Info */}
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

              {/* User Profile Display */}
              {userProfile && (
                <div className="hidden md:flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm font-medium text-lexguard-text">
                      Welcome, {userProfile.name}
                    </p>
                    <p className="text-xs text-lexguard-muted">
                      {userProfile.occupation} • {userProfile.experience}
                    </p>
                  </div>
                  <div className="w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {userProfile.name?.charAt(0)?.toUpperCase()}
                    </span>
                  </div>
                </div>
              )}

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
              <div className="space-y-8">
                <UploadZone onAnalyze={handleAnalyze} />
                
                {/* Personalization Notice */}
                {userProfile && (
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-6 border border-indigo-200 dark:border-indigo-800">
                    <div className="flex items-start space-x-4">
                      <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="font-semibold text-lexguard-text mb-2">
                          Analysis Personalized for You
                        </h3>
                        <p className="text-sm text-lexguard-muted mb-3">
                          Your contract analysis will be tailored based on your profile as a {userProfile.occupation} 
                          with {userProfile.experience} experience in the {userProfile.industry} industry.
                        </p>
                        <div className="flex flex-wrap gap-2">
                          <span className="px-3 py-1 bg-indigo-100 dark:bg-indigo-800/30 text-indigo-800 dark:text-indigo-200 text-xs rounded-full">
                            {userProfile.riskTolerance} Risk Tolerance
                          </span>
                          <span className="px-3 py-1 bg-purple-100 dark:bg-purple-800/30 text-purple-800 dark:text-purple-200 text-xs rounded-full">
                            {userProfile.companySize}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {view === VIEWS.ANALYZING && (
              <div className="space-y-8">
                <AnalysisProgress 
                  progress={progress} 
                  clauseResults={clauseResults}
                  userProfile={userProfile}
                />
                
                {/* Live Agent Debate Visualization */}
                {activeDebate && (
                  <div className="mt-8">
                    <div className="mb-4">
                      <h2 className="text-2xl font-bold text-lexguard-text mb-2">
                        Live Agent Debate
                      </h2>
                      <p className="text-lexguard-muted">
                        Watch our AI agents debate the risks and protections in real-time
                      </p>
                    </div>
                    <AgentDebate 
                      clauseId={activeDebate.clauseId}
                      debateData={activeDebate.debateData}
                      isActive={true}
                    />
                  </div>
                )}

                {/* Clause Results Stream */}
                {clauseResults.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-lg font-semibold text-lexguard-text mb-4">
                      Analysis Results ({clauseResults.length} clauses processed)
                    </h3>
                    <div className="space-y-4">
                      {clauseResults.slice(-3).map((result, idx) => (
                        <div key={idx} className="bg-lexguard-surface rounded-lg p-4 border border-lexguard-border">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-medium text-lexguard-text">
                              {result.clause?.section || 'General'}
                            </h4>
                            {result.severity && (
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                result.severity === 'HIGH' 
                                  ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200'
                                  : result.severity === 'MEDIUM'
                                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200'
                                  : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
                              }`}>
                                {result.severity} RISK
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-lexguard-muted line-clamp-2">
                            {result.plain_english || result.clause?.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {view === VIEWS.REPORT && (
              <div className="space-y-8">
                <RiskDashboard 
                  report={report} 
                  clauseResults={clauseResults}
                  userProfile={userProfile}
                />
                
                {/* Enhanced Clause Details with Debate Data */}
                <div className="space-y-6">
                  {clauseResults
                    .filter(result => result.debate_data)
                    .map((result, idx) => (
                      <AgentDebate 
                        key={result.clause?.id || idx}
                        clauseId={result.clause?.id}
                        debateData={result.debate_data}
                        isActive={false}
                      />
                    ))}
                </div>
              </div>
            )}
          </main>
        </>
      )}
    </div>
  )
}
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
