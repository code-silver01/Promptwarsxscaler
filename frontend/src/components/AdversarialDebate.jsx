import React from 'react'
import PropTypes from 'prop-types'

/**
 * AdversarialDebate — Red/Blue/Verdict debate display.
 * Shows Risk Agent (red), Defense Agent (blue), and Verdict (neutral).
 *
 * @param {Object} props
 * @param {Object} props.riskPosition - Risk Agent output
 * @param {Object} props.defensePosition - Defense Agent output
 * @param {Object} props.verdict - Verdict Agent output
 */
export default function AdversarialDebate({ riskPosition, defensePosition, verdict }) {
  if (!riskPosition && !defensePosition) return null

  return (
    <div className="space-y-4" role="region" aria-label="Adversarial debate analysis">
      <h4 className="text-sm font-semibold text-lexguard-text flex items-center gap-2">
        <svg className="w-4 h-4 text-lexguard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        Adversarial Debate
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Risk Agent (Red) */}
        {riskPosition && (
          <div className="rounded-xl bg-agent-risk-bg/40 border border-risk-high/20 p-4" aria-label="Risk Agent position">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-risk-high/20 flex items-center justify-center">
                <span className="text-risk-high text-sm" aria-hidden="true">⚔️</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-risk-high">Risk Agent</p>
                <p className="text-xs text-lexguard-muted">Red Team</p>
              </div>
            </div>
            <p className="text-sm text-agent-risk leading-relaxed">{riskPosition.risk_position}</p>
            {riskPosition.key_phrases?.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-lexguard-muted mb-1.5">Key Phrases:</p>
                <div className="flex flex-wrap gap-1.5">
                  {riskPosition.key_phrases.map((phrase, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-risk-high/10 text-risk-high text-xs">
                      "{phrase}"
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="mt-3 p-2 rounded-lg bg-risk-high/5 border border-risk-high/10">
              <p className="text-xs text-lexguard-muted">Worst Case:</p>
              <p className="text-xs text-risk-high mt-0.5">{riskPosition.worst_case}</p>
            </div>
          </div>
        )}

        {/* Defense Agent (Blue) */}
        {defensePosition && (
          <div className="rounded-xl bg-agent-defense-bg/40 border border-blue-500/20 p-4" aria-label="Defense Agent position">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <span className="text-blue-400 text-sm" aria-hidden="true">🛡️</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-blue-400">Defense Agent</p>
                <p className="text-xs text-lexguard-muted">Blue Team</p>
              </div>
            </div>
            <p className="text-sm text-agent-defense leading-relaxed">{defensePosition.defense_position}</p>
            {defensePosition.favorable_phrases?.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-lexguard-muted mb-1.5">Favorable Phrases:</p>
                <div className="flex flex-wrap gap-1.5">
                  {defensePosition.favorable_phrases.map((phrase, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-xs">
                      "{phrase}"
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="mt-3 p-2 rounded-lg bg-blue-500/5 border border-blue-500/10">
              <p className="text-xs text-lexguard-muted">Best Case:</p>
              <p className="text-xs text-blue-400 mt-0.5">{defensePosition.best_case}</p>
            </div>
          </div>
        )}
      </div>

      {/* Verdict */}
      {verdict && (
        <div className="rounded-xl bg-agent-verdict-bg border border-lexguard-border p-4" aria-label="Verdict synthesis">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-lexguard-accent/20 flex items-center justify-center">
                <span className="text-lexguard-accent text-sm" aria-hidden="true">⚖️</span>
              </div>
              <p className="text-sm font-semibold text-lexguard-accent">Verdict</p>
            </div>
            {verdict.confidence !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-lexguard-muted">Confidence:</span>
                <div className="w-24 h-2 rounded-full bg-lexguard-surface overflow-hidden">
                  <div className="h-full bg-lexguard-accent rounded-full transition-all" style={{ width: `${verdict.confidence * 100}%` }} />
                </div>
                <span className="text-xs font-mono text-lexguard-accent">{(verdict.confidence * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
          <p className="text-sm text-lexguard-text">{verdict.verdict}</p>
          {verdict.plain_english && (
            <p className="mt-2 text-sm text-lexguard-muted italic">{verdict.plain_english}</p>
          )}
        </div>
      )}
    </div>
  )
}

AdversarialDebate.propTypes = {
  riskPosition: PropTypes.shape({
    risk_position: PropTypes.string,
    key_phrases: PropTypes.arrayOf(PropTypes.string),
    worst_case: PropTypes.string,
  }),
  defensePosition: PropTypes.shape({
    defense_position: PropTypes.string,
    favorable_phrases: PropTypes.arrayOf(PropTypes.string),
    best_case: PropTypes.string,
  }),
  verdict: PropTypes.shape({
    verdict: PropTypes.string,
    severity: PropTypes.oneOf(['HIGH', 'MEDIUM', 'LOW']),
    confidence: PropTypes.number,
    plain_english: PropTypes.string,
  }),
}
