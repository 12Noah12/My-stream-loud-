# app.py — OptiFin (full, launch-ready)
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import xlsxwriter
import datetime
import io
import textwrap
import math
import requests
import json
import openai

# Optional Google Sheets (graceful fallback if secrets not present)
GS_ENABLED = False
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GS_ENABLED = True
except Exception:
    GS_ENABLED = False

# ---------------- BRAND / CONFIG ----------------
APP_TITLE = "OptiFin"
TAGLINE = "Your Wealth, Optimized."
LOGO_TEXT = "OPTIFIN"

# If you add a logo URL in secrets, PDFs/Excels use it
# st.secrets["LOGO_URL"] = "https://your-cdn/logo.png"
LOGO_URL = st.secrets.get("LOGO_URL", "")

# Optional Google Sheets settings in secrets
# st.secrets["GOOGLE_SHEETS_SERVICE_ACCOUNT"] = {...service account json...}
# st.secrets["GOOGLE_SHEET_ID"] = "1xxxxx..."
GS_SA = st.secrets.get("GOOGLE_SHEETS_SERVICE_ACCOUNT", None)
GS_SHEET_ID = st.secrets.get("GOOGLE_SHEET_ID", None)

# Optional OpenAI
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")

st.set_page_config(page_title=APP_TITLE, page_icon="💼", layout="wide")

