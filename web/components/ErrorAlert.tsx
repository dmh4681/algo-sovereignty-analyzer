'use client'

import { AlertTriangle, RefreshCcw, X, Wifi, Server, Key } from 'lucide-react'
import { cn } from '@/lib/utils'

/** The five error categories that determine the alert's icon, color, and help text. */
type ErrorType = 'network' | 'server' | 'validation' | 'auth' | 'generic'

/**
 * Props for the {@link ErrorAlert} component.
 *
 * @property message - The error message to display. Also used for auto-detection
 *   of error type if `type` is not explicitly provided.
 * @property type - Explicit error type override. If omitted, the type is
 *   auto-detected from the message content using keyword matching.
 * @property onRetry - Callback for the "Try again" button. If not provided,
 *   the retry button is hidden.
 * @property onDismiss - Callback for the dismiss button (X icon). If not provided,
 *   the dismiss button is hidden.
 * @property retrying - When true, shows a spinning animation on the retry button
 *   and disables it. Defaults to false.
 * @property className - Additional CSS classes to merge with the alert container.
 */
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

/**
 * Auto-detects the error type from the error message content using keyword matching.
 *
 * Detection priority (first match wins):
 * 1. Rate limiting: "rate", "429", "too many", "throttl" -> network
 * 2. Network issues: "network", "timeout", "fetch" -> network
 * 3. Server errors: "server", "500", "503" -> server
 * 4. Validation: "invalid", "not found", "empty" -> validation
 * 5. Auth: "auth", "unauthorized", "403" -> auth
 * 6. Default: generic
 *
 * @param message - The error message string to analyze
 * @returns The detected ErrorType
 */
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

/**
 * Checks if an error message indicates a rate limit condition. Used to show
 * specific help text ("wait a moment") instead of generic network error advice.
 *
 * @param message - The error message to check
 * @returns True if the message contains rate-limiting keywords
 */
function isRateLimitError(message: string): boolean {
  const lowerMessage = message.toLowerCase()
  return lowerMessage.includes('rate') || lowerMessage.includes('429') || lowerMessage.includes('too many') || lowerMessage.includes('throttl')
}

/**
 * A color-coded, accessible error alert with auto-detection of error types,
 * contextual help text, and optional retry/dismiss actions.
 *
 * The component renders a rounded card with:
 * - Type-specific icon (Wifi, Server, AlertTriangle, Key)
 * - Type-specific title (e.g., "Connection Error", "Server Error")
 * - The error message
 * - Contextual help text based on error type:
 *   - Validation + "not found": suggests checking the wallet address
 *   - Network + rate limit: suggests waiting before retrying
 *   - Network (general): suggests checking internet connection
 * - Retry button with spinning animation when `retrying` is true
 * - Dismiss button (both inline and corner X icon)
 *
 * Color coding: network=orange, server=red, validation=yellow,
 * auth=purple, generic=red.
 *
 * Accessibility: Uses `role="alert"` for screen reader announcements and
 * `aria-label="Dismiss"` on the close button.
 *
 * @param props - Component props
 *
 * @example
 * ```tsx
 * <ErrorAlert
 *   message="Failed to fetch wallet data"
 *   onRetry={() => refetch()}
 *   retrying={isRetrying}
 * />
 * ```
 */
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
