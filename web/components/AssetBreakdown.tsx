'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatUSD, formatNumber } from '@/lib/utils'
import { Asset, Categories, CATEGORY_CONFIGS, getHardMoneyType, HARD_MONEY_COLORS, HardMoneyType } from '@/lib/types'

interface AssetBreakdownProps {
  categories: Categories
}

export function AssetBreakdown({ categories }: AssetBreakdownProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {CATEGORY_CONFIGS.map((config) => (
        <CategoryCard
          key={config.key}
          config={config}
          assets={categories[config.key]}
        />
      ))}
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
