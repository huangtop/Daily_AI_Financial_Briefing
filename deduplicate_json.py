import json
from difflib import SequenceMatcher
import os

def deduplicate_json(cache_file="news_cache.json", threshold=0.6):
    """從JSON文件中去除重複新聞"""
    if not os.path.exists(cache_file):
        print(f"找不到 {cache_file}")
        return

    with open(cache_file, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    articles = cache['articles']
    print(f"原始文章數: {len(articles)}")

    unique_articles = []
    for article in articles:
        is_duplicate = False
        for unique in unique_articles:
            similarity = SequenceMatcher(None, article['title'], unique['title']).ratio()
            if similarity > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_articles.append(article)

    cache['articles'] = unique_articles
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

    print(f"去重後文章數: {len(unique_articles)}")

if __name__ == "__main__":
    deduplicate_json()
