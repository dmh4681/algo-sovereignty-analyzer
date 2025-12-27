/**
 * Badge Configuration for Sovereignty Achievement System
 * File: web/lib/badge-config.ts
 */

export interface BadgeDefinition {
  id: string
  name: string
  emoji: string
  description: string
  requirement: string
  ratioNeeded: number | null  // null for hard_money_maxi (percentage based)
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  image: string
  color: string
  checkEligibility: (sovereigntyRatio: number, hardMoneyPercentage: number) => boolean
}

export const BADGE_DEFINITIONS: BadgeDefinition[] = [
  {
    id: 'fragile',
    name: 'Fragile',
    emoji: '🔴',
    description: 'Reached 1+ years of sovereignty runway',
    requirement: '1.0+ years',
    ratioNeeded: 1.0,
    rarity: 'common',
    image: '/badges/fragile.png',
    color: '#ef4444',
    checkEligibility: (ratio) => ratio >= 1.0
  },
  {
    id: 'robust',
    name: 'Robust',
    emoji: '🟡',
    description: 'Reached 3+ years of sovereignty runway',
    requirement: '3.0+ years',
    ratioNeeded: 3.0,
    rarity: 'rare',
    image: '/badges/robust.png',
    color: '#f59e0b',
    checkEligibility: (ratio) => ratio >= 3.0
  },
  {
    id: 'antifragile',
    name: 'Antifragile',
    emoji: '🟢',
    description: 'Reached 6+ years of sovereignty runway',
    requirement: '6.0+ years',
    ratioNeeded: 6.0,
    rarity: 'epic',
    image: '/badges/antifragile.png',
    color: '#22c55e',
    checkEligibility: (ratio) => ratio >= 6.0
  },
  {
    id: 'generational',
    name: 'Generationally Sovereign',
    emoji: '👑',
    description: 'Reached 20+ years of sovereignty runway',
    requirement: '20+ years',
    ratioNeeded: 20.0,
    rarity: 'legendary',
    image: '/badges/generational.png',
    color: '#10b981',
    checkEligibility: (ratio) => ratio >= 20.0
  },
  {
    id: 'hard_money_maxi',
    name: 'Hard Money Maximalist',
    emoji: '💎',
    description: '100% of portfolio in hard money assets',
    requirement: '100% hard money',
    ratioNeeded: null,
    rarity: 'legendary',
    image: '/badges/hard_money_maxi.png',
    color: '#06b6d4',
    checkEligibility: (_, hardMoneyPct) => hardMoneyPct >= 99.9
  }
]

/**
 * Get all badges the user has earned
 */
export function getEarnedBadges(
  sovereigntyRatio: number, 
  hardMoneyPct: number
): BadgeDefinition[] {
  return BADGE_DEFINITIONS.filter(badge => 
    badge.checkEligibility(sovereigntyRatio, hardMoneyPct)
  )
}

/**
 * Get all badges with earned status
 */
export function getBadgesWithStatus(
  sovereigntyRatio: number,
  hardMoneyPct: number
): Array<BadgeDefinition & { earned: boolean }> {
  return BADGE_DEFINITIONS.map(badge => ({
    ...badge,
    earned: badge.checkEligibility(sovereigntyRatio, hardMoneyPct)
  }))
}

/**
 * Get the next badge the user can earn (ratio-based only)
 */
export function getNextRatioBadge(
  sovereigntyRatio: number
): BadgeDefinition | null {
  const ratioBadges = BADGE_DEFINITIONS.filter(b => b.ratioNeeded !== null)
  const unearned = ratioBadges.filter(badge => sovereigntyRatio < (badge.ratioNeeded || 0))
  return unearned[0] || null
}

/**
 * Calculate progress to next badge (0-100)
 */
export function getProgressToNextBadge(
  sovereigntyRatio: number
): { badge: BadgeDefinition; progress: number; remaining: number } | null {
  const nextBadge = getNextRatioBadge(sovereigntyRatio)
  if (!nextBadge || nextBadge.ratioNeeded === null) return null
  
  // Find the previous threshold
  const badgeIndex = BADGE_DEFINITIONS.findIndex(b => b.id === nextBadge.id)
  const prevThreshold = badgeIndex > 0 
    ? BADGE_DEFINITIONS[badgeIndex - 1].ratioNeeded || 0 
    : 0
  
  const range = nextBadge.ratioNeeded - prevThreshold
  const current = sovereigntyRatio - prevThreshold
  const progress = Math.min(100, Math.max(0, (current / range) * 100))
  const remaining = nextBadge.ratioNeeded - sovereigntyRatio
  
  return { badge: nextBadge, progress, remaining }
}

/**
 * Get Tailwind styles based on rarity
 */
export function getRarityStyles(rarity: BadgeDefinition['rarity']) {
  switch (rarity) {
    case 'common':
      return {
        border: 'border-slate-400',
        glow: 'shadow-slate-400/20',
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        gradient: 'from-slate-500 to-slate-600'
      }
    case 'rare':
      return {
        border: 'border-blue-500',
        glow: 'shadow-blue-500/30',
        bg: 'bg-blue-500/10',
        text: 'text-blue-400',
        gradient: 'from-blue-500 to-blue-600'
      }
    case 'epic':
      return {
        border: 'border-purple-500',
        glow: 'shadow-purple-500/40',
        bg: 'bg-purple-500/10',
        text: 'text-purple-400',
        gradient: 'from-purple-500 to-purple-600'
      }
    case 'legendary':
      return {
        border: 'border-orange-500',
        glow: 'shadow-orange-500/50',
        bg: 'bg-orange-500/10',
        text: 'text-orange-400',
        gradient: 'from-orange-500 to-yellow-500'
      }
  }
}

/**
 * Get rarity label with styling
 */
export function getRarityLabel(rarity: BadgeDefinition['rarity']): string {
  return rarity.charAt(0).toUpperCase() + rarity.slice(1)
}

/**
 * Local storage key for tracking newly earned badges
 */
const EARNED_BADGES_KEY = 'sovereignty_earned_badges'

/**
 * Check if any badges are newly earned (for celebration)
 */
export function checkForNewBadges(
  address: string,
  currentEarned: string[]
): string[] {
  const storageKey = `${EARNED_BADGES_KEY}_${address}`
  const previousEarned = JSON.parse(localStorage.getItem(storageKey) || '[]')
  const newBadges = currentEarned.filter(id => !previousEarned.includes(id))
  
  // Update storage
  localStorage.setItem(storageKey, JSON.stringify(currentEarned))
  
  return newBadges
}
