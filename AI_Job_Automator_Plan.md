# Creating a highly detailed Markdown file for the AI Job Automator project as requested.

full_md_content = """# AI Job Automator: Technical Specification & Implementation Guide

## 1. Project Vision
The **AI Job Automator** is a sophisticated local web application designed to automate the end-to-end job application lifecycle. Unlike simple scrapers, this tool uses Artificial Intelligence to perform "semantic matching," ensuring that applications are only submitted when there is a high probability of a fit, and tailoring each submission to the specific job requirements.

---

## 2. System Architecture

The application is built using a "Brain and Brawn" approach:
* **The Brain (Gemini API):** Handles decision-making, CV parsing, and form field mapping.
* **The Brawn (Playwright):** Handles the physical interaction with the web browser.
* **The Interface (Streamlit):** Provides a clean, local web dashboard to manage the process.

### Functional Block Diagram
1.  **Ingestion:** User uploads CV (PDF) -> AI converts to structured JSON.
2.  **Discovery:** Crawler scans LinkedIn/Social Media for keywords.
3.  **Filtering:** AI compares Job Description (JD) vs. CV JSON -> Calculates Match Score.
4.  **Action:** If Score > Threshold -> Playwright opens browser -> AI maps form fields -> Submits.

---

## 3. Deep Technical Components

### A. Intelligent CV Parsing
Instead of searching for keywords like "Python," the AI understands the **context** of your experience. 
* **Prompting Strategy:** The system sends your CV text to Gemini with instructions to output a "Personal Identity Map" which includes soft skills, technical expertise, and career level.

### B. The "Smart" Crawler
To avoid being banned by LinkedIn:
* **Stealth Browsing:** Uses `playwright-stealth` to hide the fact that the browser is automated.
* **Human-Like Interaction:** The bot scrolls through pages at varying speeds and moves the mouse cursor randomly.
* **Session Management:** The tool saves your browser "context" (cookies) locally so you don't have to log in every time.

### C. Adaptive Form Mapping
This is the "secret sauce." When the bot hits a job portal (e.g., Greenhouse, Lever, or Workday), it:
1.  Scrapes all `<label>` and `<input>` tags.
2.  Sends these tags to the AI.
3.  **AI Logic:** "Based on the user's CV, what is the correct value for the field labeled 'Total Years of Experience in Frontend'?"
4.  The bot enters the value and clicks "Submit."

---

## 4. Local Web App Features
* **Real-time Logs:** See exactly what the bot is doing (e.g., "Scanning job 4/10...", "High match found for Senior Dev...").
* **Manual Intervention Mode:** If the bot encounters a CAPTCHA or a complex question it can't answer, it pauses and alerts you via the web UI.
* **Application History:** A local SQLite database tracks every job title, company, and date applied to prevent duplicates.

---

## 5. Development Roadmap (The "How-To")

### Phase 1: Environment Setup
You will need to install the following core libraries:
```bash
pip install streamlit playwright google-generativeai python-dotenv beautifulsoup4
playwright install chromium

Phase 2: Building the Intelligence Layer
Create a utility script that interacts with the Gemini API to:

Extract text from PDF.

Compare JD and CV.

Generate custom answers for application questions.

Phase 3: The Automation Loop
Write the Playwright script that:

Navigates to LinkedIn.

Iterates through job cards.

Extracts the "Apply" link.

6. Security and Ethics
Local Storage: Your credentials and CV are stored only on your machine.

Ethical Scraping: Respect robots.txt where possible and implement a "cool-down" period between applications to avoid overwhelming job servers.

Accuracy: Always review the AI's generated cover letters in the "Manual Mode" during your first few runs.

7. Example Directory Structure
Plaintext
/automator_project
│
├── app.py              # The Streamlit Web App (Run this)
├── .env                # API Keys (GEMINI_API_KEY)
├── modules/
│   ├── ai_logic.py     # Gemini API calls
│   ├── scraper.py      # LinkedIn/Social Media crawler
│   └── browser.py      # Playwright automation scripts
└── data/
    ├── my_resume.pdf   # Your CV
    └── history.db      # SQLite tracking database
Created for a local, AI-driven development environment.
"""

with open("AI_Job_Automator_Full_Spec.md", "w") as f:
f.write(full_md_content)

Your detailed Markdown specification file for the AI Job Automator is ready. This version includes a deep dive into the system architecture, the "Adaptive Form Mapping" logic, and the technical roadmap for building it on your local machine.

[file-tag: code-generated-file-0-1777112243237792122]

### Key Sections in the Markdown:
* **System Architecture:** Details the "Brain and Brawn" approach using Gemini and Playwright.
* **Adaptive Form Mapping:** Explains how the AI identifies and fills out dynamic web forms by "reading" labels.
* **Development Roadmap:** Provides a step-by-step guide for setting up your environment and building the core modules.
* **Local Web App Features:** Outlines the Streamlit dashboard components like real-time logs and manual intervention mode.

Since you're using AI to build this, would you like me to generate a **starter `app.py` script** that integrates the Streamlit UI with a basic Playwright/Gemini workflow?