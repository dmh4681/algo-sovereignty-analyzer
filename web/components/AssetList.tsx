'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ChevronDown, Loader2 } from 'lucide-react'
import { formatUSD, formatNumber } from '@/lib/utils'
import { Asset, CategoryType, CATEGORY_CONFIGS, getHardMoneyType, HARD_MONEY_COLORS } from '@/lib/types'
import { getPaginatedAssets, ApiError } from '@/lib/api'

// Page size for loading more assets
const PAGE_SIZE = 20

// Number of items to show initially before Load More
const INITIAL_DISPLAY_COUNT = 10

interface AssetListProps {
  // The wallet address (needed for pagination API calls)
  address: string
  // Category configuration
  category: CategoryType
  // Initial assets to display (first batch from full analysis)
  initialAssets: Asset[]
  // Total number of assets in this category
  totalCount: number
  // Total USD value for the category
  totalUsd: number
  // Whether the category needs pagination (>50 assets)
  needsPagination: boolean
  // Optional callback when assets are loaded
  onAssetsLoaded?: (assets: Asset[]) => void
}

interface AssetItemProps {
  asset: Asset
  isHardMoney: boolean
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

// Detect LP (liquidity pool) tokens
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

function AssetItem({ asset, isHardMoney }: AssetItemProps) {
  const { textClass, emoji } = getAssetColor(asset, isHardMoney)
  const isLP = isLPToken(asset.ticker, asset.name)
  const hardMoneyType = isHardMoney ? getHardMoneyType(asset.ticker) : null

  return (
    <div
      className={`flex justify-between items-center text-sm py-1.5 border-b border-slate-700/50 last:border-0 ${
        isHardMoney && hardMoneyType ? HARD_MONEY_COLORS[hardMoneyType].bg + ' rounded px-1' : ''
      }`}
    >
      <div className="truncate pr-2 flex items-center gap-1">
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
  )
}

// Skeleton for loading assets
function AssetItemSkeleton() {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-slate-700/50">
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-24 hidden sm:block" />
      </div>
      <div className="text-right">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-3 w-16 mt-1" />
      </div>
    </div>
  )
}

