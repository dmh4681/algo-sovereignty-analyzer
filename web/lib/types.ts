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

// News Curator types
export interface NewsArticle {
  title: string
  summary: string
  link: string
  published: string
  source: string
}

export interface AnalyzedArticle {
  original: NewsArticle
  analysis: string
  sovereignty_score: number
  metal: string
  analyzed_at: string
}

export interface NewsArticlesResponse {
  articles: NewsArticle[]
  count: number
  metal: string
}

export interface CurateBatchRequest {
  metal: 'gold' | 'silver'
  hours?: number
  limit?: number
  min_score?: number
}

export interface CurateBatchResponse {
  articles: AnalyzedArticle[]
  count: number
  metal: string
  fetched_count: number
}

// Infrastructure Audit types
export interface InfrastructureNode {
  hostname: string
  ip: string
  port: number
  isp: string
  org: string
  country: string
  region: string
  city: string
  asn: string
  classification: 'cloud' | 'sovereign'
}

export interface InfrastructureInterpretation {
  health: 'healthy' | 'moderate' | 'concerning' | 'critical'
  color: string
  message: string
  cloud_dependency: string
  recommendation: string
}

export interface InfrastructureAudit {
  total_nodes: number
  cloud_nodes: number
  sovereign_nodes: number
  cloud_percentage: number
  sovereign_percentage: number
  decentralization_score: number
  top_providers: Record<string, number>
  top_countries: Record<string, number>
  timestamp: string
  cache_expires: string
  interpretation: InfrastructureInterpretation
}

// Participation Audit types
export interface ParticipationValidator {
  address: string
  address_short: string
  stake_algo: number
  stake_formatted: string
  incentive_eligible: boolean
  vote_first_valid: number
  vote_last_valid: number
  keys_valid: boolean
  last_proposed: number | null
  last_heartbeat: number | null
  recently_active: boolean
}

export interface ParticipationInterpretation {
  health: 'strong' | 'healthy' | 'moderate' | 'low' | 'critical'
  color: string
  message: string
  stake_description: string
  recommendation: string
}

export interface ParticipationStats {
  current_round: number
  online_stake: {
    algo: number
    formatted: string
    percentage: number
  }
  total_supply: {
    algo: number
    formatted: string
  }
  validators: {
    estimated_count: number
    top_validators: ParticipationValidator[]
    incentive_eligible_count: number
    incentive_eligible_stake: string
  }
  interpretation: ParticipationInterpretation
  timestamp: string
  cache_expires: string
}

// Gold/Silver Ratio types
export interface GoldSilverRatio {
  ratio: number
  gold_price: number
  silver_price: number
  historical_mean: number
  historical_range: {
    low: number
    high: number
  }
  status: 'undervalued' | 'below_average' | 'normalized' | 'compressed'
  color: string
  message: string
  interpretation: {
    what_it_means: string
    current_signal: string
    historical_note: string
  }
}
