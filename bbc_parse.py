import re
from bs4 import BeautifulSoup

from typing import Optional, Tuple
from config import ARTICLE_SELECTOR, GOSSIP_MAIN_URL

BBC_BASE = "https://www.bbc.com"

def to_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")

def get_latest_gossip_url(main_soup: BeautifulSoup) -> Optional[str]:
    a = main_soup.select_one("a[href*='/sport/football/articles/']")
    if not a or not a.has_attr("href"):
        return None

    href = a["href"].strip()
    if href.startswith("/"):
        return BBC_BASE + href
    return href


def parse_gossip_article(article_soup: BeautifulSoup) -> tuple[str, Optional[str], BeautifulSoup]:
    h1 = article_soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "BBC Football Gossip"

    time_tag = article_soup.find("time")
    published_datetime = time_tag.get("datetime") if time_tag else None

    return title, published_datetime, article_soup

# 마지막에 붙는 "(talkSPORT)" 같은 출처 토큰 분리
# - 괄호 안이 너무 길면 본문 괄호일 가능성이 커서 제외
# - 보통 소스는 짧고, 공백/하이픈/& 정도만 포함되는 경우가 많음
SOURCE_PAREN_RE = re.compile(r"""
    \s*                       # 앞 공백
    \((?P<source>[^()]{2,40})\)  # 괄호 안 2~40자
    \s*$                      # 문장 끝
""", re.VERBOSE)

def _clean_text(s: str) -> str:
    s = re.sub(r"\u00a0", " ", s)           # &nbsp;
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _looks_like_source_token(token: str) -> bool:
    t = token.strip()

    # 너무 길면 출처 토큰일 확률 낮음
    if len(t) > 40:
        return False

    # "talkSPORT", "Sky Sports", "The Athletic", "BBC Sport" 같은 패턴 허용
    # 문장형(마침표 포함)이나 괄호 내용이 너무 복잡하면 제외
    if re.search(r"[.!?]", t):
        return False

    # 출처 토큰은 보통 단어/공백/&/'/- 정도
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 &'\-./]{0,39}", t):
        return False

    return True

def split_body_and_source(text: str) -> Tuple[str, Optional[str]]:
    """
    text 끝에 '(talkSPORT)' 형태가 있으면 body/source로 분리.
    """
    text = _clean_text(text)

    m = SOURCE_PAREN_RE.search(text)
    if not m:
        return text, None

    candidate = m.group("source").strip()
    if not _looks_like_source_token(candidate):
        return text, None

    body = _clean_text(text[: m.start()].rstrip(" -–—:"))
    source = candidate
    return body, source


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

def extract_gossip_items(soup: BeautifulSoup) -> list[tuple[str, Optional[str], Optional[str]]]:
    """
    반환: [(본문, 출처명, 출처링크), ...]
    - 출처명: 괄호 끝 '(talkSPORT)'에서 추출 (없으면 None)
    - 출처링크: 문단의 마지막 a[href] (있으면)
    """
    items: list[tuple[str, Optional[str], Optional[str]]] = []

    for p in soup.select(ARTICLE_SELECTOR):
        raw = p.get_text(" ", strip=True)
        raw = clean_gossip_text(raw)

        if len(raw) < 50:
            continue

        # 1) 텍스트 기준으로 본문/출처 분리 (정교한 버전 사용)
        body, source = split_body_and_source(raw)

        # 2) 가능하면 출처 링크도 추출 (문단 내 마지막 링크를 후보로)
        href: Optional[str] = None
        a_tags = p.find_all("a", href=True)
        if a_tags:
            last_a = a_tags[-1]
            href = last_a["href"].strip()

            # BBC 내부 상대경로면 절대경로로
            if href.startswith("/"):
                href = "https://www.bbc.com" + href

            # 괄호 출처가 없는데, 마지막 링크 텍스트가 출처처럼 보이면 보정
            if source is None:
                label = last_a.get_text(" ", strip=True)
                if _looks_like_source_token(label):
                    source = label

        items.append((body, source, href))

    return items
