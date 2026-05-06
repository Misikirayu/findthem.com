from playwright.sync_api import sync_playwright
import os

def test_scrape_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        url = "https://www.linkedin.com/jobs/search/?keywords=software+engineer+remote"
        page.goto(url, wait_until="networkidle")
        
        card = page.locator(".base-card, .job-search-card, .result-card").first
        if card:
            print(card.inner_html())
        browser.close()

if __name__ == "__main__":
    test_scrape_html()
