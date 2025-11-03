import scrapy
from admin_scraper.items import AdminScraperItem

class ServicePublicSpider(scrapy.Spider):
    name = "service_public"
    allowed_domains = ["google.com"]
    start_urls = ["google.com"]

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
           'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
           # Other middlewares...
        },
        'ROBOTSTXT_OBEY': True,
    }

    def parse(self, response):
        # Follow all links that seem to be a "procedure" page
        for href in response.css('a[href*="procedure"]::attr(href)').getall():
            yield response.follow(href, callback=self.parse_page)

    def parse_page(self, response):
        item = AdminScraperItem()
        item['url'] = response.url
        item['titre'] = response.css("h1::text").get('').strip()
        item['contenu'] = " ".join(response.css("div.field-items p::text").getall()).strip()
        if item['titre'] and item['contenu']:
            yield item
        
        with open("data/sources.txt", "a") as f:
            f.write(response.url + "\n")

