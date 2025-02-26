import time
import json
import io
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# PyPDF2 for PDF extraction
import PyPDF2

def setup_driver(headless=True):
    """
    Configures and returns a Selenium WebDriver (Chrome) instance
    with the desired options. Uses webdriver_manager to install
    the correct ChromeDriver version automatically.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_pdf(url):
    """
    Downloads and extracts text from a PDF file given by the URL.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return f"Error fetching PDF: {response.status_code}"
        pdf_bytes = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_bytes)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        print(f"Scraped PDF: {url} ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"Error processing PDF {url}: {e}")
        return f"Error processing PDF: {e}"

def crawl_site_selenium(driver, start_url, max_depth, max_pages, visited=None):
    """
    Recursively crawls from start_url up to max_depth link-hops,
    limiting to max_pages in total, using Selenium to render pages.
    Returns a dict {url: cleaned_text}.
    This function also handles PDF files.
    """
    if visited is None:
        visited = {}

    # If we already visited this URL, skip
    if start_url in visited:
        return visited

    parsed_url = urlparse(start_url)
    # Check if the URL points to a PDF file
    if parsed_url.path.lower().endswith(".pdf"):
        visited[start_url] = scrape_pdf(start_url)
        return visited

    try:
        driver.get(start_url)
        time.sleep(1)  # wait for JavaScript to load
    except Exception as e:
        print(f"Error loading {start_url} with Selenium: {e}")
        visited[start_url] = f"Error scraping: {e}"
        return visited

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Extract visible text
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_text = " ".join(lines)

    visited[start_url] = cleaned_text
    print(f"Scraped (Selenium): {start_url} ({len(cleaned_text)} chars)")

    if max_depth > 0:
        domain = urlparse(start_url).netloc
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            next_url = urljoin(start_url, href)
            # Only follow links within the same domain
            if urlparse(next_url).netloc == domain:
                if len(visited) < max_pages and next_url not in visited:
                    crawl_site_selenium(driver, next_url, max_depth - 1, max_pages, visited)
    return visited

def main():
    """
    Crawls given seed URLs and saves the results in a JSON file in a Weaviate-friendly format.
    Now also supports scraping PDF files.
    """
    driver = setup_driver(headless=True)
    seed_urls = [
        "https://leap-stc.github.io",
        "https://leap.columbia.edu",
        "https://catalog.leap.columbia.edu"
    ]
    all_scraped = {}
    for url in seed_urls:
        crawled_data = crawl_site_selenium(driver, start_url=url, max_depth=1000000, max_pages=1000000, visited=None)
        all_scraped.update(crawled_data)
    driver.quit()

    # Convert the scraped data dictionary to a list of objects in the desired format.
    # Since this crawler handles websites (and PDFs), we use "WebPage" as the class.
    # Unavailable fields are set to empty strings.
    weaviate_objects = []
    for url, text in all_scraped.items():
        obj = {
            "class": "WebPage",
            "title": "",            # Optionally, extract <title> from the HTML if needed
            "videoId": "",          # Not applicable for websites or PDFs
            "url": url,
            "transcript": text      # Use the cleaned text or extracted PDF text as the "transcript" field
        }
        weaviate_objects.append(obj)

    output_filename = "crawl_results.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(weaviate_objects, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved crawl results to '{output_filename}'.")

if __name__ == "__main__":
    main()
