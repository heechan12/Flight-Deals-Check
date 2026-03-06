"""대한항공 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper


class KoreanAirScraper(NewsRssScraper):
    name = "대한항공"
    rss_query = "대한항공+특가+항공권"
