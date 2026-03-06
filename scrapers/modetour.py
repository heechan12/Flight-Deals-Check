"""모두투어 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper, _TRAVEL_INCLUDE


class ModetourScraper(NewsRssScraper):
    name = "모두투어"
    rss_query = "모두투어+특가"
    include_keywords = _TRAVEL_INCLUDE
