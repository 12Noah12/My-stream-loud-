import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="FinAI",
    page_icon="💡",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "user_type" not in st.session_state:
    st.session_state.user_type = None

if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False

# ---------------- CSS / STYLING ----------------
st.markdown("""
<style>
.block-container { padding-top: 4rem; }
.navbar {
  position: fixed; top: 0; left: 0;
  width: 100%; background: rgba(255,255,255,0.95);
  backdrop-filter: blur(10px); box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  padding: 0.7rem 1.5rem; display: flex; justify-content: space-between;
  align-items: center; z-index: 1000;
}
.navbar .logo { font-weight: 700; font-size: 1.2rem; color: #2563eb; }
.nav-links { display: flex; gap: 1rem; }
.nav-button button {
  background: none; border: none; font-weight: 600;
  padding: 0.3rem 0.8rem; border-radius: 6px; cursor: pointer;
  transition: background 0.3s;
}
.nav-button button:hover { background: rgba(37,99,235,0.1); }
.ai-search {
  display: flex; justify-content: center; margin-top: 3rem;
}
.ai-search input {
  font-weight: 700; font-size: 1.1rem;
  border: 2px solid #2563eb;
  border-radius: 12px; padding: 0.8rem 1.2rem;
  width: 60%; text-align: center;
  box-shadow: 0 0 12px rgba(37,99,235,0.3);
  animation: pulse 2s infinite;
}
.ai-search input:focus {
  outline: none;
  box-shadow: 0 0 20px rgba(37,99,235,0.6);
}
@keyframes pulse {
  0% { box-shadow: 0 0 10px rgba(37,99,235,0.5); }
  50% { box-shadow: 0 0 20px rgba(37,99,235,0.9); }
  100% { box-shadow: 0 0 10px rgba(37,99,235,0.5); }
}
.card {
    background: rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
}
.card h4 { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------------- NAVIGATION ----------------
def show_navbar():
    pages = ["Home", "Individual", "Family", "Business/SME", "Investments", "Estate", "Premium"]
    st.markdown(f"""
    <div class="navbar">
        <div class="logo">💡 FinAI</div>
        <div class="nav-links">
            {''.join([f'<span class="nav-button"><button onclick="window.parent.postMessage({{page: \'{p}\' }}, \'*\')">{p}</button></span>' for p in pages])}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------- HELPER FUNCTIONS ----------------
def parse_float_input(val):
    try:
        return float(val.replace(",", "")) if val else 0
    except:
        return 0

def recommendation_card(title, items):
    st.markdown(f"<div class='card'><h4>{title}</h4>", unsafe_allow_html=True)
    for item in items:
        st.markdown(f"- {item}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- PRIVACY AGREEMENT ----------------
def show_privacy_agreement():
    st.subheader("Privacy & Liability Agreement")
    st.write("""
    By using this tool, you acknowledge that all information entered is for illustrative purposes only.
    FinAI and its affiliates are **not responsible for decisions made based on this data**.
    No data entered is stored or shared.
    """)
    if st.checkbox("I accept the privacy agreement"):
        st.session_state.privacy_accepted = True

# ---------------- AI SEARCH ----------------
def ai_search():
    query = st.text_input("🔍 Ask FinAI anything...", "")
    if st.button("Go") or st.session_state.get("ai_submit", False):
        st.session_state.ai_submit = False
        # Intent detection
        q = query.lower()
        if "business" in q or "sme" in q:
            st.session_state.page = "Business/SME"
        elif "family" in q or "household" in q:
            st.session_state.page = "Family"
        elif "individual" in q or "personal" in q:
            st.session_state.page = "Individual"
        elif "investment" in q:
            st.session_state.page = "Investments"
        elif "estate" in q or "inheritance" in q:
            st.session_state.page = "Estate"
        else:
            st.session_state.page = "Individual"
        st.experimental_rerun()

# ---------------- SELECT USER TYPE ----------------
def select_user_type():
    st.subheader("Select your category")
    cols = st.columns(3)
    if cols[0].button("Individual"):
        st.session_state.page = "Individual"
    if cols[1].button("Family"):
        st.session_state.page = "Family"
    if cols[2].button("Business / SME"):
        st.session_state.page = "Business/Corporate"

# ---------------- PAGES ----------------
def show_home():
    st.title("Welcome to FinAI")
    st.markdown("Your intelligent financial assistant.")
    ai_search()
    select_user_type()

def show_individual():
    st.subheader("Personal Finance & Tax")
    income = parse_float_input(st.text_input("Monthly Income (R)", "0"))
    investments = parse_float_input(st.text_input("Monthly Investment Income (R)", "0"))
    deductions = parse_float_input(st.text_input("Monthly Deductions (R)", "0"))
    credits = parse_float_input(st.text_input("Tax Credits (R)", "0"))
    taxable = income + investments - deductions
    tax_owed = max(taxable * 0.18 - credits, 0)
    st.write(f"Estimated Tax Owed: R{tax_owed:,.2f}")
    recommendation_card("Suggestions (partial tips — contact us for full strategy)", [
        "Maximize retirement contributions",
        "Use tax-free savings accounts",
        "Review insurance and deductions for optimization"
    ])

def show_family():
    st.subheader("Family Finance & Tax")
    salary = parse_float_input(st.text_input("Combined Monthly Household Income (R)", "0"))
    investment_income = parse_float_input(st.text_input("Combined Investment Income (R)", "0"))
    deductions = parse_float_input(st.text_input("Existing Deductions (R)", "0"))
    credits = parse_float_input(st.text_input("Tax Credits (R)", "0"))
    taxable_income = salary + investment_income - deductions
    tax_owed = max(taxable_income * 0.18 - credits, 0)
    st.write(f"Estimated Tax Owed: R{tax_owed:,.2f}")
    recommendation_card("Suggestions (partial tips — contact us for full strategy)", [
        "Maximize household tax-free investments",
        "Track medical and educational deductions",
        "Consider joint retirement contributions"
    ])

def show_business():
    st.subheader("Business / SME Dashboard")
    revenue = parse_float_input(st.text_input("Monthly Revenue (R)", "0"))
    expenses = parse_float_input(st.text_input("Monthly Expenses (R)", "0"))
    employees = parse_float_input(st.text_input("Number of Employees", "0"))
    current_deductions = parse_float_input(st.text_input("Current Tax Deductions (R)", "0"))
    taxable = revenue - expenses - current_deductions
    tax_owed = max(taxable * 0.28, 0)  # simplified corporate tax
    st.write(f"Estimated Tax Owed: R{tax_owed:,.2f}")
    potential_savings = 0.1 * expenses
    st.write(f"Potential Savings (illustrative): R{potential_savings:,.2f}")
    recommendation_card("Suggestions (partial tips — contact us for full strategy)", [
        "Run business expenses through corporate accounts strategically",
        "Review deductible operational costs",
        "Consider reinvestment options to optimize tax obligations"
    ])

def show_investments():
    st.subheader("Investment Dashboard")
    invest_amount = parse_float_input(st.text_input("Investment Amount (R)", "0"))
    risk_level = st.selectbox("Risk Appetite", ["Conservative", "Balanced", "Aggressive"])
    df = pd.DataFrame({
        "Asset": ["Stocks", "Bonds", "Real Estate", "Cash"],
        "Allocation": [0.5, 0.2, 0.2, 0.1]
    })
    fig = px.pie(df, names="Asset", values="Allocation", title="Sample Portfolio Allocation")
    st.plotly_chart(fig, use_container_width=True)
    recommendation_card("Investment Suggestions (partial)", [
        "Diversify portfolio based on risk level",
        "Consider tax-free investments for long-term savings",
        "Rebalance portfolio periodically"
    ])

def show_estate():
    st.subheader("Estate Planning")
    net_worth = parse_float_input(st.text_input("Net Worth (R)", "0"))
    liabilities = parse_float_input(st.text_input("Liabilities (R)", "0"))
    st.write(f"Net Estate Value: R{net_worth - liabilities:,.2f}")
    recommendation_card("Suggestions (partial)", [
        "Create a will and assign beneficiaries",
        "Consider trusts for efficiency",
        "Regularly review estate plans"
    ])

def show_premium():
    st.subheader("Premium AI Modules")
    st.write("Advanced predictive analytics and wealth optimization available upon contact.")

# ---------------- MAIN ----------------
show_privacy_agreement()
if st.session_state.privacy_accepted:
    show_navbar()
    page = st.session_state.page
    if page == "home":
        show_home()
    elif page == "Individual":
        show_individual()
    elif page == "Family":
        show_family()
    elif page == "Business/SME":
        show_business()
    elif page == "Investments":
        show_investments()
    elif page == "Estate":
        show_estate()
    elif page == "Premium":
        show_premium()