# ---------------- THEME / CSS ----------------
BG_GRADIENT = "linear-gradient(180deg, #eef3f9 0%, #ffffff 100%)"
st.markdown(
    f"""
    <style>
    .stApp {{
        background: {BG_GRADIENT};
    }}
    .content-card {{
        background: rgba(255,255,255,0.98);
        padding: 18px 18px 10px 18px;
        border-radius: 12px;
        box-shadow: 0 8px 22px rgba(20,20,40,0.08);
    }}
    .brand-title {{ font-weight:800; color:#08283f; letter-spacing:1px; }}
    .brand-sub {{ color:#08283f; opacity:0.8; }}
    .muted {{ color:#5b6b7a; font-size:0.95rem; }}
    .insight-card {{
        background: linear-gradient(180deg,#ffffff,#f7f9ff);
        border-left: 4px solid #0b5fff;
        padding: 12px;
        border-radius: 10px;
    }}
    .small-note {{ font-size:0.9rem; color:#444; }}
    .btn-dark > button {{ background:#08283f; color:#fff; border-radius:10px; font-weight:700; padding:8px 14px; }}
    .btn-gold > button {{ background:#caa84a; color:#111; border-radius:10px; font-weight:700; padding:8px 14px; }}
    .pill {{
        display:inline-block; padding:6px 10px; border-radius:999px; background:#eff3fb; color:#08283f; font-size:0.85rem; margin-right:6px;
    }}
    .kpi {{
        background:#0b5fff10; border:1px solid #0b5fff30; border-radius:10px; padding:10px; text-align:center;
    }}
    .kpi h4 {{ margin:2px 0 0 0; color:#08283f }}
    .kpi small {{ color:#4d5b6a }}
    .cta {{
        background:#08283f; color:#fff; padding:10px 14px; border-radius:10px; font-weight:700;
    }}
    input[type="text"], textarea, input[type="number"] {{ font-size: 1rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION STATE ----------------
ss = st.session_state
if "page" not in ss: ss.page = "privacy"
if "privacy_accepted" not in ss: ss.privacy_accepted = False
if "user_type" not in ss: ss.user_type = None
if "service_choice" not in ss: ss.service_choice = None
if "inputs_individual" not in ss: ss.inputs_individual = {}
if "inputs_household" not in ss: ss.inputs_household = {}
if "inputs_business" not in ss: ss.inputs_business = {}
if "advice_text" not in ss: ss.advice_text = ""
if "lead" not in ss: ss.lead = {}
if "market_context" not in ss:
    ss.market_context = (
        "Macro: Gradual disinflation with rate-cut bias; maintain liquidity buffer; "
        "diversify across equities, quality bonds, and real assets."
    )

# ---------------- UTIL ----------------
def parse_num(s):
    if s is None: return 0.0
    if isinstance(s, (int,float)): return float(s)
    s = str(s).strip()
    if s == "": return 0.0
    try:
        s = s.replace(",", "").replace("R", "").replace("ZAR", "").replace("$", "").strip()
        return float(s)
    except Exception:
        return 0.0

def openai_available():
    return bool(OPENAI_KEY)

def call_openai(prompt, max_tokens=400, temperature=0.15):
    if not OPENAI_KEY:
        raise RuntimeError("OpenAI key missing")
    openai.api_key = OPENAI_KEY
    resp = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].text.strip()

# ---------------- GOOGLE SHEETS (optional) ----------------
def gs_client():
    if not GS_ENABLED or not GS_SA or not GS_SHEET_ID:
        return None
    try:
        if isinstance(GS_SA, str):
            cred_info = json.loads(GS_SA)
        else:
            cred_info = dict(GS_SA)
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(cred_info, scopes=scopes)
        gc = gspread.authorize(creds)
        return gc
    except Exception:
        return None

def append_lead_to_gsheet(lead_dict):
    gc = gs_client()
    if not gc: return False, "Google Sheets not configured"
    try:
        sh = gc.open_by_key(GS_SHEET_ID)
        ws = sh.sheet1
        row = [
            datetime.datetime.now().isoformat(),
            lead_dict.get("name",""),
            lead_dict.get("email",""),
            lead_dict.get("phone",""),
            lead_dict.get("user_type",""),
            lead_dict.get("service",""),
            lead_dict.get("notes",""),
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True, "Saved to Google Sheets"
    except Exception as e:
        return False, f"Sheets error: {e}"

# ---------------- PRIVACY ----------------
def page_privacy():
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-title' style='font-size:22px'>{LOGO_TEXT}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-sub'>{APP_TITLE} — {TAGLINE}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Privacy & Data Agreement")
    st.markdown(
        """
        **Please read carefully before continuing.**  
        By using OptiFin, you acknowledge and agree that:

        - Your inputs are stored securely and used to generate personalized recommendations and reports.  
        - We do not sell your personal information. Aggregated, anonymized data may be used to improve our models and services.  
        - Advice provided here is high-level and educational. It does not constitute tax, legal, or investment advice. Implementation requires a separate signed engagement.  
        - We take commercially reasonable measures to protect your data, but no system is perfectly secure.  
        - By clicking **Accept & Continue**, you enter a legally binding agreement to these terms.
        """)
    accepted = st.checkbox("I ACCEPT the Privacy & Data Agreement", key="privacy_accept_chk")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Accept & Continue", key="privacy_go_btn"):
            if accepted:
                ss.privacy_accepted = True
                ss.page = "home"
                st.rerun()
            else:
                st.warning("Please tick the checkbox to accept before continuing.")
    with c2:
        if st.button("Decline & Exit", key="privacy_decline_btn"):
            st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- HOME ----------------
def detect_user_type(text):
    t = (text or "").lower()
    if t.strip() == "": return "individual"
    # Try OpenAI classification first
    if openai_available():
        try:
            out = call_openai(
                f"Classify this into one of: individual, household, business.\nQuery: {text}\nReturn one word.",
                max_tokens=6,
                temperature=0.0
            ).strip().lower()
            if out in ("individual","household","business"):
                return out
        except Exception:
            pass
    # Fallback rules
    if any(k in t for k in ["business","company","employees","revenue","invoice","corp","pty"]):
        return "business"
    if any(k in t for k in ["household","family","kids","children","spouse","partner","home"]):
        return "household"
    return "individual"

def page_home():
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center'><div><div class='brand-title' style='font-size:22px'>{LOGO_TEXT}</div><div class='brand-sub'>{APP_TITLE} — {TAGLINE}</div></div><div><span class='pill'>Private</span><span class='pill'>No spam</span></div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### How can we help you today?")
    st.markdown("<div class='muted'>Describe your situation in your own words or choose a category.</div>", unsafe_allow_html=True)
    col = st.columns([3,1,1,1])
    with col[0]:
        query = st.text_input("Ask OptiFin in plain English (optional):", key="home_query", placeholder="e.g., I earn R420k/year, maxing TFSA, need business tax help")
    with col[1]:
        if st.button("Detect & Route", key="home_detect_btn"):
            ss.user_type = detect_user_type(query)
            ss.page = "service"
            st.rerun()
    with col[2]:
        if st.button("Clear", key="home_clear_btn"):
            ss.home_query = ""
            st.experimental_set_query_params()  # harmless no-op
    with col[3]:
        st.markdown("<div class='muted' style='padding-top:8px'>or choose below →</div>", unsafe_allow_html=True)

    b = st.columns(3)
    if b[0].button("Individual", key="home_ind_btn"): ss.user_type="individual"; ss.page="service"; st.rerun()
    if b[1].button("Household", key="home_hh_btn"): ss.user_type="household"; ss.page="service"; st.rerun()
    if b[2].button("Business", key="home_bus_btn"): ss.user_type="business"; ss.page="service"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- SERVICE ----------------
def page_service():
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"### {ss.user_type.capitalize()} — Choose a Service")
    svc = st.selectbox(
        "What would you like to do?",
        options=["Invest","Tax Optimization","Cashflow & Budget","Full Growth Plan"],
        index=0, key="svc_select"
    )
    if st.button("Continue", key="svc_continue_btn"):
        ss.service_choice = svc
        ss.page = "questions"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- QUESTIONS ----------------
def page_questions():
    ut = ss.user_type
    svc = ss.service_choice or "Invest"
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"### {ut.capitalize()} — {svc} Questions")

    st.subheader("Contact")
    name = st.text_input("Full name", key="q_name", value=ss.lead.get("name",""))
    email = st.text_input("Email", key="q_email", value=ss.lead.get("email",""))
    phone = st.text_input("Phone (optional)", key="q_phone", value=ss.lead.get("phone",""))

    st.markdown("---")
    if ut == "individual":
        st.subheader("Individual Financial Details (type numbers; no +/- spinners)")
        income = st.text_input("Annual Gross Income (R)", key="ind_income", value=str(ss.inputs_individual.get("Income","")))
        expenses = st.text_input("Annual Expenses (R)", key="ind_expenses", value=str(ss.inputs_individual.get("Expenses","")))
        investable = st.text_input("Current investable assets (R)", key="ind_investable", value=str(ss.inputs_individual.get("Investable","")))
        monthly_contrib = st.text_input("Monthly investable contribution (R)", key="ind_monthly", value=str(ss.inputs_individual.get("Monthly Contrib","")))
        risk = st.selectbox("Risk tolerance", ["Low","Moderate","High"], index=1, key="ind_risk")
        retire_age = st.selectbox("Target retirement age", [55,60,65,70], index=2, key="ind_ret_age")
        dependents = st.number_input("Dependents", min_value=0, step=1, value=int(ss.inputs_individual.get("Dependents",0) or 0), key="ind_deps")
        notes = st.text_area("Notes (monthly vs annual, existing deductions, etc.)", key="ind_notes", value=ss.inputs_individual.get("Notes",""))

        ss.inputs_individual = {
            "Income": income,
            "Expenses": expenses,
            "Investable": investable,
            "Monthly Contrib": monthly_contrib,
            "Risk": risk,
            "Retirement Age": retire_age,
            "Dependents": int(dependents),
            "Notes": notes
        }

    elif ut == "household":
        st.subheader("Household Financial Details")
        hh_income = st.text_input("Household Annual Income (R)", key="hh_income", value=str(ss.inputs_household.get("Household Income","")))
        hh_deductions = st.text_input("Total Household Deductions (R)", key="hh_deductions", value=str(ss.inputs_household.get("Deductions","")))
        children = st.number_input("Children", min_value=0, step=1, value=int(ss.inputs_household.get("Children",0) or 0), key="hh_children")
        edu = st.text_input("Annual education/childcare costs (R)", key="hh_edu", value=str(ss.inputs_household.get("Education","")))
        housing = st.text_input("Annual mortgage/rent (R)", key="hh_housing", value=str(ss.inputs_household.get("Housing","")))
        monthly_surplus = st.text_input("Monthly investable surplus (R)", key="hh_surplus", value=str(ss.inputs_household.get("Monthly Surplus","")))
        risk = st.selectbox("Risk tolerance", ["Low","Moderate","High"], index=1, key="hh_risk")
        notes = st.text_area("Notes (what you already claim; monthly vs annual)", key="hh_notes", value=ss.inputs_household.get("Notes",""))

        ss.inputs_household = {
            "Household Income": hh_income,
            "Deductions": hh_deductions,
            "Children": int(children),
            "Education": edu,
            "Housing": housing,
            "Monthly Surplus": monthly_surplus,
            "Risk": risk,
            "Notes": notes
        }

    else:
        st.subheader("Business Financial Details")
        revenue = st.text_input("Annual Revenue (R)", key="bus_rev", value=str(ss.inputs_business.get("Revenue","")))
        expenses = st.text_input("Annual Expenses (R)", key="bus_exp", value=str(ss.inputs_business.get("Expenses","")))
        employees = st.number_input("Employees", min_value=0, step=1, value=int(ss.inputs_business.get("Employees",0) or 0), key="bus_emps")
        bus_type = st.selectbox("Business Type", ["Sole Proprietorship","Private Company","Partnership","Other"], index=1, key="bus_type")
        owner_draw = st.text_input("Owner remuneration last 12 months (R)", key="bus_draw", value=str(ss.inputs_business.get("Owner Draw","")))
        tax_paid = st.text_input("Tax paid last year (R)", key="bus_tax_paid", value=str(ss.inputs_business.get("Tax Paid","")))
        monthly_capex = st.text_input("Average monthly capex (R)", key="bus_capex", value=str(ss.inputs_business.get("Monthly Capex","")))
        notes = st.text_area("Notes (existing deductions, assets, structures)", key="bus_notes", value=ss.inputs_business.get("Notes",""))

        ss.inputs_business = {
            "Revenue": revenue,
            "Expenses": expenses,
            "Employees": int(employees),
            "Business Type": bus_type,
            "Owner Draw": owner_draw,
            "Tax Paid": tax_paid,
            "Monthly Capex": monthly_capex,
            "Notes": notes
        }

    ss.lead.update({"name": name, "email": email, "phone": phone})

    st.markdown("---")
    c1, c2 = st.columns([1,1])
    if c1.button("Generate Advice & View Results", key="q_generate"):
        ss.page = "results"; st.rerun()
    if c2.button("Save & View Results", key="q_save"):
        ss.page = "results"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- ADVICE ENGINE ----------------
def deterministic_advice(user_type, data, service):
    adv = []
    def m(x):
        try: return f"R {float(x):,.0f}"
        except: return str(x)
    if user_type == "individual":
        income = parse_num(data.get("Income",0))
        investable = parse_num(data.get("Investable",0))
        monthly = parse_num(data.get("Monthly Contrib",0))
        adv.append("Maximise tax-efficient wrappers first (retirement annuity / pension / TFSA) before taxable accounts.")
        adv.append("Use low-cost diversified ETFs; set quarterly contributions on autopilot and rebalance annually.")
        adv.append("Maintain an emergency fund of 3–6 months’ expenses; avoid high-interest debt before adding risk.")
        adv.append("We can model exact tax savings and automate contributions — contact OptiFin to implement.")
    elif user_type == "household":
        kids = int(data.get("Children",0) or 0)
        deductions = parse_num(data.get("Deductions",0))
        adv.append("Audit household deductions (medical, retirement, education) and allocate to the higher-bracket spouse.")
        adv.append(f"Explore child-linked credits and education savings plans; with {kids} dependents these can be material.")
        adv.append("Balance growth assets with inflation-linked bonds; automate sinking funds for school and housing.")
        adv.append("Contact OptiFin for a household tax & investment blueprint with quantified savings.")
    else:
        revenue = parse_num(data.get("Revenue",0)); expenses = parse_num(data.get("Expenses",0))
        adv.append("Use a dedicated business card & expense policy; standardise categories to avoid missed deductions.")
        adv.append("Optimise owner remuneration (salary vs distributions) and company retirement schemes for tax efficiency.")
        adv.append("Capex scheduling & depreciation planning can smooth cash taxes; review asset write-off rules.")
        adv.append("OptiFin can quantify savings and implement accounting automations. Reach out to start.")
    return "\n\n".join(adv)

def generate_advice(user_type, inputs_raw, service):
    # numeric-cleaned dict (but keep strings where needed)
    cleaned = {k: (parse_num(v) if isinstance(v, str) else v) for k,v in inputs_raw.items()}
    prompt = (
        f"Market: {ss.market_context}\nUser type: {user_type}\nService: {service}\n"
        "User inputs:\n" + "\n".join([f"- {k}: {v}" for k,v in cleaned.items()]) +
        "\nProvide 4 actionable, high-level recommendations tailored to this case. "
        "Do not give step-by-step filing instructions. End with a call-to-action to contact OptiFin for implementation."
    )
    if openai_available():
        try:
            return call_openai(prompt, max_tokens=420, temperature=0.2)
        except Exception:
            pass
    return deterministic_advice(user_type, cleaned, service)

# ---------------- PROJECTIONS (multi-scenario) ----------------
def scenario_growth(initial, monthly, years, rate):
    """Future value with monthly contributions, compounded monthly."""
    n = years * 12
    r = rate / 12.0
    fv = initial * ((1+r)**n)
    if r == 0:
        fv += monthly * n
    else:
        fv += monthly * (((1+r)**n - 1) / r)
    return fv

def build_scenarios(user_type, raw_inputs):
    # Defaults
    if user_type == "individual":
        initial = parse_num(raw_inputs.get("Investable",0))
        monthly = parse_num(raw_inputs.get("Monthly Contrib",0))
        years = 10
        risk = (raw_inputs.get("Risk","Moderate") or "Moderate").lower()
    elif user_type == "household":
        initial = parse_num(raw_inputs.get("Monthly Surplus",0)) * 6  # assume a small starting buffer
        monthly = parse_num(raw_inputs.get("Monthly Surplus",0))
        years = 10
        risk = (raw_inputs.get("Risk","Moderate") or "Moderate").lower()
    else:
        # business: treat capex savings invested
        initial = max(0.0, parse_num(raw_inputs.get("Revenue",0)) - parse_num(raw_inputs.get("Expenses",0))) * 0.1
        monthly = parse_num(raw_inputs.get("Monthly Capex",0)) * 0.1
        years = 7
        risk = "moderate"

    # risk anchor baseline
    if risk == "low":
        base = 0.05
    elif risk == "high":
        base = 0.10
    else:
        base = 0.075

    rates = {
        "Conservative": base - 0.02,
        "Baseline": base,
        "Aggressive": base + 0.02,
    }
    # monthly series for chart
    months = list(range(0, years*12+1, max(1, (years*12)//60)))  # cap ~60 points
    series = {}
    for name, r in rates.items():
        vals = []
        for m in months:
            yrs = m/12.0
            vals.append(scenario_growth(initial, monthly, yrs, r))
        series[name] = vals

    metrics = {k: scenario_growth(initial, monthly, years, r) for k, r in rates.items()}
    return months, series, metrics

# ---------------- EXPORTS ----------------
def fetch_logo_reader():
    if not LOGO_URL: return None
    try:
        r = requests.get(LOGO_URL, timeout=5)
        if r.status_code == 200:
            return ImageReader(io.BytesIO(r.content))
    except Exception:
        return None
    return None

def build_branded_pdf(user_type, inputs_raw, advice, lead):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter

    # Header bar
    c.setFillColorRGB(0.03,0.19,0.31)
    c.rect(0, h-78, w, 78, fill=1, stroke=0)

    # Logo (optional)
    img = fetch_logo_reader()
    c.setFillColorRGB(1,1,1)
    if img:
        c.drawImage(img, 40, h-70, width=120, height=40, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 22)
        c.drawString(40, h-48, LOGO_TEXT)

    c.setFont("Helvetica", 10)
    c.drawString(40, h-68, f"{APP_TITLE} — {TAGLINE}")

    # Footer
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 8)
    c.drawString(40, 30, f"OptiFin Confidential • Generated: {datetime.date.today().isoformat()}")

    # Body
    y = h - 110
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
        c.drawString(45, y, f"{k}: {v}")
        y -= 12
        if y < 110:
            c.showPage(); y = h - 80

    y -= 6
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "High-level Advice:")
    y -= 14
    c.setFont("Helvetica", 10)
    for line in textwrap.wrap(advice, width=90):
        c.drawString(45, y, line)
        y -= 12
        if y < 90:
            c.showPage(); y = h - 80

    c.save()
    return buf.getvalue()

def build_styled_excel(user_type, inputs_raw, advice):
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory': True})
    fmt_title = wb.add_format({'bold': True, 'font_size': 18, 'font_color': '#08283f'})
    fmt_sub = wb.add_format({'font_color': '#08283f'})
    fmt_header = wb.add_format({'bold': True, 'bg_color': '#EDE7D9', 'border':1})
    fmt_money = wb.add_format({'num_format': '#,##0.00', 'align': 'left'})
    fmt_wrap = wb.add_format({'text_wrap': True})
    fmt_box = wb.add_format({'border':1})

    ws = wb.add_worksheet("OptiFin Report")
    ws.set_column('A:A', 32); ws.set_column('B:B', 50)
    ws.write(0,0, LOGO_TEXT, fmt_title)
    ws.write(1,0, f"{APP_TITLE} — {TAGLINE}", fmt_sub)

    ws.write(3,0, "User Type", fmt_header); ws.write(3,1, user_type)
    ws.write(5,0, "Input", fmt_header); ws.write(5,1, "Value", fmt_header)
    row = 6
    for k, v in inputs_raw.items():
        ws.write(row,0,k, fmt_box)
        val = parse_num(v) if isinstance(v, str) else v
        if isinstance(val, (int,float)) and not (isinstance(val, float) and math.isnan(val)):
            ws.write_number(row,1,val, fmt_money)
        else:
            ws.write(row,1,str(v))
        row += 1
    row += 1
    ws.write(row,0,"Advice", fmt_header)
    ws.write(row,1,advice, fmt_wrap)

    ws2 = wb.add_worksheet("Brand")
    ws2.write(0,0, APP_TITLE, fmt_title)
    ws2.write(1,0, TAGLINE, fmt_sub)

    wb.close()
    return out.getvalue()

def build_contact_summary_pdf(user_type, inputs_raw, advice, lead):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter

    c.setFillColorRGB(0.03,0.19,0.31)
    c.rect(0, h-60, w, 60, fill=1, stroke=0)

    img = fetch_logo_reader()
    c.setFillColorRGB(1,1,1)
    if img:
        c.drawImage(img, 40, h-52, width=110, height=32, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 16); c.drawString(40, h-40, LOGO_TEXT)

    y = h - 90
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Contact Summary")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Lead: {lead.get('name','')}")
    y -= 14
    c.drawString(40, y, f"Email: {lead.get('email','')}")
    y -= 14
    c.drawString(40, y, f"Phone: {lead.get('phone','')}")
    y -= 18
    c.setFont("Helvetica-Bold", 11); c.drawString(40,y,"Inputs:"); y -= 12
    c.setFont("Helvetica", 10)
    for k, v in inputs_raw.items():
        c.drawString(45, y, f"{k}: {v}"); y -= 12
        if y < 70: c.showPage(); y = h - 90
    y -= 6
    c.setFont("Helvetica-Bold", 11); c.drawString(40,y,"Advice summary:"); y -= 12
    c.setFont("Helvetica", 10)
    for line in textwrap.wrap(advice, width=90):
        c.drawString(45, y, line); y -= 12
        if y < 70: c.showPage(); y = h - 90
    c.save()
    return buf.getvalue()

# ---------------- RESULTS ----------------
def page_results():
    ut = ss.user_type
    svc = ss.service_choice or "Invest"

    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    st.markdown(f"### {ut.capitalize()} — Results")

    # gather inputs
    if ut == "individual":
        raw_inputs = ss.inputs_individual
    elif ut == "household":
        raw_inputs = ss.inputs_household
    else:
        raw_inputs = ss.inputs_business

    # advice (only generate once per visit)
    if not ss.advice_text:
        ss.advice_text = generate_advice(ut, raw_inputs, svc)

    # scenarios
    months, series, metrics = build_scenarios(ut, raw_inputs)

    # layout: chart + insights
    left, right = st.columns([2,1])
    with left:
        st.subheader("Multi-Scenario Projection")
        # Compact, uncluttered chart
        fig, ax = plt.subplots(figsize=(6.2,2.8))
        x = np.arange(len(months))
        for name, vals in series.items():
            ax.plot(x, vals, linewidth=1.6, label=name)
        ax.set_xticks([0, len(x)//2, len(x)-1])
        ax.set_xticklabels(["Now", f"{int(months[len(x)//2]/12)}y", f"{int(months[-1]/12)}y"])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"R {v:,.0f}"))
        ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.6)
        ax.legend(loc="upper left", ncol=3, fontsize=8, frameon=False)
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

    with right:
        st.subheader("Key Metrics")
        c1, c2, c3 = st.columns(3)
        def fmt(v): 
            try: return f"R {float(v):,.0f}"
            except: return str(v)
        c1.markdown(f"<div class='kpi'><small>Conservative</small><h4>{fmt(metrics['Conservative'])}</h4></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='kpi'><small>Baseline</small><h4>{fmt(metrics['Baseline'])}</h4></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='kpi'><small>Aggressive</small><h4>{fmt(metrics['Aggressive'])}</h4></div>", unsafe_allow_html=True)

        st.markdown("<div class='insight-card' style='margin-top:8px'>", unsafe_allow_html=True)
        st.markdown("**Smart Insights**")
        bullets = [s.strip() for s in (ss.advice_text.replace("\r","").split("\n\n")) if s.strip()]
        for b in bullets[:3]:
            st.markdown(f"- {b}")
        st.markdown("<div class='small-note'>For implementation steps and quantified tax savings, contact OptiFin.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Full Advice")
    st.write(ss.advice_text)

    # Exports
    st.markdown("---")
    st.subheader("Branded Exports")
    colp1, colp2 = st.columns([1,1])
    with colp1:
        pdf_bytes = build_branded_pdf(ut, raw_inputs, ss.advice_text, ss.lead)
        st.download_button("Download Branded PDF", data=pdf_bytes, file_name=f"OptiFin_Report_{ut}.pdf", key="dl_pdf")
    with colp2:
        xlsx_bytes = build_styled_excel(ut, raw_inputs, ss.advice_text)
        st.download_button("Download Branded Excel", data=xlsx_bytes, file_name=f"OptiFin_Report_{ut}.xlsx", key="dl_xlsx")

    # Lead capture
    st.markdown("---")
    st.subheader("Contact & Lead Capture")
    lead_name = st.text_input("Contact name", value=ss.lead.get("name",""), key="lead_name")
    lead_email = st.text_input("Contact email", value=ss.lead.get("email",""), key="lead_email")
    lead_phone = st.text_input("Phone", value=ss.lead.get("phone",""), key="lead_phone")
    lead_notes = st.text_area("Notes", value=ss.lead.get("notes",""), key="lead_notes")
    col_save, col_pdf, col_sheet = st.columns([1,1,1])
    if col_save.button("Save Lead", key="lead_save_btn"):
        ss.lead.update({"name": lead_name, "email": lead_email, "phone": lead_phone, "notes": lead_notes, "user_type": ut, "service": ss.service_choice})
        st.success("Lead saved locally for this session.")
    if col_pdf.button("Download Contact Summary PDF", key="lead_pdf_btn"):
        ss.lead.update({"name": lead_name, "email": lead_email, "phone": lead_phone, "notes": lead_notes, "user_type": ut, "service": ss.service_choice})
        summary_pdf = build_contact_summary_pdf(ut, raw_inputs, ss.advice_text, ss.lead)
        st.download_button("Download Now", data=summary_pdf, file_name="OptiFin_Contact_Summary.pdf", key="lead_pdf_dl")
    if col_sheet.button("Send to Google Sheets", key="lead_sheet_btn"):
        if GS_ENABLED and GS_SA and GS_SHEET_ID:
            ok, msg = append_lead_to_gsheet({
                "name": lead_name, "email": lead_email, "phone": lead_phone,
                "notes": lead_notes, "user_type": ut, "service": ss.service_choice
            })
            if ok: st.success("Lead stored to Google Sheets.")
            else: st.warning(msg)
        else:
            st.info("Google Sheets not configured. Add service account JSON + SHEET ID to secrets.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- NAV ----------------
def render_top_nav():
    c1, c2, c3, c4 = st.columns([1,1,1,3])
    if c1.button("Home", key="nav_home"): ss.page="home"; st.rerun()
    if c2.button("Service", key="nav_service"):
        if ss.user_type: ss.page="service"; st.rerun()
        else: st.warning("Choose a category on Home first.")
    if c3.button("Questions", key="nav_questions"):
        if ss.user_type: ss.page="questions"; st.rerun()
        else: st.warning("Choose a category on Home first.")
    c4.markdown(f"<div style='text-align:right;color:#444'><small>{APP_TITLE} • {TAGLINE}</small></div>", unsafe_allow_html=True)

# ---------------- MAIN ----------------
def main():
    if not ss.privacy_accepted or ss.page == "privacy":
        page_privacy(); return
    render_top_nav()
    if ss.page == "home": page_home()
    elif ss.page == "service": 
        if not ss.user_type: ss.page="home"; st.rerun()
        page_service()
    elif ss.page == "questions":
        if not ss.user_type: ss.page="home"; st.rerun()
        page_questions()
    elif ss.page == "results":
        if not ss.user_type: ss.page="home"; st.rerun()
        page_results()
    else:
        page_home()

if __name__ == "__main__":
    main()
