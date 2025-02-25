import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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

def crawl_site_selenium(driver, start_url, max_depth, max_pages, visited=None):
    """
    Recursively crawls from start_url up to max_depth link-hops,
    limiting to max_pages in total, using Selenium to render pages.
    Returns a dict {url: cleaned_text}.

    :param driver: Selenium WebDriver instance
    :param start_url: The initial URL to crawl from
    :param max_depth: Maximum depth of link-following
    :param max_pages: Maximum number of distinct pages to crawl
    :param visited: A dict of {url: text} to track visited pages
    :return: Updated visited dict containing page text
    """
    if visited is None:
        visited = {}

    # If we already visited this URL, skip
    if start_url in visited:
        return visited

    try:
        # Load page in Selenium to execute JavaScript
        driver.get(start_url)
        # Optional wait for JavaScript content to load
        time.sleep(1)  # Adjust as needed for slower sites
    except Exception as e:
        print(f"Error loading {start_url} with Selenium: {e}")
        visited[start_url] = f"Error scraping: {e}"
        return visited

    # Get the final rendered HTML after JS execution
    page_source = driver.page_source

    # Parse with BeautifulSoup
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

    # Follow links if we still have depth left
    if max_depth > 0:
        domain = urlparse(start_url).netloc  # e.g., "example.com"
        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"]
            next_url = urljoin(start_url, href)

            # Only follow links on the same domain (optional check)
            if urlparse(next_url).netloc == domain:
                # Respect max_pages limit
                if len(visited) < max_pages and next_url not in visited:
                    crawl_site_selenium(
                        driver,
                        next_url,
                        max_depth - 1,
                        max_pages,
                        visited
                    )

    return visited

def main():
    """
    Example usage of the Selenium-based crawler.
    """
    # Initialize a headless Chrome browser
    driver = setup_driver(headless=True)

    # URLs to start crawling from
    seed_urls = [
        "https://leap-stc.github.io",  # Example 1
        "https://leap.columbia.edu",   # Example 2
        "https://catalog.leap.columbia.edu"  # Example 3
    ]

    all_scraped = {}
    for url in seed_urls:
        # Start crawling each seed URL
        crawled_data = crawl_site_selenium(
            driver=driver,
            start_url=url,
            max_depth=1000,
            max_pages=1000,
            visited=None
        )
        # Merge results into a single dictionary
        all_scraped.update(crawled_data)

    # Clean up Selenium
    driver.quit()

    # Write results to a JSON file
    output_filename = "crawl_results.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_scraped, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved crawl results to '{output_filename}'.")

if __name__ == "__main__":
    main()
