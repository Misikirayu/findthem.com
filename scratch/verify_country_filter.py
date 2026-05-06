import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.scraper import fetch_source_results

def test_location_search():
    query = "Software Engineer"
    location = "United Kingdom"
    print(f"Testing location search for '{query}' in '{location}'...")
    
    # We'll just fetch 1 page to verify
    jobs = fetch_source_results("LinkedIn", query, location, 0)
    
    if not jobs:
        print("No jobs found. This might be due to LinkedIn blocking or no results.")
        return

    print(f"Found {len(jobs)} jobs.")
    unique_countries = set(j.get('country') for j in jobs)
    print(f"Countries found: {unique_countries}")
    
    for job in jobs[:5]:
        print(f"- {job['title']} @ {job['company']} in {job['location']} (Country: {job['country']})")

if __name__ == "__main__":
    test_location_search()
