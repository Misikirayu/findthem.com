import asyncio
import httpx
import re
import json
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Retry / backoff settings
MAX_RATE_LIMIT_RETRIES = 5
RATE_LIMIT_BASE_DELAY = 5  # seconds, doubles each retry
MAX_TRANSIENT_RETRIES = 3
TRANSIENT_RETRY_DELAY = 3  # seconds


async def _discover_video_ids(page, username, max_videos=None):
    """
    Uses an existing Playwright page to scroll through a user's profile
    and yield video IDs as they are discovered.
    """
    yielded_ids = set()
    url = f"https://www.tiktok.com/@{username}"
    print(f"DEBUG: [Playwright] Navigating to {url}...")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)

        # Wait for videos to load
        try:
            await page.wait_for_selector('a[href*="/video/"]', timeout=8000)
        except:
            pass

        # Dismiss any modals quickly
        for selector in [
            '[data-e2e="modal-close-inner-button"]',
            'svg[aria-label="Close"]',
            'text=Not now',
            'text=Skip',
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=500):
                    await btn.click()
            except:
                pass

        if await page.locator("text=Verify to continue").count() > 0:
            print("DEBUG: [Playwright] CAPTCHA detected.")
            return

        # Scroll and yield new IDs as we find them
        last_count = 0
        no_new_ids_count = 0
        scroll_count = 0

        while True:
            scroll_count += 1
            print(
                f"DEBUG: [Playwright] Scanning for videos (Scroll {scroll_count})... Found: {len(yielded_ids)}"
            )

            # Extract all hrefs via JS
            hrefs = await page.evaluate(
                """() => {
                return Array.from(document.querySelectorAll('a[href*="/video/"]')).map(a => a.href);
            }"""
            )

            for href in hrefs:
                if href:
                    match = re.search(r"/video/(\d+)", href)
                    if match:
                        v_id = match.group(1)
                        if v_id not in yielded_ids:
                            yielded_ids.add(v_id)
                            yield v_id
                            if max_videos and len(yielded_ids) >= max_videos:
                                return

            if len(yielded_ids) == last_count:
                if len(yielded_ids) > 0:
                    no_new_ids_count += 1
                if no_new_ids_count >= 10:
                    print(
                        "DEBUG: [Playwright] No new videos found after 10 scrolls. Reached end of page."
                    )
                    break
            else:
                no_new_ids_count = 0
                last_count = len(yielded_ids)

            await page.keyboard.press("PageDown")
            await asyncio.sleep(0.5)
            await page.mouse.wheel(0, 4000)
            await asyncio.sleep(1.5)

    except Exception as e:
        print(f"DEBUG: [Playwright] Error during video discovery: {e}")


