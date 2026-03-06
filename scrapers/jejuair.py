"""제주항공 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper


class JejuAirScraper(NewsRssScraper):
    name = "제주항공"
    rss_query = "제주항공+특가+항공권"
