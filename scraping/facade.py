"""ScraperFacade -- 全スクレイパーの登録・実行・結果出力を統括する。"""

from __future__ import annotations

from datetime import datetime

from core.models import FieldResult
from scraping.base import BaseFieldScraper
from scraping.output import print_field_result, save_results_json


class ScraperFacade:
    """サバゲーフィールドスクレイパーの Facade。

    使い方::

        facade = ScraperFacade()
        facade.register_all(ALL_SCRAPERS)
        results = await facade.run()
    """

    def __init__(self) -> None:
        self._scrapers: list[BaseFieldScraper] = []

    def register(self, scraper: BaseFieldScraper) -> "ScraperFacade":
        """スクレイパーを 1 件登録する (メソッドチェーン対応)。"""
        self._scrapers.append(scraper)
        return self

    def register_all(self, scrapers: list[BaseFieldScraper]) -> "ScraperFacade":
        """スクレイパーを一括登録する。"""
        self._scrapers.extend(scrapers)
        return self

    async def run(
        self,
        *,
        headless: bool = True,
        output_path: str = "sabagame_results.json",
    ) -> list[FieldResult]:
        """全スクレイパーを順次実行し、結果を表示・保存する。"""
        from playwright.async_api import async_playwright

        print("=" * 70)
        print("  福岡サバゲーフィールド 週末予約数スクレイパー")
        print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(
                locale="ja-JP",
                timezone_id="Asia/Tokyo",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            )

            all_results: list[FieldResult] = []
            for scraper in self._scrapers:
                print(f"▶ [{scraper.name}] スクレイピング中...")
                page = await context.new_page()
                try:
                    result = await scraper.scrape(page)
                    all_results.append(result)
                    weekend_count = sum(
                        1
                        for r in result.reservations
                        if r.day_of_week in {"土", "日"}
                    )
                    if result.error:
                        print(f"  ⚠ {result.error[:80]}")
                    print(
                        f"  ✓ 取得件数: {len(result.reservations)}件 (うち週末: {weekend_count}件)"
                    )
                except Exception as e:
                    all_results.append(
                        FieldResult(name=scraper.name, url=scraper.url, error=str(e))
                    )
                    print(f"  ✗ 致命的エラー: {e}")
                finally:
                    await page.close()

            await browser.close()

        # 結果表示
        print()
        print("=" * 70)
        print("  スクレイピング結果サマリー")
        print("=" * 70)
        for result in all_results:
            print_field_result(result)

        # JSON 保存
        save_results_json(all_results, output_path)
        print(f"\n{'━' * 60}")
        print(f"詳細結果JSON: {output_path}")

        return all_results
