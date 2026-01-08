from __future__ import annotations

import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# 로컬에서만 .env 로드 (Lambda에서는 자동으로 환경변수 주입됨)
if os.getenv("AWS_LAMBDA_FUNCTION_NAME") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ModuleNotFoundError:
        # python-dotenv가 없어도 로컬에서 export로 실행 가능하게
        pass

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
GOSSIP_MAIN_URL = "https://www.bbc.com/sport/football/gossip"
ARTICLE_SELECTOR = "div[data-component='text-block'] p[class*='Paragraph']"

DRY_RUN = os.getenv("DRY_RUN") == "1"


def get_config() -> str:
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_webhook:
        raise ValueError("SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
    return slack_webhook


def make_session() -> requests.Session:
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.25,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


SESSION = make_session()


def fetch_html(url: str) -> BeautifulSoup:
    res = SESSION.get(url, headers=HEADERS, timeout=(3, 10))
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def send_slack_message(text: str, webhook_url: str) -> None:
    if DRY_RUN:
        print("[DRY_RUN] Slack 전송 생략. 미리보기(앞 500자):\n", text[:500])
        return
    res = SESSION.post(webhook_url, json={"text": text}, timeout=(3, 10))
    res.raise_for_status()


def get_latest_gossip_url() -> str | None:
    soup = fetch_html(GOSSIP_MAIN_URL)
    article = soup.select_one("a[href*='/sport/football/articles/']")
    if not article:
        return None
    return "https://www.bbc.com" + article["href"]


def parse_gossip_article(url: str) -> tuple[str, str | None, BeautifulSoup]:
    soup = fetch_html(url)
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "BBC Football Gossip"

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
    items: list[str] = []
    for p in soup.select(ARTICLE_SELECTOR):
        raw = p.get_text(" ", strip=True)
        if len(raw) < 50:
            continue
        items.append(clean_gossip_text(raw))
    return items


def is_today_article(published_datetime_str: str | None) -> bool:
    if not published_datetime_str:
        return False

    published_utc = datetime.fromisoformat(published_datetime_str.replace("Z", "+00:00"))
    published_kst = published_utc.astimezone(ZoneInfo("Asia/Seoul"))
    today_kst = datetime.now(ZoneInfo("Asia/Seoul")).date()
    return published_kst.date() == today_kst

SOURCE_PATTERN = re.compile(r"\s*\(([^)]+)\)\s*$")
def split_source_tail(text: str) -> tuple[str, str]:
    """
    문장 맨 끝의 (출처) 꼬리를 분리한다.
    - 반환: (본문, 출처꼬리)  예) ("... season.", " (Mirror)")
    """
    m = SOURCE_PATTERN.search(text)
    if not m:
        return text.strip(), ""
    main = text[:m.start()].strip()
    tail = m.group(0)  # 괄호 포함 원문 그대로
    return main, tail

def make_token(i: int) -> str:
    # 번역기가 건드리기 어려운 토큰 형태(대문자/꺾쇠)
    return f"<<<SRC{i}>>>"

def run() -> dict:
    print("🚀 BBC Gossip 실행")

    try:
        webhook_url = get_config()
    except ValueError as e:
        return {"statusCode": 500, "body": str(e)}

    t0 = time.perf_counter()
    url = get_latest_gossip_url()
    print("t(get_latest):", time.perf_counter() - t0)
    if not url:
        return {"statusCode": 404, "body": "기사 링크 못 찾음"}

    t1 = time.perf_counter()
    title, published_date, soup = parse_gossip_article(url)
    print("t(parse):", time.perf_counter() - t1)
    if not is_today_article(published_date):
        return {"statusCode": 200, "body": "오늘 기사 아님"}

    items = extract_gossip_items(soup)
    if not items:
        return {"statusCode": 200, "body": "가십 없음"}

    

    # ---- 여기부터 속도 우선 번역 로직 ----
    tails: list[str] = []
    lines: list[str] = []

    for i, x in enumerate(items):
        main, tail = split_source_tail(x)
        token = make_token(i)
        tails.append(tail)
        lines.append(f"• {main} {token}")  # 본문 뒤에 토큰

    refined_with_tokens = "\n".join(lines)

    translator = GoogleTranslator(source="en", target="ko")
    
    t2 = time.perf_counter()
    try:
        translated = translator.translate(refined_with_tokens)
    except Exception as e:
        print("❌ 번역 1차 실패(재시도) :", e)
        try:
            translated = translator.translate(refined_with_tokens)
        except Exception as e2:
            print("❌ 번역 2차 실패 (원문을 그대로 반환):", e2)
            translated = refined_with_tokens

    print("t(translate_once):", time.perf_counter() - t2)

    def format_source_tail(tail: str) -> str:
        if not tail:
            return "\n"
        return f"\n*{tail.strip()}*\n"
    

    for i, tail in enumerate(tails):
        translated = translated.replace(make_token(i), format_source_tail(tail))

    # 번역 결과에 토큰을 출처 꼬리로 되돌리기
    for i, tail in enumerate(tails):
        translated = translated.replace(make_token(i), tail)

    # 토큰 복원이 누락된 경우(번역기가 토큰을 훼손한 케이스) 안전 처리
    if "<<<SRC" in translated:
        print("⚠️ 일부 출처 토큰이 복원되지 않았습니다. (번역기가 토큰을 변경했을 수 있음)")

    message = f"*{title}*\n\n{translated}"

    t3 = time.perf_counter()
    send_slack_message(message, webhook_url)
    print("t(slack):", time.perf_counter() - t3)

    return {"statusCode": 200, "body": f"Gossip {len(items)}개"}


if __name__ == "__main__":
    # 로컬 실행용
    result = run()
    print("result:", result)
