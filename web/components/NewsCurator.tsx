'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { getCuratedNews, getNewsArticles } from '@/lib/api'
import { AnalyzedArticle, NewsArticle } from '@/lib/types'

type MetalType = 'gold' | 'silver' | 'bitcoin'

function SovereigntyBadge({ score }: { score: number }) {
  let color = 'bg-red-500/20 text-red-400 border-red-500/50'
  let emoji = ''

  if (score >= 8) {
    color = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
    emoji = ''
  } else if (score >= 6) {
    color = 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
    emoji = ''
  } else if (score >= 4) {
    color = 'bg-orange-500/20 text-orange-400 border-orange-500/50'
    emoji = ''
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium border ${color}`}>
      {emoji} {score}/10
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

export default function NewsCurator() {
  const [metal, setMetal] = useState<MetalType>('gold')
  const [articles, setArticles] = useState<AnalyzedArticle[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [fetchedCount, setFetchedCount] = useState(0)

  const fetchCuratedNews = async () => {
    setLoading(true)
    setError(null)
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
      setError(err instanceof Error ? err.message : 'Failed to fetch news')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">{metal === 'gold' ? '' : metal === 'silver' ? '' : '₿'}</span>
              Sovereignty News Curator
            </CardTitle>
            <CardDescription className="mt-1">
              AI-analyzed hard money news through the sovereignty lens
            </CardDescription>
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
            <Button
              variant={metal === 'bitcoin' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setMetal('bitcoin')}
              className={metal === 'bitcoin' ? 'bg-orange-500 hover:bg-orange-600' : ''}
            >
              Bitcoin
            </Button>
          </div>

          <Button
            onClick={fetchCuratedNews}
            disabled={loading}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {loading ? 'Analyzing...' : 'Fetch & Analyze'}
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <div className="p-4 mb-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {loading && (
          <div>
            <p className="text-slate-400 text-sm mb-4">
              Fetching news and analyzing with Claude AI... This may take 30-60 seconds.
            </p>
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </div>
        )}

        {!loading && articles.length === 0 && !error && (
          <div className="text-center py-8 text-slate-400">
            <p className="text-4xl mb-2">{metal === 'gold' ? '' : metal === 'silver' ? '' : '₿'}</p>
            <p>Click &ldquo;Fetch & Analyze&rdquo; to get curated {metal} news</p>
            <p className="text-sm mt-2 text-slate-500">
              Articles are scored 0-10 based on sovereignty relevance
            </p>
          </div>
        )}

        {!loading && articles.length > 0 && (
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
  )
}
