import scrapy
import re
import json
import csv
import requests
from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from chainxy.items import ChainItem


import cfscrape
from fake_useragent import UserAgent

import string
import time
import random
import pdb

class Untappd(scrapy.Spider):
    name = "untappd11"
    handle_httpstatus_list = [301]

    domain = "https://untappd.com"
    search_url = "https://untappd.com/search?q=%s&type=brewery&sort=brewery_name_asc"
    brewery_list = []
    number_of_beers = 1
    number_of_images = 1

    proxy_list = [
        '37.48.118.90:13042',
        '83.149.70.159:13042'
    ]

    cookies = {
        '__cfduid': 'd383f60c6733bf9b94e99c6a718d3d38c1560237067',
        '__utma': '13579763.1526814854.1560237076.1560237076.1560237076.1',
        '__utmc': '13579763' ,
        '__utmz': '13579763.1560237076.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
        '__utmt': '1',
        '_ALGOLIA': '79c29b2b-afd9-4548-b789-85290a05cb84',
        '__gads': 'ID=f996f0ec9c71aee6:T=1560237078:S=ALNI_MY7XZsX7RRWYF1juoE8F0rs2-jPHQ',
        'ut_d_l': 'e95ac755971bd0a9d8230c6fe09131ea5773ccd7cfb560911cf488ecc92e5cb76a07fc5868a71638986ab5d3443e55ff995e028c48acf2ad9beaaa46267db65dA2zDmqr2BsB+7U7u5tcgAgAeZQY1w/H/TrTB/wu+g3pDUKSePuZQ/cbmlSIexAGuKqhijV6WZbpmzTDwOYYXUQ==',
        'untappd_user_v3_e': 'd870a77f483ffc86b71ec7964fea92049ae0956c62816f3d48a8f5468d912f46fb6678b2c3f46757761afe341edadde052eda8cc2c26d9c4674b27a9bc337fc9szY1ZMiogRToPJXLUR1aFKVttuNqjhBRO70NV/RtxGFCgcT4EryeVTEGahJznTJMxmaEwbvYtihFvTrWloEtMA==',
        '__utmb': '13579763.4.10.1560237076',
        'ut_tos_update': 'true'
    }

    def start_requests(self):
        user_agent = UserAgent().random;
        proxy = random.choice(self.proxy_list)
        url = "https://untappd.com/search?q=*&type=beer"
        token, agent = cfscrape.get_tokens(url, 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36')
        request =  Request(url=url, cookies={'__cfduid': token['__cfduid']}, headers={'User-Agent': user_agent}, callback=self.parse_beer, meta={'proxy': proxy})

        yield request

    # def parse_brewery(self, response):
    #     breweries = response.xpath('//div[@class="results-container"]/div[@class="beer-item"]')
    #     for brewery in breweries:
    #         beer_list_url = brewery.xpath('.//div[@class="details brewery"]/p[@class="abv"]/a/@href').extract_first()
    #         proxy = random.choice(self.proxy_list)
    #         request = Request(self.domain + beer_list_url, callback=self.parse_beer, meta={'proxy': proxy})
    #         request.meta['brewery'] = response.meta['brewery']

    #         yield request

    def parse_beer(self, response):
        # pdb.set_trace()
        beers = response.xpath('//div[contains(@class, "beer-item")]')
        
        if len(beers):
            for beer in beers:
                beer_details = beer.xpath(".//div[@class='beer-details']")
                beer_url = self.domain + beer_details.xpath(".//p[@class='name']/a/@href").extract_first()
                proxy = random.choice(self.proxy_list)
                request = Request(beer_url, callback=self.parse_beer_image, meta={'proxy': proxy})

                request.meta['brewery_name'] = self.validate(beer_details.xpath(".//p[@class='brewery']//text()").extract_first())
                request.meta['beer_name'] = self.validate(beer_details.xpath(".//p[@class='name']//text()").extract_first())
                request.meta['beer_Description'] = beer_details.xpath(".//p[contains(@class, 'style')]").xpath(".//text()").extract_first()
                request.meta['beer_url'] = beer_url

                details = beer.xpath(".//div[contains(@class, 'details')]")
                request.meta['beer_ABV'] = self.validate(details.xpath(".//p[@class='abv']//text()").extract_first())
                request.meta['beer_IBU'] = self.validate(details.xpath(".//p[@class='ibu']//text()").extract_first())
                request.meta['beer_rating'] = self.validate(details.xpath(".//p[@class='rating']/span[@class='num']//text()").extract_first()).strip("()")

                yield request

            proxy = random.choice(self.proxy_list)
            request = Request("https://untappd.com/search/more_search/beer?offset=25&q=*&sort=beer_name_asc", callback=self.parse_beer, meta={'proxy': proxy}, cookies=self.cookies, headers={'accept-encoding': 'gzip, deflate, br', 'user-agent':' Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest'})
            yield request

        else:
            pdb.set_trace()
            print('------- end -----------')
        

    def parse_beer_image(self, response):
            item = ChainItem()

            item['brewery_name'] = response.meta['brewery_name']
            item['beer_name'] = response.meta['beer_name']
            item['beer_url'] = response.meta['beer_url']
            item['beer_Description'] = response.meta['beer_Description']
            item['beer_ABV'] = response.meta['beer_ABV']
            item['beer_IBU'] = response.meta['beer_IBU']
            item['beer_rating'] = response.meta['beer_rating']

            images = response.xpath("//div[@class='photo-boxes']/p/a/img/@data-original").extract()
            for x in range(0, min(len(images), int(self.number_of_images))):
                image = images[x]
                beer_image = self.format_filename(item['beer_name']) + '_image' + str(x+1) + '.jpg'
                x += 1
                proxy = random.choice(self.proxy_list)
                request = scrapy.Request(image, self.parse_image, meta={'proxy': proxy})
                request.meta['image_name'] = beer_image
                item['beer_images'] = beer_image        
                yield request

                yield item

    def parse_image(self, response):
        with open('images/' + response.meta["image_name"] + '.jpg', 'wb') as f:
            f.write(response.body)

    def validate(self, value):
        if value != None:
            try:
                return unicode(value.strip(), encoding='unicode-escape') 
            except TypeError:
                return value.strip()
        else:
            return ""

    def format_filename(self, s):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in s if c in valid_chars)
        filename = filename.replace(' ','_') # I don't like spaces in filenames.
        return filename



        

