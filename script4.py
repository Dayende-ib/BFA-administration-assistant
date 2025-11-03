# ========================================
# scraper_breadcrumb_final.py
# Suivi du fil d'Ariane + extraction complète
# ========================================
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import csv
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

print("SCRAPER AVEC BREADCRUMB ACTIF")
print(f"Heure : {datetime.now().strftime('%H:%M:%S')}")

# Vérification
for path, name in [(CHROME_BINARY_PATH, "Chrome"), (CHROMEDRIVER_PATH, "ChromeDriver")]:
    if not os.path.exists(path):
        print(f"ERREUR : {name} introuvable → {path}")
        exit()
    print(f"{name} trouvé")

# ========================================
# 2. SELENIUM + SSL BYPASS
# ========================================
print("\nLancement de Chrome...")
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
print("Navigateur prêt")

# ========================================
# 3. DONNÉES
# ========================================
all_pages = []
visited_urls = set()
MAX_DEPTH = 15
START_URL = "https://www.servicepublic.gov.bf/particuliers/"

# ========================================
# 4. FONCTION : Extraire le breadcrumb
# ========================================
def get_breadcrumb(soup):
    print("Lecture du fil d'Ariane...")
    breadcrumb = []
    nav = soup.select_one("nav.crumbread")
    if not nav:
        print("Aucun breadcrumb trouvé")
        return ["Particuliers"]

    for a in nav.select("a.breadcrumb"):
        text = a.get_text(strip=True)
        if text and text.lower() not in ["service public", "accueil"]:
            breadcrumb.append(text)
            print(f"   Étape : {text}")

    if not breadcrumb:
        breadcrumb = ["Particuliers"]
    print(f"Chemin breadcrumb : {' > '.join(breadcrumb)}")
    return breadcrumb

# ========================================
# 5. FONCTION : Extraire tout le texte
# ========================================
def extract_all_text(soup, url, breadcrumb):
    print(f"\nEXTRACTION DU CONTENU DE LA PAGE...")
    print(f"URL : {url}")
    print(f"Chemin : {' > '.join(breadcrumb)}")

    data = {
        "url": url,
        "breadcrumb": " > ".join(breadcrumb),
        "timestamp": datetime.now().isoformat(),
        "titres": [],
        "paragraphes": [],
        "listes": [],
        "definitions": {},
        "autres_textes": []
    }

    # === Titres ===
    print("Titres (h1-h6)...")
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text(strip=True)
        if text:
            data["titres"].append(text)
            print(f"   {tag.name.upper()} : {text[:100]}...")

    # === Paragraphes, gras, etc. ===
    print("Paragraphes et textes...")
    for tag in soup.find_all(['p', 'b', 'strong', 'small', 'span']):
        text = tag.get_text(strip=True)
        if text and len(text) > 10:
            data["paragraphes"].append(text)
            print(f"   <{tag.name}> : {text[:120]}...")

    # === Listes ===
    print("Listes...")
    for ul in soup.find_all(['ul', 'ol']):
        items = [li.get_text(strip=True) for li in ul.find_all('li') if li.get_text(strip=True)]
        if items:
            data["listes"].extend(items)
            for item in items[:3]:
                print(f"   • {item[:100]}...")

    # === Définitions <dl> ===
    print("Définitions (dt/dd)...")
    for dl in soup.find_all('dl'):
        current_dt = None
        for child in dl.children:
            if child.name == 'dt':
                current_dt = child.get_text(strip=True).rstrip(":").strip()
                print(f"   Question : {current_dt}")
            elif child.name == 'dd' and current_dt:
                dd_text = child.get_text(strip=True)
                data["definitions"][current_dt] = dd_text
                print(f"   Réponse : {dd_text[:120]}...")

    # === Texte brut ===
    print("Texte brut global...")
    body = soup.find('body')
    if body:
        full = ' '.join(body.get_text(separator=' ', strip=True).split())
        if len(full) > 300:
            data["autres_textes"].append(full[:500] + "...")
            print(f"   Extrait : {full[:500]}...")

    print(f"EXTRAIT : {len(data['titres'])} titres | {len(data['definitions'])} Q&R")
    return data

# ========================================
# 6. FONCTION : Trouver les liens suivants
# ========================================
def get_next_links(soup, current_url):
    print("Recherche des liens de navigation...")
    links = []
    selectors = [
        'a.collection-item',
        '.collapsible-body a',
        'a[href^="/particuliers"]'
    ]
    for sel in selectors:
        for a in soup.select(sel):
            href = a.get('href')
            text = a.get_text(strip=True)
            if href and text and 'retour' not in text.lower() and 'accueil' not in text.lower():
                full = urljoin(current_url, href)
                if full not in visited_urls:
                    links.append((full, text))
                    print(f"   Lien : {text} → {full}")

    links = list(dict.fromkeys(links))
    print(f"{len(links)} lien(s) à explorer")
    return links

# ========================================
# 7. FONCTION RÉCURSIVE
# ========================================
def explore_page(url, depth=0):
    if depth > MAX_DEPTH or url in visited_urls:
        return
    visited_urls.add(url)

    indent = "  " * depth
    print(f"\n{indent}{'='*70}")
    print(f"{indent}PAGE {depth} | URL : {url}")
    print(f"{indent}Profondeur : {depth} | Visitées : {len(visited_urls)}")

    try:
        print(f"{indent}Chargement...")
        driver.get(url)
        time.sleep(random.uniform(3, 5))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # === BREADCRUMB ===
        breadcrumb = get_breadcrumb(soup)

        # === EXTRACTION ===
        page_data = extract_all_text(soup, url, breadcrumb)
        all_pages.append(page_data)

        # === LIENS SUIVANTS ===
        next_links = get_next_links(soup, url)

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
# 8. LANCEMENT
# ========================================
try:
    print("\nDÉBUT DU SCRAPING AVEC BREADCRUMB")
    explore_page(START_URL)

finally:
    print("\nFERMETURE DU NAVIGATEUR")
    driver.quit()

# ========================================
# 9. SAUVEGARDE
# ========================================
print(f"\nSAUVEGARDE...")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# JSON
with open(f"data_breadcrumb_{ts}.json", "w", encoding="utf-8") as f:
    json.dump(all_pages, f, ensure_ascii=False, indent=2)
print(f"JSON : data_breadcrumb_{ts}.json")

# CSV Q&R
rows = []
for page in all_pages:
    for q, r in page["definitions"].items():
        rows.append({
            "Chemin": page["breadcrumb"],
            "Question": q,
            "Réponse": r
        })

with open(f"qa_breadcrumb_{ts}.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["Chemin", "Question", "Réponse"])
    writer.writeheader()
    writer.writerows(rows)
print(f"CSV : qa_breadcrumb_{ts}.csv")

print(f"\nFIN ! {len(all_pages)} pages | {len(rows)} Q&R")