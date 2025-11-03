# ========================================
# scraper_exhaustif_final.py
# Ne saute AUCUN lien + ouvre tous les menus
# ========================================
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
from urllib.parse import urljoin
import os
from datetime import datetime

# ========================================
# 1. CONFIGURATION
# ========================================
CHROME_BINARY_PATH = r"E:/Téléchargements/Compressed/chrome-win64/chrome.exe"
CHROMEDRIVER_PATH = r"E:/Téléchargements/Compressed/chromedriver-win64/chromedriver.exe"
HEADLESS = False
WAIT_TIMEOUT = 10

print("SCRAPER EXHAUSTIF – AUCUN LIEN MANQUÉ")
print(f"Démarrage : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# Vérification
for path, name in [(CHROME_BINARY_PATH, "Chrome"), (CHROMEDRIVER_PATH, "ChromeDriver")]:
    if not os.path.exists(path):
        print(f"ERREUR : {name} manquant → {path}")
        exit()
    print(f"{name} trouvé")

# ========================================
# 2. SELENIUM + SSL + WAIT
# ========================================
print("\nLancement du navigateur...")
options = Options()
options.binary_location = CHROME_BINARY_PATH
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--allow-running-insecure-content')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
if HEADLESS:
    options.add_argument('--headless=new')

service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, WAIT_TIMEOUT)
print("Navigateur prêt")

# ========================================
# 3. DONNÉES
# ========================================
all_fiches = []
visited_urls = set()
MAX_DEPTH = 15
START_URL = "https://www.servicepublic.gov.bf/particuliers/"

# ========================================
# 4. FONCTION : Ouvrir tous les accordéons
# ========================================
def open_all_accordions():
    print("Ouverture de TOUS les menus (collapsible)...")
    headers = driver.find_elements(By.CSS_SELECTOR, ".collapsible-header")
    print(f"{len(headers)} menus trouvés")
    for i, header in enumerate(headers):
        try:
            if "active" not in header.get_attribute("class"):
                driver.execute_script("arguments[0].scrollIntoView(true);", header)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", header)
                print(f"   Menu ouvert : {header.text.strip()[:60]}...")
                time.sleep(1)
        except Exception as e:
            print(f"   Erreur ouverture menu {i} : {e}")
    time.sleep(2)

# ========================================
# 5. FONCTION : Lire le breadcrumb
# ========================================
def get_breadcrumb():
    print("Lecture du fil d'Ariane...")
    try:
        nav = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "nav.crumbread")))
        breadcrumb = []
        for a in nav.find_elements(By.CSS_SELECTOR, "a.breadcrumb"):
            text = a.text.strip()
            if text and text.lower() not in ["service public", "accueil", "particuliers"]:
                breadcrumb.append(text)
                print(f"   Étape : {text}")
        if not breadcrumb:
            breadcrumb = ["Particuliers"]
        print(f"Chemin : {' > '.join(breadcrumb)}")
        return breadcrumb
    except:
        print("Breadcrumb non trouvé")
        return ["Particuliers"]

# ========================================
# 6. FONCTION : Extraire une fiche
# ========================================
def extract_fiche(card_body, breadcrumb):
    soup_cb = BeautifulSoup(card_body.get_attribute('outerHTML'), 'html.parser')
    dl = soup_cb.find('dl')
    if not dl:
        return None

    title_elem = card_body.find_element(By.XPATH, ".//preceding::h4 | .//preceding::h3 | .//preceding::.card-title")
    titre = title_elem.text.strip() if title_elem else "Sans titre"
    print(f"\nFICHE : {titre}")

    fiche = {
        "Chemin": " > ".join(breadcrumb),
        "Titre": titre,
        "Description": "", "Pièces à fournir": "", "Coût": "",
        "Conditions d’accès": "", "Informations complémentaires": "", "Lien externe": ""
    }

    for dt in dl.find_all('dt'):
        key = dt.get_text(strip=True).rstrip(" :").strip()
        dd = dt.find_next_sibling('dd')
        value = dd.get_text(strip=True) if dd else ""
        link = dd.find('a')['href'] if dd and dd.find('a') else ""

        print(f"   {key} → {value[:100]}{'...' if len(value)>100 else ''}")
        if link: print(f"   Lien : {link}")

        if "Description" in key: fiche["Description"] = value
        elif "Pièce" in key: fiche["Pièces à fournir"] = value
        elif "Coût" in key: fiche["Coût"] = value
        elif "Conditions" in key: fiche["Conditions d’accès"] = value
        elif "Informations complémentaires" in key: fiche["Informations complémentaires"] = value
        elif "Adresse web" in key: fiche["Lien externe"] = link

    return fiche

