'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatUSD, formatNumber } from '@/lib/utils'
import { Asset, Categories, CATEGORY_CONFIGS, getHardMoneyType, HARD_MONEY_COLORS, HardMoneyType } from '@/lib/types'

interface AssetBreakdownProps {
  categories: Categories
}

export function AssetBreakdown({ categories }: AssetBreakdownProps) {
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
        <Card className="border-orange-500/30 bg-gradient-to-br from-orange-500/5 via-yellow-500/5 to-slate-400/5 border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-2xl">
              <span className="flex gap-2">
                <span className="text-orange-500">₿</span>
                <span className="text-yellow-400">🥇</span>
                <span className="text-slate-300">🥈</span>
              </span>
              <span className="bg-gradient-to-r from-orange-500 via-yellow-400 to-slate-400 bg-clip-text text-transparent">
                Hard Money
              </span>
            </CardTitle>
            <p className="text-sm text-slate-400">Bitcoin, Gold, Silver</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Gold Card */}
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-yellow-600/20 to-yellow-900/20 border-2 border-yellow-500/30 p-6 hover:border-yellow-400/50 transition-all">
                <div className="absolute top-0 right-0 text-9xl opacity-10">🥇</div>
                <div className="relative z-10">
                  <div className="text-yellow-400 text-sm font-medium mb-2">GOLD</div>
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
                    <div className="text-yellow-600/50 text-sm italic">No gold holdings</div>
                  )}
                </div>
              </div>

              {/* Silver Card */}
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-slate-400/20 to-slate-700/20 border-2 border-slate-400/30 p-6 hover:border-slate-300/50 transition-all">
                <div className="absolute top-0 right-0 text-9xl opacity-10">🥈</div>
                <div className="relative z-10">
                  <div className="text-slate-300 text-sm font-medium mb-2">SILVER</div>
                  <div className="text-4xl font-bold text-slate-200 mb-1 tabular-nums">
                    {formatUSD(silverValue)}
                  </div>
                  <div className="space-y-1">
                    {silverAssets.map((asset, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-slate-300/70">{asset.ticker}</span>
                        <span className="text-slate-200 tabular-nums">{formatNumber(asset.amount)}</span>
                      </div>
                    ))}
                  </div>
                  {silverAssets.length === 0 && (
                    <div className="text-slate-600/50 text-sm italic">No silver holdings</div>
                  )}
                </div>
              </div>

              {/* Bitcoin Card */}
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-orange-600/20 to-orange-900/20 border-2 border-orange-500/30 p-6 hover:border-orange-400/50 transition-all">
                <div className="absolute top-0 right-0 text-9xl opacity-10">₿</div>
                <div className="relative z-10">
                  <div className="text-orange-400 text-sm font-medium mb-2">BITCOIN</div>
                  <div className="text-4xl font-bold text-orange-300 mb-1 tabular-nums">
                    {formatUSD(bitcoinValue)}
                  </div>
                  <div className="space-y-1">
                    {bitcoinAssets.map((asset, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-orange-200/70">{asset.ticker}</span>
                        <span className="text-orange-100 tabular-nums">{formatNumber(asset.amount)}</span>
                      </div>
                    ))}
                  </div>
                  {bitcoinAssets.length === 0 && (
                    <div className="text-orange-600/50 text-sm italic">No bitcoin holdings</div>
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

interface CategoryCardProps {
  config: typeof CATEGORY_CONFIGS[number]
  assets: Asset[]
}

// Get color styling for hard money assets
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

// Filter out insignificant assets for cleaner display (NFTs, dust, etc.)
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

function CategoryCard({ config, assets }: CategoryCardProps) {
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
              return (
                <div
                  key={`${asset.ticker}-${idx}`}
                  className={`flex justify-between items-center text-sm py-1 border-b border-slate-700/50 last:border-0 ${isHardMoney ? 'rounded px-1 ' + (getHardMoneyType(asset.ticker) ? HARD_MONEY_COLORS[getHardMoneyType(asset.ticker)!].bg : '') : ''}`}
                >
                  <div className="truncate pr-2 flex items-center gap-1">
                    {emoji && <span className="text-xs">{emoji}</span>}
                    <span className={`font-medium ${textClass}`}>{asset.ticker}</span>
                    {asset.name !== asset.ticker && (
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

interface AssetBreakdownSummaryProps {
  categories: Categories
}

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
