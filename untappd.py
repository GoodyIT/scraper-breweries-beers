import scrapy
import re
import json
import csv
import requests
from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from chainxy.items import ChainItem

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup as BSoup
from lxml import etree

import cfscrape
from fake_useragent import UserAgent

import string
import time
import random
import pdb

class Untappd(scrapy.Spider):
    handle_httpstatus_all = True
    name = "untappd"

    domain = "https://untappd.com"
    search_url = "https://untappd.com/search?q=%s&type=brewery&sort=brewery_name_asc"
    brewery_list = []
    number_of_beers = 1
    number_of_images = 1

    number_of_loops = 0
    loop_limit = 200000
    beers_group = []

    cnt = 0

    proxy_list = [
        '37.48.118.90:13042',
        '83.149.70.159:13042'
    ]

    def __init__(self):
        self.option = webdriver.ChromeOptions()
        # self.option.add_argument('headless')
        self.option.add_argument('blink-settings=imagesEnabled=false')
        self.option.add_argument('--ignore-certificate-errors')
        self.option.add_argument('--ignore-ssl-errors')
        self.option.add_argument("--no-sandbox")
        self.option.add_argument("--disable-impl-side-painting")
        self.option.add_argument("--disable-setuid-sandbox")
        self.option.add_argument("--disable-seccomp-filter-sandbox")
        self.option.add_argument("--disable-breakpad")
        self.option.add_argument("--disable-client-side-phishing-detection")
        self.option.add_argument("--disable-cast")
        self.option.add_argument("--disable-cast-streaming-hw-encoding")
        self.option.add_argument("--disable-cloud-import")
        self.option.add_argument("--disable-popup-blocking")
        self.option.add_argument("--disable-session-crashed-bubble")
        self.option.add_argument("--disable-ipv6")
        proxy = random.choice(self.proxy_list)
        self.option.add_argument('--proxy-server=%s' % proxy)
        self.driver = webdriver.Chrome(executable_path='./data/chromedriver.exe', chrome_options=self.option)

    def start_requests(self):
        yield Request("https://stackoverflow.com/", callback=self.parse_dummy)

    def parse_dummy(self, response):
        self.driver.get("https://untappd.com/login")
        time.sleep(2)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys("beerfan003")
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "password"))).send_keys("imobile123")
        self.driver.find_element(By.XPATH, '//span[@class="button yellow submit-btn"]/input').click()
   
        self.driver.get("https://untappd.com/search?q=*&type=beer")
        time.sleep(1)
        yield Request("https://www.sitepoint.com/", callback=self.parse_beer, dont_filter = True)

    def parse_beer(self, response):
        self.number_of_loops += 1

        beers = etree.HTML(self.driver.page_source).xpath('//div[contains(@class, "beer-item")]')
        self.cnt += 1
        print('=========cnt', self.cnt)

        self.beers_group.append(beers)
        # pdb.set_trace()
        if len(beers) == 0 or self.number_of_loops == self.loop_limit: # no more beers from selenium, and start download
            for beers in self.beers_group:
                for beer in beers:
                    beer_details = beer.xpath(".//div[@class='beer-details']")
                    beer_url = self.domain + beer_details[0].xpath(".//p[@class='name']/a/@href")[0]
                    proxy = random.choice(self.proxy_list)
                    request = Request(beer_url, callback=self.parse_beer_image, meta={'proxy': proxy})

                    try:
                        request.meta['brewery_name'] = self.validate(beer_details[0].xpath(".//p[@class='brewery']//text()")[0])
                        request.meta['beer_Description'] = beer_details[0].xpath(".//p[contains(@class, 'style')]//text()")[0]
                    except:
                        request.meta['brewery_name'] = self.validate(beer_details[0].xpath(".//p[@class='style']//text()")[0])
                        request.meta['beer_Description'] = beer_details[0].xpath(".//p[contains(@class, 'style')]")[1].xpath(".//text()")[0]

                    request.meta['beer_name'] = self.validate(beer_details[0].xpath(".//p[@class='name']//text()")[0])
                    request.meta['beer_url'] = beer_url

                    details = beer.xpath(".//div[contains(@class, 'details')]")
                    request.meta['beer_ABV'] = self.validate(details[1].xpath(".//p[@class='abv']//text()")[0])
                    request.meta['beer_IBU'] = self.validate(details[1].xpath(".//p[@class='ibu']//text()")[0])
                    request.meta['beer_rating'] = self.validate(details[1].xpath(".//p[@class='rating']/span[@class='num']//text()")[0]).strip("()")

                    yield request
        else:
            try: 
                self.driver.switch_to.frame(self.driver.find_element_by_tag_name("iframe"))
                self.driver.find_element_by_id('branch-banner-close').click()
                self.driver.switch_to.default_content()
            except:
                self.driver.find_element_by_xpath('//a[contains(@class, "more_search")]')
                WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "more_search")]'))).click()
            time.sleep(3)
            yield Request("https://www.tutorialspoint.com/", callback=self.parse_beer, dont_filter = True)

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



        

