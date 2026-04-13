"""Tactics Field -- 予約ページ (Google カレンダー埋め込み)。"""

from scraping.gcal import GCalFieldScraper


class TacticsFieldScraper(GCalFieldScraper):
    name = "Tactics Field（タクティクスフィールド）"
    url = "https://www.tactics-field.com/reservation/"
    method = "予約ページ内Googleカレンダー埋め込みを取得"
    keywords = ["定例", "貸切", "イベント", "ゲーム", "DAY", "セミ", "フル", "休", "参加"]
    no_iframe_error = "GCal iframe未検出。JS動的読み込みの可能性。"
