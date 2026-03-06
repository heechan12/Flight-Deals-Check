"""노랑풍선 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper, _TRAVEL_INCLUDE


class NorangScraper(NewsRssScraper):
    name = "노랑풍선"
    rss_query = "노랑풍선+특가+항공"
    include_keywords = _TRAVEL_INCLUDE
