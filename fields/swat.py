"""福岡サバゲ SWAT SAF -- PHP 予約カレンダー ([残り:N] 形式)。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.models import FieldResult
from scraping.base import BaseFieldScraper
from scraping.utils import js_row_to_day_reservation, next_month_first_day


class SwatScraper(BaseFieldScraper):
    name = "福岡サバゲSWAT・SAF"
    url = "https://swat1980.jp/res/svg-entry/pc.php"
    method = "PHP予約カレンダー (残枠数[残り:N]形式) 2ヶ月分取得"

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        for month_offset in range(2):
            if month_offset == 0:
                url = self.url
            else:
                ym = next_month_first_day(1).strftime("%Y-%m")
                url = f"{self.url}?ym={ym}"

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
                        const dayMatch = cellText.match(/^(\d{1,2})\s/);
                        if (!dayMatch) continue;
                        const day = parseInt(dayMatch[1]);
                        if (day < 1 || day > 31) continue;

                        let d;
                        try { d = new Date(year, month - 1, day); } catch(e) { continue; }
                        const dow = d.getDay();

                        const remainingMatches = [...cellText.matchAll(/\[残り:(\d+)\]/g)];
                        let totalRemaining = null;
                        if (remainingMatches.length > 0) {
                            totalRemaining = remainingMatches.reduce((s, m) => s + parseInt(m[1]), 0);
                        }

                        let status = '';
                        let eventName = '';
                        if (cellText.includes('受付終了')) status = '受付終了';
                        else if (totalRemaining !== null) status = `残${totalRemaining}枠`;
                        else if (cellText.includes('定休日')) continue;

                        if (cellText.includes('定例会')) eventName = '定例会';
                        if (cellText.includes('記念祭')) eventName = cellText.match(/.+記念祭/)?.[0] || '記念祭';
                        if (cellText.includes('貸切')) {
                            eventName = cellText.includes('受付終了') ? '貸切(予約済)' : '貸切受付中';
                        }

                        results.push({
                            date: `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,
                            dow,
                            dowStr: dow === 0 ? '日' : dow === 6 ? '土' : ['月','火','水','木','金'][dow-1],
                            status: status || '情報あり',
                            remaining: totalRemaining,
                            eventName,
                            note: cellText.replace(/\s+/g, ' ').substring(0, 120),
                        });
                    }
                }
                return results;
            }""")

            for row in data:
                reservation = js_row_to_day_reservation(row)
                if reservation:
                    result.reservations.append(reservation)
