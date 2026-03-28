from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.url_utils import make_absolute_url


class UrlUtilsTestCase(unittest.TestCase):
    def test_make_absolute_url(self) -> None:
        self.assertEqual(
            make_absolute_url("https://www.nju.edu.cn/news/index.html", "../article/1.html"),
            "https://www.nju.edu.cn/article/1.html",
        )

    def test_skip_invalid_link(self) -> None:
        self.assertIsNone(make_absolute_url("https://www.nju.edu.cn/", "javascript:void(0)"))


if __name__ == "__main__":
    unittest.main()