export function AssetList({
  address,
  category,
  initialAssets,
  totalCount,
  totalUsd,
  needsPagination,
  onAssetsLoaded,
}: AssetListProps) {
  const config = CATEGORY_CONFIGS.find(c => c.key === category)!
  const isHardMoney = category === 'hard_money'

  // All loaded assets (starts with initial assets)
  const [assets, setAssets] = useState<Asset[]>(initialAssets)
  // Current page for pagination
  const [currentPage, setCurrentPage] = useState(1)
  // Loading state for Load More
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  // Error state
  const [error, setError] = useState<string | null>(null)
  // Track if we've reached the end
  const [hasMore, setHasMore] = useState(initialAssets.length < totalCount)

  // For infinite scroll (optional, enabled by scrolling)
  const loadMoreRef = useRef<HTMLDivElement>(null)
  const [useInfiniteScroll, setUseInfiniteScroll] = useState(false)

  // How many assets to display (for "show more" within initial data)
  const [displayCount, setDisplayCount] = useState(INITIAL_DISPLAY_COUNT)

  // Load more assets from the server
  const loadMoreAssets = useCallback(async () => {
    if (isLoadingMore || !hasMore) return

    setIsLoadingMore(true)
    setError(null)

    try {
      const nextPage = currentPage + 1
      const response = await getPaginatedAssets(address, category, nextPage, PAGE_SIZE)

      const newAssets = response.page.items as Asset[]
      setAssets(prev => [...prev, ...newAssets])
      setCurrentPage(nextPage)
      setHasMore(response.page.has_more)
      setDisplayCount(prev => prev + newAssets.length)

      if (onAssetsLoaded) {
        onAssetsLoaded([...assets, ...newAssets])
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to load more assets')
      }
    } finally {
      setIsLoadingMore(false)
    }
  }, [address, category, currentPage, hasMore, isLoadingMore, assets, onAssetsLoaded])

  // Infinite scroll observer
  useEffect(() => {
    if (!useInfiniteScroll || !loadMoreRef.current) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
          loadMoreAssets()
        }
      },
      { threshold: 0.1 }
    )

    observer.observe(loadMoreRef.current)

    return () => observer.disconnect()
  }, [useInfiniteScroll, hasMore, isLoadingMore, loadMoreAssets])

  // Show more from already-loaded assets (client-side)
  const showMoreLoaded = () => {
    const newDisplayCount = Math.min(displayCount + 10, assets.length)
    setDisplayCount(newDisplayCount)

    // If we've displayed all loaded assets and there are more on server, load them
    if (newDisplayCount >= assets.length && hasMore) {
      loadMoreAssets()
    }
  }

  // Assets to actually display
  const displayedAssets = assets.slice(0, displayCount)
  const remainingLoaded = assets.length - displayCount
  const remainingTotal = totalCount - displayCount

  return (
    <Card className={`${config.borderClass} ${config.bgClass} border`}>
      <CardHeader className="pb-2">
        <CardTitle className={`flex items-center gap-2 text-lg ${config.colorClass}`}>
          <span>{config.emoji}</span>
          <span>{config.title}</span>
          <span className="text-sm font-normal text-slate-400 ml-auto">
            {totalCount} assets
          </span>
        </CardTitle>
        <p className={`text-sm ${config.colorClass} opacity-70`}>{config.description}</p>
      </CardHeader>
      <CardContent>
        {/* Total value */}
        <div className="mb-3">
          <div className={`text-3xl font-bold tabular-nums ${config.colorClass}`}>
            {formatUSD(totalUsd)}
          </div>
        </div>

        {/* Asset list */}
        {displayedAssets.length > 0 ? (
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {displayedAssets.map((asset, idx) => (
              <AssetItem
                key={`${asset.ticker}-${idx}`}
                asset={asset}
                isHardMoney={isHardMoney}
              />
            ))}

            {/* Loading skeletons */}
            {isLoadingMore && (
              <>
                <AssetItemSkeleton />
                <AssetItemSkeleton />
                <AssetItemSkeleton />
              </>
            )}

            {/* Infinite scroll trigger */}
            {useInfiniteScroll && hasMore && (
              <div ref={loadMoreRef} className="h-4" />
            )}
          </div>
        ) : (
          <div className="text-sm text-slate-500 italic">
            No assets in this category
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
            {error}
            <button
              onClick={loadMoreAssets}
              className="ml-2 text-red-300 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Load More button */}
        {remainingTotal > 0 && !useInfiniteScroll && (
          <div className="mt-3 pt-3 border-t border-slate-700/50">
            <Button
              variant="ghost"
              size="sm"
              className={`w-full ${config.colorClass} hover:bg-slate-700/50`}
              onClick={remainingLoaded > 0 ? showMoreLoaded : loadMoreAssets}
              disabled={isLoadingMore}
            >
              {isLoadingMore ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-2" />
                  Load More ({remainingTotal} remaining)
                </>
              )}
            </Button>

            {/* Option to enable infinite scroll */}
            {needsPagination && !useInfiniteScroll && (
              <button
                onClick={() => setUseInfiniteScroll(true)}
                className="mt-2 w-full text-xs text-slate-500 hover:text-slate-400"
              >
                Enable infinite scroll
              </button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Skeleton component for loading state
export function AssetListSkeleton({ category }: { category: CategoryType }) {
  const config = CATEGORY_CONFIGS.find(c => c.key === category)!

  return (
    <Card className={`${config.borderClass} ${config.bgClass} border animate-pulse`}>
      <CardHeader className="pb-2">
        <CardTitle className={`flex items-center gap-2 text-lg ${config.colorClass}`}>
          <span>{config.emoji}</span>
          <span>{config.title}</span>
        </CardTitle>
        <Skeleton className="h-4 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-28 mb-4" />
        <div className="space-y-2">
          <AssetItemSkeleton />
          <AssetItemSkeleton />
          <AssetItemSkeleton />
          <AssetItemSkeleton />
        </div>
      </CardContent>
    </Card>
  )
}

// Compact summary for quick display before full list loads
interface AssetListSummaryProps {
  category: CategoryType
  count: number
  totalUsd: number
  isLoading?: boolean
}

export function AssetListSummary({ category, count, totalUsd, isLoading }: AssetListSummaryProps) {
  const config = CATEGORY_CONFIGS.find(c => c.key === category)!

  return (
    <Card className={`${config.borderClass} ${config.bgClass} border`}>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">{config.emoji}</span>
            <div>
              <div className={`font-medium ${config.colorClass}`}>{config.title}</div>
              <div className="text-xs text-slate-500">{config.description}</div>
            </div>
          </div>
          <div className="text-right">
            {isLoading ? (
              <>
                <Skeleton className="h-6 w-20 mb-1" />
                <Skeleton className="h-4 w-16" />
              </>
            ) : (
              <>
                <div className={`text-xl font-bold tabular-nums ${config.colorClass}`}>
                  {formatUSD(totalUsd)}
                </div>
                <div className="text-sm text-slate-400">{count} assets</div>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
