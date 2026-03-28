from __future__ import annotations

import html
import re
from difflib import SequenceMatcher
from typing import Iterable

from bs4 import BeautifulSoup


WHITESPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^\w\u4e00-\u9fff]+", re.UNICODE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])")


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def strip_html_tags(html_text: str | None) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "lxml")
    return clean_text(soup.get_text(" ", strip=True))


def shorten_text(text: str | None, max_length: int = 160) -> str:
    normalized = clean_text(text)
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1].rstrip() + "…"


def split_sentences(text: str | None) -> list[str]:
    normalized = clean_text(text)
    if not normalized:
        return []
    parts = SENTENCE_SPLIT_RE.split(normalized)
    return [part.strip() for part in parts if part and part.strip()]


def extract_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    normalized = clean_text(text).lower()
    hits: list[str] = []
    for keyword in keywords:
        token = clean_text(keyword)
        if token and token.lower() in normalized and token not in hits:
            hits.append(token)
    return hits


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_for_compare(a), normalize_for_compare(b)).ratio()


def normalize_for_compare(text: str | None) -> str:
    normalized = clean_text(text).lower()
    return PUNCT_RE.sub("", normalized)


def title_fingerprint(text: str | None) -> str:
    return normalize_for_compare(text)
