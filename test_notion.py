"""
Notion 연동 테스트 스크립트

사용법:
  export NOTION_API_KEY="secret_xxx"
  export NOTION_DATABASE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  python test_notion.py
"""
import asyncio
import os
from scrapers.base import Deal
from notifiers.notion_notifier import NotionNotifier


async def main():
    api_key = os.environ.get("NOTION_API_KEY")
    db_id   = os.environ.get("NOTION_DATABASE_ID")

    if not api_key or not db_id:
        print("환경변수를 설정해주세요:")
        print("  export NOTION_API_KEY='secret_xxx'")
        print("  export NOTION_DATABASE_ID='xxxxxxxx...'")
        return

    notifier = NotionNotifier(api_key=api_key, database_id=db_id)

    # DB 접근 검증
    ok = await notifier.verify()
    if not ok:
        return

    # 테스트 딜 1개 등록
    test_deal = Deal(
        source="테스트",
        title="[테스트] 항공 특가 알림 연동 확인",
        url="https://github.com/heechan12/Flight-Deals-Check",
    )
    await notifier.add_deals([test_deal], [])
    print("Notion DB에서 테스트 행이 추가됐는지 확인해주세요!")


asyncio.run(main())
