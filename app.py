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

# ---------------- CURRENT MARKET SNAPSHOT (embedded) ----------------
# This snapshot was collected when the assistant generated this file.
MARKET_OVERVIEW = (
    "Market snapshot (context for advice):\n\n"
    "• Central banks (notably the U.S. Fed) have signalled a more dovish stance recently, "
    "which lifted equities and lowered short-term yields — markets are pricing in possible rate cuts in coming months.\n\n"
    "• The IMF has nudged up global growth forecasts for 2025 but warns that trade tensions and tariffs are a material downside risk.\n\n"
    "• Large asset managers caution that while equities may perform well over the medium term, valuations are concentrated in a few mega-cap names, "
    "so diversification and selective exposure are important.\n\n"
    "• Strategists recommend a cautious, diversified approach: focus on quality growth where valuations are reasonable, consider inflation-protected and "
    "real-assets exposure, and maintain liquidity buffers until clearer macro signals emerge.\n\n"
    "Sources: Reuters, AP, IMF, BlackRock, Morningstar (summarized)."
)

# ---------------- STYLING & CONTRAST ----------------
BG_IMAGE_URL = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1470&q=80"
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BG_IMAGE_URL}');
        background-size: cover;
        background-position: center;
    }}
    /* content panels (white translucent) for contrast */
    .panel {{
        background: rgba(255,255,255,0.96);
        padding: 18px;
        border-radius: 10px;
        color: #111;
    }}
    .small-muted {{ color:#555; font-size:0.9em; }}
    .btn-black button {{ color: black !important; font-weight:700; }}
    .search-glow input {{ box-shadow: 0 0 12px rgba(79, 195, 86, 0.45); border-radius:8px; padding:10px; }}
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False
if "user_type" not in st.session_state:
    st.session_state.user_type = "individual"
# inputs per type
if "individual_inputs" not in st.session_state:
    st.session_state.individual_inputs = {"Income": 0.0, "Deductions": 0.0}
if "household_inputs" not in st.session_state:
    st.session_state.household_inputs = {"Household Income": 0.0, "Children": 0, "Deductions": 0.0}
if "business_inputs" not in st.session_state:
    st.session_state.business_inputs = {"Revenue": 0.0, "Expenses": 0.0, "Employees": 0}
if "advice_text" not in st.session_state:
    st.session_state.advice_text = ""

# ---------------- PRIVACY AGREEMENT (white font) ----------------
def show_privacy_and_block():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#fff;'>Privacy & Data Agreement</h2>", unsafe_allow_html=True)
    st.markdown("""
        <div style='color:white; line-height:1.4'>
        <p><strong>Purpose:</strong> This platform (FinAI) collects the financial information you provide in order to produce personalized
        financial, tax, and investment recommendations. By clicking 'Accept' you consent to the use of your data for these purposes.</p>

        <p><strong>Storage & Security:</strong> Your data will be stored in secure, encrypted systems. FinAI will not sell your personal data.
        Data may be used in aggregated and anonymized form to improve services.</p>

        <p><strong>Legal:</strong> By clicking Accept you enter a legally binding agreement allowing FinAI to use your data as described. FinAI and its
        affiliates are not responsible for outcomes from implementation of the advice; professional execution is required.</p>

        <p><strong>Opt-out:</strong> If you do not accept, you will not be able to use this platform and will be redirected away from the service.</p>
        </div>
    """, unsafe_allow_html=True)

    accept = st.checkbox("I have read and ACCEPT this Privacy & Data Agreement")
    if accept:
        st.session_state.privacy_accepted = True
        # Immediately navigate to home/dashboard without requiring scroll
        st.session_state.page = "home"
        st.experimental_rerun()
    else:
        st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- AI / RULE-BASED CLASSIFICATION ----------------
def detect_user_type(text: str) -> str:
    text_l = (text or "").lower()
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if api_key:
        try:
            openai.api_key = api_key
            prompt = f"Classify the query into one of: individual, household, business. Query: {text}"
            res = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=6, temperature=0)
            out = res.choices[0].text.strip().lower()
            if out in ("individual","household","business"):
                return out
        except Exception:
            pass
    # fallback simple rules
    if any(k in text_l for k in ["business","company","employees","revenue","profit","expenses"]):
        return "business"
    if any(k in text_l for k in ["household","family","kids","children","spouse","partner","home"]):
        return "household"
    return "individual"

# ---------------- AI-STYLE ADVICE (OpenAI when available, fallback deterministic) ----------------
def build_advice(user_type: str, inputs: dict) -> str:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    summary = "\n".join([f"{k}: {v}" for k,v in inputs.items()])
    context = MARKET_OVERVIEW  # embed snapshot context
    if api_key:
        try:
            openai.api_key = api_key
            prompt = f"""
You are a conservative, professional financial advisor. Use the MARKET CONTEXT provided below and the user's inputs to craft 4 concise,
actionable bullets (no full step-by-step legal instructions) including approximate monthly or annual savings where reasonable.
Also add a one-line CTA to contact the firm for implementation.

MARKET CONTEXT:
{context}

USER INPUTS:
{summary}

Provide clear, practical recommendations tailored to the user's type ({user_type})."""
            res = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=450, temperature=0.2)
            return res.choices[0].text.strip()
        except Exception:
            pass

    # Fallback rule-based advice
    def fmt(x):
        try:
            return f"R {float(x):,.0f}"
        except:
            return str(x)
    adv = []
    if user_type == "individual":
        income = float(inputs.get("Income",0) or 0)
        ded = float(inputs.get("Deductions",0) or 0)
        adv.append(f"Prioritize tax-advantaged savings: Maximize retirement contributions and tax-free savings. Estimate: reducing taxable income by 5-10% may save you ~R {max(0,int(0.05*income))} annually.")
        adv.append("Use diversified low-cost index funds for long-term growth; avoid concentrated bets in a few mega-cap names.")
        adv.append("Review recurring costs — cutting 5% of non-essential spending increases monthly savings.")
        adv.append("Contact us to model precise tax credits and implement a compliant tax strategy that preserves upside.")
    elif user_type == "household":
        inc = float(inputs.get("Household Income",0) or 0)
        kids = int(inputs.get("Children",0) or 0)
        adv.append(f"Keep an emergency fund of 3–6 months of household expenses; consider allocating idle cash to tax-efficient savings.")
        if kids>0:
            adv.append("Explore child/education tax benefits and savings accounts—these often yield both tax efficiency and long-term growth.")
        else:
            adv.append("Consider spousal income-splitting and maximizing retirement account contributions to reduce household tax burden.")
        adv.append("Diversify between equities and inflation-protected assets given current macro backdrop.")
        adv.append("Contact us for a household tax-savings audit and a tailored investment plan.")
    else:  # business
        rev = float(inputs.get("Revenue",0) or 0)
        exp = float(inputs.get("Expenses",0) or 0)
        profit = rev - exp
        adv.append("Classify and capture all allowable deductible expenses; a clean bookkeeping process increases deductible claims and lowers taxable profit.")
        adv.append("Consider tax-efficient owner remuneration (salary vs dividend) and retirement or pension schemes for owners/employees.")
        adv.append("Track business expenses on a dedicated card and implement robust expense categories for proper tax treatment.")
        adv.append("Contact our corporate team — we model scenarios and estimate potential annual tax savings after review.")
    return "\n\n".join(adv)

