# ========================================
# scraper_final_corrige.py
# ========================================
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
from urllib.parse import urljoin
import os
from collections import defaultdict

# ========================================
# 1. CONFIGURATION
# ========================================
CHROME_BINARY_PATH = r"E:/Téléchargements/Compressed/chrome-win64/chrome.exe"
CHROMEDRIVER_PATH = r"E:/Téléchargements/Compressed/chromedriver-win64/chromedriver.exe"
HEADLESS = False

# Vérification
for path, name in [(CHROME_BINARY_PATH, "Chrome"), (CHROMEDRIVER_PATH, "ChromeDriver")]:
    if not os.path.exists(path):
        print(f"ERREUR : {name} non trouvé → {path}")
        exit()
    print(f"{name} trouvé : {path}")

# ========================================
# 2. SELENIUM + SSL BYPASS
# ========================================
options = Options()
options.binary_location = CHROME_BINARY_PATH
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--allow-running-insecure-content')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1720,980')
if HEADLESS:
    options.add_argument('--headless=new')

service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# ========================================
# 3. DONNÉES
# ========================================
all_data = []
visited = set()
hierarchy = defaultdict(list)
MAX_DEPTH = 10

# ========================================
# 4. FONCTION : Extraire fiche
# ========================================
def extract_fiche(card, chemin):
    dl = card.find('dl')
    if not dl:
        return None

    title_elem = card.find_previous(['h4', 'h3', 'h2', '.card-title'])
    titre = title_elem.get_text(strip=True) if title_elem else "Sans titre"

    fiche = {
        'Chemin': " > ".join(chemin),
        'Titre': titre,
        'Description': '',
        'Pièces à fournir': '',
        'Coût': '',
        'Conditions d’accès': '',
        'Informations complémentaires': '',
        'Lien externe': ''
    }

    for dt in dl.find_all('dt'):
        key = dt.get_text(strip=True).rstrip(':').strip()
        dd = dt.find_next_sibling('dd')
        value = dd.get_text(strip=True) if dd else ''
        link = dd.find('a')['href'] if dd and dd.find('a') else ''

        if 'Description' in key: fiche['Description'] = value
        elif 'Pièce' in key: fiche['Pièces à fournir'] = value
        elif 'Coût' in key: fiche['Coût'] = value
        elif 'Conditions' in key: fiche['Conditions d’accès'] = value
        elif 'Informations complémentaires' in key: fiche['Informations complémentaires'] = value
        elif 'Adresse web' in key: fiche['Lien externe'] = link

    return fiche

# ========================================
# 5. FONCTION RÉCURSIVE (SANS TQDM BLOQUANT)
# ========================================
def explore(url, chemin=[], depth=0):
    if depth > MAX_DEPTH or url in visited:
        return
    visited.add(url)

    print(f"\n{'  ' * depth}Exploration : {' > '.join(chemin)} | {url}")

    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # === EXTRAIRE TOUTES LES FICHES (même dans .card) ===
        cards = soup.select('.card')
        extracted = 0
        for card in cards:
            fiche = extract_fiche(card, chemin)
            if fiche:
                all_data.append(fiche)
                hierarchy[" > ".join(chemin)].append(fiche['Titre'])
                extracted += 1
                print(f"{'  ' * depth}   Fiche : {fiche['Titre'][:60]}...")
        if extracted:
            print(f"{'  ' * depth}   {extracted} fiche(s) trouvée(s)")

        # === TROUVER LES SOUS-CATÉGORIES ===
        links = []
        for a in soup.select('a.collection-item'):
            href = a.get('href')
            text = a.get_text(strip=True)
            if href and 'retour' not in text.lower():
                full = urljoin("https://www.servicepublic.gov.bf", href)
                links.append((full, text))

        links = list(dict.fromkeys(links))

        if links:
            print(f"{'  ' * depth}   {len(links)} sous-catégorie(s) → exploration...")
            for sub_url, sub_title in links:
                explore(sub_url, chemin + [sub_title], depth + 1)
        else:
            print(f"{'  ' * depth}   Aucune sous-catégorie")

    except Exception as e:
        print(f"{'  ' * depth}ERREUR : {e}")

# ========================================
# 6. LANCEMENT
# ========================================
try:
    print("DÉBUT DU SCRAPING COMPLET")
    start = "https://www.servicepublic.gov.bf/particuliers/"
    explore(start, ["Particuliers"])

finally:
    driver.quit()

# ========================================
# 7. SAUVEGARDE
# ========================================
if all_data:
    # CSV + Excel
    df = pd.DataFrame(all_data)
    df.to_csv("procedures_burkina.csv", index=False, encoding="utf-8")
    df.to_excel("procedures_burkina.xlsx", index=False)

    # JSON plat
    with open("procedures_burkina.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # JSON hiérarchique
    hier_json = {}
    for path, titles in hierarchy.items():
        parts = path.split(" > ")
        node = hier_json
        for part in parts:
            if part not in node:
                node[part] = {}
            node = node[part]
        node["procédures"] = titles

    with open("procedures_hierarchie.json", "w", encoding="utf-8") as f:
        json.dump(hier_json, f, ensure_ascii=False, indent=2)

    print(f"\nSCRAPING TERMINÉ ! {len(all_data)} fiches extraites")
    print("Fichiers générés :")
    print("  - procedures_burkina.csv")
    print("  - procedures_burkina.xlsx")
    print("  - procedures_burkina.json")
    print("  - procedures_hierarchie.json")

else:
    print("\nAUCUNE FICHE TROUVÉE – Vérifiez le site ou les sélecteurs")