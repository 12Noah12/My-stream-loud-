import streamlit as st
import pandas as pd
import numpy as np
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
    .black-font button {{
        color: black !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }}
    input[type=text] {{
        font-size: 1.2em;
        padding: 0.5em;
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
    st.markdown("<h1 style='color:white'>Privacy Agreement</h1>", unsafe_allow_html=True)
    st.markdown("""
        <p style='color:white'>
        By entering your data, you consent to the storage and processing of this information securely. 
        This information is used solely for providing personalized financial advice. 
        By clicking 'Accept', you enter a legally binding agreement that your information will be used 
        for advisory purposes only. If you do not accept, you cannot continue to the platform.
        </p>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement")
    if accept:
        st.session_state.privacy_accepted = True
    else:
        st.error("You must accept to continue.")
        st.stop()

# ---------------- NAVBAR ----------------
def show_navbar(pages):
    cols = st.columns(len(pages))
    for i, (key, label) in enumerate(pages.items()):
        if cols[i].button(label):
            st.session_state.page = key

# ---------------- AI SEARCH ----------------
def ai_search():
    st.subheader("Describe your financial situation or goals")
    query = st.text_input("", placeholder="Type anything about your finances, business, or household...")
    if st.button("Submit") and query:
        response = get_ai_redirect(query)
        st.session_state.user_type = response
        st.session_state.page = 'dashboard'
        st.experimental_rerun()

# ---------------- GPT BACKEND ----------------
def get_ai_redirect(text):
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        st.warning("OpenAI API key not found, defaulting to Individual.")
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

    if 'rerun_pending' not in st.session_state:
        st.session_state.rerun_pending = False

    if col1.button("Individual", key="btn_individual") and not st.session_state.rerun_pending:
        st.session_state.user_type = 'individual'
        st.session_state.page = 'dashboard'
        st.session_state.rerun_pending = True

    if col2.button("Household", key="btn_household") and not st.session_state.rerun_pending:
        st.session_state.user_type = 'household'
        st.session_state.page = 'dashboard'
        st.session_state.rerun_pending = True

    if col3.button("Business", key="btn_business") and not st.session_state.rerun_pending:
        st.session_state.user_type = 'business'
        st.session_state.page = 'dashboard'
        st.session_state.rerun_pending = True

    if st.session_state.rerun_pending:
        st.session_state.rerun_pending = False
        st.experimental_rerun()

# ---------------- DASHBOARD ----------------
def dashboard():
    st.title(f"{st.session_state.user_type.capitalize()} Dashboard")
    user_type = st.session_state.user_type

    inputs = {}
    if user_type == 'individual':
        inputs['Income'] = st.number_input("Annual Income", min_value=0.0, format="%.2f")
        inputs['Deductions'] = st.number_input("Annual Deductions", min_value=0.0, format="%.2f")
    elif user_type == 'household':
        inputs['Household Income'] = st.number_input("Household Annual Income", min_value=0.0, format="%.2f")
        inputs['Children'] = st.number_input("Number of Children", min_value=0, step=1)
        inputs['Deductions'] = st.number_input("Total Household Deductions", min_value=0.0, format="%.2f")
    elif user_type == 'business':
        inputs['Revenue'] = st.number_input("Annual Revenue", min_value=0.0, format="%.2f")
        inputs['Expenses'] = st.number_input("Annual Expenses", min_value=0.0, format="%.2f")
        inputs['Employees'] = st.number_input("Number of Employees", min_value=0, step=1)

    if st.button("Get Personalized Advice"):
        advice = generate_advice_gpt(user_type, inputs)
        st.info(advice)

    if st.button("Download PDF Report"):
        pdf_bytes = create_pdf(inputs, user_type, advice)
        st.download_button("Download PDF", pdf_bytes, file_name="report.pdf")

    if st.button("Download Excel Report"):
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
        Provide actionable financial advice in 3-4 bullet points. Do NOT give the full instructions; encourage the user to contact us to implement solutions.
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

