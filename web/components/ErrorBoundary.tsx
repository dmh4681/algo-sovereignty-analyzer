'use client'

import React, { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCcw, Home, Bug } from 'lucide-react'
import Link from 'next/link'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo })

    console.error('[ErrorBoundary] Caught error:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
    })

    this.props.onError?.(error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md w-full">
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/20">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>

              <h2 className="text-lg font-semibold text-red-300 mb-2">
                Something went wrong
              </h2>

              <p className="text-sm text-slate-400 mb-4">
                {this.state.error?.message || 'An unexpected error occurred while analyzing your wallet'}
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <button
                  onClick={this.handleReset}
                  className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white transition-colors"
                >
                  <RefreshCcw className="h-4 w-4" />
                  Try again
                </button>

                <Link
                  href="/"
                  className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
                >
                  <Home className="h-4 w-4" />
                  Go Home
                </Link>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="flex items-center gap-2 text-xs text-slate-500 cursor-pointer hover:text-slate-300">
                    <Bug className="h-3 w-3" />
                    Developer Details
                  </summary>
                  <pre className="mt-2 p-3 rounded bg-slate-900 text-xs text-red-300 overflow-auto max-h-48">
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
