# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AdminScraperItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    titre = scrapy.Field()
    contenu = scrapy.Field()
