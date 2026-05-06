from playwright.sync_api import sync_playwright
import os
import re
from urllib.parse import quote, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_job_description(url: str):
    try:
        with sync_playwright() as p:
            user_data_dir = os.path.join(os.path.dirname(__file__), '..', 'browser_session')
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            body_text = page.locator("body").inner_text()
            context.close()
            return body_text
    except Exception as e:
        return f"Error: {e}"

# LinkedIn URL filter parameter mappings
LINKEDIN_WORKPLACE_FILTERS = {
    "Remote":  "2",
    "On-site": "1",
    "Hybrid":  "3",
}

LINKEDIN_JOBTYPE_FILTERS = {
    "Full-time":  "F",
    "Part-time":  "P",
    "Contract":   "C",
    "Internship": "I",
}


# ── Canonical country name lookup ─────────────────────────────────────────────
# Maps any variant/suffix that might appear in a LinkedIn location string to a
# canonical country name.  Add more entries as needed.
_COUNTRY_ALIASES: dict[str, str] = {
    # United Kingdom
    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    # United States
    "united states": "United States",
    "usa": "United States",
    "us": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "america": "United States",
    # Common countries
    "canada": "Canada",
    "australia": "Australia",
    "germany": "Germany",
    "deutschland": "Germany",
    "france": "France",
    "netherlands": "Netherlands",
    "holland": "Netherlands",
    "india": "India",
    "singapore": "Singapore",
    "ireland": "Ireland",
    "spain": "Spain",
    "italy": "Italy",
    "portugal": "Portugal",
    "sweden": "Sweden",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "switzerland": "Switzerland",
    "austria": "Austria",
    "belgium": "Belgium",
    "poland": "Poland",
    "brazil": "Brazil",
    "mexico": "Mexico",
    "japan": "Japan",
    "south korea": "South Korea",
    "korea": "South Korea",
    "china": "China",
    "new zealand": "New Zealand",
    "south africa": "South Africa",
    "israel": "Israel",
    "uae": "UAE",
    "united arab emirates": "UAE",
    "dubai": "UAE",
    "remote": "Remote",
    "worldwide": "Remote",
    "anywhere": "Remote",
    # ── Major UK cities (for "Greater X Area" stripping) ─────────────────────
    "london": "United Kingdom",
    "manchester": "United Kingdom",
    "birmingham": "United Kingdom",
    "edinburgh": "United Kingdom",
    "glasgow": "United Kingdom",
    "bristol": "United Kingdom",
    "leeds": "United Kingdom",
    "liverpool": "United Kingdom",
    "sheffield": "United Kingdom",
    "cardiff": "United Kingdom",
    "belfast": "United Kingdom",
    "oxford": "United Kingdom",
    "cambridge": "United Kingdom",
    "exeter": "United Kingdom",
    "portsmouth": "United Kingdom",
    "brighton": "United Kingdom",
    "nottingham": "United Kingdom",
    "coventry": "United Kingdom",
    "stoke-on-trent": "United Kingdom",
    "stoke on trent": "United Kingdom",
    # ── Major Australian cities ───────────────────────────────────────────────
    "sydney": "Australia",
    "melbourne": "Australia",
    "brisbane": "Australia",
    "perth": "Australia",
    "adelaide": "Australia",
    # ── Major Canadian cities ─────────────────────────────────────────────────
    "toronto": "Canada",
    "vancouver": "Canada",
    "montreal": "Canada",
    "calgary": "Canada",
    "ottawa": "Canada",
    # ── Major German cities ───────────────────────────────────────────────────
    "berlin": "Germany",
    "munich": "Germany",
    "münchen": "Germany",
    "hamburg": "Germany",
    "frankfurt": "Germany",
    # ── Major French cities ───────────────────────────────────────────────────
    "paris": "France",
    "lyon": "France",
    "marseille": "France",
    # ── Major Dutch cities ────────────────────────────────────────────────────
    "amsterdam": "Netherlands",
    "rotterdam": "Netherlands",
    # ── Major Irish cities ────────────────────────────────────────────────────
    "dublin": "Ireland",
    "cork": "Ireland",
    # ── Major Spanish cities ──────────────────────────────────────────────────
    "madrid": "Spain",
    "barcelona": "Spain",
    # ── Major Indian cities ───────────────────────────────────────────────────
    "bangalore": "India",
    "bengaluru": "India",
    "mumbai": "India",
    "delhi": "India",
    "hyderabad": "India",
    "chennai": "India",
    "pune": "India",
    # ── Singapore needs no city aliases (city-state) ─────────────────────────
}

