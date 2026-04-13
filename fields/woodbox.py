"""WOODBOX (北九州) -- WordPress 予約カレンダー (予約数:N人 形式)。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.models import FieldResult
from scraping.base import BaseFieldScraper
from scraping.utils import js_row_to_day_reservation, next_month_first_day


class WoodboxScraper(BaseFieldScraper):
    name = "WOODBOX（北九州）"
    url = "https://woodbox.main.jp/yoyaku_calendar/"
    method = "WordPress予約カレンダー (予約数:N人形式) 2ヶ月分取得"

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        for month_offset in range(2):
            ym = next_month_first_day(month_offset).strftime("%Y-%m")
            url = f"{self.url}?date={ym}"

            await page.goto(url, timeout=30_000)
            await page.wait_for_load_state("networkidle", timeout=15_000)

            data = await page.evaluate(r"""() => {
                const results = [];
                const tables = document.querySelectorAll('table');
                for (const table of tables) {
                    const text = table.textContent || '';
                    const ymMatch = text.match(/(\d{4})年(\d{1,2})月/);
                    if (!ymMatch) continue;
                    const year = parseInt(ymMatch[1]);
                    const month = parseInt(ymMatch[2]);

                    const tds = table.querySelectorAll('td');
                    for (const td of tds) {
                        const cellText = td.textContent.trim();
                        const dayMatch = cellText.match(/^(\d{1,2})日/);
                        if (!dayMatch) continue;
                        const day = parseInt(dayMatch[1]);
                        if (day < 1 || day > 31) continue;

                        let d;
                        try { d = new Date(year, month - 1, day); } catch(e) { continue; }
                        const dow = d.getDay();

                        const bookingMatches = [...cellText.matchAll(/予約数:(\d+)人/g)];
                        let totalBooked = 0;
                        for (const bm of bookingMatches) totalBooked += parseInt(bm[1]);

                        let eventName = '';
                        if (cellText.includes('定例会')) eventName = '定例会';
                        else if (cellText.includes('初サバ')) eventName = '初サバ開催';
                        else if (cellText.includes('周年')) eventName = '周年祭';
                        else if (cellText.includes('セミオンリー')) eventName = 'セミオンリーDAY';
                        else if (cellText.includes('セミフル')) eventName = 'セミフル定例会';
                        else if (cellText.includes('ガスとエアコキ')) eventName = 'ガスコキ祭り';

                        let status = '';
                        if (cellText.includes('店休日')) status = '店休日';
                        else if (cellText.includes('満員御礼')) status = '満員御礼';
                        else if (totalBooked > 0) status = `${totalBooked}人予約済`;
                        else if (cellText.includes('受付終了')) status = '受付終了';
                        else status = '受付中(0人)';

                        results.push({
                            date: `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,
                            dow,
                            dowStr: dow === 0 ? '日' : dow === 6 ? '土' : ['月','火','水','木','金'][dow-1],
                            status,
                            peopleCount: totalBooked > 0 ? totalBooked : null,
                            eventName,
                            note: cellText.replace(/\s+/g, ' ').substring(0, 120),
                        });
                    }
                }
                return results;
            }""")

            for row in data:
                if row.get("status") == "店休日":
                    continue
                reservation = js_row_to_day_reservation(row)
                if reservation:
                    result.reservations.append(reservation)
