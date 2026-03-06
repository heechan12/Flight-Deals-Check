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
NOTION_DB_URL  = "https://api.notion.com/v1/databases/{}"
NOTION_VERSION = "2022-06-28"


class NotionNotifier:
    def __init__(self, api_key: str, database_id: str):
        # 하이픈 포함/미포함 모두 허용
        self.database_id = database_id.replace("-", "")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    async def verify(self) -> bool:
        """DB 접근 가능 여부 및 컬럼 구성을 사전 검증합니다."""
        url = NOTION_DB_URL.format(self.database_id)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=self.headers)

        if resp.status_code != 200:
            print(f"[Notion] DB 접근 실패 (HTTP {resp.status_code})")
            body = resp.json()
            print(f"[Notion] 오류: {body.get('message', body)}")
            print(f"[Notion] 확인사항:")
            print(f"  1. NOTION_DATABASE_ID 가 올바른지 확인 (현재: {self.database_id})")
            print(f"  2. 통합(Integration)이 해당 DB에 연결되어 있는지 확인")
            print(f"     Notion DB 페이지 → 우측 상단 ... → 연결 → 통합 선택")
            return False

        props = resp.json().get("properties", {})
        required = {"이름", "출처", "링크", "발견일", "상태"}
        missing = required - set(props.keys())
        if missing:
            print(f"[Notion] DB 컬럼 누락: {missing}")
            print(f"[Notion] 현재 DB 컬럼: {list(props.keys())}")
            print(f"[Notion] 누락된 컬럼을 Notion DB에 추가해주세요.")
            return False

        print(f"[Notion] DB 연결 확인 완료 ✓")
        return True

    async def add_deals(self, new_deals: list[Deal], seen_deals: list[Deal]) -> None:
        # 등록 전 DB 접근 검증
        if not await self.verify():
            return

        today = datetime.now().strftime("%Y-%m-%d")

        async with httpx.AsyncClient(timeout=15) as client:
            tasks = (
                [self._create_page(client, deal, "🆕 신규", today) for deal in new_deals]
                + [self._create_page(client, deal, "✅ 확인완료", today) for deal in seen_deals]
            )
            results = await asyncio.gather(*tasks, return_exceptions=True)

        ok    = sum(1 for r in results if not isinstance(r, Exception))
        errors = [r for r in results if isinstance(r, Exception)]

        print(f"[Notion] {ok}개 등록 완료" + (f" | {len(errors)}개 실패" if errors else ""))
        for e in errors[:3]:  # 최대 3개만 출력
            print(f"[Notion] 오류 상세: {e}")

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
                "이름":   {"title":  [{"text": {"content": deal.title[:2000]}}]},
                "출처":   {"select": {"name": deal.source}},
                "링크":   {"url": deal.url or None},
                "발견일": {"date":   {"start": today}},
                "상태":   {"select": {"name": status}},
            },
        }
        resp = await client.post(NOTION_API_URL, headers=self.headers, json=payload)
        if not resp.is_success:
            body = resp.json()
            raise Exception(f"HTTP {resp.status_code} - {body.get('message', body)}")