# US state abbreviations (all-caps 2-letter codes that aren't country codes)
_US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}

# Regex for "Greater X Area" / "X Metropolitan Area" / "X Region" patterns
_METRO_RE = re.compile(
    r'^(?:greater\s+)?(.+?)\s+(?:area|metropolitan area|metro|region|county|district)$',
    re.IGNORECASE,
)


def _extract_country(raw_loc: str) -> str:
    """
    Convert a raw LinkedIn location string into a clean country name.

    Priority order:
    1. Explicit known country at the END of a comma-separated string.
    2. US-state abbreviation detection → "United States".
    3. Strip 'Greater X Area' / 'X Metropolitan Area' patterns and recurse.
    4. Whole-string lookup in the alias table.
    5. Fall back to "Other".
    """
    if not raw_loc:
        return "Other"

    raw_loc = raw_loc.strip()

    # 1. Split on commas, check each part from last to first
    parts = [p.strip() for p in raw_loc.split(',')]
    for part in reversed(parts):
        key = part.lower()
        if key in _COUNTRY_ALIASES:
            return _COUNTRY_ALIASES[key]
        # US state abbreviation
        if part.upper() in _US_STATES:
            return "United States"

    # 2. Strip metro-area suffixes and retry on the whole string
    m = _METRO_RE.match(raw_loc)
    if m:
        inner = m.group(1).strip()
        # Recurse – try to identify country from the inner city/region name
        result = _extract_country(inner)
        if result != "Other":
            return result
        # If still unknown, keep the inner city name so filter is at least useful
        return inner.title()

    # 3. Whole-string alias lookup (handles "Remote", "Worldwide", etc.)
    key = raw_loc.lower()
    if key in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[key]

    # 4. If there is only one comma-less token and it looks like a city/country
    #    that we couldn't match, return it as-is so the filter is still useful.
    if len(parts) == 1:
        return raw_loc.title()

    # 5. For any multi-part location where no segment matched a known alias
    #    (e.g. "Addis Ababa, Ethiopia" or "Nairobi, Kenya"), LinkedIn always
    #    puts the country LAST — so use it directly rather than returning "Other".
    last = parts[-1].strip()
    if last:
        return last.title()

    return "Other"


