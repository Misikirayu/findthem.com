import os
import fitz  # PyMuPDF
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = None
if OPENROUTER_API_KEY:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

# Use a model from OpenRouter (e.g., google/gemini-2.5-flash or another model of your choice)
MODEL_NAME = "google/gemini-2.0-flash-001"

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def _generate_json_response(prompt):
    if not client:
        raise Exception("OpenRouter API Key not found. Please set OPENROUTER_API_KEY in .env")
        
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    
    content = response.choices[0].message.content
    
    # Robust JSON extraction using regex
    import re
    json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
    if json_match:
        cleaned_text = json_match.group(0)
    else:
        cleaned_text = content.replace("```json", "").replace("```", "").strip()
        
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from content: {content}")
        raise e

def parse_resume(pdf_path):
    resume_text = extract_text_from_pdf(pdf_path)
    if not resume_text:
        return None
        
    prompt = """
    Extract the following information from the resume and return it ONLY as a valid JSON object:
    - full_name
    - email
    - phone
    - location
    - skills (list of strings)
    - experience_years (integer)
    - summary (a brief paragraph summarizing the candidate)
    
    Resume Text:
    """ + resume_text

    try:
        return _generate_json_response(prompt)
    except Exception as e:
        print(f"Error parsing resume with OpenRouter: {e}")
        return {"error": str(e), "raw_text": resume_text[:100] + "..."}

def calculate_match_score(resume_json, job_description):
    if not resume_json:
        return 0, "No resume provided"
        
    prompt = f"""
    Compare this resume with the job description.
    Provide a match score from 0 to 100 based on skills, experience, and requirements fit.
    Also provide a very brief explanation (1-2 sentences).
    
    Respond EXACTLY in this JSON format:
    {{"score": 85, "reason": "Candidate has strong Python skills matching the requirement, but lacks AWS experience."}}
    
    Resume:
    {json.dumps(resume_json)}
    
    Job Description:
    {job_description}
    """
    
    try:
        result = _generate_json_response(prompt)
        return int(result.get("score", 0)), result.get("reason", "Unknown reason")
    except Exception as e:
        print(f"Error matching with OpenRouter: {e}")
        return 0, str(e)

def map_form_fields(resume_json, fields_data):
    """
    fields_data typically a list of dicts: [{'label': 'First Name', 'type': 'text', 'id': 'fname'}]
    Returns a dict mapping the field `id` to the value to fill.
    """
    prompt = f"""
    Given the applicant's profile, provide the correct value for each form field.
    If a field asks for a URL or something not in the profile, try to infer or return an empty string.
    
    Applicant Profile:
    {json.dumps(resume_json)}
    
    Form Fields to Fill:
    {json.dumps(fields_data)}
    
    Return ONLY a JSON mapping where keys are the field 'id' and values are the string to input.
    Example: {{"fname": "John", "lname": "Doe", "years_exp": "5"}}
    """
    
    try:
        return _generate_json_response(prompt)
    except Exception as e:
        print(f"Error mapping fields with OpenRouter: {e}")
        return {}

def broaden_query(user_query):
    if not client: return user_query
    
    prompt = f"Convert this job title into a broad search query using OR for synonyms. Output ONLY the string. Example: 'frontend' -> 'frontend engineer OR web developer'. Query: {user_query}"
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are a job search expert. Respond only with the search string."},
                      {"role": "user", "content": prompt}],
            max_tokens=100
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        print(f"Query broadening failed: {e}")
        return user_query
