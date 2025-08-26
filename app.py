# app.py
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
import hashlib
import json
import os
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
st.set_page_config(page_title="OptiFin", page_icon="💼", layout="wide")

BG_IMAGE_URL = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80"

# ---------------- STYLES ----------------
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
        color: black;
    }}
    input[type=text], input[type=number], select {{
        font-size: 1.2em;
        padding: 0.5em;
        color: black;
    }}
    .privacy-text {{
        color: white;
        font-size: 1.1em;
    }}
    .btn {{
        background-color:#1f77b4;color:white;padding:0.5em 1em;border-radius:5px;border:none;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False

USERS_FILE = "users.json"
BOOKINGS_FILE = "bookings.json"

# ---------------- UTILITIES ----------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE,"r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE,"w") as f:
        json.dump(users,f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE,"r") as f:
            return json.load(f)
    return {}

def save_bookings(bookings):
    with open(BOOKINGS_FILE,"w") as f:
        json.dump(bookings,f)

# ---------------- LOGIN / REGISTER ----------------
def login_page():
    st.title("Welcome to OptiFin")
    st.subheader("Client Login")
    users = load_users()

    tab1, tab2 = st.tabs(["Login","Register"])
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if username in users and users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.session_state.page = "privacy"
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            if new_user in users:
                st.error("Username exists")
            elif new_user == "" or new_pass == "":
                st.error("Enter valid credentials")
            else:
                users[new_user] = {"password":hash_password(new_pass)}
                save_users(users)
                st.success("User registered. Please login.")

# ---------------- PRIVACY AGREEMENT ----------------
def privacy_page():
    st.title("Privacy Agreement")
    st.markdown("""
    <div class="privacy-text">
    By using OptiFin, you agree to our data handling policies. All personal and financial information entered
    is securely stored on our servers. This data is used solely to generate personalized financial advice,
    investment suggestions, and optimize tax strategies. Accepting this agreement constitutes a legally binding consent.
    You may refuse and exit, in which case no data will be stored.
    </div>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement")
    if accept:
        st.session_state.privacy_accepted = True
        st.session_state.page = "home"
        st.experimental_rerun()
    else:
        st.info("You must accept to continue. Closing session in 5 seconds...")
        st.stop()

# ---------------- AI REDIRECT ----------------
def get_ai_redirect(text):
    openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        return "individual"
    try:
        prompt = f"Classify this query into 'individual', 'household', or 'business': {text}"
        completion = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=10)
        res = completion.choices[0].text.strip().lower()
        if res not in ["individual","household","business"]:
            return "individual"
        return res
    except:
        return "individual"

# ---------------- HOME PAGE ----------------
def home_page():
    st.title("OptiFin - Smart Financial Advisor")
    st.subheader("Describe your financial situation or goals")
    query = st.text_input("", placeholder="Type about income, investments, tax or business...")
    if st.button("Submit Query"):
        redir = get_ai_redirect(query)
        st.session_state.user_type = redir
        st.session_state.page = "dashboard"
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Or choose a category")
    col1, col2, col3 = st.columns(3)
    if col1.button("Individual"):
        st.session_state.user_type = "individual"
        st.session_state.page = "dashboard"
        st.experimental_rerun()
    if col2.button("Household"):
        st.session_state.user_type = "household"
        st.session_state.page = "dashboard"
        st.experimental_rerun()
    if col3.button("Business"):
        st.session_state.user_type = "business"
        st.session_state.page = "dashboard"
        st.experimental_rerun()

# ---------------- DASHBOARD ----------------
def dashboard():
    st.title(f"{st.session_state.user_type.capitalize()} Dashboard")
    inputs = {}
    ut = st.session_state.user_type

    if ut == "individual":
        inputs["Annual Income"] = st.number_input("Annual Income", min_value=0.0, format="%.2f")
        inputs["Annual Deductions"] = st.number_input("Annual Deductions", min_value=0.0, format="%.2f")
        risk = st.selectbox("Risk Tolerance", ["Low","Medium","High"])
        inputs["Risk"] = risk
    elif ut == "household":
        inputs["Household Income"] = st.number_input("Household Annual Income", min_value=0.0, format="%.2f")
        inputs["Children"] = st.number_input("Number of Children", min_value=0)
        inputs["Deductions"] = st.number_input("Total Household Deductions", min_value=0.0, format="%.2f")
        risk = st.selectbox("Risk Tolerance", ["Low","Medium","High"])
        inputs["Risk"] = risk
    elif ut == "business":
        inputs["Revenue"] = st.number_input("Annual Revenue", min_value=0.0, format="%.2f")
        inputs["Expenses"] = st.number_input("Annual Expenses", min_value=0.0, format="%.2f")
        inputs["Employees"] = st.number_input("Number of Employees", min_value=0)
        risk = st.selectbox("Risk Tolerance", ["Low","Medium","High"])
        inputs["Risk"] = risk

    if st.button("Get Personalized Advice"):
        advice = generate_advice(inputs, ut)
        st.info(advice)
        # Pie chart example
        fig, ax = plt.subplots()
        labels = list(inputs.keys())
        values = [float(v) if isinstance(v,(int,float)) else 0 for v in inputs.values()]
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        st.pyplot(fig)

    if st.button("Download PDF"):
        pdf_bytes = create_pdf(inputs, ut, advice)
        st.download_button("Download PDF", pdf_bytes, file_name="OptiFin_Report.pdf")

    if st.button("Download Excel"):
        excel_bytes = create_excel(inputs, ut, advice)
        st.download_button("Download Excel", excel_bytes, file_name="OptiFin_Report.xlsx")

# ---------------- AI ADVICE ----------------
def generate_advice(inputs, ut):
    openai.api_key = st.secrets.get("OPENAI_API_KEY","")
    if not openai.api_key:
        return "Cannot generate advice: OpenAI key missing"
    try:
        text = "\n".join([f"{k}: {v}" for k,v in inputs.items()])
        prompt = f"You are a smart financial advisor. User inputs:\n{text}\nProvide actionable advice including investment and tax strategies but encourage contacting a professional for implementation. Give up-to-date market suggestions."
        completion = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=400)
        return completion.choices[0].text.strip()
    except:
        return "Unable to generate advice at this time"

# ---------------- PDF / EXCEL ----------------
def create_pdf(inputs, ut, advice):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold",14)
    c.drawString(50,750,"OptiFin Financial Report")
    c.setFont("Helvetica",12)
    c.drawString(50,730,f"User Type: {ut.capitalize()}")
    y = 710
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

def create_excel(inputs, ut, advice):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    worksheet.write("A1","OptiFin Financial Report")
    worksheet.write("A2","User Type")
    worksheet.write("B2", ut)
    row = 3
    for k,v in inputs.items():
        worksheet.write(row,0,k)
        worksheet.write(row,1,v)
        row += 1
    worksheet.write(row,0,"Advice")
    worksheet.write(row,1,advice)
    workbook.close()
    return output.getvalue()

# ---------------- MAIN ----------------
def main():
    if not st.session_state.logged_in:
        login_page()
    elif not st.session_state.privacy_accepted:
        privacy_page()
    else:
        if st.session_state.page == "home":
            home_page()
        elif st.session_state.page == "dashboard":
            dashboard()

if __name__ == "__main__":
    main()
