# AI Job Automator: Build Log & How-To

This document summarizes the steps taken to build and configure the AI Job Automator project.

## 1. Initial Scaffold & Architecture
We started with the architectural vision defined in `AI_Job_Automator_Plan.md`. We set up the core project structure:
* `app.py`: The Streamlit dashboard acting as our UI.
* `requirements.txt`: The Python dependencies.
* `.env`: Environment variables configuration.
* `modules/`: Directory containing all our core logic.

## 2. Core Modules Implementation
* **Database (`modules/database.py`)**: Created an SQLite database (`data/history.db`) to track application history (job title, URL, company, match score, and status) to prevent duplicate applications.
* **Brain / AI Logic (`modules/ai_logic.py`)**: 
  * Initially built using Google's generative AI SDK to extract text from a PDF resume and map form fields.
  * **Refactor:** Later switched the underlying SDK from `google-generativeai` to `openai` to support **OpenRouter**. We configured the base URL to `https://openrouter.ai/api/v1` and used the `OPENROUTER_API_KEY`.
  * **Token Limit Fix:** We encountered a `402 Error` because OpenRouter was anticipating the maximum possible token request (over 65k tokens for Gemini 2.5 Flash), which exceeded account credits. We fixed this by limiting the request size using `max_tokens=2048`.
* **Brawn / Automation (`modules/browser.py` & `modules/scraper.py`)**:
  * Implemented Playwright to handle scraping job descriptions and automatically finding/filling HTML form inputs (`<label>` and `<input>`).
  * **Persistent Login Fix:** Initially, Playwright launched a fresh browser each time, which blocked users at the Google Sign-in phase. We modified the code to use `launch_persistent_context` with a local `browser_session/` folder. This ensures that any Google Account logins, cookies, and session data remain persistent across automation runs!

## 3. How to Run

1. **Environment Setup**:
   Ensure you have a `.env` file in the root directory:
   ```env
   OPENROUTER_API_KEY=your_key_here
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Launch the App**:
   ```bash
   streamlit run app.py
   ```
   
4. **Usage Flow**:
   * **Tab 1**: Upload a PDF resume. The AI will extract it into a structured "Identity Map".
   * **Tab 2**: Paste a job portal URL (e.g., a Greenhouse or Lever link). The Playwright scraper will fetch the JD, the AI will score the match, and if it exceeds your threshold, a visible browser window will open. If you encounter a Google login, sign in once, and the local session will be saved for all future loops!
