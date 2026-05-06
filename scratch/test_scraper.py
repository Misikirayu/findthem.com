import asyncio
from modules.tiktok_scraper import fetch_tiktok_comments

async def test():
    count = 0
    print("Starting test scrape for @hannahgidey...")
    async for comment in fetch_tiktok_comments("hannahgidey", max_videos=2):
        count += 1
        if count % 100 == 0:
            print(f"Fetched {count} comments so far...")
        if count > 2000:
            break
    print(f"Finished. Total fetched in test: {count}")

if __name__ == "__main__":
    asyncio.run(test())
