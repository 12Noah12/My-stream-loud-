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
st.set_page_config(page_title="OptiFin", page_icon="💼", layout="wide")

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
    input[type=text], .stNumberInput>div>input {{
        font-size: 1.2em !important;
        padding: 0.5em;
        color: black !important;
        background-color: rgba(255,255,255,0.9) !important;
    }}
    .stButton>button {{
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }}
    .privacy-text {{
        color: white;
        font-size: 1.1em;
    }}
    .ai-insight-box {{
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 10px;
        margin-top: 10px;
        background-color: rgba(255,255,255,0.85);
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if 'page' not in st.session_state:
    st.session_state.page = 'privacy'
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'privacy_accepted' not in st.session_state:
    st.session_state.privacy_accepted = False
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""
if 'category' not in st.session_state:
    st.session_state.category = None

# ---------------- PRIVACY AGREEMENT ----------------
def privacy_agreement():
    st.title("Privacy Agreement")
    st.markdown("""
    <div class="privacy-text">
    Welcome to OptiFin. All information you provide will be securely stored in our encrypted network. 
    By clicking 'Accept', you acknowledge and agree that you have read this privacy agreement, 
    and you consent to the collection and use of your data for the purpose of providing personalized 
    financial advice. This is a legally binding agreement. If you do not accept, you will be redirected 
    away from this site.
    </div>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement", key="privacy_accept")
    if accept:
        st.session_state.privacy_accepted = True
        st.session_state.page = 'home'
        st.experimental_rerun()
    else:
        st.error("You must accept to continue.")
        st.stop()

# ---------------- AI SEARCH ----------------
def ai_search():
    st.subheader("Describe your financial situation or goals")
    query = st.text_input("", placeholder="Type anything about your finances, investments, or taxes...", key="ai_search_input")
    if st.button("Submit", key="ai_search_button") and query:
        response = get_ai_redirect(query)
        st.session_state.user_type = response
        st.session_state.page = 'dashboard'
        st.experimental_rerun()

def get_ai_redirect(text):
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai.api_key:
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
    if user_type == 'individual':
        inputs['Annual Income'] = st.number_input("Annual Income (R)", min_value=0.0, format="%.2f", key="ind_income")
        inputs['Current Investments'] = st.number_input("Current Investments (R)", min_value=0.0, format="%.2f", key="ind_invest")
        inputs['Risk Tolerance (1-10)'] = st.slider("Risk Tolerance (1 = low, 10 = high)", 1, 10, key="ind_risk")
        inputs['Deductions'] = st.number_input("Annual Deductions (R)", min_value=0.0, format="%.2f", key="ind_deduct")
    elif user_type == 'household':
        inputs['Household Income'] = st.number_input("Household Annual Income (R)", min_value=0.0, format="%.2f", key="hh_income")
        inputs['Number of Children'] = st.number_input("Number of Children", min_value=0, step=1, key="hh_children")
        inputs['Current Household Investments'] = st.number_input("Current Investments (R)", min_value=0.0, format="%.2f", key="hh_invest")
        inputs['Deductions'] = st.number_input("Total Household Deductions (R)", min_value=0.0, format="%.2f", key="hh_deduct")
    elif user_type == 'business':
        inputs['Annual Revenue'] = st.number_input("Annual Revenue (R)", min_value=0.0, format="%.2f", key="bus_revenue")
        inputs['Annual Expenses'] = st.number_input("Annual Expenses (R)", min_value=0.0, format="%.2f", key="bus_expenses")
        inputs['Number of Employees'] = st.number_input("Number of Employees", min_value=0, step=1, key="bus_employees")
        inputs['Current Business Investments'] = st.number_input("Current Business Investments (R)", min_value=0.0, format="%.2f", key="bus_invest")

    if st.button("Get Personalized Advice", key="btn_get_advice"):
        advice = generate_advice_gpt(user_type, inputs)
        st.session_state.ai_response = advice
        st.info(advice)

    # ---------------- CHARTS ----------------
    st.subheader("Financial Overview")
    values = list(inputs.values())
    labels = list(inputs.keys())
    if values:
        fig, ax = plt.subplots(figsize=(5,3))
        ax.plot(labels, values, marker='o')
        ax.set_ylabel('R Amounts')
        ax.set_title('Line Chart Overview')
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # AI insight box
        st.markdown(f"<div class='ai-insight-box'><b>AI Insights:</b> Based on your inputs, strategic planning can help optimize your finances. Contact us for detailed execution.</div>", unsafe_allow_html=True)

    if st.button("Download PDF Report", key="btn_pdf"):
        pdf_bytes = create_pdf(inputs, user_type, st.session_state.ai_response)
        st.download_button("Download PDF", pdf_bytes, file_name="report.pdf")

    if st.button("Download Excel Report", key="btn_excel"):
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
        Provide actionable financial advice in 3-5 bullet points, including potential tax reductions and investment ideas. Do NOT give complete instructions; encourage the user to contact us to implement solutions.
        """
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=400
        )
        return completion.choices[0].text.strip()
    except:
        return "Unable to generate advice at this time."

# ---------------- PDF ----------------
def create_pdf(inputs, user_type, advice):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50,770,"OptiFin Financial Report")
    c.setFont("Helvetica", 12)
    c.drawString(50,750,f"User Type: {user_type.capitalize()}")
    y = 730
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
    worksheet = workbook.add_worksheet()
    header_format = workbook.add_format({'bold': True, 'font_color': 'blue', 'font_size': 14})
    worksheet.write('A1', 'OptiFin Financial Report', header_format)
    worksheet.write('A2', 'User Type', header_format)
    worksheet.write('B2', user_type.capitalize())
    row = 3
    for k,v in inputs.items():
        worksheet.write(row,0,k)
        worksheet.write(row,1,v)
        row += 1
    worksheet.write(row,0,"AI Advice", header_format)
    worksheet.write(row,1,advice)
    workbook.close()
    return output.getvalue()

# ---------------- MAIN ----------------
def main():
    if not st.session_state.privacy_accepted:
        privacy_agreement()
    elif st.session_state.page == 'home':
        st.title("Welcome to OptiFin")
        ai_search()
        select_user_type()
    elif st.session_state.page == 'dashboard':
        dashboard()

if __name__ == "__main__":
    main()
