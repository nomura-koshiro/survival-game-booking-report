"""エントリーポイント: python main.py で実行。

スクレイピング -> 天気取得 -> LINE 送信を一気通貫で実行する。

使い方::

    uv sync
    uv run python main.py

crontab 設定例 (毎週金曜 8:00):
    0 8 * * 5 cd /path/to/project && uv run python main.py

環境変数 (.env ファイルまたは export):
    LINE_CHANNEL_ACCESS_TOKEN=xxx
    LINE_USER_ID=xxx
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


def _load_env() -> None:
    """sabagame/.env から環境変数を読み込む。既に設定済みの変数は上書きしない。"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key not in os.environ:
            os.environ[key] = value


async def _run() -> None:
    """メイン処理。"""
    from fields import ALL_SCRAPERS
    from notification import format_message, send_line_message
    from scraping.facade import ScraperFacade
    from weather.forecast import fetch_fukuoka_target_weather

    # 1. スクレイピング
    facade = ScraperFacade()
    facade.register_all(ALL_SCRAPERS)
    results = await facade.run()

    # 2. 天気取得
    print("\n▶ 天気予報を取得中...")
    try:
        weather = fetch_fukuoka_target_weather()
        for w in weather:
            holiday_label = f" [{w.holiday_name}]" if w.holiday_name else ""
            print(f"  {w.date}({w.day_of_week}){holiday_label}: {w.weather_emoji} {w.weather_text} {w.temp_max}℃/{w.temp_min}℃")
    except Exception as e:
        print(f"  ⚠ 天気取得失敗: {e}")
        weather = []

    # 3. メッセージ整形
    message = format_message(results, weather)
    print(f"\n{'━' * 60}")
    print("送信メッセージプレビュー:")
    print(f"{'━' * 60}")
    print(message)
    print(f"{'━' * 60}")
    print(f"文字数: {len(message)}")

    # 4. LINE 送信
    if "LINE_CHANNEL_ACCESS_TOKEN" not in os.environ:
        print("\n⚠ LINE_CHANNEL_ACCESS_TOKEN が未設定のため送信スキップ")
        print("  .env ファイルを sabagame/.env に作成してください")
        sys.exit(0)

    print("\n▶ LINE 送信中...")
    try:
        send_line_message(message)
        print("  ✓ LINE 送信完了!")
    except Exception as e:
        print(f"  ✗ LINE 送信失敗: {e}")
        sys.exit(1)


def main() -> None:
    _load_env()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
