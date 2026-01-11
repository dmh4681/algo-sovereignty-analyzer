import {
  AnalyzeRequest,
  AnalysisResponse,
  HistoryResponse,
  HistorySaveRequest,
  HistorySaveResponse,
  NewsArticlesResponse,
  CurateBatchRequest,
  CurateBatchResponse,
  GoldSilverRatio,
  InfrastructureAudit,
  ParticipationStats,
  NetworkStatsResponse,
  WalletParticipationResponse,
  MeldArbitrageResponse,
  BTCHistoryResponse,
} from './types'

// Use direct backend URL to avoid Next.js proxy timeout issues
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function analyzeWallet(
  request: AnalyzeRequest
): Promise<AnalysisResponse> {
  // Create AbortController for timeout
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 second timeout

  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || 'Wallet analysis failed',
        response.status,
        errorData.code
      )
    }

    return response.json()
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('Request timed out after 60 seconds', 408)
    }
    throw error
  }
}

export async function getClassifications(): Promise<Record<string, { name: string; ticker: string; category: string }>> {
  const response = await fetch(`${API_BASE}/classifications`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch classifications', response.status)
  }

  return response.json()
}

export function calculateSovereigntyMetrics(
  portfolioUSD: number,
  monthlyExpenses: number,
  algoPrice: number = 0.174
) {
  const annualExpenses = monthlyExpenses * 12
  const ratio = annualExpenses > 0 ? portfolioUSD / annualExpenses : 0

  let status: string
  if (ratio >= 20) {
    status = 'Generationally Sovereign 🟩'
  } else if (ratio >= 6) {
    status = 'Antifragile 🟢'
  } else if (ratio >= 3) {
    status = 'Robust 🟡'
  } else if (ratio >= 1) {
    status = 'Fragile 🔴'
  } else {
    status = 'Vulnerable ⚫'
  }

  // Calculate next milestone
  let nextMilestone: { target: string; ratio: number; needed: number } | null = null
  const milestones = [
    { target: 'Fragile 🔴', ratio: 1 },
    { target: 'Robust 🟡', ratio: 3 },
    { target: 'Antifragile 🟢', ratio: 6 },
    { target: 'Generationally Sovereign 🟩', ratio: 20 },
  ]

  for (const milestone of milestones) {
    if (ratio < milestone.ratio) {
      const neededUSD = milestone.ratio * annualExpenses - portfolioUSD
      nextMilestone = {
        target: milestone.target,
        ratio: milestone.ratio,
        needed: neededUSD,
      }
      break
    }
  }

  return {
    ratio,
    status,
    yearsOfRunway: ratio,
    annualExpenses,
    nextMilestone,
    neededAlgo: nextMilestone ? nextMilestone.needed / algoPrice : 0,
  }
}

/**
 * Get historical sovereignty snapshots for an address
 */
export async function getHistory(
  address: string,
  days: 30 | 90 | 365 = 90
): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE}/history/${address}?days=${days}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch history', response.status)
  }

  return response.json()
}

/**
 * Save a sovereignty snapshot to history
 */
export async function saveHistorySnapshot(
  request: HistorySaveRequest
): Promise<HistorySaveResponse> {
  const response = await fetch(`${API_BASE}/history/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(
      errorData.detail || 'Failed to save history snapshot',
      response.status
    )
  }

  return response.json()
}

// --- News Curator API ---

/**
 * Get raw news articles without AI analysis
 */
export async function getNewsArticles(
  metal: 'gold' | 'silver' | 'bitcoin' = 'gold',
  hours: number = 48,
  limit: number = 10
): Promise<NewsArticlesResponse> {
  const response = await fetch(
    `${API_BASE}/news/articles?metal=${metal}&hours=${hours}&limit=${limit}`
  )

  if (!response.ok) {
    throw new ApiError('Failed to fetch news articles', response.status)
  }

  return response.json()
}

/**
 * Get AI-curated news with sovereignty analysis
 */
export async function getCuratedNews(
  request: CurateBatchRequest
): Promise<CurateBatchResponse> {
  const controller = new AbortController()
  // Longer timeout for AI analysis (2 minutes)
  const timeoutId = setTimeout(() => controller.abort(), 120000)

  try {
    const response = await fetch(`${API_BASE}/news/curate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || 'News curation failed',
        response.status
      )
    }

    return response.json()
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('News curation timed out', 408)
    }
    throw error
  }
}

