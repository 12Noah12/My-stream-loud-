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
    st.markdown(f"""
    <div class="navbar">
        <div class="logo">💡 FinAI</div>
        <div class="nav-links">
            {''.join([f'<span class="nav-button"><button onclick="window.parent.postMessage({{page: \'{k}\' }}, \'*\')">{v}</button></span>' for k,v in PAGES.items()])}
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
if st.session_state.page == "business_tax":
    st.header("Business Tax Optimization 💼")
    for var in ["revenue","expenses","deductions","vat_paid","tax_owed"]:
        if var not in st.session_state:
            st.session_state[var] = 0
    with st.form("business_tax_form"):
        st.session_state.revenue = st.number_input("Revenue ($)", value=st.session_state.revenue, min_value=0, help="Total revenue generated by the business")
        st.session_state.expenses = st.number_input("Expenses ($)", value=st.session_state.expenses, min_value=0, help="Operational costs of the business")
        st.session_state.deductions = st.number_input("Deductions ($)", value=st.session_state.deductions, min_value=0, help="Tax-deductible expenses")
        st.session_state.vat_paid = st.number_input("VAT Paid ($)", value=st.session_state.vat_paid, min_value=0, help="VAT already paid to authorities")
        submit_business_tax = st.form_submit_button("Calculate Tax")
    if submit_business_tax:
        st.session_state.tax_owed = max(0, (st.session_state.revenue - st.session_state.expenses - st.session_state.deductions) * 0.28)
        st.success(f"Estimated Business Tax Owed: ${st.session_state.tax_owed:,.2f}")

# ---------------- FAMILY TAX ----------------
if st.session_state.page == "family_tax":
    st.header("Family Tax Optimization 💰")
    for var in ["salary","investment_income","deductions","tax_credits","tax_owed"]:
        if var not in st.session_state:
            st.session_state[var] = 0
    with st.form("family_tax_form"):
        st.session_state.salary = st.number_input("Salary ($)", value=st.session_state.salary, min_value=0, help="Your total annual income from salary")
        st.session_state.investment_income = st.number_input("Investment Income ($)", value=st.session_state.investment_income, min_value=0, help="Income from investments, dividends, etc.")
        st.session_state.deductions = st.number_input("Deductions ($)", value=st.session_state.deductions, min_value=0, help="Total tax-deductible expenses")
        st.session_state.tax_credits = st.number_input("Tax Credits ($)", value=st.session_state.tax_credits, min_value=0, help="Eligible credits for children, education, etc.")
        submit_family_tax = st.form_submit_button("Calculate Tax")
    if submit_family_tax:
        taxable_income = st.session_state.salary + st.session_state.investment_income - st.session_state.deductions
        st.session_state.tax_owed = max(0, taxable_income * 0.25 - st.session_state.tax_credits)
        st.success(f"Estimated Tax Owed: ${st.session_state.tax_owed:,.2f}")

# ---------------- INVESTMENTS ----------------
if st.session_state.page == "investments":
    st.header("Investments Dashboard 📈")
    for var in ["initial_investment","monthly_contribution","expected_return","years"]:
        if var not in st.session_state:
            st.session_state[var] = 0
    with st.form("investments_form"):
        st.session_state.initial_investment = st.number_input("Initial Investment ($)", value=st.session_state.initial_investment, min_value=0, help="Amount you start investing with")
        st.session_state.monthly_contribution = st.number_input("Monthly Contribution ($)", value=st.session_state.monthly_contribution, min_value=0, help="Monthly amount you plan to invest")
        st.session_state.expected_return = st.number_input("Expected Annual Return (%)", value=st.session_state.expected_return, min_value=0.0, help="Expected yearly return rate of your investments")
        st.session_state.years = st.number_input("Years to Invest", value=st.session_state.years, min_value=1, help="Number of years you plan to invest")
        submit_investments = st.form_submit_button("Run Simulation")
    if submit_investments:
        ending_balances = []
        for i in range(1000):
            balance = st.session_state.initial_investment
            for _ in range(st.session_state.years):
                balance = balance*(1 + np.random.normal(st.session_state.expected_return/100,0.05)) + st.session_state.monthly_contribution*12
            ending_balances.append(balance)
        st.success(f"Projected Portfolio Value (mean of 1000 sims): ${np.mean(ending_balances):,.2f}")
        fig = px.histogram(ending_balances, nbins=50, title="Monte Carlo Portfolio Distribution")
        st.plotly_chart(fig)

# ---------------- SME DASHBOARD ----------------
if st.session_state.page == "sme":
    st.header("SME Dashboard 🏢")
    for var in ["revenue","expenses","marketing","operations","profit"]:
        if var not in st.session_state:
            st.session_state[var] = 0
    with st.form("sme_form"):
        st.session_state.revenue = st.number_input("Revenue ($)", value=st.session_state.revenue, min_value=0, help="Total business revenue")
        st.session_state.expenses = st.number_input("Expenses ($)", value=st.session_state.expenses, min_value=0, help="Operational expenses")
        st.session_state.marketing = st.number_input("Marketing Expenses ($)", value=st.session_state.marketing, min_value=0, help="Marketing & advertising spend")
        st.session_state.operations = st.number_input("Operations Expenses ($)", value=st.session_state.operations, min_value=0, help="Other operational costs")
        submit_sme = st.form_submit_button("Calculate KPIs")
    if submit_sme:
        st.session_state.profit = st.session_state.revenue - st.session_state.expenses
        st.success(f"Profit: ${st.session_state.profit:,.2f}")
        fig = px.bar(
            x=["Marketing","Operations","Profit"],
            y=[st.session_state.marketing,st.session_state.operations,st.session_state.profit],
            title="SME Allocation"
        )
        st.plotly_chart(fig)

# ---------------- ESTATE PLANNING ----------------
if st.session_state.page == "estate":
    st.header("Estate Planning ⚖️")
    for var in ["total_estate","num_heirs","estate_tax_rate","special_allocations"]:
        if var not in st.session_state:
            st.session_state[var] = 0
    with st.form("estate_form"):
        st.session_state.total_estate = st.number_input("Total Estate ($)", value=st.session_state.total_estate, min_value=0, help="Total estate value")
        st.session_state.num_heirs = st.number_input("Number of Heirs", value=st.session_state.num_heirs, min_value=1, help="Total number of heirs")
        st.session_state.estate_tax_rate = st.number_input("Estate Tax Rate (%)", value=st.session_state.estate_tax_rate, min_value=0.0, max_value=100.0, help="Applicable estate tax rate")
        st.session_state.special_allocations = st.text_input("Special Allocations (Heir:Amount, ...)", value=st.session_state.special_allocations, help="Specify any special inheritance allocations")
        submit_estate = st.form_submit_button("Calculate Inheritance")
    if submit_estate:
        base_amount = st.session_state.total_estate*(1 - st.session_state.estate_tax_rate/100)/st.session_state.num_heirs
        inheritance = {f"Heir {i+1}": base_amount for i in range(st.session_state.num_heirs)}
        try:
            for item in st.session_state.special_allocations.split(","):
                if ":" in item:
                    heir, amt = item.split(":")
                    inheritance[heir.strip()] = float(amt.strip())
        except:
            st.warning("Special allocations format incorrect. Use Heir:Amount,Heir2:Amount2")
        st.success("Inheritance Calculated")
        df = pd.DataFrame({"Heir": list(inheritance.keys()), "Amount": list(inheritance.values())})
        fig = px.pie(df, names="Heir", values="Amount", title="Estate Distribution", hole=0.3)
        st.plotly_chart(fig)

# ---------------- PREMIUM MODULE ----------------
if st.session_state.page == "premium":
    st.subheader("Premium Modules Coming Soon 🚀")
