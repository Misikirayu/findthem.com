import asyncio
import sys
import traceback
import os

# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def main():
    try:
        from main import analyze_tiktok_user_stream
        
        # Test the generator
        print("Starting generator...")
        resp = await analyze_tiktok_user_stream("demo")
        async for chunk in resp.body_iterator:
            print(f"Chunk: {chunk}")
            
    except Exception as e:
        print("EXCEPTION CAUGHT!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
