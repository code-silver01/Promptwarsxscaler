import React, { useState, useCallback, useRef } from 'react'

/**
 * UploadZone — Drag-and-drop file upload with keyboard accessibility.
 * Accepts PDF and DOCX files up to 10MB.
 *
 * @param {Object} props
 * @param {Function} props.onAnalyze - Callback when file is ready for analysis
 */
export default function UploadZone({ onAnalyze }) {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragError, setDragError] = useState('')
  const fileInputRef = useRef(null)

  const ACCEPTED_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ]
  const ACCEPTED_EXTENSIONS = ['.pdf', '.docx']
  const MAX_SIZE_MB = 10

  /** Validate selected file */
  const validateFile = useCallback((selectedFile) => {
    setDragError('')
    if (!selectedFile) return false

    const ext = '.' + selectedFile.name.split('.').pop().toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      setDragError(`Unsupported format "${ext}". Please upload PDF or DOCX.`)
      return false
    }
    if (selectedFile.size > MAX_SIZE_MB * 1024 * 1024) {
      setDragError(`File exceeds ${MAX_SIZE_MB}MB limit.`)
      return false
    }
    return true
  }, [])

  /** Handle file drop */
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (validateFile(dropped)) setFile(dropped)
  }, [validateFile])

  /** Handle file input change */
  const handleFileChange = useCallback((e) => {
    const selected = e.target.files[0]
    if (validateFile(selected)) setFile(selected)
  }, [validateFile])

  /** Handle keyboard activation on dropzone */
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      fileInputRef.current?.click()
    }
  }, [])

  const fileSizeDisplay = file
    ? (file.size / (1024 * 1024)).toFixed(2) + ' MB'
    : ''

  return (
    <section className="animate-fade-in-up max-w-2xl mx-auto" aria-label="Document upload">
      {/* Hero text */}
      <div className="text-center mb-10">
        <h2 className="text-4xl sm:text-5xl font-extrabold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
          Analyze Your Contract
        </h2>
        <p className="text-lexguard-muted text-lg max-w-lg mx-auto">
          Upload a legal document and our adversarial AI agents will debate every clause to find hidden risks before you sign.
        </p>
      </div>

      {/* Dropzone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Drop zone: drag and drop a PDF or DOCX file, or press Enter to browse"
        className={`
          glass-card p-12 text-center cursor-pointer transition-all duration-300
          border-2 border-dashed hover:border-lexguard-accent hover:shadow-lg hover:shadow-lexguard-accent/10
          ${isDragging ? 'dropzone-active border-lexguard-accent scale-[1.02]' : 'border-lexguard-border'}
          ${file ? 'border-green-500/50' : ''}
        `}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={handleKeyDown}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="hidden"
          aria-hidden="true"
          id="file-upload-input"
        />

        {!file ? (
          <>
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
              <svg className="w-10 h-10 text-lexguard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-lg font-semibold text-lexguard-text mb-2">
              {isDragging ? 'Drop your file here' : 'Drag & drop your contract'}
            </p>
            <p className="text-sm text-lexguard-muted">or click to browse files</p>
          </>
        ) : (
          <div className="flex items-center justify-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-green-500/10 flex items-center justify-center">
              <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-left">
              <p className="font-semibold text-lexguard-text">{file.name}</p>
              <p className="text-sm text-lexguard-muted">{fileSizeDisplay}</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null) }}
              className="ml-4 p-2 rounded-lg hover:bg-lexguard-surface-2 text-lexguard-muted hover:text-risk-high transition-colors"
              aria-label="Remove selected file"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Error message */}
      {dragError && (
        <p className="mt-3 text-sm text-risk-high text-center" role="alert">{dragError}</p>
      )}

      {/* Supported types */}
      <div className="mt-6 flex flex-wrap justify-center gap-3 text-xs text-lexguard-muted">
        {['Employment Contracts', 'Freelance Agreements', 'Rental Agreements', 'Subscription T&Cs', 'Vendor Agreements', 'Privacy Policies'].map(type => (
          <span key={type} className="px-3 py-1.5 rounded-full bg-lexguard-surface-2 border border-lexguard-border/50">
            {type}
          </span>
        ))}
      </div>

      {/* Analyze button */}
      <div className="mt-8 text-center">
        <button
          onClick={() => file && onAnalyze(file)}
          disabled={!file}
          className={`
            px-8 py-3.5 rounded-xl font-semibold text-white transition-all duration-300
            ${file
              ? 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:scale-[1.02] animate-pulse-glow'
              : 'bg-lexguard-surface-2 text-lexguard-muted cursor-not-allowed border border-lexguard-border'}
          `}
          aria-label={file ? `Analyze ${file.name}` : 'Select a file first'}
          id="analyze-button"
        >
          <span className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Analyze Contract
          </span>
        </button>
      </div>
    </section>
  )
}
