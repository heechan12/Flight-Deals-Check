"""
항공 특가 알림 메인 실행 파일

사용법:
  python main.py                    # 모든 스크래퍼 실행
  python main.py --dry-run          # 이메일 발송 없이 딜만 확인
  python main.py --force-notify     # seen_deals 무시하고 현재 딜 전체 발송
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from scrapers.korean_air import KoreanAirScraper
from scrapers.asiana import AsianaScraper
from scrapers.jinair import JinAirScraper
from scrapers.jejuair import JejuAirScraper
from scrapers.tway import TWayScraper
from scrapers.interpark import InterparkScraper
from scrapers.hanatour import HanatourScraper
from scrapers.myrealtrip import MyrealtripScraper
from scrapers.tripdotcom import TripdotcomScraper
from scrapers.agoda import AgodaScraper
from scrapers.skyscanner import SkyscannerScraper
from scrapers.modetour import ModetourScraper
from scrapers.norang import NorangScraper
from notifiers.email_notifier import EmailNotifier

SEEN_DEALS_FILE = Path("data/seen_deals.json")

# 활성화할 스크래퍼 목록 (주석 처리로 비활성화 가능)
SCRAPERS = [
    # 항공사
    KoreanAirScraper(),
    AsianaScraper(),
    JinAirScraper(),
    JejuAirScraper(),
    TWayScraper(),
    # 여행사 + 예약 플랫폼
    InterparkScraper(),
    HanatourScraper(),
    MyrealtripScraper(),
    TripdotcomScraper(),
    AgodaScraper(),
    SkyscannerScraper(),
    ModetourScraper(),
    NorangScraper(),
]


def load_seen_ids() -> set[str]:
    if SEEN_DEALS_FILE.exists():
        data = json.loads(SEEN_DEALS_FILE.read_text(encoding="utf-8"))
        return set(data.get("ids", []))
    return set()


def save_seen_ids(ids: set[str]) -> None:
    SEEN_DEALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_DEALS_FILE.write_text(
        json.dumps({"ids": sorted(ids)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def run(dry_run: bool = False, force_notify: bool = False) -> None:
    print("=" * 50)
    print("항공 특가 알림 시스템 시작")
    print("=" * 50)

    # 모든 스크래퍼 병렬 실행
    tasks = [scraper.scrape() for scraper in SCRAPERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_deals = []
    for scraper, result in zip(SCRAPERS, results):
        if isinstance(result, Exception):
            print(f"[{scraper.name}] 실패: {result}")
        else:
            all_deals.extend(result)

    print(f"\n전체 {len(all_deals)}개 딜 수집 완료")

    if not all_deals:
        print("수집된 딜이 없습니다.")
        return

    # 새 딜 필터링
    seen_ids = load_seen_ids() if not force_notify else set()
    new_deals = [d for d in all_deals if d.id not in seen_ids]

    print(f"신규 딜: {len(new_deals)}개 (기존: {len(all_deals) - len(new_deals)}개 중복 제외)")

    if not new_deals:
        print("새로운 딜이 없습니다. 종료합니다.")
        return

    # 딜 목록 출력
    print("\n[신규 딜 목록]")
    for deal in new_deals:
        print(f"  [{deal.source}] {deal.title}")
        if deal.price:
            print(f"    가격: {deal.price}")
        if deal.url:
            print(f"    URL: {deal.url}")

    if dry_run:
        print("\n[dry-run 모드] 이메일 발송 생략")
        return

    # 이메일 발송
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_PASSWORD")
    gmail_to = os.environ.get("GMAIL_TO", gmail_user)  # TO가 없으면 본인에게

    if not gmail_user or not gmail_password:
        print("\n[경고] GMAIL_USER 또는 GMAIL_PASSWORD 환경변수가 없습니다.")
        print("  - 로컬 테스트: export GMAIL_USER=your@gmail.com GMAIL_PASSWORD=앱비밀번호")
        print("  - GitHub: Repository Settings → Secrets and variables → Actions")
        sys.exit(1)

    notifier = EmailNotifier(
        smtp_user=gmail_user,
        smtp_password=gmail_password,
        to_email=gmail_to,
    )
    notifier.send(new_deals)

    # seen_deals 업데이트
    seen_ids.update(d.id for d in new_deals)
    save_seen_ids(seen_ids)
    print(f"\nseen_deals.json 업데이트 완료 (총 {len(seen_ids)}개 ID 저장)")


def main() -> None:
    parser = argparse.ArgumentParser(description="항공 특가 알림 시스템")
    parser.add_argument("--dry-run", action="store_true", help="이메일 발송 없이 딜만 확인")
    parser.add_argument("--force-notify", action="store_true", help="seen_deals 무시하고 전체 발송")
    args = parser.parse_args()

    asyncio.run(run(dry_run=args.dry_run, force_notify=args.force_notify))


if __name__ == "__main__":
    main()
