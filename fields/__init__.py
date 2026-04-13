"""全フィールドスクレイパーの登録簿。

新しいフィールドを追加する場合:
  1. このディレクトリに新ファイルを作成してスクレイパークラスを実装
  2. 下の import と ALL_SCRAPERS に追記
"""

from fields.buggy_land import BuggyLandScraper
from fields.camp_hirokawa import CampHirokawaScraper
from fields.heat import HeatScraper
from fields.isgf import ISGFScraper
from fields.munakata import MunakataScraper
from fields.sabageland import SabagelandScraper
from fields.sansui import SansuiScraper
from fields.swat import SwatScraper
from fields.tactics_field import TacticsFieldScraper
from fields.woodbox import WoodboxScraper

ALL_SCRAPERS = [
    BuggyLandScraper(),
    WoodboxScraper(),
    SwatScraper(),
    SansuiScraper(),
    TacticsFieldScraper(),
    SabagelandScraper(),
    ISGFScraper(),
    HeatScraper(),
    CampHirokawaScraper(),
    MunakataScraper(),
]

__all__ = [
    "ALL_SCRAPERS",
    "BuggyLandScraper",
    "CampHirokawaScraper",
    "HeatScraper",
    "ISGFScraper",
    "MunakataScraper",
    "SabagelandScraper",
    "SansuiScraper",
    "SwatScraper",
    "TacticsFieldScraper",
    "WoodboxScraper",
]
