# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
import stripe

# =========================
# Configuration & Setup
# =========================
st.set_page_config(page_title="FinAI - AI Financial Platform", layout="wide", initial_sidebar_state="expanded")

# ✅ Load API keys from Streamlit Secrets (make sure to set them in Streamlit Cloud!)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
stripe.api_key = st.secrets["STRIPE_TEST_SECRET_KEY"]

# Example product/price IDs (replace with real Stripe test IDs if you want checkout)
PRODUCT_ID = "prod_xxxxx"
PRICE_ID = "price_xxxxx"

# Session state for page navigation and premium
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "premium" not in st.session_state:
    st.session_state["premium"] = False
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# =========================
# Sidebar Navigation
# =========================
st.sidebar.title("FinAI Navigation")
pages = ["Home", "Tax Optimization", "Investments", "SME Dashboard", "Premium Modules"]

for p in pages:
    if st.sidebar.button(p):
        st.session_state["page"] = p

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **AI Assistant:** Ask questions or get guidance here.")

# =========================
# AI Assistant Function
# =========================
def ai_chat():
    user_input = st.sidebar.text_input("Ask the AI Assistant")
    if st.sidebar.button("Send"):
        if user_input:
            try:
                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[{"role": "user", "content": user_input}],
                    temperature=0.7,
                )
                answer = response.choices[0].message.content
                st.sidebar.markdown(f"**AI Assistant:** {answer}")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

ai_chat()

# =========================
# Utility Functions
# =========================
def calculate_sa_tax(income, age=30, retirement=0):
    taxable_income = max(income - retirement, 0)
    brackets = [
        (0, 237100, 0.18),
        (237101, 370500, 0.26),
        (370501, 512800, 0.31),
        (512801, 673000, 0.36),
        (673001, 857900, 0.39),
        (857901, 1817000, 0.41),
        (1817001, float("inf"), 0.45),
    ]
    tax = 0
    for lower, upper, rate in brackets:
        if taxable_income > upper:
            tax += (upper - lower + 1) * rate
        elif taxable_income > lower:
            tax += (taxable_income - lower + 1) * rate
            break
    tax -= 17450
    if age >= 65:
        tax -= 9590
    if age >= 75:
        tax -= 3190
    return max(int(tax), 0)

def suggest_optimizations(data):
    suggestions = []
    if data["retirement_contributions"] < 35000:
        potential = int((35000 - data["retirement_contributions"]) * 0.3)
        suggestions.append({"action": "Increase retirement contributions", "saving": potential})
    if data["medical_aid_contributions"] > 0:
        potential = int(data["medical_aid_contributions"] * 0.25)
        suggestions.append({"action": "Claim medical aid credits", "saving": potential})
    if data["donations"] < 100000:
        potential = int((100000 - data["donations"]) * 0.18)
        suggestions.append({"action": "Make deductible donations", "saving": potential})
    if data.get("owns_business", False):
        suggestions.append({"action": "Claim business expenses", "saving": "Varies"})
    if st.session_state["premium"]:
        suggestions.append({"action": "Entity structuring & investment planning (Premium)", "saving": "Varies"})
        suggestions.append({"action": "Advanced investment simulations (Premium)", "saving": "Long-term"})
    return sorted(suggestions, key=lambda x: x["saving"] if isinstance(x["saving"], int) else 0, reverse=True)

def project_investments(current, annual, years, rate=0.08):
    projection = []
    total = current
    for y in range(1, years + 1):
        total = total * (1 + rate) + annual
        projection.append({"Year": y, "Value": int(total)})
    return projection

# =========================
# Pages
# =========================
page = st.session_state["page"]

