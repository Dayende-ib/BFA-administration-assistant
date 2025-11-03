# ========================================
# scraper_verbose_full.py
# Extraction complète et verbeuse du site servicepublic.gov.bf
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
# 1. CONFIGURATION MANUELLE
# ========================================
CHROME_BINARY_PATH = r"E:/Téléchargements/Compressed/chrome-win64/chrome.exe"
CHROMEDRIVER_PATH = r"E:/Téléchargements/Compressed/chromedriver-win64/chromedriver.exe"
HEADLESS = False  # Mettez True pour cacher le navigateur

print("DÉMARRAGE DU SCRAPER VERBEUX")
print(f"Heure : {datetime.now().strftime('%H:%M:%S')}")
print(f"Chrome : {CHROME_BINARY_PATH}")
print(f"ChromeDriver : {CHROMEDRIVER_PATH}")

# Vérification des fichiers
for path, name in [(CHROME_BINARY_PATH, "Chrome"), (CHROMEDRIVER_PATH, "ChromeDriver")]:
    if not os.path.exists(path):
        print(f"ERREUR : {name} introuvable → {path}")
        exit()
    print(f"{name} trouvé")

# ========================================
# 2. CONFIGURATION SELENIUM + SSL BYPASS
# ========================================
print("\nConfiguration de Chrome avec bypass SSL...")
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
print("Navigateur lancé avec succès")

# ========================================
# 3. DONNÉES
# ========================================
all_pages = []        # Stocke chaque page visitée
visited_urls = set()  # Évite les doublons
MAX_DEPTH = 15
START_URL = "https://www.servicepublic.gov.bf/particuliers/"

# ========================================
# 4. FONCTION : Extraire TOUT le texte d'une page
# ========================================
def extract_all_text(soup, url, chemin):
    print(f"\nEXTRACTION DE TOUT LE TEXTE DE LA PAGE...")
    print(f"URL : {url}")
    print(f"Chemin : {' > '.join(chemin)}")

    data = {
        "url": url,
        "chemin": " > ".join(chemin),
        "timestamp": datetime.now().isoformat(),
        "titres": [],
        "paragraphes": [],
        "listes": [],
        "definitions": {},  # dt → dd
        "autres_textes": []
    }

    # === 1. Tous les titres (h1 à h6) ===
    print("Recherche des titres (h1 à h6)...")
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text(strip=True)
        if text:
            data["titres"].append(text)
            print(f"   Titre ({tag.name}) : {text[:80]}...")

    # === 2. Paragraphes, b, small, p ===
    print("Recherche des paragraphes et textes en gras...")
    for tag in soup.find_all(['p', 'b', 'strong', 'small', 'span']):
        text = tag.get_text(strip=True)
        if text and len(text) > 5:
            data["paragraphes"].append(text)
            print(f"   Texte ({tag.name}) : {text[:100]}...")

    # === 3. Listes (ul, ol, li) ===
    print("Recherche des listes...")
    for ul in soup.find_all(['ul', 'ol']):
        items = [li.get_text(strip=True) for li in ul.find_all('li') if li.get_text(strip=True)]
        if items:
            data["listes"].extend(items)
            for item in items:
                print(f"   Liste : {item[:80]}...")

    # === 4. Définitions <dl>, <dt>, <dd> ===
    print("Recherche des définitions (dl/dt/dd)...")
    for dl in soup.find_all('dl'):
        current_dt = None
        for child in dl.children:
            if child.name == 'dt':
                current_dt = child.get_text(strip=True)
                print(f"   DT : {current_dt}")
            elif child.name == 'dd' and current_dt:
                dd_text = child.get_text(strip=True)
                data["definitions"][current_dt] = dd_text
                print(f"   DD : {dd_text[:100]}...")

    # === 5. Tout le reste (texte brut) ===
    print("Extraction du texte brut restant...")
    body = soup.find('body')
    if body:
        full_text = body.get_text(separator=' ', strip=True)
        # Nettoyer les doublons
        clean_text = ' '.join(full_text.split())
        if len(clean_text) > 200:
            data["autres_textes"].append(clean_text[:500] + "...")
            print(f"   Texte brut (500 premiers caractères) : {clean_text[:500]}...")

    print(f"EXTRACTION TERMINÉE → {len(data['titres'])} titres, {len(data['paragraphes'])} paragraphes, {len(data['definitions'])} définitions")
    return data

