"""스카이스캐너 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper, _TRAVEL_INCLUDE


class SkyscannerScraper(NewsRssScraper):
    name = "스카이스캐너"
    rss_query = "스카이스캐너+특가+항공"
    include_keywords = _TRAVEL_INCLUDE
