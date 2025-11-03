from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin
import os

# ========================================
# CONFIGURATION MANUELLE
# ========================================
CHROME_BINARY_PATH = r"E:/Téléchargements/Compressed/chrome-win64/chrome.exe"
CHROMEDRIVER_PATH = r"E:/Téléchargements/Compressed/chromedriver-win64/chromedriver.exe"
HEADLESS = False
MAX_DEPTH = 10  # Sécurité anti-boucle

# Vérification des chemins
for path, name in [(CHROME_BINARY_PATH, "Chrome"), (CHROMEDRIVER_PATH, "ChromeDriver")]:
    if not os.path.exists(path):
        print(f"ERREUR : {name} non trouvé → {path}")
        exit()
    print(f"{name} trouvé : {path}")

# ========================================
# OPTIONS CHROME (BYPASS SSL + SÉCURITÉ)
# ========================================
options = Options()
options.binary_location = CHROME_BINARY_PATH

# BYPASS SSL
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('--allow-running-insecure-content')
options.add_argument('--disable-web-security')

# AUTRES
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
if HEADLESS:
    options.add_argument('--headless=new')

service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# ========================================
# DONNÉES
# ========================================
all_procedures = []
visited_urls = set()

# ========================================
# FONCTION : Extraire une fiche
# ========================================
def extract_procedure(card, breadcrumbs):
    title_elem = card.select_one(".card-title")
    dl = card.select_one("dl")
    if not title_elem or not dl:
        return None

    proc = {
        'Chemin complet': " > ".join(breadcrumbs),
        'Titre': title_elem.get_text(strip=True),
        'Description': '', 'Pièces à fournir': '', 'Coût': '',
        'Conditions d’accès': '', 'Informations complémentaires': '', 'Lien externe': ''
    }

    for dt in dl.select("dt"):
        key = dt.get_text(strip=True).rstrip(" :")
        dd = dt.find_next_sibling("dd")
        value = dd.get_text(strip=True) if dd else ''
        link = dd.find("a")['href'] if dd and dd.find("a") else ''

        mapping = {
            "Description": "Description",
            "Pièce": "Pièces à fournir",
            "Coût": "Coût",
            "Conditions": "Conditions d’accès",
            "Informations complémentaires": "Informations complémentaires",
            "Adresse web": "Lien externe"
        }
        for k, field in mapping.items():
            if k in key:
                proc[field] = link if field == "Lien externe" else value

    return proc

# ========================================
# FONCTION RÉCURSIVE : EXPLORER TOUT
# ========================================
def explore_page(url, breadcrumbs=[], depth=0):
    if depth > MAX_DEPTH or url in visited_urls:
        return
    visited_urls.add(url)

    indent = "  " * depth
    print(f"{indent}Exploration : {' > '.join(breadcrumbs)} | {url}")

    try:
        driver.get(url)
        time.sleep(random.uniform(2.0, 3.5))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # === 1. EXTRAIRE LES FICHES (même si on continue) ===
        cards = soup.select(".card")
        extracted = 0
        for card in cards:
            if card.select_one("dl"):
                proc = extract_procedure(card, breadcrumbs)
                if proc:
                    all_procedures.append(proc)
                    extracted += 1
                    print(f"{indent}   Fiche : {proc['Titre'][:60]}...")
        if extracted:
            print(f"{indent}   {extracted} fiche(s) extraite(s)")

        # === 2. CHERCHER LES SOUS-CATÉGORIES (TOUJOURS) ===
        sub_links = []

        # Cas 1 : Accordéon (collapsible)
        for header in soup.select(".collapsible-header"):
            body = header.find_next_sibling(".collapsible-body")
            if body:
                for a in body.select("a.collection-item"):
                    href = a.get('href')
                    text = a.get_text(strip=True)
                    if href and 'retour' not in text.lower():
                        full_url = urljoin("https://www.servicepublic.gov.bf", str(href))
                        sub_links.append((full_url, text))

        # Cas 2 : Liens directs dans .collection
        for a in soup.select("a.collection-item, .collection a"):
            href = a.get('href')
            text = a.get_text(strip=True)
            if href and 'retour' not in text.lower() and str(href).startswith('/particuliers'):
                full_url = urljoin("https://www.servicepublic.gov.bf", str(href))
                sub_links.append((full_url, text))

        # Éviter doublons
        sub_links = list(dict.fromkeys(sub_links))

        if sub_links:
            print(f"{indent}   {len(sub_links)} sous-catégorie(s) trouvée(s)")
            for sub_url, sub_title in sub_links:
                explore_page(sub_url, breadcrumbs + [sub_title], depth + 1)
        else:
            print(f"{indent}   Aucune sous-catégorie")

    except Exception as e:
        print(f"{indent}ERREUR : {e}")

# ========================================
# LANCEMENT
# ========================================
try:
    print("DÉBUT DU SCRAPING EXHAUSTIF (SSL ignoré)")
    start_url = "https://www.servicepublic.gov.bf/particuliers/"
    explore_page(start_url, breadcrumbs=["Particuliers"])

finally:
    driver.quit()

# ========================================
# SAUVEGARDE
# ========================================
if all_procedures:
    df = pd.DataFrame(all_procedures)
    df.to_csv("procedures_burkina_exhaustif.csv", index=False, encoding="utf-8")
    df.to_excel("procedures_burkina_exhaustif.xlsx", index=False)
    print(f"\nSCRAPING TERMINÉ ! {len(all_procedures)} procédures extraites")
    print("Fichiers : procedures_burkina_exhaustif.csv | .xlsx")
    print("\nAPERÇU :")
    print(df[['Chemin complet', 'Titre', 'Coût']].head(10))
else:
    print("Aucune donnée extraite")