/**
 * Get current Gold/Silver ratio with historical context
 */
export async function getGoldSilverRatio(): Promise<GoldSilverRatio> {
  const response = await fetch(`${API_BASE}/gold-silver-ratio`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch gold/silver ratio', response.status)
  }

  return response.json()
}

// --- Infrastructure Audit API ---

/**
 * Get Algorand relay node infrastructure audit
 * Analyzes centralization of relay network
 */
export async function getInfrastructureAudit(
  forceRefresh: boolean = false
): Promise<InfrastructureAudit> {
  const url = forceRefresh
    ? `${API_BASE}/sovereignty/infrastructure?force_refresh=true`
    : `${API_BASE}/sovereignty/infrastructure`

  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to fetch infrastructure audit', response.status)
  }

  return response.json()
}

/**
 * Get Algorand consensus participation statistics
 * Analyzes online stake and validator distribution
 */
export async function getParticipationStats(
  forceRefresh: boolean = false
): Promise<ParticipationStats> {
  const url = forceRefresh
    ? `${API_BASE}/sovereignty/participation?force_refresh=true`
    : `${API_BASE}/sovereignty/participation`

  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to fetch participation stats', response.status)
  }

  return response.json()
}

// --- Network Stats API (new endpoints from core/network.py) ---

/**
 * Get Algorand network participation and decentralization statistics
 * Returns Foundation vs Community stake breakdown
 */
export async function getNetworkStats(): Promise<NetworkStatsResponse> {
  const response = await fetch(`${API_BASE}/network/stats`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch network stats', response.status)
  }

  return response.json()
}

/**
 * Get participation status for a specific wallet
 */
export async function getWalletParticipation(
  address: string
): Promise<WalletParticipationResponse> {
  const response = await fetch(`${API_BASE}/network/wallet/${address}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch wallet participation', response.status)
  }

  return response.json()
}

// --- Meld Arbitrage API ---

/**
 * Get Meld Gold/Silver arbitrage analysis
 * Compares on-chain Meld prices to spot precious metal prices
 */
export async function getMeldArbitrage(): Promise<MeldArbitrageResponse> {
  const response = await fetch(`${API_BASE}/arbitrage/meld`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch Meld arbitrage data', response.status)
  }

  return response.json()
}

/**
 * Get Bitcoin price history for charting
 * Returns historical data for Coinbase spot, goBTC, and WBTC
 */
export async function getBTCHistory(hours: number = 24): Promise<BTCHistoryResponse> {
  const response = await fetch(`${API_BASE}/arbitrage/btc-history?hours=${hours}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch BTC history data', response.status)
  }

  return response.json()
}

// --- Gold Miner Metrics API ---

export interface MinerMetric {
  id: number | null
  company: string
  ticker: string
  period: string
  aisc: number
  production: number
  revenue: number
  fcf: number
  dividend_yield: number
  market_cap: number
  tier1: number
  tier2: number
  tier3: number
  timestamp: string | null
}

export interface MinerMetricsResponse {
  metrics: MinerMetric[]
  count: number
  timestamp: string
}

export interface SectorStats {
  avg_aisc: number
  total_production: number
  avg_yield: number
  tier1_exposure: number
  company_count: number
}

export interface SectorStatsResponse {
  stats: SectorStats
  timestamp: string
}

export interface CreateMinerMetricRequest {
  company: string
  ticker: string
  period: string
  aisc: number
  production: number
  revenue: number
  fcf: number
  dividend_yield: number
  market_cap: number
  tier1?: number
  tier2?: number
  tier3?: number
}

/**
 * Get all gold miner quarterly metrics
 */
