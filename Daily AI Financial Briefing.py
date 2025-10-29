import requests
from datetime import date, timedelta, datetime as dt
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import logging
import os
import feedparser
import datetime
from difflib import SequenceMatcher
import torch
import matplotlib.pyplot as plt
from collections import Counter
import json

# 減少 logs
logging.getLogger("transformers").setLevel(logging.ERROR)

# GPU 加速
device = 0 if torch.cuda.is_available() else -1
if device == -1:
    device = "cpu"

# 設定 Hugging Face 本地模型
generator = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="yiyanghkust/finbert-tone",  # 專為財經設計！
    return_all_scores=True,
    device=device
)

# NLLB 翻譯模型：直接到繁體中文
model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang="eng_Latn")
model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

def translate_to_zh(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
    translated = model.generate(
        **inputs,
        forced_bos_token_id=256201,  # zho_Hant
        max_length=200
    )
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def clean_summary(text):
    text = text.strip()
    if text.endswith('...') and len(text) < 50:
        return text + "（內容過長已截斷）"
    return text.replace('...', '…')

def get_finance_sentiment(title):
    results = sentiment_pipeline(title)[0]
    scores = {r['label']: r['score'] for r in results}
    label = max(scores, key=scores.get)  # Positive / Negative / Neutral
    return label, scores[label]

def get_finance_sentiment(title):
    results = sentiment_pipeline(title)[0]
    scores = {r['label']: r['score'] for r in results}
    label = max(scores, key=scores.get)  # Positive / Negative / Neutral
    return label, scores[label]

# 設定 NewsAPI 和 RSS 來源
news_api_key = os.getenv("NEWS_API_KEY")  # 從環境變數設定
rss_feeds = [
    "https://finance.yahoo.com/rss/",  # Yahoo Finance
    "https://feeds.bloomberg.com/markets/news.rss",  # Bloomberg (修正 URL)
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC
    "https://feeds.reuters.com/reuters/topNews"  # Reuters
]

def deduplicate_articles(articles, threshold=0.8):
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
    return unique_articles[:100]  # 限制 100 篇，避免過載

def is_recent_article(published_at, hours=24):
    if not published_at:
        return True  # 如果沒有時間，保留
    try:
        if isinstance(published_at, str):
            pub_time = dt.fromisoformat(published_at.replace('Z', '+00:00'))
        else:
            pub_time = dt(*published_at[:6])  # RSS published_parsed
        return (dt.now() - pub_time).total_seconds() < hours * 3600
    except:
        return True

# 從 NewsAPI 和 RSS 獲取新聞
def get_news_articles():
    cache_file = "news_cache.json"
    today_str = date.today().isoformat()
    
    # 檢查緩存
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if cache.get('date') == today_str:
            print("使用本地緩存的新聞")
            return cache['articles']
    
    articles = []
    
    # 從 NewsAPI 獲取
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)
        url = f"https://newsapi.org/v2/everything?q=finance+AI&from={yesterday}&to={today}&sortBy=publishedAt&apiKey={news_api_key}&pageSize=50"  # 增加 pageSize
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") == "ok":
            for article in data["articles"]:  # 全取
                if is_recent_article(article.get('publishedAt')):
                    article["source"] = article.get("source", {}).get("name", "NewsAPI")
                    articles.append(article)
    except Exception as e:
        print(f"NewsAPI 失敗: {e}, fallback 到 RSS")
    
    # 從 RSS 獲取
    for rss_url in rss_feeds:
        try:
            feed = feedparser.parse(rss_url)
            source_name = rss_url.split('//')[1].split('/')[0]
            for entry in feed.entries:  # 全取
                if is_recent_article(getattr(entry, 'published_parsed', None)):
                    article = {
                        "title": entry.title,
                        "description": getattr(entry, 'summary', ''),
                        "url": entry.link,
                        "source": source_name
                    }
                    articles.append(article)
        except Exception as e:
            print(f"RSS {rss_url} 失敗: {e}")
    
    # 去重
    articles = deduplicate_articles(articles)
    
    # 保存緩存
    cache = {'date': today_str, 'articles': articles}
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)
    print(f"已下載並緩存 {len(articles)} 篇新聞")
    
    # 在 get_news_articles 後，print 文章
    for i, a in enumerate(articles, 1):
        print(f"{i}. {a['title']}: {a.get('description', '')}")
    
    return articles

