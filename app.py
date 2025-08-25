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
import math
import textwrap

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# ---------------- STYLES (ensure readability over background) ----------------
BG_IMAGE_URL = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1470&q=80"
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
    }}
    .content-box {{
        background-color: rgba(255,255,255,0.92);
        padding: 18px;
        border-radius: 10px;
        color: #111;
    }}
    .header-text {{ color: #111 !important; }}
    .category-btn button {{ color: #000 !important; font-weight:700; }}
    .submit-btn button {{ color: #000 !important; font-weight:700; background:#E6E6E6; border-radius:8px; }}
    .privacy-text {{ color: #fff; line-height:1.5; }}
    .tooltip {{ color: #666; font-size:0.9em; }}
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION INIT ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False
# per-type stored inputs
if "individual_inputs" not in st.session_state:
    st.session_state.individual_inputs = {}
if "household_inputs" not in st.session_state:
    st.session_state.household_inputs = {}
if "business_inputs" not in st.session_state:
    st.session_state.business_inputs = {}
if "advice_text" not in st.session_state:
    st.session_state.advice_text = ""

# ---------------- PRIVACY AGREEMENT ----------------
def show_privacy_agreement():
    st.markdown("<div class='content-box'>", unsafe_allow_html=True)
    st.markdown("<h2 class='header-text'>Privacy & Data Agreement</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class='privacy-text'>
    <p>
    This site (FinAI) collects and processes personal and financial information you provide for the purpose of generating personalised financial, tax and investment advice.
    By selecting <strong>Accept</strong> you confirm you understand and consent to:
    </p>
    <ul>
      <li>Storage of the data you provide on secure, encrypted servers for the purpose of generating advice, reports, and contacting you if requested.</li>
      <li>Use of aggregated, anonymized data to improve FinAI models and services.</li>
      <li>That FinAI and its agents do not accept liability for decisions made solely on the basis of the automated advice — professional implementation is required.</li>
      <li>This agreement is legally binding. If you do not accept, you will not be permitted to use the platform and will be redirected off the app.</li>
    </ul>
    <p>FinAI will not sell your personal data and will only share information with third parties with your explicit consent or if required by law.</p>
    </div>
    """, unsafe_allow_html=True)
    agree = st.checkbox("I have read and I ACCEPT this Privacy & Data Agreement")
    if agree:
        st.session_state.privacy_accepted = True
    else:
        st.warning("You must accept the privacy agreement to continue.")
        st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- AI routing + fallback logic ----------------
def detect_user_type_free_text(text: str) -> str:
    """Use OpenAI if available to classify as individual/household/business, else fallback rule-based."""
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    text_clean = (text or "").lower()
    if api_key:
        openai.api_key = api_key
        try:
            prompt = f"Classify the following financial query into one of: individual, household, business.\n\nQuery: \"{text}\"\n\nReturn only one word: individual, household, or business."
            resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=6, temperature=0.0)
            out = resp.choices[0].text.strip().lower()
            if out in ("individual","household","business"):
                return out
        except Exception:
            # fall through to rule-based
            pass

    # Rule-based fallback
    if any(k in text_clean for k in ["business", "company", "corporate", "revenue", "employees", "profit"]):
        return "business"
    if any(k in text_clean for k in ["household", "family", "kids", "children", "spouse", "partner", "house"]):
        return "household"
    return "individual"

# ---------------- AI advice generator (OpenAI if available, else strong fallback) ----------------
def generate_advice(user_type: str, inputs: dict) -> str:
    """
    Returns AI-style advice. If OpenAI API key exists, use model. Otherwise use a deterministic
    fallback that still gives realistic suggestions (tax saving, investment, next steps).
    """
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    # Build an input summary string
    lines = [f"{k}: {v}" for k, v in inputs.items()]
    summary = "\n".join(lines) if lines else "No inputs provided."

    # If OpenAI available -> call it
    if api_key:
        openai.api_key = api_key
        try:
            prompt = f"""
You are a professional, conservative financial advisor. The user type is: {user_type}.
User inputs:
{summary}

Provide:
1) A 4-bullet high-quality personalized summary of what they should consider (tax saving ideas, investment places, expense optimization).
2) For each bullet include a short estimate of potential monthly savings or impact where reasonable (use conservative assumptions).
3) Conclude with a call-to-action: ask user to contact the firm to implement.

Do NOT provide step-by-step legal/filing instructions — encourage professional implementation.
"""
            resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, temperature=0.2, max_tokens=450)
            advice_text = resp.choices[0].text.strip()
            return advice_text
        except Exception:
            # fallback below
            pass

    # Fallback deterministic advisor (rule-based)
    # We'll generate realistic-sounding advice based on inputs.
    adv = []
    def fmt_amt(x):
        try:
            return f"R {float(x):,.0f}"
        except Exception:
            return str(x)

    if user_type == "individual":
        income = float(inputs.get("Income", 0) or 0)
        deductions = float(inputs.get("Deductions", 0) or 0)
        # basic estimates
        est_taxable = max(income - deductions, 0)
        adv.append(f"Review tax-advantaged savings: contributing to retirement and tax-free savings can reduce taxable income; potential yearly saving could be ~{fmt_amt(min(0.1*income, 0.15*est_taxable))}.")
        adv.append("Automate investments into diversified low-cost funds (index trackers) to improve net returns and reduce fees.")
        adv.append("Identify recurring subscriptions and non-essential expenses — trimming 5-10% may increase monthly savings meaningfully.")
        adv.append("Contact us to review precise tax credits/exemptions for your profile and implement legally-compliant strategies.")
    elif user_type == "household":
        inc = float(inputs.get("Household Income", 0) or 0)
        ded = float(inputs.get("Deductions", 0) or 0)
        kids = int(inputs.get("Children", 0) or 0)
        adv.append(f"Household budgeting: aggregate income {fmt_amt(inc)} — ensure emergency fund equals 3-6 months expenses. Consider directing idle cash into tax-efficient accounts.")
        # child-related idea
        if kids > 0:
            adv.append(f"Explore child-related tax credits/deductions and education investment plans — these often yield both tax and long-term wealth benefits.")
        else:
            adv.append("If no dependents, consider spouse/partner income-splitting strategies and maximizing retirement contributions.")
        adv.append("Use itemized deductions where applicable; implementing business-structured investments where appropriate can change tax profile.")
        adv.append("Contact us for a household-specific tax-savings audit — we can estimate exact annual savings after reviewing statements.")
    else:  # business
        rev = float(inputs.get("Revenue", 0) or 0)
        exp = float(inputs.get("Expenses", 0) or 0)
        employees = int(inputs.get("Employees", 0) or 0)
        profit = rev - exp
        adv.append(f"Focus on deductible expenses and correct classification of costs — maximizing legitimate deductions could reduce taxable profit by a material amount (depends on business).")
        adv.append("Consider tax-efficient remuneration strategies (salary vs dividends) and retirement savings plans for owners/employees to optimize tax treatment.")
        adv.append(f"Implement expense controls and track deductible purchases using a dedicated business card to ensure clean accounting — this can increase deductible claims and lower audit risk.")
        adv.append("Contact us for a full tax optimization plan; we will model scenarios and provide an estimate of potential annual tax savings.")
    # join with line breaks
    return "\n\n".join(adv)

# ---------------- PLOT HELPERS ----------------
def show_financial_chart(user_type: str, inputs: dict):
    # Use matplotlib; put inside white box for contrast
    st.markdown("<div class='content-box'>", unsafe_allow_html=True)
    st.subheader("Financial Summary Chart")
    fig, ax = plt.subplots(figsize=(6,3.5))
    labels = []
    values = []
    if user_type == "individual":
        labels = ["Income","Deductions"]
        values = [float(inputs.get("Income",0) or 0), float(inputs.get("Deductions",0) or 0)]
    elif user_type == "household":
        labels = ["Household Income","Deductions"]
        values = [float(inputs.get("Household Income",0) or 0), float(inputs.get("Deductions",0) or 0)]
    else:
        labels = ["Revenue","Expenses"]
        values = [float(inputs.get("Revenue",0) or 0), float(inputs.get("Expenses",0) or 0)]
    # protect zeros for plotting
    if all(v == 0 for v in values):
        ax.text(0.5,0.5,"No numeric inputs yet", ha='center', va='center', fontsize=12)
    else:
        bars = ax.bar(labels, values, color=['#2b8cbe','#f03b20'])
        ax.set_ylabel("Amount (R)")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=10)
        # annotate bars
        for b in bars:
            h = b.get_height()
            ax.annotate(f"R {h:,.0f}", xy=(b.get_x()+b.get_width()/2, h), xytext=(0,4), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        ax.set_ylim(0, max(values)*1.2 if max(values)>0 else 1)
    st.pyplot(fig, clear_figure=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- EXPORTS: PDF & EXCEL ----------------
def export_pdf(inputs: dict, user_type: str, advice: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 750, f"FinAI Report - {user_type.capitalize()}")
    c.setFont("Helvetica", 10)
    y = 730
    c.drawString(40, y, "Inputs:")
    y -= 16
    for k,v in inputs.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 14
        if y < 60:
            c.showPage()
            y = 750
    y -= 6
    c.drawString(40, y, "AI Advice:")
    y -= 16
    wrapper = textwrap.wrap(advice, width=90)
    for line in wrapper:
        c.drawString(50, y, line)
        y -= 12
        if y < 60:
            c.showPage()
            y = 750
    c.save()
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

def export_excel(inputs: dict, user_type: str, advice: str) -> bytes:
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory': True})
    ws = wb.add_worksheet("Summary")
    ws.write(0,0,"User Type")
    ws.write(0,1,user_type)
    row = 2
    ws.write(1,0,"Input")
    ws.write(1,1,"Value")
    for k,v in inputs.items():
        ws.write(row,0,k)
        ws.write(row,1, v)
        row += 1
    row += 1
    ws.write(row,0,"Advice")
    ws.write(row,1,advice)
    wb.close()
    return out.getvalue()

# ---------------- MAIN PAGES ----------------

def page_home():
    st.markdown("<div class='content-box'>", unsafe_allow_html=True)
    st.title("FinAI — Personalised Tax & Investment Advisor")
    st.markdown("Describe your situation in plain English and FinAI will route you to targeted tools and tailored advice.")
    # glowing input style via CSS class for the block
    query = st.text_input("🔎 Ask FinAI anything...", value="", help="Type what you want help with: e.g. 'I run a small bakery. I pay R50k monthly in rent and have 3 employees' — FinAI will route you.", key="search")
    submit_clicked = st.button("Submit", key="submit_search")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    # Manual category buttons
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("Individual", key="home_ind"):
            st.session_state.page = "dashboard"
            st.session_state.user_type = "individual"
    with col2:
        if st.button("Household", key="home_house"):
            st.session_state.page = "dashboard"
            st.session_state.user_type = "household"
    with col3:
        if st.button("Business", key="home_bus"):
            st.session_state.page = "dashboard"
            st.session_state.user_type = "business"

    st.markdown("</div>", unsafe_allow_html=True)

    # If user typed a query and clicked submit -> detect and go
    if submit_clicked and query.strip():
        detected = detect_user_type_free_text(query)
        st.session_state.user_type = detected
        st.session_state.page = "dashboard"
        # note: Streamlit automatically reruns after interaction; just proceed

def page_dashboard():
    ut = st.session_state.get("user_type", "individual") or "individual"
    st.markdown("<div class='content-box'>", unsafe_allow_html=True)
    st.title(f"{ut.capitalize()} Dashboard")
    st.markdown("<small class='tooltip'>Fields marked are monthly/annual amounts — where relevant specify whether annual or monthly in the label or notes.</small>", unsafe_allow_html=True)
    st.markdown("---")
    # gather inputs and persist them to session_state
    if ut == "individual":
        ins = st.session_state.individual_inputs
        income = st.number_input("Annual Income (R)", value=float(ins.get("Income", 0)), format="%.2f", help="Total annual taxable income")
        deductions = st.number_input("Annual Deductions (R)", value=float(ins.get("Deductions", 0)), format="%.2f", help="Total annual deductions you currently claim")
        # save
        st.session_state.individual_inputs = {"Income": income, "Deductions": deductions}
        current_inputs = st.session_state.individual_inputs
    elif ut == "household":
        ins = st.session_state.household_inputs
        h_income = st.number_input("Household Annual Income (R)", value=float(ins.get("Household Income",0)), format="%.2f", help="Total household annual income")
        children = st.number_input("Number of Children", value=int(ins.get("Children",0)), min_value=0, step=1, help="Number of dependents")
        deductions = st.number_input("Total Household Deductions (R)", value=float(ins.get("Deductions",0)), format="%.2f", help="Total household deductions")
        st.session_state.household_inputs = {"Household Income": h_income, "Children": children, "Deductions": deductions}
        current_inputs = st.session_state.household_inputs
    else:  # business
        ins = st.session_state.business_inputs
        revenue = st.number_input("Annual Revenue (R)", value=float(ins.get("Revenue",0)), format="%.2f", help="Total revenue for the business (annual)")
        expenses = st.number_input("Annual Expenses (R)", value=float(ins.get("Expenses",0)), format="%.2f", help="Total business expenses (annual)")
        employees = st.number_input("Number of Employees", value=int(ins.get("Employees",0)), min_value=0, step=1, help="Number of employees")
        st.session_state.business_inputs = {"Revenue": revenue, "Expenses": expenses, "Employees": employees}
        current_inputs = st.session_state.business_inputs

    st.markdown("---")
    col_a, col_b = st.columns([2,1])
    with col_a:
        # Advice button
        if st.button("Get AI-style Personalized Advice"):
            st.session_state.advice_text = generate_advice(ut, current_inputs)
            # show advice
            st.markdown("<div class='white-box'>", unsafe_allow_html=True)
            st.subheader("Personalized Advice")
            st.write(st.session_state.advice_text)
            st.markdown("</div>", unsafe_allow_html=True)
            # show chart
            show_financial_chart(ut, current_inputs)
        else:
            # if previously generated advice exists, show partially
            if st.session_state.advice_text:
                st.markdown("<div class='white-box'>", unsafe_allow_html=True)
                st.subheader("Most Recent Advice")
                st.write(st.session_state.advice_text)
                st.markdown("</div>", unsafe_allow_html=True)
                show_financial_chart(ut, current_inputs)
    with col_b:
        st.subheader("Quick actions")
        # Export (works even if empty advice)
        advice_for_export = st.session_state.advice_text or "No advice generated yet. Press 'Get AI-style Personalized Advice' to create."
        pdf_bytes = export_pdf(current_inputs, ut, advice_for_export)
        excel_bytes = export_excel(current_inputs, ut, advice_for_export)
        st.download_button("Download PDF Report", data=pdf_bytes, file_name="finai_report.pdf")
        st.download_button("Download Excel Report", data=excel_bytes, file_name="finai_report.xlsx")
        st.markdown("---")
        st.markdown("**Need hands-on help?**")
        st.markdown("Contact our team to turn recommendations into actionable steps. We assist with tax filing, investment setup, and implementation.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- APP START ----------------
def main():
    # ensure privacy accepted
    if not st.session_state.get("privacy_accepted", False):
        show_privacy_agreement()

    # top navbar (simple)
    pages = {"home": "Home", "dashboard": "Dashboard"}
    st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)
    # show simple nav links
    nav_cols = st.columns([1,1,1,2])
    if nav_cols[0].button("Home"):
        st.session_state.page = "home"
    if nav_cols[1].button("Individual"):
        st.session_state.page = "dashboard"; st.session_state.user_type = "individual"
    if nav_cols[2].button("Household"):
        st.session_state.page = "dashboard"; st.session_state.user_type = "household"
    if nav_cols[3].button("Business"):
        st.session_state.page = "dashboard"; st.session_state.user_type = "business"

    # route pages
    if st.session_state.page == "home":
        page_home()
    elif st.session_state.page == "dashboard":
        # ensure user_type exists
        if "user_type" not in st.session_state or not st.session_state.user_type:
            st.session_state.user_type = "individual"
        page_dashboard()
    else:
        page_home()

if __name__ == "__main__":
    main()
