'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Scale, AlertTriangle, Shield, Coins, ChevronDown, ChevronUp } from 'lucide-react'
import { ALGORAND_2025_RESEARCH } from '@/lib/algorand-2025-research'

// ============================================================================
// Types
// ============================================================================

interface KingSafetyAlertProps {
  className?: string
  expanded?: boolean
}

// ============================================================================
// Sub-components
// ============================================================================

function ArgumentCard({
  title,
  icon,
  arguments: args,
  variant
}: {
  title: string
  icon: React.ReactNode
  arguments: string[]
  variant: 'for' | 'against'
}) {
  const bgColor = variant === 'for' ? 'bg-cyan-500/10' : 'bg-orange-500/10'
  const borderColor = variant === 'for' ? 'border-cyan-500/30' : 'border-orange-500/30'
  const textColor = variant === 'for' ? 'text-cyan-400' : 'text-orange-400'
  const bulletColor = variant === 'for' ? 'bg-cyan-500' : 'bg-orange-500'

  return (
    <div className={`rounded-lg p-4 ${bgColor} border ${borderColor}`}>
      <h4 className={`font-semibold ${textColor} flex items-center gap-2 mb-3`}>
        {icon}
        {title}
      </h4>
      <ul className="space-y-2">
        {args.map((arg, idx) => (
          <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
            <span className={`w-1.5 h-1.5 rounded-full ${bulletColor} mt-2 flex-shrink-0`} />
            {arg}
          </li>
        ))}
      </ul>
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function KingSafetyAlert({ className = '', expanded: defaultExpanded = true }: KingSafetyAlertProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const data = ALGORAND_2025_RESEARCH.projectKingSafety

  return (
    <Card className={`border-2 border-amber-500/50 bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/20 overflow-hidden ${className}`}>
      {/* Animated top border accent */}
      <div className="h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-red-500" />

      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5">
                CRITICAL DEBATE
              </Badge>
              <Badge className="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5">
                2027 DEADLINE
              </Badge>
            </div>
            <CardTitle className="text-2xl flex items-center gap-3 mt-2">
              <Scale className="h-7 w-7 text-amber-500" />
              Project King Safety
            </CardTitle>
            <CardDescription className="text-base text-slate-400">
              The 10 Billion ALGO Supply Cap Controversy
            </CardDescription>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-slate-400 hover:text-white"
          >
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* The Issue - Always visible */}
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">The Issue</div>
              <p className="text-slate-200 font-medium">{data.issue}</p>
            </div>
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">The Proposal</div>
              <p className="text-slate-200 font-medium">{data.proposal}</p>
            </div>
          </div>
        </div>

        {isExpanded && (
          <>
            {/* FOR vs AGAINST Arguments */}
            <div className="grid md:grid-cols-2 gap-4">
              <ArgumentCard
                title="Security View"
                icon={<Shield className="h-5 w-5" />}
                arguments={data.forArguments}
                variant="for"
              />
              <ArgumentCard
                title="Sound Money View"
                icon={<Coins className="h-5 w-5" />}
                arguments={data.againstArguments}
                variant="against"
              />
            </div>

            {/* Alternative Solutions */}
            <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700">
              <h4 className="font-semibold text-slate-300 mb-2 flex items-center gap-2">
                <span className="text-lg">💡</span>
                Alternative Solutions Being Discussed
              </h4>
              <div className="flex flex-wrap gap-2">
                {data.alternatives.map((alt, idx) => (
                  <Badge key={idx} variant="outline" className="text-slate-300 border-slate-600">
                    {alt}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Sovereignty Analysis - THE MOST IMPORTANT PART */}
            <div className="relative overflow-hidden rounded-lg">
              {/* Background gradient */}
              <div className="absolute inset-0 bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-red-500/10" />

              <div className="relative p-5 border-2 border-amber-500/40 rounded-lg">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-amber-500/20 rounded-lg">
                    <AlertTriangle className="h-6 w-6 text-amber-500" />
                  </div>
                  <div className="flex-1 space-y-3">
                    <h4 className="font-bold text-lg text-amber-400">
                      Sovereignty Analysis
                    </h4>
                    <p className="text-slate-200 leading-relaxed">
                      {data.sovereigntyAnalysis}
                    </p>
                    <div className="pt-2 space-y-2">
                      <p className="text-sm text-slate-400">
                        <strong className="text-slate-200">Our Position:</strong> For a hard money advocate, this is the central question.
                        Bitcoin maximalists will argue that any supply uncapping is an immediate disqualification from "sound money" status.
                        Pragmatists counter that a dead network stores no value. The truth is this: <span className="text-amber-400 font-medium">if Algorand uncaps,
                        it becomes a utility token, not a store of value.</span>
                      </p>
                      <p className="text-sm text-slate-400">
                        <strong className="text-slate-200">What this means for you:</strong> If you're holding ALGO as a
                        <span className="text-green-400"> sovereignty asset</span>, this vote will determine if it stays in that category.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Vote Requirement */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-800/50 rounded-lg p-4 border border-slate-700">
              <div className="text-center sm:text-left">
                <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Required to Pass</div>
                <p className="text-xl font-bold text-slate-200">
                  {data.voteRequirement}
                </p>
              </div>

              <a
                href="https://www.reddit.com/r/AlgorandOfficial/comments/1pkdpi8/update_on_the_status_of_the_project_king_safety/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 rounded-lg transition-colors border border-orange-500/30"
              >
                <span className="text-lg">📖</span>
                Read Full Discussion
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>

            {/* Timeline */}
            <div className="text-center pt-2">
              <div className="inline-flex items-center gap-2 text-sm text-slate-500">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                Foundation treasury depletes: <span className="text-red-400 font-semibold">~January 2027</span>
              </div>
            </div>
          </>
        )}

        {!isExpanded && (
          <Button
            variant="outline"
            className="w-full border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
            onClick={() => setIsExpanded(true)}
          >
            Expand Full Analysis
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Compact Version for sidebars/summaries
// ============================================================================

export function KingSafetyCompact({ className = '' }: { className?: string }) {
  const data = ALGORAND_2025_RESEARCH.projectKingSafety

  return (
    <Card className={`border-amber-500/40 bg-amber-500/5 ${className}`}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3 mb-3">
          <Scale className="h-5 w-5 text-amber-500" />
          <span className="font-semibold text-amber-400">Project King Safety</span>
          <Badge className="bg-red-500/20 text-red-400 text-xs ml-auto">2027</Badge>
        </div>
        <p className="text-sm text-slate-400 mb-3">
          {data.issue}. Community vote on supply cap removal expected.
        </p>
        <a
          href="https://www.reddit.com/r/AlgorandOfficial/comments/1pkdpi8/update_on_the_status_of_the_project_king_safety/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-amber-500 hover:text-amber-400 flex items-center gap-1"
        >
          Learn more <ExternalLink className="h-3 w-3" />
        </a>
      </CardContent>
    </Card>
  )
}

export default KingSafetyAlert
