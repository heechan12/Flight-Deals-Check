"""
Notion API를 이용한 딜 데이터베이스 등록 모듈

필요한 Notion DB 컬럼 구성 (타입):
  - 이름   (Title)
  - 출처   (Select)
  - 링크   (URL)
  - 발견일 (Date)
  - 상태   (Select): 🆕 신규 / ✅ 확인완료

설정 방법:
1. notion.so/my-integrations → 새 통합 생성 → API 키 복사
2. Notion에서 DB 페이지 생성 후 통합 연결 (... → 연결)
3. DB URL에서 ID 추출: notion.so/{workspace}/{DATABASE_ID}?v=...
4. GitHub Secrets에 NOTION_API_KEY, NOTION_DATABASE_ID 등록
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import httpx

from scrapers.base import Deal

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"


class NotionNotifier:
    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    async def add_deals(self, new_deals: list[Deal], seen_deals: list[Deal]) -> None:
        today = datetime.now().strftime("%Y-%m-%d")

        async with httpx.AsyncClient(timeout=15) as client:
            tasks = (
                [self._create_page(client, deal, "🆕 신규", today) for deal in new_deals]
                + [self._create_page(client, deal, "✅ 확인완료", today) for deal in seen_deals]
            )
            results = await asyncio.gather(*tasks, return_exceptions=True)

        ok    = sum(1 for r in results if not isinstance(r, Exception))
        fails = sum(1 for r in results if isinstance(r, Exception))
        print(f"[Notion] {ok}개 등록 완료" + (f" | {fails}개 실패" if fails else ""))

    async def _create_page(
        self,
        client: httpx.AsyncClient,
        deal: Deal,
        status: str,
        today: str,
    ) -> None:
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "이름": {
                    "title": [{"text": {"content": deal.title[:2000]}}]
                },
                "출처": {
                    "select": {"name": deal.source}
                },
                "링크": {
                    "url": deal.url or None
                },
                "발견일": {
                    "date": {"start": today}
                },
                "상태": {
                    "select": {"name": status}
                },
            },
        }
        resp = await client.post(NOTION_API_URL, headers=self.headers, json=payload)
        resp.raise_for_status()
