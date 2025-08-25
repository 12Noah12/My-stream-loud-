# app.py - OptiFin (Full launch-ready Streamlit app)
# Save as app.py and run: streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import io
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import textwrap
import datetime
import openai
import math
import requests  # optional for news (if NEWSAPI_KEY provided)

# ---------------- CONFIG & BRAND ----------------
APP_TITLE = "OptiFin"
TAGLINE = "Your Wealth, Optimized."
LOGO_TEXT = "OPTIFIN"
BG_GRADIENT = "linear-gradient(180deg, #f4f7fb 0%, #ffffff 100%)"

st.set_page_config(page_title=APP_TITLE, page_icon="💼", layout="wide")

# ---------------- CSS for readability (overlay cards) ----------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background: {BG_GRADIENT};
    }}
    .content-card {{
        background: rgba(255,255,255,0.98);
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 6px 18px rgba(20,20,40,0.06);
    }}
    .muted {{ color: #666; font-size:0.95rem; }}
    .brand-title {{ font-size:20px; font-weight:800; color:#08304d; }}
    .brand-sub {{ color:#08304d; font-size:0.95rem; }}
    .insight-card {{
        background: linear-gradient(180deg,#ffffff,#fbfbff);
        border-left: 4px solid #0b5fff;
        padding: 12px;
        border-radius: 8px;
    }}
    .small-note {{ font-size:0.9rem; color:#444; }}
    .btn-primary>button {{ background-color: #08304d; color: white; border-radius: 8px; font-weight:700; padding:8px 12px; }}
    .download-btn>button {{ background-color: #caa84a; color: #111; border-radius: 8px; font-weight:700; padding:8px 12px; }}
    input[type="text"], textarea, input[type="number"] {{ font-size: 1rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "privacy"
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "service_choice" not in st.session_state:
    st.session_state.service_choice = None
if "inputs_individual" not in st.session_state:
    st.session_state.inputs_individual = {}
if "inputs_household" not in st.session_state:
    st.session_state.inputs_household = {}
if "inputs_business" not in st.session_state:
    st.session_state.inputs_business = {}
if "advice_text" not in st.session_state:
    st.session_state.advice_text = ""
if "lead" not in st.session_state:
    st.session_state.lead = {}
if "market_context" not in st.session_state:
    # default embedded market snapshot
    st.session_state.market_context = (
        "Market snapshot: central banks showing moderate easing expectations; "
        "favor diversified, low-cost exposures and maintain liquidity buffer."
    )

# ---------------- UTIL: numeric parsing ----------------
def parse_num(s):
    if s is None:
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    s2 = str(s).strip()
    if s2 == "":
        return 0.0
    try:
        # remove common currency chars and commas
        cleaned = s2.replace(",", "").replace("R", "").replace("ZAR", "").replace("$", "").strip()
        return float(cleaned)
    except Exception:
        return 0.0

# ---------------- UTIL: OpenAI ----------------
def openai_available():
    return bool(st.secrets.get("OPENAI_API_KEY", ""))

def call_openai(prompt, max_tokens=400, temp=0.2):
    key = st.secrets.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("OpenAI API key not set in st.secrets")
    openai.api_key = key
    resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens, temperature=temp)
    return resp.choices[0].text.strip()

# ---------------- PRIVACY PAGE ----------------
def page_privacy():
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; gap:12px; align-items:center'><div class='brand-title'>{LOGO_TEXT}</div><div class='brand-sub'>{APP_TITLE} — {TAGLINE}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<h3>Privacy & Data Agreement</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="small-note">
        <p>To use OptiFin you must accept our Privacy & Data Agreement. Please read carefully:</p>
        <ul>
            <li>Your inputs are stored securely and used to generate personalized financial recommendations and reports.</li>
            <li>OptiFin will not sell your personal data. Aggregated anonymised data may be used to improve services.</li>
            <li>Advice on this platform is informational and does not substitute professional implementation. OptiFin is not liable for outcomes from implementation unless contractually agreed.</li>
            <li>Clicking "Accept & Continue" is a legal acknowledgement of this agreement.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    accepted = st.checkbox("I have read and ACCEPT the Privacy & Data Agreement", key="privacy_chk")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Accept & Continue", key="privacy_accept_btn"):
            if accepted:
                st.session_state.privacy_accepted = True
                # optionally fetch live market headlines if API Key present
                if st.secrets.get("NEWSAPI_KEY", ""):
                    try:
                        headers = {"Authorization": st.secrets.get("NEWSAPI_KEY")}
                        # simple headlines fetch - not necessary; skip if fails
                        r = requests.get("https://newsapi.org/v2/top-headlines?q=markets&language=en&pageSize=3", headers=headers, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            articles = data.get("articles", [])[:3]
                            headlines = " | ".join([a.get("title","") for a in articles])
                            st.session_state.market_context = "Live headlines: " + headlines
                    except Exception:
                        pass
                st.session_state.page = "home"
                st.rerun()
            else:
                st.warning("Please check the box to accept before continuing.")
    with c2:
        if st.button("Decline & Exit", key="privacy_decline_btn"):
            st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- HOME PAGE ----------------
def page_home():
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center'><div><div class='brand-title'>{LOGO_TEXT}</div><div class='brand-sub'>{APP_TITLE} — {TAGLINE}</div></div><div class='small-note'>Built for clarity & privacy</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<h3>How can OptiFin help you today?</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small-note'>Describe your situation in plain English or choose a category below.</div>", unsafe_allow_html=True)

    # NLP query input
    q = st.text_input("Ask OptiFin in plain English (optional):", placeholder="e.g., 'I earn R420k/year and have R30k deductions' ", key="home_query")
    ccol = st.columns([1,1,1])
    if ccol[0].button("Detect & Route", key="home_detect_btn"):
        detected = detect_user_type(q)
        st.session_state.user_type = detected
        st.session_state.page = "service"
        st.rerun()

    # manual category buttons (unique keys)
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Individual", key="home_ind_btn"):
            st.session_state.user_type = "individual"; st.session_state.page = "service"; st.rerun()
    with c2:
        if st.button("Household", key="home_hh_btn"):
            st.session_state.user_type = "household"; st.session_state.page = "service"; st.rerun()
    with c3:
        if st.button("Business", key="home_bus_btn"):
            st.session_state.user_type = "business"; st.session_state.page = "service"; st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- DETECTION (NLP) ----------------
def detect_user_type(text):
    text_l = (text or "").lower()
    if text_l.strip() == "":
        return "individual"
    # try OpenAI classification if available
    if openai_available():
        try:
            prompt = f"Classify this query into one of: individual, household, business. Query: {text}\nReturn exactly one word."
            out = call_openai(prompt, max_tokens=6, temp=0.0)
            out = out.strip().lower()
            if out in ("individual", "household", "business"):
                return out
        except Exception:
            pass
    # fallback rule-based
    if any(k in text_l for k in ["business", "company", "employees", "revenue", "profit", "expenses"]):
        return "business"
    if any(k in text_l for k in ["household", "family", "kids", "children", "home", "spouse", "partner"]):
        return "household"
    return "individual"

# ---------------- SERVICE SELECTION PAGE ----------------
def page_service():
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.title(f"{st.session_state.user_type.capitalize()} — Choose a Service")
    st.markdown("<div class='small-note'>Pick the objective so we can ask targeted questions.</div>", unsafe_allow_html=True)
    service = st.selectbox("What would you like to do?", options=["Invest", "Tax Optimization", "Cashflow & Budget", "Full Growth Plan"], index=0, key="service_select")
    if st.button("Continue to Questions", key="service_continue_btn"):
        st.session_state.service_choice = service
        st.session_state.page = "questions"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- QUESTIONS PAGE (deeper plan inputs) ----------------
def page_questions():
    ut = st.session_state.user_type
    svc = st.session_state.service_choice or "Invest"
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.title(f"{ut.capitalize()} — {svc} Questions")
    st.subheader("Contact (used on your report)")
    name = st.text_input("Full name", key="q_name", value=st.session_state.lead.get("name",""))
    email = st.text_input("Email", key="q_email", value=st.session_state.lead.get("email",""))
    phone = st.text_input("Phone (optional)", key="q_phone", value=st.session_state.lead.get("phone",""))
    st.markdown("---")

    # Individual form
    if ut == "individual":
        st.subheader("Individual Financial Details (type numbers, no +/- spinners)")
        income_s = st.text_input("Annual Gross Income (R)", key="ind_income", value=str(st.session_state.inputs_individual.get("Income","")))
        expenses_s = st.text_input("Annual Expenses (R)", key="ind_expenses", value=str(st.session_state.inputs_individual.get("Expenses","")))
        investable_s = st.text_input("Current investable assets (R)", key="ind_investable", value=str(st.session_state.inputs_individual.get("Investable","")))
        retirement_age = st.selectbox("Planned retirement age", options=[55,60,65,70], index=1, key="ind_ret_age")
        risk = st.selectbox("Risk tolerance", options=["Low","Moderate","High"], index=1, key="ind_risk")
        dependents = st.number_input("Number of dependents", min_value=0, step=1, key="ind_dependents", value=int(st.session_state.inputs_individual.get("Dependents",0) or 0))
        notes = st.text_area("Notes (monthly vs annual etc.)", key="ind_notes", value=st.session_state.inputs_individual.get("Notes",""))

        st.session_state.inputs_individual = {
            "Income": income_s,
            "Expenses": expenses_s,
            "Investable": investable_s,
            "Retirement Age": retirement_age,
            "Risk": risk,
            "Dependents": int(dependents),
            "Notes": notes
        }

    # Household form
    elif ut == "household":
        st.subheader("Household Financial Details")
        hh_income_s = st.text_input("Household Annual Income (R)", key="hh_income", value=str(st.session_state.inputs_household.get("Household Income","")))
        children = st.number_input("Number of children", min_value=0, step=1, key="hh_children", value=int(st.session_state.inputs_household.get("Children",0) or 0))
        hh_deductions_s = st.text_input("Total Household Deductions (R)", key="hh_deductions", value=str(st.session_state.inputs_household.get("Deductions","")))
        education_s = st.text_input("Annual education/childcare costs (R)", key="hh_edu", value=str(st.session_state.inputs_household.get("Education","")))
        housing_s = st.text_input("Annual mortgage/rent (R)", key="hh_housing", value=str(st.session_state.inputs_household.get("Housing","")))
        risk = st.selectbox("Risk tolerance", options=["Low","Moderate","High"], index=1, key="hh_risk")
        notes = st.text_area("Notes", key="hh_notes", value=st.session_state.inputs_household.get("Notes",""))

        st.session_state.inputs_household = {
            "Household Income": hh_income_s,
            "Children": int(children),
            "Deductions": hh_deductions_s,
            "Education": education_s,
            "Housing": housing_s,
            "Risk": risk,
            "Notes": notes
        }

    # Business form
    else:
        st.subheader("Business Financial Details")
        revenue_s = st.text_input("Annual Revenue (R)", key="bus_revenue", value=str(st.session_state.inputs_business.get("Revenue","")))
        expenses_s = st.text_input("Annual Expenses (R)", key="bus_expenses", value=str(st.session_state.inputs_business.get("Expenses","")))
        employees = st.number_input("Number of employees", min_value=0, step=1, key="bus_employees", value=int(st.session_state.inputs_business.get("Employees",0) or 0))
        business_type = st.selectbox("Business Type", options=["Sole Proprietorship","Private Company","Partnership","Other"], index=1, key="bus_type")
        owner_draw_s = st.text_input("Owner remuneration last 12 months (R)", key="bus_owner_draw", value=str(st.session_state.inputs_business.get("Owner Draw","")))
        tax_paid_s = st.text_input("Tax paid last year (R)", key="bus_tax_paid", value=str(st.session_state.inputs_business.get("Tax Paid","")))
        notes = st.text_area("Notes", key="bus_notes", value=st.session_state.inputs_business.get("Notes",""))

        st.session_state.inputs_business = {
            "Revenue": revenue_s,
            "Expenses": expenses_s,
            "Employees": int(employees),
            "Business Type": business_type,
            "Owner Draw": owner_draw_s,
            "Tax Paid": tax_paid_s,
            "Notes": notes
        }

    # persist lead basic info
    st.session_state.lead.update({"name": name, "email": email, "phone": phone})

    st.markdown("---")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Generate Advice & View Results", key="questions_generate_btn"):
            st.session_state.page = "results"
            st.rerun()
    with c2:
        if st.button("Save & Continue to Results (no advice)", key="questions_save_btn"):
            st.session_state.page = "results"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- ADVICE ENGINE ----------------
def generate_advice(user_type, inputs_raw, service):
    # Clean and convert inputs
    cleaned = {}
    for k, v in inputs_raw.items():
        if isinstance(v, (int, float)):
            cleaned[k] = v
        else:
            cleaned[k] = parse_num(v) if isinstance(v, str) else v

    # Build prompt if OpenAI available
    prompt = f"Market context: {st.session_state.market_context}\nUser type: {user_type}\nService: {service}\nUser inputs:\n"
    for k, v in cleaned.items():
        prompt += f"- {k}: {v}\n"
    prompt += (
        "\nYou are a careful professional financial advisor. Provide 4 concise recommendations "
        "and end with a call-to-action to contact OptiFin for implementation. Do not provide legal filing steps."
    )

    if openai_available():
        try:
            out = call_openai(prompt, max_tokens=400, temp=0.15)
            return out
        except Exception:
            pass

    # deterministic fallback
    return deterministic_advice(user_type, cleaned, service)

def deterministic_advice(user_type, data, service):
    def money(x):
        try:
            return f"R {float(x):,.0f}"
        except Exception:
            return str(x)
    adv = []
    if user_type == "individual":
        income = float(data.get("Income",0) or 0)
        adv.append("Prioritise tax-efficient savings: retirement or tax-free accounts to reduce taxable income.")
        adv.append("Use a low-cost diversified ETF allocation and rebalance annually; avoid concentrated bets.")
        adv.append("Build a 3–6 month emergency fund before pursuing higher-risk investments.")
        adv.append("Contact OptiFin for a detailed tax-credit audit and step-by-step implementation.")
    elif user_type == "household":
        adv.append("Maintain an emergency fund and use tax-efficient saving vehicles for education and retirement.")
        adv.append("Explore child-related tax credits and education savings plans if you have dependents.")
        adv.append("Balance long-term growth assets with inflation-protected instruments.")
        adv.append("Contact OptiFin for a household tax & investment audit and modeled savings estimates.")
    else:
        adv.append("Ensure robust bookkeeping and a dedicated business card to capture deductions accurately.")
        adv.append("Review owner remuneration (salary vs dividends) and company retirement schemes for tax efficiency.")
        adv.append("Automate expense categorisation to avoid missed deductions.")
        adv.append("Contact OptiFin's corporate team for a modeled optimization and estimated tax savings.")
    return "\n\n".join(adv)

# ---------------- RESULTS PAGE ----------------
def page_results():
    ut = st.session_state.user_type
    svc = st.session_state.service_choice or "Invest"

    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.title(f"{ut.capitalize()} — Results")

    # select inputs
    if ut == "individual":
        raw_inputs = st.session_state.inputs_individual
    elif ut == "household":
        raw_inputs = st.session_state.inputs_household
    else:
        raw_inputs = st.session_state.inputs_business

    # cleaned numeric map for charts
    numeric_map = {}
    for k, v in raw_inputs.items():
        numeric_map[k] = parse_num(v) if not isinstance(v, (int, float)) else v

    # generate advice if not already
    if not st.session_state.advice_text:
        st.session_state.advice_text = generate_advice(ut, raw_inputs, svc)

    # layout: chart (left) + insight card (right)
    left, right = st.columns([2,1])
    with left:
        st.subheader("Compact Financial Trend")
        labels = list(numeric_map.keys())
        values = [numeric_map[k] for k in labels]
        # limit labels to 6
        if len(labels) > 6:
            labels = labels[:6]
            values = values[:6]
        fig, ax = plt.subplots(figsize=(5,2.2))
        x = np.arange(len(labels))
        ax.plot(x, values, marker='o', linewidth=1.5, color="#08304d")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, fontsize=9)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"R {v:,.0f}"))
        ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

    with right:
        st.subheader("Smart Insights")
        st.markdown("<div class='insight-card'>", unsafe_allow_html=True)
        adv_text = st.session_state.advice_text
        # Split into bullets
        bullets = []
        if "\n\n" in adv_text:
            bullets = adv_text.split("\n\n")
        elif "\n" in adv_text:
            bullets = adv_text.split("\n")
        else:
            bullets = [s.strip() for s in adv_text.split(". ") if s.strip()]
        for i, b in enumerate(bullets[:4]):
            st.markdown(f"**•** {b.strip()}")
        st.markdown("---")
        st.markdown("<div class='small-note'>High-level insights only. For implementation, contact OptiFin.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Full Advice")
    st.write(adv_text)

    # Exports
    st.markdown("---")
    st.subheader("Branded Exports")
    colp1, colp2 = st.columns([1,1])
    with colp1:
        pdf_bytes = build_branded_pdf(ut, raw_inputs, adv_text, st.session_state.lead)
        st.download_button("Download Branded PDF", data=pdf_bytes, file_name=f"OptiFin_Report_{ut}.pdf", key="download_pdf")
    with colp2:
        xlsx_bytes = build_styled_excel(ut, raw_inputs, adv_text)
        st.download_button("Download Branded Excel", data=xlsx_bytes, file_name=f"OptiFin_Report_{ut}.xlsx", key="download_xlsx")

    # Contact capture
    st.markdown("---")
    st.subheader("Contact & Lead Capture")
    lead_name = st.text_input("Contact name", value=st.session_state.lead.get("name",""), key="lead_name")
    lead_email = st.text_input("Contact email", value=st.session_state.lead.get("email",""), key="lead_email")
    lead_notes = st.text_area("Notes for our team", value=st.session_state.lead.get("notes",""), key="lead_notes")
    if st.button("Save Lead & Generate Contact PDF", key="lead_save"):
        st.session_state.lead.update({"name": lead_name, "email": lead_email, "notes": lead_notes, "user_type": ut, "service": svc})
        summary_pdf = build_contact_summary_pdf(ut, raw_inputs, adv_text, st.session_state.lead)
        st.download_button("Download Contact Summary PDF", data=summary_pdf, file_name="OptiFin_Contact_Summary.pdf", key="download_contact_summary")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- EXPORT: PDF & Excel ----------------
def build_branded_pdf(user_type, inputs_raw, advice, lead):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    # header bar
    c.setFillColorRGB(0.03,0.19,0.31)
    c.rect(0, h-72, w, 72, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, h-48, LOGO_TEXT)
    c.setFont("Helvetica", 9)
    c.drawString(40, h-64, f"{APP_TITLE} — {TAGLINE}")
    # footer
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 8)
    c.drawString(40, 30, f"OptiFin Confidential • Generated: {datetime.date.today().isoformat()}")
    # body
    y = h - 100
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"Client: {lead.get('name','(not provided)')}")
    c.setFont("Helvetica", 10)
    c.drawString(350, y, f"User Type: {user_type.capitalize()}")
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Inputs:")
    y -= 12
    c.setFont("Helvetica", 10)
    for k, v in inputs_raw.items():
        line = f"{k}: {v}"
        c.drawString(45, y, (line[:110]))
        y -= 12
        if y < 110:
            c.showPage(); y = h - 100
    y -= 6
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "High-level Advice:")
    y -= 14
    c.setFont("Helvetica", 10)
    for line in textwrap.wrap(advice, width=85):
        c.drawString(45, y, line)
        y -= 12
        if y < 90:
            c.showPage(); y = h - 100
    c.save()
    pdf = buf.getvalue(); buf.close()
    return pdf

def build_styled_excel(user_type, inputs_raw, advice):
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory': True})
    fmt_title = wb.add_format({'bold': True, 'font_size': 16})
    fmt_header = wb.add_format({'bold': True, 'bg_color': '#EDE7D9'})
    fmt_money = wb.add_format({'num_format': '#,##0.00', 'align': 'left'})
    fmt_wrap = wb.add_format({'text_wrap': True})
    ws = wb.add_worksheet("OptiFin Report")
    ws.set_column('A:A', 30)
    ws.set_column('B:B', 50)
    ws.write(0,0, LOGO_TEXT, fmt_title)
    ws.write(1,0, f"Report type: {user_type}")
    ws.write(3,0, "Input", fmt_header)
    ws.write(3,1, "Value", fmt_header)
    row = 4
    for k, v in inputs_raw.items():
        ws.write(row, 0, k)
        val = parse_num(v) if isinstance(v, str) else v
        if isinstance(val, (int,float)) and not (isinstance(val, float) and math.isnan(val)):
            ws.write_number(row, 1, val, fmt_money)
        else:
            ws.write(row, 1, str(v))
        row += 1
    row += 1
    ws.write(row, 0, "Advice", fmt_header)
    ws.write(row, 1, advice, fmt_wrap)
    ws2 = wb.add_worksheet("Brand")
    ws2.write(0,0, APP_TITLE, fmt_title)
    ws2.write(1,0, TAGLINE)
    wb.close()
    return out.getvalue()

def build_contact_summary_pdf(user_type, inputs_raw, advice, lead):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    c.setFillColorRGB(0.03,0.19,0.31)
    c.rect(0, h-60, w, 60, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, h-42, LOGO_TEXT)
    c.setFont("Helvetica", 9)
    c.drawString(40, h-58, f"Contact Summary • {datetime.date.today().isoformat()}")
    y = h - 90
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Lead: {lead.get('name','(not provided)')}")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Email: {lead.get('email','')}")
    y -= 16
    c.drawString(40, y, "Inputs summary:")
    y -= 12
    for k, v in inputs_raw.items():
        c.drawString(45, y, f"{k}: {v}")
        y -= 12
        if y < 60:
            c.showPage(); y = h - 90
    y -= 6
    c.drawString(40, y, "Advice summary:")
    y -= 12
    for line in textwrap.wrap(advice, width=85):
        c.drawString(45, y, line)
        y -= 12
        if y < 60:
            c.showPage(); y = h - 90
    c.save()
    pdf = buf.getvalue(); buf.close()
    return pdf

# ---------------- TOP NAV ----------------
def render_top_nav():
    col1, col2, col3, col4 = st.columns([1,1,1,3])
    with col1:
        if st.button("Home", key="topnav_home_btn"):
            st.session_state.page = "home"; st.rerun()
    with col2:
        if st.button("Service", key="topnav_service_btn"):
            if st.session_state.user_type:
                st.session_state.page = "service"; st.rerun()
            else:
                st.warning("Choose a category from Home first.")
    with col3:
        if st.button("Questions", key="topnav_questions_btn"):
            if st.session_state.user_type:
                st.session_state.page = "questions"; st.rerun()
            else:
                st.warning("Choose a category from Home first.")
    with col4:
        st.markdown(f"<div style='text-align:right; color:#444'><small>{APP_TITLE} • {TAGLINE}</small></div>", unsafe_allow_html=True)

# ---------------- MAIN ----------------
def main():
    if not st.session_state.privacy_accepted or st.session_state.page == "privacy":
        page_privacy()
        return

    render_top_nav()

    page = st.session_state.page
    if page == "home":
        page_home()
    elif page == "service":
        page_service()
    elif page == "questions":
        page_questions()
    elif page == "results":
        page_results()
    else:
        page_home()

if __name__ == "__main__":
    main()
