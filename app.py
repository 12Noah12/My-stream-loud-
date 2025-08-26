import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="OptiFin", layout="wide", page_icon="💼")

# ---------------- BACKGROUND ----------------
BG_IMAGE_URL = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1470&q=80"
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
    }}
    .title {{
        color: white;
        font-size: 2.5em;
        font-weight: bold;
    }}
    .subheader {{
        color: white;
        font-size: 1.5em;
    }}
    input, .stButton > button {{
        color: black;
        background-color: #f0f0f0;
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
def show_privacy():
    st.title("Privacy Agreement", anchor=False)
    st.markdown("""
    <div style='color:white;'>
    All data entered on this platform is stored securely in compliance with applicable privacy laws.
    By clicking 'Accept', you enter a legally binding agreement that allows OptiFin to use your 
    information solely for providing personalized financial advice. No data will be shared 
    externally without your explicit consent. If you do not accept, you will be redirected away 
    from this website.
    </div>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement", key="privacy_accept")
    if accept:
        st.session_state.privacy_accepted = True
        st.experimental_rerun()
    else:
        st.warning("You must accept to continue.")
        st.stop()

# ---------------- HOME PAGE ----------------
def show_home():
    st.title("Welcome to OptiFin", anchor=False)
    st.subheader("Get personalized financial advice", anchor=False)

    st.markdown("### Select your profile type:")
    col1, col2, col3 = st.columns(3)

    if col1.button("Individual", key="home_individual_btn"):
        st.session_state.user_type = 'individual'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if col2.button("Household", key="home_household_btn"):
        st.session_state.user_type = 'household'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()
    if col3.button("Business", key="home_business_btn"):
        st.session_state.user_type = 'business'
        st.session_state.page = 'dashboard'
        st.experimental_rerun()

# ---------------- DASHBOARD ----------------
def show_dashboard():
    st.title(f"{st.session_state.user_type.capitalize()} Dashboard", anchor=False)
    user_type = st.session_state.user_type
    inputs = {}

    # ---------------- INPUTS ----------------
    if user_type == 'individual':
        inputs['Annual Income'] = st.number_input("Annual Income (R)", min_value=0.0, key="ind_income")
        inputs['Current Investments'] = st.number_input("Current Investment Value (R)", min_value=0.0, key="ind_invest")
        inputs['Risk Tolerance'] = st.slider("Risk Tolerance (1-10)", 1, 10, key="ind_risk")
        inputs['Deductions'] = st.number_input("Annual Deductions (R)", min_value=0.0, key="ind_deduction")
    elif user_type == 'household':
        inputs['Household Income'] = st.number_input("Household Annual Income (R)", min_value=0.0, key="hh_income")
        inputs['Number of Children'] = st.number_input("Number of Children", min_value=0, step=1, key="hh_children")
        inputs['Household Deductions'] = st.number_input("Total Household Deductions (R)", min_value=0.0, key="hh_deduction")
        inputs['Current Investments'] = st.number_input("Current Investments (R)", min_value=0.0, key="hh_invest")
    elif user_type == 'business':
        inputs['Annual Revenue'] = st.number_input("Annual Revenue (R)", min_value=0.0, key="biz_revenue")
        inputs['Annual Expenses'] = st.number_input("Annual Expenses (R)", min_value=0.0, key="biz_expenses")
        inputs['Number of Employees'] = st.number_input("Employees", min_value=0, step=1, key="biz_employees")
        inputs['Current Investments'] = st.number_input("Current Business Investments (R)", min_value=0.0, key="biz_invest")

    # ---------------- ADVICE ----------------
    advice_box = st.empty()
    if st.button("Get Personalized Advice", key="btn_get_advice"):
        advice = generate_advice(inputs, user_type)
        st.session_state.ai_response = advice
        advice_box.info(advice)

    # ---------------- CHART ----------------
    if inputs:
        st.subheader("Financial Overview")
        fig, ax = plt.subplots(figsize=(4,3))
        if user_type in ['individual','household']:
            labels = list(inputs.keys())
            values = [v if isinstance(v,(int,float)) else 0 for v in inputs.values()]
            ax.plot(labels, values, marker='o')
            ax.set_title("Your Financial Data")
        elif user_type == 'business':
            labels = ['Revenue','Expenses','Investments']
            values = [inputs.get('Annual Revenue',0), inputs.get('Annual Expenses',0), inputs.get('Current Investments',0)]
            ax.bar(labels, values, color=['green','red','blue'])
            ax.set_title("Business Financial Overview")
        st.pyplot(fig)

    # ---------------- DOWNLOAD REPORTS ----------------
    if st.button("Download PDF Report", key="btn_download_pdf"):
        pdf_bytes = create_pdf(inputs, user_type, st.session_state.ai_response)
        st.download_button("Download PDF", pdf_bytes, file_name="OptiFin_Report.pdf", key="download_pdf")
    if st.button("Download Excel Report", key="btn_download_excel"):
        excel_bytes = create_excel(inputs, user_type, st.session_state.ai_response)
        st.download_button("Download Excel", excel_bytes, file_name="OptiFin_Report.xlsx", key="download_excel")

# ---------------- AI ADVICE ----------------
def generate_advice(inputs, user_type):
    openai.api_key = st.secrets.get("OPENAI_API_KEY","")
    if not openai.api_key:
        return "OpenAI API key not found. Cannot generate advice."

    try:
        input_text = "\n".join([f"{k}: {v}" for k,v in inputs.items()])
        prompt = f"""
        You are a professional financial advisor. Based on these user inputs:
        {input_text}
        Provide actionable financial advice in bullet points. Focus on ways to reduce taxes, improve investments,
        and optimize finances. Do not reveal full instructions—encourage contacting OptiFin to implement strategies.
        """
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=350
        )
        return completion.choices[0].text.strip()
    except:
        return "Unable to generate advice at this time."

# ---------------- PDF ----------------
def create_pdf(inputs, user_type, advice):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50,750,"OptiFin Financial Report")
    c.setFont("Helvetica", 12)
    c.drawString(50,730,f"User Type: {user_type.capitalize()}")
    y = 710
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
    worksheet = workbook.add_worksheet("OptiFin Report")
    bold = workbook.add_format({'bold': True})
    worksheet.write('A1', "OptiFin Financial Report", bold)
    worksheet.write('A2', f"User Type: {user_type.capitalize()}")
    row = 3
    for k,v in inputs.items():
        worksheet.write(row,0,k)
        worksheet.write(row,1,v)
        row += 1
    worksheet.write(row+1,0,"AI Advice")
    for i,line in enumerate(advice.split("\n")):
        worksheet.write(row+2+i,0,line)
    workbook.close()
    return output.getvalue()

# ---------------- MAIN ----------------
def main():
    if not st.session_state.privacy_accepted:
        show_privacy()
    elif st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'dashboard':
        show_dashboard()
    else:
        show_home()

if __name__ == "__main__":
    main()

