import React from 'react'
import PropTypes from 'prop-types'

/**
 * CategoryHeatmap — Horizontal bar chart showing flagged clause count per category.
 *
 * @param {Object} props
 * @param {Array} props.heatmap - Array of {category, count} entries
 */
export default function CategoryHeatmap({ heatmap }) {
  if (!heatmap || heatmap.length === 0) return null

  const maxCount = Math.max(...heatmap.map(h => h.count), 1)

  const categoryColors = {
    IP_TRANSFER: 'from-red-500 to-rose-600',
    NON_COMPETE: 'from-orange-500 to-amber-600',
    ARBITRATION: 'from-yellow-500 to-yellow-600',
    AUTO_RENEWAL: 'from-emerald-500 to-green-600',
    LIABILITY_LIMITATION: 'from-teal-500 to-cyan-600',
    DATA_COLLECTION: 'from-blue-500 to-indigo-600',
    TERMINATION: 'from-violet-500 to-purple-600',
    PAYMENT_PENALTY: 'from-pink-500 to-rose-600',
    INDEMNIFICATION: 'from-fuchsia-500 to-purple-600',
    JURISDICTION: 'from-slate-400 to-slate-500',
  }

  return (
    <div className="glass-card p-6" role="region" aria-label="Category risk heatmap">
      <h3 className="text-lg font-semibold text-lexguard-text mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-lexguard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        Risk Category Breakdown
      </h3>
      <div className="space-y-3">
        {heatmap.map(({ category, count }) => {
          const width = (count / maxCount) * 100
          const gradient = categoryColors[category] || 'from-gray-500 to-gray-600'
          return (
            <div key={category} className="group">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-lexguard-muted group-hover:text-lexguard-text transition-colors">
                  {category.replace(/_/g, ' ')}
                </span>
                <span className="text-sm font-mono font-semibold text-lexguard-text">
                  {count}
                </span>
              </div>
              <div className="h-3 bg-lexguard-surface rounded-full overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r ${gradient} rounded-full transition-all duration-700 ease-out`}
                  style={{ width: `${width}%` }}
                  role="meter"
                  aria-valuenow={count}
                  aria-valuemin={0}
                  aria-valuemax={maxCount}
                  aria-label={`${category}: ${count} flagged clauses`}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

CategoryHeatmap.propTypes = {
  heatmap: PropTypes.arrayOf(PropTypes.shape({
    category: PropTypes.string,
    count: PropTypes.number,
  })),
}
