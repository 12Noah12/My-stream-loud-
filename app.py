import streamlit as st
import pandas as pd
import xlsxwriter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Smart Financial Planner", layout="wide")
st.markdown("""
    <style>
        body { font-family: 'Montserrat', sans-serif; color: #000000; }
        h1, h2, h3 { color: #0a2540; }
        .stButton>button {
            background-color: #0a2540; color: white; border-radius: 10px; padding: 10px 20px;
        }
        .privacy-text { color: white; }
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if 'privacy_accepted' not in st.session_state:
    st.session_state.privacy_accepted = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'goal' not in st.session_state:
    st.session_state.goal = None

# ---------------- PRIVACY AGREEMENT ----------------
def privacy_agreement():
    st.markdown("<h2 class='privacy-text'>Privacy Agreement</h2>", unsafe_allow_html=True)
    st.markdown("""
        <p class='privacy-text'>
        We take your privacy seriously. All information entered is securely stored.
        By clicking 'Accept', you enter a legally binding agreement that allows
        us to use your data to provide personalized financial recommendations.
        If you do not accept, you will be redirected and cannot proceed.
        </p>
    """, unsafe_allow_html=True)
    accept = st.checkbox("I accept the privacy agreement")
    if accept:
        st.session_state.privacy_accepted = True
        st.experimental_rerun()
    else:
        st.warning("You must accept to continue.")
        st.stop()

# ---------------- MAIN ----------------
def main():
    if not st.session_state.privacy_accepted:
        privacy_agreement()
        return

    st.title("💼 Smart Financial Planner")
    st.write("Choose your category:")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Individual"):
            st.session_state.user_type = 'individual'
            st.experimental_rerun()
    with col2:
        if st.button("Household"):
            st.session_state.user_type = 'household'
            st.experimental_rerun()
    with col3:
        if st.button("Business"):
            st.session_state.user_type = 'business'
            st.experimental_rerun()

    if st.session_state.user_type:
        show_user_module(st.session_state.user_type)

# ---------------- USER MODULE ----------------
def show_user_module(user_type):
    st.header(f"{user_type.capitalize()} Financial Planning")

    st.session_state.goal = st.selectbox("What is your goal?", ["Invest", "Optimise Tax", "Budget & Save"])

    inputs = {}
    if user_type == 'individual':
        inputs['Income'] = st.number_input("Monthly Income (ZAR)", min_value=0.0, format="%.2f")
        inputs['Expenses'] = st.number_input("Monthly Expenses (ZAR)", min_value=0.0, format="%.2f")
        inputs['Dependants'] = st.number_input("Number of Dependants", min_value=0, step=1)
    elif user_type == 'household':
        inputs['Household Income'] = st.number_input("Monthly Household Income (ZAR)", min_value=0.0, format="%.2f")
        inputs['Children'] = st.number_input("Number of Children", min_value=0, step=1)
        inputs['Expenses'] = st.number_input("Monthly Household Expenses (ZAR)", min_value=0.0, format="%.2f")
    elif user_type == 'business':
        inputs['Revenue'] = st.number_input("Monthly Revenue (ZAR)", min_value=0.0, format="%.2f")
        inputs['Expenses'] = st.number_input("Monthly Expenses (ZAR)", min_value=0.0, format="%.2f")
        inputs['Employees'] = st.number_input("Number of Employees", min_value=0, step=1)

    if st.button("Get Personalized Advice"):
        advice = generate_advice(user_type, inputs, st.session_state.goal)
        st.info(advice)

        if st.button("Download PDF Report"):
            pdf_bytes = create_pdf(user_type, inputs, advice)
            st.download_button("Download PDF", pdf_bytes, file_name=f"{user_type}_report.pdf")

        if st.button("Download Excel Report"):
            excel_bytes = create_excel(user_type, inputs, advice)
            st.download_button("Download Excel", excel_bytes, file_name=f"{user_type}_report.xlsx")

# ---------------- ADVICE GENERATION ----------------
def generate_advice(user_type, inputs, goal):
    # Placeholder AI advice
    advice_lines = [
        f"Based on your {user_type} profile and goal '{goal}':",
        "- Consider tax-efficient savings accounts.",
        "- Track all deductible expenses.",
        "- Invest in diversified portfolios.",
        "- Consult a financial advisor to implement strategies."
    ]
    return "\n".join(advice_lines)

# ---------------- PDF ----------------
def create_pdf(user_type, inputs, advice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(f"{user_type.capitalize()} Financial Report", styles['Title']))
    elements.append(Spacer(1, 20))
    for key, value in inputs.items():
        elements.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
        elements.append(Spacer(1, 10))
    elements.append(Paragraph("Advice:", styles['Heading2']))
    for line in advice.split("\n"):
        elements.append(Paragraph(line, styles['Normal']))
        elements.append(Spacer(1, 5))
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# ---------------- EXCEL ----------------
def create_excel(user_type, inputs, advice):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    worksheet.write('A1', 'User Type')
    worksheet.write('B1', user_type)
    row = 1
    for key, value in inputs.items():
        worksheet.write(row, 0, key)
        worksheet.write(row, 1, value)
        row += 1
    worksheet.write(row, 0, "Advice")
    worksheet.write(row, 1, advice)
    workbook.close()
    return output.getvalue()

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