# ---------------- CHARTS (bar + pie) ----------------
def render_charts(user_type: str, inputs: dict):
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Visual overview")
    # create data depending on type
    if user_type == "individual":
        labels = ["Income","Deductions"]
        values = [float(inputs.get("Income",0)), float(inputs.get("Deductions",0))]
    elif user_type == "household":
        labels = ["Household Income","Deductions"]
        values = [float(inputs.get("Household Income",0)), float(inputs.get("Deductions",0))]
    else:
        labels = ["Revenue","Expenses"]
        values = [float(inputs.get("Revenue",0)), float(inputs.get("Expenses",0))]

    # Bar chart
    fig1, ax1 = plt.subplots(figsize=(6,3))
    if sum(values) == 0:
        ax1.text(0.5, 0.5, "No numeric inputs yet", ha="center", va="center")
    else:
        bars = ax1.bar(labels, values, color=['#2b8cbe','#f03b20'])
        ax1.set_ylabel("Amount (R)")
        for b in bars:
            h = b.get_height()
            ax1.annotate(f"R {h:,.0f}", xy=(b.get_x()+b.get_width()/2, h), xytext=(0,3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    st.pyplot(fig1, clear_figure=True)

    # Pie chart when a breakdown is useful (business with expenses split, or individual with multiple components)
    # For demo, show pie for revenue vs expenses or income vs deductions if both >0
    if all(v>0 for v in values):
        fig2, ax2 = plt.subplots(figsize=(4,4))
        ax2.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#2b8cbe','#f03b20'])
        ax2.axis('equal')
        st.pyplot(fig2, clear_figure=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- EXPORTS ----------------
def build_pdf(inputs: dict, user_type: str, advice: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40,750, f"FinAI Report — {user_type.capitalize()}")
    c.setFont("Helvetica", 10)
    y = 730
    c.drawString(40,y, "Market Context (snapshot):")
    y -= 14
    for line in textwrap.wrap(MARKET_OVERVIEW, width=90):
        c.drawString(45,y, line)
        y -= 12
        if y < 60:
            c.showPage(); y = 750
    y -= 8
    c.drawString(40,y, "Inputs:")
    y -= 12
    for k,v in inputs.items():
        c.drawString(45,y, f"{k}: {v}")
        y -= 12
        if y < 60:
            c.showPage(); y = 750
    y -= 6
    c.drawString(40,y, "AI Advice:")
    y -= 14
    for line in textwrap.wrap(advice, width=90):
        c.drawString(45,y, line)
        y -= 12
        if y < 60:
            c.showPage(); y = 750
    c.save()
    pdf = buf.getvalue()
    buf.close()
    return pdf

def build_excel(inputs: dict, user_type: str, advice: str) -> bytes:
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory': True})
    ws = wb.add_worksheet("Summary")
    ws.write(0,0,"User Type"); ws.write(0,1, user_type)
    ws.write(2,0,"Input"); ws.write(2,1,"Value")
    r = 3
    for k,v in inputs.items():
        ws.write(r,0,k); ws.write(r,1, v); r += 1
    r += 1
    ws.write(r,0,"AI Advice"); ws.write(r,1, advice)
    wb.close()
    return out.getvalue()

# ---------------- PAGES ----------------
def page_home():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title("FinAI — Intelligent Tax & Investment Assistant")
    st.markdown("<small class='small-muted'>Market context (snapshot):</small>")
    st.info(MARKET_OVERVIEW)
    st.markdown("---")
    q = st.text_input("Describe your situation in plain English:", key="home_query", placeholder="e.g. 'I run a small bakery with R2M revenue and R1.4M expenses'  — or 'I am an individual with R400k annual salary' ")
    submit = st.button("Detect & Go", key="home_submit")
    st.markdown("Or choose your path:")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Individual", key="home_ind"):
            st.session_state.user_type = "individual"
            st.session_state.page = "dashboard"
            st.experimental_rerun()
    with c2:
        if st.button("Household", key="home_house"):
            st.session_state.user_type = "household"
            st.session_state.page = "dashboard"
            st.experimental_rerun()
    with c3:
        if st.button("Business", key="home_bus"):
            st.session_state.user_type = "business"
            st.session_state.page = "dashboard"
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # if query submitted, detect and go
    if submit:
        detected = detect_user_type(q)
        st.session_state.user_type = detected
        st.session_state.page = "dashboard"
        st.experimental_rerun()

def page_dashboard():
    ut = st.session_state.get("user_type","individual") or "individual"
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title(f"{ut.capitalize()} Dashboard")
    st.markdown("<small class='small-muted'>All numeric fields accept typed values (no +/-). Specify if amounts are monthly or annual in labels/note.</small>")
    # render input blocks, save into session_state
    if ut == "individual":
        d = st.session_state.individual_inputs
        income = st.number_input("Annual Income (R)", value=float(d.get("Income",0.0)), format="%.2f", help="Total annual taxable income")
        deductions = st.number_input("Annual Deductions (R)", value=float(d.get("Deductions",0.0)), format="%.2f", help="Total deductions")
        st.session_state.individual_inputs = {"Income": income, "Deductions": deductions}
        inputs = st.session_state.individual_inputs
    elif ut == "household":
        d = st.session_state.household_inputs
        hinc = st.number_input("Household Annual Income (R)", value=float(d.get("Household Income",0.0)), format="%.2f")
        kids = st.number_input("Number of Children", value=int(d.get("Children",0)), min_value=0, step=1)
        hd = st.number_input("Total Household Deductions (R)", value=float(d.get("Deductions",0.0)), format="%.2f")
        st.session_state.household_inputs = {"Household Income": hinc, "Children": kids, "Deductions": hd}
        inputs = st.session_state.household_inputs
    else:
        d = st.session_state.business_inputs
        rev = st.number_input("Annual Revenue (R)", value=float(d.get("Revenue",0.0)), format="%.2f")
        exp = st.number_input("Annual Expenses (R)", value=float(d.get("Expenses",0.0)), format="%.2f")
        emp = st.number_input("Number of Employees", value=int(d.get("Employees",0)), min_value=0, step=1)
        st.session_state.business_inputs = {"Revenue": rev, "Expenses": exp, "Employees": emp}
        inputs = st.session_state.business_inputs

    st.markdown("---")
    colL, colR = st.columns([2,1])
    with colL:
        if st.button("Get AI-style Personalized Advice"):
            advice = build_advice(ut, inputs)
            st.session_state.advice_text = advice
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Personalized Advice (high-level)")
            st.write(advice)
            st.markdown("</div>", unsafe_allow_html=True)
            # charts
            render_charts(ut, inputs)
        else:
            # show cached advice if exists
            if st.session_state.advice_text:
                st.markdown("<div class='panel'>", unsafe_allow_html=True)
                st.subheader("Most Recent Advice")
                st.write(st.session_state.advice_text)
                st.markdown("</div>", unsafe_allow_html=True)
                render_charts(ut, inputs)
            else:
                st.info("Press 'Get AI-style Personalized Advice' to generate recommendations based on current market snapshot.")
    with colR:
        st.subheader("Quick actions")
        advice_for_export = st.session_state.advice_text or "No advice generated yet."
        pdf_b = build_pdf(inputs, ut, advice_for_export)
        xlsx_b = build_excel(inputs, ut, advice_for_export)
        st.download_button("Download PDF Report", data=pdf_b, file_name="finai_report.pdf")
        st.download_button("Download Excel Report", data=xlsx_b, file_name="finai_report.xlsx")
        st.markdown("---")
        st.markdown("**Want implementation help?**")
        st.markdown("Contact our team for a tailored, executed plan — we help implement tax strategies, investment allocations, and accounting best-practices.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- APP MAIN ----------------
def main():
    # privacy gate — show first and immediately navigate on accept
    if not st.session_state.privacy_accepted:
        show_privacy_and_block()

    # top nav
    nav1, nav2, nav3, nav4 = st.columns([1,1,1,2])
    if nav1.button("Home"):
        st.session_state.page = "home"
    if nav2.button("Dashboard (Individual)"):
        st.session_state.page = "dashboard"; st.session_state.user_type = "individual"
    if nav3.button("Dashboard (Household)"):
        st.session_state.page = "dashboard"; st.session_state.user_type = "household"
    if nav4.button("Dashboard (Business)"):
        st.session_state.page = "dashboard"; st.session_state.user_type = "business"

    if st.session_state.page == "home":
        page_home()
    elif st.session_state.page == "dashboard":
        page_dashboard()
    else:
        page_home()

if __name__ == "__main__":
    main()
