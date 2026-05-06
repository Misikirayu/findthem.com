import sys
sys.path.insert(0, '/home/mskr/Desktop/jobjob')
from modules.scraper import fetch_source_results
from collections import Counter

results = fetch_source_results("LinkedIn", "software engineer", 0)
print(f"\nTotal unique jobs: {len(results)}")

policies = Counter(j['policy'] for j in results)
types = Counter(j['type'] for j in results)

print(f"\n--- Workplace Policy ---")
for k, v in policies.most_common():
    print(f"  {k}: {v}")

print(f"\n--- Job Type ---")
for k, v in types.most_common():
    print(f"  {k}: {v}")
