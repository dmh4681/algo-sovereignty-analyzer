"""
News Curator Prototype
Quick test of end-to-end news curation flow
"""

import asyncio
import sys
import os

# Add parent directory to path so we can import api modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_news_aggregator import NewsAggregator
from api_news_curator import MetalsCurator


async def test_gold_news():
    """Test gold news curation"""
    print("🏆 GOLD NEWS CURATOR TEST")
    print("=" * 80)
    
    print("\n🔍 Fetching recent gold news...\n")
    
    # Fetch news
    async with NewsAggregator() as agg:
        articles = await agg.fetch_all('gold', hours=48)
    
    print(f"✅ Found {len(articles)} articles from the last 48 hours\n")
    
    if not articles:
        print("❌ No articles found. Check RSS feeds.")
        return
    
    # Show first 3 articles
    print("📰 Top 3 Articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Link: {article['link'][:60]}...")
    
    print("\n" + "=" * 80)
    print("\n🤖 Analyzing with Claude AI...\n")
    
    # Analyze first article in detail
    curator = MetalsCurator()
    
    result = await curator.analyze_article(articles[0], 'gold')
    
    if result:
        print("✅ ANALYSIS COMPLETE")
        print(f"\n🎯 Sovereignty Score: {result['sovereignty_score']}/10")
        print("\n" + "=" * 80)
        print(result['analysis'])
        print("=" * 80)
    else:
        print("❌ Analysis failed")
    
    return result


async def test_silver_news():
    """Test silver news curation"""
    print("\n\n⚡ SILVER NEWS CURATOR TEST")
    print("=" * 80)
    
    print("\n🔍 Fetching recent silver news...\n")
    
    async with NewsAggregator() as agg:
        articles = await agg.fetch_all('silver', hours=48)
    
    print(f"✅ Found {len(articles)} articles\n")
    
    if not articles:
        print("❌ No articles found. Check RSS feeds.")
        return
    
    print("📰 Top Article:")
    print(f"\n1. {articles[0]['title']}")
    print(f"   Source: {articles[0]['source']}")
    
    print("\n" + "=" * 80)
    print("\n🤖 Analyzing with Claude AI...\n")
    
    curator = MetalsCurator()
    result = await curator.analyze_article(articles[0], 'silver')
    
    if result:
        print("✅ ANALYSIS COMPLETE")
        print(f"\n🎯 Sovereignty Score: {result['sovereignty_score']}/10")
        print("\n" + "=" * 80)
        print(result['analysis'])
        print("=" * 80)
    else:
        print("❌ Analysis failed")
    
    return result


async def test_batch_curation():
    """Test batch curation with filtering"""
    print("\n\n📊 BATCH CURATION TEST")
    print("=" * 80)
    
    print("\n🔍 Fetching and analyzing multiple gold articles...\n")
    
    async with NewsAggregator() as agg:
        articles = await agg.fetch_all('gold', hours=72)
    
    print(f"✅ Found {len(articles)} articles\n")
    
    if not articles:
        print("❌ No articles found")
        return
    
    # Analyze first 5 articles
    curator = MetalsCurator()
    print("🤖 Analyzing first 5 articles (this will take ~30-60 seconds)...\n")
    
    analyzed = await curator.curate_batch(articles[:5], 'gold', min_score=5)
    
    print(f"✅ Analysis complete!")
    print(f"📈 High-signal articles: {len(analyzed)}/5\n")
    
    print("=" * 80)
    print("RESULTS BY SOVEREIGNTY SCORE:")
    print("=" * 80)
    
    for i, result in enumerate(analyzed, 1):
        print(f"\n{i}. Score {result['sovereignty_score']}/10: {result['original']['title'][:70]}...")
        print(f"   Source: {result['original']['source']}")
    
    return analyzed


async def main():
    """Run all tests"""
    print("\n" + "🚀 NEWS CURATOR PROTOTYPE TEST" + "\n")
    
    # Test 1: Gold news
    try:
        await test_gold_news()
    except Exception as e:
        print(f"\n❌ Gold test failed: {e}")
    
    # Test 2: Silver news
    try:
        await test_silver_news()
    except Exception as e:
        print(f"\n❌ Silver test failed: {e}")
    
    # Test 3: Batch curation
    try:
        await test_batch_curation()
    except Exception as e:
        print(f"\n❌ Batch test failed: {e}")
    
    print("\n\n" + "=" * 80)
    print("🎉 PROTOTYPE TEST COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review sovereignty scores - are they reasonable?")
    print("2. Check analysis quality - sovereign perspective clear?")
    print("3. Adjust prompts in api_news_curator.py if needed")
    print("4. Build FastAPI routes for production use")


if __name__ == "__main__":
    asyncio.run(main())
