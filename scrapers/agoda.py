"""아고다 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper, _TRAVEL_INCLUDE


class AgodaScraper(NewsRssScraper):
    name = "아고다"
    rss_query = "아고다+특가+항공"
    include_keywords = _TRAVEL_INCLUDE