export async function getMinerMetrics(limit: number = 100): Promise<MinerMetricsResponse> {
  const response = await fetch(`${API_BASE}/gold/miners?limit=${limit}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch miner metrics', response.status)
  }

  return response.json()
}

/**
 * Get the most recent metrics for each gold mining company
 */
export async function getLatestMinerMetrics(): Promise<MinerMetricsResponse> {
  const response = await fetch(`${API_BASE}/gold/miners/latest`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch latest miner metrics', response.status)
  }

  return response.json()
}

/**
 * Get sector-wide statistics
 */
export async function getSectorStats(): Promise<SectorStatsResponse> {
  const response = await fetch(`${API_BASE}/gold/miners/stats`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch sector stats', response.status)
  }

  return response.json()
}

/**
 * Get all metrics for a specific company by ticker
 */
export async function getMinerByTicker(ticker: string): Promise<MinerMetricsResponse & { ticker: string; company: string }> {
  const response = await fetch(`${API_BASE}/gold/miners/${ticker}`)

  if (!response.ok) {
    throw new ApiError(`Failed to fetch metrics for ${ticker}`, response.status)
  }

  return response.json()
}

/**
 * Submit a new quarterly report for a gold miner
 */
export async function createMinerMetric(data: CreateMinerMetricRequest): Promise<{ success: boolean; id: number; message: string }> {
  const response = await fetch(`${API_BASE}/gold/miners`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(errorData.detail || 'Failed to create miner metric', response.status)
  }

  return response.json()
}

// --- Silver Miner Metrics API ---
// Uses same interfaces as gold miners (MinerMetric, SectorStats, etc.)

/**
 * Get all silver miner quarterly metrics
 */
export async function getSilverMetrics(limit: number = 100): Promise<MinerMetricsResponse> {
  const response = await fetch(`${API_BASE}/silver/miners?limit=${limit}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch silver miner metrics', response.status)
  }

  return response.json()
}

/**
 * Get the most recent metrics for each silver mining company
 */
export async function getSilverLatestMetrics(): Promise<MinerMetricsResponse> {
  const response = await fetch(`${API_BASE}/silver/miners/latest`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch latest silver miner metrics', response.status)
  }

  return response.json()
}

/**
 * Get silver sector-wide statistics
 */
export async function getSilverSectorStats(): Promise<SectorStatsResponse> {
  const response = await fetch(`${API_BASE}/silver/miners/stats`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch silver sector stats', response.status)
  }

  return response.json()
}

/**
 * Get all metrics for a specific silver company by ticker
 */
export async function getSilverByTicker(ticker: string): Promise<MinerMetricsResponse & { ticker: string; company: string }> {
  const response = await fetch(`${API_BASE}/silver/miners/${ticker}`)

  if (!response.ok) {
    throw new ApiError(`Failed to fetch silver metrics for ${ticker}`, response.status)
  }

  return response.json()
}

/**
 * Submit a new quarterly report for a silver miner
 */
export async function createSilverMetric(data: CreateMinerMetricRequest): Promise<{ success: boolean; id: number; message: string }> {
  const response = await fetch(`${API_BASE}/silver/miners`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(errorData.detail || 'Failed to create silver miner metric', response.status)
  }

  return response.json()
}

// --- Inflation-Adjusted Charts API ---

export interface InflationDataPoint {
  date: string
  cpi: number | null
  m2: number | null
  gold_price: number | null
  silver_price: number | null
}

export interface AdjustedPrice {
  date: string
  nominal_price: number
  real_price: number
  base_year: number
  cpi_at_date: number
  cpi_at_base: number
}

export interface M2Comparison {
  date: string
  gold_price: number
  silver_price: number
  m2_billions: number
  gold_m2_ratio: number
  silver_m2_ratio: number
  gold_m2_ratio_pct_of_peak: number
}

export interface PurchasingPower {
  from_year: number
  to_date: string
  dollar_value_today: number
  purchasing_power_lost_pct: number
  cumulative_inflation_pct: number
  average_annual_inflation_pct: number
  cpi_from: number
  cpi_now: number
}

export interface InflationSummary {
  latest_date: string | null
  current_cpi: number | null
  current_m2_billions: number | null
  current_gold: number | null
  current_silver: number | null
  gold_1980_peak_in_todays_dollars: number
  current_gold_vs_1980_real_pct: number
  purchasing_power: PurchasingPower
}

/**
 * Get inflation dashboard summary statistics
 */
export async function getInflationSummary(): Promise<{ stats: InflationSummary; timestamp: string }> {
  const response = await fetch(`${API_BASE}/inflation/summary`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch inflation summary', response.status)
  }

  return response.json()
}

/**
 * Get historical inflation data (CPI, M2, gold, silver)
 */
