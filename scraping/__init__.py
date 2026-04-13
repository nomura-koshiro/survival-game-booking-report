"""スクレイピング基盤パッケージ。"""

from scraping.base import BaseFieldScraper
from scraping.facade import ScraperFacade

__all__ = ["BaseFieldScraper", "ScraperFacade"]
