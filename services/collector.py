from __future__ import annotations

from config import Config
from crawlers.competition_crawler import CompetitionCrawler
from crawlers.nju_crawler import NJUCrawler
from services.classifier import classify_item, extract_item_keywords
from services.deduplicator import deduplicate_items
from services.storage import SQLiteStorage
from services.summarizer import summarize_item
from utils.time_utils import format_publish_text, now_local, sort_items


class DailyCollector:
    def __init__(self, config: Config, logger) -> None:
        self.config = config
        self.logger = logger
        self.storage = SQLiteStorage(config, logger)
        self.nju_crawler = NJUCrawler(config, logger)
        self.competition_crawler = CompetitionCrawler(config, logger)

    def collect(self) -> dict:
        raw_items = []
        raw_items.extend(self.nju_crawler.crawl())
        raw_items.extend(self.competition_crawler.crawl())
        self.logger.info("原始抓取总量：%s", len(raw_items))

        deduped_items = deduplicate_items(raw_items)
        self.logger.info("去重后总量：%s", len(deduped_items))

        for item in deduped_items:
            extract_item_keywords(item, self.config.competition_keywords)
            item["category"] = classify_item(item)
            item["summary"] = summarize_item(item)
            item["published_at_text"] = item.get("published_at_text") or format_publish_text(
                item.get("published_at"),
                self.config.timezone,
            )

        deduped_items = sort_items(deduped_items, self.config.timezone)

        new_count = 0
        for item in deduped_items:
            if self.storage.upsert_item(item):
                new_count += 1

        pending_items = self.storage.get_unsent_items()
        report_date = now_local(self.config.timezone).strftime("%Y-%m-%d")
        return {
            "report_date": report_date,
            "raw_count": len(raw_items),
            "dedup_count": len(deduped_items),
            "new_count": new_count,
            "pending_items": pending_items,
        }

    def mark_sent(self, items: list[dict]) -> None:
        self.storage.mark_sent([item["url"] for item in items if item.get("url")])

    def close(self) -> None:
        self.nju_crawler.close()
        self.competition_crawler.close()
