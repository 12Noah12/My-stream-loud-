import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# ---------------- USER TYPE SELECTION ----------------
if "user_type" not in st.session_state:
    st.session_state.user_type = None

if st.session_state.user_type is None:
    st.title("Welcome to FinAI! 💡")
    st.write("Please select your user type to see relevant tools:")
    col1, col2 = st.columns(2)
    if col1.button("👔 Business"):
        st.session_state.user_type = "business"
        st.experimental_rerun()
    if col2.button("🏠 Family"):
        st.session_state.user_type = "family"
        st.experimental_rerun()

# ---------------- FILTER PAGES ----------------
if st.session_state.user_type == "business":
    PAGES = {
        "home": "Home",
        "business_tax": "Business Tax Optimization",
        "investments": "Investments",
        "sme": "SME Dashboard",
        "estate": "Estate Planning",
        "premium": "Premium Modules"
    }
elif st.session_state.user_type == "family":
    PAGES = {
        "home": "Home",
        "family_tax": "Family Tax Optimization",
        "investments": "Investments",
        "estate": "Estate Planning",
        "premium": "Premium Modules"
    }

BG_STYLES = {
    "home": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
    "business_tax": "linear-gradient(135deg, #00c6ff 0%, #0072ff 100%)",
    "family_tax": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
    "investments": "linear-gradient(135deg, #f7971e 0%, #ffd200 100%)",
    "sme": "linear-gradient(135deg, #485563 0%, #29323c 100%)",
    "estate": "linear-gradient(135deg, #8e44ad 0%, #6c3483 100%)",
    "premium": "linear-gradient(135deg, #f7971e 0%, #ffd200 100%)"
}

SECTION_TEXT = {
    "home": "👋 Welcome to FinAI! Ask me anything below.",
    "business_tax": "💼 Optimize your business taxes efficiently.",
    "family_tax": "🏠 Optimize your family taxes with AI guidance.",
    "investments": "📈 Grow your wealth with AI-guided investments.",
    "sme": "🏢 Manage your business efficiently with our SME tools.",
    "estate": "⚖️ Plan your estate and inheritance smartly.",
    "premium": "🌟 Unlock powerful premium features here."
}

# ---------------- INIT STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------------- CSS ----------------
st.markdown("""
<style>
.block-container { padding-top: 6rem; }
.navbar {
  position: fixed; top: 0; left: 0; width: 100%;
  background: rgba(255,255,255,0.95); backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  padding: 0.7rem 1.5rem; display: flex; justify-content: space-between; align-items: center;
  z-index: 1000;
}
.navbar .logo { font-weight: 700; font-size: 1.2rem; color: #2563eb; }
.nav-links { display: flex; gap: 1rem; }
.nav-button button {
  background: none; border: none; font-weight: 600;
  padding: 0.3rem 0.8rem; border-radius: 6px; cursor: pointer; transition: background 0.3s;
}
.nav-button button:hover { background: rgba(37,99,235,0.1); }
.dots { cursor: pointer; font-size: 1.5rem; font-weight: bold; }
.dots:hover { color: #2563eb; }
body { color: white; }

.card { padding:1rem; margin:0.5rem 0; border-radius:12px; background: rgba(255,255,255,0.05); }

/* Home AI search bar styling */
.ai-search-container {
    display: flex; justify-content: center; margin-top: 3rem;
}
.ai-search-input {
    font-weight: 700; font-size: 1.3rem;
    border: 3px solid #2563eb;
    border-radius: 15px;
    padding: 1rem 2rem;
    width: 70%;
    text-align: center;
    box-shadow: 0 0 20px rgba(37,99,235,0.4);
    transition: box-shadow 0.3s, transform 0.3s;
}
.ai-search-input:focus {
    outline: none;
    box-shadow: 0 0 40px rgba(37,99,235,0.8);
    transform: scale(1.02);
    animation: glow 2s infinite;
}
@keyframes glow {
  0% { box-shadow: 0 0 20px rgba(37,99,235,0.4); }
  50% { box-shadow: 0 0 40px rgba(37,99,235,0.8); }
  100% { box-shadow: 0 0 20px rgba(37,99,235,0.4); }
}
</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ----------------
with st.container():
    nav_buttons_html = ""
    for k, v in PAGES.items():
        nav_buttons_html += f"""<span class="nav-button">
        <button onclick="window.parent.postMessage({{page: '{k}'}}, '*')">{v}</button>
        </span>"""
    st.markdown(f"""
    <div class="navbar">
        <div class="logo">💡 FinAI</div>
        <div class="nav-links">
            {nav_buttons_html}
        </div>
        <div class="dots">⋮</div>
    </div>
    """, unsafe_allow_html=True)

for key in PAGES.keys():
    if st.button(PAGES[key], key=f"btn-{key}"):
        st.session_state.page = key

st.markdown(f"""
<style>
body {{
    background: {BG_STYLES[st.session_state.page]};
    color: white;
}}
</style>
""", unsafe_allow_html=True)

st.title(PAGES[st.session_state.page])
st.write(SECTION_TEXT[st.session_state.page])

# ---------------- HOME PAGE ----------------
if st.session_state.page == "home":
    st.markdown('<div class="ai-search-container"><input class="ai-search-input" type="text" placeholder="🔍 Ask FinAI anything..."></div>', unsafe_allow_html=True)

# ---------------- BUSINESS TAX ----------------
# ... same as previous full code for business_tax, family_tax, investments, sme, estate, premium modules ...
# (use the code I provided earlier for all forms and calculations)

