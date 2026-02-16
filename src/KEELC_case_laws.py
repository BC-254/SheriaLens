import os
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuring the scraper
START_URL = "https://new.kenyalaw.org/judgments/KEELC/2025/1/"
BASE_URL = "https://new.kenyalaw.org"
DELAY_SECONDS = 6  # Conforming with robots.txt
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Directory for each month's case laws
DOWNLOAD_FOLDER = "Datasets/Raw_data/case_laws/2025/January"
DOWNLOAD_DELAY = 3
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def KEELC_Case_laws():
    driver = setup_driver()
    current_url = START_URL
    current_page_number = 1
    all_pdf_links = []

    while True:
        print(f"\n Scraping Page: {current_page_number} ")
        driver.get(current_url)
        time.sleep(3)  # Allowing time for JS to load
        
        try:
            WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "td.cell-title a"))
                )
        except Exception as e:
            print(f"Page took too long to load or structure changed: {e}")
            
        # Getting the HTML since JS has rendered the content
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Getting all the links on current page
        found_on_page = 0
        rows = soup.find_all('tr')
        
        for row in rows:
            title_cell = row.select_one('td.cell-title')
            if title_cell:
                link_tag = title_cell.find('a')
                if link_tag and link_tag.get('href'):
                    raw_href = link_tag.get('href')
                    
                    # Making the link absolute
                    full_link = urljoin(BASE_URL, raw_href)
                    all_pdf_links.append(full_link)
                    found_on_page += 1
        print(f"Found {found_on_page} items on this page.")

        # Getting links in the next page
        next_page = current_page_number + 1
        # Targeting class "page-link" with text of the next page number
        next_link_tag = soup.find('a', class_='page-link', string=str(next_page))
        # Incase strict find fails
        if not next_link_tag:
            for a_tag in soup.find_all('a', class_='page-link'):
                if a_tag.get_text(strip=True) == str(next_page):
                    next_link_tag = a_tag
                    break
        # If it contains the next page number in its text
        if not next_link_tag:
            for a_tag in soup.find_all('a', class_='page-link'):
                if str(next_page) in a_tag.get_text(strip=True):
                    next_link_tag = a_tag
                    break
        # Incase it contains the word "Next" 
        if not next_link_tag:
                for a_tag in soup.find_all('a', class_='page-link'):
                    if "next" in a_tag.get_text(strip=True).lower():
                        next_link_tag = a_tag
                        break
           
        # Updating the url and looping again
        if next_link_tag and next_link_tag.get('href'):
            next_href = next_link_tag.get('href')
            current_url = urljoin(current_url, next_href)
    
            print(f"Page({next_page}) found. Waiting {DELAY_SECONDS}s...")
            time.sleep(DELAY_SECONDS)
            current_page_number += 1
        else:
            print("No next page link found. Scraper finished.")
            break 
    
    return all_pdf_links


def download_cases(all_links):
    print(f"\n Starting Download of {len(all_links)} case laws")
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
        print(f"Created directory: {DOWNLOAD_FOLDER}")
    for index, base_link in enumerate(all_links, 1):
        try:
            download_url = base_link.rstrip('/')  + "/source"
            parsed_url = urlparse(download_url)
            path_parts = parsed_url.path.split('/') 
            filename_part = "_".join([p for p in path_parts if p.isdigit() or 'keelc' in p.lower()]) 
            
            # Incase URL structure is weird
            if not filename_part:
                filename_part = f"document_{index}"
            
            filename = f"{filename_part}.pdf"
            save_path = os.path.join(DOWNLOAD_FOLDER, filename)

            # Skipping duplicates
            if os.path.exists(save_path):
                print(f"   [SKIP] {filename} already exists.")
                continue

            # Downloading the files
            print(f"[{index}/{len(all_links)}] Downloading {filename}")
            
            # Streaming to handle large files
            with requests.get(download_url, headers=HEADERS, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)

            time.sleep(DOWNLOAD_DELAY)  # Delay between downloads
        except Exception as e:
            print(f"   [ERROR] Failed to download {filename}: {e}")


if __name__ == "__main__":
    all_links = KEELC_Case_laws()
    print(f"Found {len(all_links)} links.")
    download_cases(all_links)
    