export async function getInflationData(
  startDate?: string,
  endDate?: string
): Promise<{ data: InflationDataPoint[]; count: number; timestamp: string }> {
  const params = new URLSearchParams()
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)

  const url = params.toString()
    ? `${API_BASE}/inflation/data?${params}`
    : `${API_BASE}/inflation/data`

  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to fetch inflation data', response.status)
  }

  return response.json()
}

/**
 * Get inflation-adjusted prices for gold or silver
 */
export async function getInflationAdjustedPrices(
  metal: 'gold' | 'silver',
  baseYear: number = 2024
): Promise<{ metal: string; base_year: number; data: AdjustedPrice[]; count: number; timestamp: string }> {
  const response = await fetch(`${API_BASE}/inflation/adjusted/${metal}?base_year=${baseYear}`)

  if (!response.ok) {
    throw new ApiError(`Failed to fetch ${metal} adjusted prices`, response.status)
  }

  return response.json()
}

/**
 * Get gold/silver vs M2 money supply comparison
 */
export async function getM2Comparison(): Promise<{
  data: M2Comparison[]
  count: number
  interpretation: {
    peak_year: number
    peak_context: string
    current_pct_of_peak: number | null
    implication: string
  }
  timestamp: string
}> {
  const response = await fetch(`${API_BASE}/inflation/m2-comparison`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch M2 comparison', response.status)
  }

  return response.json()
}

/**
 * Get dollar purchasing power decline calculation
 */
export async function getPurchasingPower(
  fromYear: number = 1970
): Promise<{ purchasing_power: PurchasingPower; timestamp: string }> {
  const response = await fetch(`${API_BASE}/inflation/purchasing-power?from_year=${fromYear}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch purchasing power', response.status)
  }

  return response.json()
}

// --- Central Bank Gold Tracker API ---

export interface CBGoldSummary {
  total_holdings_tonnes: number
  total_countries: number
  latest_year_purchases: number
  previous_year_purchases: number
  yoy_change_tonnes: number
  consecutive_buying_years: number
  dedollarization_score: number
  dedollarization_interpretation: string
  top_holder: string | null
  top_holder_tonnes: number
}

export interface CountryRanking {
  rank: number
  country_code: string
  country_name: string
  flag: string
  tonnes: number
  pct_of_reserves: number
  change_12m: number | null
  region: string
}

export interface CBHolding {
  id: number
  country_code: string
  country_name: string
  date: string
  tonnes: number
  pct_of_reserves: number
  region: string
  flag: string
}

export interface NetPurchase {
  year: string
  tonnes: number
  is_buying: boolean
}

export interface DeDollarizationScore {
  date: string
  score: number
  components: {
    gold_pct_score: number
    buying_streak_score: number
    acceleration_score: number
    volume_score: number
    consecutive_buying_years: number
    avg_recent_purchases: number
    total_global_tonnes: number
  }
  interpretation: string
}

/**
 * Get central bank gold dashboard summary
 */
export async function getCBGoldSummary(): Promise<{ stats: CBGoldSummary; timestamp: string }> {
  const response = await fetch(`${API_BASE}/central-banks/summary`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch CB gold summary', response.status)
  }

  return response.json()
}

/**
 * Get country leaderboard by gold holdings
 */
export async function getCBLeaderboard(
  limit: number = 20
): Promise<{ rankings: CountryRanking[]; count: number; timestamp: string }> {
  const response = await fetch(`${API_BASE}/central-banks/leaderboard?limit=${limit}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch CB leaderboard', response.status)
  }

  return response.json()
}

/**
 * Get historical holdings for a specific country
 */
export async function getCBCountryHistory(
  countryCode: string
): Promise<{ country_code: string; country_name: string; history: CBHolding[]; count: number; timestamp: string }> {
  const response = await fetch(`${API_BASE}/central-banks/country/${countryCode}`)

  if (!response.ok) {
    throw new ApiError(`Failed to fetch CB history for ${countryCode}`, response.status)
  }

  return response.json()
}

/**
 * Get global net gold purchases by year
 */
