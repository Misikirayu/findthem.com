import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from urllib.parse import quote
from playwright.sync_api import sync_playwright

def test_linkedin_location(loc_str):
    q = quote("Developer")
    l = quote(loc_str)
    # Remove strict filters to see if we get anything
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={l}&start=0"
    print(f"Testing URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Referer": "https://www.google.com/"
                }
            )
        page = context.new_page()
        page.goto(url, wait_until="commit", timeout=60000)
        
        try:
            page.wait_for_selector(".base-card", timeout=8000)
            cards = page.locator(".base-card").all()
            print(f"  -> Found {len(cards)} jobs")
            if len(cards) > 0:
                for i in range(min(3, len(cards))):
                    loc_text = cards[i].locator(".job-search-card__location").inner_text() if cards[i].locator(".job-search-card__location").count() > 0 else "Unknown"
                    print(f"  -> Job {i} location: {loc_text.strip()}")
        except Exception as e:
            print(f"  -> No jobs found or error: {e}")
        browser.close()

if __name__ == "__main__":
    test_linkedin_location("Addis Ababa")
    test_linkedin_location("addis ababa , ethiopia")
    test_linkedin_location("Ethiopia")
