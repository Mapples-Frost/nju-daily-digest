from __future__ import annotations

from utils.text_utils import similarity, title_fingerprint
from utils.url_utils import normalize_url


def _item_score(item: dict) -> tuple[int, int, int, int]:
    return (
        1 if item.get("published_at") else 0,
        len(item.get("detail_text", "")),
        len(item.get("summary", "")),
        len(item.get("title", "")),
    )


def choose_better_item(left: dict, right: dict) -> dict:
    winner = left if _item_score(left) >= _item_score(right) else right
    loser = right if winner is left else left

    merged_keywords = []
    for keyword in winner.get("matched_keywords", []) + loser.get("matched_keywords", []):
        if keyword and keyword not in merged_keywords:
            merged_keywords.append(keyword)
    winner["matched_keywords"] = merged_keywords

    if not winner.get("detail_text") and loser.get("detail_text"):
        winner["detail_text"] = loser["detail_text"]
    if not winner.get("summary") and loser.get("summary"):
        winner["summary"] = loser["summary"]
    if not winner.get("published_at") and loser.get("published_at"):
        winner["published_at"] = loser["published_at"]
        winner["published_at_text"] = loser.get("published_at_text")
    return winner


def deduplicate_items(items: list[dict], title_similarity_threshold: float = 0.92) -> list[dict]:
    by_url: dict[str, dict] = {}
    for raw_item in items:
        if not raw_item.get("url") or not raw_item.get("title"):
            continue
        item = raw_item.copy()
        item["url"] = normalize_url(item["url"])
        if item["url"] in by_url:
            by_url[item["url"]] = choose_better_item(by_url[item["url"]], item)
        else:
            by_url[item["url"]] = item

    deduped: list[dict] = []
    for item in by_url.values():
        fingerprint = title_fingerprint(item.get("title"))
        duplicate_index: int | None = None
        for index, existing in enumerate(deduped):
            existing_fingerprint = title_fingerprint(existing.get("title"))
            if not fingerprint or not existing_fingerprint:
                continue
            if fingerprint == existing_fingerprint or similarity(fingerprint, existing_fingerprint) >= title_similarity_threshold:
                duplicate_index = index
                break
        if duplicate_index is None:
            deduped.append(item)
        else:
            deduped[duplicate_index] = choose_better_item(deduped[duplicate_index], item)
    return deduped
