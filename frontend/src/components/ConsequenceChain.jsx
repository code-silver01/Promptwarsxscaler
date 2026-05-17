import React from 'react'

/**
 * ConsequenceChain — 4-step visual flow for high-severity consequences.
 *
 * @param {Object} props
 * @param {Object} props.chain - Consequence chain data
 */
export default function ConsequenceChain({ chain }) {
  if (!chain) return null

  const steps = [
    { label: 'Trigger', text: chain.trigger_condition, color: 'text-yellow-400', bg: 'bg-yellow-400/10', icon: '⚡' },
    { label: 'Immediate', text: chain.immediate_consequence, color: 'text-orange-400', bg: 'bg-orange-400/10', icon: '💥' },
    { label: 'Downstream', text: chain.downstream_impact, color: 'text-red-400', bg: 'bg-red-400/10', icon: '🔗' },
    { label: 'Worst Case', text: chain.worst_case_scenario, color: 'text-risk-high', bg: 'bg-risk-high/10', icon: '🚨' },
  ]

  return (
    <div role="region" aria-label="Consequence chain analysis">
      <h4 className="text-sm font-semibold text-lexguard-text flex items-center gap-2 mb-4">
        <svg className="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Consequence Chain
      </h4>
      <div className="relative">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-start gap-4 mb-4 last:mb-0">
            {/* Connector line */}
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-xl ${step.bg} flex items-center justify-center shrink-0`}>
                <span aria-hidden="true">{step.icon}</span>
              </div>
              {idx < steps.length - 1 && (
                <div className="w-0.5 h-6 bg-lexguard-border/50 mt-1" aria-hidden="true" />
              )}
            </div>
            <div className="pt-1">
              <p className={`text-xs font-semibold ${step.color} uppercase tracking-wider`}>{step.label}</p>
              <p className="text-sm text-lexguard-text mt-0.5">{step.text}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
