import scrapy
import os
import re
from datetime import datetime
from urllib.parse import urljoin
from scrapy.selector import Selector

class ProcedurePlaywrightSpider(scrapy.Spider):
    name = "procedure_playwright"
    allowed_domains = ["servicepublic.gov.bf"]
    start_urls = ["http://www.servicepublic.gov.bf/"]

    keywords = [
    # termes généraux
    "service", "procédure", "démarche", "administrative", "formulaire", "demande",
    # destinés au public
    "particulier", "citoyen", "usager", "public",
    # expressions typiques des fiches de service
    "pièces à fournir", "conditions d’obtention", "conditions de délivrance",
    "délai de traitement", "lieu du service", "coût du service", "document requis",
    "formalités", "prestations", "acte administratif", "autorisation", "attestation",
    "inscription", "enrôlement", "certificat", "extrait", "permis", "immatriculation"
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "USER_AGENT": "DayendeBot (+https://github.com/Dayende-ib)",
        "FEED_EXPORT_ENCODING": "utf-8",
        "PLAYWRIGHT_INCLUDE_PAGE": True,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True, "args": ["--ignore-certificate-errors"]},
        "PLAYWRIGHT_CONTEXT_ARGS": {"ignore_https_errors": True},
        "ROBOTSTXT_OBEY": False,
    }

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url, meta={"playwright": True})

    async def parse(self, response):
        """Charge la page avec JavaScript activé"""
        page = response.meta["playwright_page"]
        await page.wait_for_timeout(2000)  # Attendre le rendu JS

        content = await page.content()
        selector = Selector(text=content)
        await page.close()

        links = selector.css("a::attr(href)").getall()
        for link in links:
            if not link:
                continue

            url = urljoin(response.url, link)

            # Si c’est un lien PDF pertinent
            if link.endswith(".pdf") and any(kw in link.lower() for kw in self.keywords):
                yield scrapy.Request(
                    url,
                    callback=self.save_pdf,
                    meta={"playwright": False}  # inutile d’activer JS ici
                )

            # Si c’est une page du site
            elif "servicepublic.gov.bf" in url and not link.endswith(".pdf"):
                yield scrapy.Request(
                    url,
                    callback=self.parse_page,
                    meta={"playwright": True}
                )

    async def parse_page(self, response):
        """Analyse une page rendue avec JavaScript"""
        page = response.meta["playwright_page"]
        await page.wait_for_timeout(2000)
        html = await page.content()
        await page.close()
        selector = Selector(text=html)

        titre = selector.css("h1::text, h2::text, title::text").get()
        texte = " ".join(selector.css("p::text, li::text, div::text, span::text").getall())
        texte_clean = re.sub(r"\s+", " ", texte.lower())

        if any(kw in texte_clean for kw in self.keywords):
            os.makedirs("data/pages_playwright", exist_ok=True)
            file_name = re.sub(r"[^a-zA-Z0-9]", "_", titre or "page")[:60] + ".txt"
            path = os.path.join("data/pages_playwright", file_name)

            with open(path, "w", encoding="utf-8") as f:
                f.write(texte_clean)

            with open("data/sources_playwright.txt", "a", encoding="utf-8") as f:
                f.write(response.url + "\n")

            yield {
                "url": response.url,
                "titre": titre.strip() if titre else "Sans titre",
                "contenu": texte_clean,
                "date_scraping": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    def save_pdf(self, response):
        os.makedirs("data/pdfs_playwright", exist_ok=True)
        file_name = os.path.join("data/pdfs_playwright", os.path.basename(response.url))

        with open(file_name, "wb") as f:
            f.write(response.body)

        self.log(f"📄 PDF téléchargé : {file_name}")

        with open("data/pdf_sources_playwright.txt", "a", encoding="utf-8") as f:
            f.write(response.url + "\n")
