"""バギーランド (北九州) -- HTML カレンダーテーブル。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.constants import WEEKEND_JS_DAYS
from core.models import DayReservation, FieldResult
from scraping.base import BaseFieldScraper


class BuggyLandScraper(BaseFieldScraper):
    name = "バギーランド（北九州）"
    url = "http://www.shinmoji-buggy.com/"
    method = "HTMLカレンダーテーブルから予約状況をパース (人数/満員/空き)"

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        await page.goto(self.url, timeout=30_000)
        await page.wait_for_load_state("networkidle", timeout=15_000)

        data = await page.evaluate(r"""() => {
            const results = [];
            const tables = document.querySelectorAll('table');
            for (const table of tables) {
                table.querySelectorAll('td').forEach(td => {
                    const dateEl = td.querySelector('.inputDate');
                    if (!dateEl || !dateEl.textContent.trim().match(/\d/)) return;

                    const getDate = (btn) => {
                        if (!btn) return null;
                        const onclick = btn.getAttribute('onclick') || '';
                        const m = onclick.match(/date=(\d{4})\/(\d{1,2})\/(\d{1,2})/);
                        return m ? { year: parseInt(m[1]), month: parseInt(m[2]), day: parseInt(m[3]) } : null;
                    };
                    const getStatus = (btn) => {
                        if (!btn) return '受付終了';
                        const alt = (btn.alt || '').trim();
                        if (alt.includes('満員')) return '満員';
                        if (alt.includes('予約可')) return '予約可';
                        if (alt.includes('受付終了') || alt === '') return '受付終了';
                        return alt;
                    };

                    const dayBtn = td.querySelector('.inputDay input[type=image], .inputDay img[onclick]');
                    const nightBtn = td.querySelector('.inputNight input[type=image], .inputNight img[onclick]');
                    const dateInfo = getDate(dayBtn) || getDate(nightBtn);
                    if (!dateInfo) return;

                    const { year, month, day } = dateInfo;
                    const d = new Date(year, month - 1, day);
                    const dow = d.getDay();
                    const dowStr = dow === 0 ? '日' : dow === 6 ? '土' : ['月','火','水','木','金'][dow-1];
                    const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;

                    results.push({ date: dateStr, dow, dowStr, status: getStatus(dayBtn), session: '昼' });
                    results.push({ date: dateStr, dow, dowStr, status: getStatus(nightBtn), session: '夜' });
                });
            }
            return results;
        }""")

        for row in data:
            if row["dow"] not in WEEKEND_JS_DAYS:
                continue
            result.reservations.append(
                DayReservation(
                    date=row["date"],
                    day_of_week=row["dowStr"],
                    session=row["session"],
                    status=row["status"],
                )
            )
