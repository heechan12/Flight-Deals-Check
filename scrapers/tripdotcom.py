"""트립닷컴 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper, _TRAVEL_INCLUDE


class TripdotcomScraper(NewsRssScraper):
    name = "트립닷컴"
    rss_query = "트립닷컴+특가+항공"
    include_keywords = _TRAVEL_INCLUDE
