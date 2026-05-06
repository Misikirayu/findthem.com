import sys, os
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
            for i in range(min(3, len(cards))):
                html = cards[i].inner_html()
                print(f"--- CARD {i} ---")
                print(html[:1000]) # Print first 1000 chars of HTML
                
        except Exception as e:
            print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run()
