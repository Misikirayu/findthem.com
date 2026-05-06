from modules.scraper import fetch_source_results
import json
import os

def test_remote_in_title():
    query = "Remote Software Engineer"
    print(f"Testing actual scraper with query: {query}")
    results = fetch_source_results("LinkedIn", query, 0)
    print(f"Found {len(results)} results")
    for i, job in enumerate(results[:10]):
        if job['policy'] == 'Remote' or job['type'] == 'Full-time':
            print(f"\n--- Job {i} ---")
            print(f"Title: {job['title']}")
            print(f"Location: {job['location']}")
            print(f"Policy: {job['policy']}")
            print(f"Type: {job['type']}")
        else:
            # Just print the first 3 if they don't match
            if i < 3:
                print(f"\n--- Job {i} (No match) ---")
                print(f"Title: {job['title']}")
                print(f"Policy: {job['policy']}")

if __name__ == "__main__":
    test_remote_in_title()
