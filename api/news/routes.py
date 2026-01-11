"""
News Curator API Routes
Exposes news aggregation and curation via FastAPI
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from .aggregator import NewsAggregator
from .curator import MetalsCurator

router = APIRouter(prefix="/news", tags=["news"])


# --- Pydantic Models ---

class ArticleBase(BaseModel):
    title: str
    summary: str
    link: str
    published: str
    source: str


class AnalyzedArticle(BaseModel):
    original: ArticleBase
    analysis: str
    sovereignty_score: int
    metal: str
    analyzed_at: str


class ArticlesResponse(BaseModel):
    articles: List[ArticleBase]
    count: int
    metal: str


class AnalyzeArticleRequest(BaseModel):
    article: ArticleBase
    metal: str = "gold"


class AnalyzeArticleResponse(BaseModel):
    success: bool
    result: Optional[AnalyzedArticle] = None
    error: Optional[str] = None


class CurateBatchRequest(BaseModel):
    metal: str = "gold"
    hours: int = 48
    limit: int = 5
    min_score: int = 5


class CurateBatchResponse(BaseModel):
    articles: List[AnalyzedArticle]
    count: int
    metal: str
    fetched_count: int


# --- Routes ---

@router.get("/articles", response_model=ArticlesResponse)
async def get_articles(
    metal: str = Query("gold", description="Metal type: gold, silver, or bitcoin"),
    hours: int = Query(48, description="Hours to look back"),
    limit: int = Query(10, description="Max articles to return")
):
    """
    Fetch recent hard money news articles.
    Returns raw articles without AI analysis.
    """
    if metal not in ("gold", "silver", "bitcoin"):
        raise HTTPException(status_code=400, detail="Metal must be 'gold', 'silver', or 'bitcoin'")

    try:
        async with NewsAggregator() as agg:
            articles = await agg.fetch_all(metal, hours=hours)

        # Limit results
        articles = articles[:limit]

        return ArticlesResponse(
            articles=[ArticleBase(**a) for a in articles],
            count=len(articles),
            metal=metal
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")


@router.post("/analyze", response_model=AnalyzeArticleResponse)
async def analyze_article(request: AnalyzeArticleRequest):
    """
    Analyze a single article through the sovereignty lens using Claude AI.
    """
    try:
        curator = MetalsCurator()
        result = await curator.analyze_article(
            request.article.model_dump(),
            request.metal
        )

        if result:
            return AnalyzeArticleResponse(
                success=True,
                result=AnalyzedArticle(
                    original=request.article,
                    analysis=result['analysis'],
                    sovereignty_score=result['sovereignty_score'],
                    metal=result['metal'],
                    analyzed_at=result['analyzed_at']
                )
            )
        else:
            return AnalyzeArticleResponse(
                success=False,
                error="Analysis failed"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.post("/curate", response_model=CurateBatchResponse)
async def curate_batch(request: CurateBatchRequest):
    """
    Fetch and analyze multiple articles, returning only high-signal ones.
    This is the main endpoint for getting curated news.
    """
    if request.metal not in ("gold", "silver", "bitcoin"):
        raise HTTPException(status_code=400, detail="Metal must be 'gold', 'silver', or 'bitcoin'")

    try:
        # Fetch articles
        async with NewsAggregator() as agg:
            articles = await agg.fetch_all(request.metal, hours=request.hours)

        if not articles:
            return CurateBatchResponse(
                articles=[],
                count=0,
                metal=request.metal,
                fetched_count=0
            )

        # Limit articles to analyze (to control API costs)
        to_analyze = articles[:request.limit]

        # Analyze with Claude
        curator = MetalsCurator()
        analyzed = await curator.curate_batch(
            to_analyze,
            request.metal,
            min_score=request.min_score
        )

        return CurateBatchResponse(
            articles=[
                AnalyzedArticle(
                    original=ArticleBase(**a['original']),
                    analysis=a['analysis'],
                    sovereignty_score=a['sovereignty_score'],
                    metal=a['metal'],
                    analyzed_at=a['analyzed_at']
                )
                for a in analyzed
            ],
            count=len(analyzed),
            metal=request.metal,
            fetched_count=len(articles)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Curation error: {str(e)}")


@router.get("/health")
async def news_health():
    """Health check for news service"""
    return {"status": "ok", "service": "news-curator"}
