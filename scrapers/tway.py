"""티웨이항공 특가 스크래퍼 - Google News RSS 기반"""
from .base import NewsRssScraper


class TWayScraper(NewsRssScraper):
    name = "티웨이항공"
    rss_query = "티웨이항공+특가+항공권"
