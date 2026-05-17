import React, { useState } from 'react';
import PropTypes from 'prop-types';

const STEPS = [
  {
    title: "Discover Hidden Liabilities",
    description: "Legal jargon is designed to confuse. LexGuard One reads every single line of your contract and flags exploitative clauses.",
    icon: "🔍",
    color: "from-blue-500 to-indigo-600"
  },
  {
    title: "Adversarial AI Debate",
    description: "We don't just summarize. Our Risk Agent and Defense Agent debate each clause to find worst-case consequences before you sign.",
    icon: "⚔️",
    color: "from-indigo-500 to-purple-600"
  },
  {
    title: "Fairer Negotiations",
    description: "Get instant pushback points and fairer alternative clauses backed by our contract benchmark database.",
    icon: "🛡️",
    color: "from-purple-500 to-pink-600"
  }
];

/**
 * Onboarding - Guided tour for first-time users
 */
export default function Onboarding({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(curr => curr + 1);
    } else {
      onComplete();
    }
  };

  const step = STEPS[currentStep];

  return (
    <div className="fixed inset-0 bg-lexguard-bg flex items-center justify-center z-40 p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-br ${step.color} blur-[120px] rounded-full opacity-20 transition-colors duration-700`} />
      </div>

      <div className="glass-card max-w-lg w-full p-8 md:p-12 relative z-10 animate-fade-in-up">
        {/* Step indicator */}
        <div className="flex justify-center gap-2 mb-8">
          {STEPS.map((_, idx) => (
            <div 
              key={idx} 
              className={`h-1.5 rounded-full transition-all duration-300 ${
                idx === currentStep ? 'w-8 bg-lexguard-accent' : 'w-4 bg-lexguard-surface-2'
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="text-center min-h-[220px] flex flex-col items-center">
          <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center text-4xl mb-6 shadow-lg transform transition-transform duration-500 hover:scale-110`}>
            {step.icon}
          </div>
          <h2 className="text-2xl font-bold text-white mb-4 transition-all duration-300">
            {step.title}
          </h2>
          <p className="text-lexguard-muted leading-relaxed transition-all duration-300">
            {step.description}
          </p>
        </div>

        {/* Controls */}
        <div className="mt-8 flex justify-between items-center">
          <button 
            onClick={onComplete}
            className="text-sm font-medium text-lexguard-muted hover:text-white transition-colors"
          >
            Skip
          </button>
          
          <button 
            onClick={handleNext}
            className={`px-6 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r ${step.color} shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105`}
          >
            {currentStep === STEPS.length - 1 ? "Get Started" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}

Onboarding.propTypes = {
  onComplete: PropTypes.func.isRequired,
}
