import React from 'react'
import PropTypes from 'prop-types'
import ClauseCard from './ClauseCard.jsx'
import CategoryHeatmap from './CategoryHeatmap.jsx'

/** Risk tier badge with color + icon */
function RiskTierBadge({ tier }) {
  const cfg = {
    'Low Risk': { bg: 'bg-risk-low/15 border-risk-low/30', text: 'text-risk-low', icon: '✅' },
    'Moderate Risk': { bg: 'bg-risk-medium/15 border-risk-medium/30', text: 'text-risk-medium', icon: '⚡' },
    'High Risk': { bg: 'bg-risk-high/15 border-risk-high/30', text: 'text-risk-high', icon: '⚠️' },
    'Critical Risk': { bg: 'bg-red-600/20 border-red-600/40', text: 'text-red-500', icon: '🚨' },
  }
  const s = cfg[tier] || cfg['Moderate Risk']
  return (
    <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold border ${s.bg} ${s.text}`} role="status" aria-label={`Risk level: ${tier}`}>
      <span aria-hidden="true">{s.icon}</span> {tier}
    </span>
  )
}

/** Score ring visualization */
function ScoreRing({ score }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score <= 25 ? '#22c55e' : score <= 50 ? '#f59e0b' : score <= 75 ? '#ef4444' : '#dc2626'

  return (
    <div className="relative w-36 h-36" role="meter" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100} aria-label={`Risk score: ${score}`}>
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} stroke="currentColor" strokeWidth="8" fill="none" className="text-lexguard-surface-2" />
        <circle cx="60" cy="60" r={radius} stroke={color} strokeWidth="8" fill="none" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" className="transition-all duration-1000 ease-out" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black text-lexguard-text">{Math.round(score)}</span>
        <span className="text-xs text-lexguard-muted">/ 100</span>
      </div>
    </div>
  )
}

/**
 * RiskDashboard — Full report dashboard with document overview,
 * category heatmap, and expandable clause cards.
 *
 * @param {Object} props
 * @param {Object} props.report - Complete analysis report
 */
export default function RiskDashboard({ report }) {
  if (!report) return null

  return (
    <div className="animate-fade-in-up space-y-8" aria-label="Analysis report" role="main">
      {/* Overview header */}
      <div className="glass-card p-8">
        <div className="flex flex-col md:flex-row items-center gap-8">
          {/* Score ring */}
          <ScoreRing score={report.aggregate_risk_score || 0} />

          {/* Stats */}
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <h2 className="text-2xl font-bold text-lexguard-text">Analysis Complete</h2>
              <RiskTierBadge tier={report.risk_tier} />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 rounded-xl bg-lexguard-surface-2/50">
                <p className="text-xs text-lexguard-muted mb-1">Document Type</p>
                <p className="text-sm font-semibold text-lexguard-text">{report.document_type}</p>
              </div>
              <div className="p-3 rounded-xl bg-lexguard-surface-2/50">
                <p className="text-xs text-lexguard-muted mb-1">Total Clauses</p>
                <p className="text-2xl font-bold text-lexguard-text">{report.total_clauses}</p>
              </div>
              <div className="p-3 rounded-xl bg-lexguard-surface-2/50">
                <p className="text-xs text-lexguard-muted mb-1">Flagged</p>
                <p className="text-2xl font-bold text-risk-high">{report.flagged_clauses}</p>
              </div>
              <div className="p-3 rounded-xl bg-lexguard-surface-2/50">
                <p className="text-xs text-lexguard-muted mb-1">Risk Score</p>
                <p className="text-2xl font-bold text-lexguard-accent">{report.aggregate_risk_score?.toFixed(1)}</p>
              </div>
            </div>

            {/* Score breakdown */}
            {report.score_breakdown && (
              <div className="mt-4 p-3 rounded-xl bg-lexguard-surface/50 border border-lexguard-border/30 text-xs text-lexguard-muted">
                <span className="font-semibold text-lexguard-text">Score Formula: </span>
                Total ({report.score_breakdown.total_clause_score?.toFixed(2)}) / Max ({report.score_breakdown.max_possible_score?.toFixed(2)}) × 100 = {report.score_breakdown.raw_percentage?.toFixed(2)}%
                <span className="ml-2 text-lexguard-muted">({report.score_breakdown.clause_count} scored clauses)</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Contradictions */}
      {report.contradictions?.length > 0 && (
        <div className="glass-card p-6 border-yellow-500/20">
          <h3 className="text-lg font-semibold text-yellow-400 flex items-center gap-2 mb-4">
            <span aria-hidden="true">⚡</span> Contradictions Detected ({report.contradictions.length})
          </h3>
          <div className="space-y-3">
            {report.contradictions.map((c, i) => (
              <div key={i} className="p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/20 text-sm">
                <p className="text-yellow-300">{c.explanation}</p>
                <p className="text-xs text-lexguard-muted mt-1">Between {c.clause_a_id} and {c.clause_b_id}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category heatmap */}
      <CategoryHeatmap heatmap={report.category_heatmap} />

      {/* Clause list */}
      <div>
        <h3 className="text-xl font-bold text-lexguard-text mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-lexguard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Clause Analysis ({report.clause_reports?.length || 0})
        </h3>
        <div className="space-y-4">
          {report.clause_reports?.map((cr, idx) => (
            <ClauseCard key={cr.clause?.id || idx} clauseReport={cr} index={idx} />
          ))}
        </div>
      </div>
    </div>
  )
}

RiskDashboard.propTypes = {
  report: PropTypes.shape({
    aggregate_risk_score: PropTypes.number,
    risk_tier: PropTypes.string,
    document_type: PropTypes.string,
    total_clauses: PropTypes.number,
    flagged_clauses: PropTypes.number,
    score_breakdown: PropTypes.object,
    contradictions: PropTypes.arrayOf(PropTypes.object),
    category_heatmap: PropTypes.arrayOf(PropTypes.object),
    clause_reports: PropTypes.arrayOf(PropTypes.object),
  }),
}
