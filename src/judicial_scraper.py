import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuring the Scraper with headers and delay to respect eKLR's robots.txt guidelines
BASE_URL = "https://kenyalaw.org/kl/"
HEADERS = {
    'User-Agent': 'SheriaLens-ResearchBot/1.0 (+mailto:luchanito500@gmail.com)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}
DELAY = 6  # 6 seconds delay to be extra cautious (robots.txt allows 5s)

# Setting up directories for saving the scraped data
DATA_DIR = "Datasets/Raw_data/"
FOLDERS = {
    "constitution": os.path.join(DATA_DIR, "constitution"),
    "counties": os.path.join(DATA_DIR, "county_laws"),
    "treaties": os.path.join(DATA_DIR, "treaties"),
}

for path in FOLDERS.values():
    os.makedirs(path, exist_ok=True)

# Creating a download function that handles errors and respects the delay
def download_file(url, folder, filename):
    try:
        # Check if file already exists to save bandwidth
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            print(f"   [SKIP] {filename} already exists.")
            return

        print(f"   [DOWNLOADING] {filename}...")
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"   [SUCCESS] Saved to {folder}")
        time.sleep(DELAY) 
        
    except Exception as e:
        print(f"   [ERROR] Failed to download {filename}: {e}")

# Function to fetch a page and return a BeautifulSoup object
def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"[ERROR] Could not fetch page {url}: {e}")
        return None


# THE MAIN SCRAPING FUNCTIONS
def scrape_constitution():
    print("\n STARTING THE DOWNLOAD OF THE CONSTITUTION OF KENYA 2010...")
    target_url = "http://kenyalaw.org/kl/index.php?id=398"
    soup = get_soup(target_url)
    
    if soup:
        # Find PDF links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if "Constitution" in link.text and ".pdf" in href:
                filename = "TheConstitutionOfKenya.pdf"
                download_file(href, FOLDERS["constitution"], filename)
                break 

def scrape_county_laws():
    print("\n STARTING THE DOWNLOAD OF COUNTY LAWS")
    index_url = "http://new.kenyalaw.org/legislation/counties/"
    soup = get_soup(index_url)
    
    if not soup: return

    # Finding all County Links
    county_links = []
    content_div = soup.find('div', {'class': 'content'}) # Generic class, might need adjustment
    
    # Fallback to a specific text search if class names change
    for a in soup.find_all('a', href=True):
        if "id=countylaws" in a['href'] and "&c=" in a['href']: # Standard pattern for county sub-pages
            county_name = a.text.strip()
            full_url = urljoin(BASE_URL, a['href'])
            county_links.append((county_name, full_url))
    
    print(f"Found {len(county_links)} Counties. Starting Extraction...")

    # Iterating through each county to download their respective PDF Acts
    for name, url in county_links:
        print(f"\n Currently Processing County: {name}")
        
        # Creating county-specific folder
        county_folder = os.path.join(FOLDERS["counties"], name.replace(" ", "_").lower())
        os.makedirs(county_folder, exist_ok=True)
        
        # Getting the County Page soup
        c_soup = get_soup(url)
        time.sleep(DELAY) 
        
        if c_soup:
            # Find PDF Acts on the County Page
            pdf_count = 0
            for link in c_soup.find_all('a', href=True):
                href = link['href']
                text = link.text.strip()
                
                # Checking if it's a PDF and looks like a Law/Act
                if href.lower().endswith('.pdf'):
                    # Cleaning filename to avoid issues with special characters and length
                    safe_filename = text.replace("/", "-").replace(" ", "_")[:50] + ".pdf"
                    download_file(href, county_folder, safe_filename)
                    pdf_count += 1
            
            if pdf_count == 0:
                print("   [INFO] No PDFs found on this page.")

# THE ENTRY POINT
if __name__ == "__main__":
    print("SheriaLens Legislation Scraper has started...")
    print(f"Currently enforcing {DELAY} seconds delay for each request.")
    
    scrape_constitution()
    scrape_county_laws()
    
    
    print("\n Judicial scraper has finished.")
