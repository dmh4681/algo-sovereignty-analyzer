"""
News Aggregator Service
Fetches and aggregates precious metals news from multiple RSS sources
"""

import feedparser
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import aiohttp


class NewsAggregator:
    """Fetches and aggregates precious metals news from multiple sources"""
    
    GOLD_SOURCES = [
        'https://www.kitco.com/rss/gold.xml',
        'https://www.mining.com/category/gold/feed/',
        'https://www.mining-technology.com/feed/',
        'https://www.marketwatch.com/rss/topstories',
    ]
    
    SILVER_SOURCES = [
        'https://www.kitco.com/rss/silver.xml',
        'https://www.mining.com/category/silver/feed/',
        'https://www.silverinstitute.org/feed/',
    ]
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_feed(self, url: str) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        try:
            async with self.session.get(url, timeout=10) as response:
                content = await response.text()
                feed = feedparser.parse(content)
                
                articles = []
                for entry in feed.entries[:10]:  # Limit to 10 most recent
                    articles.append({
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': feed.feed.get('title', url),
                    })
                return articles
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []
    
    async def fetch_all(self, metal: str, hours: int = 24) -> List[Dict]:
        """Fetch all news for a specific metal within timeframe"""
        sources = self.GOLD_SOURCES if metal == 'gold' else self.SILVER_SOURCES
        
        tasks = [self.fetch_feed(url) for url in sources]
        results = await asyncio.gather(*tasks)
        
        # Flatten and deduplicate
        all_articles = []
        seen_titles = set()
        
        for articles in results:
            for article in articles:
                if article['title'] not in seen_titles:
                    seen_titles.add(article['title'])
                    all_articles.append(article)
        
        # Filter by timeframe (basic check, can be enhanced)
        cutoff = datetime.now() - timedelta(hours=hours)
        
        return sorted(all_articles, key=lambda x: x.get('published', ''), reverse=True)
