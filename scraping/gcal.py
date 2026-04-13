"""Google カレンダー共通ヘルパーと GCal 系基底クラス。"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from core.constants import DOW_LABELS, GCAL_EVENTS_JS, GCAL_SRC_JS
from core.models import DayReservation, FieldResult
from scraping.base import BaseFieldScraper


async def fetch_gcal_src(page: Page) -> str | None:
    """ページ内の Google カレンダー iframe の src URL を返す。"""
    return await page.evaluate(GCAL_SRC_JS)


def _to_agenda_url(gcal_src: str) -> str:
    """GCal 埋め込みURLをAGENDAモードに変換する。

    AGENDA モードは全イベントをリスト表示するため、
    「他N件」の折りたたみ問題を回避できる。
    """
    import urllib.parse

    parsed = urllib.parse.urlparse(gcal_src)
    params = urllib.parse.parse_qs(parsed.query)
    params["mode"] = ["AGENDA"]
    new_query = urllib.parse.urlencode(params, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


async def fetch_gcal_events(page: Page, gcal_src: str) -> list[dict[str, str]]:
    """Google カレンダーページを新規タブで開き、イベントリストを取得する。

    まず AGENDA モード (リスト表示) で全件取得を試みる。
    取得できなければ元の URL でフォールバックする。
    """
    gcal_page = await page.context.new_page()
    try:
        # AGENDA モードで全件取得を試みる
        agenda_url = _to_agenda_url(gcal_src)
        await gcal_page.goto(agenda_url, timeout=30_000)
        await gcal_page.wait_for_load_state("networkidle", timeout=15_000)
        await asyncio.sleep(3)
        events = await gcal_page.evaluate(GCAL_EVENTS_JS)

        if events:
            return events

        # フォールバック: 元の URL
        await gcal_page.goto(gcal_src, timeout=30_000)
        await gcal_page.wait_for_load_state("networkidle", timeout=15_000)
        await asyncio.sleep(3)
        return await gcal_page.evaluate(GCAL_EVENTS_JS)
    finally:
        await gcal_page.close()


def parse_gcal_events(
    events: list[dict[str, str]],
    result: FieldResult,
    *,
    keywords: list[str] | None = None,
) -> bool:
    """GCal イベントリストを DayReservation に変換して result に追記する。

    Returns:
        1 件以上追記できた場合は True。
    """
    seen: set[tuple[str, str]] = set()
    for ev in events:
        combined = f"{ev['text']} {ev['label']} {ev.get('title', '')}".strip()
        if keywords is not None and not any(kw in combined for kw in keywords):
            continue

        date_str = ""
        day_of_week = ""
        dm = re.search(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", combined)
        if dm:
            y, mo, d = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
            try:
                dt = datetime(y, mo, d)
                date_str = dt.strftime("%Y-%m-%d")
                day_of_week = DOW_LABELS[dt.weekday()]
            except ValueError:
                pass

        name_m = re.search(r"「(.+?)」", combined)
        event_name = name_m.group(1) if name_m else combined.split("終日")[0].strip()
        event_name = event_name[:80]

        key = (date_str, event_name)
        if key in seen:
            continue
        seen.add(key)

        result.reservations.append(
            DayReservation(
                date=date_str,
                day_of_week=day_of_week,
                session="終日",
                status="イベントあり",
                event_name=event_name,
                note=combined[:120],
            )
        )

    return len(result.reservations) > 0


async def scrape_gcal_embedded(
    page: Page,
    result: FieldResult,
    *,
    keywords: list[str] | None = None,
    no_iframe_error: str = "GCal iframe未検出。",
) -> bool:
    """Google カレンダー埋め込みから予約情報を取得して result へ追記する。

    Returns:
        イベントを 1 件以上取得できた場合は True。
    """
    gcal_src = await fetch_gcal_src(page)
    if not gcal_src:
        result.error = no_iframe_error
        return False

    result.method += " → GCal iframe検出"
    events = await fetch_gcal_events(page, gcal_src)

    if parse_gcal_events(events, result, keywords=keywords):
        return True

    result.error = (
        f"GCalイベント要素取得不可。iframe内JS描画の可能性。URL: {gcal_src[:80]}"
    )
    return False


class GCalFieldScraper(BaseFieldScraper):
    """GCal 埋め込みパターンの共通基底クラス。

    サブクラスは keywords / no_iframe_error を定義するだけで動く。
    pre_scrape() をオーバーライドすれば事前操作(スクロール等)を挟める。
    """

    keywords: list[str] | None = None
    no_iframe_error: str = "GCal iframe未検出。"

    async def pre_scrape(self, page: Page) -> None:
        """GCal 取得前のページ操作。必要ならオーバーライドする。"""

    async def _do_scrape(self, page: Page, result: FieldResult) -> None:
        await page.goto(self.url, timeout=30_000)
        await page.wait_for_load_state("networkidle", timeout=15_000)
        await self.pre_scrape(page)
        await scrape_gcal_embedded(
            page,
            result,
            keywords=self.keywords,
            no_iframe_error=self.no_iframe_error,
        )