# ========================================
# 5. FONCTION : Trouver tous les liens de navigation
# ========================================
def get_navigation_links(soup, base_url):
    print("Recherche des liens de navigation...")
    links = []
    # Tous les <a> dans les menus, collections, collapsible
    selectors = [
        'a.collection-item',
        '.collapsible-body a',
        'a[href^="/particuliers"]',
        'nav a.breadcrumb'
    ]
    for sel in selectors:
        for a in soup.select(sel):
            href = a.get('href')
            text = a.get_text(strip=True)
            if href and text and 'retour' not in text.lower() and 'accueil' not in text.lower():
                full_url = urljoin(base_url, href)
                if full_url not in visited_urls:
                    links.append((full_url, text))
                    print(f"   Lien trouvé : {text} → {full_url}")
    links = list(dict.fromkeys(links))  # Supprimer doublons
    print(f"{len(links)} lien(s) unique(s) à explorer")
    return links

# ========================================
# 6. FONCTION RÉCURSIVE : Explorer
# ========================================
def explore_page(url, chemin=[], depth=0):
    if depth > MAX_DEPTH or url in visited_urls:
        return
    visited_urls.add(url)

    indent = "  " * depth
    print(f"\n{indent}{'='*60}")
    print(f"{indent}OUVERTURE DE LA PAGE (profondeur {depth})")
    print(f"{indent}URL : {url}")
    print(f"{indent}Chemin : {' > '.join(chemin)}")
    print(f"{indent}Pages déjà visitées : {len(visited_urls)}")
    print(f"{indent}Fiches extraites : {len(all_pages)}")

    try:
        print(f"{indent}Chargement de la page...")
        driver.get(url)
        time.sleep(random.uniform(3, 5))  # Respect du serveur

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # === EXTRAIRE TOUT LE TEXTE ===
        page_data = extract_all_text(soup, url, chemin)
        all_pages.append(page_data)

        # === TROUVER LES NOUVEAUX LIENS ===
        new_links = get_navigation_links(soup, url)

        # === EXPLORER LES SOUS-PAGES ===
        if new_links:
            print(f"{indent}Exploration des {len(new_links)} sous-pages...")
            for sub_url, sub_title in new_links:
                explore_page(sub_url, chemin + [sub_title], depth + 1)
        else:
            print(f"{indent}Aucun nouveau lien → fin de cette branche")

    except Exception as e:
        print(f"{indent}ERREUR lors du chargement : {e}")

# ========================================
# 7. LANCEMENT
# ========================================
try:
    print("\nLANCEMENT DU SCRAPING COMPLET")
    print(f"Page de départ : {START_URL}")
    explore_page(START_URL, ["Accueil", "Particuliers"])

finally:
    print("\nFERMETURE DU NAVIGATEUR...")
    driver.quit()

# ========================================
# 8. SAUVEGARDE
# ========================================
print(f"\nSAUVEGARDE DES DONNÉES...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# JSON complet
with open(f"extraction_complete_{timestamp}.json", "w", encoding="utf-8") as f:
    json.dump(all_pages, f, ensure_ascii=False, indent=2)
print(f"JSON sauvegardé : extraction_complete_{timestamp}.json")

# CSV simplifié (titres + définitions)
rows = []
for page in all_pages:
    for dt, dd in page["definitions"].items():
        rows.append({
            "Chemin": page["chemin"],
            "Question": dt,
            "Réponse": dd
        })

with open(f"procedures_qr_{timestamp}.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["Chemin", "Question", "Réponse"])
    writer.writeheader()
    writer.writerows(rows)
print(f"CSV Q&R : procedures_qr_{timestamp}.csv")

print(f"\nSCRAPING TERMINÉ !")
print(f"Pages visitées : {len(visited_urls)}")
print(f"Fiches extraites : {len(all_pages)}")
print(f"Questions/Réponses : {len(rows)}")