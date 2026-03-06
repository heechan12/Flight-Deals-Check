"""마이리얼트립 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper, _TRAVEL_INCLUDE


class MyrealtripScraper(NewsRssScraper):
    name = "마이리얼트립"
    rss_query = "마이리얼트립+특가"
    include_keywords = _TRAVEL_INCLUDE
