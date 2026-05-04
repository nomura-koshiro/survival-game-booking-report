"""定数定義モジュール。"""

#: 月曜始まりの曜日ラベル。Python の datetime.weekday() と同じ順序 (0=月)
DOW_LABELS: list[str] = ["月", "火", "水", "木", "金", "土", "日"]

#: 全角数字 → 半角数字変換テーブル
ZEN_TO_HAN: dict[int, int] = str.maketrans("０１２３４５６７８９", "0123456789")

# Google カレンダーのイベント DOM 要素を特定する CSS セレクター。
GCAL_EVENT_SELECTORS: str = (
    '[data-eventid], [data-eventchip], [class*="event"], '
    '[role="listitem"], [role="button"], .rb-n'
)

# Google カレンダーの iframe src URL を取得する JavaScript
GCAL_SRC_JS: str = """() => {
    const iframes = document.querySelectorAll('iframe');
    for (const f of iframes) {
        if ((f.src || '').includes('calendar.google.com')) return f.src;
    }
    return null;
}"""

# Google カレンダーページからイベント要素リストを取得する JavaScript。
GCAL_EVENTS_JS: str = (
    """() => {
    const results = [];
    const sel = '"""
    + GCAL_EVENT_SELECTORS
    + """';
    document.querySelectorAll(sel).forEach(el => {
        const text = (el.textContent || '').trim();
        const label = el.getAttribute('aria-label') || '';
        const title = el.getAttribute('title') || '';
        if (text.length > 1 || label.length > 1) {
            results.push({
                text: text.substring(0, 200),
                label: label.substring(0, 200),
                title: title.substring(0, 200),
            });
        }
    });
    return results.slice(0, 80);
}"""
)
