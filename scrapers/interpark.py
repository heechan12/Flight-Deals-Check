"""
인터파크(NOL) 항공 특가 스크래퍼
- URL: https://nol.interpark.com/ (항공 + 여행 통합 포털)
- Playwright로 JS 렌더링 후 특가 링크 수집
"""
from __future__ import annotations

from playwright.async_api import Page

from .base import BaseScraper, Deal, browser_context

BASE_URL = "https://nol.interpark.com/"
DEAL_KEYWORDS = ["특가", "할인", "이벤트", "단독", "마감임박", "한정", "최저", "긴급", "SALE", "프로모션"]
EXCLUDE_KEYWORDS = ["쿠폰", "포인트", "적립", "회원가입", "로그인", "앱 다운"]


class InterparkScraper(BaseScraper):
    name = "인터파크"

    async def scrape(self) -> list[Deal]:
        deals: list[Deal] = []

        async with browser_context() as context:
            page = await context.new_page()
            try:
                await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
                # 스크롤로 lazy-load 트리거
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await page.wait_for_timeout(1500)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

                deals = await self._extract_deals(page)
                print(f"[{self.name}] {len(deals)}개 딜 발견")

            except Exception as e:
                print(f"[{self.name}] 스크래핑 오류: {e}")

        return deals

    async def _extract_deals(self, page: Page) -> list[Deal]:
        deals: list[Deal] = []
        seen_titles: set[str] = set()

        links = await page.query_selector_all("a[href]")
        for link in links:
            text = (await link.inner_text()).strip()
            # 멀티라인 텍스트 정리
            text = " ".join(text.split())
            href = await link.get_attribute("href") or ""

            if not text or len(text) < 4 or text in seen_titles:
                continue
            if not href or href.startswith("javascript") or href == "#":
                continue
            if any(ex in text for ex in EXCLUDE_KEYWORDS):
                continue
            if not any(kw in text for kw in DEAL_KEYWORDS):
                continue

            seen_titles.add(text)
            full_url = (
                href if href.startswith("http")
                else f"https://nol.interpark.com{href}"
            )
            deals.append(self._make_deal(title=text[:100], url=full_url))

        return deals
