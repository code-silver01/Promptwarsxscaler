import React from 'react'
import PropTypes from 'prop-types'

const STAGES = [
  'Extracting Clauses',
  'Classifying Clauses',
  'Adversarial Analysis',
  'Benchmark Comparison',
  'Detecting Contradictions',
  'Calculating Risk Score',
  'Generating Report',
]

/** Severity badge component */
function SeverityBadge({ severity }) {
  const config = {
    HIGH: { bg: 'bg-risk-high/15', text: 'text-risk-high', icon: '⚠️', label: 'High Risk' },
    MEDIUM: { bg: 'bg-risk-medium/15', text: 'text-risk-medium', icon: '⚡', label: 'Medium Risk' },
    LOW: { bg: 'bg-risk-low/15', text: 'text-risk-low', icon: '✓', label: 'Low Risk' },
  }
  const s = config[severity] || config.LOW
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${s.bg} ${s.text}`} role="status" aria-label={s.label}>
      <span aria-hidden="true">{s.icon}</span> {severity}
    </span>
  )
}

/**
 * AnalysisProgress — Real-time streaming progress indicator.
 * Shows pipeline stages and clause cards as they arrive.
 *
 * @param {Object} props
 * @param {string} props.stage - Current processing stage
 * @param {number} props.percent - Progress percentage (0-100)
 * @param {Array} props.clauseResults - Clause results received so far
 */
export default function AnalysisProgress({ stage, percent, clauseResults }) {
  const activeStageIndex = STAGES.findIndex(s => stage?.includes(s.split(' ')[0]))

  return (
    <section className="animate-fade-in-up max-w-4xl mx-auto" aria-label="Analysis in progress" aria-live="polite">
      {/* Progress header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-lexguard-text mb-2">Analyzing Your Contract</h2>
        <p className="text-lexguard-muted">{stage || 'Initializing...'}</p>
      </div>

      {/* Progress bar */}
      <div className="glass-card p-6 mb-8">
        <div className="flex justify-between text-sm text-lexguard-muted mb-3">
          <span>Progress</span>
          <span className="font-mono">{Math.round(percent || 0)}%</span>
        </div>
        <div className="h-3 bg-lexguard-surface rounded-full overflow-hidden" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100} aria-label={`Analysis ${Math.round(percent)}% complete`}>
          <div className="h-full progress-bar-fill rounded-full transition-all duration-500 ease-out" style={{ width: `${percent || 0}%` }} />
        </div>

        {/* Stage indicators */}
        <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {STAGES.slice(0, 4).map((s, idx) => {
            const isActive = activeStageIndex === idx
            const isDone = activeStageIndex > idx
            return (
              <div key={s} className={`flex items-center gap-2 text-xs rounded-lg px-3 py-2 transition-colors ${isActive ? 'bg-lexguard-accent/10 text-lexguard-accent' : isDone ? 'text-green-400' : 'text-lexguard-muted'}`}>
                {isDone ? (
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                ) : isActive ? (
                  <div className="w-4 h-4 shrink-0 border-2 border-lexguard-accent border-t-transparent rounded-full animate-spin" aria-hidden="true" />
                ) : (
                  <div className="w-4 h-4 shrink-0 rounded-full border border-lexguard-border" aria-hidden="true" />
                )}
                <span className="truncate">{s}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Streaming clause cards */}
      {clauseResults.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-lexguard-text mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-lexguard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Clauses Found ({clauseResults.length})
          </h3>
          <div className="space-y-3">
            {clauseResults.map((cr, idx) => (
              <div key={idx} className="animate-slide-in glass-card p-4 flex items-start gap-4" style={{ animationDelay: `${idx * 50}ms` }}>
                <div className="shrink-0 w-10 h-10 rounded-lg bg-lexguard-surface-2 flex items-center justify-center text-sm font-mono text-lexguard-muted">
                  {idx + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-lexguard-text line-clamp-2">{cr.clause?.text?.slice(0, 150)}...</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {cr.category && (
                      <span className="px-2 py-0.5 rounded-md bg-lexguard-accent/10 text-lexguard-accent text-xs font-medium">
                        {cr.category}
                      </span>
                    )}
                    {cr.severity && <SeverityBadge severity={cr.severity} />}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

AnalysisProgress.propTypes = {
  stage: PropTypes.string,
  percent: PropTypes.number,
  clauseResults: PropTypes.arrayOf(PropTypes.object),
}
