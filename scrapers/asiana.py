"""
아시아나항공 특가 스크래퍼 - Google News RSS 기반

아시아나항공 웹사이트는 직접 접근이 어려워
Google News RSS를 통해 특가 뉴스를 수집합니다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, Deal

RSS_URL = (
    "https://news.google.com/rss/search"
    "?q=아시아나항공+특가+항공권&hl=ko&gl=KR&ceid=KR:ko"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
EXCLUDE_KEYWORDS = ["사고", "추락", "결항", "지연", "파업", "소송", "사망"]
MAX_AGE_DAYS = 30


class AsianaScraper(BaseScraper):
    name = "아시아나항공"

    async def scrape(self) -> list[Deal]:
        deals: list[Deal] = []
        try:
            async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15) as client:
                resp = await client.get(RSS_URL)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml-xml")
            items = soup.find_all("item")

            for item in items:
                title = item.find("title")
                link = item.find("link")
                pub_date = item.find("pubDate")
                source = item.find("source")

                if not title or not link:
                    continue

                title_text = title.text.strip()
                link_text = link.text.strip() if link.text else ""

                if any(kw in title_text for kw in EXCLUDE_KEYWORDS):
                    continue
                if not any(kw in title_text for kw in ["특가", "할인", "프로모션", "이벤트", "세일", "SALE"]):
                    continue

                if pub_date:
                    try:
                        pub_dt = parsedate_to_datetime(pub_date.text)
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                        if datetime.now(timezone.utc) - pub_dt > timedelta(days=MAX_AGE_DAYS):
                            continue
                    except Exception:
                        pass

                source_name = source.text.strip() if source else ""
                extra = f"출처: {source_name}" if source_name else None
                deadline = pub_date.text.strip()[:16] if pub_date else None

                deals.append(self._make_deal(
                    title=title_text,
                    url=link_text,
                    deadline=deadline,
                    extra=extra,
                ))

            print(f"[{self.name}] {len(deals)}개 딜 발견 (RSS {len(items)}개 중 필터링)")
        except Exception as e:
            print(f"[{self.name}] 스크래핑 오류: {e}")

        return deals
