import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import openai
import base64
from reportlab.pdfgen import canvas

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinAI Pro", page_icon="💡", layout="wide")

# --- INIT SESSION STATE ---
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False
if "ai_input" not in st.session_state:
    st.session_state.ai_input = ""
if "advice" not in st.session_state:
    st.session_state.advice = ""

# --- OPENAI CONFIG ---
# Replace with your API key or set as environment variable
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")

# --- PRIVACY AGREEMENT ---
def privacy_agreement():
    st.title("Privacy Agreement")
    st.markdown("""
    By using this platform, you consent to the collection and processing of your financial data.
    All information is securely stored and used solely to provide personalized financial advice.
    Clicking 'Accept' constitutes a legally binding agreement. Declining will exit the platform.
    """)
    agree = st.checkbox("I accept the privacy agreement")
    if agree:
        st.session_state.privacy_accepted = True
        st.experimental_rerun()
    else:
        st.warning("You must accept to proceed. Exiting app.")
        st.stop()

# --- AI SEARCH ---
def ai_search():
    st.markdown("<style>input{animation: glow 2s infinite;} @keyframes glow {0% {box-shadow: 0 0 10px #2563eb;} 50% {box-shadow: 0 0 20px #2563eb;} 100% {box-shadow: 0 0 10px #2563eb;}}</style>", unsafe_allow_html=True)
    query = st.text_input("Type your financial question here", key="ai_search")
    if query:
        st.session_state.ai_input = query
        route_user(query)

# --- ROUTE USER BASED ON AI INPUT ---
def route_user(query):
    q = query.lower()
    if any(word in q for word in ["family", "household"]):
        st.session_state.user_type = "family"
    elif any(word in q for word in ["business", "company", "corporate"]):
        st.session_state.user_type = "business"
    else:
        st.session_state.user_type = "individual"
    st.experimental_rerun()

# --- USER TYPE SELECTION ---
def select_user_type():
    st.subheader("Select your user type")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Individual"):
            st.session_state.user_type = "individual"
            st.experimental_rerun()
    with col2:
        if st.button("Family"):
            st.session_state.user_type = "family"
            st.experimental_rerun()
    with col3:
        if st.button("Business"):
            st.session_state.user_type = "business"
            st.experimental_rerun()

# --- AI ADVICE FUNCTION ---
def generate_ai_advice(prompt_text):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt_text,
            max_tokens=300
        )
        advice = response.choices[0].text.strip()
        st.session_state.advice = advice
        return advice
    except Exception as e:
        st.error("Error generating AI advice: {}".format(e))
        return ""

# --- DASHBOARDS ---
def individual_dashboard():
    st.header("Individual Financial Dashboard")
    income = st.number_input("Monthly Income", min_value=0.0, step=1.0)
    investments = st.number_input("Current Investments", min_value=0.0, step=1.0)
    deductions = st.number_input("Existing Deductions", min_value=0.0, step=1.0)

    if st.button("Get Personalized Advice"):
        prompt = f"Individual with monthly income {income}, investments {investments}, deductions {deductions}. Provide personalized advice on tax saving and investment optimization without giving full execution steps."
        advice = generate_ai_advice(prompt)
        st.info(advice)
        generate_chart([income, investments, deductions], ['Income', 'Investments', 'Deductions'], 'Financial Overview')
        download_options({'Income': income, 'Investments': investments, 'Deductions': deductions, 'Advice': advice}, 'individual')


def family_dashboard():
    st.header("Family Financial Dashboard")
    income = st.number_input("Household Monthly Income", min_value=0.0, step=1.0)
    children = st.number_input("Number of Dependents/Children", min_value=0, step=1)
    deductions = st.number_input("Existing Deductions", min_value=0.0, step=1.0)

    if st.button("Get Personalized Advice"):
        prompt = f"Family with monthly income {income}, children {children}, deductions {deductions}. Provide personalized advice on tax credits, deductions, and investments without giving full execution steps."
        advice = generate_ai_advice(prompt)
        st.info(advice)
        generate_chart([income, deductions], ['Income', 'Deductions'], 'Family Financial Overview')
        download_options({'Income': income, 'Children': children, 'Deductions': deductions, 'Advice': advice}, 'family')


def business_dashboard():
    st.header("Business Financial Dashboard")
    revenue = st.number_input("Monthly Revenue", min_value=0.0, step=1.0)
    expenses = st.number_input("Monthly Expenses", min_value=0.0, step=1.0)
    employees = st.number_input("Number of Employees", min_value=0, step=1)

    if st.button("Get Personalized Advice"):
        prompt = f"Business with revenue {revenue}, expenses {expenses}, employees {employees}. Provide personalized tax and expense optimization advice without giving full execution steps."
        advice = generate_ai_advice(prompt)
        st.info(advice)
        generate_chart([revenue, expenses], ['Revenue', 'Expenses'], 'Business Financial Overview')
        download_options({'Revenue': revenue, 'Expenses': expenses, 'Employees': employees, 'Advice': advice}, 'business')

# --- CHART FUNCTION ---
def generate_chart(values, labels, title):
    fig, ax = plt.subplots()
    ax.bar(labels, values, color='#2563eb')
    ax.set_title(title)
    st.pyplot(fig)

# --- PDF AND EXCEL DOWNLOAD ---
def download_options(data_dict, category):
    df = pd.DataFrame(list(data_dict.items()), columns=['Field', 'Value'])

    # Excel
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Summary')
    excel_bytes = excel_buffer.getvalue()
    b64_excel = base64.b64encode(excel_bytes).decode()
    st.markdown(f"[Download Excel](data:application/octet-stream;base64,{b64_excel})")

    # PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, f"{category.capitalize()} Financial Summary")
    y = 780
    for k, v in data_dict.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 20
    c.showPage()
    c.save()
    pdf_bytes = pdf_buffer.getvalue()
    b64_pdf = base64.b64encode(pdf_bytes).decode()
    st.markdown(f"[Download PDF](data:application/pdf;base64,{b64_pdf})")

# --- HOME PAGE ---
def home_page():
    st.title("Welcome to FinAI Pro")
    st.markdown("Get personalized financial advice for Individuals, Families, or Businesses")
    ai_search()
    st.markdown("---")
    select_user_type()

# --- MAIN ---
def main():
    # Background Image
    bg_image = "https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1350&q=80"
    st.markdown(f"<style>body {{background-image: url('{bg_image}'); background-size: cover;}}</style>", unsafe_allow_html=True)

    if not st.session_state.privacy_accepted:
        privacy_agreement()
    else:
        if st.session_state.user_type is None:
            home_page()
        elif st.session_state.user_type == "individual":
            individual_dashboard()
       
