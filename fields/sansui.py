"""山水グリーンフィールド -- Wix トップページの新着情報。"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.constants import DOW_LABELS, ZEN_TO_HAN
from core.models import DayReservation, FieldResult
from scraping.base import BaseFieldScraper
from scraping.utils import guess_year


class SansuiScraper(BaseFieldScraper):
    name = "山水グリーンフィールド"
    url = "https://kokusimusou5963.wixsite.com/sansui"
    method = "Wixトップ新着情報 (○名参戦/募集中)"

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        await page.goto(self.url, timeout=30_000)
        await page.wait_for_load_state("networkidle", timeout=20_000)

        text = (await page.inner_text("body")).translate(ZEN_TO_HAN)
        for line in text.split("\n"):
            line = line.strip().translate(ZEN_TO_HAN)
            m = re.match(r"(\d{1,2})月(\d{1,2})日\s*(.*)", line)
            if not m:
                continue

            month, day = int(m.group(1)), int(m.group(2))
            info = m.group(3).strip()
            year = guess_year(month)

            try:
                date_obj = datetime(year, month, day)
            except ValueError:
                continue

            people: int | None = None
            pm = re.search(r"(\d+)名", info)
            if pm:
                people = int(pm.group(1))

            if "募集中" in info:
                status = f"募集中（現在{people}名）" if people else "募集中"
            elif "参戦" in info and people:
                status = f"{people}名参加済"
            elif "貸切" in info:
                status = "貸切"
            elif "中止" in info:
                status = "中止"
            elif people:
                status = f"{people}名"
            else:
                status = "不明"

            result.reservations.append(
                DayReservation(
                    date=date_obj.strftime("%Y-%m-%d"),
                    day_of_week=DOW_LABELS[date_obj.weekday()],
                    session="昼",
                    status=status,
                    people_count=people,
                    event_name="定例会" if "定例" in info else "",
                    note=info[:80],
                )
            )
