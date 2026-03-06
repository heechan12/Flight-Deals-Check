"""하나투어 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper, _TRAVEL_INCLUDE


class HanatourScraper(NewsRssScraper):
    name = "하나투어"
    rss_query = "하나투어+특가"
    include_keywords = _TRAVEL_INCLUDE
