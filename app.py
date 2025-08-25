import streamlit as st

# ------------------ Privacy Agreement ------------------
def show_privacy_and_block():
    st.title("🔒 Privacy Agreement")

    st.write("""
    Before using this AI Financial Advisor, please read and accept the privacy agreement.  
    """)

    agreement_text = """
    ✅ Your financial inputs will not be shared.  
    ✅ Advice is based on market insights and tax strategies.  
    ✅ You remain responsible for final investment decisions.  
    """

    st.info(agreement_text)

    if st.checkbox("I have read and agree to the privacy policy"):
        if st.button("Continue"):
            st.session_state["accepted_privacy"] = True
            st.rerun()
    else:
        st.warning("You must accept the privacy agreement to proceed.")

# ------------------ AI Financial Advisor ------------------
def show_financial_dashboard():
    st.title("🤖 Smart AI Financial Advisor")
    st.subheader("Personalized Investment & Tax Optimization")

    st.write("Enter your financial details below to receive tailored investment advice:")

    # ------------------ Inputs ------------------
    income = st.number_input("💵 Monthly Income (R)", min_value=0, step=1000)
    expenses = st.number_input("📉 Monthly Expenses (R)", min_value=0, step=500)
    retirement_age = st.number_input("🎯 Retirement Age", min_value=50, max_value=75, value=60)
    current_savings = st.number_input("💰 Current Savings (R)", min_value=0, step=5000)
    monthly_investment = st.number_input("📈 Monthly Investment (R)", min_value=0, step=500)

    st.markdown("---")

    if st.button("Generate AI Advice"):
        disposable = income - expenses
        st.write(f"✅ Your disposable income: **R{disposable:,.2f}**")

        # ------------------ Advice Engine ------------------
        advice = []

        if disposable <= 0:
            advice.append("⚠️ You are spending more than you earn. Reduce expenses before investing.")
        else:
            # Retirement advice
            if retirement_age < 60:
                advice.append("📊 Consider increasing retirement savings — early retirement requires larger monthly contributions.")
            else:
                advice.append("✅ Your retirement age goal is reasonable. Stay consistent with investments.")

            # Tax efficiency
            if monthly_investment > 0:
                advice.append("💡 Max out your **Tax-Free Savings Account (TFSA)** first (limit ~R36,000/year).")
                advice.append("📑 Consider **Retirement Annuities (RA)** — contributions are tax-deductible up to 27.5% of income.")
                advice.append("🌍 Diversify with global ETFs (e.g., S&P 500 tracker) for long-term growth.")
            else:
                advice.append("⚠️ You are not investing monthly. Start with even R500/month in a TFSA or ETF.")

            # Emergency fund
            if current_savings < (expenses * 3):
                advice.append("🚨 Build an emergency fund (3–6 months of expenses) before aggressive investing.")

        # Display advice
        st.markdown("### 📌 AI-Generated Financial Plan")
        for tip in advice:
            st.write(tip)

        # Future Value Projection (basic compound interest)
        if monthly_investment > 0:
            years = retirement_age - 25  # assume starting at 25, you can adjust
            rate = 0.08  # 8% annual return average
            future_value = current_savings * ((1 + rate) ** years)
            future_value += monthly_investment * (((1 + rate) ** years - 1) / rate) * (1 + rate)
            st.success(f"📈 Estimated Retirement Value at age {retirement_age}: **R{future_value:,.2f}**")

# ------------------ Main App ------------------
def main():
    # Session state init
    if "accepted_privacy" not in st.session_state:
        st.session_state["accepted_privacy"] = False

    if not st.session_state["accepted_privacy"]:
        show_privacy_and_block()
    else:
        show_financial_dashboard()

if __name__ == "__main__":
    main()
