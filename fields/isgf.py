"""ISGF (糸島サバイバルゲームフィールド) -- ペライチ内 Google カレンダー埋め込み。"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from scraping.gcal import GCalFieldScraper


class ISGFScraper(GCalFieldScraper):
    name = "ISGF（糸島サバイバルゲームフィールド）"
    url = "https://isgf.jp/"
    method = "ペライチLP内「予約状況」セクションのGoogleカレンダー埋め込みを取得"
    no_iframe_error = "GCal iframe未検出。ペライチウィジェットの動的読み込みの可能性。"

    async def pre_scrape(self, page: Page) -> None:
        # GCal は予約状況セクション内に lazy-load されるため、スクロールして表示させる
        await page.evaluate(
            "() => { const el = document.querySelector('#section-41'); if (el) el.scrollIntoView(); }"
        )
        await asyncio.sleep(2)
