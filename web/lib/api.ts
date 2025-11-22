import { AnalyzeRequest, AnalysisResponse } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

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
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(
      errorData.detail || 'Wallet analysis failed',
      response.status,
      errorData.code
    )
  }

  return response.json()
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
