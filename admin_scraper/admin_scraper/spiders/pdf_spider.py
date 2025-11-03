import scrapy
import os
from urllib.parse import urljoin

class PDFSpider(scrapy.Spider):
    name = "pdf_spider"
    allowed_domains = ["servicepublic.gov.bf"]
    start_urls = ["https://www.servicepublic.gov.bf/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "USER_AGENT": "DayendeBot (+https://github.com/Dayende)",
        "FEED_EXPORT_ENCODING": "utf-8",
        "FILES_STORE": "data/pdfs"
    }

    def parse(self, response):
        # Trouver tous les liens PDF sur la page
        pdf_links = response.css("a::attr(href)").getall()
        for link in pdf_links:
            if link.endswith(".pdf"):
                pdf_url = urljoin(response.url, link)
                yield scrapy.Request(pdf_url, callback=self.save_pdf)

        # Suivre d'autres pages internes (liens internes au site)
        internal_links = response.css("a::attr(href)").getall()
        for link in internal_links:
            if link.startswith("/") or ("servicepublic.gov.bf" in link):
                next_page = urljoin(response.url, link)
                yield scrapy.Request(next_page, callback=self.parse)

    def save_pdf(self, response):
        # Créer le dossier s'il n'existe pas
        os.makedirs("data/pdfs", exist_ok=True)
        filename = os.path.join("data/pdfs", os.path.basename(response.url))

        # Sauvegarder le PDF localement
        with open(filename, "wb") as f:
            f.write(response.body)

        self.log(f"PDF téléchargé : {filename}")

        # Sauvegarder la source
        with open("data/pdf_sources.txt", "a", encoding="utf-8") as f:
            f.write(response.url + "\n")
