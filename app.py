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
st.set_page_config(page_title="OptiFin", page_icon="💹", layout="wide")

# ---------------- BACKGROUND IMAGE ----------------
BG_IMAGE_URL = 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80'
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
    }}
    .black-text input[type=text], .black-text label {{
        color: black !important;
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
if 'advice' not in st.session_state:
    st.session_state.advice = ""

# ---------------- PRIVACY AGREEMENT ----------------
def privacy_agreement():
    st.title("Privacy Agreement")
    st.markdown("""
        <div style="color:white; max-width:800px;">
        <p>Welcome to OptiFin. Your privacy and security are of utmost importance. By entering your financial data and clicking 'Accept', you agree that this information will be stored securely within our encrypted network for the purpose of generating personalized financial advice.</p>
        <p>This is a legally binding agreement. You acknowledge that OptiFin will provide suggestions based on the information you provide, and any actions you take based on these suggestions are your own responsibility. We are not liable for direct financial decisions made without professional consultation.</p>
        <p>If you do not accept this agreement, you will be redirected from the site and will not be able to continue.</p>
        </div>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement")
    if accept:
        st.session_state.privacy_accepted = True
        st.session_state.page = 'home'
        st.experimental_rerun()
    else:
        st.error("You must accept to continue.")
        st.stop()

# ---------------- AI REDIRECT ----------------
def get_ai_redirect(text):
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        st.warning("OpenAI API key not found. Defaulting to Individual.")
        return 'individual'
    try:
        prompt = f"""
        Determine whether the following input is best suited for 'individual', 'household', or 'business' financial advice:
        {text}
        Respond only with one: individual, household, business
        """
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=10
        )
        result = completion.choices[0].text.strip().lower()
        if result not in ['individual','household','business']:
            return 'individual'
        return result
    except:
        return 'individual'

# ---------------- AI ADVICE GENERATION ----------------
def generate_advice_gpt(user_type, inputs):
    openai.api_key = st.secrets.get("OPENAI_API_KEY","")
    if not openai.api_key:
        return "OpenAI API key not found. Cannot generate advice."
    try:
        input_text = "\n".join([f"{k}: {v}" for k,v in inputs.items()])
        prompt = f"""
        You are a professional financial advisor. Based on the following user inputs:
        {input_text}
        Provide actionable financial advice in 3-5 bullet points.
        Include potential tax-saving strategies, investment recommendations based on risk tolerance, and savings suggestions.
        Do NOT give full instructions—encourage user to contact OptiFin for implementation.
        """
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300
        )
        return completion.choices[0].text.strip()
    except:
        return "Unable to generate advice at this time."

# ---------------- DASHBOARD INPUTS ----------------
def dashboard():
    st.title(f"{st.session_state.user_type.capitalize()} Dashboard")
    user_type = st.session_state.user_type
    inputs = {}
    st.subheader("Enter your financial information")

    if user_type == 'individual':
        inputs['Annual Income'] = st.number_input("Annual Income", min_value=0.0, format="%.2f")
        inputs['Annual Deductions'] = st.number_input("Annual Deductions", min_value=0.0, format="%.2f")
        inputs['Age'] = st.number_input("Your Age", min_value=18, max_value=100, value=30)
        inputs['Risk Tolerance'] = st.selectbox("Risk Tolerance", ["Low","Medium","High"])
    elif user_type == 'household':
        inputs['Household Income'] = st.number_input("Household Annual Income", min_value=0.0, format="%.2f")
        inputs['Number of Children'] = st.number_input("Number of Children", min_value=0, step=1)
        inputs['Total Household Deductions'] = st.number_input("Total Household Deductions", min_value=0.0, format="%.2f")
    elif user_type == 'business':
        inputs['Annual Revenue'] = st.number_input("Annual Revenue", min_value=0.0, format="%.2f")
        inputs['Annual Expenses'] = st.number_input("Annual Expenses", min_value=0.0, format="%.2f")
        inputs['Number of Employees'] = st.number_input("Number of Employees", min_value=0, step=1)

    if st.button("Get Personalized Advice"):
        st.session_state.advice = generate_advice_gpt(user_type, inputs)
        st.info(st.session_state.advice)

        # ---------------- CHARTS ----------------
        st.subheader("Financial Overview")
        col1, col2 = st.columns([2,1])
        with col1:
            x = list(inputs.keys())
            y = [v for v in inputs.values()]
            plt.figure(figsize=(6,3))
            plt.plot(x,y, marker='o', linestyle='-', color='green')
            plt.title("Financial Inputs Overview")
            plt.grid(True)
            plt.tight_layout()
            st.pyplot(plt)
            plt.clf()

            # Pie chart
            plt.figure(figsize=(3,3))
            plt.pie(y, labels=x, autopct='%1.1f%%', startangle=140)
            plt.title("Financial Distribution")
            st.pyplot(plt)
            plt.clf()
        with col2:
            st.markdown(f"""
                <div style="border:1px solid #ccc; padding:10px; border-radius:10px; background-color:#f9f9f9;">
                <h4>AI Insight</h4>
                <p>{st.session_state.advice}</p>
                </div>
            """, unsafe_allow_html=True)

        if st.button("Download PDF Report"):
            pdf_bytes = create_pdf(inputs, user_type, st.session_state.advice)
            st.download_button("Download PDF", pdf_bytes, file_name="OptiFin_Report.pdf")

        if st.button("Download Excel Report"):
            excel_bytes = create_excel(inputs, user_type, st.session_state.advice)
            st.download_button("Download Excel", excel_bytes, file_name="OptiFin_Report.xlsx")

# ---------------- PDF ----------------
def create_pdf(inputs, user_type, advice):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    # Branding Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height-50, "OptiFin Personalized Financial Report")
    c.setFont("Helvetica", 12)
    c.drawString(50, height-75, f"User Type: {user_type.capitalize()}")
    y = height - 110
    for k,v in inputs.items():
        c.drawString(50,y,f"{k}: {v}")
        y -= 20
    c.drawString(50,y-10,"AI Advice:")
    y -= 30
    for line in advice.split("\n"):
        c.drawString(60,y,line)
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
    # Branding
    header_format = workbook.add_format({'bold': True, 'font_color': 'blue', 'font_size': 14})
    worksheet.write('A1', "OptiFin Financial Report", header_format)
    worksheet.write('A2', "User Type")
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

# ---------------- HOME ----------------
def show_home():
    st.title("Welcome to OptiFin")
    st.subheader("Your AI-powered financial advisor")
    query = st.text_input("Describe your financial situation or goals", placeholder="Type anything about finances, investments, or tax...")
    if st.button("Submit Query") and query:
        st.session_state.user_type = get_ai_redirect(query)
        st.session_state.page = 'dashboard'
        st.experimental_rerun()

    st.subheader("Or select your category:")
    col1, col2, col3 = st.columns(3)
    if col1.button("Individual"):
        st.session_state.user_type = 'individual'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if col2.button("Household"):
        st.session_state.user_type = 'household'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if col3.button("Business"):
        st.session_state.user_type = 'business'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()

# ---------------- MAIN ----------------
def main():
    if not st.session_state.privacy_accepted:
        privacy_agreement()
    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'dashboard':
        dashboard()

if __name__ == "__main__":
    main()
