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

# Sync with query params
params = st.experimental_get_query_params()
if "page" in params and params["page"]:
    candidate = params["page"][0]
    if candidate in PAGES and candidate != st.session_state.page:
        st.session_state.page = candidate

current_page = st.session_state.page

# =========================
# Styles
# =========================
st.markdown("""
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

html, body, [class*="css"]  { font-family: 'Inter', sans-serif !important; color: var(--ink); }
h1,h2,h3,h4,h5 { font-family: 'Inter', sans-serif; }

.main .block-container{
  padding-top: 1.5rem;
  padding-bottom: 2rem;
  margin-left: 300px;
  max-width: 1200px;
}

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
  background: linear-gradient(135deg, rgba(37,99,235,0.08), rgba(29,78,216,0.08));
}
.finai-logo .dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--brand);
}
.finai-logo h2{
  margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.2px;
}

.menu-card {
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.menu-item {
  display: block;
  text-decoration: none;
  color: var(--ink);
  padding: 12px 14px;
  border-radius: 12px;
  transition: all .18s ease;
  font-weight: 600;
  border: 1px solid transparent;
}
.menu-item:hover {
  background: #F9FAFB;
  transform: translateX(3px);
}
.menu-item.active {
  background: rgba(37,99,235,0.08);
  color: var(--brand);
  border: 1px solid rgba(37,99,235,0.35);
}

.stButton>button {
  background-color: var(--brand); 
  color:white; 
  border:none; 
  border-radius:10px; 
  padding:0.6rem 1.0rem;
  transition: background .15s ease, transform .05s ease;
  box-shadow: var(--shadow);
}
.stButton>button:hover { background-color: var(--brand-dark); }
.stButton>button:active { transform: translateY(1px); }

.card {
  background-color: var(--card);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  transition: transform 0.15s, box-shadow 0.15s;
}
.card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }

.page-hero img {
  width:100%; border-radius:16px; filter: brightness(0.72);
}

.finai-footer-sep { margin-left: 300px; }
</style>
""", unsafe_allow_html=True)

# =========================
# Custom Sidebar
# =========================
def _menu_link(label: str, active: bool) -> str:
    href = f"?page={quote(label)}"
    cls = "menu-item active" if active else "menu-item"
    return f'<a class="{cls}" href="{href}">{label}</a>'

sidebar_html = f"""
<div class="finai-sidebar">
  <div class="finai-logo">
    <div class="dot"></div>
    <h2>FinAI</h2>
  </div>
  <div class="menu-card">
    {_menu_link("Home", current_page=="Home")}
    {_menu_link("Tax Optimization", current_page=="Tax Optimization")}
    {_menu_link("Investments", current_page=="Investments")}
    {_menu_link("SME Dashboard", current_page=="SME Dashboard")}
    {_menu_link("Premium Modules", current_page=="Premium Modules")}
  </div>
  <div class="card" style="margin-top:auto;">
    <div style="font-weight:700; margin-bottom:6px;">Status</div>
    <div style="font-size:14px; color:var(--muted);">
      Premium: <strong>{"Active" if st.session_state.premium else "Inactive"}</strong>
    </div>
  </div>
</div>
"""
st.markdown(sidebar_html, unsafe_allow_html=True)

# =========================
# AI Chat
# =========================
def ai_chat(user_input: str) -> str:
    if user_input:
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": user_input}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"
    return ""

# =========================
# Utilities
# =========================
def calculate_sa_tax(income, age=30, retirement=0):
    taxable_income = max(income - retirement, 0)
    brackets = [
        (0,237100,0.18),
        (237101,370500,0.26),
        (370501,512800,0.31),
        (512801,673000,0.36),
        (673001,857900,0.39),
        (857901,1817000,0.41),
        (1817001,float("inf"),0.45)
    ]
    tax = 0
    for lower, upper, rate in brackets:
        if taxable_income > upper:
            tax += (upper - lower + 1)*rate
        elif taxable_income > lower:
            tax += (taxable_income - lower + 1)*rate
            break
    tax -= 17450
    if age >= 65: tax -= 9590
    if age >= 75: tax -= 3190
    return max(int(tax),0)

def suggest_optimizations(data):
    suggestions=[]
    if data['retirement_contributions'] < 35000:
        potential = int((35000 - data['retirement_contributions'])*0.3)
        suggestions.append({"action":"Increase retirement contributions","saving":potential})
    if data['medical_aid_contributions']>0:
        potential=int(data['medical_aid_contributions']*0.25)
        suggestions.append({"action":"Claim medical aid credits","saving":potential})
    if data['donations']<100000:
        potential=int((100000-data['donations'])*0.18)
        suggestions.append({"action":"Make deductible donations","saving":potential})
    if data.get('owns_business',False):
        suggestions.append({"action":"Claim business expenses","saving":"Varies"})
    if st.session_state['premium']:
        suggestions.append({"action":"Entity structuring & investment planning (Premium)","saving":"Varies"})
        suggestions.append({"action":"Advanced investment simulations (Premium)","saving":"Long-term"})
    return sorted(suggestions,key=lambda x: x['saving'] if isinstance(x['saving'],int) else 0,reverse=True)

def project_investments(current, annual, years, rate=0.08):
    projection=[]
    total=current
    for y in range(1,years+1):
        total = total*(1+rate)+annual
        projection.append({"Year":y,"Value":int(total)})
    return projection

# =========================
# Pages
# =========================
page = current_page

