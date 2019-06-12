import scrapy
import re
import json
import csv
import requests
from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from chainxy.items import ChainItem

import string
import time
import random
import pdb

class Untappd(scrapy.Spider):
    name = "untappd"
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

    def __init__(self, number_of_beers = 25, number_of_images = 3):
        self.number_of_images = number_of_images
        self.number_of_beers = number_of_beers

        with open('data/top 50.csv', encoding="utf8") as csvfile:
            brewery_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for brewery in brewery_reader:
                self.brewery_list.append("".join(str(x) for x in brewery))

    def start_requests(self):
        proxy = random.choice(self.proxy_list)
        for brewery in self.brewery_list:
            url = "https://untappd.com/search?q=" + brewery + "&type=brewery&sort=brewery_name_asc"
            request =  Request(url=url, callback=self.parse_brewery, meta={'proxy': proxy})
            request.meta['brewery'] = brewery

            yield request

    def parse_brewery(self, response):
        breweries = response.xpath('//div[@class="results-container"]/div[@class="beer-item"]')
        if len(breweries) == 0:
            # wrong brewery, Highlight
            item = ChainItem()
            item['brewery_name'] = response.meta['brewery']
            item['typo_error'] = 'yes'

            yield item
        else:
            beer_list_url = breweries[0].xpath('.//div[@class="details brewery"]/p[@class="abv"]/a/@href').extract_first()
            proxy = random.choice(self.proxy_list)
            request = Request(self.domain + beer_list_url, callback=self.parse_beer, meta={'proxy': proxy})
            request.meta['brewery'] = response.meta['brewery']

            yield request

    def parse_beer(self, response):
        beers = response.xpath('//div[@class="content"]/div[@class="beer-container"]/div[contains(@class, "beer-item")]')
        
        for x in range(0, min(len(beers), int(self.number_of_beers))):
            beer = beers[x];
            beer_details = beer.xpath(".//div[@class='beer-details']")
            beer_url = self.domain + beer_details.xpath(".//p[@class='name']/a/@href").extract_first()
            proxy = random.choice(self.proxy_list)
            request = Request(beer_url, callback=self.parse_beer_image, meta={'proxy': proxy})

            request.meta['brewery_name'] = self.validate(response.meta['brewery'])
            request.meta['beer_name'] = self.validate(beer_details.xpath(".//p[@class='name']//text()").extract_first())
            request.meta['beer_Description'] = beer_details.xpath(".//p[contains(@class, 'desc')]")[1].xpath(".//text()").extract_first()
            request.meta['beer_url'] = beer_url

            details = beer.xpath(".//div[@class='details']")
            request.meta['beer_ABV'] = self.validate(details.xpath(".//p[@class='abv']//text()").extract_first())
            request.meta['beer_IBU'] = self.validate(details.xpath(".//p[@class='ibu']//text()").extract_first())
            request.meta['beer_rating'] = self.validate(details.xpath(".//p[@class='rating']/span[@class='num']//text()").extract_first()).strip("()")

            yield request

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
        with open('images/' + response.meta["image_name"], 'wb') as f:
            f.write(response.body)

    def validate(self, value):
        if value != None:
            return value.strip()
        else:
            return ""

    def format_filename(self, s):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in s if c in valid_chars)
        filename = filename.replace(' ','_') # I don't like spaces in filenames.
        return filename



        

