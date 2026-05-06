import sys, os
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def run():
    url = "https://www.linkedin.com/jobs/search/?keywords=Developer&location=United%20States&start=0"
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
                link_el = cards[i].locator("a[href*='/jobs/view/'], a.base-card__full-link").first
                href = link_el.get_attribute("href") if link_el.count() else ""
                clean_href = href.split("?")[0] if href else ""
                
                # Check salary
                salary_text = "Competitive"
                salary_el = cards[i].locator('.job-search-card__salary-info, .salary-info, .result-card__meta .salary')
                if salary_el.count() > 0:
                    salary_text = salary_el.first.inner_text().strip()
                
                print(f"[{i}] URL: {href[:50]}... -> {clean_href}")
                print(f"[{i}] Salary: {salary_text}")
        except Exception as e:
            print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run()
