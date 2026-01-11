"""
News Aggregator Service
Fetches and aggregates precious metals news from multiple RSS sources
"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import aiohttp
import re
import html


class NewsAggregator:
    """Fetches and aggregates precious metals news from multiple sources"""

    # Updated RSS feeds - tested November 2024
    GOLD_SOURCES = [
        # Kitco mining news
        'https://www.kitco.com/news/category/mining/rss',
        # Mining.com main feed
        'https://www.mining.com/feed/',
        # Google News RSS for gold
        'https://news.google.com/rss/search?q=gold+price+mining&hl=en-US&gl=US&ceid=US:en',
        # Reddit r/Gold (always works)
        'https://www.reddit.com/r/Gold/.rss',
    ]

    SILVER_SOURCES = [
        # Kitco mining (covers silver too)
        'https://www.kitco.com/news/category/mining/rss',
        # Google News RSS for silver
        'https://news.google.com/rss/search?q=silver+price+mining&hl=en-US&gl=US&ceid=US:en',
        # Reddit r/Silverbugs
        'https://www.reddit.com/r/Silverbugs/.rss',
    ]

    BITCOIN_SOURCES = [
        'https://news.google.com/rss/search?q=bitcoin+price&hl=en-US&gl=US&ceid=US:en',
        'https://www.reddit.com/r/Bitcoin/.rss',
        'https://www.reddit.com/r/BitcoinMarkets/.rss',
        'https://bitcoinmagazine.com/feed',
    ]

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsCurator/1.0)'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags and decode HTML entities"""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities like &nbsp;, &amp;, etc.
        clean = html.unescape(clean)
        return clean.strip()

    def _parse_rss(self, content: str, source_url: str) -> List[Dict]:
        """Parse RSS/Atom feed XML"""
        articles = []
        try:
            root = ET.fromstring(content)

            # Try RSS 2.0 format
            channel = root.find('channel')
            if channel is not None:
                feed_title = channel.findtext('title', source_url)
                for item in channel.findall('item')[:10]:
                    articles.append({
                        'title': item.findtext('title', ''),
                        'summary': self._strip_html(item.findtext('description', '')),
                        'link': item.findtext('link', ''),
                        'published': item.findtext('pubDate', ''),
                        'source': feed_title,
                    })
                return articles

            # Try Atom format
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            feed_title = root.findtext('atom:title', source_url, ns)
            if feed_title == source_url:
                feed_title = root.findtext('title', source_url)

            entries = root.findall('atom:entry', ns)
            if not entries:
                entries = root.findall('entry')

            for entry in entries[:10]:
                link = ''
                link_elem = entry.find('atom:link', ns)
                if link_elem is None:
                    link_elem = entry.find('link')
                if link_elem is not None:
                    link = link_elem.get('href', link_elem.text or '')

                articles.append({
                    'title': entry.findtext('atom:title', '', ns) or entry.findtext('title', ''),
                    'summary': self._strip_html(
                        entry.findtext('atom:summary', '', ns) or entry.findtext('summary', '')
                    ),
                    'link': link,
                    'published': entry.findtext('atom:published', '', ns) or entry.findtext('published', ''),
                    'source': feed_title,
                })

        except ET.ParseError as e:
            print(f"XML parse error for {source_url}: {e}")

        return articles

    async def fetch_feed(self, url: str) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with self.session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    print(f"HTTP {response.status} for {url}")
                    return []
                content = await response.text()
                return self._parse_rss(content, url)
        except asyncio.TimeoutError:
            print(f"Timeout fetching {url}")
            return []
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []

    async def fetch_all(self, metal: str, hours: int = 24) -> List[Dict]:
        """Fetch all news for a specific metal within timeframe"""
        if metal == 'gold':
            sources = self.GOLD_SOURCES
        elif metal == 'silver':
            sources = self.SILVER_SOURCES
        else:  # bitcoin
            sources = self.BITCOIN_SOURCES

        tasks = [self.fetch_feed(url) for url in sources]
        results = await asyncio.gather(*tasks)

        # Flatten and deduplicate
        all_articles = []
        seen_titles = set()

        for articles in results:
            for article in articles:
                title = article['title'].strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_articles.append(article)

        return sorted(all_articles, key=lambda x: x.get('published', ''), reverse=True)
