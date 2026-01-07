from deep_translator import GoogleTranslator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import os

# from req.session import make_session

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
GOSSIP_MAIN_URL = "https://www.bbc.com/sport/football/gossip"
ARTICLE_SELECTOR = "div[data-component='text-block'] p[class*='Paragraph']"

# SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
# if not SLACK_WEBHOOK_URL:
#     raise RuntimeError("SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")

def get_config():
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_webhook:
        raise ValueError("SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
    return slack_webhook

def make_session() -> requests.Session:
    retry = Retry(
        total=3,                 # 총 재시도 횟수(요청 1번 + 재시도 3번 = 최대 4번 시도)
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.7,      # 0.7초 기반으로 0.7, 1.4, 2.8... 식 지수 백오프
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,   # 여기선 일단 응답 받아보고 res.raise_for_status로 처리
    )

    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


# def fetch_html(url: str) -> BeautifulSoup:
#     res = requests.get(url, headers=HEADERS, timeout=10)
#     res.raise_for_status()
#     return BeautifulSoup(res.text, "html.parser")

SESSION = make_session()

def fetch_html(url: str) -> BeautifulSoup:
    res = SESSION.get(url, headers=HEADERS, timeout=(3, 10))
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def get_latest_gossip_url() -> str | None:
    soup = fetch_html(GOSSIP_MAIN_URL)
    article = soup.select_one("a[href*='/sport/football/articles/']")
    if not article:
        return None
    return "https://www.bbc.com" + article["href"]


def parse_gossip_article(url: str):
    soup = fetch_html(url)
    title = soup.find("h1").get_text(strip=True)

    time_tag = soup.find("time")
    published_datetime = (
        time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None
    )

    return title, published_datetime, soup


def clean_gossip_text(text: str) -> str:
    text = re.sub(r"\s*,?\s*external\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+'s", "'s", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("Â£", "£")
    return text.strip()


def extract_gossip_items(soup: BeautifulSoup) -> list[str]:
    items = []
    for p in soup.select(ARTICLE_SELECTOR):
        raw = p.get_text(" ", strip=True)
        if len(raw) < 50:
            continue
        items.append(clean_gossip_text(raw))
    return items


def is_today_article(published_datetime_str: str | None) -> bool:
    if not published_datetime_str:
        return False

    published_utc = datetime.fromisoformat(
        published_datetime_str.replace("Z", "+00:00")
    )
    published_kst = published_utc.astimezone(ZoneInfo("Asia/Seoul"))
    today_kst = datetime.now(ZoneInfo("Asia/Seoul")).date()

    return published_kst.date() == today_kst

# def send_slack_message(text: str, webhook_url: str):
#     res = SESSION.post(webhook_url, json={"text": text}, timeout=(3, 10))
#     res.raise_for_status()

    # SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    # if not SLACK_WEBHOOK_URL:
    #     return {
    #         "statusCode": 500,
    #         "body": "SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다."
    #     }

    # print("SLACK_WEBHOOK_URL 환경변수 로드 성공")

def send_slack_message(text: str):
    try:
        SLACK_WEBHOOK_URL = get_config()
    except ValueError as e:
        print(e)
        return {"statusCode": 500, "body": str(e)}
    payload = { "text": text, }
    res = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    res.raise_for_status()


def lambda_handler(event, context):

    print("🚀 BBC Gossip Lambda 실행")

    url = get_latest_gossip_url()
    if not url:
        return {"statusCode": 404, "body": "기사 링크 못 찾음"}

    title, published_date, soup = parse_gossip_article(url)

    if not is_today_article(published_date):
        return {"statusCode": 200, "body": "오늘 기사 아님"}

    items = extract_gossip_items(soup)
    if not items:
        return {"statusCode": 200, "body": "가십 없음"}

    refined_eng_article = "\n\n".join(items)

    translator = GoogleTranslator(source="en", target="ko")

    translated_text = translator.translate(refined_eng_article)
    send_slack_message(f"*{title}*\n\n{translated_text}")

    return {
        "statusCode": 200,
        "body": f"Gossip {len(items)}개 Slack 전송 완료"
    }