if page == "Home":
    st.markdown(
        """
    <style>
    .main-title {
        font-family: 'Arial', sans-serif;
        font-size: 42px;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 5px;
    }
    .sub-title {
        font-family: 'Arial', sans-serif;
        font-size: 20px;
        color: gray;
        text-align: center;
        margin-top: -5px;
        margin-bottom: 20px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-title">FinAI - Smart Finance Made Simple</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Your AI-powered platform for tax, investments & business growth</div>',
        unsafe_allow_html=True,
    )

    st.image(
        "https://images.unsplash.com/photo-1581091012184-35f55b63b78c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        use_column_width=True,
    )
    st.markdown(
        """
    <div style="text-align:center; margin-top:20px;">
        <p style="font-size:18px; color:#555;">
        Navigate through modules using the sidebar. Ask the AI assistant for advice anytime!
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

elif page == "Tax Optimization":
    st.header("💸 Tax Optimization")
    with st.form("tax_form"):
        income = st.number_input("Annual Income (ZAR)", value=500000)
        age = st.number_input("Age", value=30)
        retirement = st.number_input("Retirement Contributions", value=0)
        medical = st.number_input("Medical Aid Contributions", value=0)
        donations = st.number_input("Donations", value=0)
        owns_business = st.checkbox("Owns Business?")
        submitted = st.form_submit_button("Calculate Tax & Suggestions")
    if submitted:
        tax_due = calculate_sa_tax(income, age, retirement)
        st.subheader(f"Estimated Tax Due: ZAR {tax_due}")
        user_data = {
            "income": income,
            "age": age,
            "retirement_contributions": retirement,
            "medical_aid_contributions": medical,
            "donations": donations,
            "owns_business": owns_business,
        }
        suggestions = suggest_optimizations(user_data)
        st.markdown("### Suggested Tax Optimization Strategies:")
        for s in suggestions:
            st.markdown(f"- **{s['action']}** ({s['saving']})")
        df = pd.DataFrame([{"Strategy": s["action"], "Potential Saving": s["saving"]} for s in suggestions])
        fig = px.bar(df, x="Strategy", y="Potential Saving", color="Potential Saving", title="Potential Savings by Strategy")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Investments":
    st.header("📈 Investment Projections")
    with st.form("investment_form"):
        current = st.number_input("Current Savings (ZAR)", value=0)
        annual = st.number_input("Annual Contribution (ZAR)", value=0)
        years = st.slider("Years", 1, 50, 20)
        rate = st.slider("Expected Annual Return %", 0.0, 20.0, 8.0) / 100
        submitted = st.form_submit_button("Project Growth")
    if submitted:
        proj = project_investments(current, annual, years, rate)
        df = pd.DataFrame(proj)
        st.line_chart(df.set_index("Year"))
        st.table(df.tail(5))

elif page == "SME Dashboard":
    st.header("🏢 SME Dashboard")
    st.markdown("Interactive cashflow, tax simulations, and entity guidance for SMEs.")
    revenue = st.number_input("Annual Revenue (ZAR)", value=1000000)
    expenses = st.number_input("Annual Expenses (ZAR)", value=600000)
    profit = revenue - expenses
    st.subheader(f"Estimated Profit: ZAR {profit}")
    tax_due = calculate_sa_tax(profit)
    st.subheader(f"Estimated Tax: ZAR {tax_due}")
    st.markdown("Unlock **Premium modules** for advanced entity structuring, deductions, and projections.")

elif page == "Premium Modules":
    st.header("⭐ Premium Modules")
    st.markdown("Unlock advanced tax strategies, entity simulations, and investment planning.")
    if not st.session_state["premium"]:
        st.markdown("You need a premium subscription to access these modules.")
        if st.button("Activate Premium (Sandbox)"):
            st.session_state["premium"] = True
            st.success("Premium Mode Activated!")
    if st.session_state["premium"]:
        st.markdown("- Entity Structuring (PTY, LTD simulations)")
        st.markdown("- Advanced Tax Deductions")
        st.markdown("- Scenario-based Investment Planning")
        st.markdown("- Detailed Projection Charts")
        st.subheader("Advanced Investment Scenario")
        proj = project_investments(100000, 50000, 20, 0.12)
        df = pd.DataFrame(proj)
        fig = px.line(df, x="Year", y="Value", title="Premium Investment Growth Scenario")
        st.plotly_chart(fig, use_container_width=True)

# =========================
# Footer
# =========================
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:gray;'>FinAI - AI Financial Platform | Prototype Demo | All projections are for guidance only.</p>",
    unsafe_allow_html=True,
)
