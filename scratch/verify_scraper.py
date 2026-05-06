from modules.scraper import fetch_source_results
import json

def test_actual_scraper():
    query = "software engineer remote"
    print(f"Testing actual scraper with query: {query}")
    results = fetch_source_results("LinkedIn", query, 0)
    print(f"Found {len(results)} results")
    for i, job in enumerate(results[:5]):
        print(f"\n--- Job {i} ---")
        print(f"Title: {job['title']}")
        print(f"Location: {job['location']}")
        print(f"Policy: {job['policy']}")
        print(f"Type: {job['type']}")

if __name__ == "__main__":
    test_actual_scraper()