# 使用本地 Hugging Face 模型生成財經簡報
def generate_finance_briefing(articles):
    now = datetime.datetime.now()
    date_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # 趨勢分析：簡單關鍵字計數
    keywords = ['AI', 'crypto','OKLO','NUKZ','SMR','ARM','MSFT','GOOGL','PLTR',"TSLA",'NVDA','AAPL','META',
                'GOOGLE','Microsoft','OpenAI','ChatGPT','Tesla','NVIDIA','Amazon','TSMC','Chipsets',
                'Oracle','Neo Cloud','AWS','blockchain','Nebius', 'NBIS','Semiconductor','CSP','ASIC',
                'Elon Musk','blockchain','Sam Altman','Morgan Stanley','Trump',
                'Apple','RoboTaxi','Energy','Quantum Computing','5G','Optimus','Neuralink','SpaceX','Fed']
    trends = Counter()
    for title in [a['title'] for a in articles]:
        for word in keywords:
            if word.lower() in title.lower():
                trends[word] += 1
    top_trends = trends.most_common(3)
    
    # 篩選相關新聞：基於 top_trends 關鍵字
    relevant_keywords = [k for k, v in top_trends]
    filtered_articles = [a for a in articles if any(kw.lower() in a['title'].lower() for kw in relevant_keywords)]
    filtered_articles = filtered_articles[:10]  # 取前10篇
    
    # 情感分析
    sentiments = [get_finance_sentiment(a['title']) for a in filtered_articles]
    
    # 生成摘要
    descriptions = [a.get('description', a['title'])[:512] for a in filtered_articles]
    summaries = generator(
        descriptions,
        max_length=100,
        min_length=40,
        length_penalty=2.0,
        num_beams=4,
        truncation=True,
        early_stopping=True
    )
    for s in summaries:
        s['summary_text'] = clean_summary(s['summary_text'])
    
    # 英文 briefing：列出標題 + 摘要 + 情感
    english_briefing = f"AI Financial Briefing Headlines (Generated on {date_time}):\n"
    english_briefing += f"Top Trends: {', '.join([f'{k}: {v} mentions' for k, v in top_trends])}\n\n"
    for i, (a, sent, summ) in enumerate(zip(filtered_articles, sentiments, summaries), 1):
        english_briefing += f"{i}. {a['title']} (Source: {a.get('source', 'Unknown')})\n   Summary: {summ['summary_text']}\n   Sentiment: {sent[0]} ({sent[1]:.2f})\n\n"
    
        # 繁體中文翻譯（用 NLLB 直接翻譯到繁體）
    chinese_titles = [translate_to_zh(a['title']) for a in filtered_articles]
    chinese_summaries = [translate_to_zh(s['summary_text']) for s in summaries]
    
    chinese_briefing = f"AI 財經簡報標題（繁體中文翻譯，生成於 {date_time}）：\n"
    for i, (title, summ, sent) in enumerate(zip(chinese_titles, chinese_summaries, sentiments), 1):
        chinese_briefing += f"{i}. {title} (來源: {filtered_articles[i-1].get('source', 'Unknown')})\n   摘要: {summ} (情感: {sent[0]} {sent[1]:.2f})\n\n"
    
    briefing = english_briefing + "\n" + chinese_briefing
    return briefing, filtered_articles

# 主程式
if __name__ == "__main__":
    # 清除前次資料
    txt_file = "Daily AI Financial Briefing.txt"
    md_file = "Daily AI Financial Briefing.md"
    png_file = "source_distribution.png"
    for f in [txt_file, md_file, png_file]:
        if os.path.exists(f):
            os.remove(f)
            print(f"已清除舊的 {f}")
    
    articles = get_news_articles()
    if articles:
        briefing, filtered_articles = generate_finance_briefing(articles)
        print("AI 財經簡報:\n", briefing)
        # 寫入 .txt 文件
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(briefing)
        print(f"簡報已保存到 {txt_file}")
        
        # 生成 Markdown
        md_briefing = briefing.replace("AI Financial Briefing", "# AI Financial Briefing").replace("AI 財經簡報", "## AI 財經簡報")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_briefing)
        print(f"Markdown 簡報已保存到 {md_file}")
        
        # 生成視覺化：來源分佈 pie chart
        sources = [a.get('source', 'Unknown') for a in filtered_articles]
        source_counts = Counter(sources)
        labels = list(source_counts.keys())
        sizes = list(source_counts.values())
        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title('News Source Distribution')
        plt.axis('equal')
        plt.savefig(png_file)
        print(f"來源分佈圖已保存到 {png_file}")
    else:
        print("無法獲取新聞文章。")