import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

async def analyze_stream(comment_generator):
    """
    Takes an async generator of comments and yields analyzed chunks.
    Each chunk contains a list of analyzed bullies.
    """
    batch = []
    batch_size = 5 # Analyze in small groups for efficiency while maintaining "stream" feel

    async for comment in comment_generator:
        batch.append(comment)
        if len(batch) >= batch_size:
            analyzed = await analyze_comments(batch)
            if "top_bullies" in analyzed:
                for bully in analyzed["top_bullies"]:
                    yield bully
            batch = []
    
    # Final batch
    if batch:
        analyzed = await analyze_comments(batch)
        if "top_bullies" in analyzed:
            for bully in analyzed["top_bullies"]:
                yield bully

async def analyze_comments(comments):
    """
    Analyzes a list of comments for toxicity and bullying.
    Returns a categorized report.
    """
    if not comments:
        return {"total": 0, "bullies": [], "summary": "No comments found."}

    # Prepare comments for analysis
    comments_text = "\n".join([f"- {c['user']}: {c['text']}" for c in comments])

    prompt = f"""
    You are an expert in social media toxicity and behavioral analysis, specialized in English and Amharic (አማርኛ).
    
    TASK: Analyze the following TikTok comments for bullying, harassment, and toxicity. 
    
    IMPORTANT - AMHARIC CONTEXT: 
    - Amharic insults are often metaphorical or focused on family, social status, or appearance.
    - Words like "ኩታራ" (insignificant), "እስስት" (chameleon/fake), "ባምቡላ" (metaphorical insult), "ፋራ" (uncultured/loser), "ፎርጅድ" (fake) should be flagged if used maliciously.
    - Pay attention to sarcasm and "Double Entendre" (ቅኔ- መሰል ስድቦች). 
    - If a comment starts with "ምድረ" followed by a negative term, it's usually a group attack.
    - Even if a comment seems "neutral" to a basic translator, if the intent is mocking or condescending in Ethiopian social context, mark it as 'Bully'.
    - Analyze the sentiment and behavior regardless of whether it's in Geez script or Latinized Amharic (Amharlish).

    CATEGORIES:
    1. Neutral: No harmful intent.
    2. Positive: Supportive or kind.
    3. Bully: Any form of harassment, mocking, or toxicity.
    
    BULLY SUB-CATEGORIES:
    - Personal Attack: Direct insults to character or intelligence.
    - Appearance Mockery: Insults about looks, body, or physical traits.
    - Intelligence Mockery: Calling someone stupid or incapable.
    - Hate Speech: Attacks based on ethnicity, religion, or gender.
    - Threat: Any suggestion of harm.

    Comments:
    {comments_text}

    Return the analysis ONLY as a JSON object with the following structure:


    {{
        "total_analyzed": int,
        "overall_toxicity_score": float (0-100),
        "categories": {{
            "Neutral": int,
            "Positive": int,
            "Bully": int
        }},
        "bully_breakdown": {{
            "Personal Attack": int,
            "Appearance Mockery": int,
            "Intelligence Mockery": int,
            "Hate Speech": int,
            "Threat": int
        }},
        "top_bullies": [
            {{
                "user": "username",
                "text": "comment text",
                "category": "sub-category",
                "severity": float (0-10)
            }}
        ],
        "summary": "Brief overall analysis summary"
    }}
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-pro-1.5", # High reasoning capability for linguistic nuances
                    "messages": [
                        {"role": "system", "content": "You are an expert toxicity analyst specialized in social media behavior."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": { "type": "json_object" }
                },
                timeout=60.0
            )
            
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            return json.loads(analysis_text)
            
    except Exception as e:
        print(f"Error analyzing comments: {e}")
        return {
            "error": str(e),
            "total_analyzed": len(comments),
            "summary": "Failed to analyze comments due to an error."
        }
