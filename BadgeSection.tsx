/**
 * Badge Section Component - Displays sovereignty achievement badges
 * File: web/components/BadgeSection.tsx
 */

'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { 
  BADGE_DEFINITIONS,
  getBadgesWithStatus,
  getProgressToNextBadge,
  getRarityStyles,
  getRarityLabel,
  checkForNewBadges,
  type BadgeDefinition
} from '@/lib/badge-config'

interface BadgeSectionProps {
  sovereigntyRatio: number
  hardMoneyPercentage: number
  walletAddress?: string
}

interface BadgeWithStatus extends BadgeDefinition {
  earned: boolean
}

export function BadgeSection({ 
  sovereigntyRatio, 
  hardMoneyPercentage,
  walletAddress 
}: BadgeSectionProps) {
  const [badges, setBadges] = useState<BadgeWithStatus[]>([])
  const [earnedCount, setEarnedCount] = useState(0)
  const [newlyEarned, setNewlyEarned] = useState<string[]>([])
  const [showCelebration, setShowCelebration] = useState(false)
  
  useEffect(() => {
    const badgesWithStatus = getBadgesWithStatus(sovereigntyRatio, hardMoneyPercentage)
    setBadges(badgesWithStatus)
    
    const earned = badgesWithStatus.filter(b => b.earned)
    setEarnedCount(earned.length)
    
    // Check for newly earned badges
    if (walletAddress) {
      const earnedIds = earned.map(b => b.id)
      const newBadges = checkForNewBadges(walletAddress, earnedIds)
      if (newBadges.length > 0) {
        setNewlyEarned(newBadges)
        setShowCelebration(true)
        // Hide celebration after 5 seconds
        setTimeout(() => setShowCelebration(false), 5000)
      }
    }
  }, [sovereigntyRatio, hardMoneyPercentage, walletAddress])
  
  const nextBadgeProgress = getProgressToNextBadge(sovereigntyRatio)
  
  return (
    <Card className="border-orange-500/20 bg-slate-900/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-2xl">
              🏆 Sovereignty Badges
            </CardTitle>
            <CardDescription className="mt-1">
              Earn badges by reaching sovereignty milestones
            </CardDescription>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-400">Earned</div>
            <div className="text-3xl font-bold text-orange-500">
              {earnedCount}<span className="text-lg text-slate-500">/{badges.length}</span>
            </div>
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="mt-4">
          <Progress 
            value={(earnedCount / badges.length) * 100} 
            className="h-2 bg-slate-700"
          />
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Celebration banner for new badges */}
        {showCelebration && newlyEarned.length > 0 && (
          <div className="mb-6 p-4 bg-gradient-to-r from-orange-500/20 to-yellow-500/20 border border-orange-500/30 rounded-lg text-center animate-pulse">
            <div className="text-2xl mb-2">🎉</div>
            <div className="font-bold text-orange-400">
              Congratulations! You just earned {newlyEarned.length} new badge{newlyEarned.length > 1 ? 's' : ''}!
            </div>
            <div className="text-sm text-slate-300 mt-1">
              {newlyEarned.map(id => badges.find(b => b.id === id)?.name).join(', ')}
            </div>
          </div>
        )}
        
        {/* Badge Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {badges.map(badge => (
            <BadgeCard key={badge.id} badge={badge} isNew={newlyEarned.includes(badge.id)} />
          ))}
        </div>
        
        {/* Next Badge Progress */}
        {nextBadgeProgress && earnedCount < badges.length - 1 && (
          <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Next badge:</span>
              <span className="font-semibold text-slate-200">
                {nextBadgeProgress.badge.name}
              </span>
            </div>
            <Progress 
              value={nextBadgeProgress.progress} 
              className="h-3 bg-slate-700"
            />
            <div className="flex justify-between mt-2 text-xs text-slate-400">
              <span>{sovereigntyRatio.toFixed(1)} years</span>
              <span>{nextBadgeProgress.remaining.toFixed(1)} more to go</span>
              <span>{nextBadgeProgress.badge.ratioNeeded} years</span>
            </div>
          </div>
        )}
        
        {/* All badges earned */}
        {earnedCount === badges.length && (
          <div className="mt-6 p-6 bg-gradient-to-r from-orange-500/10 to-yellow-500/10 border border-orange-500/20 rounded-lg text-center">
            <div className="text-4xl mb-2">👑</div>
            <div className="text-xl font-bold text-orange-400 mb-1">Badge Master!</div>
            <div className="text-slate-300">
              You've earned all sovereignty badges. True financial freedom achieved.
            </div>
          </div>
        )}
        
        {/* NFT Teaser */}
        <div className="mt-6 pt-4 border-t border-slate-700 text-center">
          <p className="text-xs text-slate-500">
            🔮 NFT minting coming soon — claim your badges on-chain
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

// Individual Badge Card Component
function BadgeCard({ badge, isNew }: { badge: BadgeWithStatus; isNew: boolean }) {
  const rarityStyles = getRarityStyles(badge.rarity)
  
  return (
    <div
      className={`
        relative rounded-xl p-3 text-center transition-all duration-300
        ${badge.earned 
          ? `border-2 ${rarityStyles.border} ${rarityStyles.bg} shadow-lg ${rarityStyles.glow}` 
          : 'border border-slate-700 bg-slate-800/30 opacity-50 grayscale'
        }
        ${isNew ? 'ring-2 ring-orange-400 ring-offset-2 ring-offset-slate-900 animate-bounce' : ''}
        hover:scale-105
      `}
    >
      {/* Badge Image */}
      <div className="relative w-full aspect-square mb-2">
        <Image
          src={badge.image}
          alt={badge.name}
          fill
          className="object-contain"
          sizes="(max-width: 640px) 40vw, (max-width: 1024px) 25vw, 15vw"
        />
      </div>
      
      {/* Badge Name */}
      <div className="text-sm font-bold text-slate-200 line-clamp-2 min-h-[2.5rem]">
        {badge.name}
      </div>
      
      {/* Requirement */}
      <div className="text-xs text-slate-400 mb-2">
        {badge.requirement}
      </div>
      
      {/* Rarity Tag */}
      <div className={`
        text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full inline-block
        ${rarityStyles.bg} ${rarityStyles.text}
      `}>
        {getRarityLabel(badge.rarity)}
      </div>
      
      {/* Earned Checkmark */}
      {badge.earned && (
        <div className="absolute -top-2 -right-2 bg-green-500 rounded-full w-6 h-6 flex items-center justify-center shadow-lg">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}
      
      {/* Locked Icon for unearned */}
      {!badge.earned && (
        <div className="absolute -top-2 -right-2 bg-slate-600 rounded-full w-6 h-6 flex items-center justify-center">
          <svg className="w-3 h-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
      )}
    </div>
  )
}
