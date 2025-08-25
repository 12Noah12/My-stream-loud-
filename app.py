import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io
import xlsxwriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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
        color: black;
    }}
    input[type=text], .stTextInput {{
        font-size: 1.2em;
        padding: 0.5em;
    }}
    .privacy-text {{
        color: white;
        font-size: 16px;
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
if 'inputs' not in st.session_state:
    st.session_state.inputs = {}

# ---------------- PRIVACY AGREEMENT ----------------
def privacy_agreement():
    st.title("Privacy Agreement")
    st.markdown("""
        <div class="privacy-text">
        All information entered into this system is stored securely in our network.
        By clicking 'Accept', you acknowledge and agree that:
        <ul>
            <li>The data you enter may be used to provide personalized financial advice.</li>
            <li>This agreement is legally binding.</li>
            <li>We take no responsibility for actions you take without contacting our advisors.</li>
        </ul>
        You must accept this agreement to continue using the service.
        </div>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement")
    if accept:
        st.session_state.privacy_accepted = True
        st.session_state.page = 'home'
        st.experimental_rerun()
    else:
        st.warning("You must accept to continue.")
        st.stop()

# ---------------- NAVBAR ----------------
def show_navbar():
    cols = st.columns(3)
    if cols[0].button("Individual"):
        st.session_state.user_type = 'individual'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if cols[1].button("Household"):
        st.session_state.user_type = 'household'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if cols[2].button("Business"):
        st.session_state.user_type = 'business'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()

# ---------------- AI SEARCH ----------------
def ai_search():
    st.subheader("Describe your financial situation or goals")
    query = st.text_input("", placeholder="Type anything about your finances, household, or business...")
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

# ---------------- DASHBOARD ----------------
def dashboard():
    st.title(f"{st.session_state.user_type.capitalize()} Dashboard")
    user_type = st.session_state.user_type
    inputs = {}

    # Input fields per user type
    if user_type == 'individual':
        inputs['Income'] = st.number_input("Annual Income", min_value=0.0, format="%.2f")
        inputs['Deductions'] = st.number_input("Annual Deductions", min_value=0.0, format="%.2f")
    elif user_type == 'household':
        inputs['Household Income'] = st.number_input("Household Annual Income", min_value=0.0, format="%.2f")
        inputs['Children'] = st.number_input("Number of Children", min_value=0)
        inputs['Deductions'] = st.number_input("Total Household Deductions", min_value=0.0, format="%.2f")
    elif user_type == 'business':
        inputs['Revenue'] = st.number_input("Annual Revenue", min_value=0.0, format="%.2f")
        inputs['Expenses'] = st.number_input("Annual Expenses", min_value=0.0, format="%.2f")
        inputs['Employees'] = st.number_input("Number of Employees", min_value=0)

    st.session_state.inputs = inputs

    if st.button("Get Personalized Advice"):
        advice = generate_advice_gpt(user_type, inputs)
        st.session_state.ai_response = advice
        # Display chart and AI insight box
        display_chart(user_type, inputs, advice)

    if st.session_state.ai_response:
        st.info(st.session_state.ai_response)

    if st.button("Download PDF Report"):
        pdf_bytes = create_pdf(inputs, user_type, st.session_state.ai_response)
        st.download_button("Download PDF", pdf_bytes, file_name="report.pdf")

    if st.button("Download Excel Report"):
        excel_bytes = create_excel(inputs, user_type, st.session_state.ai_response)
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
        Provide actionable financial advice in 3-4 bullet points. Encourage contacting us to implement solutions.
        """
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300
        )
        return completion.choices[0].text.strip()
    except:
        return "Unable to generate advice at this time."

# ---------------- CHART ----------------
def display_chart(user_type, inputs, advice):
    st.subheader("Financial Overview")
    fig, ax = plt.subplots(figsize=(5,3))
    categories = list(inputs.keys())
    values = [v for v in inputs.values()]
    ax.plot(categories, values, marker='o')
    ax.set_title(f"{user_type.capitalize()} Overview")
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("AI Insights")
    st.info(advice)

# ---------------- PDF ----------------
def create_pdf(inputs, user_type, advice):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50,750,f"FinAI Report - {user_type.capitalize()}")
    c.setFont("Helvetica", 12)
    y = 720
    for k,v in inputs.items():
        c.drawString(50,y,f"{k}: {v}")
        y -= 20
    c.drawString(50,y-10,"AI Advice:")
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
    worksheet = workbook.add_worksheet("Report")
    header_format = workbook.add_format({'bold': True, 'font_color':'blue','font_size':14})
    worksheet.write('A1','FinAI Report', header_format)
    worksheet.write('A2', 'User Type')
    worksheet.write('B2', user_type)
    row = 3
    for k,v in inputs.items():
        worksheet.write(row,0,k)
        worksheet.write(row,1,v)
        row += 1
    worksheet.write(row,0,"AI Advice")
    worksheet.write(row,1,advice)
    workbook.close()
    return output.getvalue()

# ---------------- MAIN ----------------
def main():
    if not st.session_state.privacy_accepted:
        privacy_agreement()
    else:
        st.title("Welcome to FinAI")
        show_navbar()
        ai_search()
        if st.session_state.page == 'dashboard':
            dashboard()

if __name__ == "__main__":
    main()
