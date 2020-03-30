# -*- coding: utf-8 -*-
import scrapy
from learn.items import LearnItem


class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['tlxsw.net']
    start_urls = ['https://www.tlxsw.net/full/1/']
    base_url = 'https://www.tlxsw.net'

    def parse(self, response):
        print(response.url)
        trs = response.xpath('//table[@class="table"]/tr')[1:]
        for tr in trs:
            book_type = tr.xpath('./td[1]/text()').get()
            book_name = tr.xpath('./td[2]/a/@title').get()
            book_link = tr.xpath('./td[2]/a/@href').get()
            book_auth = tr.xpath('./td[4]/text()').get()
            book_updt = '20' + tr.xpath('./td[5]/text()').get()
            book = LearnItem(
                book_type=book_type,
                book_name=book_name,
                book_link=book_link,
                book_auth=book_auth,
                book_updt=book_updt
            )
            yield book
        next_page = response.xpath('//ul[@id="pagelink"]/li[@class="next"]/a/@href').get()
        if next_page:
            next_page = self.base_url + next_page
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            return