# -------- Home --------
if page=="Home":
    st.markdown("""
    <div class="page-hero" style="position:relative;text-align:center;color:white;">
        <img src="https://images.unsplash.com/photo-1576675780660-5d162e08cdb0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1600">
        <div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%);">
            <h1 style="font-size:60px; margin-bottom:10px;">Welcome to FinAI</h1>
            <p style="font-size:22px; margin-bottom:20px;">Use the AI assistant below to navigate your financial dashboard instantly.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    user_question = st.text_input("Ask the AI Assistant anything...", "", key="home_ai_input")
    if st.button("Send Question"):
        answer = ai_chat(user_question)
        st.success(answer)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card"><h2>Tax Optimization</h2><p>Calculate taxes and explore strategies to reduce them efficiently.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="card"><h2>SME Dashboard</h2><p>Track revenue, expenses, and profits for your business easily.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card"><h2>Investments</h2><p>Project your savings growth and plan long-term investments.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="card"><h2>Premium Modules</h2><p>Access advanced tax, investment, and entity structuring tools.</p></div>', unsafe_allow_html=True)

# -------- Tax Optimization --------
elif page=="Tax Optimization":
    st.markdown("## Tax Calculation")
    with st.form("tax_calc"):
        income = st.text_input("Annual Income (ZAR)","500000")
        age = st.text_input("Age","30")
        retirement = st.text_input("Retirement Contributions (ZAR)","0")
        submitted = st.form_submit_button("Calculate Tax")
    if submitted:
        try:
            tax_due = calculate_sa_tax(float(income.replace(",","")), int(age), float(retirement.replace(",","")))
            st.success(f"Estimated Tax Due: ZAR {tax_due:,}")
        except ValueError:
            st.error("Please enter valid numbers.")

    st.markdown("## Suggestions to Reduce Tax")
    with st.form("tax_sugg"):
        medical = st.text_input("Medical Aid Contributions (ZAR)","0")
        donations = st.text_input("Donations (ZAR)","0")
        owns_business = st.checkbox("Owns Business?")
        submitted_sugg = st.form_submit_button("Show Suggestions")
    if submitted_sugg:
        try:
            user_data = {
                "income": float(income.replace(",","")),
                "age": int(age),
                "retirement_contributions": float(retirement.replace(",","")),
                "medical_aid_contributions": float(medical.replace(",","")),
                "donations": float(donations.replace(",","")),
                "owns_business": owns_business
            }
            suggestions = suggest_optimizations(user_data)
            for s in suggestions:
                st.markdown(f"- **{s['action']}** ({s['saving']})")
            if suggestions:
                df = pd.DataFrame([{"Strategy": s['action'], "Potential Saving": s['saving']} for s in suggestions if isinstance(s['saving'], int)])
                if not df.empty:
                    fig = px.bar(df, x="Strategy", y="Potential Saving", color="Potential Saving", title="Potential Savings by Strategy")
                    st.plotly_chart(fig, use_container_width=True)
        except ValueError:
            st.error("Please enter valid numbers.")

# -------- Investments --------
elif page=="Investments":
    st.markdown("## Investment Projections")
    with st.form("invest_form"):
        current = st.text_input("Current Savings (ZAR)","0")
        annual = st.text_input("Annual Contribution (ZAR)","0")
        years = st.slider("Years",1,50,20)
        rate = st.slider("Expected Annual Return %",0.0,20.0,8.0)/100
        submitted = st.form_submit_button("Project Growth")
    if submitted:
        try:
            proj = project_investments(float(current.replace(",","")), float(annual.replace(",","")), years, rate)
            df = pd.DataFrame(proj)
            st.line_chart(df.set_index("Year"))
            st.table(df.tail(5))
        except ValueError:
            st.error("Please enter valid numbers.")

# -------- SME Dashboard --------
elif page=="SME Dashboard":
    st.markdown("## SME Dashboard")
    revenue = st.text_input("Annual Revenue (ZAR)","1000000")
    expenses = st.text_input("Annual Expenses (ZAR)","600000")
    if st.button("Calculate Profit"):
        try:
            profit = float(revenue.replace(",","")) - float(expenses.replace(",",""))
            st.success(f"Estimated Profit: ZAR {profit:,}")
            tax_due = calculate_sa_tax(profit)
            st.info(f"Estimated Tax: ZAR {tax_due:,}")
        except ValueError:
            st.error("Please enter valid numbers.")

# -------- Premium Modules --------
elif page=="Premium Modules":
    st.markdown("## Premium Modules")
    if not st.session_state['premium']:
        st.info("Activate Premium to unlock advanced features.")
        if st.button("Activate Premium (Sandbox)"):
            st.session_state['premium'] = True
            st.success("Premium Mode Activated!")
    if st.session_state['premium']:
        st.markdown("- Entity Structuring (PTY, LTD simulations)")
        st.markdown("- Advanced Tax Deductions")
        st.markdown("- Scenario-based Investment Planning")
        st.markdown("- Detailed Projection Charts")
        proj = project_investments(100000,50000,20,0.12)
        df = pd.DataFrame(proj)
        fig = px.line(df,x="Year",y="Value",title="Premium Investment Growth Scenario")
        st.plotly_chart(fig,use_container_width=True)

# -------- Footer --------
st.markdown("---", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>FinAI - AI Financial Platform | Prototype Demo | All projections are for guidance only.</p>", unsafe_allow_html=True)
