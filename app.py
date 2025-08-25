import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# ---------------- SESSION STATE ----------------
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "ai_query" not in st.session_state:
    st.session_state.ai_query = ""

# ---------------- USER TYPE SELECTION ----------------
if st.session_state.user_type is None:
    st.title("Welcome to FinAI! 💡")
    st.write("Please select your user type to see relevant tools:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👔 Business"):
            st.session_state.user_type = "business"
            st.session_state.page = "home"
    
    with col2:
        if st.button("🏠 Family"):
            st.session_state.user_type = "family"
            st.session_state.page = "home"
    st.stop()  # Wait for selection

# ---------------- NAVIGATION PAGES ----------------
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

# ---------------- BACKGROUND STYLES ----------------
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

# ---------------- CSS ----------------
st.markdown("""
<style>
.block-container { padding-top: 6rem; }
.navbar { position: fixed; top: 0; left: 0; width: 100%; background: rgba(255,255,255,0.95); 
backdrop-filter: blur(10px); box-shadow: 0 2px 8px rgba(0,0,0,0.15); padding:0.7rem 1.5rem; 
display:flex; justify-content:space-between; align-items:center; z-index:1000; }
.navbar .logo { font-weight:700; font-size:1.2rem; color:#2563eb; }
.nav-links { display:flex; gap:1rem; }
.nav-button button { background:none; border:none; font-weight:600; padding:0.3rem 0.8rem;
border-radius:6px; cursor:pointer; transition: background 0.3s;}
.nav-button button:hover { background: rgba(37,99,235,0.1);}
.dots { cursor:pointer; font-size:1.5rem; font-weight:bold;}
body { color:white; }
.ai-search-container { display:flex; justify-content:center; margin-top:3rem; }
.ai-search-input { font-weight:700; font-size:1.3rem; border:3px solid #2563eb; border-radius:15px;
padding:1rem 1.5rem; width:60%; text-align:left; box-shadow:0 0 20px rgba(37,99,235,0.4);
transition: box-shadow 0.3s, transform 0.3s; }
.ai-search-button { margin-left: -45px; background:none; border:none; font-size:1.5rem; cursor:pointer;}
.ai-search-input:focus { outline:none; box-shadow:0 0 40px rgba(37,99,235,0.8); transform:scale(1.02);}
</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ----------------
nav_buttons_html = "".join([f"""<span class="nav-button">
<button onclick="window.parent.postMessage({{page: '{k}'}}, '*')">{v}</button>
</span>""" for k,v in PAGES.items()])
st.markdown(f"""
<div class="navbar">
    <div class="logo">💡 FinAI</div>
    <div class="nav-links">{nav_buttons_html}</div>
    <div class="dots">⋮</div>
</div>
""", unsafe_allow_html=True)

# ---------------- BACKGROUND ----------------
st.markdown(f"""
<style>
body {{ background: {BG_STYLES[st.session_state.page]}; color:white; }}
</style>
""", unsafe_allow_html=True)

# ---------------- PAGE TITLE ----------------
st.title(PAGES[st.session_state.page])
st.write(SECTION_TEXT[st.session_state.page])

# ---------------- HOME PAGE WITH FUNCTIONAL AI SEARCH ----------------
if st.session_state.page == "home":
    with st.form("ai_form"):
        query = st.text_input("🔍 Ask FinAI anything...", st.session_state.ai_query)
        submitted = st.form_submit_button("Submit")
        if submitted and query:
            st.session_state.ai_query = query
            st.success(f"You asked: {query}")

# ---------------- BUSINESS TAX OPTIMIZATION ----------------
if st.session_state.page == "business_tax":
    st.subheader("Business Tax Optimization Calculator")
    revenue = st.number_input("Annual Revenue (R)", min_value=0.0, value=100000.0, help="Total revenue for the year")
    expenses = st.number_input("Total Expenses (R)", min_value=0.0, value=50000.0, help="Deductible business expenses")
    profit = revenue - expenses
    st.write(f"**Profit:** R{profit:,.2f}")
    tax_rate = 0.28 if profit > 1000000 else 0.0
    tax_payable = profit * tax_rate
    st.write(f"**Estimated Tax Payable:** R{tax_payable:,.2f} at {tax_rate*100}% rate")

# ---------------- FAMILY TAX OPTIMIZATION ----------------
if st.session_state.page == "family_tax":
    st.subheader("Family Tax Optimization Calculator")
    salary = st.number_input("Annual Salary (R)", min_value=0.0, value=350000.0)
    other_income = st.number_input("Other Income (R)", min_value=0.0, value=0.0)
    deductions = st.number_input("Deductions (R)", min_value=0.0, value=15000.0)
    taxable_income = max(0, salary + other_income - deductions)
    brackets = [(0, 237100, 0.18, 0),
                (237101, 370500, 0.26, 42678),
                (370501, 512800, 0.31, 77362),
                (512801, 673000, 0.36, 121910),
                (673001, 857900, 0.39, 179258),
                (857901, 1817000, 0.41, 251258),
                (1817001, np.inf, 0.45, 644489)]
    tax_owed = 0
    for low, high, rate, base in brackets:
        if taxable_income >= low and taxable_income <= high:
            tax_owed = base + (taxable_income - low) * rate
            break
    st.write(f"**Taxable Income:** R{taxable_income:,.2f}")
    st.write(f"**Estimated Tax Owed:** R{tax_owed:,.2f}")

# ---------------- INVESTMENTS ----------------
if st.session_state.page == "investments":
    st.subheader("Investment Growth Simulator")
    principal = st.number_input("Initial Investment (R)", min_value=0.0, value=100000.0)
    monthly = st.number_input("Monthly Contribution (R)", min_value=0.0, value=2000.0)
    years = st.number_input("Years", min_value=1, value=10)
    risk = st.selectbox("Risk Profile", ["Conservative (5%)", "Moderate (7%)", "Aggressive (10%)"])
    rate_map = {"Conservative (5%)":0.05, "Moderate (7%)":0.07, "Aggressive (10%)":0.10}
    rate = rate_map[risk]
    months = years*12
    balance = []
    total = principal
    for m in range(months):
        total = total*(1+rate/12) + monthly
        balance.append(total)
    df = pd.DataFrame({"Month": list(range(1, months+1)), "Balance": balance})
    fig = px.line(df, x="Month", y="Balance", title="Projected Investment Growth")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- SME DASHBOARD ----------------
if st.session_state.page == "sme" and st.session_state.user_type=="business":
    st.subheader("SME Dashboard")
    employees = st.number_input("Number of Employees", min_value=0, value=5)
    revenue = st.number_input("Monthly Revenue (R)", min_value=0.0, value=50000.0)
    expenses = st.number_input("Monthly Expenses (R)", min_value=0.0, value=30000.0)
    profit = revenue - expenses
    st.write(f"**Monthly Profit:** R{profit:,.2f}")

# ---------------- ESTATE PLANNING ----------------
if st.session_state.page == "estate":
    st.subheader("Estate Planning Calculator")
    estate_value = st.number_input("Total Estate Value (R)", min_value=0.0, value=2000000.0)
    heirs = st.number_input("Number of Heirs", min_value=1, value=2)
    inheritance_per_heir = estate_value/heirs
    st.write(f"**Each heir receives:** R{inheritance_per_heir:,.2f}")

# ---------------- PREMIUM MODULES ----------------
if st.session_state.page == "premium":
    st.subheader("Premium AI Modules")
    st.write("Advanced analytics, predictive simulations, and professional reporting included here.")
