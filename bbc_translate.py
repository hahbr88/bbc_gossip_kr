from __future__ import annotations

from typing import Optional, TypeAlias
from deep_translator import GoogleTranslator

Item: TypeAlias = tuple[str, Optional[str], Optional[str]]  # (body, source, href)


def make_token(i: int) -> str:
    # 번역기가 건드리기 어려운 토큰
    return f"[[[SRC_{i}]]]"


def format_source_line(source: Optional[str], href: Optional[str]) -> str:
    if not source:
        return "\n"
    if href:
        return f"\n*<{href}|{source}>*\n"
    return f"\n*{source}*\n"


def preprocess_translate(items: list[Item]) -> tuple[str, list[tuple[Optional[str], Optional[str]]]]:
    """
    items를 한 번에 번역하기 위해 토큰을 붙여 하나의 문자열로 만든다.
    반환:
      - refined_with_tokens: 번역할 전체 문자열
      - tails: 토큰 복원용 (source, href) 리스트
    """
    tails: list[tuple[Optional[str], Optional[str]]] = []  # (source, href)
    lines: list[str] = []

    for i, (body, source, href) in enumerate(items):
        token = make_token(i)
        tails.append((source, href))
        lines.append(f"• {body}{token}")

    refined_with_tokens = "\n".join(lines)
    return refined_with_tokens, tails


def google_translator(
    title: str,
    refined_with_tokens: str,
    tails: list[tuple[Optional[str], Optional[str]]],
) -> str:
    translator = GoogleTranslator(source="en", target="ko")

    try:
        translated = translator.translate(refined_with_tokens)
    except Exception as e:
        print("❌ 번역 1차 실패(재시도) :", e)
        try:
            translated = translator.translate(refined_with_tokens)
        except Exception as e2:
            print("❌ 번역 2차 실패 (원문을 그대로 반환):", e2)
            translated = refined_with_tokens

    # 토큰 복원
    for i, (source, href) in enumerate(tails):
        translated = translated.replace(make_token(i), format_source_line(source, href))

    if "[[[SRC_" in translated:
        print("⚠️ 일부 출처 토큰이 복원되지 않았습니다. (번역기가 토큰을 변경했을 수 있음)")

    return f"*{title}*\n\n{translated}"
