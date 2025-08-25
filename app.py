import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import random

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FinAI Enterprise", page_icon="💡", layout="wide")

# ---------------- NAVIGATION PAGES ----------------
PAGES = {
    "home": "Home",
    "business_tax": "Business Tax Optimization",
    "family_tax": "Family Tax Optimization",
    "investments": "Investments Dashboard",
    "sme": "SME Dashboard",
    "premium": "Premium Modules",
    "estate": "Estate Planning"
}

# ---------------- BACKGROUND STYLES ----------------
BG_STYLES = {
    "home": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
    "business_tax": "linear-gradient(135deg, #00c6ff 0%, #0072ff 100%)",
    "family_tax": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
    "investments": "linear-gradient(135deg, #ff512f 0%, #dd2476 100%)",
    "sme": "linear-gradient(135deg, #485563 0%, #29323c 100%)",
    "premium": "linear-gradient(135deg, #f7971e 0%, #ffd200 100%)",
    "estate": "linear-gradient(135deg, #7b4397 0%, #dc2430 100%)"
}

# ---------------- SECTION TEXT ----------------
SECTION_TEXT = {
    "home": "👋 Welcome to FinAI Enterprise! Select your user type below to access tailored tools.",
    "business_tax": "💼 Optimize your business taxes with AI-guided strategies.",
    "family_tax": "🏠 Optimize your personal/family taxes efficiently.",
    "investments": "📈 Grow your wealth with AI-guided investments and portfolio simulations.",
    "sme": "🏢 Manage your business efficiently with our SME tools and KPIs.",
    "premium": "🌟 Unlock powerful premium features here.",
    "estate": "⚖️ Plan your estate and inheritance efficiently with visualization."
}

