import requests
import os
from dotenv import load_dotenv


load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")

def get_latest_news():
    
    """SerpApi를 이용하여 최신 비트코인 관련 뉴스 가져오기"""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_news",
        "q": "Bitcoin",
        "gl": "us",  # 미국 뉴스
        "hl": "en",  # 영어
        "api_key": SERP_API_KEY
    }
    
    response = requests.get(url, params=params)
    news_data = response.json()

    if "news_results" in news_data:
        headlines = [{"title": news["title"], "date": news["date"]} for news in news_data["news_results"][:5]]
        print("Latest Bitcoin News Headlines:", headlines)
        return headlines
    else:
        print("No news results found")
        return []