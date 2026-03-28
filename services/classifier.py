from __future__ import annotations

from utils.text_utils import clean_text, extract_keywords


CATEGORY_ORDER = [
    "南大校内消息",
    "国家级/省级竞赛",
    "创新创业类",
    "学术科研类",
    "程序设计/技术类",
    "文体/综合活动类",
    "其他",
]


CATEGORY_RULES = {
    "创新创业类": [
        "创新创业",
        "创业",
        "互联网+",
        "挑战杯",
        "创客",
        "创业计划",
        "孵化",
        "路演",
        "大学生创新大赛",
    ],
    "程序设计/技术类": [
        "程序设计",
        "编程",
        "算法",
        "数学建模",
        "电子设计",
        "人工智能",
        "软件",
        "开发",
        "技术",
        "网络安全",
        "机器人",
    ],
    "学术科研类": [
        "科研",
        "学术",
        "论文",
        "征文",
        "课题",
        "基金",
        "论坛",
        "研讨会",
        "报告",
        "学术科技作品",
        "创新实践",
    ],
    "国家级/省级竞赛": [
        "全国",
        "国赛",
        "省赛",
        "省级",
        "国家级",
        "教育部",
        "教育厅",
        "江苏省",
        "大赛",
        "竞赛",
    ],
    "文体/综合活动类": [
        "活动",
        "志愿",
        "实践",
        "社会实践",
        "文体",
        "文化",
        "体育",
        "公益",
        "夏令营",
        "讲座",
    ],
}


def extract_item_keywords(item: dict, extra_keywords: list[str] | None = None) -> list[str]:
    combined_text = " ".join(
        [
            item.get("title", ""),
            item.get("preview", ""),
            item.get("detail_text", ""),
            item.get("source", ""),
            " ".join(item.get("matched_keywords", [])),
        ]
    )
    hits = item.get("matched_keywords", []).copy()
    if extra_keywords:
        for keyword in extract_keywords(combined_text, extra_keywords):
            if keyword not in hits:
                hits.append(keyword)
    item["matched_keywords"] = hits
    return hits


def classify_item(item: dict) -> str:
    source_type = clean_text(item.get("source_type", "")).lower()
    url = clean_text(item.get("url", "")).lower()
    if source_type == "nju" or "nju.edu.cn" in url:
        return "南大校内消息"

    hint = item.get("category_hint")
    if hint in CATEGORY_ORDER:
        return hint

    combined_text = " ".join(
        [
            item.get("title", ""),
            item.get("preview", ""),
            item.get("detail_text", ""),
            " ".join(item.get("matched_keywords", [])),
        ]
    )

    if any(token in combined_text for token in CATEGORY_RULES["创新创业类"]):
        return "创新创业类"
    if any(token in combined_text for token in CATEGORY_RULES["程序设计/技术类"]):
        return "程序设计/技术类"
    if any(token in combined_text for token in CATEGORY_RULES["学术科研类"]):
        return "学术科研类"
    if ("竞赛" in combined_text or "比赛" in combined_text) and any(
        token in combined_text for token in CATEGORY_RULES["国家级/省级竞赛"]
    ):
        return "国家级/省级竞赛"
    if any(token in combined_text for token in CATEGORY_RULES["文体/综合活动类"]):
        return "文体/综合活动类"
    return "其他"