export async function getCBNetPurchases(): Promise<{
  purchases: NetPurchase[]
  count: number
  summary: {
    total_tonnes: number
    average_per_year: number
    recent_5yr_avg: number
    peak_year: string | null
    peak_tonnes: number
  }
  timestamp: string
}> {
  const response = await fetch(`${API_BASE}/central-banks/net-purchases`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch CB net purchases', response.status)
  }

  return response.json()
}

/**
 * Get top gold buying countries (12-month change)
 */
export async function getCBTopBuyers(
  n: number = 10
): Promise<{ buyers: CountryRanking[]; count: number; timestamp: string }> {
  const response = await fetch(`${API_BASE}/central-banks/top-buyers?n=${n}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch top buyers', response.status)
  }

  return response.json()
}

/**
 * Get de-dollarization composite score
 */
export async function getDeDollarizationScore(): Promise<{ score: DeDollarizationScore; timestamp: string }> {
  const response = await fetch(`${API_BASE}/central-banks/dedollarization`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch de-dollarization score', response.status)
  }

  return response.json()
}

// --- Miner Earnings Calendar API ---

export interface EarningsEvent {
  id: number
  ticker: string
  metal: 'gold' | 'silver'
  company_name: string
  quarter: string
  earnings_date: string
  time_of_day: 'pre-market' | 'after-hours' | 'during-market'
  is_confirmed: boolean
  eps_actual: number | null
  eps_estimate: number | null
  revenue_actual: number | null
  revenue_estimate: number | null
  production_actual: number | null
  production_guidance: number | null
  aisc_actual: number | null
  aisc_guidance: number | null
  price_before: number | null
  price_1d_after: number | null
  price_5d_after: number | null
  price_30d_after: number | null
  transcript_url: string | null
  press_release_url: string | null
  created_at: string | null
  updated_at: string | null
  // Computed fields
  eps_beat: boolean | null
  revenue_beat: boolean | null
  production_beat: boolean | null
  aisc_beat: boolean | null
  price_reaction_1d: number | null
  price_reaction_5d: number | null
  price_reaction_30d: number | null
  days_until?: number
}

export interface BeatMissStats {
  ticker: string
  company_name: string
  metal: string
  quarters_tracked: number
  eps: { beats: number; misses: number; beat_rate: number }
  revenue: { beats: number; misses: number; beat_rate: number }
  production: { beats: number; misses: number; beat_rate: number }
  aisc: { beats: number; misses: number; beat_rate: number }
  price_reactions: {
    avg_1d: number | null
    avg_on_beat: number | null
    avg_on_miss: number | null
  }
}

export interface SectorEarningsStats {
  metal: string
  upcoming_count: number
  next_earnings: { ticker: string | null; date: string | null }
  sector_avg_eps_beat_rate: number
  sector_avg_revenue_beat_rate: number
  sector_avg_1d_reaction: number | null
  total_companies: number
}

/**
 * Get earnings calendar for a specific month
 */
export async function getEarningsCalendar(
  month?: string
): Promise<{ events: EarningsEvent[]; count: number; month: string; timestamp: string }> {
  const url = month
    ? `${API_BASE}/earnings/calendar?month=${month}`
    : `${API_BASE}/earnings/calendar`

  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to fetch earnings calendar', response.status)
  }

  return response.json()
}

/**
 * Get upcoming earnings events
 */
export async function getUpcomingEarnings(
  days: number = 30
): Promise<{ events: EarningsEvent[]; count: number; days_ahead: number; timestamp: string }> {
  const response = await fetch(`${API_BASE}/earnings/upcoming?days=${days}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch upcoming earnings', response.status)
  }

  return response.json()
}

/**
 * Get earnings history for a specific ticker
 */
export async function getEarningsByTicker(
  ticker: string
): Promise<{ ticker: string; company_name: string; metal: string; events: EarningsEvent[]; count: number; timestamp: string }> {
  const response = await fetch(`${API_BASE}/earnings/ticker/${ticker}`)

  if (!response.ok) {
    throw new ApiError(`Failed to fetch earnings for ${ticker}`, response.status)
  }

  return response.json()
}

/**
 * Get beat/miss statistics for a company
 */
export async function getEarningsStats(
  ticker: string
): Promise<{ stats: BeatMissStats; timestamp: string }> {
  const response = await fetch(`${API_BASE}/earnings/stats/${ticker}`)

  if (!response.ok) {
    throw new ApiError(`Failed to fetch earnings stats for ${ticker}`, response.status)
  }

  return response.json()
}

