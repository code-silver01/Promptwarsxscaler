import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

export default function AgentDebate({ clauseReport }) {
  const [expandedAgent, setExpandedAgent] = useState(null);

  if (!clauseReport.risk_position || !clauseReport.defense_position || !clauseReport.verdict) {
    return null;
  }

  const { risk_position, defense_position, verdict } = clauseReport;

  const agents = [
    {
      id: 'risk',
      name: 'Risk Agent',
      role: 'Red Team',
      color: 'red',
      icon: '⚠️',
      position: risk_position.risk_position,
      keyPoints: risk_position.key_phrases || [],
      scenario: risk_position.worst_case,
      reasoning: risk_position.reasoning,
      gradient: 'from-red-500 to-orange-500',
      bgGradient: 'from-red-500/10 to-orange-500/10',
      borderColor: 'border-red-500/30',
    },
    {
      id: 'defense',
      name: 'Defense Agent',
      role: 'Blue Team',
      color: 'blue',
      icon: '🛡️',
      position: defense_position.defense_position,
      keyPoints: defense_position.favorable_phrases || [],
      scenario: defense_position.best_case,
      reasoning: defense_position.reasoning,
      gradient: 'from-blue-500 to-cyan-500',
      bgGradient: 'from-blue-500/10 to-cyan-500/10',
      borderColor: 'border-blue-500/30',
    },
    {
      id: 'verdict',
      name: 'Verdict Agent',
      role: 'Neutral Synthesis',
      color: 'purple',
      icon: '⚖️',
      position: verdict.verdict,
      keyPoints: [],
      scenario: verdict.plain_english,
      reasoning: verdict.reasoning,
      gradient: 'from-purple-500 to-pink-500',
      bgGradient: 'from-purple-500/10 to-pink-500/10',
      borderColor: 'border-purple-500/30',
      severity: verdict.severity,
      confidence: verdict.confidence,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white">AI Agent Debate</h3>
      </div>

      <div className="space-y-3">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`bg-gradient-to-r ${agent.bgGradient} border ${agent.borderColor} rounded-xl overflow-hidden`}
          >
            <button
              onClick={() => setExpandedAgent(expandedAgent === agent.id ? null : agent.id)}
              className="w-full p-4 text-left hover:bg-white/5 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <span className="text-2xl">{agent.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-semibold text-white">{agent.name}</h4>
                      <span className={`text-xs px-2 py-0.5 rounded-full bg-gradient-to-r ${agent.gradient} text-white`}>
                        {agent.role}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 line-clamp-2">
                      {agent.position}
                    </p>
                    {agent.severity && (
                      <div className="flex items-center space-x-3 mt-2">
                        <span className={`text-xs px-2 py-1 rounded-md font-medium ${
                          agent.severity === 'HIGH' ? 'bg-red-500/20 text-red-300' :
                          agent.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-green-500/20 text-green-300'
                        }`}>
                          {agent.severity} RISK
                        </span>
                        <span className="text-xs text-slate-400">
                          Confidence: {Math.round(agent.confidence * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                <motion.svg
                  animate={{ rotate: expandedAgent === agent.id ? 180 : 0 }}
                  className="w-5 h-5 text-slate-400 flex-shrink-0 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
              </div>
            </button>

            <AnimatePresence>
              {expandedAgent === agent.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="border-t border-white/10"
                >
                  <div className="p-4 space-y-4">
                    {/* Reasoning */}
                    {agent.reasoning && (
                      <div>
                        <h5 className="text-sm font-semibold text-white mb-2 flex items-center">
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                          Agent Reasoning
                        </h5>
                        <p className="text-sm text-slate-300 leading-relaxed bg-black/20 rounded-lg p-3">
                          {agent.reasoning}
                        </p>
                      </div>
                    )}

                    {/* Key points */}
                    {agent.keyPoints.length > 0 && (
                      <div>
                        <h5 className="text-sm font-semibold text-white mb-2">Key Phrases</h5>
                        <div className="flex flex-wrap gap-2">
                          {agent.keyPoints.map((point, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-1 bg-black/30 rounded-md text-slate-300 border border-white/10"
                            >
                              "{point}"
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Scenario */}
                    <div>
                      <h5 className="text-sm font-semibold text-white mb-2">
                        {agent.id === 'verdict' ? 'Plain English' : agent.id === 'risk' ? 'Worst Case' : 'Best Case'}
                      </h5>
                      <p className="text-sm text-slate-300 leading-relaxed bg-black/20 rounded-lg p-3">
                        {agent.scenario}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mt-4">
        <p className="text-xs text-slate-400 leading-relaxed">
          <strong className="text-slate-300">How it works:</strong> Three AI agents independently analyze each risky clause. 
          The Risk Agent finds worst-case interpretations, the Defense Agent finds favorable readings, 
          and the Verdict Agent synthesizes both perspectives into a balanced assessment.
        </p>
      </div>
    </div>
  );
}
