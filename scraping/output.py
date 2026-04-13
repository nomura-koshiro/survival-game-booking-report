"""結果の表示・保存モジュール。"""

import json
from dataclasses import asdict
from datetime import datetime

from core.models import FieldResult


def print_field_result(result: FieldResult) -> None:
    """FieldResult の内容を標準出力に整形して出力する。"""
    print(f"\n{'━' * 60}")
    print(f"■ {result.name}")
    print(f"  URL    : {result.url}")
    print(f"  取得方法: {result.method}")
    if result.error:
        print(f"  ⚠ {result.error}")

    if not result.reservations:
        if not result.error:
            print("  予約情報なし")
        return

    weekend_res = [r for r in result.reservations if r.day_of_week in {"土", "日"}]
    if weekend_res:
        print(f"\n  【週末の予約状況】({len(weekend_res)}件)")
        for r in sorted(weekend_res, key=lambda x: x.date):
            date_str = r.date if r.date else "日付不明"
            parts = [f"    {date_str}({r.day_of_week})"]
            if r.session and r.session != "終日":
                parts.append(f"[{r.session}]")
            parts.append(f"→ {r.status}")
            if r.remaining is not None:
                parts.append(f"(残{r.remaining}枠)")
            if r.people_count:
                parts.append(f"({r.people_count}名)")
            if r.event_name:
                parts.append(f"【{r.event_name}】")
            print(" ".join(parts))
    else:
        print(f"\n  【全日程】({len(result.reservations)}件)")
        for r in result.reservations[:10]:
            print(
                f"    {r.date or '不明'}({r.day_of_week}) → {r.status} {r.event_name}"
            )


def save_results_json(results: list[FieldResult], path: str) -> None:
    """スクレイピング結果を JSON ファイルに保存する。"""
    output = {
        "scrape_date": datetime.now().isoformat(),
        "fields": [asdict(r) for r in results],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
