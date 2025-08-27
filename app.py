import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from io import BytesIO
from datetime import date
from fpdf import FPDF
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="OptiFin", layout="wide", page_icon="💹")

# --- GLOBAL STYLES ---
st.markdown("""
<style>
body {
    background-color: #f4f4f9;
    color: #111111;
    font-family: 'Arial', sans-serif;
}
.stButton button {
    background-color: #2a9d8f;
    color: white;
    font-size: 18px;
    border-radius: 8px;
    padding: 10px 20px;
}
.ai-box {
    border: 2px solid #264653;
    border-radius: 10px;
    padding: 15px;
    margin-top: 10px;
    background-color: #e9f5f5;
}
</style>
""", unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---
def create_excel(user_data, advice_text):
    df = pd.DataFrame({
        "Category": ["Income", "Risk Tolerance", "Goal", "Dependants", "Action", "AI Advice"],
        "Value": [user_data["income"], user_data["risk"], user_data["goal"], user_data["dependants"], user_data["action"], advice_text]
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="OptiFin Report")
        workbook  = writer.book
        worksheet = writer.sheets['OptiFin Report']
        header_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#264653'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    return output.getvalue()

def create_pdf(user_data, advice_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, "OptiFin Financial Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 14)
    pdf.cell(0, 10, f"Date: {date.today().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, f"Income: {user_data['income']}", ln=True)
    pdf.cell(0, 10, f"Risk Tolerance: {user_data['risk']}", ln=True)
    pdf.cell(0, 10, f"Goal Amount: {user_data['goal']}", ln=True)
    pdf.cell(0, 10, f"Action: {user_data['action']}", ln=True)
    pdf.cell(0, 10, f"Dependants: {user_data['dependants']}", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"AI Investment Advice:\n{advice_text}")
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    return pdf_output.getvalue()

# --- PAGES ---
def page_privacy():
    st.title("Privacy Agreement")
    st.markdown("""
    Please review our privacy policy. By clicking accept, you agree to our use of your data for personalized financial advice.
    """)
    if st.button("Accept Privacy Policy", key="privacy_accept"):
        st.session_state['privacy_accepted'] = True
        st.experimental_rerun()

def page_home():
    st.title("OptiFin - Personalized Financial AI")
    user_type = st.selectbox("Select User Type", ["Individual", "Household", "Business"], key="user_type_select")
    action = None
    if user_type:
        action = st.selectbox(f"What would you like to do as a {user_type}?", ["Investment Planning", "Tax Optimization", "Retirement Planning"], key="action_select")

    if action:
        st.subheader(f"{action} for {user_type}")
        # Collect user info
        income = st.number_input("Monthly Income ($)", min_value=0, step=500, key="income_input")
        risk = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"], key="risk_input")
        goal = st.number_input("Goal Amount ($)", min_value=0, step=1000, key="goal_input")
        dependants = st.number_input("Dependants (#)", min_value=0, step=1, key="dependants_input")
        user_data = {"income": income, "risk": risk, "goal": goal, "dependants": dependants, "action": action}

        # AI Advice
        advice_text = generate_ai_advice(user_data)
        st.markdown("### AI Insight")
        st.markdown(f'<div class="ai-box">{advice_text}</div>', unsafe_allow_html=True)

        # Show interactive chart and ROI projection
        show_portfolio_graph(user_data)

        # Downloads
        excel_bytes = create_excel(user_data, advice_text)
        pdf_bytes = create_pdf(user_data, advice_text)
        st.download_button("Download Excel Report", excel_bytes, file_name="OptiFin_Report.xlsx")
        st.download_button("Download PDF Report", pdf_bytes, file_name="OptiFin_Report.pdf")

# --- AI / GRAPH FUNCTIONS ---
def generate_ai_advice(user_data):
    # Investment advice based on risk and real-time stock prices
    risk = user_data["risk"]
    monthly_income = user_data["income"]
    goal = user_data["goal"]

    stock_portfolios = {
        "Low": ["AAPL", "MSFT", "GOOG"],
        "Medium": ["AAPL", "AMZN", "TSLA", "MSFT"],
        "High": ["TSLA", "AMD", "NVDA", "AMZN"]
    }
    selected_stocks = stock_portfolios.get(risk, ["AAPL", "MSFT"])
    advice = f"Based on your risk ({risk}), consider monitoring: {', '.join(selected_stocks)}. "

    # Live price check
    current_prices = []
    for stock in selected_stocks:
        try:
            ticker = yf.Ticker(stock)
            price = ticker.history(period="1d")['Close'][-1]
            current_prices.append((stock, price))
        except:
            current_prices.append((stock, "N/A"))

    advice += "Current prices: " + ", ".join([f"{s}: ${p}" for s,p in current_prices]) + ". "
    advice += f"With a monthly contribution of ${monthly_income*0.2}, your projected savings could approach ${goal}. Contact us for full guidance."
    return advice

def show_portfolio_graph(user_data):
    # Simple projected portfolio growth
    months = 12
    monthly_contribution = user_data["income"]*0.2
    risk_multiplier = {"Low":1.02, "Medium":1.05, "High":1.1}.get(user_data["risk"],1.03)
    balances = []
    balance = 0
    for m in range(months):
        balance = (balance + monthly_contribution)*risk_multiplier
        balances.append(balance)

    fig, ax = plt.subplots(figsize=(5,2))
    ax.plot(range(1, months+1), balances, marker='o')
    ax.set_title("Projected Portfolio Growth (Next 12 Months)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Balance ($)")
    st.pyplot(fig)

# --- MAIN ---
def main():
    if 'privacy_accepted' not in st.session_state:
        st.session_state['privacy_accepted'] = False

    if not st.session_state['privacy_accepted']:
        page_privacy()
    else:
        page_home()

if __name__ == "__main__":
    main()
