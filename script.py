from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# ========================================
# CONFIGURATION MANUELLE DES CHEMINS
# ========================================
CHROME_BINARY_PATH = r"E:/Téléchargements/Compressed/chrome-win64/chrome.exe"  # À MODIFIER
CHROMEDRIVER_PATH = r"E:/Téléchargements/Compressed/chromedriver-win64/chromedriver.exe"  # À MODIFIER

HEADLESS = False  # False = voir le navigateur (TEST), True = invisible

# Vérification
for path, name in [(CHROME_BINARY_PATH, "Chrome"), (CHROMEDRIVER_PATH, "ChromeDriver")]:
    if not os.path.exists(path):
        print(f"ERREUR : {name} non trouvé → {path}")
        exit()
    print(f"{name} trouvé : {path}")

# ========================================
# SELENIUM SETUP
# ========================================
options = Options()
options.binary_location = CHROME_BINARY_PATH
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

if HEADLESS:
    options.add_argument('--headless=new')

service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

# ========================================
# SCRAPING
# ========================================
url = "https://www.servicepublic.gov.bf/particuliers/"
all_procedures = []

try:
    print("Chargement de la page principale...")
    driver.get(url)
    time.sleep(4)

    # === ÉTAPE 1 : Ouvrir chaque catégorie principale (collapsible) ===
    headers = driver.find_elements(By.CSS_SELECTOR, ".collapsible-header")
    print(f"{len(headers)} catégories principales trouvées")

    for idx, header in enumerate(headers):
        try:
            # Ré-ouvrir la page principale à chaque fois (évite les bugs Selenium)
            driver.get(url)
            time.sleep(2)
            headers = driver.find_elements(By.CSS_SELECTOR, ".collapsible-header")
            header = headers[idx]

            # Extraire le nom de la catégorie principale
            cat_principale = header.text.strip()
            if not cat_principale:
                cat_principale = f"Catégorie {idx+1}"
            print(f"\n[{idx+1}/{len(headers)}] Catégorie : {cat_principale}")

            # Cliquer pour ouvrir
            driver.execute_script("arguments[0].click();", header)
            time.sleep(2)

            # === ÉTAPE 2 : Récupérer les sous-catégories ===
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            body = soup.select_one(".collapsible-body[style*='display: block']")
            if not body:
                print("   Aucune sous-catégorie ouverte")
                continue

            sub_links = body.select("a.collection-item")
            print(f"   {len(sub_links)} sous-catégories trouvées")

            # === ÉTAPE 3 : Parcourir chaque sous-catégorie ===
            for sub_a in sub_links:
                href = sub_a.get('href')
                title = sub_a.get_text(strip=True)
                if not href or 'retour' in title.lower():
                    continue

                sub_url = str(href) if str(href).startswith('http') else 'https://www.servicepublic.gov.bf' + str(href)
                print(f"     → {title}")

                driver.get(sub_url)
                time.sleep(3)

                page_soup = BeautifulSoup(driver.page_source, 'html.parser')

                # === ÉTAPE 4 : Extraire chaque fiche (<dl>) ===
                cards = page_soup.select(".card")
                for card in cards:
                    title_elem = card.select_one(".card-title")
                    dl = card.select_one("dl")
                    if not dl:
                        continue

                    procedure = {
                        'Catégorie principale': cat_principale,
                        'Sous-catégorie': title,
                        'Titre': title_elem.get_text(strip=True) if title_elem else '',
                        'Description': '',
                        'Pièces à fournir': '',
                        'Coût': '',
                        'Conditions d’accès': '',
                        'Informations complémentaires': '',
                        'Lien externe': ''
                    }

                    # Extraire <dt> / <dd>
                    for dt in dl.select("dt"):
                        key = dt.get_text(strip=True).rstrip(" :")
                        dd = dt.find_next_sibling("dd")
                        value = dd.get_text(strip=True) if dd else ''
                        a_tag = dd.find("a") if dd else None
                        link = a_tag.get('href', '') if a_tag else ''

                        if "Description" in key:
                            procedure['Description'] = value
                        elif "Pièce" in key:
                            procedure['Pièces à fournir'] = value
                        elif "Coût" in key:
                            procedure['Coût'] = value
                        elif "Conditions" in key:
                            procedure['Conditions d’accès'] = value
                        elif "Informations complémentaires" in key:
                            procedure['Informations complémentaires'] = value
                        elif "Adresse web" in key:
                            procedure['Lien externe'] = str(link) if link is not None else ''

                    if procedure['Titre']:
                        all_procedures.append(procedure)
                        print(f"       Fiche extraite : {procedure['Titre'][:50]}...")

        except Exception as e:
            print(f"   Erreur sur catégorie {idx+1} : {e}")
            continue

finally:
    driver.quit()

# ========================================
# SAUVEGARDE
# ========================================
if all_procedures:
    df = pd.DataFrame(all_procedures)
    df.to_csv("procedures_burkina_complet.csv", index=False, encoding="utf-8")
    df.to_excel("procedures_burkina_complet.xlsx", index=False)
    print(f"\nSCRAPING TERMINÉ ! {len(all_procedures)} procédures extraites")
    print("Fichiers : procedures_burkina_complet.csv | .xlsx")
    print("\nAPERÇU :")
    print(df[['Catégorie principale', 'Sous-catégorie', 'Titre', 'Coût']].head(10))
else:
    print("Aucune donnée extraite")