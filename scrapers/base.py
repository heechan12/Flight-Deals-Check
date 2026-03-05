from __future__ import annotations

import hashlib
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

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
