from __future__ import annotations

from utils.text_utils import clean_text, shorten_text, similarity, split_sentences, title_fingerprint


def summarize_item(item: dict) -> str:
    title = clean_text(item.get("title"))
    candidates = []

    for text in (item.get("detail_text"), item.get("preview"), item.get("summary")):
        for sentence in split_sentences(text):
            normalized = clean_text(sentence)
            if len(normalized) < 12:
                continue
            if title_fingerprint(normalized) == title_fingerprint(title):
                continue
            if any(similarity(normalized, existing) > 0.9 for existing in candidates):
                continue
            candidates.append(shorten_text(normalized, 90))
            if len(candidates) >= 2:
                break
        if len(candidates) >= 2:
            break

    if not candidates:
        fallback = clean_text(item.get("preview") or item.get("detail_text") or title)
        candidates.append(shorten_text(fallback, 90))

    summary = "".join(
        text if text.endswith(("。", "！", "？", "；")) else f"{text}。"
        for text in candidates[:3]
    )
    return shorten_text(summary, 180)
