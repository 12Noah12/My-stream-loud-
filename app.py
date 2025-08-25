import streamlit as st
import pandas as pd
import numpy as np
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

.ai-search-container { display:flex; justify-content:center; margin-top:3rem; position:relative; }
.ai-search-input { font-weight:700; font-size:1.3rem; border:3px solid #2563eb; border-radius:15px;
padding:1rem 1.5rem; width:60%; text-align:left; box-shadow:0 0 20px rgba(37,99,235,0.4);
transition: box-shadow 0.3s, transform 0.3s; }
.ai-search-button { position:absolute; right:18%; top:12px; background:none; border:none; font-size:1.5rem; cursor:pointer; color:#2563eb; }

.ai-search-input:focus { outline:none; box-shadow:0 0 40px rgba(37,99,235,0.8); transform:scale(1.02);}
@keyframes glow {
    0% { box-shadow: 0 0 15px rgba(37,99,235,0.5);}
    50% { box-shadow: 0 0 40px rgba(37,99,235,0.9);}
    100% { box-shadow: 0 0 15px rgba(37,99,235,0.5);}
}
.glow { animation: glow 2s infinite; }

</style>
""", unsafe_allow_html=True)

# ---------------- USER TYPE SELECTION ----------------
def select_user_type():
    st.markdown("<h2 style='text-align:center;'>Please select your user type:</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👔 Business"):
            st.session_state.user_type = "business"
            st.session_state.page = "home"
    with col2:
        if st.button("🏠 Family"):
            st.session_state.user_type = "family"
            st.session_state.page = "home"
    if st.session_state.user_type is None:
        st.stop()

# ---------------- PAGE DICTIONARY ----------------
def get_pages():
    if st.session_state.user_type == "business":
        return {
            "home": "Home",
            "business_tax": "Business Tax Optimization",
            "investments": "Investments",
            "sme": "SME Dashboard",
            "estate": "Estate Planning",
            "premium": "Premium Modules"
        }
    elif st.session_state.user_type == "family":
        return {
            "home": "Home",
            "family_tax": "Family Tax Optimization",
            "investments": "Investments",
            "estate": "Estate Planning",
            "premium": "Premium Modules"
        }
    else:
        return None

# ---------------- NAVBAR ----------------
def show_navbar(pages):
    if not pages:
        return
    cols = st.columns(len(pages))
    for idx, (key, name) in enumerate(pages.items()):
        with cols[idx]:
            if st.button(name):
                st.session_state.page = key

# ---------------- AI SEARCH ----------------
def ai_search():
    st.markdown('<div class="ai-search-container">', unsafe_allow_html=True)
    with st.form("ai_form"):
        query = st.text_input("", st.session_state.ai_query, placeholder="🔍 Ask FinAI anything...", key="ai_input", label_visibility="collapsed")
        submitted = st.form_submit_button("🔍")
        if submitted and query:
            st.session_state.ai_query = query.lower()
            pages = get_pages()
            keyword_map = {
                "business_tax": ["business tax", "tax optimization", "tax"],
                "family_tax": ["family tax", "deduction", "family"],
                "investments": ["investment", "invest", "portfolio"],
                "sme": ["sme", "small business", "enterprise"],
                "estate": ["estate", "inheritance", "will"],
                "premium": ["premium", "advanced", "analytics"]
            }
            redirected = False
            for page_key, keywords in keyword_map.items():
                if any(k in st.session_state.ai_query for k in keywords) and pages and page_key in pages:
                    st.session_state.page = page_key
                    redirected = True
                    break
            if not redirected:
                st.warning("No matching module found. Try keywords like 'tax', 'investment', 'SME', 'estate', 'premium'.")
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- PAGE FUNCTIONS ----------------
def show_home():
    st.markdown("### Welcome to FinAI! 💡")
    st.write("Use the AI search bar above to navigate or select modules below.")

def show_business_tax():
    st.subheader("Business Tax Optimization")
    revenue = st.number_input("Annual Revenue (R)", 0.0, 1000000.0, help="Total revenue for the year")
    expenses = st.number_input("Total Expenses (R)", 0.0, 500000.0, help="Deductible business expenses")
    profit = revenue - expenses
    st.write(f"Profit: R{profit:,.2f}")
    tax_rate = 0.28 if profit > 1000000 else 0.15
    st.write(f"Estimated Tax Payable: R{profit*tax_rate:,.2f} at {tax_rate*100}% rate")

def show_family_tax():
    st.subheader("Family Tax Optimization")
    salary = st.number_input("Annual Salary (R)", 0.0, 2000000.0)
    other_income = st.number_input("Other Income (R)", 0.0, 500000.0)
    deductions = st.number_input("Deductions (R)", 0.0, 150000.0)
    taxable_income = max(0, salary + other_income - deductions)
    st.write(f"Taxable Income: R{taxable_income:,.2f}")
    st.write(f"Estimated Tax Owed: R{taxable_income*0.25:,.2f}")  # flat 25%

def show_sme():
    st.subheader("SME Dashboard")
    employees = st.number_input("Number of Employees", 0, 1000, 10)
    avg_salary = st.number_input("Average Monthly Salary (R)", 0.0, 20000.0)
    monthly_expense = employees * avg_salary
    st.write(f"Total Monthly Payroll: R{monthly_expense:,.2f}")
    st.write(f"Annual Payroll: R{monthly_expense*12:,.2f}")

def show_investments():
    st.subheader("Investment Growth Simulator")
    principal = st.number_input("Initial Investment (R)", 0.0, 1000000.0)
    monthly = st.number_input("Monthly Contribution (R)", 0.0, 50000.0)
    years = st.number_input("Investment Period (Years)", 1, 50, 10)
    rate = st.slider("Expected Annual Return (%)", 0.0, 20.0, 7.0)/100
    months = years*12
    balances = []
    balance = principal
    for m in range(1, months+1):
        balance += monthly
        balance *= (1 + rate/12)
        balances.append(balance)
    df_inv = pd.DataFrame({"Month": list(range(1, months+1)), "Balance": balances})
    fig = px.line(df_inv, x="Month", y="Balance", title="Investment Growth Over Time")
    st.plotly_chart(fig, use_container_width=True)

def show_estate():
    st.subheader("Estate Planning")
    estate_value = st.number_input("Total Estate Value (R)", 0.0, 5000000.0)
    heirs = st.number_input("Number of Heirs", 1, 50, 2)
    st.write(f"Estimated Amount per Heir: R{estate_value/heirs:,.2f}")

def show_premium():
    st.subheader("Premium Modules")
    st.write("Advanced analytics, AI-driven recommendations, charts, and simulations.")

# ---------------- MAIN ----------------
if st.session_state.user_type is None:
    select_user_type()

pages = get_pages()
show_navbar(pages)
ai_search()

if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "business_tax":
    show_business_tax()
elif st.session_state.page == "family_tax":
    show_family_tax()
elif st.session_state.page == "investments":
    show_investments()
elif st.session_state.page == "sme":
    show_sme()
elif st.session_state.page == "estate":
    show_estate()
elif st.session_state.page == "premium":
    show_premium()