# ---------------- INIT STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------------- CSS STYLING ----------------
st.markdown("""
<style>
.block-container { padding-top: 6rem; }
/* Navbar */
.navbar { position: fixed; top: 0; left: 0; width: 100%; background: rgba(255,255,255,0.95);
backdrop-filter: blur(10px); box-shadow: 0 2px 8px rgba(0,0,0,0.15);
padding: 0.7rem 1.5rem; display: flex; justify-content: space-between; align-items: center; z-index: 1000; }
.navbar .logo { font-weight: 700; font-size: 1.3rem; color: #2563eb; }
.nav-links { display: flex; gap: 1rem; }
.nav-button button { background: none; border: none; font-weight: 600;
padding: 0.3rem 0.8rem; border-radius: 6px; cursor: pointer; transition: background 0.3s; }
.nav-button button:hover { background: rgba(37,99,235,0.1); }
/* AI Search Bar */
.ai-search { display: flex; justify-content: center; margin-top: 3rem; }
.ai-search input { font-weight: 700; font-size: 1.5rem; border: 2px solid #2563eb;
border-radius: 20px; padding: 1rem 2rem; width: 60%; text-align: center;
box-shadow: 0 0 25px rgba(37,99,235,0.5); animation: pulse 2s infinite; }
.ai-search input:focus { outline: none; box-shadow: 0 0 35px rgba(37,99,235,0.9); }
@keyframes pulse { 0% { box-shadow: 0 0 15px rgba(37,99,235,0.5); }
50% { box-shadow: 0 0 35px rgba(37,99,235,0.9); } 100% { box-shadow: 0 0 15px rgba(37,99,235,0.5); } }
/* Tooltip */
.tooltip { position: relative; display: inline-block; border-bottom: 1px dotted white; cursor: help; }
.tooltip .tooltiptext { visibility: hidden; width: 250px; background-color: rgba(0,0,0,0.8);
color: #fff; text-align: left; padding: 10px; border-radius: 6px;
position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -125px;
opacity: 0; transition: opacity 0.3s; }
.tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
/* Cards */
.card { background: rgba(255,255,255,0.1); padding: 1rem; margin: 1rem 0;
border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.3); }
</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ----------------
with st.container():
    st.markdown(f"""
    <div class="navbar">
        <div class="logo">💡 FinAI Enterprise</div>
        <div class="nav-links">
            {''.join([f'<span class="nav-button"><button onclick="window.parent.postMessage({{page: \'{k}\' }}, \'*\')" type="button">{v}</button></span>' for k,v in PAGES.items()])}
        </div>
        <div class="dots">⋮</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------- NAVIGATION ----------------
for key in PAGES.keys():
    if st.button(PAGES[key], key=f"btn-{key}"):
        st.session_state.page = key

# ---------------- APPLY BACKGROUND ----------------
st.markdown(f"""
    <style>
    body {{
        background: {BG_STYLES[st.session_state.page]};
        color: white;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------- PAGE TITLE ----------------
st.title(PAGES[st.session_state.page])
st.write(SECTION_TEXT[st.session_state.page])

# ---------------- HOME PAGE ----------------
if st.session_state.page == "home":
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:3rem; margin-top:3rem;">
        <button onclick="window.parent.postMessage({page:'business_tax'}, '*')" 
            style="padding:1rem 2rem; font-size:1.3rem; border-radius:16px; font-weight:700; cursor:pointer; background:#2563eb; color:white; border:none; box-shadow:0 0 20px rgba(37,99,235,0.6);">
            Business
        </button>
        <button onclick="window.parent.postMessage({page:'family_tax'}, '*')" 
            style="padding:1rem 2rem; font-size:1.3rem; border-radius:16px; font-weight:700; cursor:pointer; background:#38ef7d; color:white; border:none; box-shadow:0 0 20px rgba(56,239,125,0.6);">
            Family
        </button>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="ai-search">
        <input type="text" placeholder="🔍 Ask FinAI anything...">
    </div>
    """, unsafe_allow_html=True)
# ---------------- BUSINESS TAX MODULE ----------------
if st.session_state.page == "business_tax":
    st.header("Business Tax Optimization 💼")

    st.markdown("### Input Your Business Details")

    with st.form("business_tax_form"):
        revenue = st.number_input("Annual Revenue ($) 🏢", min_value=0, value=500000,
                                  help="Total revenue your business generated in the year.")
        expenses = st.number_input("Total Expenses ($) 💸", min_value=0, value=300000,
                                   help="Sum of all operating expenses, salaries, rent, etc.")
        deductions = st.number_input("Tax Deductions ($) 📝", min_value=0, value=50000,
                                     help="Allowable business tax deductions.")
        vat_paid = st.number_input("VAT Paid ($) 🏷️", min_value=0, value=40000,
                                   help="Total VAT you paid on purchases.")
        submit_business = st.form_submit_button("Calculate Business Tax")

    if submit_business:
        taxable_income = revenue - expenses - deductions
        tax_rate = 0.28  # example corporate tax
        tax_owed = max(0, taxable_income * tax_rate - vat_paid)
        st.success(f"💰 Estimated Business Tax Owed: ${tax_owed:,.2f}")

        # Charts
        st.subheader("Revenue vs Expenses vs Tax")
        fig, ax = plt.subplots()
        categories = ['Revenue', 'Expenses', 'Deductions', 'VAT Paid', 'Tax Owed']
        values = [revenue, expenses, deductions, vat_paid, tax_owed]
        ax.bar(categories, values, color=['#2563eb','#38ef7d','#fcd34d','#f87171','#9333ea'])
        ax.set_ylabel("Amount ($)")
        st.pyplot(fig)

# ---------------- FAMILY TAX MODULE ----------------
if st.session_state.page == "family_tax":
    st.header("Family/Personal Tax Optimization 🏠")
    st.markdown("### Input Your Family Income Details")

    with st.form("family_tax_form"):
        salary = st.number_input("Annual Salary ($) 👨‍👩‍👧‍👦", min_value=0, value=120000,
                                 help="Total combined salary of all family members.")
        investment_income = st.number_input("Investment Income ($) 💹", min_value=0, value=10000,
                                            help="Income earned from dividends, interest, etc.")
        deductions = st.number_input("Total Deductions ($) 📝", min_value=0, value=20000,
                                     help="Include retirement contributions, donations, etc.")
        tax_credits = st.number_input("Tax Credits ($) 🏷️", min_value=0, value=5000,
                                      help="Family tax credits applicable.")
        submit_family = st.form_submit_button("Calculate Family Tax")

    if submit_family:
        total_income = salary + investment_income
        taxable_income = max(0, total_income - deductions)
        tax_rate = 0.25
        tax_owed = max(0, taxable_income * tax_rate - tax_credits)
        st.success(f"💰 Estimated Family Tax Owed: ${tax_owed:,.2f}")

        # Pie chart for allocation
        st.subheader("Income Allocation")
        labels = ['Tax Owed', 'Deductions', 'Remaining Income']
        remaining = total_income - tax_owed - deductions
        sizes = [tax_owed, deductions, remaining]
        fig2, ax2 = plt.subplots()
        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#9333ea','#fcd34d','#38ef7d'])
        ax2.axis('equal')
        st.pyplot(fig2)

# ---------------- TOOLTIP EXAMPLES ----------------
# Already included via `help` parameter in Streamlit input widgets
# ---------------- INVESTMENTS DASHBOARD ----------------
if st.session_state.page == "investments":
    st.header("Investments Dashboard 📈")
    st.markdown("### Input Your Portfolio Details")

    with st.form("investments_form"):
        initial_investment = st.number_input("Initial Investment ($) 💰", min_value=0, value=50000,
                                             help="Total amount you want to invest initially.")
        monthly_contribution = st.number_input("Monthly Contribution ($) 🏦", min_value=0, value=2000,
                                               help="Amount you plan to add every month.")
        expected_return = st.slider("Expected Annual Return (%) 📊", min_value=0.0, max_value=20.0, value=7.0,
                                    help="Average annual return expected from your portfolio.")
        years = st.number_input("Investment Horizon (Years) ⏳", min_value=1, max_value=50, value=20,
                                help="Number of years you plan to invest.")
        submit_investments = st.form_submit_button("Simulate Portfolio")

    if submit_investments:
        months = years * 12
        monte_carlo_runs = 1000
        ending_balances = []

        for _ in range(monte_carlo_runs):
            balance = initial_investment
            monthly_return = expected_return / 12 / 100
            for _ in range(months):
                balance = balance * (1 + np.random.normal(monthly_return, 0.02)) + monthly_contribution
            ending_balances.append(balance)

        ending_balances = np.array(ending_balances)
        st.success(f"💸 Expected Portfolio Value After {years} Years: ${np.mean(ending_balances):,.2f}")
        st.info(f"10th percentile: ${np.percentile(ending_balances,10):,.2f} | 90th percentile: ${np.percentile(ending_balances,90):,.2f}")

        # Histogram
        st.subheader("Monte Carlo Distribution of Ending Portfolio Value")
        fig, ax = plt.subplots(figsize=(8,4))
        ax.hist(ending_balances, bins=50, color='#2563eb', edgecolor='white')
        ax.set_xlabel("Ending Balance ($)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

        # Example Pie chart for allocation
        st.subheader("Portfolio Allocation Example")
        allocations = {"Stocks":50, "Bonds":30, "Cash":10, "Crypto":10}
        fig2 = go.Figure(data=[go.Pie(labels=list(allocations.keys()), values=list(allocations.values()), hole=.3)])
        st.plotly_chart(fig2)

# ---------------- SME DASHBOARD ----------------
if st.session_state.page == "sme":
    st.header("SME Dashboard 🏢")
    st.markdown("### Enter Your Business KPIs")

    with st.form("sme_form"):
        revenue = st.number_input("Revenue ($) 📈", min_value=0, value=500000, help="Total revenue of the SME.")
        expenses = st.number_input("Expenses ($) 💸", min_value=0, value=350000, help="Total expenses including salaries.")
        employees = st.number_input("Number of Employees 👥", min_value=1, value=20, help="Number of employees.")
        marketing = st.number_input("Marketing Spend ($) 📢", min_value=0, value=50000, help="Budget for marketing.")
        operations = st.number_input("Operations Cost ($) ⚙️", min_value=0, value=150000, help="Operations cost.")
        submit_sme = st.form_submit_button("Calculate KPIs")

    if submit_sme:
        profit = revenue - expenses
        profit_margin = profit / revenue * 100 if revenue != 0 else 0
        revenue_per_employee = revenue / employees
        st.success(f"💰 Profit: ${profit:,.2f}")
        st.info(f"📊 Profit Margin: {profit_margin:.2f}% | Revenue per Employee: ${revenue_per_employee:,.2f}")

        # KPIs Card Example
        st.markdown(f"""
        <div class="card">
            <b>Profit:</b> ${profit:,.2f} <br>
            <b>Profit Margin:</b> {profit_margin:.2f}% <br>
            <b>Revenue per Employee:</b> ${revenue_per_employee:,.2f} <br>
            <b>Marketing % of Revenue:</b> {marketing/revenue*100:.2f}% <br>
            <b>Operations % of Revenue:</b> {operations/revenue*100:.2f}%
        </div>
        """, unsafe_allow_html=True)

        # Bar chart of SME KPIs
        st.subheader("Expense Allocation")
        categories = ['Marketing', 'Operations', 'Other Expenses', 'Profit']
        values = [marketing, operations, expenses - marketing - operations, profit]
        fig3, ax3 = plt.subplots()
        ax3.bar(categories, values, color=['#f87171','#fcd34d','#2563eb','#38ef7d'])
        ax3.set_ylabel("Amount ($)")
        st.pyplot(fig3)
# ---------------- ESTATE PLANNING MODULE ----------------
if st.session_state.page == "estate":
    st.header("Estate Planning ⚖️")
    st.markdown("### Enter Estate Details")

    with st.form("estate_form"):
        total_estate = st.number_input("Total Estate Value ($) 💰", min_value=0, value=5000000,
                                       help="The total value of your estate including cash, property, investments.")
        num_heirs = st.number_input("Number of Heirs 👨‍👩‍👧‍👦", min_value=1, value=3,
                                    help="Total number of heirs.")
        estate_tax_rate = st.slider("Estate Tax Rate (%) 🏷️", min_value=0.0, max_value=50.0, value=20.0,
                                    help="Percentage tax applied to the estate before distribution.")
        special_allocations = st.text_area("Special Allocations (optional) ✍️",
                                           placeholder="Heir Name: Amount, Heir Name: Amount...",
                                           help="Specify if any heir gets a fixed amount. Example: 'Alice: 100000, Bob: 50000'")
        submit_estate = st.form_submit_button("Calculate Inheritance")

    if submit_estate:
        tax_amount = total_estate * (estate_tax_rate/100)
        remaining_estate = total_estate - tax_amount

        # Handle special allocations
        allocations = {}
        if special_allocations.strip():
            try:
                for line in special_allocations.split(','):
                    name, amt = line.strip().split(':')
                    allocations[name.strip()] = float(amt.strip())
            except:
                st.error("Error parsing special allocations. Ensure format is correct: Name: Amount, ...")

        total_special = sum(allocations.values())
        remaining_for_equal = max(0, remaining_estate - total_special)
        heirs_equal_share = remaining_for_equal / max(1, num_heirs - len(allocations))

        # Final distribution
        inheritance = {}
        for name, amt in allocations.items():
            inheritance[name] = amt
        # Fill remaining heirs
        counter = 1
        while len(inheritance) < num_heirs:
            heir_name = f"Heir {counter}"
            if heir_name not in inheritance:
                inheritance[heir_name] = heirs_equal_share
            c
import io
import base64

# ---------------- DOWNLOAD REPORT FUNCTION ----------------
def generate_report_pdf(content:str, filename:str="FinAI_Report.pdf"):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        st.warning("ReportLab not installed. Add `reportlab` to requirements.txt to enable PDF reports.")
        return

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    for line in content.split('\n'):
        c.drawString(50, y, line)
        y -= 15
    c.save()
    buffer.seek(0)
    return buffer

def download_link(buffer, filename="report.pdf", label="Download Report"):
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'
    st.markdown(href, unsafe_allow_html=True)

# ---------------- SCENARIO ANALYSIS ----------------
if st.session_state.page in ["business_tax", "family_tax", "investments", "sme", "estate"]:
    st.subheader("Scenario Analysis 🔍")
    st.markdown("Adjust sliders to simulate different scenarios and see the projected outcomes.")

    # Example scenario sliders
    if st.session_state.page == "business_tax":
        revenue_factor = st.slider("Revenue Growth Factor (%) 📈", min_value=50, max_value=200, value=100)
        adjusted_revenue = revenue * revenue_factor / 100
        st.info(f"Projected Revenue with Scenario: ${adjusted_revenue:,.2f}")

    elif st.session_state.page == "family_tax":
        salary_factor = st.slider("Salary Change Factor (%) 👨‍👩‍👧‍👦", min_value=50, max_value=200, value=100)
        adjusted_salary = salary * salary_factor / 100
        st.info(f"Projected Salary with Scenario: ${adjusted_salary:,.2f}")

    elif st.session_state.page == "investments":
        return_factor = st.slider("Expected Return Adjustment (%) 📊", min_value=-10, max_value=20, value=0)
        adjusted_return = expected_return + return_factor
        st.info(f"Adjusted Expected Annual Return: {adjusted_return:.2f}%")

# ---------------- GENERATE DOWNLOADABLE REPORT ----------------
if st.session_state.page in ["business_tax", "family_tax", "investments", "sme", "estate"]:
    report_text = f"FinAI Report - {PAGES[st.session_state.page]}\n\n"

    if st.session_state.page == "business_tax":
        report_text += f"Revenue: ${revenue:,.2f}\nExpenses: ${expenses:,.2f}\nDeductions: ${deductions:,.2f}\nVAT Paid: ${vat_paid:,.2f}\nEstimated Tax Owed: ${tax_owed:,.2f}\n"
    elif st.session_state.page == "family_tax":
        report_text += f"Salary: ${salary:,.2f}\nInvestment Income: ${investment_income:,.2f}\nDeductions: ${deductions:,.2f}\nTax Credits: ${tax_credits:,.2f}\nEstimated Tax Owed: ${tax_owed:,.2f}\n"
    elif st.session_state.page == "investments":
        report_text += f"Initial Investment: ${initial_investment:,.2f}\nMonthly Contribution: ${monthly_contribution:,.2f}\nExpected Return: {expected_return:.2f}%\nYears: {years}\nProjected Portfolio Value: ${np.mean(ending_balances):,.2f}\n"
    elif st.session_state.page == "sme":
        report_text += f"Revenue: ${revenue:,.2f}\nExpenses: ${expenses:,.2f}\nEmployees: {employees}\nProfit: ${profit:,.2f}\nProfit Margin: {profit_margin:.2f}%\nRevenue per Employee: ${revenue_per_employee:,.2f}\n"
    elif st.session_state.page == "estate":
        report_text += f"Total Estate: ${total_estate:,.2f}\nEstate Tax Rate: {estate_tax_rate:.2f}%\nRemaining Estate: ${remaining_estate:,.2f}\nInheritance Distribution:\n"
        for heir, amt in inheritance.items():
            report_text += f"{heir}: ${amt:,.2f}\n"

    st.markdown("---")
    st.subheader("Download Report 📄")
    buffer = generate_report_pdf(report_text)
    if buffer:
        download_link(buffer, filename=f"{st.session_state.page}_FinAI_Report.pdf", label="Download PDF Report")

# ---------------- ADDITIONAL INTERACTIVE CHARTS ----------------
if st.session_state.page in ["investments", "sme", "estate"]:
    st.subheader("Interactive Charts 📊")
    if st.session_state.page == "investments":
        # Interactive Portfolio Percentiles
        percentile_slider = st.slider("Select Percentile to View", 0, 100, 50)
        value_at_percentile = np.percentile(ending_balances, percentile_slider)
        st.info(f"Portfolio Value at {percentile_slider}th Percentile: ${value_at_percentile:,.2f}")

    elif st.session_state.page == "sme":
        # Dynamic revenue per employee chart
        emp_range = st.slider("Adjust Employee Count 👥", min_value=1, max_value=100, value=employees)
        adjusted_rev_per_emp = revenue / emp_range
        st.info(f"Revenue per Employee with {emp_range} employees: ${adjusted_rev_per_emp:,.2f}")

    elif st.session_state.page == "estate":
        # Pie chart slice adjustment for visualization
        st.markdown("Adjust allocations dynamically with scenario sliders below:")
        adjust_factor = st.slider("Adjust Estate Distribution Factor (%)", 50, 150, 100)
        adjusted_inheritance = {heir: amt*adjust_factor/100 for heir, amt in inheritance.items()}
        fig, ax = plt.subplots()
        ax.pie(list(adjusted_inheritance.values()), labels=list(adjusted_inheritance.keys()), autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        st.pyplot(fig)
# ---------------- MOCK AI SEARCH BAR ----------------
if st.session_state.page == "home":
    st.markdown("### Ask FinAI Anything 🤖")
    search_query = st.text_input("🔍 Enter your question", placeholder="e.g., How can I optimize my family taxes?")
    if search_query:
        # Mock AI response for demonstration
        st.markdown(f"""
        **FinAI Response:**  
        For your query: *"{search_query}"*  
        - Review current income and deductions  
        - Consider tax credits for families  
        - Invest in tax-efficient portfolios  
        - For businesses, analyze expenses vs revenue  
        _Note: This is a simulated AI response for demo purposes._
        """)

    # Make search bar visually prominent
    st.markdown("""
    <style>
    .search-box input {
        width: 80%;
        height: 3rem;
        font-size: 1.2rem;
        border-radius: 15px;
        border: 2px solid #2563eb;
        padding-left: 1rem;
        box-shadow: 0 0 15px rgba(37,99,235,0.4);
        transition: box-shadow 0.3s;
    }
    .search-box input:focus {
        box-shadow: 0 0 25px rgba(37,99,235,0.8);
    }
    </style>
    <div class="search-box">
        <input type="text" placeholder="🔍 Ask FinAI anything..." />
    </div>
    """, unsafe_allow_html=True)

# ---------------- EXAMPLE DATA FOR USERS ----------------
if st.session_state.page in ["business_tax", "family_tax", "investments", "sme", "estate"]:
    st.subheader("Example Data 💡")
    st.markdown("Click a button to autofill with example data for testing purposes.")

    if st.button("Load Example Data"):
        if st.session_state.page == "business_tax":
            st.session_state.update({"revenue": 1000000, "expenses": 600000, "deductions": 80000, "vat_paid": 50000})
            st.success("Example Business Tax data loaded.")

        elif st.session_state.page == "family_tax":
            st.session_state.update({"salary": 180000, "investment_income": 15000, "deductions": 25000, "tax_credits": 6000})
            st.success("Example Family Tax data loaded.")

        elif st.session_state.page == "investments":
            st.session_state.update({"initial_investment": 75000, "monthly_contribution": 2500, "expected_return": 8.0, "years": 25})
            st.success("Example Investment data loaded.")

        elif st.session_state.page == "sme":
            st.session_state.update({"revenue": 800000, "expenses": 500000, "employees": 25, "marketing": 70000, "operations": 200000})
            st.success("Example SME data loaded.")

        elif st.session_state.page == "estate":
            st.session_state.update({"total_estate": 7000000, "num_heirs": 4, "estate_tax_rate": 25, "special_allocations": "Alice:100000, Bob:50000"})
            st.success("Example Estate data loaded.")

# ---------------- ADVANCED PLOTLY DASHBOARDS ----------------
import plotly.express as px
import pandas as pd

if st.session_state.page in ["investments", "sme", "estate"]:
    st.subheader("Advanced Interactive Dashboards 📊")
    st.markdown("These dashboards provide interactive exploration of your data.")

    if st.session_state.page == "investments":
        # Simulate portfolio over time
        months = np.arange(1, years*12+1)
        balance_history = [initial_investment]
        monthly_return = expected_return / 12 / 100
        for m in months[1:]:
            balance_history.append(balance_history[-1]*(1 + monthly_return) + monthly_contribution)
        df = pd.DataFrame({"Month": months, "Portfolio Value": balance_history})
        fig = px.line(df, x="Month", y="Portfolio Value", title="Portfolio Growth Over Time", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif st.session_state.page == "sme":
        categories = ['Marketing', 'Operations', 'Other Expenses', 'Profit']
        values = [marketing, operations, expenses - marketing - operations, profit]
        df = pd.DataFrame({"Category": categories, "Amount": values})
        fig = px.bar(df, x="Category", y="Amount", color="Category", title="SME Expense Allocation", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif st.session_state.page == "estate":
        df = pd.DataFrame({"Heir": list(inheritance.keys()), "Amount": list(inheritance.values())})
        fig = px.pie(df, names="Heir", values="Amount", title="Estate Distribution", template="plotly_dark", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

# ---------------- OPTIONAL MULTI-USER STATE ----------------
# This sets up a dictionary to store multiple users' input data
if "multi_user_data" not in st.session_state:
    st.session_state.multi_user_data = {}

st.subheader("Multi-User Input Tracking 👥")
user_name = st.text_input("Enter your name for this session:", placeholder="Your Name")
if user_name:
    st.session_state.multi_user_data[user_name] = {
        "page": st.session_state.page,
        "timestamp": pd.Timestamp.now()
    }
    st.info(f"Tracking session for {user_name}. Total users tracked: {len(st.session_state.multi_user_data)}")
