"""データモデル定義モジュール。"""

from dataclasses import dataclass, field


@dataclass
class DayReservation:
    """1 日分の予約情報を表すデータクラス。"""

    date: str
    """予約日付 (YYYY-MM-DD 形式)。"""

    day_of_week: str
    """曜日ラベル (土/日/祝/平日)。"""

    session: str
    """セッション区分 (昼/夜/終日)。"""

    status: str
    """予約ステータス (空き/満員/受付終了/○人予約済/募集中 等)。"""

    people_count: int | None = None
    """参加人数または予約人数。不明な場合は None。"""

    remaining: int | None = None
    """残枠数。不明な場合は None。"""

    event_name: str = ""
    """イベント名 (定例会/貸切/記念祭 等)。"""

    note: str = ""
    """セル全文など付加的なメモ情報。"""


@dataclass
class FieldResult:
    """サバゲーフィールド 1 件のスクレイピング結果を表すデータクラス。"""

    name: str
    """フィールド名称。"""

    url: str
    """スクレイピング対象の URL。"""

    method: str = ""
    """データ取得方法の説明文。"""

    reservations: list[DayReservation] = field(default_factory=list)
    """取得した予約情報のリスト。"""

    error: str = ""
    """エラーが発生した場合のメッセージ。"""


@dataclass
class DayWeather:
    """1 日分の天気予報。"""

    date: str
    day_of_week: str
    weather_code: str
    weather_emoji: str
    weather_text: str
    pop: str
    temp_max: str
    temp_min: str
