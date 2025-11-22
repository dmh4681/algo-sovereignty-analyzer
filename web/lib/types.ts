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
  dollars: Asset[]
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

export type CategoryType = 'hard_money' | 'dollars' | 'shitcoin'

export interface CategoryConfig {
  key: CategoryType
  title: string
  description: string
  emoji: string
  colorClass: string
  borderClass: string
  bgClass: string
}

export const CATEGORY_CONFIGS: CategoryConfig[] = [
  {
    key: 'hard_money',
    title: 'Hard Money',
    description: 'Bitcoin, Gold, Silver',
    emoji: '💎',
    colorClass: 'text-emerald-500',
    borderClass: 'border-emerald-500/50',
    bgClass: 'bg-emerald-500/10',
  },
  {
    key: 'dollars',
    title: 'Dollars',
    description: 'Stablecoins (Fiat-pegged)',
    emoji: '💵',
    colorClass: 'text-blue-500',
    borderClass: 'border-blue-500/50',
    bgClass: 'bg-blue-500/10',
  },
  {
    key: 'shitcoin',
    title: 'Shitcoins',
    description: 'ALGO + Everything Else',
    emoji: '💩',
    colorClass: 'text-red-500',
    borderClass: 'border-red-500/50',
    bgClass: 'bg-red-500/10',
  },
]
