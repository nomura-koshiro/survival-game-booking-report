"""HEAT AIRSOFT (太宰府) -- Wix サイト「予約状況」ページ。"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.constants import DOW_LABELS
from core.models import DayReservation, FieldResult
from scraping.base import BaseFieldScraper
from scraping.gcal import (
    fetch_gcal_events,
    parse_gcal_events,
    scrape_gcal_embedded,
)
from scraping.utils import guess_year


class HeatScraper(BaseFieldScraper):
    name = "HEAT AIRSOFT（太宰府）"
    url = "https://www.heatairsoft.com/%E4%BA%88%E7%B4%84"
    method = "Wix予約状況ページ → GCal埋め込みを取得"

    _keywords = ["定例", "貸切", "イベント", "ゲーム", "DAY", "予約", "受付", "休"]

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        # domcontentloaded で待機 (networkidle は Wix で完了しない)
        await page.goto(self.url, timeout=60_000)
        await page.wait_for_load_state("domcontentloaded", timeout=30_000)
        await asyncio.sleep(8)  # Wix の JS レンダリング待ち (長めに取る)

        # 方法1: メインページから直接 GCal iframe を探す
        gcal_direct = await page.evaluate("""() => {
            function findGcalInFrames(doc) {
                const iframes = doc.querySelectorAll('iframe');
                for (const f of iframes) {
                    if ((f.src || '').includes('calendar.google.com')) return f.src;
                    try {
                        const inner = f.contentDocument;
                        if (inner) {
                            const found = findGcalInFrames(inner);
                            if (found) return found;
                        }
                    } catch(e) {}
                }
                return null;
            }
            return findGcalInFrames(document);
        }""")

        if gcal_direct:
            result.method += " → GCal直接検出"
            events = await fetch_gcal_events(page, gcal_direct)
            if events and parse_gcal_events(
                events, result, keywords=self._keywords
            ):
                return

        # 方法2: Wix iframe (filesusr.com) 経由で GCal を探す
        wix_iframe_src = await page.evaluate("""() => {
            const iframes = document.querySelectorAll('iframe');
            const wix = Array.from(iframes).find(
                f => (f.src || '').includes('filesusr.com')
                  || (f.src || '').includes('wixsite.com')
                  || (f.src || '').includes('htmlcomponentservice')
            );
            return wix ? wix.src : null;
        }""")

        if wix_iframe_src:
            result.method += " → Wix iframe検出"
            wix_page = await page.context.new_page()
            try:
                await wix_page.goto(wix_iframe_src, timeout=45_000)
                await wix_page.wait_for_load_state("domcontentloaded", timeout=20_000)
                await asyncio.sleep(5)
                if await scrape_gcal_embedded(
                    wix_page, result, keywords=self._keywords
                ):
                    return
            except Exception:
                pass
            finally:
                await wix_page.close()

        # 方法3: ページ上のテキストからイベント情報を抽出 (フォールバック)
        text = await page.evaluate("() => document.body?.innerText || ''")
        if text and ("定例" in text or "貸切" in text or "予約" in text):
            result.method += " → テキスト抽出フォールバック"
            self._parse_text_fallback(text, result)
            return

        if not result.error:
            result.error = "GCal/Wix iframe未検出。サイト構造が変更された可能性。"

    def _parse_text_fallback(self, text: str, result: FieldResult) -> None:
        """ページテキストから定例会・貸切等の情報を抽出する。"""
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            dm = re.search(r"(\d{1,2})/(\d{1,2})", line)
            if not dm:
                continue
            if not any(kw in line for kw in self._keywords):
                continue

            mo, d = int(dm.group(1)), int(dm.group(2))
            y = guess_year(mo)
            try:
                dt = datetime(y, mo, d)
            except ValueError:
                continue

            result.reservations.append(
                DayReservation(
                    date=dt.strftime("%Y-%m-%d"),
                    day_of_week=DOW_LABELS[dt.weekday()],
                    session="終日",
                    status="イベントあり",
                    event_name=line[:60],
                    note=line[:120],
                )
            )
