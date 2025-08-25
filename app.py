# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import openai
import textwrap

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# ---------------- MARKET SNAPSHOT (embedded) ----------------
MARKET_OVERVIEW = (
    "Market snapshot (context used for advice):\n"
    "- Central banks have become more dovish recently; markets price possible rate cuts in coming months.\n"
    "- Global growth forecasts show moderate improvement but geopolitical/trade risks remain.\n"
    "- Equity valuations are concentrated in a handful of mega-cap names; diversification is recommended.\n"
    "- Strategy: favor diversified quality growth, some real-assets exposure, preserve liquidity while macro signals clarify."
)

# ---------------- STYLES ----------------
BG_IMAGE_URL = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1470&q=80"
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
    }}
    .panel {{
        background: rgba(255,255,255,0.95);
        padding: 16px;
        border-radius: 10px;
        color: #111;
    }}
    .muted {{ color: #555; font-size: 0.9em; }}
    .btn-black button {{ color: black !important; font-weight:700; }}
    .search-glow input {{ box-shadow: 0 0 14px rgba(79,195,86,0.28); border-radius:8px; padding:10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION STATE INITIALIZATION ----------------
if "page" not in st.session_state:
    st.session_state.page = "privacy"
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False
if "user_type" not in st.session_state:
    st.session_state.user_type = "individual"
if "individual_inputs" not in st.session_state:
    st.session_state.individual_inputs = {"Income": 0.0, "Deductions": 0.0}
if "household_inputs" not in st.session_state:
    st.session_state.household_inputs = {"Household Income": 0.0, "Children": 0, "Deductions": 0.0}
if "business_inputs" not in st.session_state:
    st.session_state.business_inputs = {"Revenue": 0.0, "Expenses": 0.0, "Employees": 0}
if "advice_text" not in st.session_state:
    st.session_state.advice_text = ""
if "market_context" not in st.session_state:
    st.session_state.market_context = MARKET_OVERVIEW

# ---------------- UTILITIES: OPENAI SAFE USE ----------------
def openai_available():
    return bool(st.secrets.get("OPENAI_API_KEY", "") or None)

def call_openai(prompt: str, max_tokens=400, temperature=0.2):
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OpenAI API key not set in st.secrets")
    openai.api_key = api_key
    resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens, temperature=temperature)
    return resp.choices[0].text.strip()

# ---------------- PRIVACY AGREEMENT PAGE ----------------
def show_privacy_page():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:white'>Privacy & Data Agreement</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:white; line-height:1.4'>{MARKET_OVERVIEW.splitlines()[0]}</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='color:white; line-height:1.4'>
        <p>
        This platform (FinAI) collects the financial information you provide to generate personalized advice and reports.
        By clicking <strong>Accept & Continue</strong> you agree that:
        </p>
        <ul>
         <li>Your data will be stored securely and may be used in anonymized form to improve services.</li>
         <li>FinAI is not liable for business or investment outcomes; implementation requires professional engagement.</li>
         <li>This is a legally binding agreement. If you do not accept, you will not be able to use the platform.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    accept = st.checkbox("I have read and ACCEPT this Privacy & Data Agreement", key="privacy_checkbox")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Accept & Continue", key="privacy_continue"):
            if accept:
                st.session_state.privacy_accepted = True
                st.session_state.page = "home"
                # Streamlit will rerun after this interaction; no explicit st.rerun needed
            else:
                st.warning("Please check the acceptance box before continuing.")
    with col2:
        if st.button("Decline & Exit", key="privacy_decline"):
            st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- HOME PAGE ----------------
def show_home_page():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title("FinAI — Intelligent Tax & Investment Assistant")
    st.markdown("<small class='muted'>Market snapshot (context for advice)</small>")
    st.info(st.session_state.market_context)
    st.markdown("---")

    # Glowing search input (visual) and detect button
    query = st.text_input("🔎 Ask FinAI anything (plain English):", key="home_query", placeholder="e.g., 'I run a small cafe with R2M revenue and R1.2M expenses' ")
    detect_clicked = st.button("Detect & Route")
    st.markdown("— or choose a path manually —")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Individual"):
            st.session_state.user_type = "individual"
            st.session_state.page = "dashboard"
    with c2:
        if st.button("Household"):
            st.session_state.user_type = "household"
            st.session_state.page = "dashboard"
    with c3:
        if st.button("Business"):
            st.session_state.user_type = "business"
            st.session_state.page = "dashboard"

    st.markdown("</div>", unsafe_allow_html=True)

    # handle detection
    if detect_clicked:
        detected = detect_user_type(query)
        st.session_state.user_type = detected
        st.session_state.page = "dashboard"

# ---------------- NATURAL-LANGUAGE ROUTER ----------------
def detect_user_type(text: str) -> str:
    text_l = (text or "").lower()
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    # try OpenAI classification if key set
    if api_key:
        try:
            prompt = f"Classify the query into one of: individual, household, business. Query: {text}"
            out = call_openai(prompt, max_tokens=6, temperature=0.0)
            out_clean = out.strip().lower()
            if out_clean in ("individual", "household", "business"):
                return out_clean
        except Exception:
            # fall back to rule-based
            pass

    # Simple rule-based fallback
    if any(k in text_l for k in ["business", "company", "employees", "revenue", "profit", "expenses"]):
        return "business"
    if any(k in text_l for k in ["household", "family", "kids", "children", "partner", "spouse", "home"]):
        return "household"
    return "individual"

# ---------------- ADVICE ENGINE ----------------
def build_advice(user_type: str, inputs: dict) -> str:
    """
    Uses OpenAI if available to craft 4 high-quality bullets + CTA.
    Otherwise uses deterministic fallback logic that still returns useful recommendations.
    """
    context = st.session_state.market_context
    summary = "\n".join([f"{k}: {v}" for k, v in inputs.items()]) or "No numeric inputs provided."

    if openai_available():
        try:
            prompt = f"""
You are a professional, cautious financial advisor. Use the MARKET CONTEXT and USER INPUTS to produce:
- 4 concise, actionable bullets (tax-saving ideas, investment suggestions, expense efficiency), with conservative estimates of potential monthly/annual savings where reasonable.
- A final one-line CTA encouraging the user to contact the advisory firm to implement strategies.
MARKET CONTEXT:
{context}
USER INPUTS:
{summary}
User type: {user_type}
Return plain text with bullets.
"""
            return call_openai(prompt, max_tokens=450, temperature=0.2)
        except Exception:
            # fall through to fallback
            pass

    # Fallback deterministic generation
    def fmt(x):
        try:
            return f"R {float(x):,.0f}"
        except Exception:
            return str(x)

    adv_lines = []
    if user_type == "individual":
        income = float(inputs.get("Income", 0) or 0)
        deductions = float(inputs.get("Deductions", 0) or 0)
        adv_lines.append(f"Prioritize tax-advantaged savings (retirement / tax-free accounts) to reduce taxable income; potential annual saving ~{fmt(min(0.05*income, 0.1*max(income-deductions,0)))}.")
        adv_lines.append("Use low-cost diversified ETFs for long-term growth; avoid concentrated bets in a few mega-cap names.")
        adv_lines.append("Trim recurring expenses (subscriptions, utilities) — a 5% reduction improves monthly savings and cashflow.")
        adv_lines.append("Contact our team to model your exact tax credits and legally implement strategies.")
    elif user_type == "household":
        hinc = float(inputs.get("Household Income", 0) or 0)
        kids = int(inputs.get("Children", 0) or 0)
        adv_lines.append(f"Hold an emergency fund (3–6 months of expenses). Consider tax-efficient savings for household goals; idle cash can be moved to tax-free vehicles.")
        if kids > 0:
            adv_lines.append("Explore education-linked savings and child-related tax credits to optimize long-term costs.")
        else:
            adv_lines.append("Spousal income-splitting and maximizing retirement contributions can reduce household tax burden.")
        adv_lines.append("Diversify across equities and inflation-protected assets given current macro conditions.")
        adv_lines.append("Contact us for a household tax-and-investment audit with concrete annual savings estimates.")
    else:  # business
        rev = float(inputs.get("Revenue", 0) or 0)
        exp = float(inputs.get("Expenses", 0) or 0)
        emp = int(inputs.get("Employees", 0) or 0)
        profit = rev - exp
        adv_lines.append("Ensure all allowable business deductions are captured and classified correctly — good bookkeeping increases deductible claims.")
        adv_lines.append("Consider tax-efficient owner remuneration (salary vs dividends) and retirement schemes for owners/employees.")
        adv_lines.append("Use a dedicated business card and categorised accounting to maximize valid deductions and reduce audit friction.")
        adv_lines.append("Contact our corporate tax team for a modeled scenario of potential annual tax savings after review.")
    return "\n\n".join(adv_lines)

# ---------------- CHART RENDERING ----------------
def render_charts(user_type: str, inputs: dict):
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Visual breakdown")
    # Prepare labels/values
    if user_type == "individual":
        labels = ["Income", "Deductions"]
        values = [float(inputs.get("Income", 0)), float(inputs.get("Deductions", 0))]
    elif user_type == "household":
        labels = ["Household Income", "Deductions"]
        values = [float(inputs.get("Household Income", 0)), float(inputs.get("Deductions", 0))]
    else:
        labels = ["Revenue", "Expenses"]
        values = [float(inputs.get("Revenue", 0)), float(inputs.get("Expenses", 0))]

    # Bar chart
    fig, ax = plt.subplots(figsize=(6, 3.2))
    if sum(values) == 0:
        ax.text(0.5, 0.5, "No numeric inputs yet", ha="center", va="center")
    else:
        bars = ax.bar(labels, values, color=['#2b8cbe', '#f03b20'])
        ax.set_ylabel("Amount (R)")
        for b in bars:
            h = b.get_height()
            ax.annotate(f"R {h:,.0f}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1)
    st.pyplot(fig, clear_figure=True)

    # Pie chart if both values > 0
    if all(v > 0 for v in values):
        fig2, ax2 = plt.subplots(figsize=(4, 4))
        ax2.pie(values, labels=labels, autopct='%1.1f%%', colors=['#2b8cbe', '#f03b20'], startangle=90)
        ax2.axis('equal')
        st.pyplot(fig2, clear_figure=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- EXPORTS: PDF & EXCEL ----------------
def export_pdf(inputs: dict, user_type: str, advice: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 750, f"FinAI Report — {user_type.capitalize()}")
    c.setFont("Helvetica", 10)
    y = 730
    c.drawString(40, y, "Market Context (snapshot):")
    y -= 14
    for line in textwrap.wrap(st.session_state.market_context, width=90):
        c.drawString(45, y, line)
        y -= 12
        if y < 60:
            c.showPage()
            y = 750
    y -= 6
    c.drawString(40, y, "Inputs:")
    y -= 14
    for k, v in inputs.items():
        c.drawString(45, y, f"{k}: {v}")
        y -= 12
        if y < 60:
            c.showPage()
            y = 750
    y -= 6
    c.drawString(40, y, "Advice:")
    y -= 14
    for line in textwrap.wrap(advice, width=90):
        c.drawString(45, y, line)
        y -= 12
        if y < 60:
            c.showPage()
            y = 750
    c.save()
    pdf = buf.getvalue()
    buf.close()
    return pdf

def export_excel(inputs: dict, user_type: str, advice: str) -> bytes:
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory': True})
    ws = wb.add_worksheet("Summary")
    ws.write(0, 0, "User Type"); ws.write(0, 1, user_type)
    ws.write(2, 0, "Input"); ws.write(2, 1, "Value")
    r = 3
    for k, v in inputs.items():
        ws.write(r, 0, k); ws.write(r, 1, v); r += 1
    r += 1
    ws.write(r, 0, "Advice"); ws.write(r, 1, advice)
    wb.close()
    return out.getvalue()

# ---------------- PAGES ----------------
def page_home():
    show_home_page_content = show_home_page  # alias, defined below

def show_home_page():
    show_home_page_content()  # not used; placeholder to avoid flake; actual content below

def page_dashboard():
    show_dashboard_content = show_dashboard  # alias; actual content below

# Main home content
def show_home_page_content():
    show_home_page_inner()

def show_home_page_inner():
    # identical to previously defined home content
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title("FinAI — Intelligent Tax & Investment Assistant")
    st.markdown("<small class='muted'>Market snapshot (context for advice)</small>")
    st.info(st.session_state.market_context)
    st.markdown("---")

    q = st.text_input("🔎 Ask FinAI anything (plain English):", key="home_query", placeholder="e.g., 'I run a small cafe with R2M revenue and R1.2M expenses'")
    detect = st.button("Detect & Route")
    st.markdown("— or choose a path manually —")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Individual"):
            st.session_state.user_type = "individual"
            st.session_state.page = "dashboard"
    with c2:
        if st.button("Household"):
            st.session_state.user_type = "household"
            st.session_state.page = "dashboard"
    with c3:
        if st.button("Business"):
            st.session_state.user_type = "business"
            st.session_state.page = "dashboard"

    st.markdown("</div>", unsafe_allow_html=True)

    if detect:
        detected = detect_user_type(q)
        st.session_state.user_type = detected
        st.session_state.page = "dashboard"

# Dashboard content
def show_dashboard():
    ut = st.session_state.get("user_type", "individual") or "individual"
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title(f"{ut.capitalize()} Dashboard")
    st.markdown("<small class='muted'>Type numbers directly (no +/-). Indicate whether amounts are monthly or annual in your notes.</small>")
    st.markdown("---")

    # Inputs and per-type persistence
    if ut == "individual":
        d = st.session_state.individual_inputs
        inc = st.number_input("Annual Income (R)", value=float(d.get("Income", 0.0)), format="%.2f", help="Total annual taxable income")
        ded = st.number_input("Annual Deductions (R)", value=float(d.get("Deductions", 0.0)), format="%.2f", help="Total annual deductions you currently claim")
        st.session_state.individual_inputs = {"Income": inc, "Deductions": ded}
        inputs = st.session_state.individual_inputs
    elif ut == "household":
        d = st.session_state.household_inputs
        hinc = st.number_input("Household Annual Income (R)", value=float(d.get("Household Income", 0.0)), format="%.2f")
        kids = st.number_input("Number of Children", value=int(d.get("Children", 0)), min_value=0, step=1)
        hd = st.number_input("Total Household Deductions (R)", value=float(d.get("Deductions", 0.0)), format="%.2f")
        st.session_state.household_inputs = {"Household Income": hinc, "Children": kids, "Deductions": hd}
        inputs = st.session_state.household_inputs
    else:
        d = st.session_state.business_inputs
        rev = st.number_input("Annual Revenue (R)", value=float(d.get("Revenue", 0.0)), format="%.2f")
        exp = st.number_input("Annual Expenses (R)", value=float(d.get("Expenses", 0.0)), format="%.2f")
        emp = st.number_input("Number of Employees", value=int(d.get("Employees", 0)), min_value=0, step=1)
        st.session_state.business_inputs = {"Revenue": rev, "Expenses": exp, "Employees": emp}
        inputs = st.session_state.business_inputs

    st.markdown("---")
    left, right = st.columns([2, 1])

    with left:
        if st.button("Get AI-style Personalized Advice"):
            advice = build_advice(ut, inputs)
            st.session_state.advice_text = advice
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Personalized Advice")
            st.write(advice)
            st.markdown("</div>", unsafe_allow_html=True)
            # charts
            render_charts(ut, inputs)
        else:
            if st.session_state.advice_text:
                st.markdown("<div class='panel'>", unsafe_allow_html=True)
                st.subheader("Most Recent Advice")
                st.write(st.session_state.advice_text)
                st.markdown("</div>", unsafe_allow_html=True)
                render_charts(ut, inputs)
            else:
                st.info("Press 'Get AI-style Personalized Advice' to generate recommendations based on inputs and market context.")

    with right:
        st.subheader("Quick actions")
        advice_for_export = st.session_state.advice_text or "No advice generated yet."
        pdf_b = export_pdf(inputs, ut, advice_for_export)
        xlsx_b = export_excel(inputs, ut, advice_for_export)
        st.download_button("Download PDF Report", data=pdf_b, file_name="finai_report.pdf")
        st.download_button("Download Excel Report", data=xlsx_b, file_name="finai_report.xlsx")
        st.markdown("---")
        st.markdown("**Want implementation help?**")
        st.markdown("Contact our team to implement the recommendations and handle tax filings, investment setup, and bookkeeping.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- APP MAIN ----------------
def main():
    # ROUTING
    # Privacy page first
    if not st.session_state.privacy_accepted or st.session_state.page == "privacy":
        show_privacy_page()
        return

    # top nav
    nav1, nav2, nav3, nav4 = st.columns([1,1,1,2])
    if nav1.button("Home"):
        st.session_state.page = "home"
    if nav2.button("Dashboard (Individual)"):
        st.session_state.user_type = "individual"; st.session_state.page = "dashboard"
    if nav3.button("Dashboard (Household)"):
        st.session_state.user_type = "household"; st.session_state.page = "dashboard"
    if nav4.button("Dashboard (Business)"):
        st.session_state.user_type = "business"; st.session_state.page = "dashboard"

    # route pages
    if st.session_state.page == "home":
        show_home_page_inner()
    elif st.session_state.page == "dashboard":
        show_dashboard()
    else:
        show_home_page_inner()

if __name__ == "__main__":
    main()
