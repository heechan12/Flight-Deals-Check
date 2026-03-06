"""아시아나항공 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper


class AsianaScraper(NewsRssScraper):
    name = "아시아나항공"
    rss_query = "아시아나항공+특가+항공권"
