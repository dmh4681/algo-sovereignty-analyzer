export interface BadgeDefinition {
  id: string
  name: string
  emoji: string
  description: string
  requirement: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  image: string
  checkEligibility: (sovereigntyRatio: number, hardMoneyPercentage: number) => boolean
}

export const BADGE_DEFINITIONS: BadgeDefinition[] = [
  {
    id: 'fragile',
    name: 'Fragile',
    emoji: '🔴',
    description: 'Reached 1+ years of sovereignty',
    requirement: '1.0+ years',
    rarity: 'common',
    image: '/badges/fragile.png',
    checkEligibility: (ratio) => ratio >= 1.0
  },
  {
    id: 'robust',
    name: 'Robust',
    emoji: '🟡',
    description: 'Reached 3+ years of sovereignty',
    requirement: '3.0+ years',
    rarity: 'rare',
    image: '/badges/robust.png',
    checkEligibility: (ratio) => ratio >= 3.0
  },
  {
    id: 'antifragile',
    name: 'Antifragile',
    emoji: '🟢',
    description: 'Reached 6+ years of sovereignty',
    requirement: '6.0+ years',
    rarity: 'epic',
    image: '/badges/antifragile.png',
    checkEligibility: (ratio) => ratio >= 6.0
  },
  {
    id: 'generational',
    name: 'Generationally Sovereign',
    emoji: '🟩',
    description: 'Reached 20+ years of sovereignty',
    requirement: '20+ years',
    rarity: 'legendary',
    image: '/badges/generational.png',
    checkEligibility: (ratio) => ratio >= 20.0
  },
  {
    id: 'hard_money_maxi',
    name: 'Hard Money Maximalist',
    emoji: '💎',
    description: '100% hard money portfolio',
    requirement: '100% hard money',
    rarity: 'legendary',
    image: '/badges/hard_money_maxi.png',
    checkEligibility: (_ratio, hardMoneyPct) => hardMoneyPct >= 99.9
  }
]

export const getRarityColor = (rarity: BadgeDefinition['rarity']): string => {
  switch (rarity) {
    case 'common': return 'border-slate-400'
    case 'rare': return 'border-blue-500'
    case 'epic': return 'border-purple-500'
    case 'legendary': return 'border-orange-500'
  }
}

export const getRarityGlow = (rarity: BadgeDefinition['rarity']): string => {
  switch (rarity) {
    case 'common': return 'shadow-slate-400/20'
    case 'rare': return 'shadow-blue-500/30'
    case 'epic': return 'shadow-purple-500/40'
    case 'legendary': return 'shadow-orange-500/50'
  }
}
