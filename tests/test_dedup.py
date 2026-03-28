from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.deduplicator import deduplicate_items


class DeduplicateTestCase(unittest.TestCase):
    def test_deduplicate_by_url(self) -> None:
        items = [
            {"title": "南京大学发布竞赛通知", "url": "https://a.com/x?id=1&utm_source=test", "summary": "", "detail_text": ""},
            {"title": "南京大学发布竞赛通知", "url": "https://a.com/x?id=1", "summary": "更完整摘要", "detail_text": "详情"},
        ]
        deduped = deduplicate_items(items)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["url"], "https://a.com/x?id=1")
        self.assertEqual(deduped[0]["detail_text"], "详情")

    def test_deduplicate_by_similar_title(self) -> None:
        items = [
            {"title": "第十九届挑战杯全国大学生课外学术科技作品竞赛通知", "url": "https://a.com/1", "summary": "", "detail_text": ""},
            {"title": "第十九届挑战杯全国大学生课外学术科技作品竞赛通知！", "url": "https://b.com/2", "summary": "", "detail_text": ""},
        ]
        deduped = deduplicate_items(items)
        self.assertEqual(len(deduped), 1)


if __name__ == "__main__":
    unittest.main()
