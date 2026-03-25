'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatUSD, formatNumber } from '@/lib/utils'
import { Asset, Categories, CATEGORY_CONFIGS, getHardMoneyType, HARD_MONEY_COLORS, LPDecompositionResult } from '@/lib/types'
import { CoinStack, GoldBars } from '@/components/illustrations'
import { ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { decomposeLPToken } from '@/lib/api'

/**
 * Props for the {@link AssetBreakdown} component.
 *
 * @property categories - The categorized asset data from wallet analysis,
 *   containing arrays of assets keyed by category: hard_money, algo, dollars, shitcoin.
 */
interface AssetBreakdownProps {
  categories: Categories
}

/**
 * Displays a wallet's assets organized by sovereignty category in a visual card layout.
 *
 * The component renders two sections:
 * 1. **Treasure Vault** (full-width top card): Hard money assets (Bitcoin, Gold, Silver)
 *    displayed in a 3-column grid with sub-type cards for each precious metal/crypto.
 *    Each sub-card shows the total USD value and individual token holdings.
 *
 * 2. **Other Categories** (3-column grid below): Algorand, Dollars, and Shitcoins
 *    rendered as individual {@link CategoryCard} components.
 *
 * Features:
 * - Mobile-responsive with collapsible sections (accordion pattern)
 * - LP token detection and expandable details showing pool composition
 * - NFT/dust filtering in the shitcoin category for cleaner display
 * - Decorative gold bar and coin stack illustrations
 * - Color-coded borders and backgrounds per category
 *
 * Data flow: Receives categorized assets from the parent analyze page,
 * which fetches them from `POST /api/v1/analyze`.
 *
 * @param props - Component props
 * @param props.categories - Object with hard_money, algo, dollars, and shitcoin arrays
 */
export function AssetBreakdown({ categories }: AssetBreakdownProps) {
  // Collapsible section state for mobile
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    hard_money: true,
    other: true
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  // Separate hard money assets by type
  const hardMoneyAssets = categories.hard_money
  const goldAssets = hardMoneyAssets.filter(a => getHardMoneyType(a.ticker) === 'gold')
  const silverAssets = hardMoneyAssets.filter(a => getHardMoneyType(a.ticker) === 'silver')
  const bitcoinAssets = hardMoneyAssets.filter(a => getHardMoneyType(a.ticker) === 'bitcoin')

  const goldValue = goldAssets.reduce((sum, a) => sum + a.usd_value, 0)
  const silverValue = silverAssets.reduce((sum, a) => sum + a.usd_value, 0)
  const bitcoinValue = bitcoinAssets.reduce((sum, a) => sum + a.usd_value, 0)
  const totalHardMoney = goldValue + silverValue + bitcoinValue

  return (
    <div className="space-y-4">
      {/* Hard Money - Full Width Top Section */}
      {hardMoneyAssets.length > 0 && (
        <Card className="border-yellow-500/40 bg-gradient-to-br from-amber-600/10 via-yellow-500/10 to-gray-400/10 border-2 relative overflow-hidden">
          {/* Decorative gold bars in corner */}
          <div className="absolute -right-4 -top-4 opacity-10 hidden md:block">
            <GoldBars size={120} variant="pile" animated={false} />
          </div>
          <CardHeader className="relative">
            {/* Mobile collapsible header */}
            <button
              className="md:hidden w-full flex items-center justify-between text-left"
              onClick={() => toggleSection('hard_money')}
              aria-expanded={expandedSections.hard_money}
              aria-controls="hard-money-content"
            >
              <CardTitle className="flex items-center gap-3 text-xl">
                <span className="flex gap-2">
                  <span className="text-amber-400">₿</span>
                  <span className="text-yellow-400">🪙</span>
                  <span className="text-gray-300">🥈</span>
                </span>
                <span className="gold-shimmer">
                  Treasure Vault
                </span>
              </CardTitle>
              <div className="flex items-center gap-2">
                <span className="text-sm text-amber-300/70">{formatUSD(totalHardMoney)}</span>
                {expandedSections.hard_money ? (
                  <ChevronUp className="h-5 w-5 text-amber-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-amber-400" />
                )}
              </div>
            </button>
            {/* Desktop header (always visible) */}
            <div className="hidden md:block">
              <CardTitle className="flex items-center gap-3 text-2xl">
                <span className="flex gap-2">
                  <span className="text-amber-400">₿</span>
                  <span className="text-yellow-400">🪙</span>
                  <span className="text-gray-300">🥈</span>
                </span>
                <span className="gold-shimmer">
                  Treasure Vault
                </span>
              </CardTitle>
              <p className="text-sm text-amber-200/60">Bitcoin, Gold, Silver - Your Hard Money Hoard</p>
            </div>
          </CardHeader>
          <CardContent
            id="hard-money-content"
            className={`relative transition-all duration-300 ${expandedSections.hard_money ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden md:max-h-none md:opacity-100'}`}
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
              {/* Gold Card */}
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-yellow-600/20 to-yellow-900/20 border-2 border-yellow-500/30 p-6 hover:border-yellow-400/50 hover:shadow-lg hover:shadow-yellow-500/10 transition-all">
                <div className="absolute -bottom-2 -right-2 opacity-30">
                  <CoinStack size={60} metal="gold" animated={false} />
                </div>
                <div className="relative z-10">
                  <div className="text-yellow-400 text-sm font-medium mb-2 flex items-center gap-2">
                    🪙 GOLD
                  </div>
                  <div className="text-4xl font-bold text-yellow-300 mb-1 tabular-nums">
                    {formatUSD(goldValue)}
                  </div>
                  <div className="space-y-1">
                    {goldAssets.map((asset, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-yellow-200/70">{asset.ticker}</span>
                        <span className="text-yellow-100 tabular-nums">{formatNumber(asset.amount)}</span>
                      </div>
                    ))}
                  </div>
                  {goldAssets.length === 0 && (
                    <div className="text-yellow-600/50 text-sm italic">No gold in vault</div>
                  )}
                </div>
              </div>

              {/* Silver Card */}
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-gray-400/20 to-gray-700/20 border-2 border-gray-400/30 p-6 hover:border-gray-300/50 hover:shadow-lg hover:shadow-gray-400/10 transition-all">
                <div className="absolute -bottom-2 -right-2 opacity-30">
                  <CoinStack size={60} metal="silver" animated={false} />
                </div>
                <div className="relative z-10">
                  <div className="text-gray-300 text-sm font-medium mb-2 flex items-center gap-2">
                    🥈 SILVER
                  </div>
                  <div className="text-4xl font-bold text-gray-200 mb-1 tabular-nums">
                    {formatUSD(silverValue)}
                  </div>
                  <div className="space-y-1">
                    {silverAssets.map((asset, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-gray-300/70">{asset.ticker}</span>
                        <span className="text-gray-200 tabular-nums">{formatNumber(asset.amount)}</span>
                      </div>
                    ))}
                  </div>
                  {silverAssets.length === 0 && (
                    <div className="text-gray-600/50 text-sm italic">No silver in vault</div>
                  )}
                </div>
              </div>

              {/* Bitcoin Card */}
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-amber-600/20 to-amber-900/20 border-2 border-amber-500/30 p-6 hover:border-amber-400/50 hover:shadow-lg hover:shadow-amber-500/10 transition-all">
                <div className="absolute -bottom-2 -right-2 opacity-30">
                  <CoinStack size={60} metal="bronze" animated={false} />
                </div>
                <div className="relative z-10">
                  <div className="text-amber-400 text-sm font-medium mb-2 flex items-center gap-2">
                    ₿ BITCOIN
                  </div>
                  <div className="text-4xl font-bold text-amber-300 mb-1 tabular-nums">
                    {formatUSD(bitcoinValue)}
                  </div>
                  <div className="space-y-1">
                    {bitcoinAssets.map((asset, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-amber-200/70">{asset.ticker}</span>
                        <span className="text-amber-100 tabular-nums">{formatNumber(asset.amount)}</span>
                      </div>
                    ))}
                  </div>
                  {bitcoinAssets.length === 0 && (
                    <div className="text-amber-600/50 text-sm italic">No bitcoin in vault</div>
                  )}
                </div>
              </div>

            </div>
          </CardContent>
        </Card>
      )}

      {/* Second Row - Algorand, Dollars, Shitcoins */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {CATEGORY_CONFIGS.filter(c => c.key !== 'hard_money').map((config) => (
          <CategoryCard
            key={config.key}
            config={config}
            assets={categories[config.key]}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * Props for the {@link CategoryCard} internal component.
 *
 * @property config - Category display configuration from CATEGORY_CONFIGS (title, emoji, colors)
 * @property assets - Array of assets belonging to this category
 */
interface CategoryCardProps {
  config: typeof CATEGORY_CONFIGS[number]
  assets: Asset[]
}

/**
 * Returns Tailwind text color classes and optional emoji for an asset based on
 * its hard money sub-type (gold, silver, bitcoin). Non-hard-money assets
 * receive a neutral slate color.
 *
 * @param asset - The asset to style
 * @param isHardMoney - Whether the asset is in the hard_money category
 * @returns Object with `textClass` (Tailwind CSS class) and optional `emoji`
 */
function getAssetColor(asset: Asset, isHardMoney: boolean): { textClass: string; emoji?: string } {
  if (!isHardMoney) return { textClass: 'text-slate-200' }

  const hardMoneyType = getHardMoneyType(asset.ticker)
  if (hardMoneyType) {
    return {
      textClass: HARD_MONEY_COLORS[hardMoneyType].text,
      emoji: HARD_MONEY_COLORS[hardMoneyType].emoji
    }
  }
  return { textClass: 'text-slate-200' }
}

/**
 * Detects whether an asset is a Liquidity Pool (LP) token by checking its
 * ticker and name against known LP patterns from Algorand DEXs
 * (Tinyman, Pact, Humble, etc.).
 *
 * @param ticker - The asset's ticker symbol (e.g., "ALGO-USDC-LP")
 * @param name - The asset's full name (e.g., "TinymanPool2.0 ALGO-USDC")
 * @returns True if the asset matches LP token patterns
 */
function isLPToken(ticker: string, name: string): boolean {
  const t = ticker.toUpperCase()
  const n = name.toUpperCase()
  return (
    t.includes('-LP') ||
    t.includes('TM-POOL') ||
    t.includes('TINYMAN') ||
    t.includes('PACT-') ||
    n.includes('LIQUIDITY') ||
    n.includes('LP TOKEN') ||
    n.includes('POOL')
  )
}

/**
 * Extracts the underlying asset pair from an LP token's ticker or name using
 * regex pattern matching. Tries multiple formats common to Algorand DEXs.
 *
 * Supported patterns:
 * - "ALGO-USDC-LP" (hyphenated with LP suffix)
 * - "ALGO/USDC" (slash-separated)
 * - "ALGO-USDC" (hyphenated)
 *
 * @param ticker - The LP token's ticker symbol
 * @param name - The LP token's full name
 * @returns Array of two asset ticker strings, or empty array if parsing fails
 */
function parseLPComponents(ticker: string, name: string): string[] {
  // Try to extract from patterns like "ALGO-USDC-LP" or "TinymanPool ALGO/USDC"
  const patterns = [
    /(\w+)-(\w+)-LP/i,
    /(\w+)\/(\w+)/i,
    /(\w+)-(\w+)/i,
  ]
  for (const pattern of patterns) {
    const match = ticker.match(pattern) || name.match(pattern)
    if (match) {
      return [match[1], match[2]]
    }
  }
  return []
}

/**
 * Filters out insignificant assets (NFTs, dust, collectibles) from the display
 * to reduce visual noise. Only applies filtering to the shitcoin category;
 * all other categories show every asset.
 *
 * Shitcoin filters:
 * - NFTs/collectibles: amount <= 1 and value < $1
 * - NFDs (Algorand domain names): ticker starts with "NFD" or name contains "NFD"
 * - Verification badges: tickers matching "VL" + digits, "AFK", "OGG"
 * - Dust: amount < 0.01 with zero value
 *
 * @param assets - Array of assets to filter
 * @param categoryKey - The category key (filtering only applies to "shitcoin")
 * @returns Filtered array of assets suitable for display
 */
function filterDisplayAssets(assets: Asset[], categoryKey: string): Asset[] {
  // For shitcoins, filter out noise
  if (categoryKey === 'shitcoin') {
    return assets.filter(asset => {
      const ticker = asset.ticker.toUpperCase()
      const name = asset.name.toUpperCase()

      // Filter out NFTs and collectibles (usually amount of 1)
      if (asset.amount <= 1 && asset.usd_value < 1) return false

      // Filter out NFDs (domain names)
      if (ticker.startsWith('NFD') || name.includes('NFD')) return false

      // Filter out verification badges and other collectibles
      if (ticker.match(/^VL\d+/) || ticker === 'AFK' || ticker === 'OGG') return false

      // Filter out dust (very small amounts with no value)
      if (asset.amount < 0.01 && asset.usd_value === 0) return false

      return true
    })
  }

  // For other categories, show everything
  return assets
}

/**
 * Renders a single category card showing asset count, total USD value, and a
 * scrollable list of individual assets. Used for Algorand, Dollars, and
 * Shitcoin categories (hard money has its own dedicated section in AssetBreakdown).
 *
 * Features:
 * - LP token expansion: clicking an LP token reveals pool composition details
 * - Keyboard-accessible LP toggles (Enter/Space)
 * - Hard money sub-type color coding (gold, silver, bitcoin text/background)
 * - NFT/dust count display for filtered assets
 * - Capped at 10 visible items with "+N more tokens" indicator
 *
 * @param props - Component props
 * @param props.config - Category display configuration (title, colors, emoji)
 * @param props.assets - Array of assets in this category
 */
type LPLoadState = LPDecompositionResult | 'loading' | 'error'

function CategoryCard({ config, assets }: CategoryCardProps) {
  // State for expanded LP tokens
  const [expandedLPs, setExpandedLPs] = useState<Set<string>>(new Set())
  // Lazy-loaded decomposition data keyed by assetKey
  const [lpData, setLPData] = useState<Record<string, LPLoadState>>({})

  const toggleLP = (assetKey: string, asset: Asset) => {
    setExpandedLPs(prev => {
      const next = new Set(prev)
      if (next.has(assetKey)) {
        next.delete(assetKey)
      } else {
        next.add(assetKey)
        // Trigger lazy load when expanding, if we have asset_id and haven't loaded yet
        if (asset.asset_id != null && !(assetKey in lpData)) {
          setLPData(d => ({ ...d, [assetKey]: 'loading' }))
          decomposeLPToken({
            asset_id: asset.asset_id!,
            ticker: asset.ticker,
            name: asset.name,
            amount: asset.amount,
          })
            .then(result => setLPData(d => ({ ...d, [assetKey]: result })))
            .catch(() => setLPData(d => ({ ...d, [assetKey]: 'error' })))
        }
      }
      return next
    })
  }

  const totalValue = assets.reduce((sum, asset) => sum + asset.usd_value, 0)
  const assetCount = assets.length
  const isHardMoney = config.key === 'hard_money'

  // Filter assets for display (but keep full count)
  const displayAssets = filterDisplayAssets(assets, config.key)
  const hiddenCount = assetCount - displayAssets.length

  // For hard money, show a gradient border effect
  const cardBorder = isHardMoney
    ? 'border-gradient-to-r from-orange-500 via-yellow-400 to-slate-300'
    : config.borderClass

  return (
    <Card className={`${config.borderClass} ${config.bgClass} border ${isHardMoney ? 'bg-gradient-to-br from-orange-500/5 via-yellow-500/5 to-slate-400/5' : ''}`}>
      <CardHeader className="pb-2">
        <CardTitle className={`flex items-center gap-2 text-lg ${config.colorClass}`}>
          {isHardMoney ? (
            <span className="flex gap-1">
              <span className="text-orange-500">₿</span>
              <span className="text-yellow-400">🥇</span>
              <span className="text-slate-300">🥈</span>
            </span>
          ) : (
            <span>{config.emoji}</span>
          )}
          <span>{config.title}</span>
        </CardTitle>
        <p className={`text-sm ${config.colorClass} opacity-70`}>{config.description}</p>
      </CardHeader>
      <CardContent>
        <div className="mb-3">
          <div className={`text-3xl font-bold tabular-nums ${config.colorClass}`}>
            {assetCount}
          </div>
          <div className="text-sm text-slate-400">
            {formatUSD(totalValue)}
          </div>
        </div>

        {displayAssets.length > 0 ? (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {displayAssets.slice(0, 10).map((asset, idx) => {
              const { textClass, emoji } = getAssetColor(asset, isHardMoney)
              const assetKey = `${asset.ticker}-${idx}`
              const isLP = isLPToken(asset.ticker, asset.name)
              const isExpanded = expandedLPs.has(assetKey)
              const lpComponents = isLP ? parseLPComponents(asset.ticker, asset.name) : []

              return (
                <div key={assetKey} className="space-y-1">
                  <div
                    className={`flex justify-between items-center text-sm py-1 border-b border-slate-700/50 last:border-0 ${isHardMoney ? 'rounded px-1 ' + (getHardMoneyType(asset.ticker) ? HARD_MONEY_COLORS[getHardMoneyType(asset.ticker)!].bg : '') : ''} ${isLP ? 'cursor-pointer hover:bg-slate-700/30 rounded transition-colors' : ''}`}
                    onClick={isLP ? () => toggleLP(assetKey, asset) : undefined}
                    role={isLP ? 'button' : undefined}
                    aria-expanded={isLP ? isExpanded : undefined}
                    tabIndex={isLP ? 0 : undefined}
                    onKeyDown={isLP ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        toggleLP(assetKey, asset)
                      }
                    } : undefined}
                  >
                    <div className="truncate pr-2 flex items-center gap-1">
                      {isLP && (
                        <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      )}
                      {emoji && <span className="text-xs">{emoji}</span>}
                      <span className={`font-medium ${textClass}`}>{asset.ticker}</span>
                      {isLP && (
                        <span className="text-xs bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded">LP</span>
                      )}
                      {asset.name !== asset.ticker && !isLP && (
                        <span className="text-slate-500 ml-1 hidden sm:inline">
                          ({asset.name.slice(0, 15)}{asset.name.length > 15 ? '...' : ''})
                        </span>
                      )}
                    </div>
                    <div className="text-right tabular-nums whitespace-nowrap">
                      <div className={textClass}>{formatNumber(asset.amount)}</div>
                      {asset.usd_value > 0 && (
                        <div className="text-xs text-slate-500">{formatUSD(asset.usd_value)}</div>
                      )}
                    </div>
                  </div>
                  {/* LP Expanded details - lazy loaded */}
                  {isLP && isExpanded && (
                    <div className="ml-4 pl-3 border-l-2 border-purple-500/30 py-2 text-xs space-y-1 bg-slate-800/30 rounded-r">
                      <div className="text-slate-400 font-medium">Liquidity Pool Token</div>
                      {lpData[assetKey] === 'loading' ? (
                        <div className="flex items-center gap-1.5 text-slate-400">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>Loading pool details…</span>
                        </div>
                      ) : lpData[assetKey] === 'error' ? (
                        <>
                          {lpComponents.length > 0 ? (
                            <div className="text-slate-300">
                              Pool: <span className="text-purple-300">{lpComponents.join(' / ')}</span>
                            </div>
                          ) : (
                            <div className="text-slate-500 italic">{asset.name}</div>
                          )}
                          <div className="text-slate-500 italic">Exact amounts unavailable</div>
                        </>
                      ) : lpData[assetKey] ? (
                        (() => {
                          const d = lpData[assetKey] as LPDecompositionResult
                          return (
                            <>
                              <div className="text-slate-300">
                                Pool: <span className="text-purple-300">{d.asset1_ticker} / {d.asset2_ticker}</span>
                              </div>
                              <div className="flex justify-between text-slate-300">
                                <span>{d.asset1_ticker}</span>
                                <span className="tabular-nums">
                                  {formatNumber(d.asset1_amount)}
                                  {d.asset1_usd > 0 && <span className="text-slate-500 ml-1">({formatUSD(d.asset1_usd)})</span>}
                                </span>
                              </div>
                              <div className="flex justify-between text-slate-300">
                                <span>{d.asset2_ticker}</span>
                                <span className="tabular-nums">
                                  {formatNumber(d.asset2_amount)}
                                  {d.asset2_usd > 0 && <span className="text-slate-500 ml-1">({formatUSD(d.asset2_usd)})</span>}
                                </span>
                              </div>
                              {d.total_usd > 0 && (
                                <div className="text-slate-400 border-t border-slate-700/50 pt-1 mt-1">
                                  Total: <span className="text-slate-200">{formatUSD(d.total_usd)}</span>
                                </div>
                              )}
                            </>
                          )
                        })()
                      ) : (
                        <>
                          {lpComponents.length > 0 ? (
                            <div className="text-slate-300">
                              Pool: <span className="text-purple-300">{lpComponents.join(' / ')}</span>
                            </div>
                          ) : (
                            <div className="text-slate-500 italic">{asset.name}</div>
                          )}
                          <div className="text-slate-500">Your share of liquidity in this pool</div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
            {displayAssets.length > 10 && (
              <div className="text-xs text-slate-500 text-center pt-2">
                +{displayAssets.length - 10} more tokens
              </div>
            )}
            {hiddenCount > 0 && (
              <div className="text-xs text-slate-600 text-center pt-1 italic">
                ({hiddenCount} NFTs/dust hidden)
              </div>
            )}
          </div>
        ) : assetCount > 0 ? (
          <div className="text-sm text-slate-500 italic">
            {hiddenCount} NFTs/collectibles (hidden)
          </div>
        ) : (
          <div className="text-sm text-slate-500 italic">
            No assets in this category
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Props for the {@link AssetBreakdownSummary} compact summary component.
 *
 * @property categories - The categorized asset data from wallet analysis
 */
interface AssetBreakdownSummaryProps {
  categories: Categories
}

/**
 * A compact inline summary showing asset counts and percentage allocation
 * for each category. Used in headers or condensed views where the full
 * AssetBreakdown card layout is too large.
 *
 * Renders a horizontal flex row with each category's emoji, count, and
 * percentage of total portfolio value.
 *
 * @param props - Component props
 * @param props.categories - Object with hard_money, algo, dollars, and shitcoin arrays
 */
export function AssetBreakdownSummary({ categories }: AssetBreakdownSummaryProps) {
  const totals = CATEGORY_CONFIGS.map(config => ({
    ...config,
    count: categories[config.key].length,
    value: categories[config.key].reduce((sum, a) => sum + a.usd_value, 0)
  }))

  const grandTotal = totals.reduce((sum, t) => sum + t.value, 0)

  return (
    <div className="flex flex-wrap gap-4">
      {totals.map((t) => (
        <div key={t.key} className="flex items-center gap-2">
          <span>{t.emoji}</span>
          <span className={`font-medium ${t.colorClass}`}>{t.count}</span>
          {grandTotal > 0 && (
            <span className="text-slate-500 text-sm">
              ({((t.value / grandTotal) * 100).toFixed(0)}%)
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