# ========================================
# 7. FONCTION : Trouver TOUS les liens
# ========================================
def get_all_links():
    print("Recherche de TOUS les liens de navigation...")
    links = []
    selectors = [
        "a.collection-item",
        ".collapsible-body a",
        "a[href^='/particuliers']",
        "blockquote a",
        ".section a",
        "a[href*='fiches']"
    ]
    seen = set()

    for sel in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, sel)
        for el in elements:
            href = el.get_attribute('href')
            text = el.text.strip()
            if href and text and 'retour' not in text.lower() and href not in seen:
                full = urljoin(driver.current_url, href)
                if full not in visited_urls:
                    links.append((full, text))
                    seen.add(href)
                    print(f"   Lien : {text} → {full}")

    links = list(dict.fromkeys(links))
    print(f"{len(links)} lien(s) unique(s) à explorer")
    return links

# ========================================
# 8. FONCTION RÉCURSIVE
# ========================================
def explore_page(url, depth=0):
    if depth > MAX_DEPTH or url in visited_urls:
        return
    visited_urls.add(url)

    indent = "  " * depth
    print(f"\n{indent}{'='*90}")
    print(f"{indent}PAGE {depth} | URL : {url}")
    print(f"{indent}Pages visitées : {len(visited_urls)} | Fiches : {len(all_fiches)}")

    try:
        print(f"{indent}Chargement...")
        driver.get(url)
        time.sleep(random.uniform(3, 5))

        # === OUVRIR TOUS LES MENUS ===
        open_all_accordions()

        # === BREADCRUMB ===
        breadcrumb = get_breadcrumb()

        # === EXTRAIRE FICHES ===
        card_bodies = driver.find_elements(By.CSS_SELECTOR, ".card-body")
        print(f"{len(card_bodies)} bloc(s) .card-body")
        for cb in card_bodies:
            fiche = extract_fiche(cb, breadcrumb)
            if fiche:
                all_fiches.append(fiche)

        # === TOUS LES LIENS ===
        next_links = get_all_links()

        # === EXPLORER ===
        if next_links:
            print(f"{indent}Exploration de {len(next_links)} sous-pages...")
            for sub_url, sub_title in next_links:
                explore_page(sub_url, depth + 1)
        else:
            print(f"{indent}Fin de la branche")

    except Exception as e:
        print(f"{indent}ERREUR : {e}")

# ========================================
# 9. LANCEMENT
# ========================================
try:
    print("\nDÉBUT DU SCRAPING EXHAUSTIF")
    explore_page(START_URL)

finally:
    print("\nFERMETURE")
    driver.quit()

# ========================================
# 10. SAUVEGARDE
# ========================================
print(f"\nSAUVEGARDE...")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
df = pd.DataFrame(all_fiches)
df.to_csv(f"fiches_completes_{ts}.csv", index=False, encoding="utf-8")
df.to_excel(f"fiches_completes_{ts}.xlsx", index=False)
with open(f"fiches_completes_{ts}.json", "w", encoding="utf-8") as f:
    json.dump(all_fiches, f, ensure_ascii=False, indent=2)

print(f"TERMINÉ ! {len(all_fiches)} fiches | {len(visited_urls)} pages")
print(f"Fichiers : fiches_completes_{ts}.*")