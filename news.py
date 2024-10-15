import requests
import os
from dotenv import load_dotenv
import json

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
    
    # 'news_results'에서 상위 5개의 뉴스만 선택
    news_results = news_data["news_results"][:5]
    
    all_stories = []
    
    # 각 news에 대해 stories와 top-level title을 확인하고 title과 date를 가져오기
    for news in news_results:
        # 먼저 각 top-level 뉴스의 title 저장
        top_level_title = news.get("title", "No title available")
        all_stories.append({"title": top_level_title, "date": "No date (top-level)"})
        
        # 각 news 항목에서 stories를 확인하여 title과 date 추출
        if "stories" in news:
            for story in news["stories"]:
                title = story.get("title", "No title available")
                date = story.get("date", "No date available")
                all_stories.append({"title": title, "date": date})
    

    return all_stories

# 최신 비트코인 관련 뉴스 및 stories 가져오기
stories = get_latest_news()
print(json.dumps(stories, indent=4, ensure_ascii=False))
