from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import pandas as pd

# --- Configuration ---
url = "http://www.servicepublic.gov.bf/particuliers/"
# options = webdriver.ChromeOptions()
options = webdriver.ChromeOptions()

options.binary_location = 'E:/Téléchargements/Compressed/chrome-win64/chrome.exe'
# options.add_argument('--headless')  # Commentez cette ligne pour voir le navigateur
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

driver = webdriver.Chrome(options=options)
driver.get(url)

# Attente que la page charge
wait = WebDriverWait(driver, 15)
time.sleep(3)  # Sécurité

# --- Étape 1 : Trouver les catégories principales (accordeons ou boutons) ---
# Inspectez la page : les catégories sont probablement dans des <a> ou <button> avec JS
# Exemple : supposons qu'elles soient dans des <h3> ou <a class="category-title">

try:
    # Adaptez ce sélecteur selon la structure réelle
    categories = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='particuliers'], .category-item, .accordion-header,  .blockquote, .card-body, .dl, .dt"))
    )
except:
    print("Aucune catégorie trouvée. Vérifiez les sélecteurs.")
    driver.quit()
    exit()

print(f"Nombre de catégories trouvées : {len(categories)}")

# --- Étape 2 : Parcourir chaque catégorie ---
all_services = []

for i, cat in enumerate(categories):
    try:
        # Recharger la page pour éviter les éléments détachés
        driver.get(url)
        time.sleep(2)
        
        # Ré-attendre les catégories
        categories = driver.find_elements(By.CSS_SELECTOR, "a[href*='particuliers'], .category-item, .accordion-header,  .blockquote, .card-body, .dl, .dt")
        cat = categories[i]
        
        # Extraire le titre de la catégorie
        cat_title = cat.text.strip()
        if not cat_title:
            cat_title = f"Catégorie {i+1}"
        
        print(f"\n[{i+1}/{len(categories)}] Ouverture : {cat_title}")
        
        # Faire défiler jusqu'à l'élément
        driver.execute_script("arguments[0].scrollIntoView(true);", cat)
        time.sleep(1)
        
        # Cliquer sur la catégorie
        driver.execute_script("arguments[0].click();", cat)
        
        # Attendre que les sous-services chargent
        time.sleep(3)
        
        # Extraire le HTML mis à jour
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # --- Adaptez ce sélecteur aux sous-services ---
        # Exemple : les sous-services sont dans <div class="service-item"> ou <li>
        sub_items = soup.select('.service-item, .sub-service, .list-group-item, li a, dt, dl, blockquotes, .card-body')

        for item in sub_items:
            title = item.get_text(strip=True)
            # Récupérer le lien en gérant différents types de balises/attributs
            link = ''
            # Si l'élément est un <a>, prendre son href, sinon chercher un <a> à l'intérieur
            if getattr(item, 'name', None) == 'a':
                link = item.get('href') or ''
            else:
                a_tag = item.find('a')
                link = (a_tag.get('href') if a_tag else '') or ''
            # Si BeautifulSoup a retourné une liste (AttributeValueList), prendre le premier élément
            if isinstance(link, (list, tuple)):
                link = link[0] if link else ''
            # Normaliser les urls relatives
            if link and str(link).startswith('/'):
                link = 'https://www.servicepublic.gov.bf' + link
            elif not link:
                link = 'Pas de lien'
            
            if title and ('service' in title.lower() or 'procédure' in title.lower() or len(title) > 5):
                all_services.append({
                    'Catégorie': cat_title,
                    'Service': title,
                    'Lien': link
                })
                print(f"   → {title}")
    
    except Exception as e:
        print(f"   Erreur sur catégorie {i+1} : {e}")
        continue

# --- Fermer le navigateur ---
driver.quit()

# --- Sauvegarder en CSV ---
df = pd.DataFrame(all_services)
df.to_csv('services_particuliers_burkina.csv', index=False, encoding='utf-8')
print(f"\nScraping terminé ! {len(all_services)} services extraits.")
print("Fichier sauvegardé : services_particuliers_burkina.csv")