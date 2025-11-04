#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web scraper for collecting administrative documents from Burkinabè government websites.
Sources:
- https://www.servicepublic.gov.bf/
- https://www.gouvernement.gov.bf/
- https://legiburkina.bf/ (PDFs)

This script scrapes documents, cleans the text, removes duplicates, and saves them in a structured JSON format.
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
from datetime import datetime
import pdfplumber
from collections import OrderedDict
from io import BytesIO

# Configuration
BASE_URLS = [
    "https://www.servicepublic.gov.bf/",
    "https://www.gouvernement.gov.bf/",
    # Note: legiburkina.bf will be handled separately for PDFs
]

OUTPUT_DIR = "../data"
CORPUS_FILE = os.path.join(OUTPUT_DIR, "corpus.json")
SOURCES_FILE = os.path.join(OUTPUT_DIR, "sources.txt")

# Headers to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def create_output_dirs():
    """Create output directories if they don't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_valid_url(url):
    """Check if URL is valid and belongs to target domains."""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme) and (
            "servicepublic.gov.bf" in url or 
            "gouvernement.gov.bf" in url or
            "legiburkina.bf" in url
        )
    except:
        return False

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep French accents
    text = re.sub(r'[^\w\s\-\'àâäéèêëïîôöùûüÿçÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ.,;:!?()"\[\]/]', ' ', text)
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_pdf_text(pdf_url):
    """Extract text from PDF using pdfplumber."""
    try:
        response = requests.get(pdf_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        with pdfplumber.open(BytesIO(response.content)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return clean_text(text)
    except Exception as e:
        print(f"Error extracting PDF text from {pdf_url}: {e}")
        return ""

def scrape_servicepublic_page(url):
    """Scrape a page from servicepublic.gov.bf."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1')
        title = clean_text(title_elem.get_text()) if title_elem else "Sans titre"
        
        # Extract content
        content_div = soup.find('div', class_='content') or soup.find('div', class_='fiche-content')
        if not content_div:
            # Try to find any div with content
            content_div = soup.find('div', {'id': 'content'}) or soup.find('div')
        
        content_text = ""
        if content_div:
            # Remove script and style elements
            for script in content_div(["script", "style"]):
                script.decompose()
            content_text = clean_text(content_div.get_text())
        
        # Extract metadata if available
        espace = "Particuliers"  # Default
        theme = "Non spécifié"
        rubrique = "Non spécifié"
        cout = "Non spécifié"
        conditions = "Non spécifié"
        delai = "Non spécifié"
        info_compl = "Non spécifié"
        
        # Try to find metadata in the page
        metadata_sections = soup.find_all(['h2', 'h3', 'dt'])
        for section in metadata_sections:
            section_text = clean_text(section.get_text()).lower()
            next_elem = section.find_next_sibling() or section.find_next()
            
            if next_elem:
                next_text = clean_text(next_elem.get_text())
                
                if 'espace' in section_text:
                    espace = next_text
                elif 'thème' in section_text or 'theme' in section_text:
                    theme = next_text
                elif 'rubrique' in section_text:
                    rubrique = next_text
                elif 'coût' in section_text or 'cout' in section_text:
                    cout = next_text
                elif 'condition' in section_text:
                    conditions = next_text
                elif 'délai' in section_text or 'delai' in section_text:
                    delai = next_text
                elif 'information' in section_text:
                    info_compl = next_text
        
        return {
            "Titre": title,
            "Espace": espace,
            "Thème": theme,
            "Rubrique": rubrique,
            "Description": content_text[:2000],  # Limit description length
            "Coût(s)": cout,
            "Conditions d’accès": conditions,
            "Délai de traitement": delai,
            "Informations complémentaires": info_compl,
            "Adresse web": url
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_gouvernement_page(url):
    """Scrape a page from gouvernement.gov.bf."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1') or soup.find('title')
        title = clean_text(title_elem.get_text()) if title_elem else "Sans titre"
        
        # Extract content
        content_div = soup.find('div', class_='content') or soup.find('article') or soup.find('main')
        if not content_div:
            # Try to find any div with content
            content_div = soup.find('div')
        
        content_text = ""
        if content_div:
            # Remove script and style elements
            for script in content_div(["script", "style"]):
                script.decompose()
            content_text = clean_text(content_div.get_text())
        
        return {
            "Titre": title,
            "Espace": "Particuliers",  # Default
            "Thème": "Non spécifié",
            "Rubrique": "Non spécifié",
            "Description": content_text[:2000],  # Limit description length
            "Coût(s)": "Non spécifié",
            "Conditions d’accès": "Non spécifié",
            "Délai de traitement": "Non spécifié",
            "Informations complémentaires": "Non spécifié",
            "Adresse web": url
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def get_all_links(url, max_pages=100):
    """Get all valid links from a webpage."""
    links = set()
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert href to string to fix type issue
            href_str = str(href)
            full_url = urljoin(url, href_str)
            
            if is_valid_url(full_url) and full_url not in links:
                links.add(full_url)
                
            if len(links) >= max_pages:
                break
                
    except Exception as e:
        print(f"Error getting links from {url}: {e}")
    
    return list(links)

def scrape_website(base_url, max_pages=100):
    """Scrape a website for documents."""
    print(f"Scraping {base_url}...")
    documents = []
    
    # Get all links from the main page
    links = get_all_links(base_url, max_pages)
    
    for i, link in enumerate(links):
        print(f"Processing {i+1}/{len(links)}: {link}")
        
        try:
            if "servicepublic.gov.bf" in link:
                doc = scrape_servicepublic_page(link)
            elif "gouvernement.gov.bf" in link:
                doc = scrape_gouvernement_page(link)
            elif "legiburkina.bf" in link and link.endswith('.pdf'):
                # Handle PDF documents
                pdf_text = extract_pdf_text(link)
                if pdf_text:
                    doc = {
                        "Titre": f"Document PDF - {link.split('/')[-1]}",
                        "Espace": "Particuliers",
                        "Thème": "Non spécifié",
                        "Rubrique": "Non spécifié",
                        "Description": pdf_text[:2000],
                        "Coût(s)": "Non spécifié",
                        "Conditions d’accès": "Non spécifié",
                        "Délai de traitement": "Non spécifié",
                        "Informations complémentaires": "Document PDF extrait de legiburkina.bf",
                        "Adresse web": link
                    }
                else:
                    doc = None
            else:
                doc = None
            
            if doc and doc["Description"].strip():
                documents.append(doc)
            
            # Be respectful - add delay
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing {link}: {e}")
            continue
    
    return documents

def remove_duplicates(documents):
    """Remove duplicate documents based on title and description."""
    unique_docs = OrderedDict()
    
    for doc in documents:
        # Create a key based on title and description
        key = (doc["Titre"], doc["Description"][:100])  # Use first 100 chars for efficiency
        
        if key not in unique_docs:
            unique_docs[key] = doc
    
    return list(unique_docs.values())

def save_corpus(documents):
    """Save documents to corpus.json."""
    with open(CORPUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(documents)} documents to {CORPUS_FILE}")

def save_sources(documents):
    """Save sources to sources.txt."""
    with open(SOURCES_FILE, 'w', encoding='utf-8') as f:
        for doc in documents:
            url = doc.get("Adresse web", "Non spécifié")
            date = datetime.now().strftime("%Y-%m-%d")
            if "servicepublic.gov.bf" in url:
                source = "ServicePublic.gov.bf"
            elif "gouvernement.gov.bf" in url:
                source = "Gouvernement.gov.bf"
            elif "legiburkina.bf" in url:
                source = "Legiburkina.bf"
            else:
                source = "Site gouvernemental"
            f.write(f"{url} | {date} | Domaine public (site gouvernemental) | {source}\n")
    print(f"Saved sources to {SOURCES_FILE}")

def main():
    """Main function to scrape websites and collect documents."""
    create_output_dirs()
    
    all_documents = []
    
    # Scrape each website
    for base_url in BASE_URLS:
        try:
            documents = scrape_website(base_url, max_pages=100)
            all_documents.extend(documents)
            print(f"Found {len(documents)} documents from {base_url}")
        except Exception as e:
            print(f"Error scraping {base_url}: {e}")
    
    # Also scrape legiburkina.bf for PDFs
    try:
        pdf_documents = scrape_website("https://legiburkina.bf/", max_pages=50)
        all_documents.extend(pdf_documents)
        print(f"Found {len(pdf_documents)} PDF documents from legiburkina.bf")
    except Exception as e:
        print(f"Error scraping legiburkina.bf: {e}")
    
    # Remove duplicates
    unique_documents = remove_duplicates(all_documents)
    print(f"Total unique documents: {len(unique_documents)}")
    
    # Save to files
    if unique_documents:
        save_corpus(unique_documents)
        save_sources(unique_documents)
        print("Scraping completed successfully!")
    else:
        print("No documents found.")

if __name__ == "__main__":
    main()