/**
 * Get sector-wide earnings statistics
 */
export async function getSectorEarningsStats(
  metal?: 'gold' | 'silver'
): Promise<{ stats: SectorEarningsStats; timestamp: string }> {
  const url = metal
    ? `${API_BASE}/earnings/sector-stats?metal=${metal}`
    : `${API_BASE}/earnings/sector-stats`

  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to fetch sector earnings stats', response.status)
  }

  return response.json()
}

// --- Physical Premium Tracker API ---

export interface PremiumDealer {
  id: string
  name: string
  website: string
  shipping_info: string
  min_free_shipping: number | null
  is_active: boolean
}

export interface PremiumProduct {
  id: string
  name: string
  metal: 'gold' | 'silver'
  weight_oz: number
  product_type: 'coin' | 'bar' | 'round' | 'junk'
  mint: string | null
  is_government: boolean
  typical_premium_low: number
  typical_premium_high: number
}

export interface ProductPrice {
  id: number
  product_id: string
  dealer_id: string
  dealer_name?: string
  dealer_website?: string
  shipping_info?: string
  price: number
  quantity: number
  spot_price: number
  premium_dollars: number
  premium_percent: number
  in_stock: boolean
  product_url: string | null
  captured_at: string
}

export interface ProductComparison {
  product: PremiumProduct
  prices: ProductPrice[]
  best_price: ProductPrice | null
  spot_price: number
  melt_value: number
}

export interface DealerRanking {
  dealer: PremiumDealer
  avg_premium_percent: number
  products_tracked: number
  best_for: string[]
}

export interface PremiumSummary {
  spot_prices: { gold?: number; silver?: number }
  product_count: number
  dealer_count: number
  avg_premiums: { gold?: number; silver?: number }
  last_update: string | null
}

/**
 * Get premium tracker summary stats
 */
export async function getPremiumSummary(): Promise<{ stats: PremiumSummary; timestamp: string }> {
  const response = await fetch(`${API_BASE}/premiums/summary`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch premium summary', response.status)
  }

  return response.json()
}

/**
 * Get all tracked products
 */
export async function getPremiumProducts(
  metal?: 'gold' | 'silver'
): Promise<{ products: PremiumProduct[]; count: number; timestamp: string }> {
  const url = metal
    ? `${API_BASE}/premiums/products?metal=${metal}`
    : `${API_BASE}/premiums/products`

  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to fetch premium products', response.status)
  }

  return response.json()
}

/**
 * Get all dealers
 */
export async function getPremiumDealers(): Promise<{ dealers: PremiumDealer[]; count: number; timestamp: string }> {
  const response = await fetch(`${API_BASE}/premiums/dealers`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch dealers', response.status)
  }

  return response.json()
}

/**
 * Compare prices for a product across dealers
 */
export async function compareProductPrices(
  productId: string
): Promise<{ comparison: ProductComparison; timestamp: string }> {
  const response = await fetch(`${API_BASE}/premiums/compare/${productId}`)

  if (!response.ok) {
    throw new ApiError(`Failed to fetch comparison for ${productId}`, response.status)
  }

  return response.json()
}

/**
 * Get best deals (lowest premiums)
 */
export async function getBestDeals(
  metal?: 'gold' | 'silver',
  limit: number = 10
): Promise<{ deals: (PremiumProduct & ProductPrice)[]; count: number; timestamp: string }> {
  const params = new URLSearchParams()
  if (metal) params.append('metal', metal)
  params.append('limit', limit.toString())

  const response = await fetch(`${API_BASE}/premiums/best-deals?${params}`)

  if (!response.ok) {
    throw new ApiError('Failed to fetch best deals', response.status)
  }

  return response.json()
}

/**
 * Get dealer leaderboard
 */
export async function getDealerLeaderboard(
  metal?: 'gold' | 'silver'
): Promise<{ rankings: DealerRanking[]; count: number; timestamp: string }> {
  const url = metal
    ? `${API_BASE}/premiums/leaderboard?metal=${metal}`
    : `${API_BASE}/premiums/leaderboard`

  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to fetch dealer leaderboard', response.status)
  }

  return response.json()
}
