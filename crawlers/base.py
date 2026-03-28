from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import feedparser
import httpx
from bs4 import BeautifulSoup, Tag

from config import Config
from utils.text_utils import clean_text, extract_keywords, shorten_text
from utils.time_utils import extract_datetime_from_text, format_publish_text, struct_time_to_iso
from utils.url_utils import get_domain, has_blocked_extension, is_same_domain, make_absolute_url


class BaseCrawler:
    _robots_cache: dict[str, RobotFileParser | None] = {}
    _last_request_at: dict[str, float] = {}
    CONTENT_SELECTORS = [
        "article",
        ".article",
        ".article-content",
        ".content",
        ".detail",
        ".entry-content",
        ".news_content",
        ".v_news_content",
        ".wp_articlecontent",
        "#vsb_content",
        "main",
    ]
    DETAIL_BLOCKED_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")

    def __init__(self, config: Config, logger, source_type: str) -> None:
        self.config = config
        self.logger = logger
        self.source_type = source_type
        self.client_verified = httpx.Client(
            headers={"User-Agent": config.user_agent, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"},
            timeout=config.request_timeout,
            follow_redirects=True,
            verify=config.verify_ssl,
        )
        self.client_unverified = httpx.Client(
            headers={"User-Agent": config.user_agent, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"},
            timeout=config.request_timeout,
            follow_redirects=True,
            verify=False,
        )

    def close(self) -> None:
        self.client_verified.close()
        self.client_unverified.close()

    def crawl(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _get_client(self, verify_ssl: bool | None) -> httpx.Client:
        verify = self.config.verify_ssl if verify_ssl is None else verify_ssl
        return self.client_verified if verify else self.client_unverified

    def _respect_rate_limit(self, url: str) -> None:
        domain = get_domain(url)
        last_request = self._last_request_at.get(domain, 0.0)
        wait_seconds = self.config.request_delay_seconds - (time.time() - last_request)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        self._last_request_at[domain] = time.time()

    def _load_robots_parser(self, url: str, verify_ssl: bool | None) -> RobotFileParser | None:
        domain = get_domain(url)
        if domain in self._robots_cache:
            return self._robots_cache[domain]

        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()

        try:
            content, _ = self.fetch_text(robots_url, verify_ssl=verify_ssl, check_robots=False)
            if not content:
                self._robots_cache[domain] = None
                return None
            parser.parse(content.splitlines())
            self._robots_cache[domain] = parser
            return parser
        except Exception as exc:  # pragma: no cover
            self.logger.warning("读取 robots.txt 失败，默认放行：%s | %s", robots_url, exc)
            self._robots_cache[domain] = None
            return None

    def can_fetch(self, url: str, verify_ssl: bool | None = None) -> bool:
        parser = self._load_robots_parser(url, verify_ssl)
        if parser is None:
            return True
        try:
            return parser.can_fetch(self.config.user_agent, url)
        except Exception:
            return True

    def fetch_text(
        self,
        url: str,
        verify_ssl: bool | None = None,
        check_robots: bool = True,
    ) -> tuple[str | None, str]:
        if check_robots and not self.can_fetch(url, verify_ssl):
            self.logger.warning("robots.txt 禁止抓取：%s", url)
            return None, url

        final_url = url
        client = self._get_client(verify_ssl)
        for attempt in range(1, self.config.request_retries + 1):
            try:
                self._respect_rate_limit(url)
                response = client.get(url)
                final_url = str(response.url)
                response.raise_for_status()
                return response.text, final_url
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response is not None else "unknown"
                self.logger.warning(
                    "请求失败（HTTP %s，第 %s/%s 次）：%s",
                    status_code,
                    attempt,
                    self.config.request_retries,
                    url,
                )
            except httpx.HTTPError as exc:
                self.logger.warning(
                    "请求异常（第 %s/%s 次）：%s | %s",
                    attempt,
                    self.config.request_retries,
                    url,
                    exc,
                )
            time.sleep(min(attempt, 3))
        return None, final_url

    def fetch_soup(self, url: str, verify_ssl: bool | None = None) -> tuple[BeautifulSoup | None, str]:
        content, final_url = self.fetch_text(url, verify_ssl=verify_ssl)
        if not content:
            return None, final_url
        return BeautifulSoup(content, "lxml"), final_url

    def _iter_anchor_tags(self, soup: BeautifulSoup, source_conf: dict[str, Any]) -> list[Tag]:
        selector = source_conf.get("anchor_selector")
        if selector:
            return [node for node in soup.select(selector) if isinstance(node, Tag)]
        return [node for node in soup.find_all("a", href=True) if isinstance(node, Tag)]

    def _find_context_text(self, anchor: Tag) -> str:
        texts: list[str] = []
        parent = anchor.parent if isinstance(anchor.parent, Tag) else None
        if parent is not None:
            texts.append(parent.get_text(" ", strip=True))
            grand = parent.parent if isinstance(parent.parent, Tag) else None
            if grand is not None:
                texts.append(grand.get_text(" ", strip=True))
        texts.append(anchor.get("title", ""))
        texts.append(anchor.get_text(" ", strip=True))
        return shorten_text(" ".join(texts), 300)

    def _build_item_from_anchor(
        self,
        anchor: Tag,
        page_url: str,
        source_conf: dict[str, Any],
        page_title: str,
    ) -> dict[str, Any] | None:
        title = clean_text(anchor.get_text(" ", strip=True)) or clean_text(anchor.get("title"))
        if len(title) < 5 or len(title) > 120:
            return None

        url = make_absolute_url(page_url, anchor.get("href"))
        if not url or url == page_url or has_blocked_extension(url):
            return None

        if not source_conf.get("allow_external", False) and not is_same_domain(url, page_url):
            return None

        context_text = self._find_context_text(anchor)
        published_at = extract_datetime_from_text(context_text, self.config.timezone) or extract_datetime_from_text(
            url,
            self.config.timezone,
        )
        seed_keywords = source_conf.get("seed_keywords", [])
        include_keywords = source_conf.get("include_keywords", [])
        matched_keywords = extract_keywords(f"{title} {context_text} {page_title}", [*seed_keywords, *include_keywords])

        preview = context_text.replace(title, "", 1).strip() if title in context_text else context_text
        preview = shorten_text(preview or title, 140)

        return {
            "title": title,
            "url": url,
            "published_at": published_at,
            "published_at_text": format_publish_text(published_at, self.config.timezone),
            "source": source_conf.get("source") or source_conf.get("name") or get_domain(page_url),
            "source_name": source_conf.get("name") or source_conf.get("source") or get_domain(page_url),
            "source_type": source_conf.get("source_type", self.source_type),
            "category_hint": source_conf.get("category_hint"),
            "matched_keywords": matched_keywords,
            "preview": preview,
            "summary": preview,
            "detail_text": "",
            "list_page": page_url,
        }

    def should_keep_item(self, item: dict[str, Any], source_conf: dict[str, Any], page_title: str) -> bool:
        return True

    def extract_items_from_html(self, source_conf: dict[str, Any]) -> list[dict[str, Any]]:
        soup, final_url = self.fetch_soup(source_conf["url"], verify_ssl=source_conf.get("verify_ssl"))
        if soup is None:
            return []

        page_title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
        anchors = self._iter_anchor_tags(soup, source_conf)
        candidate_limit = max(40, source_conf.get("max_items", self.config.max_items_per_source) * 6)
        items: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for anchor in anchors:
            item = self._build_item_from_anchor(anchor, final_url, source_conf, page_title)
            if item is None:
                continue
            if item["url"] in seen_urls:
                continue
            if not self.should_keep_item(item, source_conf, page_title):
                continue
            items.append(item)
            seen_urls.add(item["url"])
            if len(items) >= candidate_limit:
                break

        detail_fetch_limit = source_conf.get("detail_fetch_limit", self.config.detail_fetch_limit_per_source)
        for item in items[:detail_fetch_limit]:
            detail_text = self.fetch_detail_text(item["url"], verify_ssl=source_conf.get("verify_ssl"))
            if detail_text:
                item["detail_text"] = detail_text
                if not item.get("published_at"):
                    item["published_at"] = extract_datetime_from_text(detail_text[:500], self.config.timezone)
                    item["published_at_text"] = format_publish_text(item.get("published_at"), self.config.timezone)

        return items[: source_conf.get("max_items", self.config.max_items_per_source)]

    def fetch_detail_text(self, url: str, verify_ssl: bool | None = None) -> str:
        lowered = url.lower()
        if lowered.endswith(self.DETAIL_BLOCKED_SUFFIXES):
            return ""

        soup, _ = self.fetch_soup(url, verify_ssl=verify_ssl)
        if soup is None:
            return ""

        best_text = ""
        for selector in self.CONTENT_SELECTORS:
            for node in soup.select(selector):
                text = clean_text(node.get_text(" ", strip=True))
                if len(text) > len(best_text):
                    best_text = text

        if len(best_text) < 80:
            paragraphs = []
            for node in soup.find_all(["p", "div"]):
                text = clean_text(node.get_text(" ", strip=True))
                if 18 <= len(text) <= 300:
                    paragraphs.append(text)
                if len(paragraphs) >= 12:
                    break
            best_text = " ".join(paragraphs)

        return shorten_text(best_text, 900)

    def fetch_rss_items(self, source_conf: dict[str, Any]) -> list[dict[str, Any]]:
        rss_url = source_conf.get("rss_url")
        if not rss_url:
            return []

        content, _ = self.fetch_text(rss_url, verify_ssl=source_conf.get("verify_ssl"))
        if not content:
            return []

        feed = feedparser.parse(content)
        items: list[dict[str, Any]] = []
        for entry in feed.entries[: source_conf.get("max_items", self.config.max_items_per_source)]:
            title = clean_text(entry.get("title"))
            url = make_absolute_url(rss_url, entry.get("link"))
            if not title or not url:
                continue
            summary = clean_text(entry.get("summary") or entry.get("description") or "")
            published_at = (
                struct_time_to_iso(entry.get("published_parsed"), self.config.timezone)
                or struct_time_to_iso(entry.get("updated_parsed"), self.config.timezone)
            )
            item = {
                "title": title,
                "url": url,
                "published_at": published_at,
                "published_at_text": format_publish_text(published_at, self.config.timezone),
                "source": source_conf.get("source") or source_conf.get("name") or get_domain(url),
                "source_name": source_conf.get("name") or source_conf.get("source") or get_domain(url),
                "source_type": source_conf.get("source_type", self.source_type),
                "category_hint": source_conf.get("category_hint"),
                "matched_keywords": extract_keywords(
                    f"{title} {summary}",
                    [*source_conf.get("seed_keywords", []), *source_conf.get("include_keywords", [])],
                ),
                "preview": shorten_text(summary or title, 140),
                "summary": shorten_text(summary or title, 140),
                "detail_text": clean_text(summary),
                "list_page": rss_url,
            }
            if self.should_keep_item(item, source_conf, clean_text(feed.feed.get("title", ""))):
                items.append(item)
        return items