def _scrape_linkedin_filtered(query, location, page_idx, policy_name, policy_code, type_name, type_code):
    """
    Scrape a single LinkedIn filtered URL. Returns list of job dicts
    with policy and type pre-tagged from the URL filter used.
    """
    q = quote(query.strip())
    l = quote(location.strip()) if location else ""
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={l}&start={page_idx * 25}&f_WT={policy_code}&f_JT={type_code}"

    found_jobs = []
    seen_urls = set()
    blacklist = ['/career/salaries', '/companies', '/salaries', '/trending', '/faq', '/support']

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ])
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

            print(f"   📡 [{policy_name} / {type_name}] Fetching page {page_idx}...")

            try:
                page.goto(url, wait_until="commit", timeout=60000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            except:
                pass

            try:
                try:
                    page.wait_for_selector(".base-card", timeout=8000)
                except:
                    pass

                cards = page.locator(".base-card, .job-search-card, .result-card, [data-entity-urn]").all()
                for card in cards:
                    try:
                        title_el = card.locator("h2, h3, .title, [class*='title']").first
                        link_el = card.locator("a[href*='/jobs/view/'], a.base-card__full-link").first
                        if title_el and link_el.count() > 0:
                            title = title_el.inner_text().strip()
                            href = link_el.first.get_attribute("href")

                            company = "LinkedIn Company"
                            for c_sel in [".base-search-card__subtitle", ".hidden-nested-link", "h4", ".subtitle"]:
                                el = card.locator(c_sel)
                                if el.count() > 0:
                                    company = el.first.inner_text().strip()
                                    break

                            raw_loc = ""
                            country = "Other"
                            posted = "Recently"
                            for l_sel in [".job-search-card__location", ".base-search-card__metadata", "span.metadata"]:
                                el = card.locator(l_sel)
                                if el.count() > 0:
                                    full_meta = el.first.inner_text().strip()
                                    parts = [p.strip() for p in full_meta.split('·')]
                                    raw_loc = parts[0]
                                    country = _extract_country(raw_loc)
                                    if len(parts) > 1:
                                        posted = parts[1].replace("Reposted", "").replace("Promoted", "").strip()
                                    break

                            # Refine date
                            if posted == "Recently":
                                for d_sel in [".job-search-card__listdate", "time"]:
                                    el = card.locator(d_sel)
                                    if el.count() > 0:
                                        posted = el.first.inner_text().strip()
                                        break

                            # Salary
                            salary = "Competitive"
                            # Expanded selectors for salary indicators (often containing $, £, €, or keywords like 'salary')
                            for s_sel in [".job-search-card__salary-info", ".salary", "span:has-text('$')", "span.metadata:has-text('£')"]:
                                el = card.locator(s_sel)
                                if el.count() > 0:
                                    stext = el.first.inner_text().strip()
                                    if any(ch in stext for ch in ['$', '£', '€']) or any(k in stext.lower() for k in ['salary', '/yr', '/hr']):
                                        salary = stext
                                    break

                            if href:
                                clean_href = href.split('?')[0] # Remove query parameters to deduplicate tracking URLs
                            else:
                                clean_href = None

                            if clean_href and clean_href not in seen_urls and not any(b in clean_href for b in blacklist):
                                found_jobs.append({
                                    "title": title,
                                    "url": clean_href,
                                    "source": "LinkedIn",
                                    "company": company,
                                    "location": raw_loc,
                                    "posted": posted,
                                    "salary": salary,
                                    "type": type_name,      # Known from URL filter
                                    "policy": policy_name,   # Known from URL filter
                                    "country": country,
                                })
                                seen_urls.add(clean_href)
                    except:
                        continue
            except:
                pass

            context.close()
            browser.close()
            print(f"   ✅ [{policy_name} / {type_name}] Found {len(found_jobs)} jobs")
            return found_jobs
    except Exception as e:
        print(f"   ❌ [{policy_name} / {type_name}] Error: {e}")
        return []


def fetch_source_results(source_name, query, location, page_idx):
    """
    Fetches jobs from LinkedIn using multiple filtered requests in parallel
    to get accurate policy and type data.
    """
    if source_name != "LinkedIn":
        return []

    all_jobs = []
    seen_urls = set()

    # Define which filter combinations to fetch
    # Each combo = (policy_name, policy_code, type_name, type_code)
    filter_combos = []
    for policy_name, policy_code in LINKEDIN_WORKPLACE_FILTERS.items():
        for type_name, type_code in LINKEDIN_JOBTYPE_FILTERS.items():
            filter_combos.append((policy_name, policy_code, type_name, type_code))

    print(f"📡 SCANNING LinkedIn with {len(filter_combos)} filter combos (Page {page_idx})...")

    # Run all filtered scrapes in parallel threads
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(
                _scrape_linkedin_filtered, query, location, page_idx,
                policy_name, policy_code, type_name, type_code
            ): (policy_name, type_name)
            for policy_name, policy_code, type_name, type_code in filter_combos
        }

        for future in as_completed(futures):
            try:
                jobs = future.result()
                for job in jobs:
                    if job["url"] not in seen_urls:
                        all_jobs.append(job)
                        seen_urls.add(job["url"])
            except Exception as e:
                label = futures[future]
                print(f"   ❌ {label} failed: {e}")

    print(f"   ✅ TOTAL: Found {len(all_jobs)} unique jobs across all filters")
    return all_jobs


def fetch_page_results(query, location, page_idx):
    all_jobs = []
    for source in ["LinkedIn"]:
        all_jobs.extend(fetch_source_results(source, query, location, page_idx))
    return all_jobs

def discover_job_links(query, location="Remote", max_pages=3):
    """
    A generator that yields job links by iterating through pages.
    """
    for i in range(max_pages):
        jobs = fetch_page_results(query, location, i)
        if not jobs:
            break
        for job in jobs:
            yield job
