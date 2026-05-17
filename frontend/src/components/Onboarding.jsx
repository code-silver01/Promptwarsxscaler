import React, { useState } from 'react'

/**
 * User Onboarding Component
 * Collects user profile information for personalized analysis
 */
export default function Onboarding({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [userProfile, setUserProfile] = useState({
    name: '',
    occupation: '',
    experience: '',
    companySize: '',
    industry: '',
    riskTolerance: '',
    contractTypes: []
  })

  const steps = [
    {
      title: "Welcome to LexGuard One",
      subtitle: "Let's personalize your contract analysis experience",
      fields: [
        {
          key: 'name',
          label: 'Your Name',
          type: 'text',
          placeholder: 'Enter your full name',
          required: true
        }
      ]
    },
    {
      title: "Professional Background",
      subtitle: "Help us understand your role and experience",
      fields: [
        {
          key: 'occupation',
          label: 'Occupation',
          type: 'select',
          options: [
            'Software Developer',
            'Product Manager',
            'Designer',
            'Marketing Professional',
            'Sales Representative',
            'Consultant',
            'Entrepreneur',
            'Legal Professional',
            'Executive',
            'Freelancer',
            'Student',
            'Other'
          ],
          required: true
        },
        {
          key: 'experience',
          label: 'Experience Level',
          type: 'select',
          options: [
            'Entry Level (0-2 years)',
            'Mid Level (3-5 years)',
            'Senior Level (6-10 years)',
            'Executive Level (10+ years)'
          ],
          required: true
        }
      ]
    },
    {
      title: "Company Context",
      subtitle: "Tell us about your work environment",
      fields: [
        {
          key: 'companySize',
          label: 'Company Size',
          type: 'select',
          options: [
            'Startup (1-10 employees)',
            'Small Business (11-50 employees)',
            'Medium Business (51-200 employees)',
            'Large Company (201-1000 employees)',
            'Enterprise (1000+ employees)',
            'Self-employed'
          ],
          required: true
        },
        {
          key: 'industry',
          label: 'Industry',
          type: 'select',
          options: [
            'Technology',
            'Healthcare',
            'Finance',
            'Education',
            'Manufacturing',
            'Retail',
            'Consulting',
            'Media & Entertainment',
            'Real Estate',
            'Non-profit',
            'Government',
            'Other'
          ],
          required: true
        }
      ]
    },
    {
      title: "Risk Preferences",
      subtitle: "How should we calibrate our analysis for you?",
      fields: [
        {
          key: 'riskTolerance',
          label: 'Risk Tolerance',
          type: 'select',
          options: [
            'Conservative (Flag all potential risks)',
            'Moderate (Balance risk and opportunity)',
            'Aggressive (Focus on major risks only)'
          ],
          required: true
        },
        {
          key: 'contractTypes',
          label: 'Contract Types You Typically Review',
          type: 'multiselect',
          options: [
            'Employment Agreements',
            'Freelance Contracts',
            'Service Agreements',
            'NDAs',
            'Partnership Agreements',
            'Licensing Agreements',
            'Vendor Contracts',
            'Real Estate Contracts'
          ],
          required: false
        }
      ]
    }
  ]

  const handleInputChange = (key, value) => {
    setUserProfile(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const handleMultiSelectChange = (key, option) => {
    setUserProfile(prev => ({
      ...prev,
      [key]: prev[key].includes(option)
        ? prev[key].filter(item => item !== option)
        : [...prev[key], option]
    }))
  }

  const isStepValid = () => {
    const currentStepData = steps[currentStep]
    return currentStepData.fields.every(field => {
      if (!field.required) return true
      const value = userProfile[field.key]
      return value && (Array.isArray(value) ? value.length > 0 : value.trim() !== '')
    })
  }

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      // Store user profile in localStorage for use during analysis
      localStorage.setItem('lexguard_user_profile', JSON.stringify(userProfile))
      onComplete(userProfile)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const currentStepData = steps[currentStep]

  return (
    <div className="min-h-screen bg-lexguard-bg flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-lexguard-muted">
              Step {currentStep + 1} of {steps.length}
            </span>
            <span className="text-sm text-lexguard-muted">
              {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-lexguard-surface-2 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Main content */}
        <div className="bg-lexguard-surface rounded-2xl p-8 border border-lexguard-border shadow-xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-lexguard-text mb-2">
              {currentStepData.title}
            </h1>
            <p className="text-lexguard-muted text-lg">
              {currentStepData.subtitle}
            </p>
          </div>

          <div className="space-y-6">
            {currentStepData.fields.map((field) => (
              <div key={field.key}>
                <label className="block text-sm font-medium text-lexguard-text mb-2">
                  {field.label}
                  {field.required && <span className="text-risk-high ml-1">*</span>}
                </label>

                {field.type === 'text' && (
                  <input
                    type="text"
                    value={userProfile[field.key]}
                    onChange={(e) => handleInputChange(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    className="w-full px-4 py-3 rounded-lg bg-lexguard-surface-2 border border-lexguard-border text-lexguard-text placeholder-lexguard-muted focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  />
                )}

                {field.type === 'select' && (
                  <select
                    value={userProfile[field.key]}
                    onChange={(e) => handleInputChange(field.key, e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-lexguard-surface-2 border border-lexguard-border text-lexguard-text focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  >
                    <option value="">Select {field.label}</option>
                    {field.options.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                )}

                {field.type === 'multiselect' && (
                  <div className="grid grid-cols-2 gap-3">
                    {field.options.map((option) => (
                      <label
                        key={option}
                        className="flex items-center p-3 rounded-lg bg-lexguard-surface-2 border border-lexguard-border cursor-pointer hover:bg-lexguard-surface-3 transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={userProfile[field.key].includes(option)}
                          onChange={() => handleMultiSelectChange(field.key, option)}
                          className="w-4 h-4 text-indigo-600 bg-lexguard-surface-2 border-lexguard-border rounded focus:ring-indigo-500 focus:ring-2"
                        />
                        <span className="ml-3 text-sm text-lexguard-text">
                          {option}
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Navigation buttons */}
          <div className="flex justify-between mt-8">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="px-6 py-3 rounded-lg border border-lexguard-border text-lexguard-muted hover:text-lexguard-text hover:border-lexguard-accent transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>

            <button
              onClick={handleNext}
              disabled={!isStepValid()}
              className="px-8 py-3 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:from-indigo-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-lexguard-surface transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/25"
            >
              {currentStep === steps.length - 1 ? 'Complete Setup' : 'Next'}
            </button>
          </div>

          {/* Skip option for non-required steps */}
          {currentStep > 0 && (
            <div className="text-center mt-4">
              <button
                onClick={() => onComplete(userProfile)}
                className="text-sm text-lexguard-muted hover:text-lexguard-accent transition-colors"
              >
                Skip remaining steps
              </button>
            </div>
          )}
        </div>

        {/* Privacy notice */}
        <div className="mt-6 text-center">
          <p className="text-xs text-lexguard-muted">
            Your information is used only to personalize your analysis experience and is not shared with third parties.
          </p>
        </div>
      </div>
    </div>
  )
}