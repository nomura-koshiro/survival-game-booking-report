"""日本の祝日判定と「サバゲーできる日」の集合を提供する。

`target_dates()` は次の予約対象日 (土日 + 祝日) を返す。
- 範囲: 今日 〜 次の土曜日 + 2日 (= 月曜)
- 土曜18時以降は次の土曜扱いに繰り下げる (既存週末ロジック踏襲)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache

import jpholiday


def is_holiday(d: date) -> bool:
    """日本の祝日判定。"""
    return jpholiday.is_holiday(d)


def holiday_name(d: date) -> str:
    """祝日名を返す。祝日でなければ空文字。"""
    name = jpholiday.is_holiday_name(d)
    return name or ""


def target_dates() -> list[str]:
    """次の予約対象日 (土日 + 祝日) を YYYY-MM-DD 形式で返す。"""
    now = datetime.now()
    today = now.date()

    days_until_sat = (5 - today.weekday()) % 7
    if days_until_sat == 0 and now.hour >= 18:
        days_until_sat = 7
    next_sat = today + timedelta(days=days_until_sat)
    end = next_sat + timedelta(days=2)

    targets: list[str] = []
    cur = today
    while cur <= end:
        if cur.weekday() in (5, 6) or is_holiday(cur):
            targets.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)
    return targets


@lru_cache(maxsize=1)
def target_date_set() -> frozenset[str]:
    """target_dates() の集合版 (スクレイパーのフィルタ用)。プロセス内で1度のみ計算する。"""
    return frozenset(target_dates())
