/**
 * INTEGRATION GUIDE
 * How to integrate BadgeSection and HistoryChart into your analyze page
 * 
 * File to modify: web/app/analyze/page.tsx
 */

// ============================================================================
// STEP 1: Add imports at the top of your analyze page
// ============================================================================

import { BadgeSection } from '@/components/BadgeSection'
import { HistoryChart } from '@/components/HistoryChart'

// ============================================================================
// STEP 2: Calculate hardMoneyPercentage after analysis completes
// ============================================================================

// Add this helper function to your page or lib/utils.ts

const calculateHardMoneyPercentage = (analysisData: any): number => {
  if (!analysisData?.assets) return 0
  
  const hardMoneyValue = (analysisData.assets.hard_money || [])
    .reduce((sum: number, asset: any) => sum + (asset.usd_value || 0), 0)
  
  const dollarsValue = (analysisData.assets.dollars || [])
    .reduce((sum: number, asset: any) => sum + (asset.usd_value || 0), 0)
  
  const shitcoinValue = (analysisData.assets.shitcoin || [])
    .reduce((sum: number, asset: any) => sum + (asset.usd_value || 0), 0)
  
  const totalValue = hardMoneyValue + dollarsValue + shitcoinValue
  
  return totalValue > 0 ? (hardMoneyValue / totalValue) * 100 : 0
}

// ============================================================================
// STEP 3: Auto-save snapshot after successful analysis
// ============================================================================

// Add this after your analysis fetch succeeds:

const saveSnapshot = async (address: string, analysisResult: any) => {
  try {
    await fetch('/api/v1/history/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        address, 
        analysis_result: analysisResult 
      })
    })
  } catch (err) {
    console.error('Failed to save snapshot:', err)
    // Non-blocking - don't break analysis if history save fails
  }
}

// Call it after analysis succeeds:
// const data = await response.json()
// setAnalysis(data)
// if (connectedAddress) {
//   saveSnapshot(connectedAddress, data)
// }

// ============================================================================
// STEP 4: Add components to your JSX render
// ============================================================================

// After your existing sovereignty metrics section, add:

/*
{analysis && (
  <>
    {/* Badge Section */}
    <BadgeSection 
      sovereigntyRatio={analysis.sovereignty?.sovereignty_ratio || 0}
      hardMoneyPercentage={calculateHardMoneyPercentage(analysis)}
      walletAddress={connectedAddress}
    />
    
    {/* History Chart - only show if wallet connected */}
    {connectedAddress && (
      <HistoryChart 
        address={connectedAddress}
        currentRatio={analysis.sovereignty?.sovereignty_ratio || 0}
      />
    )}
  </>
)}
*/

// ============================================================================
// STEP 5: Full example component structure
// ============================================================================

/*
export default function AnalyzePage() {
  const [analysis, setAnalysis] = useState(null)
  const { activeAccount } = useWallet()
  const connectedAddress = activeAccount?.address

  const handleAnalyze = async () => {
    const response = await fetch('/api/v1/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        address: connectedAddress,
        monthly_fixed_expenses: monthlyExpenses 
      })
    })
    
    const data = await response.json()
    setAnalysis(data)
    
    // Auto-save snapshot for history
    if (connectedAddress) {
      saveSnapshot(connectedAddress, data)
    }
  }

  const hardMoneyPct = analysis ? calculateHardMoneyPercentage(analysis) : 0

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* ... Wallet Connect, Expenses Input, Analyze Button ... */}
      
      {analysis && (
        <>
          {/* Sovereignty Metrics Card (existing) */}
          <SovereigntyMetrics data={analysis.sovereignty} />
          
          {/* NEW: Badge Section */}
          <BadgeSection 
            sovereigntyRatio={analysis.sovereignty.sovereignty_ratio}
            hardMoneyPercentage={hardMoneyPct}
            walletAddress={connectedAddress}
          />
          
          {/* NEW: History Chart */}
          {connectedAddress && (
            <HistoryChart 
              address={connectedAddress}
              currentRatio={analysis.sovereignty.sovereignty_ratio}
            />
          )}
          
          {/* Asset Breakdown (existing) */}
          <AssetBreakdown assets={analysis.assets} />
        </>
      )}
    </div>
  )
}
*/

// ============================================================================
// LAYOUT ORDER (Recommended)
// ============================================================================

/*
1. Sovereignty Metrics (the main hero card with ratio and status)
2. Badge Section (gamification, achievement badges)
3. History Chart (progress over time)
4. Asset Breakdown (detailed holdings by category)
*/

// ============================================================================
// REQUIRED: Copy badge images to public folder
// ============================================================================

/*
Make sure to copy your badge images to web/public/badges/:

web/public/badges/
├── fragile.png
├── robust.png
├── antifragile.png
├── generational.png
└── hard_money_maxi.png

The images are already in your project root directory.
Run this from project root:

mkdir -p web/public/badges
cp fragile.png robust.png antifragile.png generational.png hard_money_maxi.png web/public/badges/
*/
