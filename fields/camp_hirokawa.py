"""キャンプ広川 (CAMP HIROKAWA) -- 臨時休業中。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.models import FieldResult
from scraping.base import BaseFieldScraper


class CampHirokawaScraper(BaseFieldScraper):
    name = "キャンプ広川 (CAMP HIROKAWA)"
    url = "https://camp-hirokawa.com/"
    method = "トップページお知らせ + Instagram情報"

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        await page.goto(self.url, timeout=30_000)
        await page.wait_for_load_state("networkidle", timeout=15_000)
        body_text = await page.inner_text("body")

        if "臨時休業" in body_text or "予約はできません" in body_text:
            result.error = "現在臨時休業中のため予約不可"
        else:
            result.error = "予約カレンダー未検出。電話予約制の可能性。"
