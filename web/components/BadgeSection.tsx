'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useWallet } from '@txnlab/use-wallet-react'
import { BADGE_DEFINITIONS, getRarityColor, getRarityGlow } from '@/lib/badge-config'
import type { BadgeDefinition } from '@/lib/badge-config'
import Image from 'next/image'

interface BadgeSectionProps {
  sovereigntyRatio: number
  hardMoneyPercentage: number
}

interface BadgeStatus extends BadgeDefinition {
  achieved: boolean
}

export function BadgeSection({ sovereigntyRatio, hardMoneyPercentage }: BadgeSectionProps) {
  const { activeAccount } = useWallet()
  const [badges, setBadges] = useState<BadgeStatus[]>([])
  const [achievedCount, setAchievedCount] = useState(0)
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({})

  useEffect(() => {
    // Calculate which badges are achieved
    const badgeStatuses = BADGE_DEFINITIONS.map(badge => ({
      ...badge,
      achieved: badge.checkEligibility(sovereigntyRatio, hardMoneyPercentage)
    }))

    setBadges(badgeStatuses)
    setAchievedCount(badgeStatuses.filter(b => b.achieved).length)
  }, [sovereigntyRatio, hardMoneyPercentage])

  const handleClaimBadge = async (badgeId: string) => {
    if (!activeAccount) {
      alert('Please connect your wallet to claim badges')
      return
    }

    // TODO: Implement actual NFT minting
    // For now, just show success message
    const badge = badges.find(b => b.id === badgeId)
    alert(`Badge Earned!\n\nYou've achieved the ${badge?.name} badge!\n\n(NFT minting coming soon - this will be minted to your wallet)`)
  }

  const handleImageError = (badgeId: string) => {
    setImageErrors(prev => ({ ...prev, [badgeId]: true }))
  }

  return (
    <Card className="mt-6 border-orange-500/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-2xl">
              Sovereignty Badges
            </CardTitle>
            <CardDescription className="mt-2">
              Earn achievement badges by reaching sovereignty milestones
            </CardDescription>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-400">Earned</div>
            <div className="text-3xl font-bold text-orange-500">
              {achievedCount}/{badges.length}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {badges.map(badge => {
            const borderColor = getRarityColor(badge.rarity)
            const glowEffect = getRarityGlow(badge.rarity)
            const hasImageError = imageErrors[badge.id]

            return (
              <div
                key={badge.id}
                className={`
                  relative border-2 rounded-xl p-4 text-center transition-all duration-300
                  ${badge.achieved
                    ? `${borderColor} ${glowEffect} shadow-lg bg-gradient-to-b from-slate-800 to-slate-900`
                    : 'border-slate-700 bg-slate-800/30 opacity-40 grayscale'
                  }
                `}
              >
                {/* Badge Image or Emoji Fallback */}
                <div className="mb-3 relative w-full aspect-square flex items-center justify-center">
                  {!hasImageError ? (
                    <Image
                      src={badge.image}
                      alt={badge.name}
                      fill
                      className="object-contain"
                      onError={() => handleImageError(badge.id)}
                    />
                  ) : (
                    <span className="text-5xl">{badge.emoji}</span>
                  )}
                </div>

                {/* Badge Info */}
                <div className="text-sm font-bold mb-1 line-clamp-2 min-h-[2.5rem]">
                  {badge.name}
                </div>
                <div className="text-xs text-slate-400 mb-3">
                  {badge.requirement}
                </div>

                {/* Rarity Indicator */}
                <div className={`
                  text-[10px] uppercase font-semibold mb-3 px-2 py-1 rounded-full inline-block
                  ${badge.rarity === 'legendary' ? 'bg-orange-500/20 text-orange-400' : ''}
                  ${badge.rarity === 'epic' ? 'bg-purple-500/20 text-purple-400' : ''}
                  ${badge.rarity === 'rare' ? 'bg-blue-500/20 text-blue-400' : ''}
                  ${badge.rarity === 'common' ? 'bg-slate-500/20 text-slate-400' : ''}
                `}>
                  {badge.rarity}
                </div>

                {/* Claim Button or Status */}
                {badge.achieved ? (
                  <Button
                    size="sm"
                    onClick={() => handleClaimBadge(badge.id)}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-xs font-semibold"
                  >
                    Claim NFT
                  </Button>
                ) : (
                  <div className="text-xs text-slate-500 font-medium">
                    Not Yet Earned
                  </div>
                )}

                {/* Achievement Checkmark */}
                {badge.achieved && (
                  <div className="absolute -top-2 -right-2 bg-green-500 rounded-full w-7 h-7 flex items-center justify-center shadow-lg">
                    <span className="text-white text-sm">&#10003;</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Footer Info */}
        <div className="mt-6 pt-6 border-t border-slate-700 text-center">
          {!activeAccount ? (
            <p className="text-sm text-slate-400">
              Connect your wallet to claim achievement badges as NFTs
            </p>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-slate-300">
                Achievement NFTs will be minted to: <span className="font-mono text-orange-400">{activeAccount.address.slice(0, 8)}...</span>
              </p>
              <p className="text-xs text-slate-500">
                (NFT minting functionality coming soon)
              </p>
            </div>
          )}
        </div>

        {/* Progress Indicator */}
        {achievedCount > 0 && achievedCount < badges.length && (
          <div className="mt-4 text-center">
            <div className="text-sm text-slate-400 mb-2">
              Keep stacking hard money to unlock more badges!
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-orange-500 to-orange-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(achievedCount / badges.length) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* All Badges Earned */}
        {achievedCount === badges.length && (
          <div className="mt-4 bg-gradient-to-r from-orange-500/10 to-orange-600/10 border border-orange-500/20 rounded-lg p-4 text-center">
            <div className="font-bold text-orange-400 mb-1">Badge Master!</div>
            <div className="text-sm text-slate-300">You've earned all sovereignty badges</div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
