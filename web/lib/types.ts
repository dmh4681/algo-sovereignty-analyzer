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
  metal: 'gold' | 'silver' | 'bitcoin'
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
  classification: 'sovereign' | 'corporate' | 'hyperscale'
  provider_normalized: string
}

export interface InfrastructureInterpretation {
  health: 'excellent' | 'healthy' | 'moderate' | 'concerning' | 'critical'
  color: string
  message: string
  tier_breakdown: string
  tier_analysis?: string[]  // New: detailed tier analysis points
  sovereign_status: string
  risk_assessment: string
  recommendation: string
  largest_provider?: string  // New: shows concentration leader
}

export interface InfrastructureAudit {
  total_nodes: number
  // 3-tier breakdown
  sovereign_nodes: number       // Tier 1: Residential (green) - rare for relays
  corporate_nodes: number       // Tier 2: Data centers (yellow) - expected for relays
  hyperscale_nodes: number      // Tier 3: AWS/Google/Azure (red) - kill switch risk
  sovereign_percentage: number
  corporate_percentage: number
  hyperscale_percentage: number
  // Legacy
  cloud_nodes: number
  cloud_percentage: number
  // Score and distribution
  decentralization_score: number
  by_tier: {
    sovereign: number
    corporate: number
    hyperscale: number
  }
  top_providers: Record<string, number>
  top_countries: Record<string, number>
  timestamp: string
  cache_expires: string
  interpretation: InfrastructureInterpretation
  // Audit context for relay nodes
  audit_context?: {
    node_type: 'relay' | 'participation'
    note: string
    scoring_model: string
  }
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

// Network Stats types (from /api/v1/network/stats)
export interface NetworkInfo {
  total_supply_algo: number
  online_stake_algo: number
  participation_rate: number
  current_round: number
}

export interface FoundationInfo {
  total_balance_algo: number
  online_balance_algo: number
  pct_of_total_supply: number
  pct_of_online_stake: number
  address_count: number
}

export interface CommunityInfo {
  estimated_stake_algo: number
  pct_of_online_stake: number
}

export interface ScoreBreakdown {
  // Positive factors
  community_online_pct: number
  community_online_score: number
  participation_rate_score: number
  // Risk penalties
  foundation_supply_pct: number
  foundation_supply_penalty: number
  foundation_potential_control: number
  potential_control_penalty: number
  relay_centralization_penalty: number
  governance_penalty: number
  // Totals
  raw_score: number
  final_score: number
}

export interface NetworkStatsResponse {
  network: NetworkInfo
  foundation: FoundationInfo
  community: CommunityInfo
  decentralization_score: number
  score_breakdown?: ScoreBreakdown
  estimated_node_count: number
  fetched_at: string
}

export interface ParticipationKeyInfo {
  first_valid: number | null
  last_valid: number | null
  is_expired: boolean
  rounds_remaining: number | null
}

export interface WalletParticipationResponse {
  address: string
  is_participating: boolean
  balance_algo: number
  stake_percentage: number
  participation_key: ParticipationKeyInfo | null
  contribution_tier: string
  current_round: number
}

// Meld Arbitrage types
export interface ArbitrageMetalData {
  spot_per_oz: number
  implied_per_gram: number
  meld_price: number
  premium_pct: number
  premium_usd: number
  signal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
  signal_strength: number
}

// Legacy single Bitcoin data (kept for backwards compatibility)
export interface ArbitrageBitcoinDataLegacy {
  spot_price: number
  gobtc_price: number
  premium_pct: number
  premium_usd: number
  signal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
  signal_strength: number
}

// New 3-way Bitcoin arbitrage data
export interface BitcoinTokenData {
  price: number
  premium_pct: number
  premium_usd: number
  signal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
  signal_strength: number
  asa_id: number
  tinyman_url: string
  liquidity_warning?: string
  error?: string
}

export interface CrossDexSpread {
  gobtc_vs_wbtc_pct: number
  description: string
}

export interface BestOpportunity {
  token: 'goBTC' | 'WBTC'
  action: 'BUY' | 'SELL' | 'PREFER' | 'EQUAL'
  reason: string
  advantage_pct: number
  liquidity_note?: string
}

export interface ArbitrageBitcoinData {
  spot_price: number
  gobtc: BitcoinTokenData | { error: string }
  wbtc: BitcoinTokenData | { error: string }
  cross_dex_spread: CrossDexSpread | null
  best_opportunity: BestOpportunity | null
}

export interface ArbitrageMetalError {
  error: string
  spot_available: boolean
  meld_available?: boolean
  gobtc_available?: boolean
  wbtc_available?: boolean
}

// GSR (Gold/Silver Ratio) types
export interface GSRContext {
  zone: 'extreme_high' | 'high' | 'normal' | 'low' | 'extreme_low'
  color: string
  message: string
  bias: 'silver' | 'gold' | 'neutral'
}

export interface GSRData {
  meld_gsr: number
  spot_gsr: number | null
  gsr_spread_pct: number | null
  context: GSRContext
}

export interface RotationSignal {
  signal: 'HOLD' | 'CONSIDER_SILVER_TO_GOLD' | 'CONSIDER_GOLD_TO_SILVER' | 'SILVER_TO_GOLD' | 'GOLD_TO_SILVER'
  strength: number
  spread_pct: number
  description: string
}

export interface MeldArbitrageResponse {
  gold: ArbitrageMetalData | ArbitrageMetalError | null
  silver: ArbitrageMetalData | ArbitrageMetalError | null
  bitcoin: ArbitrageBitcoinData | ArbitrageMetalError | null
  gsr: GSRData | null
  rotation: RotationSignal | null
  timestamp: string
  data_complete: boolean
}

// Bitcoin History types
export interface BTCHistoryDataPoint {
  timestamp: string
  spot_btc: number
  gobtc_price: number
  wbtc_price: number | null
  gobtc_premium_pct: number
  wbtc_premium_pct: number | null
}

export interface BTCHistoryStats {
  gobtc: {
    avg_premium_pct: number
    min_premium_pct: number
    max_premium_pct: number
  }
  wbtc: {
    avg_premium_pct: number | null
    min_premium_pct: number | null
    max_premium_pct: number | null
  }
  data_points: number
  hours: number
}

export interface BTCHistoryResponse {
  data_points: BTCHistoryDataPoint[]
  stats: BTCHistoryStats
  hours_requested: number
  timestamp: string
}
