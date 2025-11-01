import feedparser

feeds = [
    'https://finance.yahoo.com/rss/',
    'https://feeds.bloomberg.com/markets/news.rss',
    'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    'https://feeds.reuters.com/reuters/topNews',
    'https://techcrunch.com/feed/'
]

for url in feeds:
    print(f"\n=== {url} ===")
    try:
        feed = feedparser.parse(url)
        for i, entry in enumerate(feed.entries[:2]):
            print(f"Entry {i+1}:")
            print(f"Title: {entry.title}")
            summary = getattr(entry, 'summary', 'NO SUMMARY')
            print(f"Summary: {summary[:200]}...")
            print("---")
    except Exception as e:
        print(f"Error: {e}")
