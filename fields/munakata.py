"""福岡サバゲーキャンプ宗像基地 -- LINE/電話予約 + ニュースページ。"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.constants import DOW_LABELS, ZEN_TO_HAN
from core.models import DayReservation, FieldResult
from scraping.base import BaseFieldScraper
from scraping.gcal import scrape_gcal_embedded
from scraping.utils import guess_year


class MunakataScraper(BaseFieldScraper):
    name = "福岡サバゲーキャンプ宗像基地"
    url = "https://sabagecampmunakata.com/"
    method = "トップページGoogleカレンダー埋め込みを取得"

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        await page.goto(self.url, timeout=30_000)
        await page.wait_for_load_state("networkidle", timeout=15_000)

        gcal_found = await scrape_gcal_embedded(
            page,
            result,
            no_iframe_error="GCal iframe未検出。ニュースページにフォールバック。",
        )
        if gcal_found:
            return

        # フォールバック: ニュースページをテキスト解析
        result.error = ""
        await page.goto(
            "https://sabagecampmunakata.com/archives/category/news/", timeout=15_000
        )
        await page.wait_for_load_state("networkidle", timeout=10_000)
        news_text = (await page.inner_text("body")).translate(ZEN_TO_HAN)

        event_keywords = ["定例", "イベント", "参加", "ゲーム"]
        for line in news_text.split("\n"):
            line = line.strip().translate(ZEN_TO_HAN)
            m = re.search(r"(\d{1,2})月(\d{1,2})日", line)
            if not m or not any(kw in line for kw in event_keywords):
                continue

            month, day = int(m.group(1)), int(m.group(2))
            try:
                date_obj = datetime(guess_year(month), month, day)
            except ValueError:
                continue

            people: int | None = None
            pm = re.search(r"(\d+)\s*[名人]", line)
            if pm:
                people = int(pm.group(1))

            result.reservations.append(
                DayReservation(
                    date=date_obj.strftime("%Y-%m-%d"),
                    day_of_week=DOW_LABELS[date_obj.weekday()],
                    session="終日",
                    status=f"{people}名" if people else "イベントあり",
                    people_count=people,
                    note=line[:80],
                )
            )

        if not result.reservations:
            result.error = "LINE/電話予約のみ。オンライン予約カレンダー無し。"
