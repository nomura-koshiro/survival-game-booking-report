"""スクレイピング結果と天気予報を LINE 用メッセージに整形する。"""

from __future__ import annotations

import re

from core.models import DayReservation, DayWeather, FieldResult

# フィールド名 -> 短縮名
_SHORT_NAMES: dict[str, str] = {
    "バギーランド（北九州）": "バギーランド",
    "WOODBOX（北九州）": "WOODBOX",
    "福岡サバゲSWAT・SAF": "SWAT",
    "山水グリーンフィールド": "山水",
    "Tactics Field（タクティクスフィールド）": "Tactics",
    "福岡サバゲーランド 新宮店": "サバゲーランド新宮",
    "ISGF（糸島サバイバルゲームフィールド）": "ISGF糸島",
    "HEAT AIRSOFT（太宰府）": "HEAT太宰府",
    "キャンプ広川 (CAMP HIROKAWA)": "キャンプ広川",
    "福岡サバゲーキャンプ宗像基地": "宗像基地",
}

# ノイズイベント名 (部分一致で除外)
_NOISE_KEYWORDS: list[str] = [
    "24時間",
    "シューティングレンジ営業",
    "予約受付中",
    "参加お待ち",
    "🔥予約",
]


def _short_name(name: str) -> str:
    return _SHORT_NAMES.get(name, name)


def _is_noise(text: str) -> bool:
    return any(kw in text for kw in _NOISE_KEYWORDS)


def _pick_best_event(reservations: list[DayReservation]) -> str:
    """複数イベントから最も有用な1件のイベント名を選ぶ。"""
    for r in reservations:
        if r.event_name and not _is_noise(r.event_name):
            cleaned = re.sub(r"[🔥🔫🔰🎉✨☆]", "", r.event_name).strip()
            # 「15名」のような人数だけのイベント名はスキップ
            if re.fullmatch(r"\d+名?", cleaned):
                continue
            # 「予約38様(内🔰4名)」のようなものもスキップ
            if re.match(r"予約\d+", cleaned):
                continue
            return cleaned
    return ""


def _extract_people(reservations: list[DayReservation]) -> int | None:
    """予約から人数を抽出する。複数予約は合算する。"""
    total = 0
    found = False

    for r in reservations:
        # people_count があればそれを使う
        if r.people_count and r.people_count > 0:
            total += r.people_count
            found = True
            continue

        text = f"{r.event_name} {r.status} {r.note}".translate(
            str.maketrans("０１２３４５６７８９", "0123456789")
        )

        # 「予約38様」パターン (サバゲーランド)
        m = re.search(r"予約(\d+)様", text)
        if m:
            total += int(m.group(1))
            found = True
            continue

        # 「N名」パターン (ISGF「2名 小野様」等)
        m = re.search(r"(\d+)\s*名", text)
        if m:
            val = int(m.group(1))
            if 1 <= val < 500:
                total += val
                found = True
                continue

        # 「N人予約」パターン
        m = re.search(r"(\d+)\s*人予約", text)
        if m:
            total += int(m.group(1))
            found = True

    return total if found else None


def _extract_remaining(reservations: list[DayReservation]) -> int | None:
    """残枠数を抽出する。"""
    for r in reservations:
        if r.remaining is not None:
            return r.remaining
    return None


def _get_status_tag(reservations: list[DayReservation]) -> str:
    """簡潔なステータスタグを返す。"""
    for r in reservations:
        if "受付終了" in r.status:
            return "受付終了"
        if "満員" in r.status:
            return "満員"
        if "貸切" in r.status:
            return "貸切"
        if "募集中" in r.status:
            return "募集中"
        if "中止" in r.status:
            return "中止"
    return ""


def _format_field_line(
    field_result: FieldResult,
    day_res: list[DayReservation],
) -> tuple[str, int]:
    """1フィールド1日分を整形する。(表示文字列, ソート用人数) を返す。"""
    name = _short_name(field_result.name)
    people = _extract_people(day_res)
    remaining = _extract_remaining(day_res)
    tag = _get_status_tag(day_res)

    # 人数表示を組み立て
    if people:
        count_str = f"{people}名"
    elif remaining is not None:
        count_str = f"残{remaining}枠"
    else:
        count_str = "--"

    # 補足情報 (ステータスタグのみ、イベント名は省略)
    extra_str = f"  ({tag})" if tag else ""

    # 昼/夜がある場合は補足に追記
    day_r = next((r for r in day_res if r.session == "昼"), None)
    night_r = next((r for r in day_res if r.session == "夜"), None)
    if day_r and night_r and not people and not remaining:
        def short_s(r: DayReservation) -> str:
            if "予約可" in r.status:
                return "○"
            if "満員" in r.status or "受付終了" in r.status or "締切" in r.status:
                return "✗"
            if "イベント" in r.status:
                return "△"
            return r.status[:3]
        count_str = f"昼{short_s(day_r)}/夜{short_s(night_r)}"

    line = f"  {name}: {count_str}{extra_str}"
    sort_key = people if people else 0
    return line, sort_key


def _format_date_header(w: DayWeather) -> str:
    """天気付き日付ヘッダー。祝日の場合は祝日名を併記する。"""
    month_day = f"{int(w.date[5:7])}/{int(w.date[8:10])}"
    holiday_tag = f"🎌{w.holiday_name} " if w.holiday_name else ""
    header = f"📅 {month_day}({w.day_of_week}) {holiday_tag}{w.weather_emoji}{w.weather_text}"
    if w.temp_max and w.temp_min and w.temp_max != "-" and w.temp_min != "-":
        header += f" {w.temp_max}/{w.temp_min}℃"
    elif w.temp_max and w.temp_max != "-":
        header += f" {w.temp_max}℃"
    if w.pop and w.pop != "-":
        header += f" 降水{w.pop}%"
    return header


def format_message(
    results: list[FieldResult],
    weather: list[DayWeather],
) -> str:
    """スクレイピング結果 + 天気予報 -> LINE 送信用テキスト。"""
    lines: list[str] = ["🔫 今週の予約状況 (土日・祝日)", ""]

    for w in weather:
        lines.append(_format_date_header(w))
        lines.append("─────────────")

        field_lines: list[tuple[str, int]] = []
        for field_result in results:
            if field_result.error and not field_result.reservations:
                continue

            day_res = [r for r in field_result.reservations if r.date == w.date]
            if not day_res:
                continue

            field_lines.append(_format_field_line(field_result, day_res))

        if field_lines:
            # 人数が多い順にソート (0は末尾)
            field_lines.sort(key=lambda x: (-x[1] if x[1] > 0 else 0, x[0]))
            for line, _ in field_lines:
                lines.append(line)
        else:
            lines.append("  情報なし")
        lines.append("")

    # エラーフィールド
    errors = [r for r in results if r.error]
    if errors:
        names = ", ".join(_short_name(r.name) for r in errors)
        lines.append(f"⚠️ 取得不可: {names}")

    return "\n".join(lines)
