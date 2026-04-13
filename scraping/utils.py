"""共通ユーティリティ関数。"""

from datetime import datetime, timedelta
from typing import Any

from core.constants import DOW_LABELS, WEEKEND_JS_DAYS
from core.models import DayReservation


def guess_year(month: int) -> int:
    """月番号から年を推定する。

    現在の月から前後 6 ヶ月の範囲で比較し、最も近い年を返す。
    年またぎのデータ（例: 12 月に翌年 1 月の情報を取得）に対応する。
    """
    now = datetime.now()
    year = now.year
    if month < now.month - 6:
        year += 1
    elif month > now.month + 6:
        year -= 1
    return year


def next_month_first_day(offset: int = 1) -> datetime:
    """現在月から指定オフセット分後の月初日を返す。"""
    base = datetime.now().replace(day=1)
    for _ in range(offset):
        base = (base + timedelta(days=32)).replace(day=1)
    return base


def js_row_to_day_reservation(
    row: dict[str, Any], session: str = "終日"
) -> DayReservation | None:
    """JavaScript スクレイピング結果の辞書を DayReservation に変換する。

    週末 (土・日) 以外のデータは None を返して破棄する。
    """
    if row["dow"] not in WEEKEND_JS_DAYS:
        return None
    return DayReservation(
        date=row["date"],
        day_of_week=row["dowStr"],
        session=session,
        status=row["status"],
        people_count=row.get("peopleCount"),
        remaining=row.get("remaining"),
        event_name=row.get("eventName", ""),
        note=row.get("note", ""),
    )
