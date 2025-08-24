# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

# =========================
# Config
# =========================
st.set_page_config(page_title="FinAI - AI Financial Platform",
                   layout="wide",
                   initial_sidebar_state="expanded")

# =========================
# OpenAI client
# =========================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except KeyError:
    st.error("OpenAI API key not found! Add it to Streamlit Cloud Secrets as OPENAI_API_KEY.")
    st.stop()

# =========================
# Session State
# =========================
if 'page' not in st.session_state:
    st.session_state['page'] = "Home"
if 'premium' not in st.session_state:
    st.session_state['premium'] = False

# =========================
# CSS for modern UI
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

body {font-family: 'Inter', sans-serif; color:#1F2937;}
h1,h2,h3,h4,h5 {font-family: 'Inter', sans-serif;}

.stButton>button {
    background-color:#2563EB; 
    color:white; 
    border:none; 
    border-radius:5px; 
    padding:0.5rem 1rem;
}
.stButton>button:hover {background-color:#1D4ED8;}

.card {
    background-color:white;
    border-radius:15px;
    padding:25px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {transform: translateY(-5px); box-shadow: 0 12px 25px rgba(0,0,0,0.15);}

.info-icon {
    display:inline-block;
    margin-left:5px;
    color:#2563EB;
    font-weight:bold;
    cursor:help;
}
.ai-input {width:60%; padding:12px 20px; border-radius:10px; border:1px solid #ccc; font-size:18px;}
</style>
""", unsafe_allow_html=True)

# =========================
# Sidebar
# =========================
st.sidebar.title("Navigation")
pages = ["Home", "Tax Optimization", "Investments", "SME Dashboard", "Premium Modules"]
for p in pages:
    if st.sidebar.button(p):
        st.session_state['page'] = p

# =========================
# AI Chat
# =========================
def ai_chat(user_input):
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
page = st.session_state['page']

# -------- Home Page --------
if page=="Home":
    st.markdown("""
    <div style="position:relative;text-align:center;color:white;">
        <img src="https://images.unsplash.com/photo-1576675780660-5d162e08cdb0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1400"
            style="width:100%; border-radius:15px; filter: brightness(0.65);">
        <div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%);">
            <h1 style="font-size:60px; margin-bottom:10px;">Welcome to FinAI</h1>
            <p style="font-size:22px; margin-bottom:20px;">Use the AI assistant below to navigate your financial dashboard instantly.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # AI Input
    user_question = st.text_input("Ask the AI Assistant anything...", "", key="home_ai_input")
    if st.button("Send Question"):
        answer = ai_chat(user_question)
        st.success(answer)

    # Modern Cards for modules
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex; justify-content:space-around; flex-wrap:wrap; gap:20px;">
        <div class="card" style="flex:1; min-width:220px;"><h2>Tax Optimization</h2><p>Calculate taxes and explore strategies to reduce them efficiently.</p></div>
        <div class="card" style="flex:1; min-width:220px;"><h2>Investments</h2><p>Project your savings growth and plan long-term investments.</p></div>
        <div class="card" style="flex:1; min-width:220px;"><h2>SME Dashboard</h2><p>Track revenue, expenses, and profits for your business easily.</p></div>
        <div class="card" style="flex:1; min-width:220px;"><h2>Premium Modules</h2><p>Access advanced tax, investment, and entity structuring tools.</p></div>
    </div>
    """, unsafe_allow_html=True)

# -------- Tax Optimization --------
elif page=="Tax Optimization":
    st.markdown("## Tax Calculation")
    with st.form("tax_calc"):
        income = st.text_input("Annual Income (ZAR)","500000")
        age = st.text_input("Age","30")
        retirement = st.text_input("Retirement Contributions (ZAR)","0", help="Reduces taxable income")
        submitted = st.form_submit_button("Calculate Tax")
    if submitted:
        try:
            tax_due = calculate_sa_tax(float(income.replace(",","")), int(age), float(retirement.replace(",","")))
            st.success(f"Estimated Tax Due: ZAR {tax_due}")
        except ValueError:
            st.error("Please enter valid numbers.")

    st.markdown("## Suggestions to Reduce Tax")
    with st.form("tax_sugg"):
        medical = st.text_input("Medical Aid Contributions (ZAR)","0")
        donations = st.text_input("Donations (ZAR)","0")
        owns_business = st.checkbox("Owns Business?", help="Business ownership affects tax deductions")
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
                df = pd.DataFrame([{"Strategy": s['action'], "Potential Saving": s['saving']} for s in suggestions])
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
            st.success(f"Estimated Profit: ZAR {profit}")
            tax_due = calculate_sa_tax(profit)
            st.info(f"Estimated Tax: ZAR {tax_due}")
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
st.markdown("---")
st.markdown("<p style='text-align:center;color:gray;'>FinAI - AI Financial Platform | Prototype Demo | All projections are for guidance only.</p>", unsafe_allow_html=True)
