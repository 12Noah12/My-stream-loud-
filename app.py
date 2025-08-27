import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="OptiFin", layout="wide", page_icon="💰")

# --- Background Styling ---
st.markdown(
    """
    <style>
    body {
        background-image: url('https://images.unsplash.com/photo-1605902711622-cfb43c4435eb?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        color: white;
    }
    .stButton button {
        background-color: #00BFFF;
        color: white;
        font-size: 18px;
        padding: 10px 20px;
        border-radius: 10px;
    }
    .stTextInput input {
        color: black;
        background-color: rgba(255,255,255,0.8);
    }
    .stNumberInput input {
        color: black;
        background-color: rgba(255,255,255,0.8);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Privacy Agreement ---
def page_privacy():
    st.header("Privacy Agreement")
    st.write("Please read and accept our privacy agreement to continue.")
    st.write("""
    We value your privacy. Any information provided is strictly confidential. 
    The AI recommendations are suggestions only and do not constitute financial advice.
    """)
    if st.button("Accept"):
        st.session_state['privacy_accepted'] = True
        st.experimental_rerun()

# --- User Type Selection ---
def page_home():
    st.header("Welcome to OptiFin")
    st.write("Select your user type to start:")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Individual"):
            st.session_state['user_type'] = "Individual"
    with col2:
        if st.button("Household"):
            st.session_state['user_type'] = "Household"
    with col3:
        if st.button("Business"):
            st.session_state['user_type'] = "Business"

# --- User Options ---
def page_options():
    st.header(f"{st.session_state['user_type']} Options")
    option = st.radio("Select what you want to do:",
                      ["Investment Planning", "Tax Optimization", "Retirement Planning"])
    st.session_state['user_option'] = option

# --- User Inputs ---
def page_inputs():
    st.header("Provide Your Details")
    st.session_state['income'] = st.number_input("Annual Income ($)", min_value=0)
    st.session_state['dependants'] = st.number_input("Number of Dependants", min_value=0)
    st.session_state['risk_tolerance'] = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"])
    st.session_state['goal_amount'] = st.number_input("Goal Amount for Retirement ($)", min_value=0)

# --- AI Advisor ---
def page_advisor():
    st.header("AI Advisor Insights")
    
    # Real-time market data
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "SPY"]
    data = {ticker: yf.Ticker(ticker).history(period="1mo")['Close'] for ticker in tickers}
    df = pd.DataFrame(data)
    
    # Small chart block
    st.subheader("Recent Stock Trends")
    fig, ax = plt.subplots(figsize=(6,3))
    df.plot(ax=ax)
    st.pyplot(fig)
    
    # AI insight box
    st.subheader("AI Insights")
    risk = st.session_state.get('risk_tolerance', 'Medium')
    income = st.session_state.get('income', 0)
    dependants = st.session_state.get('dependants', 0)
    goal = st.session_state.get('goal_amount', 0)
    
    # Simple calculation example
    advice_text = f"""
    Based on your income of ${income} and {dependants} dependants,
    with {risk} risk tolerance:
    - Recommended investment allocation: 60% stocks, 30% bonds, 10% cash.
    - You could potentially save ${income*0.15} annually if optimized.
    - Retirement goal of ${goal} could be achieved in {goal/(income*0.15):.1f} years.
    """
    st.text_area("AI Recommendation", value=advice_text, height=200)

    return advice_text

# --- PDF Export ---
def create_pdf(advice_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="OptiFin Report", ln=True, align='C')
    pdf.multi_cell(0, 10, advice_text)
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_bytes = pdf_output.getvalue()
    return pdf_bytes

# --- Main ---
def main():
    if 'privacy_accepted' not in st.session_state:
        st.session_state['privacy_accepted'] = False
    if 'user_type' not in st.session_state:
        st.session_state['user_type'] = None
    
    if not st.session_state['privacy_accepted']:
        page_privacy()
        return
    
    if st.session_state['user_type'] is None:
        page_home()
        return

    page_options()
    page_inputs()
    advice_text = page_advisor()
    
    # Export button
    if st.button("Download PDF"):
        pdf_bytes = create_pdf(advice_text)
        st.download_button(label="Download Report", data=pdf_bytes, file_name="OptiFin_Report.pdf")

if __name__ == "__main__":
    main()
