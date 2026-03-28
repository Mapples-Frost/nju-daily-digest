from __future__ import annotations

import re
from typing import Any

from .base import BaseCrawler


NEGATIVE_TOKENS = {
    "首页",
    "更多",
    "查看更多",
    "上一条",
    "下一条",
    "上一篇",
    "下一篇",
    "返回",
    "关闭",
    "联系我们",
    "English",
    "中文版",
    "校园地图",
    "进入",
    "详情",
}
NJU_TOPIC_TOKENS = ["新闻", "通知", "公告", "活动", "讲座", "比赛", "科研", "招生", "就业", "学工", "教务", "动态"]


class NJUCrawler(BaseCrawler):
    def __init__(self, config, logger) -> None:
        super().__init__(config, logger, source_type="nju")

    def crawl(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for source_conf in self.config.nju_sources:
            try:
                rss_items = self.fetch_rss_items(source_conf)
                html_items = self.extract_items_from_html(source_conf)
                items.extend(rss_items)
                items.extend(html_items)
                self.logger.info("南大来源抓取完成：%s | %s 条", source_conf.get("name"), len(rss_items) + len(html_items))
            except Exception as exc:  # pragma: no cover
                self.logger.error("南大来源抓取失败：%s | %s", source_conf.get("name"), exc)
        return items

    def should_keep_item(self, item: dict[str, Any], source_conf: dict[str, Any], page_title: str) -> bool:
        title = item.get("title", "")
        if title in NEGATIVE_TOKENS:
            return False
        if any(title.startswith(token) for token in NEGATIVE_TOKENS):
            return False

        combined_text = " ".join(
            [
                title,
                item.get("preview", ""),
                page_title,
                source_conf.get("name", ""),
                source_conf.get("source", ""),
            ]
        )

        if any(token in combined_text for token in source_conf.get("include_keywords", [])):
            return True
        if any(token in combined_text for token in NJU_TOPIC_TOKENS):
            return True
        if item.get("published_at"):
            return True
        if re.search(r"/(node|article|content|info|notice|xw|tz|list)/", item.get("url", ""), re.IGNORECASE):
            return True
        return False
