import React from 'react'
import PropTypes from 'prop-types'

/**
 * Compute word-level diff between two strings.
 * Returns removed words (red strike) for original, added words (green highlight) for suggested.
 */
function computeWordDiff(original, suggested) {
  const origWords = original.split(/\s+/)
  const suggWords = suggested.split(/\s+/)
  const origSet = new Set(origWords)
  const suggSet = new Set(suggWords)

  const origResult = origWords.map(word => ({
    word,
    removed: !suggSet.has(word),
  }))
  const suggResult = suggWords.map(word => ({
    word,
    added: !origSet.has(word),
  }))
  return { origResult, suggResult }
}

/**
 * NegotiationSuggest — Side-by-side original vs. suggested clause text with word-level diff.
 *
 * @param {Object} props
 * @param {Object} props.suggestion - Negotiation suggestion data
 */
export default function NegotiationSuggest({ suggestion }) {
  if (!suggestion) return null

  const hasDiff = suggestion.original_clause_text && suggestion.suggested_alternative_text
  const { origResult, suggResult } = hasDiff
    ? computeWordDiff(suggestion.original_clause_text, suggestion.suggested_alternative_text)
    : { origResult: [], suggResult: [] }

  return (
    <div role="region" aria-label="Negotiation suggestion">
      <h4 className="text-sm font-semibold text-lexguard-text flex items-center gap-2 mb-4">
        <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        Negotiation Suggestion
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Original */}
        <div className="rounded-xl bg-risk-high/5 border border-risk-high/20 p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-risk-high uppercase tracking-wider">Original Clause</span>
            <span className="px-1.5 py-0.5 rounded bg-risk-high/10 text-risk-high text-xs" aria-hidden="true">Risky</span>
          </div>
          <p className="text-sm text-lexguard-text leading-relaxed">
            {hasDiff
              ? origResult.map((item, i) => (
                  <span
                    key={i}
                    className={item.removed ? 'line-through text-red-400 bg-red-400/10 rounded px-0.5 mx-0.5' : 'mx-0.5'}
                  >
                    {item.word}
                  </span>
                ))
              : suggestion.original_clause_text}
          </p>
        </div>
        {/* Suggested */}
        <div className="rounded-xl bg-risk-low/5 border border-risk-low/20 p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-risk-low uppercase tracking-wider">Suggested Alternative</span>
            <span className="px-1.5 py-0.5 rounded bg-risk-low/10 text-risk-low text-xs" aria-hidden="true">Fairer</span>
          </div>
          <p className="text-sm text-lexguard-text leading-relaxed">
            {hasDiff
              ? suggResult.map((item, i) => (
                  <span
                    key={i}
                    className={item.added ? 'text-green-300 bg-green-400/15 rounded px-0.5 mx-0.5 font-medium' : 'mx-0.5'}
                  >
                    {item.word}
                  </span>
                ))
              : suggestion.suggested_alternative_text}
          </p>
        </div>
      </div>
      {suggestion.why_safer && (
        <div className="mt-3 p-3 rounded-lg bg-lexguard-surface-2 border border-lexguard-border/50">
          <p className="text-xs text-lexguard-muted">
            <span className="font-semibold text-green-400">Why Safer: </span>
            {suggestion.why_safer}
          </p>
        </div>
      )}
    </div>
  )
}

NegotiationSuggest.propTypes = {
  suggestion: PropTypes.shape({
    original_clause_text: PropTypes.string,
    suggested_alternative_text: PropTypes.string,
    why_safer: PropTypes.string,
  }),
}
