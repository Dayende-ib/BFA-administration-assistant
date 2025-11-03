import scrapy
import os
import re
from urllib.parse import urljoin
from datetime import datetime

class ProcedureParticulierSpider(scrapy.Spider):
    name = "procedure_particulier"
    allowed_domains = ["servicepublic.gov.bf"]
    start_urls = ["https://www.servicepublic.gov.bf/"]

    # Mots-clés cibles (en minuscules)
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
    }

    def parse(self, response):
        """Explore les liens du site et filtre ceux liés aux démarches pour particuliers"""
        links = response.css("a::attr(href)").getall()

        for link in links:
            if not link:
                continue

            url = urljoin(response.url, link)

            # Si le lien contient des mots-clés liés aux démarches ou aux particuliers
            if any(kw in url.lower() for kw in self.keywords):

                # Cas PDF
                if link.endswith(".pdf"):
                    yield scrapy.Request(url, callback=self.save_pdf)

                # Cas page HTML
                elif "servicepublic.gov.bf" in url:
                    yield scrapy.Request(url, callback=self.parse_page)

            # Explore récursivement les autres pages internes (pour trouver des liens cachés)
            elif link.startswith("/") or "servicepublic.gov.bf" in link:
                yield scrapy.Request(url, callback=self.parse)

    def parse_page(self, response):
        """Analyse et enregistre les pages pertinentes"""
        titre = response.css("h1::text, h2::text, title::text").get()
        texte = " ".join(response.css("p::text, li::text, div::text, span::text").getall())
        texte_clean = re.sub(r"\s+", " ", texte.lower())

        # Vérifie si le texte parle de démarches ou de services pour particuliers
        if any(kw in texte_clean for kw in self.keywords):
            os.makedirs("data/pages_particuliers", exist_ok=True)
            file_name = re.sub(r"[^a-zA-Z0-9]", "_", titre or "page")[:60] + ".txt"
            path = os.path.join("data/pages_particuliers", file_name)

            with open(path, "w", encoding="utf-8") as f:
                f.write(texte_clean)

            with open("data/sources_particuliers.txt", "a", encoding="utf-8") as f:
                f.write(response.url + "\n")

            yield {
                "url": response.url,
                "titre": titre.strip() if titre else "Sans titre",
                "contenu": texte_clean,
                "categorie": "particulier",
                "date_scraping": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    def save_pdf(self, response):
        """Télécharge les PDF liés aux démarches des particuliers"""
        os.makedirs("data/pdfs_particuliers", exist_ok=True)
        file_name = os.path.join("data/pdfs_particuliers", os.path.basename(response.url))

        with open(file_name, "wb") as f:
            f.write(response.body)

        self.log(f"📄 PDF particulier téléchargé : {file_name}")

        with open("data/pdf_sources_particuliers.txt", "a", encoding="utf-8") as f:
            f.write(response.url + "\n")
