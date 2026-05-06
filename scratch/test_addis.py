import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modules.scraper import fetch_source_results

def test():
    jobs = fetch_source_results("LinkedIn", "Frontend Developer", "Addis Ababa, Ethiopia", 0)
    for j in jobs[:5]:
        print(f"Location: {j['location']} | Country extracted: {j['country']}")

if __name__ == "__main__":
    test()
