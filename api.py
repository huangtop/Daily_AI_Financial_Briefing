from flask import Flask, jsonify
import os
import json
from datetime import date, timedelta, datetime
import requests
import feedparser
from difflib import SequenceMatcher
from collections import Counter

app = Flask(__name__)

print("Flask app created")

@app.route('/')
def home():
    return "Home page"

# 全局變數存儲 briefing
briefing_data = {"briefing": "", "date": ""}

def translate_to_zh(text):
    return text  # 測試用，返回原文

def clean_summary(text):
    text = text.strip()
    if text.endswith('...') and len(text) < 50:
        return text + "（內容過長已截斷）"
    return text.replace('...', '…')

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
    return unique_articles[:100]

def is_recent_article(published_at, hours=24):
    if not published_at:
        return True
    try:
        if isinstance(published_at, str):
            pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        else:
            pub_time = datetime(*published_at[:6])
        return (datetime.now() - pub_time).total_seconds() < hours * 3600
    except:
        return True

def get_finance_sentiment(title):
    return ("Neutral", 0.5)  # 測試用

def get_news_articles(news_api_key):
    # 測試用假數據
    return [
        {"title": "AI Stocks Surge as Tech Giants Invest Billions", "description": "Major technology companies are pouring billions into artificial intelligence development.", "source": "Bloomberg"},
        {"title": "Tesla Unveils New AI-Powered Autopilot Features", "description": "Tesla announces advanced AI capabilities for its autonomous driving system.", "source": "Reuters"}
    ]

def generate_finance_briefing(articles):
    now = datetime.now()
    date_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    keywords = ['AI', 'crypto','OKLO','NUKZ','SMR','ARM','MSFT','GOOGL','PLTR',"TSLA",'NVDA','AAPL','META',
                'GOOGLE','Microsoft','OpenAI','ChatGPT','Tesla','NVIDIA','Amazon','TSMC','Chipsets',
                'Oracle','Neo Cloud','AWS','blockchain','Nebius', 'NBIS','Semiconductor','CSP','ASIC',
                'Elon Musk','blockchain','Sam Altman','Morgan Stanley','Trump',
                'Apple','RoboTaxi','Energy','Quantum Computing','5G','Optimus','Neuralink','SpaceX','Fed']
    trends = {}
    for title in [a['title'] for a in articles]:
        for word in keywords:
            if word.lower() in title.lower():
                trends[word] = trends.get(word, 0) + 1
    top_trends = sorted(trends.items(), key=lambda x: x[1], reverse=True)[:3]
    
    relevant_keywords = [k for k, v in top_trends]
    filtered_articles = [a for a in articles if any(kw.lower() in a['title'].lower() for kw in relevant_keywords)]
    filtered_articles = filtered_articles[:10]
    
    sentiments = [get_finance_sentiment(a['title']) for a in filtered_articles]
    summaries = [{"summary_text": a.get('description', a['title'])[:100] + "..."} for a in filtered_articles]
    
    english_briefing = f"AI Financial Briefing Headlines (Generated on {date_time}):\n"
    english_briefing += f"Top Trends: {', '.join([f'{k}: {v} mentions' for k, v in top_trends])}\n\n"
    for i, (a, sent, summ) in enumerate(zip(filtered_articles, sentiments, summaries), 1):
        english_briefing += f"{i}. {a['title']} (Source: {a.get('source', 'Unknown')})\n   Summary: {summ['summary_text']}\n   Sentiment: {sent[0]} ({sent[1]:.2f})\n\n"
    
    chinese_titles = [translate_to_zh(a['title']) for a in filtered_articles]
    chinese_summaries = [translate_to_zh(s['summary_text']) for s in summaries]
    
    chinese_briefing = f"AI 財經簡報標題（繁體中文翻譯，生成於 {date_time}）：\n"
    for i, (title, summ, sent) in enumerate(zip(chinese_titles, chinese_summaries, sentiments), 1):
        chinese_briefing += f"{i}. {title} (來源: {filtered_articles[i-1].get('source', 'Unknown')})\n   摘要: {summ} (情感: {sent[0]} {sent[1]:.2f})\n\n"
    
    briefing = english_briefing + "\n" + chinese_briefing
    return briefing, filtered_articles

@app.route('/test')
def test():
    return "API is working"

@app.route('/briefing')
def get_briefing():
    print("Briefing endpoint called")
    # 測試用，總是生成新數據
    articles = get_news_articles("fake_key")
    print(f"Got {len(articles)} articles")
    briefing, filtered_articles = generate_finance_briefing(articles)
    print("Generated briefing")
    return jsonify({"briefing": briefing, "filtered_articles": filtered_articles})

if __name__ == '__main__':
    print("Starting Flask app with Waitress...")
    from waitress import serve
    serve(app, host='127.0.0.1', port=8000)
