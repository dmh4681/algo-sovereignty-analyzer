'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Coins,
  TrendingUp,
  TrendingDown,
  Store,
  Award,
  ExternalLink,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Package,
} from 'lucide-react'
import {
  getPremiumSummary,
  getPremiumProducts,
  compareProductPrices,
  getBestDeals,
  getDealerLeaderboard,
  PremiumProduct,
  ProductComparison,
  DealerRanking,
  PremiumSummary,
} from '@/lib/api'

type ViewMode = 'overview' | 'gold' | 'silver' | 'dealers'
type MetalFilter = 'all' | 'gold' | 'silver'

export function PremiumTracker() {
  const [view, setView] = useState<ViewMode>('overview')
  const [metalFilter, setMetalFilter] = useState<MetalFilter>('all')
  const [summary, setSummary] = useState<PremiumSummary | null>(null)
  const [products, setProducts] = useState<PremiumProduct[]>([])
  const [bestDeals, setBestDeals] = useState<(PremiumProduct & { premium_percent: number; dealer_name: string; price: number })[]>([])
  const [dealerRankings, setDealerRankings] = useState<DealerRanking[]>([])
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null)
  const [comparison, setComparison] = useState<ProductComparison | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load summary and best deals
  useEffect(() => {
    if (view === 'overview') {
      setLoading(true)
      Promise.all([
        getPremiumSummary(),
        getBestDeals(undefined, 8),
      ])
        .then(([summaryRes, dealsRes]) => {
          setSummary(summaryRes.stats)
          setBestDeals(dealsRes.deals as any)
          setError(null)
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }
  }, [view])

  // Load products by metal
  useEffect(() => {
    if (view === 'gold' || view === 'silver') {
      setLoading(true)
      const metal = view as 'gold' | 'silver'
      Promise.all([
        getPremiumProducts(metal),
        getBestDeals(metal, 10),
      ])
        .then(([productsRes, dealsRes]) => {
          setProducts(productsRes.products)
          setBestDeals(dealsRes.deals as any)
          setError(null)
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }
  }, [view])

  // Load dealer rankings
  useEffect(() => {
    if (view === 'dealers') {
      setLoading(true)
      const metal = metalFilter === 'all' ? undefined : metalFilter
      getDealerLeaderboard(metal)
        .then((res) => {
          setDealerRankings(res.rankings)
          setError(null)
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }
  }, [view, metalFilter])

  // Load product comparison
  useEffect(() => {
    if (selectedProduct) {
      compareProductPrices(selectedProduct)
        .then((res) => setComparison(res.comparison))
        .catch(() => setComparison(null))
    } else {
      setComparison(null)
    }
  }, [selectedProduct])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Coins className="h-8 w-8 text-amber-500" />
            Physical Premium Tracker
          </h1>
          <p className="text-slate-400 mt-1">
            Compare premiums on gold and silver products across dealers
          </p>
        </div>

        {summary && (
          <div className="flex gap-4 text-sm">
            <div className="text-center">
              <div className="text-amber-500 font-bold">${summary.spot_prices.gold?.toLocaleString()}</div>
              <div className="text-slate-500">Gold/oz</div>
            </div>
            <div className="text-center">
              <div className="text-slate-400 font-bold">${summary.spot_prices.silver?.toFixed(2)}</div>
              <div className="text-slate-500">Silver/oz</div>
            </div>
          </div>
        )}
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 border-b border-slate-700 pb-2">
        {[
          { id: 'overview', label: 'Overview', icon: Package },
          { id: 'gold', label: 'Gold', icon: Coins, color: 'text-amber-500' },
          { id: 'silver', label: 'Silver', icon: Coins, color: 'text-slate-400' },
          { id: 'dealers', label: 'Dealers', icon: Store },
        ].map(({ id, label, icon: Icon, color }) => (
          <Button
            key={id}
            variant={view === id ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setView(id as ViewMode)}
            className={`gap-2 ${color || ''}`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Button>
        ))}
      </div>

      {error && (
        <Card className="bg-red-900/20 border-red-800">
          <CardContent className="pt-6">
            <p className="text-red-400 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {error}
            </p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-slate-700 rounded w-1/3" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-32 bg-slate-700 rounded" />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Overview View */}
          {view === 'overview' && summary && (
            <div className="space-y-6">
              {/* Summary Stats */}
              <div className="grid gap-4 md:grid-cols-4">
                <StatCard
                  label="Products Tracked"
                  value={summary.product_count}
                  icon={Package}
                />
                <StatCard
                  label="Dealers"
                  value={summary.dealer_count}
                  icon={Store}
                />
                <StatCard
                  label="Avg Gold Premium"
                  value={`${summary.avg_premiums.gold?.toFixed(1)}%`}
                  icon={Coins}
                  color="amber"
                />
                <StatCard
                  label="Avg Silver Premium"
                  value={`${summary.avg_premiums.silver?.toFixed(1)}%`}
                  icon={Coins}
                  color="slate"
                />
              </div>

              {/* Best Deals */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Award className="h-5 w-5 text-green-500" />
                    Best Deals Right Now
                  </CardTitle>
                  <CardDescription>
                    Products with the lowest premiums over spot
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                    {bestDeals.map((deal: any) => (
                      <BestDealCard
                        key={deal.id}
                        name={deal.name}
                        metal={deal.metal}
                        price={deal.price}
                        premiumPercent={deal.premium_percent}
                        dealer={deal.dealer_name}
                        onClick={() => setSelectedProduct(deal.id)}
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Gold/Silver Products View */}
          {(view === 'gold' || view === 'silver') && (
            <div className="space-y-6">
              {/* Best Deals for this metal */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className={`flex items-center gap-2 ${view === 'gold' ? 'text-amber-500' : 'text-slate-300'}`}>
                    <Award className="h-5 w-5 text-green-500" />
                    Best {view === 'gold' ? 'Gold' : 'Silver'} Deals
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                    {bestDeals.map((deal: any) => (
                      <BestDealCard
                        key={deal.id}
                        name={deal.name}
                        metal={deal.metal}
                        price={deal.price}
                        premiumPercent={deal.premium_percent}
                        dealer={deal.dealer_name}
                        onClick={() => setSelectedProduct(deal.id)}
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Product List */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">All {view === 'gold' ? 'Gold' : 'Silver'} Products</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                    {products.map((product) => (
                      <Button
                        key={product.id}
                        variant="outline"
                        className="h-auto py-3 justify-between"
                        onClick={() => setSelectedProduct(product.id)}
                      >
                        <span className="text-left">
                          <div className="font-medium">{product.name}</div>
                          <div className="text-xs text-slate-500">
                            {product.weight_oz} oz | {product.product_type}
                          </div>
                        </span>
                        <span className="text-xs text-slate-400">
                          {product.typical_premium_low}-{product.typical_premium_high}%
                        </span>
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Dealers View */}
          {view === 'dealers' && (
            <div className="space-y-6">
              {/* Metal Filter */}
              <div className="flex gap-2">
                {(['all', 'gold', 'silver'] as const).map((filter) => (
                  <Button
                    key={filter}
                    variant={metalFilter === filter ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setMetalFilter(filter)}
                  >
                    {filter === 'all' ? 'All Products' : filter === 'gold' ? 'Gold Only' : 'Silver Only'}
                  </Button>
                ))}
              </div>

              {/* Dealer Rankings */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Award className="h-5 w-5 text-amber-500" />
                    Dealer Leaderboard
                  </CardTitle>
                  <CardDescription>
                    Ranked by average premium (lower is better)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {dealerRankings.map((ranking, index) => (
                      <DealerCard
                        key={ranking.dealer.id}
                        rank={index + 1}
                        name={ranking.dealer.name}
                        website={ranking.dealer.website}
                        avgPremium={ranking.avg_premium_percent}
                        productsTracked={ranking.products_tracked}
                        bestFor={ranking.best_for}
                        shippingInfo={ranking.dealer.shipping_info}
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Product Comparison Modal */}
          {selectedProduct && comparison && (
            <Card className="bg-slate-800/50 border-amber-600/50">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Coins className={comparison.product.metal === 'gold' ? 'text-amber-500' : 'text-slate-400'} />
                    {comparison.product.name}
                  </CardTitle>
                  <CardDescription>
                    Spot: ${comparison.spot_price.toFixed(2)}/oz | Melt Value: ${comparison.melt_value.toFixed(2)}
                  </CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setSelectedProduct(null)}>
                  Close
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {comparison.prices.map((price, index) => (
                    <div
                      key={price.id}
                      className={`flex items-center justify-between p-3 rounded ${
                        index === 0 && price.in_stock
                          ? 'bg-green-900/20 border border-green-600/50'
                          : 'bg-slate-900/50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {index === 0 && price.in_stock && (
                          <Award className="h-5 w-5 text-green-500" />
                        )}
                        <div>
                          <div className="font-medium text-white">{price.dealer_name}</div>
                          <div className="text-xs text-slate-500">{price.shipping_info}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-white">${price.price.toFixed(2)}</div>
                        <div className={`text-sm ${price.premium_percent < 20 ? 'text-green-500' : price.premium_percent < 30 ? 'text-yellow-500' : 'text-red-500'}`}>
                          +{price.premium_percent.toFixed(1)}%
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {price.in_stock ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <a
                          href={price.dealer_website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-400 hover:text-white"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}

// Sub-components

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'amber',
}: {
  label: string
  value: string | number
  icon: React.ElementType
  color?: 'amber' | 'green' | 'slate'
}) {
  const colorClasses = {
    amber: 'text-amber-500',
    green: 'text-green-500',
    slate: 'text-slate-400',
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="pt-4">
        <div className="flex items-center gap-3">
          <Icon className={`h-8 w-8 ${colorClasses[color]}`} />
          <div>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-xs text-slate-400">{label}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function BestDealCard({
  name,
  metal,
  price,
  premiumPercent,
  dealer,
  onClick,
}: {
  name: string
  metal: 'gold' | 'silver'
  price: number
  premiumPercent: number
  dealer: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="text-left p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-amber-500/50 transition-all"
    >
      <div className={`font-medium ${metal === 'gold' ? 'text-amber-500' : 'text-slate-300'}`}>
        {name}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-xl font-bold text-white">${price.toFixed(2)}</span>
        <span className={`text-sm ${premiumPercent < 15 ? 'text-green-500' : premiumPercent < 25 ? 'text-yellow-500' : 'text-red-500'}`}>
          +{premiumPercent.toFixed(1)}%
        </span>
      </div>
      <div className="text-xs text-slate-500 mt-1">@ {dealer}</div>
    </button>
  )
}

function DealerCard({
  rank,
  name,
  website,
  avgPremium,
  productsTracked,
  bestFor,
  shippingInfo,
}: {
  rank: number
  name: string
  website: string
  avgPremium: number
  productsTracked: number
  bestFor: string[]
  shippingInfo: string
}) {
  return (
    <div className="flex items-center gap-4 p-4 bg-slate-900/50 rounded-lg">
      <div className={`text-2xl font-bold ${rank === 1 ? 'text-amber-500' : rank === 2 ? 'text-slate-300' : rank === 3 ? 'text-amber-700' : 'text-slate-500'}`}>
        #{rank}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-white">{name}</span>
          <a
            href={website}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-500 hover:text-white"
          >
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
        <div className="text-xs text-slate-500 mt-1">
          {shippingInfo} | {productsTracked} products tracked
        </div>
        {bestFor.length > 0 && (
          <div className="flex gap-1 mt-1">
            {bestFor.map((category) => (
              <span
                key={category}
                className="text-xs bg-slate-700 px-2 py-0.5 rounded text-slate-300"
              >
                {category}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="text-right">
        <div className={`text-xl font-bold ${avgPremium < 15 ? 'text-green-500' : avgPremium < 25 ? 'text-yellow-500' : 'text-red-500'}`}>
          {avgPremium.toFixed(1)}%
        </div>
        <div className="text-xs text-slate-500">avg premium</div>
      </div>
    </div>
  )
}
