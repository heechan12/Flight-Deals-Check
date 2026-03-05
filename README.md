# ✈️ 항공 특가 알림 (check_flight)

대한항공, 아시아나항공, 인터파크 특가 딜을 자동으로 감지하고 Gmail로 알려주는 서비스입니다.
**Python + GitHub Actions** 기반으로 완전 무료 운영 가능합니다.

## 구조

```
check_flight/
├── .github/workflows/
│   └── check_deals.yml       # GitHub Actions 스케줄 (4시간마다 실행)
├── scrapers/
│   ├── base.py               # Deal 데이터 모델, 기본 스크래퍼 클래스
│   ├── korean_air.py         # 대한항공 특가 (Google News RSS)
│   ├── asiana.py             # 아시아나항공 특가 (Google News RSS)
│   └── interpark.py          # 인터파크 항공 특가 (Playwright)
├── notifiers/
│   └── email_notifier.py     # Gmail SMTP 알림
├── data/
│   └── seen_deals.json       # 이미 알림한 딜 ID 저장 (중복 방지)
├── main.py                   # 실행 진입점
└── requirements.txt
```

## 스크래핑 전략

| 출처 | 방식 | 이유 |
|---|---|---|
| 대한항공 | Google News RSS | 공식 사이트가 Cloudflare로 차단됨 |
| 아시아나항공 | Google News RSS | 공식 사이트 접근 불가 |
| 인터파크 | Playwright (headless Chrome) | JS 렌더링 필요 |

- **Google News RSS**: `news.google.com/rss/search`로 최근 30일 내 특가/할인 뉴스 수집
- **중복 방지**: `seen_deals.json`에 알림한 딜 ID를 저장해 재알림 방지
- **부정 뉴스 필터**: 사고, 결항, 파업 등 관련 없는 뉴스 자동 제외

## 셋업 방법

### 1. Gmail 앱 비밀번호 발급

1. [Google 계정 보안](https://myaccount.google.com/security) 접속
2. **2단계 인증** 활성화 (필수)
3. **앱 비밀번호** 생성 → 앱: "메일", 기기: "기타(직접 입력)" → 이름: "check_flight"
4. 생성된 16자리 비밀번호 복사

### 2. GitHub Repository 설정

1. 이 코드를 GitHub에 push
2. Repository → **Settings → Secrets and variables → Actions**
3. 아래 3개 Secret 등록:

| Secret 이름 | 설명 | 예시 |
|---|---|---|
| `GMAIL_USER` | Gmail 주소 | `your@gmail.com` |
| `GMAIL_PASSWORD` | 앱 비밀번호 (16자리) | `abcd efgh ijkl mnop` |
| `GMAIL_TO` | 알림 받을 이메일 (비워두면 GMAIL_USER로 발송) | `notify@gmail.com` |

### 3. 로컬 테스트

```bash
# 패키지 설치
pip install -r requirements.txt
playwright install chromium

# 환경변수 설정
export GMAIL_USER="your@gmail.com"
export GMAIL_PASSWORD="앱비밀번호16자리"
export GMAIL_TO="notify@gmail.com"

# dry-run (이메일 발송 없이 딜만 확인)
python main.py --dry-run

# 실제 실행
python main.py

# 강제 전송 (seen_deals 무시하고 현재 딜 전체 발송)
python main.py --force-notify
```

## GitHub Actions 실행 주기

- **자동**: 4시간마다 (KST 01, 05, 09, 13, 17, 21시)
- **수동**: GitHub → Actions → "항공 특가 알림 체크" → Run workflow
  - `dry-run`: 이메일 발송 없이 딜만 확인
  - `force-notify`: seen_deals 무시하고 전체 발송

## 새 스크래퍼 추가 방법

1. `scrapers/` 폴더에 새 파일 생성 (예: `hanatour.py`)
2. `BaseScraper`를 상속하고 `scrape()` 메서드 구현
3. `main.py`의 `SCRAPERS` 리스트에 추가

```python
# scrapers/hanatour.py
from .base import BaseScraper, Deal

class HanatourScraper(BaseScraper):
    name = "하나투어"

    async def scrape(self) -> list[Deal]:
        # 구현
        ...
```

### RSS 기반 스크래퍼 추가 (권장)

특정 항공사/여행사 사이트가 차단된 경우 Google News RSS 방식을 사용합니다:

```python
# scrapers/jeju_air.py
RSS_URL = "https://news.google.com/rss/search?q=제주항공+특가&hl=ko&gl=KR&ceid=KR:ko"
MAX_AGE_DAYS = 30  # 최근 N일 이내 뉴스만 수집
```

## 설정 값 조정

| 파일 | 상수 | 설명 | 기본값 |
|---|---|---|---|
| `korean_air.py` | `MAX_AGE_DAYS` | 뉴스 최대 수집 기간 | `30` |
| `asiana.py` | `MAX_AGE_DAYS` | 뉴스 최대 수집 기간 | `30` |
| `korean_air.py` / `asiana.py` | `EXCLUDE_KEYWORDS` | 제외할 뉴스 키워드 | 사고, 결항, 파업 등 |
| `interpark.py` | `DEAL_KEYWORDS` | 딜로 인식할 키워드 | 특가, 할인, 단독 등 |

## 비용

| 항목 | 비용 |
|---|---|
| GitHub Actions | 무료 (Public repo 무제한, Private repo 월 2,000분) |
| Gmail SMTP | 무료 |
| 총 비용 | **$0** |
