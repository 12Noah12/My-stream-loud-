import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

# ----------------- CSS & Background -----------------
st.markdown("""
<style>
.stApp {
  background-image: url('https://images.unsplash.com/photo-1567427013953-2451a0c35ef7?q=80&w=1950&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
.optifin-overlay {
  background: rgba(255,255,255,0.92);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  color: #000;
  font-size: 16px;
}
.ai-box {
  background: rgba(11,19,32,0.95);
  color: #eff4ff;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(255,255,255,0.08);
}
.chart-box {
  background: rgba(255,255,255,0.95);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 14px;
  padding: 12px;
}
.stButton>button {
  background: linear-gradient(135deg,#1f7a8c,#2a9d8f);
  color: #fff;
  border: 0;
  padding: 0.6rem 1rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# ----------------- App State -----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_goal' not in st.session_state:
    st.session_state.user_goal = None

# ----------------- Home Page -----------------
def show_home():
    st.title("OptiFin - AI Financial Advisor")
    st.markdown('<div class="optifin-overlay">Select your user type:</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Individual"):
            st.session_state.user_type = "Individual"
    with col2:
        if st.button("Household"):
            st.session_state.user_type = "Household"
    with col3:
        if st.button("Business"):
            st.session_state.user_type = "Business"

# ----------------- User Goal Selection -----------------
def select_goal():
    st.markdown('<div class="optifin-overlay">Select what you want to do:</div>', unsafe_allow_html=True)
    options = ["Investment Advice", "Tax Optimization", "Retirement Planning"]
    st.session_state.user_goal = st.radio("Choose an option:", options)

# ----------------- AI Advisor -----------------
def ai_advisor(user_type, user_goal, data):
    st.markdown(f'<div class="ai-box"><strong>AI Insight:</strong> Here is tailored advice for {user_type} focusing on {user_goal}.</div>', unsafe_allow_html=True)
    # Example chart
    fig, ax = plt.subplots(figsize=(4,3))
    ax.plot([1,2,3,4], [data.get('metric',1),2,3,4])
    ax.set_title("Projected Growth")
    st.markdown('<div class="chart-box"></div>', unsafe_allow_html=True)
    st.pyplot(fig)

# ----------------- PDF Export -----------------
def create_pdf(user_data, advice_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="OptiFin Report", ln=1, align="C")
    for key, val in user_data.items():
        pdf.cell(0, 8, txt=f"{key}: {val}", ln=1)
    pdf.ln(5)
    pdf.multi_cell(0, 8, advice_text)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes

# ----------------- App Main -----------------
def main():
    show_home()
    if st.session_state.user_type:
        select_goal()
    if st.session_state.user_type and st.session_state.user_goal:
        st.markdown('<div class="optifin-overlay">Enter your financial data:</div>', unsafe_allow_html=True)
        metric = st.number_input("Current Savings ($)", min_value=0, value=1000)
        data = {'metric': metric}
        advice_text = f"This is example advice for {st.session_state.user_type} focusing on {st.session_state.user_goal}."
        ai_advisor(st.session_state.user_type, st.session_state.user_goal, data)
        # PDF Download
        pdf_bytes = create_pdf(data, advice_text)
        st.download_button("Download PDF Report", pdf_bytes, "OptiFin_Report.pdf", "application/pdf")

main()
