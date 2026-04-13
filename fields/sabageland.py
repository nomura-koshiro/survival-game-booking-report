"""福岡サバゲーランド 新宮店 -- Google カレンダー埋め込み。"""

from scraping.gcal import GCalFieldScraper


class SabagelandScraper(GCalFieldScraper):
    name = "福岡サバゲーランド 新宮店"
    url = "http://fukuokasabageland.com/"
    method = "トップページ内Googleカレンダー埋め込みを取得"
    keywords = ["定例", "貸切", "イベント", "ゲーム", "10禁", "サバゲー", "休"]
