import os
import requests
from bs4 import BeautifulSoup
import time


# Configuring the Scraper with headers and delay to respect eKLR's robots.txt guidelines
BASE_URL = "http://kenyalaw.org/kl/"
HEADERS = {
    'User-Agent': 'SheriaLens-ResearchBot/1.0 (+mailto:luchanito500@gmail.com)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}
DELAY = 6  # robots.txt allows minimum 5s

# Setting up directories for saving the scraped data
DATA_DIR = "Datasets/Raw_data/"
FOLDERS = {
    "constitution": os.path.join(DATA_DIR, "constitution")
}

for path in FOLDERS.values():
    os.makedirs(path, exist_ok=True)

# Creating a download function that handles errors with the delay in mind
def download_file(url, folder, filename):
    try:
        # Check if file already exists
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
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Could not fetch page {url}: {e}")
        return None


# THE CONSTITUITION SCRAPING FUNCTION
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

# THE ENTRY POINT
if __name__ == "__main__":
    scrape_constitution()
    print("\n Judicial scraper has finished.")
