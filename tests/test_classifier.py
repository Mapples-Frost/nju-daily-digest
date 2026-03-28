from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.classifier import classify_item


class ClassifierTestCase(unittest.TestCase):
    def test_classify_nju(self) -> None:
        item = {"title": "南京大学关于举办讲座的通知", "source_type": "nju", "url": "https://www.nju.edu.cn/a.html"}
        self.assertEqual(classify_item(item), "南大校内消息")

    def test_classify_innovation(self) -> None:
        item = {"title": "第十九届挑战杯大学生创业计划竞赛报名通知", "source_type": "competition", "matched_keywords": ["挑战杯"]}
        self.assertEqual(classify_item(item), "创新创业类")

    def test_classify_technology(self) -> None:
        item = {"title": "全国大学生数学建模竞赛第一次通知", "source_type": "competition", "matched_keywords": ["数学建模"]}
        self.assertEqual(classify_item(item), "程序设计/技术类")


if __name__ == "__main__":
    unittest.main()
