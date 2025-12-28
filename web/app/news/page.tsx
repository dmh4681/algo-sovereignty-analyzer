'use client'

import { useState } from 'react'
import { useWallet } from '@txnlab/use-wallet-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2, Lock, Unlock, Newspaper, BookOpen, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import algosdk from 'algosdk'
import { getCuratedNews } from '@/lib/api'
import { AnalyzedArticle } from '@/lib/types'

type MetalType = 'gold' | 'silver'

function SovereigntyBadge({ score }: { score: number }) {
  let color = 'bg-red-500/20 text-red-400 border-red-500/50'

  if (score >= 8) {
    color = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
  } else if (score >= 6) {
    color = 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
  } else if (score >= 4) {
    color = 'bg-orange-500/20 text-orange-400 border-orange-500/50'
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium border ${color}`}>
      {score}/10
    </span>
  )
}

function ArticleCard({ article, expanded, onToggle }: {
  article: AnalyzedArticle
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <Card className="mb-4 hover:border-slate-700 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="text-lg leading-tight mb-2">
              <a
                href={article.original.link}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-yellow-400 transition-colors"
              >
                {article.original.title}
              </a>
            </CardTitle>
            <CardDescription className="flex items-center gap-2 text-xs">
              <span className="text-slate-500">{article.original.source}</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-500">{article.original.published}</span>
            </CardDescription>
          </div>
          <SovereigntyBadge score={article.sovereignty_score} />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-slate-400 text-sm mb-3 line-clamp-2">
          {article.original.summary}
        </p>

        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="text-yellow-500 hover:text-yellow-400 hover:bg-yellow-500/10 p-0 h-auto"
        >
          {expanded ? 'Hide Analysis' : 'View Sovereignty Analysis'}
        </Button>

        {expanded && (
          <div className="mt-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="prose prose-invert prose-sm max-w-none">
              <div
                className="text-slate-300 text-sm whitespace-pre-wrap"
                dangerouslySetInnerHTML={{
                  __html: article.analysis
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/### (.*)/g, '<h4 class="text-yellow-400 font-semibold mt-4 mb-2">$1</h4>')
                    .replace(/## (.*)/g, '<h3 class="text-yellow-500 font-bold mt-4 mb-2">$1</h3>')
                    .replace(/- (.*)/g, '<li class="ml-4">$1</li>')
                }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function LoadingCard() {
  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <Skeleton className="h-6 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/4" />
          </div>
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-2/3" />
      </CardContent>
    </Card>
  )
}

export default function NewsPage() {
  const { activeAccount, signTransactions } = useWallet()
  const [isUnlocked, setIsUnlocked] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // News curator state
  const [metal, setMetal] = useState<MetalType>('gold')
  const [articles, setArticles] = useState<AnalyzedArticle[]>([])
  const [fetchingNews, setFetchingNews] = useState(false)
  const [newsError, setNewsError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [fetchedCount, setFetchedCount] = useState(0)

  const algodClient = new algosdk.Algodv2('', 'https://mainnet-api.algonode.cloud', '')

  const handleUnlock = async () => {
    if (!activeAccount) {
      setError("Please connect your wallet first.")
      return
    }

    setIsLoading(true)
    setError(null)

    let txId = ''

    try {
      const suggestedParams = await algodClient.getTransactionParams().do()

      const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
        sender: activeAccount.address,
        receiver: activeAccount.address, // Sending to self for demo
        amount: 1000000, // 1 ALGO
        suggestedParams,
        note: new TextEncoder().encode("News Intelligence Unlock"),
      })

      const encodedTxn = algosdk.encodeUnsignedTransaction(txn)
      const signedTxns = await signTransactions([encodedTxn])
      const validSignedTxns = signedTxns.filter((stxn): stxn is Uint8Array => stxn !== null)

      if (validSignedTxns.length === 0) {
        throw new Error("Failed to sign transaction")
      }

      const signedTxn = validSignedTxns[0]
      const response = await algodClient.sendRawTransaction(signedTxn).do()
      txId = response.txid
      console.log("Transaction sent with ID:", txId)

      await algosdk.waitForConfirmation(algodClient, txId, 20)

      setIsUnlocked(true)

    } catch (e: any) {
      console.error("Transaction failed", e)
      let errorMessage = e.message || "Transaction failed. Please try again."

      if (txId) {
        errorMessage += ` (TxID: ${txId})`
        if (e.message && e.message.includes("not confirmed")) {
          errorMessage = `Transaction sent (ID: ${txId}) but not confirmed in time. Please check your wallet.`
        }
      }

      setError(errorMessage)
      alert(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchCuratedNews = async () => {
    setFetchingNews(true)
    setNewsError(null)
    setArticles([])

    try {
      const result = await getCuratedNews({
        metal,
        hours: 48,
        limit: 5,
        min_score: 4,
      })

      setArticles(result.articles)
      setFetchedCount(result.fetched_count)
    } catch (err) {
      setNewsError(err instanceof Error ? err.message : 'Failed to fetch news')
    } finally {
      setFetchingNews(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
          Precious Metals Intelligence
        </h1>
        <p className="text-xl text-gray-400">
          AI-curated gold and silver news, analyzed through the sovereignty lens.
        </p>
      </div>

      {/* Research Report Banner */}
      <Card className="bg-gradient-to-r from-purple-500/10 to-orange-500/10 border-purple-500/30 mb-8">
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <BookOpen className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-200">2025 Algorand Research Report</h3>
                <p className="text-sm text-slate-400">Comprehensive analysis: decentralization, Project King Safety, and ecosystem developments</p>
              </div>
            </div>
            <Link href="/research">
              <Button className="bg-purple-500 hover:bg-purple-600 whitespace-nowrap">
                Read Report
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {!isUnlocked ? (
        <Card className="bg-slate-900/50 border-slate-800 max-w-md mx-auto">
          <CardHeader className="text-center">
            <div className="mx-auto bg-slate-800 p-4 rounded-full mb-4 w-16 h-16 flex items-center justify-center">
              <Lock className="w-8 h-8 text-slate-400" />
            </div>
            <CardTitle className="text-2xl text-white">Unlock News Intelligence</CardTitle>
            <CardDescription>
              Access AI-curated precious metals news for 1 ALGO.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4 bg-red-900/20 border-red-900">
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button
              className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white font-bold py-6 text-lg"
              onClick={handleUnlock}
              disabled={isLoading || !activeAccount}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Unlock className="mr-2 h-5 w-5" />
                  Pay 1 ALGO to Unlock
                </>
              )}
            </Button>
            {!activeAccount && (
              <p className="text-center text-sm text-yellow-500 mt-4">
                Please connect your wallet to proceed.
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-8 animate-in fade-in duration-500">
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-center">
            <p className="text-green-400 font-medium flex items-center justify-center gap-2">
              <Unlock className="w-4 h-4" />
              News Intelligence Unlocked
            </p>
          </div>

          {/* News Curator Interface */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 rounded-xl bg-yellow-500/20 text-yellow-400">
                  <Newspaper className="w-8 h-8" />
                </div>
                <div>
                  <CardTitle className="text-2xl text-white">Sovereignty News Curator</CardTitle>
                  <CardDescription>Select metal and fetch AI-analyzed articles</CardDescription>
                </div>
              </div>

              <div className="flex items-center gap-4 mt-4">
                <div className="flex gap-2">
                  <Button
                    variant={metal === 'gold' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setMetal('gold')}
                    className={metal === 'gold' ? 'bg-yellow-600 hover:bg-yellow-700' : ''}
                  >
                    Gold
                  </Button>
                  <Button
                    variant={metal === 'silver' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setMetal('silver')}
                    className={metal === 'silver' ? 'bg-slate-500 hover:bg-slate-600' : ''}
                  >
                    Silver
                  </Button>
                </div>

                <Button
                  onClick={fetchCuratedNews}
                  disabled={fetchingNews}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {fetchingNews ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    'Fetch & Analyze'
                  )}
                </Button>
              </div>
            </CardHeader>

            <CardContent>
              {newsError && (
                <div className="p-4 mb-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
                  {newsError}
                </div>
              )}

              {fetchingNews && (
                <div>
                  <p className="text-slate-400 text-sm mb-4">
                    Fetching news and analyzing with Claude AI... This may take 30-60 seconds.
                  </p>
                  <LoadingCard />
                  <LoadingCard />
                  <LoadingCard />
                </div>
              )}

              {!fetchingNews && articles.length === 0 && !newsError && (
                <div className="text-center py-8 text-slate-400">
                  <p className="text-4xl mb-2">{metal === 'gold' ? '🥇' : '🥈'}</p>
                  <p>Click &ldquo;Fetch & Analyze&rdquo; to get curated {metal} news</p>
                  <p className="text-sm mt-2 text-slate-500">
                    Articles are scored 0-10 based on sovereignty relevance
                  </p>
                </div>
              )}

              {!fetchingNews && articles.length > 0 && (
                <div>
                  <p className="text-slate-400 text-sm mb-4">
                    Showing {articles.length} high-signal articles from {fetchedCount} fetched
                  </p>

                  {articles.map((article, index) => (
                    <ArticleCard
                      key={index}
                      article={article}
                      expanded={expandedId === index}
                      onToggle={() => setExpandedId(expandedId === index ? null : index)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
