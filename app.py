# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from urllib.parse import quote

# =========================
# Config
# =========================
st.set_page_config(
    page_title="FinAI - AI Financial Platform",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# OpenAI client
# =========================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except KeyError:
    st.error("OpenAI API key not found! Add it to Streamlit Cloud Secrets as OPENAI_API_KEY.")
    st.stop()

# =========================
# Pages / Routing
# =========================
PAGES = ["Home", "Tax Optimization", "Investments", "SME Dashboard", "Premium Modules"]

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "premium" not in st.session_state:
    st.session_state.premium = False

# Sync with query params (so the fixed HTML menu can navigate by URL)
params = st.experimental_get_query_params()
if "page" in params and params["page"]:
    candidate = params["page"][0]
    if candidate in PAGES and candidate != st.session_state.page:
        st.session_state.page = candidate

current_page = st.session_state.page

# =========================
# Styles (Modern UI + Custom Fixed Sidebar)
# =========================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

:root {
  --brand:#2563EB;
  --brand-dark:#1D4ED8;
  --ink:#1F2937;
  --muted:#6B7280;
  --card:#ffffff;
  --bg:#F3F4F6;
  --radius:16px;
  --shadow: 0 8px 20px rgba(0,0,0,0.08);
  --shadow-lg: 0 12px 25px rgba(0,0,0,0.15);
}

/* Global */
html, body, [class*="css"]  { font-family: 'Inter', sans-serif !important; color: var(--ink); }
h1,h2,h3,h4,h5 { font-family: 'Inter', sans-serif; }

/* Make main area account for fixed sidebar width */
.main .block-container{
  padding-top: 1.5rem;
  padding-bottom: 2rem;
  margin-left: 300px; /* matches sidebar width + gap */
  max-width: 1200px;
}

/* Custom fixed sidebar */
.finai-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 280px;
  background: var(--card);
  box-shadow: var(--shadow);
  padding: 18px 16px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-right: 1px solid #E5E7EB;
}

.finai-logo {
  display: flex; 
  align-items: center; 
  gap: 10px; 
  padding: 12px; 
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(37,99,235,0.08), rgba(29,78,216,0.0
