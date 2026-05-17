import React, { useState, useEffect } from 'react'

/**
 * Agent Debate Visualization Component
 * Shows real-time multi-agent debate with explicit reasoning
 */
export default function AgentDebate({ clauseId, debateData, isActive }) {
  const [currentRound, setCurrentRound] = useState(0)
  const [showReasoning, setShowReasoning] = useState({})
  const [animationStep, setAnimationStep] = useState('initial')

  useEffect(() => {
    if (isActive && debateData) {
      // Animate through debate rounds
      const timer = setTimeout(() => {
        if (currentRound < debateData.rounds?.length) {
          setCurrentRound(prev => prev + 1)
        }
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [isActive, debateData, currentRound])

  const toggleReasoning = (agentType, round = 0) => {
    const key = `${agentType}-${round}`
    setShowReasoning(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  if (!debateData) {
    return (
      <div className="bg-lexguard-surface rounded-xl p-6 border border-lexguard-border">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-lexguard-muted">Initializing agent debate...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-lexguard-surface rounded-xl border border-lexguard-border overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 p-4 border-b border-lexguard-border">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-lexguard-text">
            Multi-Agent Debate Analysis
          </h3>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-risk-high rounded-full animate-pulse"></div>
              <span className="text-xs text-lexguard-muted">Live Analysis</span>
            </div>
          </div>
        </div>
      </div>

      {/* Clause Text */}
      <div className="p-4 bg-lexguard-surface-2 border-b border-lexguard-border">
        <h4 className="text-sm font-medium text-lexguard-text mb-2">Clause Under Analysis:</h4>
        <p className="text-sm text-lexguard-muted italic bg-lexguard-surface rounded-lg p-3 border-l-4 border-indigo-500">
          "{debateData.clauseText}"
        </p>
      </div>

      {/* Agent Arena */}
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Risk Agent */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h4 className="font-semibold text-lexguard-text">Risk Agent</h4>
                <p className="text-xs text-lexguard-muted">Adversarial Analysis</p>
              </div>
            </div>

            {/* Initial Risk Position */}
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800">
              <div className="flex items-start justify-between mb-2">
                <h5 className="font-medium text-red-800 dark:text-red-200 text-sm">Risk Position</h5>
                <button
                  onClick={() => toggleReasoning('risk', 0)}
                  className="text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 transition-colors"
                >
                  {showReasoning['risk-0'] ? 'Hide' : 'Show'} Reasoning
                </button>
              </div>
              <p className="text-sm text-red-700 dark:text-red-300 mb-3">
                {debateData.riskAgent?.riskPosition}
              </p>
              
              {/* Key Risk Phrases */}
              <div className="mb-3">
                <h6 className="text-xs font-medium text-red-800 dark:text-red-200 mb-1">Key Risk Phrases:</h6>
                <div className="flex flex-wrap gap-1">
                  {debateData.riskAgent?.keyPhrases?.map((phrase, idx) => (
                    <span key={idx} className="px-2 py-1 bg-red-100 dark:bg-red-800/30 text-red-800 dark:text-red-200 text-xs rounded-full">
                      "{phrase}"
                    </span>
                  ))}
                </div>
              </div>

              {/* Worst Case Scenario */}
              <div className="bg-red-100 dark:bg-red-800/20 rounded-lg p-3 border border-red-200 dark:border-red-700">
                <h6 className="text-xs font-medium text-red-800 dark:text-red-200 mb-1">Worst Case Scenario:</h6>
                <p className="text-xs text-red-700 dark:text-red-300">
                  {debateData.riskAgent?.worstCase}
                </p>
              </div>

              {/* Reasoning (Collapsible) */}
              {showReasoning['risk-0'] && (
                <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-700">
                  <h6 className="text-xs font-medium text-red-800 dark:text-red-200 mb-2">Step-by-Step Reasoning:</h6>
                  <div className="text-xs text-red-700 dark:text-red-300 space-y-1">
                    {debateData.riskAgent?.reasoning?.split('\n').map((step, idx) => (
                      <div key={idx} className="flex items-start space-x-2">
                        <span className="text-red-500 mt-0.5">•</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Risk Agent Rebuttals */}
            {debateData.rounds?.map((round, idx) => (
              <div key={`risk-round-${idx}`} className="bg-red-50 dark:bg-red-900/10 rounded-lg p-4 border border-red-200 dark:border-red-800 opacity-75">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium text-red-800 dark:text-red-200 text-sm">
                    Round {idx + 1} Rebuttal
                  </h5>
                  <span className="text-xs text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-800/30 px-2 py-1 rounded-full">
                    Counter-Attack
                  </span>
                </div>
                <p className="text-sm text-red-700 dark:text-red-300">
                  {round.riskRebuttal?.rebuttal}
                </p>
              </div>
            ))}
          </div>

          {/* Defense Agent */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="font-semibold text-lexguard-text">Defense Agent</h4>
                <p className="text-xs text-lexguard-muted">Protective Analysis</p>
              </div>
            </div>

            {/* Initial Defense Position */}
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
              <div className="flex items-start justify-between mb-2">
                <h5 className="font-medium text-green-800 dark:text-green-200 text-sm">Defense Position</h5>
                <button
                  onClick={() => toggleReasoning('defense', 0)}
                  className="text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 transition-colors"
                >
                  {showReasoning['defense-0'] ? 'Hide' : 'Show'} Reasoning
                </button>
              </div>
              <p className="text-sm text-green-700 dark:text-green-300 mb-3">
                {debateData.defenseAgent?.defensePosition}
              </p>
              
              {/* Favorable Phrases */}
              <div className="mb-3">
                <h6 className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">Protective Phrases:</h6>
                <div className="flex flex-wrap gap-1">
                  {debateData.defenseAgent?.favorablePhrases?.map((phrase, idx) => (
                    <span key={idx} className="px-2 py-1 bg-green-100 dark:bg-green-800/30 text-green-800 dark:text-green-200 text-xs rounded-full">
                      "{phrase}"
                    </span>
                  ))}
                </div>
              </div>

              {/* Best Case Scenario */}
              <div className="bg-green-100 dark:bg-green-800/20 rounded-lg p-3 border border-green-200 dark:border-green-700">
                <h6 className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">Best Case Scenario:</h6>
                <p className="text-xs text-green-700 dark:text-green-300">
                  {debateData.defenseAgent?.bestCase}
                </p>
              </div>

              {/* Reasoning (Collapsible) */}
              {showReasoning['defense-0'] && (
                <div className="mt-3 pt-3 border-t border-green-200 dark:border-green-700">
                  <h6 className="text-xs font-medium text-green-800 dark:text-green-200 mb-2">Step-by-Step Reasoning:</h6>
                  <div className="text-xs text-green-700 dark:text-green-300 space-y-1">
                    {debateData.defenseAgent?.reasoning?.split('\n').map((step, idx) => (
                      <div key={idx} className="flex items-start space-x-2">
                        <span className="text-green-500 mt-0.5">•</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Defense Agent Rebuttals */}
            {debateData.rounds?.map((round, idx) => (
              <div key={`defense-round-${idx}`} className="bg-green-50 dark:bg-green-900/10 rounded-lg p-4 border border-green-200 dark:border-green-800 opacity-75">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium text-green-800 dark:text-green-200 text-sm">
                    Round {idx + 1} Rebuttal
                  </h5>
                  <span className="text-xs text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-800/30 px-2 py-1 rounded-full">
                    Defense
                  </span>
                </div>
                <p className="text-sm text-green-700 dark:text-green-300">
                  {round.defenseRebuttal?.rebuttal}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Verdict Agent */}
        {debateData.verdict && (
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-6 border border-indigo-200 dark:border-indigo-800">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
              </div>
              <div>
                <h4 className="text-lg font-semibold text-lexguard-text">Verdict Agent</h4>
                <p className="text-sm text-lexguard-muted">Neutral Synthesis & Final Judgment</p>
              </div>
              <div className="ml-auto">
                <div className="flex items-center space-x-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    debateData.verdict.severity === 'HIGH' 
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200'
                      : debateData.verdict.severity === 'MEDIUM'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200'
                      : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
                  }`}>
                    {debateData.verdict.severity} RISK
                  </span>
                  <span className="text-xs text-lexguard-muted">
                    {Math.round(debateData.verdict.confidence * 100)}% confidence
                  </span>
                </div>
              </div>
            </div>

            {/* Final Verdict */}
            <div className="mb-4">
              <h5 className="font-medium text-lexguard-text mb-2">Final Verdict:</h5>
              <p className="text-lexguard-text bg-white dark:bg-lexguard-surface rounded-lg p-4 border border-indigo-200 dark:border-indigo-800">
                {debateData.verdict.verdict}
              </p>
            </div>

            {/* Plain English Explanation */}
            <div className="mb-4">
              <h5 className="font-medium text-lexguard-text mb-2">In Plain English:</h5>
              <p className="text-lexguard-muted bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-200 dark:border-indigo-800">
                {debateData.verdict.plainEnglish}
              </p>
            </div>

            {/* Verdict Reasoning */}
            <div>
              <button
                onClick={() => toggleReasoning('verdict')}
                className="flex items-center space-x-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200 transition-colors mb-2"
              >
                <span className="font-medium">Verdict Reasoning</span>
                <svg 
                  className={`w-4 h-4 transition-transform ${showReasoning['verdict'] ? 'rotate-180' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {showReasoning['verdict'] && (
                <div className="bg-white dark:bg-lexguard-surface rounded-lg p-4 border border-indigo-200 dark:border-indigo-800">
                  <div className="text-sm text-lexguard-text space-y-2">
                    {debateData.verdict.reasoning?.split('\n').map((step, idx) => (
                      <div key={idx} className="flex items-start space-x-2">
                        <span className="text-indigo-500 mt-0.5 font-medium">{idx + 1}.</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Debate Statistics */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-lexguard-surface-2 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-lexguard-text">
              {debateData.rounds?.length || 0}
            </div>
            <div className="text-sm text-lexguard-muted">Debate Rounds</div>
          </div>
          <div className="bg-lexguard-surface-2 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-lexguard-text">
              {debateData.processingTime ? `${debateData.processingTime.toFixed(1)}s` : 'N/A'}
            </div>
            <div className="text-sm text-lexguard-muted">Processing Time</div>
          </div>
          <div className="bg-lexguard-surface-2 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-lexguard-text">
              {debateData.verdict?.confidence ? `${Math.round(debateData.verdict.confidence * 100)}%` : 'N/A'}
            </div>
            <div className="text-sm text-lexguard-muted">Confidence Score</div>
          </div>
        </div>
      </div>
    </div>
  )
}