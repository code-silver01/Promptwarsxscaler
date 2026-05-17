import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function OnboardingScreen({ onComplete }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    occupation: '',
    experience: '',
    purpose: '',
  });

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      // Save to localStorage
      localStorage.setItem('lexguard_user', JSON.stringify(formData));
      onComplete(formData);
    }
  };

  const handleSkip = () => {
    localStorage.setItem('lexguard_user', JSON.stringify({ skipped: true }));
    onComplete({ skipped: true });
  };

  const canProceed = () => {
    if (step === 1) return formData.name.trim().length > 0;
    if (step === 2) return formData.occupation.trim().length > 0;
    if (step === 3) return formData.purpose.trim().length > 0;
    return false;
  };

  const slideVariants = {
    enter: (direction) => ({
      x: direction > 0 ? 1000 : -1000,
      opacity: 0,
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1,
    },
    exit: (direction) => ({
      zIndex: 0,
      x: direction < 0 ? 1000 : -1000,
      opacity: 0,
    }),
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

      <div className="relative z-10 w-full max-w-2xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-2xl border border-slate-700/50 p-8"
        >
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">
              Welcome to LexGuard<span className="text-purple-400">One</span>
            </h2>
            <p className="text-slate-400">
              Let's personalize your contract analysis experience
            </p>
          </div>

          {/* Progress indicator */}
          <div className="flex items-center justify-center space-x-2 mb-8">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className={`h-2 rounded-full transition-all duration-300 ${
                  i === step
                    ? 'w-8 bg-purple-500'
                    : i < step
                    ? 'w-2 bg-purple-500'
                    : 'w-2 bg-slate-600'
                }`}
              />
            ))}
          </div>

          {/* Form steps */}
          <AnimatePresence mode="wait" custom={step}>
            <motion.div
              key={step}
              custom={step}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{
                x: { type: 'spring', stiffness: 300, damping: 30 },
                opacity: { duration: 0.2 },
              }}
              className="min-h-[200px]"
            >
              {step === 1 && (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      What's your name?
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      placeholder="Enter your full name"
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                      autoFocus
                    />
                  </div>
                  <p className="text-sm text-slate-400">
                    We'll use this to personalize your experience and generate
                    tailored recommendations.
                  </p>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      What's your occupation?
                    </label>
                    <input
                      type="text"
                      value={formData.occupation}
                      onChange={(e) =>
                        setFormData({ ...formData, occupation: e.target.value })
                      }
                      placeholder="e.g., Software Engineer, Freelancer, Business Owner"
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                      autoFocus
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Experience with legal contracts
                    </label>
                    <select
                      value={formData.experience}
                      onChange={(e) =>
                        setFormData({ ...formData, experience: e.target.value })
                      }
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    >
                      <option value="">Select your experience level</option>
                      <option value="beginner">Beginner - First time reading contracts</option>
                      <option value="intermediate">Intermediate - Some experience</option>
                      <option value="advanced">Advanced - Regularly review contracts</option>
                      <option value="expert">Expert - Legal professional</option>
                    </select>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      What brings you to LexGuard?
                    </label>
                    <select
                      value={formData.purpose}
                      onChange={(e) =>
                        setFormData({ ...formData, purpose: e.target.value })
                      }
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                      autoFocus
                    >
                      <option value="">Select your primary use case</option>
                      <option value="employment">Employment contract review</option>
                      <option value="freelance">Freelance/contractor agreements</option>
                      <option value="rental">Rental/lease agreements</option>
                      <option value="vendor">Vendor/supplier contracts</option>
                      <option value="nda">Non-disclosure agreements</option>
                      <option value="subscription">Subscription terms & conditions</option>
                      <option value="other">Other legal documents</option>
                    </select>
                  </div>
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                    <p className="text-sm text-purple-300">
                      <strong>Privacy first:</strong> Your information stays on your device.
                      We use it only to customize your analysis experience.
                    </p>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Action buttons */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700">
            <button
              onClick={handleSkip}
              className="text-slate-400 hover:text-white transition-colors text-sm font-medium"
            >
              Skip for now
            </button>
            <div className="flex items-center space-x-3">
              {step > 1 && (
                <button
                  onClick={() => setStep(step - 1)}
                  className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-colors font-medium"
                >
                  Back
                </button>
              )}
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className={`px-6 py-2.5 rounded-xl font-medium transition-all ${
                  canProceed()
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg shadow-purple-500/30'
                    : 'bg-slate-700 text-slate-500 cursor-not-allowed'
                }`}
              >
                {step === 3 ? 'Get Started' : 'Continue'}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
