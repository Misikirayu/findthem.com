import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modules.scraper import fetch_source_results

def run():
    print("Testing global search...")
    jobs = fetch_source_results("LinkedIn", "Frontend Developer", "", 0)
    print(f"Global found: {len(jobs)}")
    
    print("\nTesting Addis Ababa search...")
    jobs2 = fetch_source_results("LinkedIn", "Frontend Developer", "addis ababa , ethiopia", 0)
    print(f"Addis found: {len(jobs2)}")
if __name__ == "__main__":
    run()
