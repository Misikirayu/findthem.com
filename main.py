from fastapi import FastAPI, Request
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from modules.tiktok_scraper import fetch_tiktok_comments
from modules.analyzer import analyze_comments, analyze_stream
from modules.database import init_db, add_comment, get_comments, get_comment_count

init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared executor for scraping tasks
executor = ThreadPoolExecutor(max_workers=10)

@app.get("/")
async def root():
    return {"status": "alive", "message": "Insider Bullies API is running"}

# Serve Frontend
frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# Mount static files (JS, CSS, images)
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Serve index.html for all routes (SPA support)
        # Note: API routes defined above this will take precedence
        index_file = os.path.join(frontend_path, "index.html")
        return FileResponse(index_file)
else:
    print(f"WARNING: Frontend path not found at {frontend_path}. Make sure to run 'npm run build' in the frontend directory.")

from fastapi.responses import StreamingResponse
import json

@app.get("/analyze_stream")
async def analyze_tiktok_user_stream(username: str = "hannahgidey"):
    """
    Streams TikTok comments for the target user exclusively.
    """
    # Force the target user
    target_username = "hannahgidey"
    async def event_generator():
        print(f"INFO: Starting fresh scan for @{target_username}...")
        try:
            # Check for demo mode
            if username.lower() == "demo":
                sample = get_sample_analysis()
                for bully in sample["top_bullies"]:
                    await asyncio.sleep(0.5) 
                    yield json.dumps(bully) + "\n"
                return

            # 1. Fetch Stream directly
            comment_gen = fetch_tiktok_comments(target_username, max_videos=None, max_comments_per_video=None) 
            async for comment in comment_gen:
                # Save to database in a separate thread to avoid blocking the event loop
                await asyncio.to_thread(
                    add_comment,
                    comment["user"], 
                    comment.get("nickname", comment["user"]), 
                    target_username, 
                    comment["text"],
                    comment.get("sticker_url"),
                    comment.get("video_id")
                )
                
                # Add default metadata for UI compatibility
                comment["category"] = "Neutral"
                comment["severity"] = 0
                yield json.dumps(comment) + "\n"
                
            print(f"INFO: Scan for @{target_username} completed successfully.")
        except Exception as e:
            print(f"ERROR during scan for @{target_username}: {e}")
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.get("/history")
async def get_history(username: str = "hannahgidey", limit: int = 100, offset: int = 0):
    """
    Fetches stored comments for the target user with pagination.
    """
    target_username = "hannahgidey"
    try:
        comments = get_comments(target_username, limit=limit, offset=offset)
        total = get_comment_count(target_username)
        return {
            "status": "success",
            "comments": comments,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/analyze")
async def analyze_tiktok_user(username: str = "hannahgidey"):
    """
    Fetches and analyzes TikTok comments for the target user.
    """
    target_username = "hannahgidey"
    try:
        # Check for demo mode
        if username.lower() == "demo":
            return {
                "status": "success",
                "username": "demo_user",
                "analysis": get_sample_analysis()
            }

        # 1. Fetch comments
        comments = []
        async for comment in fetch_tiktok_comments(username, max_videos=10):
            comments.append(comment)
        
        if not comments:
            # Instead of just error, let's offer to show sample data or explain why
            return {
                "status": "error", 
                "message": f"Could not find comments for @{username}. TikTok might be blocking the request. Try 'demo' as a username to see how it works!",
                "suggestion": "demo"
            }
        
        # 2. Analyze comments
        analysis = await analyze_comments(comments)
        
        return {
            "status": "success",
            "username": username,
            "analysis": analysis
        }
    except Exception as e:
        print(f"Server Error: {e}")
        return {"status": "error", "message": str(e)}

def get_sample_analysis():
    return {
        "total_analyzed": 25,
        "overall_toxicity_score": 68.5,
        "categories": {
            "Neutral": 5,
            "Positive": 3,
            "Bully": 17
        },
        "bully_breakdown": {
            "Personal Attack": 8,
            "Appearance Mockery": 4,
            "Intelligence Mockery": 3,
            "Hate Speech": 2,
            "Threat": 0
        },
        "top_bullies": [
            {
                "user": "hater123",
                "text": "Your videos are so cringe, please stop posting.",
                "category": "Personal Attack",
                "severity": 7.5
            },
            {
                "user": "random_troll",
                "text": "You look like a potato with hair.",
                "category": "Appearance Mockery",
                "severity": 8.2
            },
            {
                "user": "smart_guy",
                "text": "Is there even a brain in that head of yours?",
                "category": "Intelligence Mockery",
                "severity": 6.8
            }
        ],
        "summary": "The comment section shows a high level of coordinated bullying, primarily focused on the creator's appearance and content style. We recommend turning on comment filters."
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
