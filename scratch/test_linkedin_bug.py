import sys, os
from urllib.parse import quote
from playwright.sync_api import sync_playwright

def run():
    q = quote("Frontend Developer")
    l = quote("addis ababa , ethiopia")
    # Using f_WT=1 (on-site), f_JT=F (full-time)
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={l}&start=0&f_WT=1&f_JT=F"
    print(f"URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        page.goto(url, wait_until="commit", timeout=60000)
        
        try:
            page.wait_for_selector(".base-card", timeout=8000)
            cards = page.locator(".base-card").all()
            print(f"Found {len(cards)} jobs")
            for i in range(min(5, len(cards))):
                title = cards[i].locator(".base-search-card__title").inner_text() if cards[i].locator(".base-search-card__title").count() else "Unknown"
                loc = cards[i].locator(".job-search-card__location").inner_text() if cards[i].locator(".job-search-card__location").count() else "Unknown"
                print(f"  - {title} in {loc}")
        except Exception as e:
            print(f"No jobs found: {e}")
        browser.close()

if __name__ == "__main__":
    run()
