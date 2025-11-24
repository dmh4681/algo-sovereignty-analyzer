"""
News Curator Test
Run with: python -m api.news.test
"""

import asyncio
import os
from pathlib import Path

# Find project root and load .env
project_root = Path(__file__).parent.parent.parent
env_file = project_root / '.env'

if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

from .aggregator import NewsAggregator
from .curator import MetalsCurator


# Sample articles for testing when RSS feeds are unreachable
SAMPLE_ARTICLES = [
    {
        'title': 'Central Banks Add 290 Tonnes of Gold in Q3, Led by BRICS Nations',
        'summary': 'Central banks continued their gold-buying spree in Q3 2024, adding 290 tonnes to reserves. China, Turkey, and India led purchases as de-dollarization accelerates.',
        'link': 'https://example.com/central-bank-gold',
        'published': '2024-11-23',
        'source': 'Kitco News'
    },
    {
        'title': 'Gold Hits Record $2,100 as Fed Signals Rate Cuts Ahead',
        'summary': 'Spot gold reached all-time highs following Fed comments suggesting multiple rate cuts in 2024. Analysts see continued upside as real rates turn negative.',
        'link': 'https://example.com/gold-record',
        'published': '2024-11-22',
        'source': 'Mining.com'
    },
    {
        'title': 'Newmont Reports Strong Q3: AISC Drops to $1,150/oz',
        'summary': 'Mining giant Newmont announced Q3 results showing improved all-in sustaining costs and increased production guidance for 2025.',
        'link': 'https://example.com/newmont-q3',
        'published': '2024-11-21',
        'source': 'Mining Technology'
    },
    {
        'title': 'Treasury Yields Surge, Testing Gold Support Levels',
        'summary': 'Rising treasury yields put pressure on gold prices, but physical demand from Asia remains strong. Analysts watching $2,000 support.',
        'link': 'https://example.com/yields-gold',
        'published': '2024-11-20',
        'source': 'Kitco News'
    },
    {
        'title': 'Silver Deficit Widens to 200M oz as Industrial Demand Soars',
        'summary': 'The Silver Institute reports structural deficit expanding due to solar panel and EV demand. Above-ground inventories at multi-decade lows.',
        'link': 'https://example.com/silver-deficit',
        'published': '2024-11-19',
        'source': 'Silver Institute'
    },
]


async def test_single_article():
    """Fetch 5 gold articles and analyze the first one"""

    print("\n" + "=" * 60)
    print("NEWS CURATOR TEST")
    print("=" * 60)

    # Step 1: Fetch articles
    print("\n[1/3] Fetching gold news from RSS feeds...")

    async with NewsAggregator() as agg:
        articles = await agg.fetch_all('gold', hours=48)

    if not articles:
        print("      RSS feeds unreachable, using sample data...")
        articles = SAMPLE_ARTICLES

    print(f"      Found {len(articles)} articles")

    # Show top 5 articles
    print("\n[2/3] Top 5 articles:")
    for i, article in enumerate(articles[:5], 1):
        title = article['title'][:50] + "..." if len(article['title']) > 50 else article['title']
        print(f"      {i}. {title}")
        print(f"         Source: {article['source']}")

    # Step 2: Analyze first article
    print("\n[3/3] Analyzing first article with Claude...")
    print("      (This takes 5-10 seconds)")

    curator = MetalsCurator()
    result = await curator.analyze_article(articles[0], 'gold')

    if not result:
        print("ERROR: Analysis failed. Check ANTHROPIC_API_KEY.")
        return False

    # Print results
    print("\n" + "=" * 60)
    print("ANALYSIS RESULT")
    print("=" * 60)

    print(f"\nOriginal: {result['original']['title']}")
    print(f"Source:   {result['original']['source']}")
    print(f"\nSovereignty Score: {result['sovereignty_score']}/10")

    print("\n" + "-" * 60)
    print("CLAUDE'S ANALYSIS:")
    print("-" * 60)
    print(result['analysis'])

    print("\n" + "=" * 60)
    print("TEST COMPLETE - News curator is working!")
    print("=" * 60)

    return True


async def test_rss_only():
    """Test just the RSS fetching (no API key needed)"""
    print("\n" + "=" * 60)
    print("RSS FEED TEST (no API key required)")
    print("=" * 60)

    print("\nFetching gold news from RSS feeds...")

    async with NewsAggregator() as agg:
        articles = await agg.fetch_all('gold', hours=48)

    if not articles:
        print("NOTE: RSS feeds unreachable (network restricted)")
        print("Using sample articles for demonstration...\n")
        articles = SAMPLE_ARTICLES

    print(f"SUCCESS: Found {len(articles)} articles\n")

    print("Top 5 articles:")
    for i, article in enumerate(articles[:5], 1):
        title = article['title'][:55] + "..." if len(article['title']) > 55 else article['title']
        print(f"  {i}. {title}")
        print(f"     Source: {article['source']}")

    print("\n" + "=" * 60)
    print("RSS feeds working! Add ANTHROPIC_API_KEY for full test.")
    print("=" * 60)
    return True


def main():
    """Entry point"""
    import sys

    # Check for --rss-only flag
    if '--rss-only' in sys.argv:
        asyncio.run(test_rss_only())
        return

    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("=" * 60)
        print("SETUP REQUIRED: ANTHROPIC_API_KEY not found")
        print("=" * 60)
        print()
        print("To test RSS feeds only (no API key needed):")
        print("  python -m api.news.test --rss-only")
        print()
        print("For full test with Claude analysis:")
        print()
        print("Option 1: Create .env file in project root:")
        print(f"  cp {project_root}/.env.example {project_root}/.env")
        print("  # Then edit .env and add your API key")
        print()
        print("Option 2: Export directly:")
        print("  export ANTHROPIC_API_KEY=sk-ant-your-key-here")
        print()
        print("Get your key at: https://console.anthropic.com/")
        return

    asyncio.run(test_single_article())


if __name__ == "__main__":
    main()
