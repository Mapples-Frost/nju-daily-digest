from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.mailer import build_email_html


class MailerHtmlTestCase(unittest.TestCase):
    def test_build_email_html_with_items(self) -> None:
        html = build_email_html(
            "2026-03-28",
            [
                {
                    "title": "南京大学创新创业大赛通知",
                    "url": "https://www.nju.edu.cn/a.html",
                    "published_at_text": "2026-03-28 08:00",
                    "source": "南京大学官网",
                    "summary": "这是摘要。",
                    "category": "南大校内消息",
                    "matched_keywords": ["创新创业大赛"],
                }
            ],
        )
        self.assertIn("南京大学创新创业大赛通知", html)
        self.assertIn("南大校内消息", html)
        self.assertIn("https://www.nju.edu.cn/a.html", html)

    def test_build_email_html_empty(self) -> None:
        html = build_email_html("2026-03-28", [])
        self.assertIn("今日无新增内容", html)


if __name__ == "__main__":
    unittest.main()
