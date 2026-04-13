"""気象庁APIから福岡の週末天気予報を取得する。"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta

from core.constants import DOW_LABELS
from core.models import DayWeather

#: 気象庁 天気予報API (福岡県: 400000)
JMA_FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/400000.json"

#: 天気コード -> (絵文字, 説明) マッピング
WEATHER_MAP: dict[str, tuple[str, str]] = {
    "100": ("☀️", "晴れ"),
    "101": ("🌤️", "晴れ時々曇り"),
    "102": ("🌦️", "晴れ一時雨"),
    "110": ("🌤️", "晴れ後曇り"),
    "111": ("🌤️", "晴れ後曇り一時雨"),
    "200": ("☁️", "曇り"),
    "201": ("⛅", "曇り時々晴れ"),
    "202": ("🌧️", "曇り一時雨"),
    "203": ("🌨️", "曇り一時雪"),
    "210": ("⛅", "曇り後晴れ"),
    "211": ("🌧️", "曇り後雨"),
    "300": ("🌧️", "雨"),
    "301": ("🌦️", "雨時々晴れ"),
    "302": ("🌧️", "雨時々止む"),
    "303": ("🌨️", "雨時々雪"),
    "311": ("🌨️", "雨後雪"),
    "313": ("🌦️", "雨後曇り"),
    "400": ("🌨️", "雪"),
    "401": ("🌨️", "雪時々晴れ"),
    "402": ("🌨️", "雪時々止む"),
}

#: 天気コード先頭桁のフォールバック
_WEATHER_EMOJI_FALLBACK: dict[str, tuple[str, str]] = {
    "1": ("☀️", "晴れ"),
    "2": ("☁️", "曇り"),
    "3": ("🌧️", "雨"),
    "4": ("🌨️", "雪"),
}


def _decode_weather_code(code: str) -> tuple[str, str]:
    """天気コードから (絵文字, テキスト) を返す。"""
    if code in WEATHER_MAP:
        return WEATHER_MAP[code]
    first = code[:1] if code else ""
    return _WEATHER_EMOJI_FALLBACK.get(first, ("❓", "不明"))


def _next_weekend() -> list[str]:
    """次の土曜・日曜の日付を YYYY-MM-DD で返す。"""
    today = datetime.now()
    days_until_saturday = (5 - today.weekday()) % 7
    # 土曜の夕方以降は翌週
    if days_until_saturday == 0 and today.hour >= 18:
        days_until_saturday = 7
    saturday = today + timedelta(days=days_until_saturday)
    sunday = saturday + timedelta(days=1)
    return [saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")]


def _find_area(areas: list[dict], keyword: str = "福岡") -> dict | None:
    """areas リストから keyword を含むエリアを返す。"""
    return next((a for a in areas if keyword in a["area"]["name"]), None)


def _extract_from_short_term(
    data: list[dict], target: str
) -> dict[str, str]:
    """短期予報 (data[0]) から対象日の天気・降水確率・気温を抽出する。"""
    info: dict[str, str] = {}
    short = data[0]

    for ts in short["timeSeries"]:
        dates = [d[:10] for d in ts["timeDefines"]]
        if target not in dates:
            continue
        idx = dates.index(target)
        area = _find_area(ts["areas"])
        if not area:
            continue

        # 天気コード
        codes = area.get("weatherCodes", [])
        if idx < len(codes) and codes[idx]:
            info.setdefault("weather_code", codes[idx])

        # 降水確率 (短期は 6 時間刻みなので日中の最大値を取る)
        pops = area.get("pops", [])
        if pops:
            day_pops = [int(p) for p in pops if p and p != "-"]
            if day_pops:
                info.setdefault("pop", str(max(day_pops)))

    return info


def fetch_fukuoka_weekend_weather() -> list[DayWeather]:
    """気象庁APIから次の週末の福岡の天気予報を取得する。

    短期予報 (2-3日先) と週間予報 (7日先) の両方を参照し、
    短期予報に該当日があればそちらを優先する。
    """
    target_dates = _next_weekend()

    req = urllib.request.Request(
        JMA_FORECAST_URL,
        headers={"User-Agent": "sabagame-scraper/1.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    # 週間予報 (data[1])
    weekly = data[1]
    weather_ts = weekly["timeSeries"][0]
    temp_ts = weekly["timeSeries"][1]

    weather_area = _find_area(weather_ts["areas"])
    temp_area = _find_area(temp_ts["areas"])

    weather_dates = [d[:10] for d in weather_ts["timeDefines"]]
    temp_dates = [d[:10] for d in temp_ts["timeDefines"]]

    results: list[DayWeather] = []
    for target in target_dates:
        weather_code = ""
        pop = ""
        temp_max = ""
        temp_min = ""

        # まず週間予報から取得
        if weather_area and target in weather_dates:
            idx = weather_dates.index(target)
            codes = weather_area.get("weatherCodes", [])
            pops = weather_area.get("pops", [])
            weather_code = codes[idx] if idx < len(codes) else ""
            pop = pops[idx] if idx < len(pops) else ""

        if temp_area and target in temp_dates:
            idx = temp_dates.index(target)
            mins = temp_area.get("tempsMin", [])
            maxs = temp_area.get("tempsMax", [])
            temp_min = mins[idx] if idx < len(mins) else ""
            temp_max = maxs[idx] if idx < len(maxs) else ""

        # 短期予報で上書き (直近のほうが精度が高い)
        short_info = _extract_from_short_term(data, target)
        if short_info.get("weather_code"):
            weather_code = short_info["weather_code"]
        if short_info.get("pop"):
            pop = short_info["pop"]
        if short_info.get("temp_max") and short_info["temp_max"] != "-":
            temp_max = short_info["temp_max"]
        if short_info.get("temp_min") and short_info["temp_min"] != "-":
            temp_min = short_info["temp_min"]

        emoji, text = _decode_weather_code(weather_code)
        dt = datetime.strptime(target, "%Y-%m-%d")

        results.append(
            DayWeather(
                date=target,
                day_of_week=DOW_LABELS[dt.weekday()],
                weather_code=weather_code,
                weather_emoji=emoji,
                weather_text=text,
                pop=pop,
                temp_max=temp_max,
                temp_min=temp_min,
            )
        )

    return results
