# pipeline.py
from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from bbc_http import SESSION, fetch_text
from bbc_parse import (
    MIN_EXPECTED_GOSSIP_ITEMS,
    to_soup,
    get_latest_gossip_url,
    parse_gossip_article,
    extract_gossip_items,
    get_parse_diagnostics,
)
from bbc_translate import google_translator, preprocess_translate
from config import GOSSIP_MAIN_URL, HEADERS, DRY_RUN, get_slack_webhook_url


class ParseFailure(RuntimeError):
    pass


def send_slack_message(text: str, webhook_url: str) -> None:
    if DRY_RUN:
        print("[DRY_RUN] Slack 전송 생략. 미리보기(앞 500자):\n", text[:500])
        return
    res = SESSION.post(webhook_url, json={"text": text}, timeout=(3, 10))
    res.raise_for_status()


def is_today_article(published_datetime_str: str | None) -> bool:
    if not published_datetime_str:
        return False
    published_utc = datetime.fromisoformat(published_datetime_str.replace("Z", "+00:00"))
    published_kst = published_utc.astimezone(ZoneInfo("Asia/Seoul"))
    return published_kst.date() == datetime.now(ZoneInfo("Asia/Seoul")).date()


def run() -> dict:
    print("🚀 BBC Gossip 실행")

    webhook_url = get_slack_webhook_url()

    # 1) 메인 페이지 가져와서 최신 기사 URL 찾기
    t0 = time.perf_counter()
    main_html = fetch_text(GOSSIP_MAIN_URL, headers=HEADERS)
    main_soup = to_soup(main_html)
    url = get_latest_gossip_url(main_soup)
    print("t(get_latest):", time.perf_counter() - t0)

    if not url:
        return {"statusCode": 404, "body": "기사 링크 못 찾음"}

    # 2) 상세 페이지 가져와서 파싱
    t1 = time.perf_counter()
    article_html = fetch_text(url, headers=HEADERS)
    article_soup = to_soup(article_html)
    title, published_date, soup = parse_gossip_article(article_soup)
    print("t(parse):", time.perf_counter() - t1)
    print("article_url:", url)
    print("article_title:", title)
    print("article_published_date:", published_date)

    if not is_today_article(published_date):
        return {"statusCode": 200, "body": "오늘 기사 아님"}

    items = extract_gossip_items(soup)
    diagnostics = get_parse_diagnostics(soup)
    print(
        "parse_summary:",
        {
            "selected_selector": diagnostics["selected_selector"],
            "paragraph_count": diagnostics["paragraph_count"],
            "item_count": len(items),
            "selector_counts": diagnostics["selector_counts"],
        },
    )
    if not items:
        print("parse_diagnostics:", diagnostics)
        raise ParseFailure(
            "금일 BBC 가십에서 발췌한 항목없음 "
            f"title={title!r}, published_date={published_date!r}, diagnostics={diagnostics!r}"
        )
    if len(items) < MIN_EXPECTED_GOSSIP_ITEMS:
        print(
            f"parse_warning: expected at least {MIN_EXPECTED_GOSSIP_ITEMS} gossip items, "
            f"got {len(items)}"
        )
        print("parse_diagnostics:", get_parse_diagnostics(soup))

    refined_with_tokens, tails = preprocess_translate(items)

    t2 = time.perf_counter()
    message = google_translator(title, refined_with_tokens, tails)
    print("t(translate):", time.perf_counter() - t2)

    t3 = time.perf_counter()
    send_slack_message(message, webhook_url)
    print("t(slack):", time.perf_counter() - t3)

    return {"statusCode": 200, "body": f"Gossip {len(items)}개"}