async def _fetch_video_comments(client, video_id, username, max_comments_per_video=None):
    """
    Fetches all comments for a single video using the authenticated httpx client.
    Yields comment dicts. Handles rate limits with exponential backoff.
    """
    cursor = 0
    has_more = True
    comments_for_this_video = 0
    is_first_request = True
    rate_limit_retries = 0

    while has_more and (
        max_comments_per_video is None
        or comments_for_this_video < max_comments_per_video
    ):
        api_url = "https://www.tiktok.com/api/comment/list/"
        count_param = (
            50
            if max_comments_per_video is None
            else min(max_comments_per_video - comments_for_this_video, 50)
        )

        params = {
            "aweme_id": video_id,
            "count": count_param,
            "cursor": cursor,
            "aid": 1988,
        }

        # Polite delay between pages (not on first request)
        if not is_first_request:
            await asyncio.sleep(random.uniform(0.8, 1.8))
        is_first_request = False

        # Transient retry loop
        for attempt in range(MAX_TRANSIENT_RETRIES):
            try:
                resp = await client.get(
                    api_url,
                    params=params,
                    headers={
                        "Referer": f"https://www.tiktok.com/@{username}/video/{video_id}"
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    comments = data.get("comments", []) or []

                    for c in comments:
                        text = (c.get("text") or "").strip()
                        unique_id = c.get("user", {}).get("unique_id")
                        nickname = c.get("user", {}).get("nickname") or unique_id

                        sticker_data = c.get("sticker", {})
                        sticker_url = None
                        if sticker_data:
                            url_list = sticker_data.get("static_url", {}).get(
                                "url_list", []
                            )
                            if url_list:
                                sticker_url = url_list[0]

                        is_placeholder = text.lower() in ["[sticker]", "sticker"]
                        if sticker_url or (text and not is_placeholder):
                            yield {
                                "video_id": video_id,
                                "user": unique_id,
                                "nickname": nickname,
                                "text": "" if is_placeholder else text,
                                "sticker_url": sticker_url,
                            }

                    comments_for_this_video += len(comments)
                    has_more = data.get("has_more") == 1
                    cursor = data.get("cursor", 0)
                    rate_limit_retries = 0  # Reset on success

                    print(
                        f"DEBUG: Fetched {len(comments)} comments (Total: {comments_for_this_video}) for video {video_id}"
                    )

                    if not comments:
                        # Empty list but has_more=true — safety break
                        has_more = False
                    break  # Success, exit retry loop

                elif resp.status_code == 429:
                    rate_limit_retries += 1
                    if rate_limit_retries > MAX_RATE_LIMIT_RETRIES:
                        print(
                            f"DEBUG: Rate limit exceeded {MAX_RATE_LIMIT_RETRIES} retries for video {video_id}. Skipping."
                        )
                        return
                    delay = RATE_LIMIT_BASE_DELAY * (2 ** (rate_limit_retries - 1))
                    print(
                        f"DEBUG: Rate limit 429! Retry {rate_limit_retries}/{MAX_RATE_LIMIT_RETRIES} — sleeping {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    break  # Break retry loop to re-enter while loop

                else:
                    print(
                        f"DEBUG: TikTok API returned status {resp.status_code} for video {video_id}"
                    )
                    if attempt < MAX_TRANSIENT_RETRIES - 1:
                        await asyncio.sleep(TRANSIENT_RETRY_DELAY)
                    else:
                        return  # Give up on this video

            except Exception as e:
                print(
                    f"DEBUG: Error fetching comments for {video_id} at cursor {cursor} (attempt {attempt + 1}): {e}"
                )
                if attempt < MAX_TRANSIENT_RETRIES - 1:
                    await asyncio.sleep(TRANSIENT_RETRY_DELAY)
                else:
                    return  # Give up on this video


async def fetch_tiktok_comments(
    username: str, max_videos: int = None, max_comments_per_video: int = None
):
    """
    Hybrid Scraper:
    1. Get Video IDs via Playwright (Reliable)
    2. Extract cookies from the Playwright browser session
    3. Get Comments via HTTP API using those cookies (Fast + Authenticated)
    Yields comments as they are found.
    """
    username = username.replace("@", "")
    stealth = Stealth()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await stealth.apply_stealth_async(page)

        # ── Phase 1: Discover all video IDs ──────────────────────────
        print(f"DEBUG: [Scraper] Phase 1 — Discovering videos for @{username}...")
        video_ids = []
        async for vid in _discover_video_ids(page, username, max_videos):
            video_ids.append(vid)

        print(f"DEBUG: [Scraper] Discovered {len(video_ids)} videos.")

        if not video_ids:
            await browser.close()
            return

        # ── Phase 2: Extract cookies from the live browser ───────────
        cookies = await context.cookies()
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        print(f"DEBUG: [Scraper] Extracted {len(cookies)} cookies from browser session.")

        # Build authenticated headers
        auth_headers = {
            **HEADERS,
            "Cookie": cookie_header,
            "Referer": f"https://www.tiktok.com/@{username}",
        }

        # ── Phase 3: Fetch comments with authenticated client ────────
        print(f"DEBUG: [Scraper] Phase 3 — Fetching comments for {len(video_ids)} videos...")
        total_comments = 0

        async with httpx.AsyncClient(
            headers=auth_headers, follow_redirects=True, timeout=30.0
        ) as client:
            for idx, video_id in enumerate(video_ids):
                print(
                    f"DEBUG: [Scraper] Processing video {idx + 1}/{len(video_ids)}: {video_id}"
                )
                async for comment in _fetch_video_comments(
                    client, video_id, username, max_comments_per_video
                ):
                    total_comments += 1
                    yield comment

                # Small delay between videos to be polite
                if idx < len(video_ids) - 1:
                    await asyncio.sleep(random.uniform(0.5, 1.5))

        print(
            f"DEBUG: [Scraper] ✅ Finished! Total comments fetched: {total_comments} from {len(video_ids)} videos."
        )
        await browser.close()


if __name__ == "__main__":
    import sys

    async def main():
        user = sys.argv[1] if len(sys.argv) > 1 else "tiktok"
        count = 0
        async for r in fetch_tiktok_comments(user):
            count += 1
            if count <= 10:
                print(f"[{r['user']}]: {r['text']}")
        print(f"\n✅ Total: {count} comments found.")

    asyncio.run(main())
