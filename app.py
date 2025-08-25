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

/* Navbar */
.navbar { position: fixed; top: 0; left: 0; width: 100%; background: rgba(255,255,255,0.95);
backdrop-filter: blur(10px); box-shadow: 0 2px 8px rgba(0,0,0,0.15); padding:0.7rem 1.5rem;
display:flex; justify-content:space-between; align-items:center; z-index:1000; }
.navbar .logo { font-weight:700; font-size:1.2rem; color:#2563eb; }
.nav-links { display:flex; gap:1rem; }
.nav-button button { background:none; border:none; font-weight:600; padding:0.3rem 0.8rem;
border-radius:6px; cursor:pointer; transition: background 0.3s;}
.nav-button button:hover { background: rgba(37,99,235,0.1);}

/* AI Search */
.ai-search-container { display:flex; justify-content:center; margin-top:3rem; position:relative; }
.ai-search-input { font-weight:700; font-size:1.3rem; border:3px solid #2563eb; border-radius:15px;
padding:1rem 1.5rem; width:60%; text-align:left; transition: box-shadow 0.3s, transform 0.3s; }
.ai-search-button { position:absolute; right:18%; top:12px; background:none; border:none; font-size:1.5rem; cursor:pointer; color:#2563eb; }

/* Glow effect animation */
@keyframes glow { 0% { box-shadow: 0 0 15px rgba(37,99,235,0.5);} 50% { box-shadow: 0 0 40px rgba(37,99,235,0.9);} 100% { box-shadow: 0 0 15px rgba(37,99,235,0.5);} }
.ai-search-input.glow:focus { animation: glow 1.5s infinite; transform: scale(1.02); outline:none; }

/* Cards */
.input-card { background: rgba(255,255,255,0.05); padding:20px; border-radius:15px; margin-bottom:15px; }
.recommendation-card { background: rgba(0,0,0,0.4); padding:20px; border-radius:15px; margin-top:15px; color:#fff; }

/* Layout sections */
.section { margin-top:30px; padding:15px; border-radius:15px; background: rgba(255,255,255,0.05); }
</style>
""", unsafe_allow_html=True)

# ---------------- USER TYPE SELECTION ----------------
def select_user_type():
    st.markdown("<h2 style='text-align:center;'>Select Your User Type:</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👤 Individual"):
            st.session_state.user_type = "individual"
            st.session_state.page = "home"
    with col2:
        if st.button("🏠 Family"):
            st.session_state.user_type = "family"
            st.session_state.page = "home"
    with col3:
        if st.button("👔 Business/Corporate"):
            st.session_state.user_type = "business"
            st.session_state.page = "home"
    if st.session_state.user_type is None:
        st.stop()

# ---------------- PAGES ----------------
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
    elif st.session_state.user_type == "individual":
        return {
            "home": "Home",
            "personal_finance": "Personal Finance Advice",
            "investments": "Investments",
            "estate": "Estate Planning",
            "premium": "Premium Modules"
        }
    else:
        return {}

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
        query = st.text_input(
            "", st.session_state.ai_query,
            placeholder="🔍 Ask FinAI for personalized financial advice...",
            key="ai_input",
            label_visibility="collapsed",
            help="Type anything related to taxes, investments, or financial planning."
        )
        submitted = st.form_submit_button("🔍")
        if submitted and query:
            st.session_state.ai_query = query.lower()
            pages = get_pages()
            redirected = False

            # Smart AI keyword matching
            tax_keywords = ["tax", "deduction", "irs", "income"]
            invest_keywords = ["invest", "portfolio", "stocks", "funds"]
            sme_keywords = ["sme", "business", "company", "enterprise"]
            estate_keywords = ["estate", "inheritance", "will", "legacy"]
            personal_keywords = ["personal", "individual", "savings", "budget"]

            if any(k in query for k in tax_keywords):
                if st.session_state.user_type == "business" and "business_tax" in pages:
                    st.session_state.page = "business_tax"
                    redirected = True
                elif st.session_state.user_type == "family" and "family_tax" in pages:
                    st.session_state.page = "family_tax"
                    redirected = True
            elif any(k in query for k in invest_keywords) and "investments" in pages:
                st.session_state.page = "investments"
                redirected = True
            elif any(k in query for k in sme_keywords) and "sme" in pages:
                st.session_state.page = "sme"
                redirected = True
            elif any(k in query for k in estate_keywords) and "estate" in pages:
                st.session_state.page = "estate"
                redirected = True
            elif any(k in query for k in personal_keywords) and "personal_finance" in pages:
                st.session_state.page = "personal_finance"
                redirected = True

            if not redirected:
                st.warning("AI could not detect the topic. Try terms like 'tax', 'investment', 'SME', 'estate', or 'personal finance'.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def parse_float_input(text, default=0.0):
    try:
        return float(text)
    except:
        return default

def recommendation_card(title, recommendations):
    rec_html = f'<div class="recommendation-card"><b>{title}</b><br>'
    for rec in recommendations:
        rec_html += f'- {rec}<br>'
    rec_html += '</div>'
    st.markdown(rec_html, unsafe_allow_html=True)

# ---------------- MODULES ----------------
def show_home():
    st.markdown("### Welcome to FinAI! 💡")
    st.write("Use the AI search bar above or select modules below.")

def show_business_tax():
    st.subheader("Business Tax Optimization")
    revenue = parse_float_input(st.text_input("Annual Revenue (R)", "0", help="Total revenue"))
    expenses = parse_float_input(st.text_input("Total Expenses (R)", "0", help="Deductible expenses"))
    profit = revenue - expenses
    st.write(f"Profit: R{profit:,.2f}")
    tax_rate = 0.28 if profit > 1000000 else 0.15
    tax_payable = profit*tax_rate
    st.write(f"Estimated Tax Payable: R{tax_payable:,.2f} ({tax_rate*100}%)")

    recommendation_card("Recommendations", [
        "Track expenses digitally to maximize deductions",
        "Explore SME tax incentives and rebates",
        "Reinvest profits to reduce taxable income"
    ])

def show_family_tax():
    st.subheader("Family Tax Optimization")
    salary = parse_float_input(st.text_input("Annual Salary (R)", "0"))
    investment_income = parse_float_input(st.text_input("Investment Income (R)", "0"))
    deductions = parse_float_input(st.text_input("Tax Deductions (R)", "0"))
    credits = parse_float_input(st.text_input("Tax Credits (R)", "0"))
    taxable_income = salary + investment_income - deductions
    tax_owed = max(taxable_income*0.18 - credits, 0)
    st.write(f"Estimated Tax Owed: R{tax_owed:,.2f}")

    recommendation_card("Recommendations", [
        "Maximize retirement contributions",
        "Claim eligible medical and educational deductions",
        "Consider tax-free investments to reduce taxable income"
    ])

def show_personal_finance():
    st.subheader("Personal Finance Advice")
    income = parse_float_input(st.text_input("Monthly Income (R)", "0"))
    expenses = parse_float_input(st.text_input("Monthly Expenses (R)", "0"))
    savings = income - expenses
    st.write(f"Monthly Savings: R{savings:,.2f}")

    recommendation_card("Recommendations", [
        "Allocate 50% to essentials, 30% to savings/investments, 20% to leisure",
        "Open tax-free savings accounts",
        "Automate monthly investments in index funds"
    ])

def show_sme():
    st.subheader("SME Dashboard")
    num_employees = parse_float_input(st.text_input("Number of Employees", "0"))
    monthly_expenses = parse_float_input(st.text_input("Monthly Expenses (R)", "0"))
    st.write(f"Employees: {num_employees}, Expenses: R{monthly_expenses:,.2f}")

def show_investments():
    st.subheader("Investment Dashboard")
    investment_amount = parse_float_input(st.text_input("Investment Amount (R)", "0"))
    st.write(f"Investing: R{investment_amount:,.2f}")
    # Example portfolio chart
    df = pd.DataFrame({
        "Asset": ["Stocks", "Bonds", "Real Estate", "Cash"],
        "Allocation": [0.5, 0.2, 0.2, 0.1]
    })
    fig = px.pie(df, names="Asset", values="Allocation", title="Portfolio Allocation")
    st.plotly_chart(fig, use_container_width=True)

def show_estate():
    st.subheader("Estate Planning")
    net_worth = parse_float_input(st.text_input("Net Worth (R)", "0"))
    st.write(f"Net Worth: R{net_worth:,.2f}")
    recommendation_card("Recommendations", [
        "Create a will and assign beneficiaries",
        "Consider trusts for tax efficiency",
        "Review estate regularly for changes"
    ])

def show_premium():
    st.subheader("Premium AI Modules")
    st.write("Coming soon: advanced predictive analytics and wealth optimization AI")

# ---------------- MAIN ----------------
select_user_type()
pages = get_pages()
show_navbar(pages)
ai_search()

# Render selected page
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "business_tax":
    show_business_tax()
elif st.session_state.page == "family_tax":
    show_family_tax()
elif st.session_state.page == "personal_finance":
    show_personal_finance()
elif st.session_state.page == "sme":
    show_sme()
elif st.session_state.page == "investments":
    show_investments()
elif st.session_state.page == "estate":
    show_estate()
elif st.session_state.page == "premium":
    show_premium()
