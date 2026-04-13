"""スクレイパー抽象基底クラス。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.models import FieldResult


class BaseFieldScraper(ABC):
    """全フィールドスクレイパーの基底クラス。

    新しいフィールドを追加するには:
      1. fields/ に新ファイルを作成
      2. このクラスを継承
      3. name, url, method を定義
      4. _do_scrape() を実装
      5. fields/__init__.py の ALL_SCRAPERS に追加
    """

    name: str
    url: str
    method: str

    async def scrape(self, page: Page) -> FieldResult:
        """Template Method: 共通のエラーハンドリングを提供する。"""
        result = FieldResult(name=self.name, url=self.url, method=self.method)
        try:
            await self._do_scrape(page, result)
        except Exception as e:
            result.error = str(e)
        return result

    @abstractmethod
    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        """サブクラスで実装する。result に予約情報を追記する。"""
        ...
