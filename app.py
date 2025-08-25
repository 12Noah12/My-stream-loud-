import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# --- SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False

# --- NAVIGATION ---
PAGES = ["home", "household", "individual", "business"]

# --- BACKGROUND IMAGES ---
BG_IMAGES = {
    "home": "url('https://images.unsplash.com/photo-1542223616-5f4cfc1dfd92?auto=format&fit=crop&w=1470&q=80')",
    "household": "url('https://images.unsplash.com/photo-1504198453319-5ce911bafcde?auto=format&fit=crop&w=1470&q=80')",
    "individual": "url('https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1470&q=80')",
    "business": "url('https://images.unsplash.com/photo-1554224154-22dec7ec8818?auto=format&fit=crop&w=1470&q=80')"
}

# --- STYLING ---
st.markdown(f"""
<style>
.stApp {{
    background-image: {BG_IMAGES.get(st.session_state.page, '')};
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}
.stApp .block-container {{
    position: relative;
    z-index: 1;
    padding: 2rem;
    background: rgba(0,0,0,0.45);
    border-radius: 12px;
    color: #ffffff;
    max-width: 900px;
    margin: 4rem auto;
    text-align: center;
}}
input[type=text], input[type=number] {{
    font-size: 1.2em;
    padding: 0.8em;
    border-radius: 10px;
    border: 2px solid #ffffff;
    background-color: rgba(255,255,255,0.9);
    color: #000000;
    width: 70%;
    display: block;
    margin: 1rem auto;
    text-align: center;
}}
input[type=text]::placeholder {{
    color: #555555;
    font-weight: bold;
}}
input[type=text]:focus, input[type=number]:focus {{
    outline: none;
    box-shadow: 0 0 20px #ffffff;
}}
.user-type-btn {{
    padding: 1rem 2rem;
    margin: 1rem;
    font-size: 1.1em;
    border-radius: 8px;
    border: 2px solid #ffffff;
    background-color: rgba(255,255,255,0.8);
    color: #000000;
    font-weight: bold;
    cursor: pointer;
    transition: 0.3s;
}}
.user-type-btn:hover {{
    background-color: rgba(255,255,255,1);
}}
.section-title {{
    font-size: 1.5em;
    font-weight: bold;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- PRIVACY AGREEMENT ----------------
def privacy_agreement():
    st.markdown("## Privacy & Data Agreement")
    st.markdown("""
    All information you enter is stored securely in encrypted storage. By clicking 'Accept', you acknowledge and agree that:
    - FinAI will use your data solely to generate personalized financial advice.
    - Data is stored securely and will not be shared with third parties.
    - This is a legally binding agreement.
    """)
    accept = st.checkbox("I ACCEPT the privacy agreement")
    if accept:
        st.session_state.privacy_accepted = True
    else:
        st.warning("You must accept to continue.")
        st.stop()

if not st.session_state.privacy_accepted:
    privacy_agreement()

# ---------------- FRONT PAGE ----------------
if st.session_state.page == "home":
    st.title("Welcome to FinAI")
    st.markdown("Enter your financial questions below, and our AI will direct you to tailored advice.")
    query = st.text_input("Ask FinAI anything...", "")
    
    # --- AI SEARCH REDIRECT ---
    if query:
        q = query.lower()
        if any(word in q for word in ["household", "family", "kids", "income", "expenses"]):
            st.session_state.page = "household"
        elif any(word in q for word in ["business", "corporate", "company", "expenses", "revenue"]):
            st.session_state.page = "business"
        else:
            st.session_state.page = "individual"
        st.experimental_rerun()

    st.markdown("Or choose your category to start:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Household"):
            st.session_state.page = "household"
            st.experimental_rerun()
    with col2:
        if st.button("Individual"):
            st.session_state.page = "individual"
            st.experimental_rerun()
    with col3:
        if st.button("Business/Corporate"):
            st.session_state.page = "business"
            st.experimental_rerun()

# ---------------- HOUSEHOLD FINANCE ----------------
elif st.session_state.page == "household":
    st.header("Household Finance Dashboard")
    st.markdown("Fill in your household income, deductions, and expenses to get personalized advice.")

    salary = st.number_input("Monthly Salary (ZAR)", min_value=0.0, format="%.2f")
    other_income = st.number_input("Other Monthly Income (ZAR)", min_value=0.0, format="%.2f")
    deductions = st.number_input("Current Deductions (ZAR)", min_value=0.0, format="%.2f")
    children = st.number_input("Number of Dependents", min_value=0)

    if st.button("Generate Advice"):
        total_income = salary + other_income
        est_tax_savings = min(deductions * 0.3, total_income * 0.2)
        st.markdown("### Recommended Actions:")
        st.markdown(f"""
        - Optimize deductions to save approximately **ZAR {est_tax_savings:,.2f} per month**.
        - Consider child-related tax credits.
        - Invest in tax-efficient savings accounts.
        - Contact us to implement full strategy.
        """)

        df = pd.DataFrame({
            "Income Type": ["Salary", "Other Income", "Deductions", "Est. Tax Savings"],
            "Amount ZAR": [salary, other_income, deductions, est_tax_savings]
        })
        towrite = BytesIO()
        df.to_excel(towrite, index=False)
        st.download_button(label="Download Excel Report", data=towrite.getvalue(), file_name="household_finance.xlsx")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Household Finance Report", ln=True, align='C')
        pdf.ln(10)
        pdf.cell(0, 10, txt=f"Salary: ZAR {salary:,.2f}", ln=True)
        pdf.cell(0, 10, txt=f"Other Income: ZAR {other_income:,.2f}", ln=True)
        pdf.cell(0, 10, txt=f"Deductions: ZAR {deductions:,.2f}", ln=True)
        pdf.cell(0, 10, txt=f"Estimated Tax Savings: ZAR {est_tax_savings:,.2f}", ln=True)
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        st.download_button(label="Download PDF Report", data=pdf_output.getvalue(), file_name="household_finance.pdf")

# ---------------- INDIVIDUAL FINANCE ----------------
elif st.session_state.page == "individual":
    st.header("Individual Finance Dashboard")
    income = st.number_input("Monthly Income (ZAR)", min_value=0.0, format="%.2f")
    expenses = st.number_input("Monthly Expenses (ZAR)", min_value=0.0, format="%.2f")
    investments = st.number_input("Current Investments (ZAR)", min_value=0.0, format="%.2f")
    if st.button("Generate Advice"):
        est_savings = max(income - expenses - investments, 0)
        st.markdown("### Recommended Actions:")
        st.markdown(f"""
        - Your estimated monthly savings: **ZAR {est_savings:,.2f}**.
        - Invest in tax-efficient products.
        - Review recurring expenses for optimization.
        - Contact us for detailed investment planning.
        """)

# ---------------- BUSINESS FINANCE ----------------
elif st.session_state.page == "business":
    st.header("Business/Corporate Dashboard")
    revenue = st.number_input("Monthly Revenue (ZAR)", min_value=0.0, format="%.2f")
    business_expenses = st.number_input("Monthly Business Expenses (ZAR)", min_value=0.0, format="%.2f")
    employees = st.number_input("Number of Employees", min_value=0)
    if st.button("Generate Advice"):
        est_tax_savings = business_expenses * 0.3
        st.markdown("### Recommended Actions:")
        st.markdown(f"""
        - Estimated monthly tax savings: **ZAR {est_tax_savings:,.2f}**
        - Use company card for deductible business expenses.
        - Optimize employee-related tax credits.
        - Contact us to implement full tax strategy.
        """)

# ---------------- RETURN TO HOME ----------------
if st.session_state.page != "home":
    if st.button("Return to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
