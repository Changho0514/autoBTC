import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")


def convert_utc_to_kst(utc_date_str):
    """UTC 시간을 KST로 변환"""
    try:
        # 문자열을 datetime 객체로 변환 (UTC 시간 기준)
        utc_datetime = datetime.strptime(utc_date_str, "%b %d, %Y %I:%M %p UTC")
        # KST로 변환 (UTC + 9시간)
        kst_datetime = utc_datetime + timedelta(hours=9)
        return kst_datetime.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return "Invalid date format"


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

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 4xx, 5xx 오류 발생 시 예외 발생

        news_data = response.json()

        if "news_results" not in news_data:
            print("⚠️ 'news_results'가 응답에 없음. API 응답:", news_data)
            return []

        news_results = news_data.get("news_results", [])[:5]
        all_stories = []

        for news in news_results:
            top_level_title = news.get("title", "No title available")
            all_stories.append({"title": top_level_title, "date": "No date (top-level)"})

            if "stories" in news:
                for story in news["stories"]:
                    title = story.get("title", "No title available")
                    utc_date = story.get("date", "No date available")

                    if "UTC" in utc_date:
                        kst_date = convert_utc_to_kst(utc_date)
                    else:
                        kst_date = utc_date

                    all_stories.append({"title": title, "date": kst_date})

        return all_stories

    except Exception as e:
        print(f"⚠️ 뉴스 요청 실패: {e}")
        return []  # 실패 시에도 빈 리스트 반환


# 최신 비트코인 관련 뉴스 및 stories 가져오기
stories = get_latest_news()
print(json.dumps(stories, indent=4, ensure_ascii=False))
