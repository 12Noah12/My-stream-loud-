# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import textwrap
import datetime
import requests
import openai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# ---------------- CONSTANTS & MARKET SNAPSHOT FALLBACK ----------------
EMBEDDED_MARKET_OVERVIEW = (
    "Market snapshot (embedded):\n"
    "- Central banks have become somewhat dovish; markets price possible rate cuts in coming months.\n"
    "- Global growth modestly improving but trade & geopolitical risks persist.\n"
    "- Diversification across quality equities and real-assets recommended in current environment.\n"
    "- Keep liquidity buffers until macro trends clarify; favor low-cost diversified ETFs for long-term investing."
)

LOGO_TITLE = "FinAI"
BRAND_LINE = "Private & Professional — Tailored tax and investment solutions"

# ---------------- STYLES & CONTRAST ----------------
BG_IMAGE_URL = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1470&q=80"
st.markdown(
    f"""
    <style>
    .stApp {{ background-image: url('{BG_IMAGE_URL}'); background-size: cover; background-position: center; }}
    .panel {{ background: rgba(255,255,255,0.97); padding: 18px; border-radius: 10px; color: #111; }}
    .muted {{ color:#555; font-size:0.9em; }}
    .btn-black button {{ color:black !important; font-weight:700; }}
    .search-glow input {{ box-shadow: 0 0 14px rgba(79,195,86,0.28); border-radius:8px; padding:10px; }}
    .small-note {{ font-size:0.9em; color:#444; }}
    .logo-title {{ font-size:22px; font-weight:800; color:#111; }}
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
# store inputs per type
if "individual_inputs" not in st.session_state:
    st.session_state.individual_inputs = {}
if "household_inputs" not in st.session_state:
    st.session_state.household_inputs = {}
if "business_inputs" not in st.session_state:
    st.session_state.business_inputs = {}
if "advice_text" not in st.session_state:
    st.session_state.advice_text = ""
if "market_context" not in st.session_state:
    st.session_state.market_context = EMBEDDED_MARKET_OVERVIEW
if "contact_lead" not in st.session_state:
    st.session_state.contact_lead = {}

# ---------------- OPTIONAL: LIVE NEWS FETCH (if NEWSAPI_KEY provided) ----------------
def fetch_live_market_news():
    key = st.secrets.get("NEWSAPI_KEY", "")
    if not key:
        return st.session_state.market_context
    try:
        url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=5&q=markets OR economy OR inflation"
        headers = {"Authorization": key}
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])[:5]
            lines = []
            for a in articles:
                title = a.get("title", "")
                src = a.get("source", {}).get("name", "")
                lines.append(f"• {title} ({src})")
            return "Live market headlines:\n\n" + "\n".join(lines)
    except Exception:
        pass
    return st.session_state.market_context

# ---------------- OPENAI HELPERS ----------------
def openai_available():
    return bool(st.secrets.get("OPENAI_API_KEY", ""))

def call_openai(prompt: str, max_tokens=400, temperature=0.2):
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OpenAI key not set")
    openai.api_key = api_key
    resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens, temperature=temperature)
    return resp.choices[0].text.strip()

# ---------------- PRIVACY AGREEMENT PAGE ----------------
def show_privacy_page():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown(f"<div class='logo-title'>{LOGO_TITLE}</div><div class='muted'>{BRAND_LINE}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<h3 style='color:#111'>Privacy & Data Agreement</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='line-height:1.4; color:#222'>
        <p>Welcome to FinAI. To use this service you must accept this Privacy & Data Agreement.</p>
        <ul>
          <li>Your inputs will be stored securely and used to generate personalized advice and reports.</li>
          <li>FinAI will not sell your personal data. Aggregated anonymized data may be used to improve services.</li>
          <li>Advice is informational — implementation requires professional assistance; FinAI is not liable for outcomes.</li>
          <li>Click 'Accept & Continue' to proceed. If you decline, you will be unable to use the platform.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    accepted = st.checkbox("I HAVE READ AND ACCEPT THIS PRIVACY & DATA AGREEMENT")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Accept & Continue"):
            if accepted:
                st.session_state.privacy_accepted = True
                # load live news into context if available
                st.session_state.market_context = fetch_live_market_news()
                st.session_state.page = "home"
                # Streamlit reruns after interaction automatically; no explicit st.rerun()
            else:
                st.warning("Please check the checkbox to accept the agreement before continuing.")
    with col2:
        if st.button("Decline & Exit"):
            st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- HOME PAGE ----------------
def show_home():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown(f"<div class='logo-title'>{LOGO_TITLE}</div><div class='muted'>{BRAND_LINE}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<small class='muted'>Market context used when generating advice:</small>", unsafe_allow_html=True)
    st.info(st.session_state.market_context)
    st.markdown("---")

    q = st.text_input("🔎 Describe your situation (plain English):", key="home_query", placeholder="e.g. 'I have R600k salary and R50k deductions'; or 'I run a small cafe with R2M revenue'")
    if st.button("Detect & Route"):
        detected = detect_user_type(q)
        st.session_state.user_type = detected
        st.session_state.page = "services"  # next step: pick service
    st.markdown("— or choose your path —")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Individual"):
            st.session_state.user_type = "individual"; st.session_state.page = "services"
    with c2:
        if st.button("Household"):
            st.session_state.user_type = "household"; st.session_state.page = "services"
    with c3:
        if st.button("Business"):
            st.session_state.user_type = "business"; st.session_state.page = "services"
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- NATURAL-LANGUAGE DETECTION (OpenAI when available) ----------------
def detect_user_type(text: str) -> str:
    text_l = (text or "").lower()
    if openai_available() and text.strip():
        try:
            prompt = f"Classify this financial query into one of: individual, household, business. Query: {text}"
            out = call_openai(prompt, max_tokens=6, temperature=0.0)
            out = out.strip().lower()
            if out in ("individual", "household", "business"):
                return out
        except Exception:
            pass
    # fallback rules
    if any(k in text_l for k in ["business", "company", "employees", "revenue", "profit", "expenses"]):
        return "business"
    if any(k in text_l for k in ["household", "family", "kids", "children", "partner", "spouse", "home"]):
        return "household"
    return "individual"

# ---------------- SERVICE CHOOSER (after selecting user type) ----------------
def show_services_selector():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title(f"{st.session_state.user_type.capitalize()} — Choose a Service")
    st.markdown("Pick what you'd like to do today. Each service will ask a few targeted questions.")
    service = st.selectbox("Select service", ["Invest", "Tax Optimization", "Cashflow & Budget", "Full Growth Plan"], index=0)
    if st.button("Continue to questions"):
        st.session_state.chosen_service = service
        st.session_state.page = "questions"
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- QUESTIONS FOR EACH FLOW (more detailed, relevant) ----------------
def show_questions_and_form():
    ut = st.session_state.user_type
    svc = st.session_state.get("chosen_service", "Invest")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title(f"{ut.capitalize()} — {svc}")
    st.markdown("<small class='muted'>Please answer these questions as accurately as possible — indicate if values are monthly or annual in the label.</small>")

    # Common fields
    contact_name = st.text_input("Full name", value=st.session_state.contact_lead.get("name",""))
    contact_email = st.text_input("Email (so we can follow up)", value=st.session_state.contact_lead.get("email",""))
    contact_phone = st.text_input("Phone (optional)", value=st.session_state.contact_lead.get("phone",""))

    # Persist partial lead info
    st.session_state.contact_lead.update({"name": contact_name, "email": contact_email, "phone": contact_phone, "user_type": ut, "service": svc})

    # Now service-specific inputs
    inputs = {}
    if ut == "individual":
        st.subheader("Individual Financial Details")
        col1, col2 = st.columns(2)
        with col1:
            income = st.number_input("Annual Gross Income (R)", value=float(st.session_state.individual_inputs.get("Income",0.0)), format="%.2f", help="Total annual gross income")
            filing_status = st.selectbox("Filing status", ["Single", "Married filing jointly", "Married filing separately", "Head of household"], index=0)
            employed = st.checkbox("Are you employed (W-2 / PAYE)?", value=True)
        with col2:
            deductions = st.number_input("Annual Deductions (R)", value=float(st.session_state.individual_inputs.get("Deductions",0.0)), format="%.2f", help="Total declared deductions")
            retirement_balance = st.number_input("Retirement savings balance (R)", value=float(st.session_state.individual_inputs.get("Retirement",0.0)), format="%.2f")
            other_income = st.number_input("Other taxable income (R)", value=float(st.session_state.individual_inputs.get("Other",0.0)), format="%.2f")
        inputs = {"Income":income, "Deductions":deductions, "Filing Status": filing_status, "Employed": employed, "Retirement": retirement_balance, "Other Income": other_income}
        st.session_state.individual_inputs = inputs

    elif ut == "household":
        st.subheader("Household Details")
        col1, col2 = st.columns(2)
        with col1:
            hh_income = st.number_input("Household Annual Income (R)", value=float(st.session_state.household_inputs.get("Household Income",0.0)), format="%.2f")
            children = st.number_input("Number of Dependents", value=int(st.session_state.household_inputs.get("Children",0)), min_value=0, step=1)
            primary_income_earner = st.text_input("Primary income earner (name, optional)", value=st.session_state.household_inputs.get("Primary",""))
        with col2:
            deductions = st.number_input("Total Household Deductions (R)", value=float(st.session_state.household_inputs.get("Deductions",0.0)), format="%.2f")
            childcare_costs = st.number_input("Annual childcare / education costs (R)", value=float(st.session_state.household_inputs.get("ChildCosts",0.0)), format="%.2f")
            mortgage_rent = st.number_input("Annual mortgage / rent (R)", value=float(st.session_state.household_inputs.get("Housing",0.0)), format="%.2f")
        inputs = {"Household Income": hh_income, "Children": int(children), "Deductions": deductions, "ChildCosts": childcare_costs, "Housing": mortgage_rent}
        st.session_state.household_inputs = inputs

    else:  # business
        st.subheader("Business Details")
        col1, col2 = st.columns(2)
        with col1:
            revenue = st.number_input("Annual Revenue (R)", value=float(st.session_state.business_inputs.get("Revenue",0.0)), format="%.2f")
            business_type = st.selectbox("Business type", ["Sole Proprietorship","Private Company (Pty Ltd)","Partnership","Other"], index=1)
            employees = st.number_input("Number of Employees", value=int(st.session_state.business_inputs.get("Employees",0)), min_value=0, step=1)
        with col2:
            expenses = st.number_input("Annual Expenses (R)", value=float(st.session_state.business_inputs.get("Expenses",0.0)), format="%.2f")
            owner_draw = st.number_input("Owner remuneration last 12 months (R)", value=float(st.session_state.business_inputs.get("OwnerDraw",0.0)), format="%.2f")
            tax_paid = st.number_input("Tax paid last year (R)", value=float(st.session_state.business_inputs.get("TaxPaid",0.0)), format="%.2f")
        inputs = {"Revenue": revenue, "Expenses": expenses, "Business Type": business_type, "Employees": int(employees), "Owner Draw": owner_draw, "Tax Paid": tax_paid}
        st.session_state.business_inputs = inputs

    st.markdown("---")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Generate Advice & Preview"):
            # build advice
            advice = generate_smart_advice(ut, inputs)
            st.session_state.advice_text = advice
            st.session_state.page = "results"
    with c2:
        if st.button("Save & Continue to Results (no advice)"):
            st.session_state.page = "results"
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- ADVICE: OpenAI + fallback deterministic ----------------
def generate_smart_advice(user_type: str, inputs: dict) -> str:
    """
    Return tailored, market-aware advice. Use OpenAI if provided; otherwise fallback logic.
    """
    context = st.session_state.market_context
    summary = "\n".join([f"{k}: {v}" for k, v in inputs.items()])

    if openai_available():
        try:
            prompt = f"""
You are a conservative, professional financial advisor. Market context:
{context}

User type: {user_type}
User inputs:
{summary}

Provide:
- 4 high-quality actionable bullets tailored to the user's inputs (include rough conservative savings/impact estimates where possible).
- One short CTA: how to contact the firm for implementation.
Do not include detailed legal filing instructions.
"""
            out = call_openai(prompt, max_tokens=500, temperature=0.15)
            return out
        except Exception as e:
            # fallback if OpenAI fails
            pass

    # Fallback deterministic advisor
    return fallback_advice(user_type, inputs)

def fallback_advice(user_type: str, inputs: dict) -> str:
    def fmt(x):
        try:
            return f"R {float(x):,.0f}"
        except:
            return str(x)
    bullets = []
    if user_type == "individual":
        inc = float(inputs.get("Income",0) or 0)
        ded = float(inputs.get("Deductions",0) or 0)
        bullets.append(f"Maximize tax-advantaged vehicles (retirement, tax-free). Conservatively, redirecting 5% of income (~{fmt(0.05*inc)}) annually may produce meaningful tax reduction.")
        bullets.append("Prioritize low-cost ETF allocations and regular monthly contributions (dollar-cost averaging) rather than market-timing.")
        bullets.append("Audit recurring costs and non-essential subscriptions — trimming 5–10% improves monthly cashflow.")
        bullets.append("Contact FinAI for a personalised tax-credit audit and step-by-step implementation.")
    elif user_type == "household":
        hh = float(inputs.get("Household Income",0) or 0)
        kids = int(inputs.get("Children",0) or 0)
        bullets.append("Create a 3–6 month emergency fund and allocate spare cash to tax-efficient vehicles.")
        if kids > 0:
            bullets.append("Explore child/education tax incentives and dedicated savings plans to reduce long-term cost.")
        else:
            bullets.append("Consider income-splitting strategies and maximizing retirement contributions.")
        bullets.append("Diversify across equities and inflation-protected assets given current macro conditions.")
        bullets.append("Contact FinAI for a household-specific tax & investment audit.")
    else:
        rev = float(inputs.get("Revenue",0) or 0)
        exp = float(inputs.get("Expenses",0) or 0)
        bullets.append("Ensure meticulous bookkeeping to capture all legitimate business deductions; this often materially lowers taxable profit.")
        bullets.append("Consider a tax-efficient mix of owner salary and dividends — it can reduce payroll taxes and total tax.")
        bullets.append("Use a dedicated corporate card and automate expense categorization to maximize deductibles.")
        bullets.append("Contact FinAI corporate team for a modeled optimization with estimated tax savings.")
    return "\n\n".join(bullets)

# ---------------- RESULTS PAGE (advice, charts, exports, lead capture) ----------------
def show_results_page():
    ut = st.session_state.user_type
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title(f"{ut.capitalize()} — Results & Next Steps")
    advice = st.session_state.advice_text or "No advice generated yet. Run 'Generate Advice & Preview' from the questions page."

    st.subheader("AI-style Recommendations")
    st.write(advice)

    # show charts depending on user type and stored inputs
    inputs = st.session_state.individual_inputs if ut=="individual" else (st.session_state.household_inputs if ut=="household" else st.session_state.business_inputs)
    render_visuals(ut, inputs)

    st.markdown("---")
    # multi-year projection if Invest service selected
    if st.session_state.get("chosen_service","").lower() in ("invest","invest", "investing"):
        show_multi_year_projection(inputs)

    # Exports: styled PDF and Excel with branding
    st.subheader("Download Branded Report")
    pdf_bytes = build_branded_pdf(inputs, ut, advice)
    xlsx_bytes = build_styled_excel(inputs, ut, advice)
    st.download_button("Download Branded PDF", data=pdf_bytes, file_name=f"FinAI_report_{ut}.pdf")
    st.download_button("Download Branded Excel", data=xlsx_bytes, file_name=f"FinAI_report_{ut}.xlsx")

    st.markdown("---")
    # Lead capture: contact form and prepopulated email
    st.subheader("Contact & Lead Capture")
    lead = st.session_state.contact_lead or {}
    name = st.text_input("Your name", value=lead.get("name",""))
    email = st.text_input("Email", value=lead.get("email",""))
    phone = st.text_input("Phone", value=lead.get("phone",""))
    notes = st.text_area("Additional notes (what you'd like us to focus on)", value=lead.get("notes",""))

    if st.button("Save & Create Contact Summary"):
        st.session_state.contact_lead.update({"name":name, "email":email, "phone":phone, "notes":notes, "user_type":ut})
        summary_bytes = generate_contact_summary(inputs, ut, advice, st.session_state.contact_lead)
        st.download_button("Download Contact Summary (PDF)", data=summary_bytes, file_name="FinAI_contact_summary.pdf")
        # Also generate a mailto link (prepopulated)
        subject = f"FinAI inquiry — {ut.capitalize()} {st.session_state.get('chosen_service','')}"
        body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nNotes:\n{notes}\n\nSummary of Advice:\n{advice[:1000]}"
        mailto = f"mailto:contact@finai.example?subject={requests.utils.quote(subject)}&body={requests.utils.quote(body)}"
        st.markdown(f"[Open email to contact us]({mailto})")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- VISUALS: bar + pie + multi-year projection ----------------
def render_visuals(user_type: str, inputs: dict):
    st.subheader("Visual Summary")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    if user_type == "individual":
        labels = ["Income","Deductions"]
        vals = [float(inputs.get("Income",0)), float(inputs.get("Deductions",0))]
    elif user_type == "household":
        labels = ["Household Income","Deductions","Child Costs"]
        vals = [float(inputs.get("Household Income",0)), float(inputs.get("Deductions",0)), float(inputs.get("ChildCosts",0) or 0)]
    else:
        labels = ["Revenue","Expenses","Owner Draw"]
        vals = [float(inputs.get("Revenue",0)), float(inputs.get("Expenses",0)), float(inputs.get("Owner Draw",0) or 0)]

    # Bar
    fig, ax = plt.subplots(figsize=(6,3))
    if sum(vals) == 0:
        ax.text(0.5, 0.5, "No numeric inputs yet", ha="center", va="center")
    else:
        bars = ax.bar(labels, vals, color=['#2b8cbe','#f03b20','#7fc97f'][:len(labels)])
        ax.set_ylabel("Amount (R)")
        for b in bars:
            h = b.get_height()
            ax.annotate(f"R {h:,.0f}", xy=(b.get_x()+b.get_width()/2, h), xytext=(0,3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        ax.set_ylim(0, max(vals)*1.2 if max(vals)>0 else 1)
    st.pyplot(fig, clear_figure=True)

    # Pie if >2 categories >0
    positive_vals = [v for v in vals if v > 0]
    if len(positive_vals) >= 2 and sum(positive_vals) > 0:
        fig2, ax2 = plt.subplots(figsize=(4,4))
        labels_nonzero = [labels[i] for i, v in enumerate(vals) if v>0]
        vals_nonzero = [v for v in vals if v>0]
        ax2.pie(vals_nonzero, labels=labels_nonzero, autopct='%1.1f%%', colors=['#2b8cbe','#f03b20','#7fc97f'], startangle=90)
        ax2.axis('equal')
        st.pyplot(fig2, clear_figure=True)
    st.markdown("</div>", unsafe_allow_html=True)

def show_multi_year_projection(inputs: dict):
    st.subheader("Multi-year Investment Projection (scenario)")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    initial = st.number_input("Current investable capital (R)", value=float(inputs.get("Initial",0.0)), format="%.2f")
    monthly = st.number_input("Monthly contribution (R)", value=float(inputs.get("Monthly",0.0)), format="%.2f")
    years = st.slider("Projection period (years)", min_value=1, max_value=40, value=20)
    rate = st.slider("Expected annual return (%)", min_value=0.0, max_value=20.0, value=7.0)
    ann_rate = rate/100.0
    # compute projection
    months = years*12
    balances = []
    bal = initial
    for m in range(1, months+1):
        bal = bal*(1+ann_rate/12) + monthly
        if m%12==0:
            balances.append(bal)
    years_range = list(range(1, years+1))
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(years_range, balances, marker='o')
    ax.set_xlabel("Years")
    ax.set_ylabel("Portfolio value (R)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"R {x:,.0f}"))
    st.pyplot(fig, clear_figure=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- BRANDED PDF & STYLED EXCEL ----------------
def build_branded_pdf(inputs: dict, user_type: str, advice: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    # Header / branding
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40,760, LOGO_TITLE)
    c.setFont("Helvetica", 10)
    c.drawString(40,746, BRAND_LINE)
    c.line(40,740,550,740)
    # meta
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40,720, f"Report: {user_type.capitalize()} — {datetime.date.today().isoformat()}")
    y = 700
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Market Context:")
    y -= 14
    c.setFont("Helvetica", 9)
    for line in textwrap.wrap(st.session_state.market_context, width=90):
        c.drawString(45,y,line); y -= 12
        if y < 60:
            c.showPage(); y = 750
    y -= 6
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40,y, "Inputs:")
    y -= 14
    c.setFont("Helvetica", 9)
    for k,v in inputs.items():
        c.drawString(45,y,f"{k}: {v}"); y -= 12
        if y < 60:
            c.showPage(); y = 750
    y -= 6
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40,y, "Advice:")
    y -= 14
    c.setFont("Helvetica", 9)
    for line in textwrap.wrap(advice, width=90):
        c.drawString(45,y, line); y -= 12
        if y < 60:
            c.showPage(); y = 750
    c.save()
    pdf = buf.getvalue(); buf.close()
    return pdf

def build_styled_excel(inputs: dict, user_type: str, advice: str) -> bytes:
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory': True})
    fmt_title = wb.add_format({'bold': True, 'font_size': 14})
    fmt_header = wb.add_format({'bold': True, 'bg_color': '#F2F2F2'})
    fmt_money = wb.add_format({'num_format': '#,##0.00', 'align':'left'})
    ws = wb.add_worksheet("Summary")
    ws.write(0,0, LOGO_TITLE, fmt_title)
    ws.write(1,0, f"Report type: {user_type}")
    ws.write(3,0, "Input", fmt_header)
    ws.write(3,1, "Value", fmt_header)
    row = 4
    for k,v in inputs.items():
        ws.write(row,0,k)
        if isinstance(v, (int,float)):
            ws.write(row,1, v, fmt_money)
        else:
            ws.write(row,1, str(v))
        row += 1
    row += 1
    ws.write(row,0, "Advice", fmt_header)
    ws.write(row,1, advice)
    # brand sheet
    ws2 = wb.add_worksheet("Brand")
    brand_fmt = wb.add_format({'bold':True, 'font_size':18})
    ws2.write(0,0, LOGO_TITLE, brand_fmt)
    ws2.write(1,0, BRAND_LINE)
    wb.close()
    return out.getvalue()

# ---------------- CONTACT SUMMARY (branded one-page PDF) ----------------
def generate_contact_summary(inputs: dict, user_type: str, advice: str, lead: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40,760, LOGO_TITLE + " — Contact Summary")
    c.setFont("Helvetica", 10)
    c.drawString(40,746, f"Prepared for: {lead.get('name','(not provided)')}")
    c.drawString(40,734, f"Contact: {lead.get('email','')}  |  {lead.get('phone','')}")
    c.line(40,726,550,726)
    y = 712
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40,y,"Client Inputs:")
    y -= 14
    c.setFont("Helvetica", 10)
    for k,v in inputs.items():
        c.drawString(45,y, f"{k}: {v}"); y -= 12
        if y < 60:
            c.showPage(); y = 750
    y -= 6
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40,y,"AI Advice Summary:")
    y -= 14
    for line in textwrap.wrap(advice, width=90):
        c.drawString(45,y, line); y -= 12
        if y < 60:
            c.showPage(); y = 750
    c.save()
    pdf = buf.getvalue(); buf.close()
    return pdf

# ---------------- MAIN APP ROUTING ----------------
def main():
    # privacy gate
    if not st.session_state.privacy_accepted or st.session_state.page == "privacy":
        show_privacy_page()
        return

    # top nav
    nav1,nav2,nav3,nav4 = st.columns([1,1,1,2])
    if nav1.button("Home"): st.session_state.page = "home"
    if nav2.button("Individual"): st.session_state.user_type="individual"; st.session_state.page="services"
    if nav3.button("Household"): st.session_state.user_type="household"; st.session_state.page="services"
    if nav4.button("Business"): st.session_state.user_type="business"; st.session_state.page="services"

    # route
    if st.session_state.page == "home":
        show_home()
    elif st.session_state.page == "services":
        show_services_selector()
    elif st.session_state.page == "questions":
        show_questions_and_form()
    elif st.session_state.page == "results":
        show_results_page()
    elif st.session_state.page == "dashboard":
        # direct dashboard as legacy route
        st.session_state.page = "services"
        show_services_selector()
    else:
        show_home()

# small wrapper to expose service selector (we defined earlier)
def show_services_selector():
    show_services_selector_inner = show_services_selector_inner_impl
    show_services_selector_inner()

def show_services_selector_inner_impl():
    show_services_selector_impl()

def show_services_selector_impl():
    show_services_selector_ui()  # calls function below

def show_services_selector_ui():
    show_services_selector()  # circular alias to original; avoid deep complexity

# Because of the way we referenced the selector earlier, define the simple one now:
def show_services_selector():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.title(f"{st.session_state.user_type.capitalize()} — Choose a Service")
    st.markdown("Pick one of the services below that best matches what you want to do.")
    service = st.selectbox("Service", ["Invest", "Tax Optimization", "Cashflow & Budget", "Full Growth Plan"], index=0)
    if st.button("Continue"):
        st.session_state.chosen_service = service
        st.session_state.page = "questions"
    st.markdown("</div>", unsafe_allow_html=True)

# Run app
if __name__ == "__main__":
    main()
