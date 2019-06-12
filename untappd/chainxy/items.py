# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class ChainItem(Item):
    brewery_name = Field()
    beer_name = Field()
    beer_images = Field()
    beer_url = Field()
    beer_ABV = Field()
    beer_IBU = Field()
    beer_Description = Field()
    beer_rating = Field()
    typo_error = Field()
    
    