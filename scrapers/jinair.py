"""진에어 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper


class JinAirScraper(NewsRssScraper):
    name = "진에어"
    rss_query = "진에어+특가+항공권"
