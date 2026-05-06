from playwright.sync_api import sync_playwright
import time
from .ai_logic import map_form_fields

def auto_apply(url, resume_json, match_score=100):
    """
    Given a url to an application form, use playwright to find inputs and ask AI what to fill.
    """
    logs = []
    def log(msg):
        logs.append(msg)
        print(f"[Browser]: {msg}")

    try:
        with sync_playwright() as p:
            import os
            # We use persistent context here to save your Google Session/Cookies!
            user_data_dir = os.path.join(os.path.dirname(__file__), '..', 'browser_session')
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False, # Headless=False so user can see it! "Brawn"
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                args=["--disable-blink-features=AutomationControlled"]
            )
            # persistent context starts with a default page
            if len(context.pages) > 0:
                page = context.pages[0]
            else:
                page = context.new_page()
            
            log(f"Navigating to {url}")
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(2) # let it breathe

            # Scrape form fields
            log("Scraping form fields...")
            # We look for inputs that are visible
            input_locators = page.locator("input:visible, textarea:visible")
            count = input_locators.count()
            
            fields_data = []
            for i in range(count):
                loc = input_locators.nth(i)
                field_id = loc.get_attribute("id") or loc.get_attribute("name") or f"input_{i}"
                field_type = loc.get_attribute("type") or "text"
                
                # try to find associated label
                label_text = page.locator(f"label[for='{field_id}']").inner_text() if loc.get_attribute("id") else ""
                if not label_text and loc.get_attribute("placeholder"):
                    label_text = loc.get_attribute("placeholder")
                    
                fields_data.append({
                    "id": field_id,
                    "type": field_type,
                    "label": label_text
                })
            
            log(f"Found {len(fields_data)} fillable fields.")
            
            # Map fields using AI
            log("Asking AI to map fields to resume...")
            mapped_values = map_form_fields(resume_json, fields_data)
            log(f"AI suggested mapping: {mapped_values}")
            
            # Fill the fields
            log("Filling fields...")
            for i in range(count):
                loc = input_locators.nth(i)
                field_id = fields_data[i]["id"]
                val = mapped_values.get(field_id, "")
                if val:
                    # simplistic check
                    if fields_data[i]["type"] not in ["checkbox", "radio", "file", "submit"]:
                        loc.fill(str(val))
                        time.sleep(0.5) # human-like typing speed simulation
            
            log("Form filled successfully. Pause for review.")
            time.sleep(5) # Pause to let the user see what happened
            
            # Note: We do NOT auto-click submit here to keep it safe for demo purposes.
            # user can click submit or we could add:
            # page.locator("button[type='submit'], input[type='submit']").first.click()
            
            browser.close()
            log("Browser closed.")
            return True, logs
    except Exception as e:
        log(f"Error during automation: {e}")
        return False, logs
