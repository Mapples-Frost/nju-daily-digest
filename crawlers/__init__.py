"""抓取器模块。"""

from .competition_crawler import CompetitionCrawler
from .nju_crawler import NJUCrawler

__all__ = ["CompetitionCrawler", "NJUCrawler"]
