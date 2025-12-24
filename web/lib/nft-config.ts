export interface PickaxeNFT {
  id: string
  name: string
  description: string
  image: string
  price: number // in ALGO
  supply: number
  targetAsset: {
    name: string
    ticker: string
    asaId: number
  }
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  color: string // Tailwind color class
  available: boolean
}

export const PICKAXE_NFTS: PickaxeNFT[] = [
  {
    id: 'gold_pickaxe',
    name: 'Gold Pickaxe',
    description: 'Auto-mine GOLD$ with every deposit. Watch your hard money stack grow automatically.',
    image: '/nfts/gold_pickaxe.png',
    price: 100,
    supply: 1000,
    targetAsset: {
      name: 'Meld Gold',
      ticker: 'GOLD$',
      asaId: 2722949
    },
    rarity: 'legendary',
    color: 'yellow',
    available: false
  },
  {
    id: 'silver_pickaxe',
    name: 'Silver Pickaxe',
    description: 'Auto-mine SILVER$ with every deposit. Stack silver on autopilot.',
    image: '/nfts/silver_pickaxe.png',
    price: 100,
    supply: 2000,
    targetAsset: {
      name: 'Meld Silver',
      ticker: 'SILVER$',
      asaId: 2751733
    },
    rarity: 'epic',
    color: 'slate',
    available: false
  },
  {
    id: 'bitcoin_pickaxe',
    name: 'Bitcoin Pickaxe',
    description: 'Auto-mine goBTC with every deposit. Stack sats the sovereign way.',
    image: '/nfts/bitcoin_pickaxe.png',
    price: 100,
    supply: 1500,
    targetAsset: {
      name: 'goBTC',
      ticker: 'goBTC',
      asaId: 386192725
    },
    rarity: 'legendary',
    color: 'orange',
    available: false
  }
]

export const BUNDLE_DEAL = {
  name: 'Ultimate Miner Bundle',
  description: 'All 3 pickaxes at a discount. Become the ultimate hard money miner.',
  pickaxeIds: ['gold_pickaxe', 'silver_pickaxe', 'bitcoin_pickaxe'],
  originalPrice: 300, // 100 + 100 + 100
  bundlePrice: 250,
  savings: 50,
  savingsPercent: 17
}

export const getRarityColor = (rarity: PickaxeNFT['rarity']): string => {
  switch (rarity) {
    case 'common': return 'border-slate-400'
    case 'rare': return 'border-blue-500'
    case 'epic': return 'border-purple-500'
    case 'legendary': return 'border-orange-500'
  }
}

export const getRarityGlow = (rarity: PickaxeNFT['rarity']): string => {
  switch (rarity) {
    case 'common': return 'shadow-slate-400/20'
    case 'rare': return 'shadow-blue-500/30'
    case 'epic': return 'shadow-purple-500/40'
    case 'legendary': return 'shadow-orange-500/50'
  }
}

export const getPickaxeColorClasses = (color: string) => {
  const colorMap: Record<string, { border: string; bg: string; text: string; glow: string }> = {
    yellow: {
      border: 'border-yellow-500/50',
      bg: 'bg-yellow-500/10',
      text: 'text-yellow-500',
      glow: 'shadow-yellow-500/30'
    },
    slate: {
      border: 'border-slate-400/50',
      bg: 'bg-slate-400/10',
      text: 'text-slate-300',
      glow: 'shadow-slate-400/30'
    },
    orange: {
      border: 'border-orange-500/50',
      bg: 'bg-orange-500/10',
      text: 'text-orange-500',
      glow: 'shadow-orange-500/30'
    }
  }
  return colorMap[color] || colorMap.orange
}
