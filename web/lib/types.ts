export interface Asset {
  ticker: string
  name: string
  amount: number
  usd_value: number
}

// Hard money sub-types for color coding
export type HardMoneyType = 'bitcoin' | 'gold' | 'silver'

export function getHardMoneyType(ticker: string): HardMoneyType | null {
  const t = ticker.toUpperCase()
  if (t.includes('BTC') || t === 'BITCOIN') return 'bitcoin'
  if (t.includes('GOLD') || t === 'XAUT' || t === 'PAXG') return 'gold'
  if (t.includes('SILVER')) return 'silver'
  return null
}

export const HARD_MONEY_COLORS = {
  bitcoin: {
    text: 'text-orange-500',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/50',
    emoji: '₿',
  },
  gold: {
    text: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/50',
    emoji: '🥇',
  },
  silver: {
    text: 'text-slate-300',
    bg: 'bg-slate-400/10',
    border: 'border-slate-400/50',
    emoji: '🥈',
  },
} as const

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
  algo: Asset[]
  dollars: Asset[]
  shitcoin: Asset[]
}

export interface AnalysisResponse {
  address: string
  is_participating: boolean
  hard_money_algo: number
  categories: Categories
  sovereignty_data: SovereigntyData | null
  participation_info?: {
    staked_amount: number
    vote_first_valid: number | null
    vote_last_valid: number | null
    key_expiration_rounds: number | null
    is_incentive_eligible: boolean
    estimated_apy: number
  }
  metadata?: {
    analyzed_at: string
    participation_status: string
  }
}

export interface AnalyzeRequest {
  address: string
  monthly_fixed_expenses?: number
}

export type CategoryType = 'hard_money' | 'algo' | 'dollars' | 'shitcoin'

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
    key: 'algo',
    title: 'Algorand',
    description: 'Native Token & Ecosystem',
    emoji: 'Ⱥ',
    colorClass: 'text-slate-200',
    borderClass: 'border-slate-500/50',
    bgClass: 'bg-slate-500/10',
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
    description: 'Everything Else',
    emoji: '💩',
    colorClass: 'text-red-500',
    borderClass: 'border-red-500/50',
    bgClass: 'bg-red-500/10',
  },
]

// History types
export interface SovereigntySnapshot {
  address: string
  timestamp: string
  sovereignty_ratio: number
  hard_money_usd: number
  total_portfolio_usd: number
  algo_price: number
  participation_status: boolean
}

export interface HistoryResponse {
  address: string
  snapshots: SovereigntySnapshot[]
  count: number
}

export interface HistorySaveRequest {
  address: string
  monthly_fixed_expenses: number
}

export interface HistorySaveResponse {
  success: boolean
  message: string
  snapshot: SovereigntySnapshot | null
}
