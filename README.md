# survival-game-booking-report

福岡県内のサバゲーフィールド10箇所の週末予約状況をスクレイピングし、天気予報と合わせてLINEで通知するツール。

## 対象フィールド

| フィールド | エリア |
| --- | --- |
| バギーランド | 北九州 |
| WOODBOX | 北九州 |
| SWAT SAF | 福岡 |
| 山水グリーンフィールド | 福岡 |
| Tactics Field | 福岡 |
| サバゲーランド 新宮店 | 福岡 |
| ISGF | 糸島 |
| HEAT AIRSOFT | 太宰府 |
| キャンプ広川 | 広川 |
| サバゲーキャンプ宗像基地 | 宗像 |

## セットアップ

### 環境変数

`.env.example` をコピーして `.env` を作成し、LINE Messaging API のトークンを設定する。

```bash
cp .env.example .env
```

```text
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_USER_ID=your_user_id_here
```

### 依存関係インストール

```bash
uv sync
uv run python -m playwright install chromium
```

## 実行方法

```bash
uv run python main.py
```

## 定期実行

GitHub Actions で毎日 19:00 JST に自動実行する設定が `.github/workflows/report.yml` に含まれている。
ローカル cron で動かす場合の例 (毎週金曜 8:00):

```cron
0 8 * * 5 cd /path/to/project && uv run python main.py
```

## ディレクトリ構成

```text
.
├── main.py                          # エントリーポイント (.env読込 → スクレイピング → 天気 → LINE通知)
├── .env.example                     # 環境変数テンプレート
│
├── core/                            # 共通モジュール
│   ├── constants.py                 #   定数 (曜日ラベル, GCalセレクタ, JS snippets)
│   └── models.py                    #   データモデル (DayReservation, FieldResult, DayWeather)
│
├── fields/                          # フィールド別スクレイパー (各クラスは BaseFieldScraper を継承)
│   ├── __init__.py                  #   ALL_SCRAPERS 登録簿
│   ├── buggy_land.py                #   バギーランド - HTMLカレンダーテーブルのJS評価
│   ├── woodbox.py                   #   WOODBOX - WordPress予約カレンダー (予約数:N人)
│   ├── swat.py                      #   SWAT - PHPカレンダー ([残り:N] 形式)
│   ├── sansui.py                    #   山水 - Wixサイトの新着情報テキスト解析
│   ├── tactics_field.py             #   Tactics Field - GCal iframe
│   ├── sabageland.py                #   サバゲーランド新宮 - GCal iframe
│   ├── isgf.py                      #   ISGF糸島 - GCal iframe
│   ├── heat.py                      #   HEAT太宰府 - Wix + GCal iframe
│   ├── camp_hirokawa.py             #   キャンプ広川 - テキスト確認 (臨時休業中)
│   └── munakata.py                  #   宗像基地 - GCal iframe + ニュースページ
│
├── scraping/                        # スクレイピング基盤
│   ├── base.py                      #   BaseFieldScraper 抽象基底クラス (Template Method)
│   ├── gcal.py                      #   GCal iframe 共通ヘルパー + GCalFieldScraper 基底
│   ├── facade.py                    #   ScraperFacade (全スクレイパーの登録・実行・結果出力)
│   ├── utils.py                     #   ユーティリティ (年推定, JS結果→DayReservation変換)
│   └── output.py                    #   結果の表示・JSON保存
│
├── weather/                         # 天気予報
│   └── forecast.py                  #   気象庁API (福岡県) から週末天気を取得
│
└── notification/                    # LINE通知
    ├── formatter.py                 #   スクレイピング結果 + 天気 → LINE用テキスト整形
    └── line.py                      #   LINE Messaging API push送信
```
