export interface Asset {
  ticker: string
  name: string
  amount: number
  usd_value: number
}

export interface SovereigntyData {
  monthly_fixed_expenses: number
  annual_fixed_expenses: number
  algo_price: number
  portfolio_usd: number
  sovereignty_ratio: number
  sovereignty_status: string
  years_of_runway: number
}

export interface Categories {
  hard_money: Asset[]
  productive: Asset[]
  nft: Asset[]
  shitcoin: Asset[]
}

export interface AnalysisResponse {
  address: string
  is_participating: boolean
  hard_money_algo: number
  categories: Categories
  sovereignty_data: SovereigntyData | null
  metadata?: {
    analyzed_at: string
    participation_status: string
  }
}

export interface AnalyzeRequest {
  address: string
  monthly_fixed_expenses?: number
}

export type CategoryType = 'hard_money' | 'productive' | 'nft' | 'shitcoin'

export interface CategoryConfig {
  key: CategoryType
  title: string
  emoji: string
  colorClass: string
  borderClass: string
  bgClass: string
}

export const CATEGORY_CONFIGS: CategoryConfig[] = [
  {
    key: 'hard_money',
    title: 'Hard Money',
    emoji: '💎',
    colorClass: 'text-emerald-500',
    borderClass: 'border-emerald-500/50',
    bgClass: 'bg-emerald-500/10',
  },
  {
    key: 'productive',
    title: 'Productive',
    emoji: '🌾',
    colorClass: 'text-amber-500',
    borderClass: 'border-amber-500/50',
    bgClass: 'bg-amber-500/10',
  },
  {
    key: 'nft',
    title: 'NFTs & Collectibles',
    emoji: '🎨',
    colorClass: 'text-purple-500',
    borderClass: 'border-purple-500/50',
    bgClass: 'bg-purple-500/10',
  },
  {
    key: 'shitcoin',
    title: 'Shitcoins',
    emoji: '💩',
    colorClass: 'text-red-500',
    borderClass: 'border-red-500/50',
    bgClass: 'bg-red-500/10',
  },
]
