import streamlit as st
import os
import json
import pandas as pd
from modules.database import init_db, add_application, get_applications, has_applied
from modules.scraper import get_job_description, discover_job_links

# Professional Page Config
st.set_page_config(
    page_title="Global Talent Finder",
    layout="wide",
    page_icon="💼",
    initial_sidebar_state="collapsed"
)

# Initialize Database
init_db()

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #0d1117;
        color: #e6edf3;
    }
    
    /* Card Styling */
    .job-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .job-card:hover {
        border-color: #3fb950;
        background: rgba(255, 255, 255, 0.08);
        transform: scale(1.02);
    }
    
    .job-title {
        font-size: 1rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.3;
    }
    
    .job-source {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: #3fb950;
        font-weight: 800;
        letter-spacing: 1px;
    }
    
    .job-link {
        color: #58a6ff;
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown('<h1 style="text-align: center; color: #3fb950; font-weight: 800; font-size: 3rem;">Global Talent Finder</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #8b949e; margin-bottom: 30px;">Relentless Real-time Discovery Engine</p>', unsafe_allow_html=True)

# Session state
if "discovered" not in st.session_state:
    st.session_state.discovered = []

tab1, tab2 = st.tabs(["🚀 Infinite Search Stream", "📁 Pipeline"])

with tab1:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        search_query = st.text_input("Unlimited Search", placeholder="e.g. Backend Developer", label_visibility="collapsed")
        start_btn = st.button("Initialize Infinite Scan", width="stretch")
    
    if start_btn:
        if search_query:
            st.session_state.discovered = []
            st.info(f"⚡ Starting Relentless Stream for: **{search_query}**")
            
            status = st.empty()
            # A dynamic container for the stream
            stream_container = st.container()
            
            # Step-by-step fetch
            count = 0
            for job in discover_job_links(search_query):
                st.session_state.discovered.append(job)
                count += 1
                status.markdown(f"📦 **Scanning Source & Paging Deeply...** Found {count} items.")
                
                # We update the UI for EVERY SINGLE ITEM
                with stream_container:
                    # To prevent drawing hundreds of items repeating, we only draw the NEW ones?
                    # Streamlit doesn't easily append to a list in a container without re-drawing everything.
                    # But we can show them in small groups to maintain performance.
                    if count % 3 == 0:
                        # Draw the last 3 in a row
                        latest = st.session_state.discovered[-3:]
                        cols = st.columns(3)
                        for i in range(3):
                            j = latest[i]
                            with cols[i]:
                                st.markdown(f"""
                                <div class="job-card">
                                    <div class="job-source">{j['source']}</div>
                                    <div class="job-title">{j['title'][:70]}</div>
                                    <a href="{j['url']}" target="_blank" class="job-link">Direct Access →</a>
                                </div>
                                """, unsafe_allow_html=True)
                                # Hidden save button to keep UI clean during stream
                                if st.button("Save", key=f"save_{count}_{i}"):
                                    add_application(j['title'], "Saved", j['url'], 100, "Interested")

        else:
            st.error("Please enter a query.")

with tab2:
    st.header("Search Intelligence & History")
    rows = get_applications()
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Job Title", "Pipeline State", "URL", "Score", "Status", "Timestamp"])
        st.dataframe(df, width=2000)
    else:
        st.info("Pipeline is empty.")
