import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import openai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# ---------------- BACKGROUND IMAGE ----------------
BG_IMAGE_URL = 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80'
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
    }}
    input[type=text], input[type=number] {{
        font-size: 1.2em;
        padding: 0.5em;
    }}
    .submit-btn {{
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 0.6em 1.2em;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        box-shadow: 0 0 10px #4CAF50;
        transition: 0.3s;
    }}
    .submit-btn:hover {{
        box-shadow: 0 0 20px #4CAF50;
    }}
    .user-btn {{
        font-size: 1.2em;
        color: black !important;
    }}
    .privacy-text {{
        color: white;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'privacy_accepted' not in st.session_state:
    st.session_state.privacy_accepted = False
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""

# ---------------- PRIVACY AGREEMENT ----------------
def privacy_agreement():
    st.markdown("<h1 class='privacy-text'>Privacy Agreement</h1>", unsafe_allow_html=True)
    st.markdown("""
        <p class='privacy-text'>
        Welcome to FinAI. All information you enter will be stored securely on encrypted servers. By clicking 'Accept', 
        you acknowledge and agree that your data will be used solely for generating financial insights and reports. 
        This agreement is legally binding. If you do not accept, you will not be able to access the platform.
        </p>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement")
    if accept:
        st.session_state.privacy_accepted = True
    else:
        st.warning("You must accept to continue.")
        st.stop()

# ---------------- NAVBAR ----------------
def show_navbar(pages):
    cols = st.columns(len(pages))
    for i, (key, label) in enumerate(pages.items()):
        if cols[i].button(label, key=key, help=f"Go to {label}"):
            st.session_state.page = key

# ---------------- AI SEARCH ----------------
def ai_search():
    st.subheader("Describe your financial situation or goals")
    query = st.text_input("", placeholder="Type anything about your finances, business, or household...")
    if st.button("Submit", key="ai_submit"):
        if query.strip() != "":
            response = get_ai_redirect(query)
            st.session_state.user_type = response
            st.session_state.page = 'dashboard'
            st.experimental_rerun()

# ---------------- GPT BACKEND ----------------
def get_ai_redirect(text):
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        st.warning("OpenAI API key not found. Defaulting to Individual.")
        return 'individual'
    try:
        prompt = f"""
        Determine if this query is best for 'individual', 'household', or 'business' financial advice:
        {text}
        Return only one of: individual, household, business
        """
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=10
        )
        result = completion.choices[0].text.strip().lower()
        if result not in ['individual', 'household', 'business']:
            return 'individual'
        return result
    except:
        return 'individual'

# ---------------- USER TYPE SELECTION ----------------
def select_user_type():
    st.subheader("Choose your category")
    col1, col2, col3 = st.columns(3)
    if col1.button("Individual", key="btn_individual"):
        st.session_state.user_type = 'individual'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if col2.button("Household", key="btn_household"):
        st.session_state.user_type = 'household'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if col3.button("Business", key="btn_business"):
        st.session_state.user_type = 'business'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()

# ---------------- DASHBOARD ----------------
def dashboard():
    st.title(f"{st.session_state.user_type.capitalize()} Dashboard")
    user_type = st.session_state.user_type
    inputs = {}

    # Input fields with hover tooltips
    if user_type == 'individual':
        inputs['Income'] = st.number_input("Annual Income", min_value=0.0, format="%.2f", help="Your total income for the year")
        inputs['Deductions'] = st.number_input("Annual Deductions", min_value=0.0, format="%.2f", help="Any deductions you currently claim")
    elif user_type == 'household':
        inputs['Household Income'] = st.number_input("Household Annual Income", min_value=0.0, format="%.2f", help="Total household income")
        inputs['Children'] = st.number_input("Number of Children", min_value=0, step=1, help="Number of children in the household")
        inputs['Deductions'] = st.number_input("Total Household Deductions", min_value=0.0, format="%.2f", help="Total deductions currently applied")
    elif user_type == 'business':
        inputs['Revenue'] = st.number_input("Annual Revenue", min_value=0.0, format="%.2f", help="Total revenue for the business")
        inputs['Expenses'] = st.number_input("Annual Expenses", min_value=0.0, format="%.2f", help="Total business expenses")
        inputs['Employees'] = st.number_input("Number of Employees", min_value=0, step=1, help="Number of employees in the business")

    if st.button("Get Personalized Advice", key="get_advice"):
        advice = generate_advice_gpt(user_type, inputs)
        st.info(advice)

    if st.button("Download PDF Report", key="download_pdf"):
        advice = generate_advice_gpt(user_type, inputs)
        pdf_bytes = create_pdf(inputs, user_type, advice)
        st.download_button("Download PDF", pdf_bytes, file_name="report.pdf")

    if st.button("Download Excel Report", key="download_excel"):
        advice = generate_advice_gpt(user_type, inputs)
        excel_bytes = create_excel(inputs, user_type, advice)
        st.download_button("Download Excel", excel_bytes, file_name="report.xlsx")

# ---------------- GPT ADVICE ----------------
def generate_advice_gpt(user_type, inputs):
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        return "OpenAI API key not found. Cannot generate advice."
    try:
        input_text = "\n".join([f"{k}: {v}" for k,v in inputs.items()])
        prompt = f"""
        You are a professional financial advisor. Based on these user inputs:
        {input_text}
        Provide actionable financial advice in 3-4 bullet points. Do NOT give full instructions; encourage contacting us.
        """
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300
        )
        return completion.choices[0].text.strip()
    except:
        return "Unable to generate advice at this time."

# ---------------- PDF ----------------
def create_pdf(inputs, user_type, advice):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(50,750,f"User Type: {user_type.capitalize()}")
    y = 730
    for k,v in inputs.items():
        c.drawString(50,y,f"{k}: {v}")
        y -= 20
    c.drawString(50,y-10,"Advice:")
    y -= 30
    for line in advice.split("\n"):
        c.drawString(70,y,line)
        y -= 20
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# ---------------- EXCEL ----------------
def create_excel(inputs, user_type, advice):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    worksheet.write('A1', 'User Type')
    worksheet.write('B1', user_type)
    row = 1
    for k,v in inputs.items():
        worksheet.write(row,0,k)
        worksheet.write(row,1,v)
        row += 1
    worksheet.write(row,0,"Advice")
    worksheet.write(row,1,advice)
    workbook.close()
    return output.getvalue()

# ---------------- MAIN ----------------
if not st.session_state.privacy_accepted:
    privacy_agreement()

if st.session_state.page == 'home':
    st.title("Welcome to FinAI")
    ai_search()
    select_user_type()
elif st.session_state.page == 'dashboard':
    dashboard()
