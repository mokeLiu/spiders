# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class LevelSpider(CrawlSpider):
    name = 'level'
    allowed_domains = ['tlxsw.net']
    start_urls = ['http://tlxsw.net/full/1/']

    rules = (
        # 小说文章：https://www.tlxsw.net/html/1244/896245.html
        Rule(LinkExtractor(allow=r'.+/html/\d+/\d+\.html'), callback='parse_chapter', follow=False),  # 有回调函数要提前
        # 小说章节：https://www.tlxsw.net/html/1244/1/
        Rule(LinkExtractor(allow=r'.+/html/\d+/'), follow=True),
        # 小说列表：https://www.tlxsw.net/full/1/
        Rule(LinkExtractor(allow=r'.+/full/\d+/'), follow=True),
    )

    def parse_chapter(self, response):
        title = response.xpath('//*[@id="content"]/div[1]/h1/text()').get()
        print(title)
