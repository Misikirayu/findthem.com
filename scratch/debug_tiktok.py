"""Debug script - takes a screenshot of what TikTok shows to headless browser."""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def debug():
    stealth = Stealth()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = await context.new_page()
        await stealth.apply_stealth_async(page)

        print("Navigating...")
        await page.goto("https://www.tiktok.com/@hannahgidey", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)

        # Dismiss the "Open TikTok" modal
        for selector in ["text=Not now", "text=Skip", "button:has-text('Not now')", '[aria-label="Close"]']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    await btn.click()
                    print(f"Dismissed modal: {selector}")
                    await asyncio.sleep(2)
                    break
            except:
                continue

        # Scroll to load content
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(2)

        # Save screenshot AFTER dismissing modal
        await page.screenshot(path="/home/mskr/Desktop/jobjob/scratch/tiktok_debug_after.png", full_page=True)
        
        # Save HTML
        html = await page.content()
        with open("/home/mskr/Desktop/jobjob/scratch/tiktok_debug.html", "w") as f:
            f.write(html)

        # Print what links are on the page
        links = await page.locator("a[href]").all()
        print(f"Found {len(links)} total links")
        hrefs = []
        for l in links[:30]:
            href = await l.get_attribute("href")
            hrefs.append(href)
        print("First 30 links:", hrefs)

        # Check page title
        print("Page title:", await page.title())

        await browser.close()

asyncio.run(debug())
