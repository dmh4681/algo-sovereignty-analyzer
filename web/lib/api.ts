import {
  AnalyzeRequest,
  AnalysisResponse,
  HistoryResponse,
  HistorySaveRequest,
  HistorySaveResponse,
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
