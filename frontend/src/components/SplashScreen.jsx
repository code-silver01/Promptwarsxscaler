import React, { useState, useEffect } from 'react'

/**
 * Enhanced Splash Screen with catchy messaging
 * Shows for 3 seconds before transitioning to onboarding
 */
export default function SplashScreen({ onComplete }) {
  const [progress, setProgress] = useState(0)
  const [currentMessage, setCurrentMessage] = useState(0)

  const messages = [
    "Authorize Only When You Know What You're Authorizing",
    "AI-Powered Contract Intelligence at Your Service",
    "Multi-Agent Legal Analysis in Real-Time"
  ]

  useEffect(() => {
    const duration = 3000 // 3 seconds
    const interval = 50 // Update every 50ms
    const increment = 100 / (duration / interval)

    const timer = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + increment
        if (newProgress >= 100) {
          clearInterval(timer)
          setTimeout(onComplete, 200) // Small delay before transition
          return 100
        }
        return newProgress
      })
    }, interval)

    // Cycle through messages
    const messageTimer = setInterval(() => {
      setCurrentMessage(prev => (prev + 1) % messages.length)
    }, 1000)

    return () => {
      clearInterval(timer)
      clearInterval(messageTimer)
    }
  }, [onComplete])

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      <div className="relative z-10 text-center max-w-4xl mx-auto px-6">
        {/* Logo and Brand */}
        <div className="mb-8">
          <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-600 flex items-center justify-center shadow-2xl shadow-indigo-500/25">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent mb-4">
            LexGuard One
          </h1>
          <p className="text-xl text-blue-100/80 font-light">
            AI Contract Intelligence Platform
          </p>
        </div>

        {/* Dynamic messaging */}
        <div className="mb-12 h-20 flex items-center justify-center">
          <h2 className="text-2xl md:text-3xl font-semibold text-white text-center leading-tight transition-all duration-500 ease-in-out">
            {messages[currentMessage]}
          </h2>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="w-full max-w-md mx-auto bg-white/10 rounded-full h-2 backdrop-blur-sm">
            <div 
              className="bg-gradient-to-r from-indigo-400 to-purple-500 h-2 rounded-full transition-all duration-100 ease-out shadow-lg shadow-indigo-500/50"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-blue-100/60 text-sm mt-3">
            Initializing AI Agents...
          </p>
        </div>

        {/* Feature highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <div className="w-8 h-8 mx-auto mb-2 text-indigo-400">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-white font-medium text-sm">Multi-Agent Debate</h3>
            <p className="text-blue-100/60 text-xs mt-1">Risk vs Defense analysis</p>
          </div>
          
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <div className="w-8 h-8 mx-auto mb-2 text-purple-400">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-white font-medium text-sm">Real-Time Analysis</h3>
            <p className="text-blue-100/60 text-xs mt-1">Streaming clause insights</p>
          </div>
          
          <div className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <div className="w-8 h-8 mx-auto mb-2 text-pink-400">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-white font-medium text-sm">Plain English</h3>
            <p className="text-blue-100/60 text-xs mt-1">Legal jargon translation</p>
          </div>
        </div>

        {/* Loading indicator */}
        <div className="mt-8 flex justify-center">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-100"></div>
            <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce delay-200"></div>
          </div>
        </div>
      </div>
    </div>
  )
}