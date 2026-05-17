import React, { useState } from 'react'
import AdversarialDebate from './AdversarialDebate.jsx'
import ConsequenceChain from './ConsequenceChain.jsx'
import NegotiationSuggest from './NegotiationSuggest.jsx'

/** Severity badge with icon + text + color */
function SeverityBadge({ severity }) {
  const cfg = {
    HIGH: { bg: 'bg-risk-high/15 border-risk-high/30', text: 'text-risk-high', icon: '⚠️', label: 'High Risk' },
    MEDIUM: { bg: 'bg-risk-medium/15 border-risk-medium/30', text: 'text-risk-medium', icon: '⚡', label: 'Medium Risk' },
    LOW: { bg: 'bg-risk-low/15 border-risk-low/30', text: 'text-risk-low', icon: '✓', label: 'Low Risk' },
  }
  const s = cfg[severity] || cfg.LOW
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${s.bg} ${s.text}`} role="status" aria-label={s.label}>
      <span aria-hidden="true">{s.icon}</span> {s.label}
    </span>
  )
}

/** Highlight vague qualifiers in clause text */
function HighlightedText({ text, qualifiers = [] }) {
  if (!qualifiers.length) return <p className="text-sm text-lexguard-text leading-relaxed">{text}</p>
  let result = text
  const parts = []
  let lastIdx = 0
  const sortedQ = [...qualifiers].sort((a, b) => {
    const ia = text.toLowerCase().indexOf(a.toLowerCase())
    const ib = text.toLowerCase().indexOf(b.toLowerCase())
    return ia - ib
  })
  for (const q of sortedQ) {
    const idx = result.toLowerCase().indexOf(q.toLowerCase(), lastIdx)
    if (idx === -1) continue
    if (idx > lastIdx) parts.push({ text: result.slice(lastIdx, idx), highlight: false })
    parts.push({ text: result.slice(idx, idx + q.length), highlight: true })
    lastIdx = idx + q.length
  }
  if (lastIdx < result.length) parts.push({ text: result.slice(lastIdx), highlight: false })
  if (!parts.length) return <p className="text-sm text-lexguard-text leading-relaxed">{text}</p>
  return (
    <p className="text-sm text-lexguard-text leading-relaxed">
      {parts.map((p, i) =>
        p.highlight ? (
          <mark key={i} className="bg-yellow-400/25 text-yellow-300 px-0.5 rounded">{p.text}</mark>
        ) : (
          <span key={i}>{p.text}</span>
        )
      )}
    </p>
  )
}

/**
 * ClauseCard — Expandable per-clause analysis card.
 *
 * @param {Object} props
 * @param {Object} props.clauseReport - Full clause analysis report
 * @param {number} props.index - Clause display index
 */
export default function ClauseCard({ clauseReport, index }) {
  const [expanded, setExpanded] = useState(false)
  const cr = clauseReport

  return (
    <article className="glass-card overflow-hidden animate-fade-in-up" style={{ animationDelay: `${index * 80}ms` }}>
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 flex items-start gap-4 text-left hover:bg-lexguard-surface-2/30 transition-colors"
        aria-expanded={expanded}
        aria-controls={`clause-detail-${cr.clause?.id}`}
        id={`clause-header-${cr.clause?.id}`}
      >
        <div className="shrink-0 w-10 h-10 rounded-lg bg-lexguard-surface-2 flex items-center justify-center text-sm font-mono text-lexguard-muted mt-0.5">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            {cr.category && (
              <span className="px-2.5 py-0.5 rounded-md bg-lexguard-accent/10 text-lexguard-accent text-xs font-medium">
                {cr.category.replace(/_/g, ' ')}
              </span>
            )}
            {cr.severity && <SeverityBadge severity={cr.severity} />}
            {cr.benchmark_comparison && (
              <span className="text-xs text-lexguard-muted">
                📊 {cr.benchmark_comparison.percentile?.toFixed(0)}th percentile
              </span>
            )}
          </div>
          <p className="text-sm text-lexguard-text line-clamp-2">{cr.clause?.text}</p>
          {cr.clause?.section && (
            <p className="text-xs text-lexguard-muted mt-1">Section: {cr.clause.section}</p>
          )}
        </div>
        <svg className={`w-5 h-5 text-lexguard-muted shrink-0 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-6 pb-6 space-y-6 border-t border-lexguard-border/30 pt-4" id={`clause-detail-${cr.clause?.id}`} role="region" aria-labelledby={`clause-header-${cr.clause?.id}`}>
          {/* Full clause text with highlights */}
          <div>
            <h4 className="text-xs font-semibold text-lexguard-muted uppercase tracking-wider mb-2">Full Clause Text</h4>
            <div className="p-4 rounded-xl bg-lexguard-surface border border-lexguard-border/50">
              <HighlightedText text={cr.clause?.text || ''} qualifiers={cr.vague_qualifiers || []} />
            </div>
          </div>

          {/* Plain English verdict */}
          {cr.plain_english && (
            <div className="p-4 rounded-xl bg-lexguard-accent/5 border border-lexguard-accent/20">
              <p className="text-sm text-lexguard-text">💡 <span className="font-semibold">In plain English:</span> {cr.plain_english}</p>
            </div>
          )}

          {/* Adversarial debate */}
          <AdversarialDebate riskPosition={cr.risk_position} defensePosition={cr.defense_position} verdict={cr.verdict} />

          {/* Consequence chain */}
          {cr.consequence_chain && <ConsequenceChain chain={cr.consequence_chain} />}

          {/* Benchmark comparison */}
          {cr.benchmark_comparison && (
            <div className="p-4 rounded-xl bg-lexguard-surface-2 border border-lexguard-border/50">
              <h4 className="text-sm font-semibold text-lexguard-text flex items-center gap-2 mb-2">
                <span aria-hidden="true">📊</span> Benchmark Comparison
              </h4>
              <p className="text-sm text-lexguard-muted">{cr.benchmark_comparison.summary}</p>
            </div>
          )}

          {/* Negotiation suggestion */}
          {cr.negotiation_suggestion && <NegotiationSuggest suggestion={cr.negotiation_suggestion} />}

          {/* Score breakdown */}
          {cr.score_breakdown && (
            <div className="p-4 rounded-xl bg-lexguard-surface-2 border border-lexguard-border/50">
              <h4 className="text-xs font-semibold text-lexguard-muted uppercase tracking-wider mb-2">Score Breakdown</h4>
              <div className="grid grid-cols-4 gap-3 text-center text-xs">
                <div><p className="text-lexguard-muted">Severity</p><p className="text-lexguard-text font-mono font-bold text-lg">{cr.score_breakdown.base_severity_score}</p></div>
                <div><p className="text-lexguard-muted">Weight</p><p className="text-lexguard-text font-mono font-bold text-lg">×{cr.score_breakdown.category_weight}</p></div>
                <div><p className="text-lexguard-muted">Deviation</p><p className="text-lexguard-text font-mono font-bold text-lg">×{cr.score_breakdown.benchmark_deviation}</p></div>
                <div><p className="text-lexguard-muted">Score</p><p className="text-lexguard-accent font-mono font-bold text-lg">={cr.score_breakdown.final_score}</p></div>
              </div>
            </div>
          )}
        </div>
      )}
    </article>
  )
}
