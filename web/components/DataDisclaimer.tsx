'use client'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertTriangle } from 'lucide-react'

interface DataDisclaimerProps {
  compact?: boolean
  className?: string
}

export function DataDisclaimer({ compact = false, className = '' }: DataDisclaimerProps) {
  if (compact) {
    return (
      <p className={`text-xs text-slate-500 italic ${className}`}>
        Data for illustrative purposes only. Verify with official sources before making financial decisions.
      </p>
    )
  }

  return (
    <Alert className={`bg-amber-900/20 border-amber-500/30 ${className}`}>
      <AlertTriangle className="h-4 w-4 text-amber-500" />
      <AlertTitle className="text-amber-400">Data Disclaimer</AlertTitle>
      <AlertDescription className="text-amber-200/80">
        The data shown on this page is for illustrative purposes only. Some values are estimates
        that may not reflect current market conditions. Do not make financial decisions based solely
        on this data. Always verify prices, holdings, and metrics with official sources before taking action.
      </AlertDescription>
    </Alert>
  )
}
