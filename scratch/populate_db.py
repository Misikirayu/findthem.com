import asyncio
from modules.tiktok_scraper import fetch_tiktok_comments
from modules.database import add_comment, init_db

async def run_scrape():
    init_db()
    target_username = "hannahgidey"
    print(f"Starting actual scrape for @{target_username} and saving to DB...")
    count = 0
    async for comment in fetch_tiktok_comments(target_username, max_videos=5):
        add_comment(
            comment["user"], 
            comment.get("nickname", comment["user"]), 
            target_username, 
            comment["text"],
            comment.get("sticker_url"),
            comment.get("video_id")
        )
        count += 1
        if count % 100 == 0:
            print(f"Saved {count} comments so far...")
    print(f"Finished. Saved {count} comments in this run.")

if __name__ == "__main__":
    asyncio.run(run_scrape())
