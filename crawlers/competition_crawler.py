from __future__ import annotations

from typing import Any

from utils.text_utils import extract_keywords

from .base import BaseCrawler


NEGATIVE_TOKENS = {
    "首页",
    "登录",
    "注册",
    "管理入口",
    "关于我们",
    "联系我们",
    "解决方案",
    "经销商招募公告",
    "寻找融资",
    "寻找项目",
    "寻找人才",
    "报名参赛",
    "查看更多",
    "更多→",
    "更多>",
}
NOTICE_TOKENS = ["通知", "公告", "报名", "征集", "申报", "比赛", "竞赛", "获奖", "结果", "论坛", "讲座", "实践", "活动"]


class CompetitionCrawler(BaseCrawler):
    def __init__(self, config, logger) -> None:
        super().__init__(config, logger, source_type="competition")

    def crawl(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for source_conf in self.config.competition_sources:
            try:
                rss_items = self.fetch_rss_items(source_conf)
                html_items = self.extract_items_from_html(source_conf)
                items.extend(rss_items)
                items.extend(html_items)
                self.logger.info("竞赛来源抓取完成：%s | %s 条", source_conf.get("name"), len(rss_items) + len(html_items))
            except Exception as exc:  # pragma: no cover
                self.logger.error("竞赛来源抓取失败：%s | %s", source_conf.get("name"), exc)
        return items

    def should_keep_item(self, item: dict[str, Any], source_conf: dict[str, Any], page_title: str) -> bool:
        title = item.get("title", "")
        if title in NEGATIVE_TOKENS or any(title.startswith(token) for token in NEGATIVE_TOKENS):
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

        hits = item.get("matched_keywords", [])
        hits.extend(extract_keywords(combined_text, self.config.competition_keywords))
        hits.extend(extract_keywords(combined_text, source_conf.get("include_keywords", [])))

        if not hits and source_conf.get("always_relevant"):
            if any(token in combined_text for token in NOTICE_TOKENS):
                hits.extend(source_conf.get("seed_keywords", []))

        deduped_hits: list[str] = []
        for keyword in hits:
            if keyword and keyword not in deduped_hits:
                deduped_hits.append(keyword)
        item["matched_keywords"] = deduped_hits

        if not item["matched_keywords"]:
            return False

        if "解决方案" in combined_text and "竞赛" not in combined_text and "比赛" not in combined_text:
            return False
        return True
