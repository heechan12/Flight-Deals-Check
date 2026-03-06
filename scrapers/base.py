from __future__ import annotations

import hashlib
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, field as dc_field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, BrowserContext


@dataclass
class Deal:
    source: str          # 출처 (대한항공, 아시아나 등)
    title: str           # 딜 제목
    url: str             # 상세 페이지 URL
    price: Optional[str] = None      # 가격 (예: "599,000원~")
    origin: Optional[str] = None     # 출발지
    destination: Optional[str] = None  # 도착지
    departure_date: Optional[str] = None  # 출발일
    deadline: Optional[str] = None   # 예약 마감일
    discount: Optional[str] = None   # 할인율/금액
    extra: Optional[str] = None      # 기타 정보
    found_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: str = field(init=False)

    def __post_init__(self):
        # source + title + price 조합으로 고유 ID 생성
        raw = f"{self.source}|{self.title}|{self.price}|{self.url}"
        self.id = hashlib.md5(raw.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "price": self.price,
            "origin": self.origin,
            "destination": self.destination,
            "departure_date": self.departure_date,
            "deadline": self.deadline,
            "discount": self.discount,
            "extra": self.extra,
            "found_at": self.found_at,
        }


@asynccontextmanager
async def browser_context():
    """
    항공사 사이트 접근에 최적화된 브라우저 컨텍스트.

    주요 설정:
    - --disable-http2: HTTP/2 프로토콜 오류 방지 (ERR_HTTP2_PROTOCOL_ERROR)
    - --no-sandbox: GitHub Actions 환경 호환
    - 실제 Chrome과 동일한 User-Agent, 언어 설정
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-http2",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            extra_http_headers={
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            },
        )
        try:
            yield context
        finally:
            await browser.close()


class BaseScraper:
    name: str = "base"

    async def scrape(self) -> list[Deal]:
        raise NotImplementedError

    def _make_deal(self, **kwargs) -> Deal:
        return Deal(source=self.name, **kwargs)


_RSS_BASE = "https://news.google.com/rss/search"
_RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
_COMMON_EXCLUDE = ["사고", "추락", "결항", "지연", "파업", "소송", "사망"]
_AIRLINE_INCLUDE = ["특가", "할인", "프로모션", "이벤트", "세일", "SALE"]
_TRAVEL_INCLUDE  = ["특가", "할인", "프로모션", "이벤트", "세일", "SALE", "패키지", "단독"]


class NewsRssScraper(BaseScraper):
    """
    Google News RSS 기반 공통 스크래퍼.

    서브클래스에서 name, rss_query, include_keywords 만 지정하면 됩니다.

    예:
        class JinAirScraper(NewsRssScraper):
            name = "진에어"
            rss_query = "진에어+특가+항공권"
    """
    rss_query: str = ""
    max_age_days: int = 30
    exclude_keywords: list[str] = _COMMON_EXCLUDE
    include_keywords: list[str] = _AIRLINE_INCLUDE

    async def scrape(self) -> list[Deal]:
        url = f"{_RSS_BASE}?q={self.rss_query}&hl=ko&gl=KR&ceid=KR:ko"
        deals: list[Deal] = []
        try:
            async with httpx.AsyncClient(headers=_RSS_HEADERS, follow_redirects=True, timeout=15) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml-xml")
            items = soup.find_all("item")

            for item in items:
                title   = item.find("title")
                link    = item.find("link")
                pub_date = item.find("pubDate")
                source  = item.find("source")

                if not title or not link:
                    continue

                title_text = title.text.strip()
                link_text  = link.text.strip() if link.text else ""

                if any(kw in title_text for kw in self.exclude_keywords):
                    continue
                if not any(kw in title_text for kw in self.include_keywords):
                    continue

                if pub_date:
                    try:
                        pub_dt = parsedate_to_datetime(pub_date.text)
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                        if datetime.now(timezone.utc) - pub_dt > timedelta(days=self.max_age_days):
                            continue
                    except Exception:
                        pass

                source_name = source.text.strip() if source else ""
                deals.append(self._make_deal(
                    title=title_text,
                    url=link_text,
                    deadline=pub_date.text.strip()[:16] if pub_date else None,
                    extra=f"출처: {source_name}" if source_name else None,
                ))

            print(f"[{self.name}] {len(deals)}개 딜 발견 (RSS {len(items)}개 중 필터링)")
        except Exception as e:
            print(f"[{self.name}] 스크래핑 오류: {e}")

        return deals
