# CLAUDE.md

## プロジェクト概要

福岡サバゲーフィールド10箇所の予約状況 (土日・祝日) をPlaywrightでスクレイピングし、気象庁APIの天気予報と日本の祝日情報と合わせてLINE Messaging APIで通知するPythonツール。

## 実行コマンド

```bash
# 依存関係インストール (pyproject.toml + uv.lock から)
uv sync

# Playwright ブラウザインストール
uv run python -m playwright install chromium

# 実行 (スクレイピング → 天気取得 → LINE送信)
uv run python main.py
```

## アーキテクチャ

- `main.py` — 唯一のエントリーポイント。.env読込 → スクレイピング → 天気 → LINE通知を一気通貫で実行
- `core/` — 定数 (`constants.py`) とデータモデル (`models.py`: DayReservation, FieldResult, DayWeather)
- `fields/` — フィールド別スクレイパー。すべて `BaseFieldScraper` を継承し `_do_scrape()` を実装
- `scraping/` — スクレイピング基盤。`BaseFieldScraper` (Template Method), `GCalFieldScraper` (GCal iframe共通), `ScraperFacade` (統括)
- `weather/` — 気象庁API天気予報取得
- `holiday/` — 日本の祝日判定 + 「予約対象日 (土日 + 祝日)」の集合提供 (jpholiday使用)
- `notification/` — LINE用メッセージ整形 + LINE Messaging API送信

## コーディング規約

- Python 3.13+、型ヒント必須
- import は絶対パス (`from core.models import ...`, `from scraping.base import ...`)
- 依存関係は `pyproject.toml` で管理し `uv.lock` で固定。必要なライブラリは積極的に採用してよい
- 環境変数は `.env` ファイルで管理。`.env` は gitignore 済み

## 新しいフィールドの追加手順

1. `fields/` に新ファイルを作成
2. `BaseFieldScraper` (または `GCalFieldScraper`) を継承したクラスを実装
3. `name`, `url`, `method` を定義し `_do_scrape()` を実装
4. `fields/__init__.py` の import と `ALL_SCRAPERS` リストに追加

## スクレイピングパターン

フィールドごとに取得方法が異なる。主なパターン:

- **GCal iframe**: `GCalFieldScraper` を継承するだけで動く (tactics_field, sabageland, isgf)
- **JS評価**: `page.evaluate()` でカレンダーDOMから情報抽出 (buggy_land, swat, woodbox)
- **テキスト解析**: ページテキストから正規表現で予約情報を抽出 (sansui, munakata)
- **複合**: 複数手法をフォールバックで組み合わせ (heat, munakata)

## 注意事項

- スクレイピング対象サイトの構造変更で動作しなくなることがある。エラー時は対象サイトのHTML構造を確認すること
- LINE テキストメッセージの上限は 5000 文字
- 予約対象日 (土・日 + 日本の祝日) のデータのみ抽出する。それ以外の平日データは破棄される
- 「対象日」の判定範囲は `holiday/jp.py::target_dates()` で集中管理 (今日 〜 次の月曜まで)
