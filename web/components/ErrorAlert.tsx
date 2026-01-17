'use client'

import { AlertTriangle, RefreshCcw, X, Wifi, Server, Key } from 'lucide-react'
import { cn } from '@/lib/utils'

type ErrorType = 'network' | 'server' | 'validation' | 'auth' | 'generic'

interface ErrorAlertProps {
  message: string
  type?: ErrorType
  onRetry?: () => void
  onDismiss?: () => void
  retrying?: boolean
  className?: string
}

const errorConfig: Record<ErrorType, { icon: typeof AlertTriangle; title: string; color: string }> = {
  network: {
    icon: Wifi,
    title: 'Connection Error',
    color: 'orange',
  },
  server: {
    icon: Server,
    title: 'Server Error',
    color: 'red',
  },
  validation: {
    icon: AlertTriangle,
    title: 'Invalid Input',
    color: 'yellow',
  },
  auth: {
    icon: Key,
    title: 'Authentication Error',
    color: 'purple',
  },
  generic: {
    icon: AlertTriangle,
    title: 'Error',
    color: 'red',
  },
}

function getErrorType(message: string): ErrorType {
  const lowerMessage = message.toLowerCase()
  // Rate limit detection
  if (lowerMessage.includes('rate') || lowerMessage.includes('429') || lowerMessage.includes('too many') || lowerMessage.includes('throttl')) {
    return 'network' // Treat rate limits as temporary network issues
  }
  if (lowerMessage.includes('network') || lowerMessage.includes('timeout') || lowerMessage.includes('fetch')) {
    return 'network'
  }
  if (lowerMessage.includes('server') || lowerMessage.includes('500') || lowerMessage.includes('503')) {
    return 'server'
  }
  if (lowerMessage.includes('invalid') || lowerMessage.includes('not found') || lowerMessage.includes('empty')) {
    return 'validation'
  }
  if (lowerMessage.includes('auth') || lowerMessage.includes('unauthorized') || lowerMessage.includes('403')) {
    return 'auth'
  }
  return 'generic'
}

function isRateLimitError(message: string): boolean {
  const lowerMessage = message.toLowerCase()
  return lowerMessage.includes('rate') || lowerMessage.includes('429') || lowerMessage.includes('too many') || lowerMessage.includes('throttl')
}

export function ErrorAlert({
  message,
  type,
  onRetry,
  onDismiss,
  retrying = false,
  className,
}: ErrorAlertProps) {
  const errorType = type || getErrorType(message)
  const config = errorConfig[errorType]
  const Icon = config.icon

  const colorClasses = {
    red: 'bg-red-500/10 border-red-500/30 text-red-300',
    orange: 'bg-orange-500/10 border-orange-500/30 text-orange-300',
    yellow: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300',
    purple: 'bg-purple-500/10 border-purple-500/30 text-purple-300',
  }

  const iconColorClasses = {
    red: 'text-red-400',
    orange: 'text-orange-400',
    yellow: 'text-yellow-400',
    purple: 'text-purple-400',
  }

  return (
    <div
      className={cn(
        'rounded-lg border p-4',
        colorClasses[config.color as keyof typeof colorClasses],
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={cn('h-5 w-5 mt-0.5 flex-shrink-0', iconColorClasses[config.color as keyof typeof iconColorClasses])} />
        <div className="flex-1 min-w-0">
          <h3 className="font-medium">{config.title}</h3>
          <p className="mt-1 text-sm text-slate-400">{message}</p>

          {errorType === 'validation' && message.toLowerCase().includes('not found') && (
            <p className="mt-2 text-xs text-slate-500">
              Please check that the wallet address is correct and try again.
            </p>
          )}

          {errorType === 'network' && (
            <p className="mt-2 text-xs text-slate-500">
              {isRateLimitError(message)
                ? 'The service is rate limited. Please wait a moment before trying again.'
                : 'Check your internet connection or try again in a few moments.'}
            </p>
          )}

          {(onRetry || onDismiss) && (
            <div className="mt-3 flex items-center gap-2">
              {onRetry && (
                <button
                  onClick={onRetry}
                  disabled={retrying}
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium',
                    'bg-slate-800 hover:bg-slate-700 border border-slate-700',
                    'text-white transition-colors',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  <RefreshCcw className={cn('h-3.5 w-3.5', retrying && 'animate-spin')} />
                  {retrying ? 'Retrying...' : 'Try again'}
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="text-sm text-slate-500 hover:text-white transition-colors"
                >
                  Dismiss
                </button>
              )}
            </div>
          )}
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-slate-500 hover:text-white transition-colors"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}
