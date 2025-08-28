# app.py - OptiFin Intelligent Financial Planning Suite - Part 1 of 3
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import date, datetime, timedelta
from io import BytesIO
import json
import pathlib
import base64
from collections import deque

# Optional imports
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ---- Constants ----
APP_NAME = "OptiFin"
APP_YEAR = 2025
DEFAULT_REGION = "South Africa"
DEFAULT_CURRENCY = "ZAR"
CURRENCY_SYMBOL = "R"
LOCALE = "Africa/Johannesburg"

BACKGROUND_IMAGES = {
    "Finance 1": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1950&q=80",
    "Architecture 1": "https://images.unsplash.com/photo-1549924231-f129b911e442?auto=format&fit=crop&w=1950&q=80",
    "Finance 2": "https://images.unsplash.com/photo-1515165562835-c702d4d30ea3?auto=format&fit=crop&w=1950&q=80",
}

ROUTE_LIST = [
    "individual:invest",
    "individual:tax",
    "individual:retirement",
    "individual:estate",
    "household:budget",
    "household:tax",
    "household:invest",
    "household:protection",
    "business:tax",
    "business:invest",
    "business:cashflow",
    "business:retirement",
    "business:valuation",
]

ROUTES = {
    'individual:invest': ('individual', 'investment'),
    'individual:tax': ('individual', 'tax'),
    'individual:retirement': ('individual', 'retirement'),
    'individual:estate': ('individual', 'estate'),
    'household:budget': ('household', 'budget'),
    'household:tax': ('household', 'tax'),
    'household:invest': ('household', 'investment'),
    'household:protection': ('household', 'protection'),
    'business:tax': ('business', 'tax'),
    'business:invest': ('business', 'investment'),
    'business:cashflow': ('business', 'cashflow'),
    'business:retirement': ('business', 'retirement'),
    'business:valuation': ('business', 'valuation'),
}

TOOLTIP_ICONS = " <span style='color:#4ade80; cursor:help;'>[?]</span>"

# ---- Session State Init ----
def init_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'privacy_gate'
    if 'consent_accepted' not in st.session_state:
        st.session_state.consent_accepted = False
    if 'user_segment' not in st.session_state:
        st.session_state.user_segment = None
    if 'sub_module' not in st.session_state:
        st.session_state.sub_module = None
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    if 'background' not in st.session_state:
        st.session_state.background = list(BACKGROUND_IMAGES.values())[0]
    if 'ai_router_result' not in st.session_state:
        st.session_state.ai_router_result = None
    if 'contact_submissions' not in st.session_state:
        st.session_state.contact_submissions = deque(maxlen=500)  # prevent memory bloat

init_state()

# ---- CSS & Styles ----
def get_base_css():
    return f"""
    <style>
    /* Body & Background */
    .stApp {{
        background-image: url("{st.session_state.background}");
        background-size: cover;
        background-position: center center;
        background-attachment: fixed;
        color: {'#f9f9f9' if st.session_state.theme == 'dark' else '#111'};
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }}
    /* Overlay for readability */
    .background-overlay {{
        position: fixed;
        top:0; left:0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.55);
        z-index: -1;
    }}
    /* Glass cards */
    .glass-card {{
      background: {"rgba(20,24,28,0.85)" if st.session_state.theme == "dark" else "rgba(255,255,255,0.9)"};
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 12px 30px rgba(2,6,23,0.15);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: {"#eee" if st.session_state.theme == "dark" else "#222"};
      font-size: 16px;
    }}
    /* Headings */
    h1 {{
      font-size: 48px;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: {"#eef6ff" if st.session_state.theme == 'dark' else '#111'};
    }}
    h2 {{
      font-size: 38px;
      font-weight: 600;
      margin-bottom: 1rem;
      color: {"#eef6ff" if st.session_state.theme == 'dark' else '#111'};
    }}
    /* Buttons */
    button {{
      background: linear-gradient(135deg,#004174,#047860);
      color: white !important;
      font-weight: 700;
      border-radius: 14px;
      padding: 10px 22px;
      border: none;
      box-shadow: 0 6px 20px rgba(4,120,96,0.4);
      transition: background 0.3s ease;
      font-size: 16px;
    }}
    button:hover {{
      background: linear-gradient(135deg,#047860,#004174);
      cursor: pointer;
    }}
    /* Input text unique keys no spinner */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {{
      -webkit-appearance: none;
      margin: 0;
    }}
    input[type=number] {{
      -moz-appearance: textfield;
    }}
    /* Search bar */
    input.ai-search-bar {{
      border: 2px solid #05f7a7;
      border-radius: 24px;
      padding: 16px 44px 16px 20px;
      font-size: 20px;
      width: 100%;
      max-width: 700px;
      background-color: rgba(0,0,0,0.6);
      color: white;
      box-shadow: 0 0 20px #05f7a7;
      transition: border-color 0.3s ease;
    }}
    input.ai-search-bar::placeholder {{
      color: rgba(255,255,255,0.7);
    }}
    input.ai-search-bar:focus {{
      outline: none;
      border-color: #50fa7b;
      box-shadow: 0 0 30px #50fa7b;
      background-color: rgba(0,0,0,0.8);
    }}
    /* Tooltip: “?” with hover */
    .tooltip-icon {{
      position: relative;
      color: #4ade80;
      font-weight: 900;
      cursor: help;
      margin-left: 6px;
      font-size: 1rem;
    }}
    .tooltip-icon:hover::after {{
      content: attr(data-tip);
      position: absolute;
      left: 110%;
      top: 50%;
      transform: translateY(-50%);
      background: #222;
      color: #eee;
      padding: 8px 12px;
      border-radius: 8px;
      width: 240px;
      font-weight: 400;
      font-size: 0.85rem;
      z-index: 99999;
      white-space: normal;
      box-shadow: 0 0 11px rgba(0,255,128,0.65);
    }}
    /* AI Insight Card */
    .ai-insight-card {{
      background: rgba(8,17,38,0.95);
      color: #eef6ff;
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 0 12px rgba(0, 255, 128, 0.35);
      font-size: 16px;
      font-weight: 500;
      line-height: 1.4rem;
    }}
    /* Chart container */
    .chart-container {{
      background: {"rgba(20,24,28,0.85)" if st.session_state.theme == 'dark' else "rgba(255,255,255,0.9)"};
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 8px 20px rgba(2,6,23,0.12);
      margin-bottom: 1rem;
    }}
    /* Footer */
    footer {{
      color: {"#a0b0bf" if st.session_state.theme == 'dark' else "#666"};
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 1px solid {"rgba(255,255,255,0.1)" if st.session_state.theme == 'dark' else "rgba(0,0,0,0.1)"};
      font-size: 0.85rem;
      text-align: center;
    }}
    /* Error messages */
    div.stError {{
      font-weight: 600;
      color: #FF5370;
    }}
    </style>
    """

def apply_styles():
    st.markdown(get_base_css(), unsafe_allow_html=True)
    st.markdown('<div class="background-overlay"></div>', unsafe_allow_html=True)

# ---- Validation Helpers ----
def validate_float(text_val):
    try:
        if text_val is None or text_val.strip() == "":
            return None, None
        val = float(text_val.replace(",", "").replace(CURRENCY_SYMBOL, "").strip())
        return val, None
    except Exception:
        return None, "Invalid number format"

def validate_int(text_val):
    try:
        if text_val is None or text_val.strip() == "":
            return None, None
        val = int(text_val.strip())
        return val, None
    except Exception:
        return None, "Invalid integer format"

# ---- Unique Widget Key Generator helper ----
def make_key(*args):
    return "_".join(str(a).replace(" ", "_").lower() for a in args)

# ---- Tooltip HTML ----
def tooltip(text):
    return f'<span class="tooltip-icon" data-tip="{text}">?</span>'

# ---- Cache market data ----
@st.cache_data(ttl=900)
def fetch_market_data(tickers):
    if not YF_AVAILABLE:
        return None
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=365)
        data = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
        return data
    except Exception:
        return None

# ---- PDF generator skeleton ----
def generate_pdf(metadata: dict, advice: str, chart_png: bytes | None = None):
    if not FPDF_AVAILABLE:
        return None
    pdf = FPDF()
    pdf.add_page()
    # Header
    pdf.set_fill_color(2, 52, 74) # deep navy
    pdf.rect(0, 0, 210, 22, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, f"{APP_NAME} Financial Advisory Report", ln=True, align="C")

    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Input Summary", ln=True)

    pdf.set_font("Helvetica", "", 12)
    for k, v in metadata.items():
        val = str(v)
        # strip emojis, non-ASCII
        safe_val = val.encode("ascii", errors="ignore").decode()
        safe_key = k.encode("ascii", errors="ignore").decode()
        pdf.cell(50, 10, f"{safe_key}:", ln=0)
        pdf.cell(0, 10, safe_val, ln=1)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "AI Recommendations", ln=True)
    pdf.set_font("Helvetica", "", 12)
    for line in advice.splitlines():
        safe_line = line.encode("ascii", errors="ignore").decode()
        pdf.multi_cell(0, 8, safe_line)

    if chart_png:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                tmp.write(chart_png)
                tmp.flush()
                pdf.image(tmp.name, x=130, w=60)
        except Exception:
            pass
    
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f"© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.", 0, 0, 'C')

    return pdf.output(dest="S").encode("latin1")

# ---- Excel export skeleton ----
def generate_excel(metadata: dict, advice: str):
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_meta = pd.DataFrame(metadata.items(), columns=["Field", "Value"])
            df_adv = pd.DataFrame({"Advice": advice.splitlines()})

            df_meta.to_excel(writer, sheet_name="Inputs", index=False)
            df_adv.to_excel(writer, sheet_name="AI_Recommendations", index=False)

            workbook = writer.book
            format_header = workbook.add_format({'bold': True, 'bg_color': '#00334e', 'font_color': 'white'})
            worksheet = writer.sheets['Inputs']
            worksheet.set_row(0, None, format_header)
            worksheet = writer.sheets['AI_Recommendations']
            worksheet.set_row(0, None, format_header)
        return output.getvalue()
    except Exception:
        return None

# ---- AI Router (OpenAI + keyword fallback) ----
def ai_natural_language_router(query_text):
    """
    Uses OpenAI or fallback keyword mapping to route user's query to segment:module with confidence
    """
    if OPENAI_AVAILABLE and "OPENAI_API_KEY" in st.secrets:
        try:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            prompt = f"""
Given this free-text, map to one route:
{json.dumps(ROUTE_LIST)}

Return JSON: {{ "segment":..., "module":..., "confidence":... }}.
If uncertain, choose most likely with confidence < 0.6.

User query:
\"\"\"{query_text}\"\"\"

JSON reply:
"""
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0,
                stop=["\n\n"]
            )
            txt = response.choices[0].text.strip()
            parsed = json.loads(txt)
            segment = parsed.get("segment")
            module = parsed.get("module")
            confidence = float(parsed.get("confidence", 0))
            if (segment in ['individual', 'household', 'business']) and module and isinstance(confidence, float):
                return segment, module, confidence
        except Exception:
            pass

    # Keyword fallback:
    l = query_text.lower()
    mappings = {
        "small company": ("business", "tax"),
        "pay less tax": ("business", "tax"),
        "save for retirement": ("individual", "retirement"),
        "retirement": ("individual", "retirement"),
        "kids": ("household", "tax"),
        "family budget": ("household", "tax"),
        "best etfs": ("individual", "investment"),
        "etfs": ("individual", "investment"),
        "cash flow": ("business", "cashflow"),
        "valuation": ("business", "valuation"),
    }
    for key, val in mappings.items():
        if key in l:
            return val[0], val[1], 0.7
    # Default fallback
    return "individual", "investment", 0.5

# ---- Helper: format Rands ----
def fmt_currency(val):
    try:
        v = float(val)
        return f"R{v:,.2f}"
    except Exception:
        return "R0.00"

# === PAGE COMPONENTS ===

def page_privacy_gate():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.title("OptiFin Privacy, Data Processing, and Electronic Communications Agreement")
    st.markdown(f"**Last updated: {date.today().isoformat()}**")
    agreement = """
You authorize OptiFin to collect, process, analyze, store, and display the data you enter into this application, including financial, demographic, and business information, for the purpose of providing personalized analyses, projections, reports, and recommendations.

Your data may be processed by third-party sub-processors strictly for functionality (e.g., secure hosting, analytics, AI inference, document generation, market data retrieval). OptiFin contracts to ensure commercially reasonable safeguards.

OptiFin implements measures designed to protect your information (encryption in transit, logical access controls, monitoring). No method of transmission or storage is 100% secure.

Reports and recommendations provided by OptiFin are general informational insights and do not constitute financial, tax, accounting, legal, or investment advice. You remain solely responsible for decisions and compliance.

You consent to receive electronic communications and to the electronic provision of notices and records.

You may request deletion of your information subject to legal and operational constraints.

By clicking “I Accept,” you provide a legally binding consent to this Agreement and the processing described herein. If you do not agree, do not use this application and select “Decline” to exit.
"""
    st.markdown(f"<pre style='color:white; white-space: pre-wrap'>{agreement}</pre>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Decline", key="privacy_decline_btn"):
            st.markdown("<script>window.location.href = 'https://your-site.example/';</script>", unsafe_allow_html=True)
            st.stop()
    with col2:
        if st.button("I Accept", key="privacy_accept_btn"):
            st.session_state.consent_accepted = True
            st.session_state.page = "home"
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def page_home():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.title("Welcome to OptiFin")
    st.markdown("Describe your situation or goals in your own words:")

    ai_input_key = "home_ai_input_text"
    user_input = st.text_input(
        "Describe your situation or goals...",
        key=ai_input_key,
        placeholder="Describe your situation or goals in your own words…",
        label_visibility='collapsed',
        max_chars=500,
        on_change=None,
    )
    submit_key = "home_ai_search_btn"
    col_left, col_right = st.columns([0.3, 0.7])
    with col_left:
        if st.button("Analyze", key=submit_key):
            if not user_input or len(user_input.strip()) < 8:
                st.error("Please enter a detailed description for better advice.")
            else:
                segment, module, confidence = ai_natural_language_router(user_input.strip())
                st.session_state.ai_router_result = {"segment": segment, "module": module, "confidence": confidence}
                st.session_state.user_segment = segment
                st.session_state.sub_module = module
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
    with col_right:
        st.markdown("### Or choose your segment:")
        seg_cols = st.columns(3)
        with seg_cols[0]:
            if st.button("Individual", key="segment_individual_btn"):
                st.session_state.user_segment = "individual"
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
        with seg_cols[1]:
            if st.button("Household", key="segment_household_btn"):
                st.session_state.user_segment = "household"
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
        with seg_cols[2]:
            if st.button("Business", key="segment_business_btn"):
                st.session_state.user_segment = "business"
                st.session_state.page = "segment_hub"
                st.experimental_rerun()

    # Show chip for AI router understanding if available
    if st.session_state.ai_router_result:
        r = st.session_state.ai_router_result
        st.markdown(f"<small style='color:#4ade80;'>Understanding you → <b>{r['segment'].capitalize()} : {r['module'].capitalize()}</b> (confidence: {r['confidence']:.2f})</small>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def page_segment_hub():
    seg = st.session_state.user_segment or "individual"
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.title(f"{seg.capitalize()} Segment Hub")
    st.markdown("Select a focus area:")

    modules_for_segment = {
        "individual": {
            "investment": ("Investment Planning", "6 questions"),
            "tax": ("Tax Optimization", "5 questions"),
            "retirement": ("Retirement & Goal Planning", "6 questions"),
            "estate": ("Estate & Protection", "4 questions"),
        },
        "household": {
            "budget": ("Budgeting & Expenses", "6 questions"),
            "tax": ("Tax Optimization", "5 questions"),
            "investment": ("Investment Planning", "6 questions"),
            "protection": ("Insurance & Protection", "4 questions"),
        },
        "business": {
            "tax": ("Tax Optimization", "7 questions"),
            "investment": ("Investment Planning", "6 questions"),
            "cashflow": ("Cash Flow Forecasting", "6 questions"),
            "retirement": ("Pension & Provident Funds", "6 questions"),
            "valuation": ("Business Valuation", "4 questions"),
        },
    }

    modules = modules_for_segment.get(seg, {})
    cols = st.columns(len(modules))
    for col, (mod_key, (mod_name, badge)) in zip(cols, modules.items()):
        with col:
            if st.button(f"{mod_name}\n({badge})", key=f"btn_{seg}_{mod_key}"):
                st.session_state.sub_module = mod_key
                st.session_state.page = "module_form"
                st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def input_number_with_validation(label:str, key:str, tooltip_text:str=None, unit:str=None, default:str=""):
    label_str = label
    if unit:
        label_str += f" ({unit})"
    label_html = label_str
    if tooltip_text:
        label_html += " " + tooltip(tooltip_text)
    raw_val = st.text_input(label_html, value=default, key=key)
    val, err = validate_float(raw_val)
    if err:
        st.error(err, icon="🚨")
    return val

def input_int_with_validation(label:str, key:str, tooltip_text:str=None, default:str=""):
    label_html = label
    if tooltip_text:
        label_html += " " + tooltip(tooltip_text)
    raw_val = st.text_input(label_html, value=default, key=key)
    val, err = validate_int(raw_val)
    if err:
        st.error(err, icon="🚨")
    return val

# ---- Individual Investment Module Example ----
def page_module_investment_individual():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Individual — Investment Planning")

    # Inputs per spec
    income = input_number_with_validation("Income (Annual)", "indiv_income_text", "Your pre-tax annual income. Example: 850,000.", "Annual")
    bonus = input_number_with_validation("Bonus Income (Annual)", "indiv_bonus_text", "Additional bonus income (annual). Optional.", "Annual", "0")
    other_income = input_number_with_validation("Other Income (Annual)", "indiv_other_income_text", "Other income sources (annual). Optional.", "Annual", "0")

    investable_assets = input_number_with_validation("Current Investable Assets (R)", "indiv_investable_text", "Cash and investments available to deploy.", "Total", "0")

    monthly_contrib = input_number_with_validation("Current Monthly Contribution (R)", "indiv_monthly_contrib_text", "Amount you currently invest monthly.", "Monthly", "0")

    debt_mortgage = input_number_with_validation("Mortgage Debt Balance (R)", "indiv_debt_mortgage", "Outstanding mortgage balance.", "Total", "0")

    debt_cards = input_number_with_validation("Credit Card Debt Balance (R)", "indiv_debt_cards", "Outstanding credit card balances.", "Total", "0")

    debt_loans = input_number_with_validation("Loans Debt Balance (R)", "indiv_debt_loans", "Outstanding loans (auto, personal).", "Total", "0")

    debt_rates = input_number_with_validation("Weighted Average Debt Interest Rate (%)", "indiv_debt_interest", "Average interest rate across debts, e.g., 10 for 10%.", "Percent", "0")

    risk_tolerance = st.slider("Risk Tolerance (Very Low → Very High)", min_value=1, max_value=5, value=3, key="indiv_risk_slider")

    retirement_age = input_int_with_validation("Target Retirement Age", "indiv_retirement_age", "Age you aim to retire.", "65")

    current_age = input_int_with_validation("Current Age", "indiv_current_age", "Your current age.", "35")

    tax_residence = st.selectbox("Tax Residency & Country", ["South Africa", "United Kingdom", "United States"], key="indiv_tax_residence")

    deductions_text = st.text_area("Current Deductions Claimed (list)", key="indiv_deductions", help="List your current deductions separated by commas, e.g., 'Section 12J, Medical Credits'", height=50)

    insurance_months = input_int_with_validation("Insurance & Emergency Fund Months", "indiv_insurance_months", "Number of months your insurance/emergency fund covers.", "6")

    retirement_target_corpus = input_number_with_validation("Retirement Target Corpus (R)", "indiv_retirement_target", "Target corpus you want at retirement.", "Total", "0")

    savings_timeframe_years = input_int_with_validation("Savings Timeframe (years)", "indiv_savings_timeframe", "Years available to save until retirement.", "30")

    savings_autoplan = st.checkbox("Enable Savings Auto Plan", value=True, key="indiv_savings_autoplan")

    # Validate mandatory fields & show friendly error messages
    errors = []
    if income is None:
        errors.append("Income (Annual) is required and must be a valid number.")
    if monthly_contrib is None:
        errors.append("Monthly Contribution is required and must be valid.")
    if retirement_age is None:
        errors.append("Retirement Age is required.")
    if current_age is None:
        errors.append("Current Age is required.")
    if savings_timeframe_years is None:
        errors.append("Savings Timeframe is required.")
    if retirement_target_corpus is None:
        errors.append("Retirement Target Corpus is required.")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    # --- Advisor Engine (simple deterministic example, replace with real logic) --
    # Calculate debt paydown timeline example
    total_debt = (debt_mortgage or 0) + (debt_cards or 0) + (debt_loans or 0)
    monthly_interest = ((debt_rates or 0) / 100) / 12
    try:
        debt_paydown_months = 0
        balance = total_debt
        monthly_payment = min(monthly_contrib or 0, balance) if balance > 0 else 0
        while balance > 0 and debt_paydown_months < 600:
            interest = balance * monthly_interest
            principal_payment = monthly_payment - interest
            balance -= principal_payment
            debt_paydown_months += 1
        if balance > 0:
            debt_paydown_months = None  # cannot pay off
    except Exception:
        debt_paydown_months = None

    # Project investment future value
    # (Simple CAGR annual return 7%, risk modifies return ±2% per risk slider)
    base_return = 0.07
    risk_adjustment = (risk_tolerance - 3) * 0.02
    annual_return = max(0.03, base_return + risk_adjustment)
    monthly_return = (1 + annual_return) ** (1/12) - 1
    months = (retirement_age - current_age) * 12
    bal = investable_assets or 0
    invest_eval = []
    for _ in range(months):
        bal = bal * (1 + monthly_return) + (monthly_contrib or 0)
        invest_eval.append(bal)

    # Compose AI insight text
    advice_lines = [
        f"Your estimated debt paydown time is {debt_paydown_months or 'more than 50 years'} months.",
        f"Based on your risk tolerance ({risk_tolerance}), expected annualized return is ~{annual_return*100:.1f}%.",
        f"Projected investment value at retirement age ({retirement_age}) is approximately R{bal:,.0f}.",
        "Consider rebalancing annually and consulting a financial advisor for tailored advice.",
        "All advice is general information and does not constitute formal financial, tax, legal, or investment consulting.",
        "Contact OptiFin for tailored implementation."
    ]
    advice_text = "\n".join(advice_lines)

    # -- Plot the investment projection as a sparkline --
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(invest_eval))), y=invest_eval,
                             mode='lines+markers',
                             line=dict(color='#50fa7b'),
                             marker=dict(size=4)))
    fig.update_layout(margin=dict(l=15, r=15, t=25, b=25),
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(20,24,28,0.85)' if st.session_state.theme == 'dark' else 'rgba(255,255,255,0.9)',
                      height=220,
                      font=dict(color='#eef6ff' if st.session_state.theme == 'dark' else '#111'),
                      xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                      yaxis=dict(showgrid=False, zeroline=False))
    
    left_col, right_col = st.columns([1.7, 1])
    with left_col:
        st.subheader("Investment Projection")
        st.plotly_chart(fig, use_container_width=True)
    with right_col:
        st.subheader("AI Insight")
        st.markdown(f"<div class='ai-insight-card'><pre style='white-space:pre-wrap'>{advice_text}</pre></div>", unsafe_allow_html=True)

    # --- Export buttons ---
    meta = {
        "Income (Annual)": fmt_currency(income),
        "Bonus Income": fmt_currency(bonus),
        "Other Income": fmt_currency(other_income),
        "Current Investable Assets": fmt_currency(investable_assets),
        "Monthly Contribution": fmt_currency(monthly_contrib),
        "Total Debt": fmt_currency(total_debt),
        "Debt Interest (%)": debt_rates or 0,
        "Risk Tolerance": risk_tolerance,
        "Retirement Age": retirement_age,
        "Current Age": current_age,
        "Tax Residence": tax_residence,
        "Insurance Months": insurance_months,
        "Retirement Target": fmt_currency(retirement_target_corpus),
        "Savings Timeframe (Years)": savings_timeframe_years,
        "Savings Auto Plan Enabled": savings_autoplan,
        "Deductions": deductions_text.strip() or "None",
    }

    # Generate PNG of chart for embedding in PDF (for complex real app, handle offline caching)
    chart_png = None
    try:
        img_bytes = fig.to_image(format="png", width=600, height=270, scale=2)
        chart_png = img_bytes
    except Exception:
        chart_png = None

    pdf_bytes = generate_pdf(meta, advice_text, chart_png)
    excel_bytes = generate_excel(meta, advice_text)

    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        if pdf_bytes:
            st.download_button("Download PDF Report",
                               data=pdf_bytes,
                               file_name=f"OptiFin_Individual_Investment_Report.pdf",
                               mime="application/pdf",
                               key="download_pdf_investment" )
        else:
            st.warning("PDF generation not available.")
    with exp_col2:
        if excel_bytes:
            st.download_button("Download Excel Report",
                               data=excel_bytes,
                               file_name=f"OptiFin_Individual_Investment_Report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="download_excel_investment")
        else:
            st.warning("Excel export not available.")

    # --- Contact & Lead Capture card ---
    st.markdown("---")
    st.subheader("Get a tailored implementation")
    with st.form("contact_form_investment", clear_on_submit=True):
        contact_name = st.text_input("Name", key="contact_invest_name")
        contact_email = st.text_input("Email", key="contact_invest_email")
        contact_phone = st.text_input("Phone", key="contact_invest_phone")
        contact_company = st.text_input("Company (optional)", key="contact_invest_company")
        if st.form_submit_button("Submit"):
            if not contact_name or not contact_email:
                st.error("Name and Email are required.")
            else:
                # Save to session_state for demo, in prod store securely
                st.session_state.contact_submissions.append({
                    "name": contact_name,
                    "email": contact_email,
                    "phone": contact_phone,
                    "company": contact_company,
                    "segment": "Individual",
                    "module": "Investment",
                    "timestamp": datetime.now().isoformat(),
                })
                st.success("Thank you for your submission! Our team will contact you soon.")
    st.markdown(f"<small style='color:gray'>We respect your privacy. See OptiFin Privacy Agreement on app start.</small>", unsafe_allow_html=True)

    # --- Back to hub ---
    if st.button("Back to Segment Hub", key="btn_back_segment_hub_invest"):
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- Map (segment, sub_module) to page functions ---
PAGE_FUNCTIONS = {
    ("individual", "investment"): page_module_investment_individual,
    # Fill in others (household, business, tax, retirement, estate, etc.) in Parts 2/3
}

def main_router():
    apply_styles()
    if not st.session_state.consent_accepted:
        st.session_state.page = "privacy_gate"

    page = st.session_state.page

    # Sidebar theme and background selector
    with st.sidebar:
        st.title(APP_NAME)
        theme_selection = st.radio("Color Theme", options=['dark', 'light'], index=0 if st.session_state.theme=="dark" else 1, key="theme_radio", horizontal=True)
        if theme_selection != st.session_state.theme:
            st.session_state.theme = theme_selection
            st.experimental_rerun()

        # Background selection dropdown
        bg_select = st.selectbox("Background Image", options=list(BACKGROUND_IMAGES.keys()), key="background_select")
        selected_url = BACKGROUND_IMAGES.get(bg_select, list(BACKGROUND_IMAGES.values())[0])
        if st.session_state.background != selected_url:
            st.session_state.background = selected_url
            st.experimental_rerun()

        st.markdown("---")
        st.markdown(f"© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.")

    if page == "privacy_gate":
        page_privacy_gate()
    elif page == "home":
        page_home()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        seg = st.session_state.user_segment
        mod = st.session_state.sub_module
        fn = PAGE_FUNCTIONS.get((seg, mod), None)
        if fn:
            fn()
        else:
            st.error(f"Module not implemented for {seg} -> {mod}.")
            if st.button("Back to Segment Hub"):
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
    else:
        st.error("Unknown app page, redirecting home...")
        st.session_state.page = "home"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    main_router()
# CONTINUE app.py - OptiFin Intelligent Financial Planning Suite - Part 2 of 3

import math

# ------------ UTILITIES & VALIDATIONS (expand) ------------

def validate_float_required(text_val, field_name):
    v, err = validate_float(text_val)
    if err or v is None:
        st.error(f"{field_name} is required and must be a valid number.")
        raise ValueError(f"{field_name} validation failed")
    return v

def validate_int_required(text_val, field_name):
    v, err = validate_int(text_val)
    if err or v is None:
        st.error(f"{field_name} is required and must be a valid integer.")
        raise ValueError(f"{field_name} validation failed")
    return v

# ------------ Advisor deterministic engine stubs ------------

def compute_tax_estimate(annual_income, deductions, dependants, country):
    """
    Highly simplified demo tax estimator by region.
    Input values:
    - annual_income, deductions: float
    - dependants: int
    Output:
    - dict { 'taxable_income': ..., 'estimated_tax': ..., 'tax_rate': ... }
    """
    taxable = max(0, annual_income - deductions - dependants * 3500)
    if country == "South Africa":
        if taxable < 50000:
            rate = 0.18
        elif taxable < 150000:
            rate = 0.26
        else:
            rate = 0.39
    elif country == "United Kingdom":
        if taxable < 12500:
            rate = 0.0
        elif taxable < 50000:
            rate = 0.20
        elif taxable < 150000:
            rate = 0.40
        else:
            rate = 0.45
    elif country == "United States":
        # Flat demo rate
        rate = 0.22
    else:
        rate = 0.25  # default fallback
    est_tax = taxable * rate
    return {
        "taxable_income": taxable,
        "estimated_tax": est_tax,
        "tax_rate": rate
    }

def compute_retirement_shortfall(current_assets, monthly_contrib, years_to_retire, risk_level, target_corpus):
    """
    Estimate retirement shortfall with simple CAGR growth.
    risk_level: 1-5 slider, translates to base returns.
    Returns shortfall amount and projection series (monthly).
    """
    base_returns = {
        1: 0.03,
        2: 0.05,
        3: 0.07,
        4: 0.10,
        5: 0.12,
    }
    ann_return = base_returns.get(risk_level, 0.07)
    monthly_return = (1 + ann_return) ** (1/12) - 1
    months = years_to_retire * 12
    bal = current_assets
    proj_series = []
    for _ in range(months):
        bal = bal * (1 + monthly_return) + monthly_contrib
        proj_series.append(bal)
    shortfall = max(0, target_corpus - bal)
    return shortfall, proj_series

# ------------ Market Data -----------------------

@st.cache_data(ttl=900)
def get_ticker_history(ticker:str, period='1y'):
    if not YF_AVAILABLE:
        return None
    try:
        data = yf.Ticker(ticker).history(period=period)
        return data['Close']
    except Exception:
        return None

# ------------ Helper to display chart + AI Insight card ------------

def display_compact_chart_and_insight(series, heading, advice, theme='dark'):
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=series, mode='lines+markers',
                             line=dict(color='#50fa7b'),
                             marker=dict(size=4)))
    fig.update_layout(
        margin=dict(l=15, r=15, t=25, b=25),
        height=220,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(20,24,28,0.85)' if theme == 'dark' else 'rgba(255,255,255,0.9)',
        font=dict(color='#eef6ff' if theme == "dark" else '#111'),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False))
    cols = st.columns([1.7, 1])
    with cols[0]:
        st.subheader(heading)
        st.plotly_chart(fig, use_container_width=True)
    with cols[1]:
        st.subheader("AI Insight")
        st.markdown(f"<div class='ai-insight-card'><pre style='white-space:pre-wrap'>{advice}</pre></div>", unsafe_allow_html=True)

# -------- Household Investment Module -------------

def page_module_investment_household():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Household — Investment Planning")

    try:
        combined_income = validate_float_required(
            st.text_input(f"Combined Household Income (Annual) {tooltip('Your household\'s total pre-tax income. Example: 1,200,000')}",
                          key="household_income_text"), "Combined Household Income")

        dependants = validate_int_required(
            st.text_input(f"Dependants (#) {tooltip('Number of financially dependent people (children, parents).')}",
                          key="household_dependants_text"), "Dependants")

        current_deductions = st.text_area(
            f"Current Deductions/Credits Claimed {tooltip('List deductions or credits claimed, comma-separated.')}",
            key="household_deductions_text")

        monthly_budget = st.text_area(
            f"Monthly Budget (categories) {tooltip('List budget categories and amounts, comma-separated - e.g., Food:1000, Transport:500')}",
            key="household_budget_text")

        goal_education = validate_float(
            st.text_input(f"Goal: Education Fund (R) {tooltip('Amount you want saved for education, annualized.')}",
                          key="household_goal_education_text")) or 0.0

        goal_home = validate_float(
            st.text_input(f"Goal: Home Purchase Fund (R) {tooltip('Target amount for home purchase.')}",
                          key="household_goal_home_text")) or 0.0

        goal_retirement = validate_float(
            st.text_input(f"Goal: Retirement Corpus (R) {tooltip('Amount targeted at retirement.')}",
                          key="household_goal_retirement_text")) or 0.0

        risk = st.slider("Risk Tolerance", min_value=1, max_value=5, value=3, key="household_risk_slider")

        investable_assets = validate_float(
            st.text_input(f"Current Investable Assets (R) {tooltip('Cash and investments available to deploy.')}",
                          key="household_investable_text")) or 0.0

        if combined_income <= 0:
            st.error("Combined household income must be positive.")
            st.stop()

        monthly_contrib = combined_income / 12 * 0.2  # naive 20% savings heuristic

        # Simple investment projection like individual module:
        base_return = 0.07
        risk_adj = (risk - 3) * 0.02
        ann_return = max(0.03, base_return + risk_adj)
        monthly_return = (1 + ann_return) ** (1/12) - 1
        months = 12
        bal = investable_assets
        projection = []
        for _ in range(months):
            bal = bal * (1 + monthly_return) + monthly_contrib
            projection.append(bal)

        advice_lines = [
            f"Risk profile: {risk} (scale 1-5).",
            f"Estimated 12 month projected investment value: {fmt_currency(bal)}.",
            "Suggested allocation: Core ETF 60%, Satellite thematic 30%, Bonds 10%.",
            "Adjust contributions or goals based on personal circumstances.",
            "Consult a professional for personalized advice.",
        ]
        advice = "\n".join(advice_lines)

        display_compact_chart_and_insight(projection, "12-Month Investment Projection", advice, st.session_state.theme)

        st.markdown("---")
        st.subheader("Get a tailored implementation")
        with st.form("contact_form_household", clear_on_submit=True):
            name = st.text_input("Name", key="contact_household_name")
            email = st.text_input("Email", key="contact_household_email")
            phone = st.text_input("Phone", key="contact_household_phone")
            company = st.text_input("Company (optional)", key="contact_household_company")
            if st.form_submit_button("Submit"):
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    st.session_state.contact_submissions.append({
                        "name": name, "email": email, "phone": phone,
                        "company": company, "segment": "Household",
                        "module": "Investment", "timestamp": datetime.now().isoformat()
                    })
                    st.success("Thank you for your submission! We will contact you soon.")

        if st.button("Back to Segment Hub", key="btn_back_household_invest"):
            st.session_state.page = "segment_hub"
            st.experimental_rerun()

    except Exception as ex:
        st.error(f"Error: {str(ex)}")

    st.markdown('</div>', unsafe_allow_html=True)

# -------- Business Investment Module -------------

def page_module_investment_business():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Business — Investment Planning")

    try:
        ann_revenue = validate_float_required(st.text_input(
            "Annual Revenue (R)"+tooltip("Total revenue for your business this year."), key="business_annual_revenue"), "Annual Revenue")

        cogs = validate_float(st.text_input(
            "COGS (Cost of Goods Sold) (R)"+tooltip("Direct costs of producing goods sold."), key="business_cogs")) or 0.0

        opex = validate_float(st.text_input(
            "Operating Expenses (OpEx) (R)"+tooltip("General operating expenses."), key="business_opex")) or 0.0

        ebitda = ann_revenue - cogs - opex

        owner_salary = validate_float(st.text_input(
            "Owner Salary (R)"+tooltip("Salary paid to owners."), key="business_owner_salary")) or 0.0

        distributions = validate_float(st.text_input(
            "Distributions/Dividends (R)"+tooltip("Payments to owners beyond salary."), key="business_distributions")) or 0.0

        employees = validate_int_required(st.text_input(
            "Number of Employees"+tooltip("Number of full-time employees."), key="business_employees"), "Number of Employees")

        payroll = validate_float(st.text_input(
            "Payroll Spend (R)"+tooltip("Total monthly payroll spend."), key="business_payroll_spend")) or 0.0

        deductions_claimed = st.text_area("Current deductions claimed", key="business_deductions_claimed")

        capex = validate_float(st.text_input(
            "Capital Expenditure (CapEx) This Year (R)"+tooltip("Equipment, vehicles, property improvements."), key="business_capex")) or 0.0

        vat_status = st.selectbox("VAT Status", options=["Registered", "Not Registered"], key="business_vat_status")
        corp_tax_regime = st.selectbox("Corporate Tax Regime", options=["Standard", "Small Business", "Other"], key="business_corp_tax_regime")

        cash_on_hand = validate_float(st.text_input("Cash on Hand (R)", key="business_cash_on_hand")) or 0.0

        runway_months = validate_int_required(st.text_input("Runway Months", key="business_runway_months"), "Runway Months")

        # Simple cash runway check
        est_monthly_burn = (opex + payroll) / 12 if opex > 0 and payroll > 0 else 0
        runway_calc = cash_on_hand / est_monthly_burn if est_monthly_burn > 0 else math.inf

        advice_lines = [
            f"EBITDA is estimated at {fmt_currency(ebitda)}.",
            f"Estimated monthly burn rate: {fmt_currency(est_monthly_burn)}.",
            f"Cash runway based on cash on hand and burn rate: approximately {runway_calc:.1f} months.",
            "Consider optimizing distributions vs salary for tax efficiency.",
            "Make use of accelerated depreciation and R&D credits if available.",
            "Consult your financial advisor for detailed tax optimization.",
        ]
        advice = "\n".join(advice_lines)

        # Investment projection dummy example (similar to others)
        monthly_investment = ann_revenue * 0.05 / 12  # invest 5% annual revenue monthly
        risk = 3  # Default risk rating for business investment
        base_return = 0.07
        risk_adj = (risk - 3) * 0.02
        ann_return = max(0.03, base_return + risk_adj)
        monthly_return = (1 + ann_return) ** (1/12) - 1
        months = 12
        bal = 0 + (monthly_investment * 2)  # start with some buffer
        projection = []
        for _ in range(months):
            bal = bal * (1 + monthly_return) + monthly_investment
            projection.append(bal)

        display_compact_chart_and_insight(projection, "12-Month Investment Projection", advice, st.session_state.theme)

        st.markdown("---")
        st.subheader("Get a tailored implementation")
        with st.form("contact_form_business", clear_on_submit=True):
            name = st.text_input("Name", key="contact_business_name")
            email = st.text_input("Email", key="contact_business_email")
            phone = st.text_input("Phone", key="contact_business_phone")
            company = st.text_input("Company (optional)", key="contact_business_company")
            if st.form_submit_button("Submit"):
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    st.session_state.contact_submissions.append({
                        "name": name, "email": email, "phone": phone,
                        "company": company, "segment": "Business",
                        "module": "Investment", "timestamp": datetime.now().isoformat()
                    })
                    st.success("Thank you for your submission! We will contact you soon.")

        if st.button("Back to Segment Hub", key="btn_back_business_invest"):
            st.session_state.page = "segment_hub"
            st.experimental_rerun()

    except Exception as ex:
        st.error(f"Error in Business Investment module: {str(ex)}")

    st.markdown('</div>', unsafe_allow_html=True)

# -------- Tax Optimization Module (shared style for all segments) ---------

def page_module_tax():
    seg = st.session_state.user_segment
    mod = "tax"
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header(f"{seg.capitalize()} — Tax Optimization")

    try:
        annual_income = validate_float_required(
            st.text_input(f"Annual Taxable Income (R) {tooltip('Your annual taxable income.')}", key=f"{seg}_tax_annual_income_text"),
            "Annual Taxable Income")
        known_deductions = validate_float(
            st.text_input(f"Known Deductions (R) {tooltip('Enter claimed tax deductions.')}", key=f"{seg}_tax_deductions_text")
        ) or 0.0
        dependants = validate_int(
            st.text_input(f"Dependants (#) {tooltip('Number of dependants for tax credits.')}", key=f"{seg}_tax_dependants_text")
        ) or 0
        tax_country = st.selectbox("Tax Residency Country", options=["South Africa", "United Kingdom", "United States"], key=f"{seg}_tax_country_select")

        tax_data = compute_tax_estimate(annual_income, known_deductions, dependants, tax_country)

        est_tax = tax_data['estimated_tax']
        tax_rate = tax_data['tax_rate']
        taxable_income = tax_data['taxable_income']

        advice_lines = [
            f"Estimated taxable income: {fmt_currency(taxable_income)}.",
            f"Estimated tax owed: {fmt_currency(est_tax)} at effective rate {tax_rate*100:.1f}%.",
            "Maximize pre-tax retirement contributions to reduce taxable income.",
            "Claim all eligible dependants and education credits applicable to your jurisdiction.",
            "Consider salary vs dividends mix if applicable for tax efficiency.",
            "Consult a tax professional for detailed advice.",
        ]
        advice = "\n".join(advice_lines)

        display_compact_chart_and_insight([est_tax]*12, "Estimated Monthly Tax Liability", advice, st.session_state.theme)

        # Contact form here again
        st.markdown("---")
        st.subheader("Get a tailored tax optimization plan")
        with st.form(f"contact_form_tax_{seg}", clear_on_submit=True):
            name = st.text_input("Name", key=f"contact_tax_{seg}_name")
            email = st.text_input("Email", key=f"contact_tax_{seg}_email")
            phone = st.text_input("Phone", key=f"contact_tax_{seg}_phone")
            company = st.text_input("Company (optional)", key=f"contact_tax_{seg}_company")
            if st.form_submit_button("Submit"):
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    st.session_state.contact_submissions.append({
                        "name": name, "email": email, "phone": phone,
                        "company": company, "segment": seg.capitalize(),
                        "module": "Tax Optimization", "timestamp": datetime.now().isoformat()
                    })
                    st.success("Thank you for your submission! Our tax experts will get in touch.")

        if st.button("Back to Segment Hub", key=f"btn_back_tax_{seg}"):
            st.session_state.page = "segment_hub"
            st.experimental_rerun()

    except Exception as e:
        st.error(f"Error in Tax module: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# -------- Retirement & Goal Planning Module ---------

def page_module_retirement():
    seg = st.session_state.user_segment
    mod = "retirement"
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header(f"{seg.capitalize()} — Retirement & Goal Planning")

    try:
        current_assets = validate_float_required(st.text_input(
            f"Current Investable Assets (R) {tooltip('Total current savings and investments.')}",
            key=f"{seg}_ret_assets_text"), "Current Investable Assets")

        monthly_contribution = validate_float_required(st.text_input(
            f"Monthly Contribution (R) {tooltip('Amount saved towards retirement monthly.')}",
            key=f"{seg}_ret_monthly_contrib_text"), "Monthly Contribution")

        years_to_retire = validate_int_required(st.text_input(
            f"Years Until Retirement {tooltip('Number of years until retirement goal.')}",
            key=f"{seg}_ret_years_text"), "Years Until Retirement")

        target_corpus = validate_float_required(st.text_input(
            "Retirement Target Corpus (R)"+tooltip("Amount desired at retirement."),
            key=f"{seg}_ret_target_corpus_text"), "Retirement Target Corpus")

        risk = st.slider(f"Risk Tolerance", min_value=1, max_value=5, value=3, key=f"{seg}_ret_risk_slider")

        if monthly_contribution <= 0:
            st.info("You are not currently saving towards retirement; consider increasing monthly contributions.")
            st.stop()

        # Compute projection and shortfall with helper
        shortfall, proj_series = compute_retirement_shortfall(current_assets, monthly_contribution, years_to_retire, risk, target_corpus)

        advice_lines = [
            f"Projected retirement savings after {years_to_retire} years: {fmt_currency(proj_series[-1])}.",
            f"Retirement shortfall (difference from target): {fmt_currency(shortfall)}.",
            "Consider increasing contributions or extending your timeframe to close the gap.",
            "Maintain consistent investment and rebalance portfolio annually.",
            "For personalized retirement planning, please consult a financial advisor.",
        ]
        advice = "\n".join(advice_lines)

        display_compact_chart_and_insight(proj_series[-36:], "Last 36 Months Projection", advice, st.session_state.theme)

        st.markdown("---")
        st.subheader("Get a tailored retirement plan")
        with st.form(f"contact_form_retirement_{seg}", clear_on_submit=True):
            name = st.text_input("Name", key=f"contact_retirement_{seg}_name")
            email = st.text_input("Email", key=f"contact_retirement_{seg}_email")
            phone = st.text_input("Phone", key=f"contact_retirement_{seg}_phone")
            company = st.text_input("Company (optional)", key=f"contact_retirement_{seg}_company")
            if st.form_submit_button("Submit"):
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    st.session_state.contact_submissions.append({
                        "name": name, "email": email, "phone": phone,
                        "company": company, "segment": seg.capitalize(),
                        "module": "Retirement Planning", "timestamp": datetime.now().isoformat()
                    })
                    st.success("Thank you! A retirement expert will contact you.")

        if st.button("Back to Segment Hub", key=f"btn_back_retirement_{seg}"):
            st.session_state.page = "segment_hub"
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Error in Retirement module: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)


# ---- Extend PAGE_FUNCTIONS dictionary from Part 1 for these modules ----

PAGE_FUNCTIONS.update({
    ("household", "investment"): page_module_investment_household,
    ("business", "investment"): page_module_investment_business,
    ("individual", "tax"): page_module_tax,
    ("household", "tax"): page_module_tax,
    ("business", "tax"): page_module_tax,
    ("individual", "retirement"): page_module_retirement,
    ("household", "retirement"): page_module_retirement,
    ("business", "retirement"): page_module_retirement,
})


# END OF PART 2
# CONTINUATION app.py - OptiFin Intelligent Financial Planning Suite - Part 3 of 3

import csv
import os
from PIL import Image
import tempfile

# ---- Estate & Protection Module -----

def page_module_estate():
    seg = st.session_state.user_segment
    mod = "estate"
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header(f"{seg.capitalize()} — Estate & Protection")

    try:
        estate_value = validate_float_required(st.text_input(
            "Current Estate Value (R)"+tooltip("Total value of your estate assets."), key=f"{seg}_estate_value_text"), "Estate Value")

        will_exists = st.radio("Do you have a valid Will?", options=["Yes", "No"], key=f"{seg}_estate_will_radio")

        trust_fund = st.radio("Do you have a trust fund established?", options=["Yes", "No"], key=f"{seg}_estate_trust_radio")

        dependants_protected = validate_int_required(st.text_input(
            "Number of Protected Dependants", key=f"{seg}_estate_dependants_text", help="Number of family members covered under protection."), "Protected Dependants")

        insurance_coverage = validate_float_required(st.text_input(
            "Total Insurance Coverage (R)", key=f"{seg}_estate_insurance_coverage", help="Value of all insurance policies related to estate."), "Insurance Coverage")

        advice_lines = [
            f"Estate value: {fmt_currency(estate_value)}.",
            f"Will status: {will_exists}.",
            f"Trust fund established: {trust_fund}.",
            f"Dependants protected: {dependants_protected}.",
            f"Insurance coverage total: {fmt_currency(insurance_coverage)}.",
            "Ensure your will and trust fund are up to date.",
            "Consider insurance policies tailored to your estate size and dependants.",
            "Consult a legal advisor for comprehensive estate planning."
        ]
        advice = "\n".join(advice_lines)

        # Simple chart: estate value over last 12 months (mocked)
        fake_series = [estate_value * (1 + 0.003 * i) for i in range(12)]
        display_compact_chart_and_insight(fake_series, "Estate Value Projection", advice, st.session_state.theme)

        st.markdown("---")
        st.subheader("Get a tailored estate & protection plan")
        with st.form(f"contact_form_estate_{seg}", clear_on_submit=True):
            name = st.text_input("Name", key=f"contact_estate_{seg}_name")
            email = st.text_input("Email", key=f"contact_estate_{seg}_email")
            phone = st.text_input("Phone", key=f"contact_estate_{seg}_phone")
            company = st.text_input("Company (optional)", key=f"contact_estate_{seg}_company")
            if st.form_submit_button("Submit"):
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    st.session_state.contact_submissions.append({
                        "name": name, "email": email, "phone": phone,
                        "company": company, "segment": seg.capitalize(),
                        "module": "Estate & Protection", "timestamp": datetime.now().isoformat()
                    })
                    st.success("Thank you! An estate specialist will be in touch.")

        if st.button("Back to Segment Hub", key=f"btn_back_estate_{seg}"):
            st.session_state.page = "segment_hub"
            st.experimental_rerun()

    except Exception as ex:
        st.error(f"Error in Estate module: {str(ex)}")

    st.markdown('</div>', unsafe_allow_html=True)

# ---- Advisor Engine -- LLM invocation + fallback with banner -----

def get_ai_advice(segment: str, module: str, inputs: dict, computed_metrics: dict):
    """
    Compose prompt and call OpenAI API if available.
    Returns advice string.
    On AI failure or missing key, returns deterministic advice with banner.
    """

    prompt_intro = f"""You are an expert financial advisor for the region '{DEFAULT_REGION}'. Given the user inputs and computed metrics below, provide 3–6 specific, region-aware actions with estimated impact ranges. Do NOT give step-by-step instructions, but include legal disclaimers and call-to-action CTA to contact OptiFin.

User segment: {segment}
Module: {module}

Inputs:
{json.dumps(inputs, indent=2)}

Computed metrics:
{json.dumps(computed_metrics, indent=2)}

Response:
"""

    if OPENAI_AVAILABLE and "OPENAI_API_KEY" in st.secrets:
        try:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt_intro,
                max_tokens=400,
                temperature=0.2,
                stop=None,
            )
            advice = response.choices[0].text.strip()
            return advice, False  # No fallback banner
        except Exception:
            pass

    # fallback deterministic advice example
    fallback_advice = f"""Advanced AI temporarily offline. Based on inputs and metrics:

- Review your debt repayment strategy focusing on highest interest rates first.
- Maximize retirement and investment contributions within legal limits.
- Monitor your tax deductions, including dependants and insurance credits.
- Consult OptiFin for a tailored plan and professional financial advice.

[Disclaimer: This is general guidance, not personalized advice.]"""

    return fallback_advice, True

# ---- Extended Investment Module example with AI advice call ----

def page_module_investment_with_ai():
    """
    More detailed Investment page incorporating AI advice
    """
    seg = st.session_state.user_segment
    mod = "investment"

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header(f"{seg.capitalize()} — Investment Planning")

    # Example inputs (simplified here to demo AI)
    income = validate_float_required(st.text_input("Income (Annual)"+tooltip("Your pre-tax annual income. Example: 850,000."), key=f"{seg}_income_text"), "Income (Annual)")
    monthly_contrib = validate_float_required(st.text_input("Monthly Contribution (R)"+tooltip("Your monthly investment contribution."), key=f"{seg}_monthly_contrib_text"), "Monthly Contribution")
    risk = st.slider("Risk Tolerance", 1, 5, 3, key=f"{seg}_risk_slider")

    # Computed metrics placeholder
    computed = {
        "estimate_annual_return": 0.07 + 0.02*(risk-3),
        "projected_12m_value": monthly_contrib * 12 * (1 + 0.07)  # simple projection
    }

    # Prepare inputs for AI
    inputs = {
        "income_annual": income,
        "monthly_contribution": monthly_contrib,
        "risk_tolerance": risk,
    }

    advice_text, is_fallback = get_ai_advice(seg, mod, inputs, computed)

    if is_fallback:
        st.warning("Advanced AI is temporarily offline. Showing deterministic fallback advice", icon="⚠️")

    # Display advice panel
    st.markdown(f"<div class='ai-insight-card'><pre style='white-space:pre-wrap'>{advice_text}</pre></div>", unsafe_allow_html=True)

    # Back button
    if st.button("Back to Segment Hub", key="btn_back_invest_ai"):
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ---- Contact & Lead Capture Export to CSV ----

CONTACTS_CSV = "contact_submissions.csv"

def save_contacts_to_csv():
    """
    On each submission, append contact data to CSV to persist data.
    Assumes local write permission.
    """
    if not st.session_state.contact_submissions:
        return
    file_exists = pathlib.Path(CONTACTS_CSV).exists()
    with open(CONTACTS_CSV, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'segment', 'module', 'name', 'email', 'phone', 'company']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for c in st.session_state.contact_submissions:
            writer.writerow({
                "timestamp": c.get("timestamp"),
                "segment": c.get("segment"),
                "module": c.get("module"),
                "name": c.get("name"),
                "email": c.get("email"),
                "phone": c.get("phone"),
                "company": c.get("company"),
            })
    # clear session state to avoid duplicates
    st.session_state.contact_submissions.clear()

# ---- Override PAGE_FUNCTIONS ----
PAGE_FUNCTIONS.update({
    ("individual", "estate"): page_module_estate,
    ("household", "estate"): page_module_estate,
    ("business", "estate"): page_module_estate,
    ("individual", "investment"): page_module_investment_with_ai,  # AI advice enabled
    ("household", "investment"): page_module_investment_household,
    ("business", "investment"): page_module_investment_business,
})

# ---- Accessibility: submit AI Search on Enter key ---

def ai_search_input():
    """
    Render AI search bar with glowing border, submit on Enter, accessible.
    """
    placeholder = "Describe your situation or goals in your own words…"
    search_key = "home_ai_input_text"
    user_input = st.text_input(
        "",
        key=search_key,
        placeholder=placeholder,
        label_visibility='collapsed',
        max_chars=500,
        help="Type your financial goals or questions here and submit with Enter or Analyze button.",
        args=None,
    )
    analyze_key = "home_ai_analyze_btn"

    # Since Streamlit no native keypress, small trick: Analyze button next to search box.

    cols = st.columns([0.85, 0.15])
    with cols[0]:
        st.text_input(
            "",
            key=f"{search_key}_dummy",
            value=user_input,
            label="(hidden)",
            label_visibility='collapsed',
        )
    with cols[1]:
        if st.button("Analyze", key=analyze_key):
            if user_input and len(user_input.strip()) >= 8:
                segment, module, confidence = ai_natural_language_router(user_input.strip())
                st.session_state.ai_router_result = {"segment": segment, "module": module, "confidence": confidence}
                st.session_state.user_segment = segment
                st.session_state.sub_module = module
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
            else:
                st.error("Please enter a more detailed description for better advice.")

# ---- Footer ---
def render_footer():
    st.markdown(f"""
    <footer>
    © {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.
    </footer>
    """, unsafe_allow_html=True)

# --- Final Main Router override to save contacts on app exit ---

def main_router_final():
    apply_styles()

    # Persist contacts to CSV on app exit
    st.experimental_set_query_params()  # trigger rerun on param change

    if not st.session_state.consent_accepted:
        st.session_state.page = "privacy_gate"

    page = st.session_state.page

    with st.sidebar:
        st.title(APP_NAME)
        theme_selection = st.radio("Color Theme", options=['dark', 'light'], index=0 if st.session_state.theme=="dark" else 1, key="theme_radio", horizontal=True)
        if theme_selection != st.session_state.theme:
            st.session_state.theme = theme_selection
            st.experimental_rerun()

        bg_select = st.selectbox("Background Image", options=list(BACKGROUND_IMAGES.keys()), key="background_select")
        selected_url = BACKGROUND_IMAGES.get(bg_select, list(BACKGROUND_IMAGES.values())[0])
        if st.session_state.background != selected_url:
            st.session_state.background = selected_url
            st.experimental_rerun()

        st.markdown("---")
        st.markdown(f"© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.")

    if page == "privacy_gate":
        page_privacy_gate()
    elif page == "home":
        # use accessible AI search input enhancement here
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.title("Welcome to OptiFin")
        st.markdown("Describe your situation or goals in your own words:")
        ai_search_input()
        col_left, col_right = st.columns(3)
        with col_left:
            if st.button("Individual", key="segment_individual_btn"):
                st.session_state.user_segment = "individual"
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
        with col_right:
            if st.button("Household", key="segment_household_btn"):
                st.session_state.user_segment = "household"
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
        with st.columns(1)[0]:
            if st.button("Business", key="segment_business_btn"):
                st.session_state.user_segment = "business"
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
        if st.session_state.ai_router_result:
            r = st.session_state.ai_router_result
            st.markdown(f"<small style='color:#4ade80;'>Understanding you → <b>{r['segment'].capitalize()} : {r['module'].capitalize()}</b> (confidence: {r['confidence']:.2f})</small>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        seg = st.session_state.user_segment
        mod = st.session_state.sub_module
        fn = PAGE_FUNCTIONS.get((seg, mod), None)
        if fn:
            fn()
        else:
            st.error(f"Module [{seg}/{mod}] not yet implemented.")
            if st.button("Back to Segment Hub"):
                st.session_state.page = "segment_hub"
                st.experimental_rerun()
    else:
        st.error("Unknown page, redirecting to home...")
        st.session_state.page = "home"
        st.experimental_rerun()

    # Save contacts on every run (append to CSV if any)
    save_contacts_to_csv()

    # Render footer
    render_footer()

if __name__ == "__main__":
    init_state()
    main_router_final()
# =========================================
# OptiFin Part 4 - Advanced Personalization & UX
# -----------------------------------------
# Add this code below the previous parts in your app.py
# =========================================


import hashlib
import uuid
import json
import threading
import queue
import time


# ------------------------------
# User Authentication & Profile
# ------------------------------

USERS_FILE = "optifin_users.json"

def hash_password(password: str) -> str:
    """Hash the password securely with salt."""
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return f"{hashed}:{salt}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided."""
    hashed, salt = stored_password.split(':')
    check = hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()
    return check == hashed

def load_users():
    if not pathlib.Path(USERS_FILE).exists():
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def init_auth_state():
    if 'auth_logged_in' not in st.session_state:
        st.session_state.auth_logged_in = False
    if 'auth_username' not in st.session_state:
        st.session_state.auth_username = ""
    if 'auth_profile' not in st.session_state:
        st.session_state.auth_profile = {}
    if 'auth_message' not in st.session_state:
        st.session_state.auth_message = ""

def auth_register():
    st.subheader("Register New Account")
    username = st.text_input("Choose username", key="register_username")
    password = st.text_input("Choose password", type="password", key="register_password")
    password_confirm = st.text_input("Confirm password", type="password", key="register_password_confirm")
    if st.button("Register", key="register_btn"):
        if not username or not password or not password_confirm:
            st.error("All fields are required.")
            return
        if password != password_confirm:
            st.error("Passwords do not match.")
            return
        users = load_users()
        if username in users:
            st.error("Username already exists.")
            return
        users[username] = {
            "password": hash_password(password),
            "profile": {
                "currency": DEFAULT_CURRENCY,
                "region": DEFAULT_REGION,
                "language": "en",
                "goals": [],
            },
        }
        save_users(users)
        st.success("Registration successful, please log in.")
        st.session_state.page = "auth_login"

def auth_login():
    st.subheader("Login to OptiFin")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login_btn"):
        users = load_users()
        if username not in users:
            st.error("Invalid username or password.")
            return
        if not verify_password(users[username]["password"], password):
            st.error("Invalid username or password.")
            return
        st.session_state.auth_logged_in = True
        st.session_state.auth_username = username
        st.session_state.auth_profile = users[username]["profile"]
        st.session_state.page = "home"
        st.experimental_rerun()

def auth_logout():
    st.session_state.auth_logged_in = False
    st.session_state.auth_username = ""
    st.session_state.auth_profile = {}
    st.session_state.page = "auth_login"

def auth_profile_edit():
    st.subheader("Edit Profile")
    profile = st.session_state.auth_profile

    currency = st.selectbox("Preferred Currency", [DEFAULT_CURRENCY, "USD", "GBP", "EUR"], index=[DEFAULT_CURRENCY,"USD","GBP","EUR"].index(profile.get("currency", DEFAULT_CURRENCY)))
    region = st.selectbox("Region/Country", [DEFAULT_REGION, "United Kingdom", "United States", "Australia"], index=[DEFAULT_REGION, "United Kingdom", "United States", "Australia"].index(profile.get("region", DEFAULT_REGION)))
    language = st.selectbox("Language", ["en", "fr", "es"], index=["en","fr","es"].index(profile.get("language", "en")))

    if st.button("Save Profile Changes", key="auth_save_profile"):
        profile["currency"] = currency
        profile["region"] = region
        profile["language"] = language
        users = load_users()
        users[st.session_state.auth_username]["profile"] = profile
        save_users(users)
        st.success("Profile updated!")

# ------------------------------
# Multi-Goal Planning & Scenarios
# ------------------------------

def page_goals_manager():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header(f"{st.session_state.auth_username}'s Financial Goals")
    profile = st.session_state.auth_profile

    if "goals" not in profile:
        profile["goals"] = []

    with st.form("add_goal_form", clear_on_submit=True):
        name = st.text_input("New Goal Name (e.g., 'Education Fund')")
        target_amount = st.number_input("Target Amount (R)", min_value=0.0, format="%f", step=1000.0)
        target_date = st.date_input("Target Date", min_value=date.today())
        priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=1)
        if st.form_submit_button("Add Goal"):
            if not name or target_amount <= 0:
                st.error("Please enter valid goal name and amount.")
            else:
                profile["goals"].append({
                    "name": name,
                    "target_amount": target_amount,
                    "target_date": target_date.isoformat(),
                    "priority": priority
                })
                users = load_users()
                users[st.session_state.auth_username]["profile"] = profile
                save_users(users)
                st.success(f"Goal '{name}' added!")
                st.experimental_rerun()

    if len(profile["goals"]) == 0:
        st.info("No financial goals yet. Add one above.")
    else:
        for i, goal in enumerate(profile["goals"]):
            target_date = pd.to_datetime(goal["target_date"]).date()
            days_left = (target_date - date.today()).days
            st.markdown(f"### {goal['name']}")
            st.markdown(f"Amount: R{goal['target_amount']:,.2f}, Target Date: {target_date} ({days_left} days left), Priority: {goal['priority']}")
            if st.button(f"Delete Goal '{goal['name']}'", key=f"del_goal_{i}"):
                profile["goals"].pop(i)
                users = load_users()
                users[st.session_state.auth_username]["profile"] = profile
                save_users(users)
                st.success(f"Goal '{goal['name']}' deleted!")
                st.experimental_rerun()

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------
# Conversational AI Chat Interface
# ------------------------------

# Simple message queue for conversational context

class ChatContext:
    def __init__(self):
        self.history = deque(maxlen=10)  # keep last 10 messages
    
    def add_user_message(self, msg):
        self.history.append({"role": "user", "content": msg})

    def add_assistant_message(self, msg):
        self.history.append({"role": "assistant", "content": msg})

    def get_messages(self):
        return list(self.history)

chat_contexts = {}

def get_user_chat_context(username):
    if username not in chat_contexts:
        chat_contexts[username] = ChatContext()
    return chat_contexts[username]

def call_openai_chat(messages):
    if not OPENAI_AVAILABLE or "OPENAI_API_KEY" not in st.secrets:
        return None
    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.4,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None

def page_chatbot_interface():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("OptiFin Financial Advisor Chatbot")

    username = st.session_state.auth_username
    context = get_user_chat_context(username)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Ask me about financial planning, investments, tax, retirement...", key="chat_input", height=100)
        submitted = st.form_submit_button("Send")
    
    if submitted and user_input.strip():
        context.add_user_message(user_input.strip())
        with st.spinner("Thinking..."):
            answer = call_openai_chat(context.get_messages())
            if answer is None:
                answer = "AI currently unavailable. Please try later or consult the deterministic advice modules."
            context.add_assistant_message(answer)
        st.experimental_rerun()
    
    # Display conversation history
    for msg in context.get_messages():
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**OptiFin:** {msg['content']}")

    if st.button("Clear Chat", key="btn_clear_chat"):
        chat_contexts.pop(username, None)
        st.experimental_rerun()

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# Notifications Framework (Basic)
# ------------------------------

def display_notifications():
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []

    # Sample notification: tile can be adapted later
    if st.session_state.auth_logged_in and len(st.session_state.notifications) == 0:
        st.session_state.notifications.append({
            "type": "info",
            "message": "Upcoming tax filing deadline is 30 September 2025."
        })

    for notif in st.session_state.notifications:
        if notif["type"] == "info":
            st.info(notif["message"])
        elif notif["type"] == "warning":
            st.warning(notif["message"])
        elif notif["type"] == "error":
            st.error(notif["message"])

# ------------------------------
# Augment Main Router & Pages
# ------------------------------

def main_router_part4():
    apply_styles()

    # Sidebar Auth/Profile management
    with st.sidebar:
        st.title(APP_NAME)
        if st.session_state.auth_logged_in:
            st.markdown(f"Signed in as **{st.session_state.auth_username}**")
            if st.button("Logout", key="btn_logout"):
                auth_logout()
                st.experimental_rerun()
            if st.button("Edit Profile", key="btn_edit_profile"):
                st.session_state.page = "auth_profile_edit"
                st.experimental_rerun()
            if st.button("Manage Goals", key="btn_manage_goals"):
                st.session_state.page = "goals_manager"
                st.experimental_rerun()
            if st.button("Chat with Advisor", key="btn_chat_advisor"):
                st.session_state.page = "chatbot"
                st.experimental_rerun()
        else:
            if st.button("Login", key="btn_show_login"):
                st.session_state.page = "auth_login"
                st.experimental_rerun()
            if st.button("Register", key="btn_show_register"):
                st.session_state.page = "auth_register"
                st.experimental_rerun()

        st.markdown("---")
        theme_selection = st.radio("Theme", options=['dark', 'light'], index=0 if st.session_state.theme == 'dark' else 1, key="theme_radio_sidebar")
        if theme_selection != st.session_state.theme:
            st.session_state.theme = theme_selection
            st.experimental_rerun()

        bg_choice = st.selectbox("Background Image", options=list(BACKGROUND_IMAGES.keys()), key="background_select_sidebar")
        new_background = BACKGROUND_IMAGES[bg_choice]
        if st.session_state.background != new_background:
            st.session_state.background = new_background
            st.experimental_rerun()

        st.markdown("---")
        st.markdown(f"© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.")

    # Show notifications when logged in
    if st.session_state.auth_logged_in:
        display_notifications()

    page = st.session_state.page

    # Route pages for Auth
    if page == "auth_login":
        auth_login()
    elif page == "auth_register":
        auth_register()
    elif page == "auth_profile_edit":
        auth_profile_edit()
    elif page == "goals_manager":
        page_goals_manager()
    elif page == "chatbot":
        page_chatbot_interface()
    # Existing pages override for logged-in users
    elif page == "privacy_gate" and not st.session_state.consent_accepted:
        page_privacy_gate()
    elif page == "home":
        if not st.session_state.auth_logged_in:
            st.info("Please log in or register to access full features.")
            if st.button("Login"):
                st.session_state.page = "auth_login"
                st.experimental_rerun()
            if st.button("Register"):
                st.session_state.page = "auth_register"
                st.experimental_rerun()
        else:
            page_home()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        seg = st.session_state.user_segment
        mod = st.session_state.sub_module
        fn = PAGE_FUNCTIONS.get((seg, mod), None)
        if fn:
            fn()
        else:
            st.error("Module not implemented yet.")
    else:
        st.error("Unknown page, redirecting to home...")
        st.session_state.page = "home"
        st.experimental_rerun()

    # Save contact submissions persistently
    save_contacts_to_csv()

    render_footer()

if __name__ == "__main__":
    init_state()
    main_router_part4()
# ===========================================
# OptiFin Part 5 - Integration & Ecosystem Expansion
# -------------------------------------------
# Append below previous parts in your app.py
# ===========================================

import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uvicorn
import base64
import mimetypes

# Note: FastAPI inclusion is conceptual here and would typically be served on a separate port
# but for demonstration, we add minimal API endpoints.

# -------------
# FastAPI backend for advisor API and webhook
# -------------

app_api = FastAPI(title="OptiFin API", description="Financial Planning Ecosystem API")

app_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as per production security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory client storage simulation (replace with DB)
advisor_clients = {}

@app_api.get("/clients/{username}")
def get_client_profile(username: str):
    client = advisor_clients.get(username)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app_api.post("/clients/{username}/update")
def update_client_profile(username: str, profile: dict):
    advisor_clients[username] = profile
    return JSONResponse(status_code=200, content={"message": f"Profile updated for {username}"})

@app_api.post("/webhook/contact")
async def contact_webhook(contact: dict):
    # In production, process webhook data (e.g., store in DB, send email)
    print(f"Received contact webhook: {contact}")
    return {"message": "Contact received"}

# ---- Run FastAPI separately (concept demo) ----
# To run backend:
# uvicorn.run(app_api, host="0.0.0.0", port=8000)

# -------------
# Real-time Market Data Enhancements
# -------------

def fetch_real_time_price(ticker):
    # Implement advanced APIs like IEX Cloud or Alpha Vantage here
    # For demo, fallback to yfinance realtime closing price
    if not YF_AVAILABLE:
        return None
    try:
        ticker_obj = yf.Ticker(ticker)
        price = ticker_obj.history(period='1d')['Close'].iloc[-1]
        return price
    except Exception:
        return None

def enhanced_investment_advice(segment, inputs):
    # This would use comprehensive datasets and live data
    # For demo, a placeholder returns enhanced advice text
    advice_text = f"""
    Based on real-time market data and your profile for {segment}:

    - Diversify your portfolio with a mix of Core ETFs and thematic funds.
    - Maintain a minimum cash buffer of 5% to 10% for liquidity.
    - Review your portfolio quarterly; adjust risk exposure based on market volatility.
    - Utilize tax-free savings vehicles appropriate to your region.
    - Contact OptiFin for personalized trade execution and tax wrap advice.
    """
    return advice_text.strip()

# -------------
# Banking & Accounting Integration Placeholder
# -------------

def bank_transaction_import_demo():
    st.info("Bank integration coming soon. Meanwhile, you can import CSV files of transactions manually.")

    uploaded_file = st.file_uploader("Upload CSV Bank Statement (Date, Description, Amount)")
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Preview of imported bank transactions")
            st.dataframe(df.head())
            # Implement categorization, tagging here...
        except Exception as ex:
            st.error(f"Error reading CSV: {ex}")

# -------------
# Document Upload & OCR Placeholder
# -------------

def document_upload_and_processing():
    st.info("Upload financial documents (bills, receipts, tax forms) for OCR extraction of data.")

    uploaded_docs = st.file_uploader("Upload PDFs or Images", accept_multiple_files=True)

    if uploaded_docs:
        for doc in uploaded_docs:
            st.write(f"Uploaded file: {doc.name} ({mimetypes.guess_type(doc.name)[0]})")
            # In production, pass file to OCR service, extract fields, autofill forms

        st.success("Document processing integrated with OCR coming soon.")

# -------------
# Compliance & Regulatory Update Monitor Placeholder
# -------------

def display_regulatory_updates():
    st.subheader("Current Regulatory & Compliance Updates")
    updates=[
        {"date": "2025-07-01", "region": "SA", "description": "New medical tax credit limits applied."},
        {"date": "2025-06-20", "region": "US", "description": "401(k) contribution limits raised for 2026."},
        {"date": "2025-06-10", "region": "UK", "description": "Capital gains tax allowance updated."},
    ]

    for upd in updates:
        st.markdown(f"**{upd['date']} [{upd['region']}]** - {upd['description']}")

# -------------
# Mobile & PWA Preparation Notes
# -------------

def pwa_installation_notice():
    st.info("""  
    OptiFin is fully designed with responsive UI for desktop and mobile browsers.  
    To install as an app on your mobile device, use your browser menu's "Add to Home Screen".  
    For native apps, mobile SDKs and sync services are planned for future releases.  
    """)

# -------------
# Augment Main Router & UI with new pages
# -------------

def main_router_part5():
    apply_styles()

    with st.sidebar:
        st.title(APP_NAME)
        if st.session_state.auth_logged_in:
            st.markdown(f"Signed in as **{st.session_state.auth_username}**")
            if st.button("Logout", key="btn_logout_p5"):
                auth_logout()
                st.experimental_rerun()
            if st.button("Edit Profile", key="btn_edit_profile_p5"):
                st.session_state.page = "auth_profile_edit"
                st.experimental_rerun()
            if st.button("Manage Goals", key="btn_manage_goals_p5"):
                st.session_state.page = "goals_manager"
                st.experimental_rerun()
            if st.button("Chat with Advisor", key="btn_chat_advisor_p5"):
                st.session_state.page = "chatbot"
                st.experimental_rerun()
            if st.button("Upload Bank Transactions", key="btn_bank_upload"):
                st.session_state.page = "bank_upload"
                st.experimental_rerun()
            if st.button("Upload Documents", key="btn_doc_upload"):
                st.session_state.page = "doc_upload"
                st.experimental_rerun()
            if st.button("Regulatory Updates", key="btn_reg_updates"):
                st.session_state.page = "reg_updates"
                st.experimental_rerun()
            if st.button("PWA Info", key="btn_pwa_info"):
                st.session_state.page = "pwa_info"
                st.experimental_rerun()
        else:
            if st.button("Login", key="btn_show_login_p5"):
                st.session_state.page = "auth_login"
                st.experimental_rerun()
            if st.button("Register", key="btn_show_register_p5"):
                st.session_state.page = "auth_register"
                st.experimental_rerun()

        st.markdown("---")
        theme_selection = st.radio("Theme", options=['dark', 'light'], index=0 if st.session_state.theme == 'dark' else 1, key="theme_radio_sidebar_p5")
        if theme_selection != st.session_state.theme:
            st.session_state.theme = theme_selection
            st.experimental_rerun()

        bg_choice = st.selectbox("Background Image", options=list(BACKGROUND_IMAGES.keys()), key="background_select_sidebar_p5")
        new_background = BACKGROUND_IMAGES[bg_choice]
        if st.session_state.background != new_background:
            st.session_state.background = new_background
            st.experimental_rerun()

        st.markdown("---")
        st.markdown(f"© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.")

    page = st.session_state.page

    if page == "bank_upload":
        bank_transaction_import_demo()
    elif page == "doc_upload":
        document_upload_and_processing()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "pwa_info":
        pwa_installation_notice()
    else:
        # Former routing from part 4
        main_router_part4()  # reuse Part4 router to handle other pages

if __name__ == "__main__":
    init_state()
    main_router_part5()
# Append to existing app.py
import pandas as pd
from prophet import Prophet
import streamlit as st

def page_predictive_cashflow():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Predictive Cashflow & Expense Forecasting")

    uploaded_file = st.file_uploader("Upload your transaction history CSV (Date, Amount, Category)", type=["csv"], key="upload_cashflow")
    if uploaded_file is None:
        st.info("Upload your CSV bank/expense transactions to generate predictions.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip().lower() for c in df.columns]
        if not all(col in df.columns for col in ["date", "amount"]):
            st.error("CSV must contain 'date' and 'amount' columns.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        df["date"] = pd.to_datetime(df["date"])
        daily_df = df.groupby("date")["amount"].sum().reset_index()

        st.subheader("Raw Daily Transactions")
        st.dataframe(daily_df.tail(50))

        # Prepare data for Prophet
        prophet_data = daily_df.rename(columns={"date": "ds", "amount": "y"})
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        model.fit(prophet_data)

        future = model.make_future_dataframe(periods=90)  # next 90 days forecast
        forecast = model.predict(future)

        st.subheader("Forecasted Cash Flow (Next 90 Days)")
        fig = model.plot(forecast)
        st.pyplot(fig)

        # Summary metrics
        predicted_spending = forecast[forecast["ds"] > daily_df["ds"].max()]["yhat"].sum()
        st.metric("Predicted Net Cashflow next 90 days", f"R{predicted_spending:,.2f}")

        st.markdown(
            "Use this forecast to anticipate low cash periods and adjust your budgets or savings plans proactively."
        )

    except Exception as e:
        st.error(f"Error processing data or forecasting: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)


# Add this to PAGE_FUNCTIONS dict:
PAGE_FUNCTIONS.update({
    ("individual", "predictive_cashflow"): page_predictive_cashflow,
    ("household", "predictive_cashflow"): page_predictive_cashflow,
    ("business", "predictive_cashflow"): page_predictive_cashflow,
})
# Append to your app.py

import numpy as np

def page_smart_savings():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Smart Savings & Auto-Investment Plan")

    # Get user profile inputs for simulation
    income = st.number_input("Monthly Net Income (R)", min_value=0.0, step=100.0, key="smart_savings_income", format="%.2f")
    current_savings = st.number_input("Current Savings (R)", min_value=0.0, step=100.0, key="smart_savings_current", format="%.2f")
    target_goal = st.number_input("Savings Goal Amount (R)", min_value=0.0, step=1000.0, key="smart_savings_goal", format="%.2f")
    months_to_goal = st.number_input("Months to Goal", min_value=1, max_value=360, value=60, key="smart_savings_months")
    risk = st.slider("Risk Tolerance (1 = Low, 5 = High)", minimum=1, maximum=5, value=3, key="smart_savings_risk")

    # Calculate recommendations dynamically
    base_return = {1: 0.035, 2: 0.05, 3: 0.07, 4: 0.09, 5: 0.12}[risk]

    # Interactive monthly savings slider to visualize future value
    st.markdown("### Try different monthly savings amounts to see projection:")
    suggested_savings = np.ceil((target_goal - current_savings) / months_to_goal)
    monthly_savings_input = st.slider("Monthly Savings (R)", min_value=0, max_value=int(income), value=int(max(suggested_savings, 0)), step=100, key="smart_savings_slider")

    # Future value calculation with compound interest monthly
    monthly_return = (1 + base_return) ** (1/12) - 1
    bal = current_savings
    projections = []
    for _ in range(months_to_goal):
        bal = bal * (1 + monthly_return) + monthly_savings_input
        projections.append(bal)

    final_value = projections[-1]
    gap = target_goal - final_value

    # Feedback
    st.markdown(f"**Projected Savings after {months_to_goal} months:** R{final_value:,.2f}")
    if gap > 0:
        st.warning(f"You are short by approximately R{gap:,.2f}. Consider increasing monthly savings or extending your timeframe.")
    else:
        st.success(f"Congratulations! Your plan exceeds the target by R{abs(gap):,.2f}.")

    # Plot projection chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=projections, mode='lines+markers', line=dict(color='#4ade80'), marker=dict(size=5)))
    fig.update_layout(
        title="Savings Projection",
        xaxis_title="Months",
        yaxis_title="Projected Savings (R)",
        height=280,
        margin=dict(l=20, r=20, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(20,24,28,0.85)' if st.session_state.theme == 'dark' else 'rgba(255,255,255,0.9)',
        font=dict(color='#eef6ff' if st.session_state.theme == 'dark' else '#111'),
    )
    st.plotly_chart(fig, use_container_width=True)

    # AI-generated suggestions (placeholder, real prompt integration in Part 4)
    advice = f"""
    Based on your inputs:
    - Monthly Income: R{income:,.2f}
    - Current Savings: R{current_savings:,.2f}
    - Goal Amount: R{target_goal:,.2f}
    - Timeframe: {months_to_goal} months
    - Risk Tolerance: {risk}

    We recommend saving at least R{max(suggested_savings, 0):,.2f} monthly with an estimated annual return of {base_return*100:.2f}%.
    Keep consistent contributions and review periodically.

    Consult OptiFin experts for personalized investment portfolio adjustments.
    """
    st.markdown(f"<div class='ai-insight-card'><pre style='white-space:pre-wrap'>{advice.strip()}</pre></div>", unsafe_allow_html=True)

    if st.button("Back to Segment Hub", key="btn_back_smart_savings"):
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# Add to PAGE_FUNCTIONS
PAGE_FUNCTIONS.update({
    ("individual", "smart_savings"): page_smart_savings,
    ("household", "smart_savings"): page_smart_savings,
    ("business", "smart_savings"): page_smart_savings,
})
# Append to your app.py

def simulate_tax_scenarios(annual_income, dependants, scenarios):
    """
    Simulates multiple tax optimization scenarios.
    scenarios: list of dicts with keys:
        - 'name': str scenario name
        - 'deductions': float total deductions for scenario
    Returns dict mapping scenario name to estimated tax and effective rate.
    """
    results = {}
    for s in scenarios:
        deductions = s.get('deductions', 0.0)
        taxable_income = max(0.0, annual_income - deductions - dependants * 3500)
        # Simple progressive tax, SA rules demo
        if taxable_income < 50000:
            rate = 0.18
        elif taxable_income < 150000:
            rate = 0.26
        else:
            rate = 0.39
        est_tax = taxable_income * rate
        eff_rate = est_tax / annual_income if annual_income > 0 else 0
        results[s['name']] = {"estimated_tax": est_tax, "effective_rate": eff_rate, "taxable_income": taxable_income}
    return results

def page_tax_scenario_simulator():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Tax Optimization Scenario Simulator")

    try:
        annual_income = st.number_input("Annual Income (R)", min_value=0.0, step=1000.0, key="tax_sim_income")
        dependants = st.number_input("Number of Dependants", min_value=0, step=1, key="tax_sim_dependants")

        st.markdown("### Define your tax scenarios (compare deductions)")

        scenarios = []
        rows = st.number_input("Number of scenarios to simulate", min_value=1, max_value=5, value=2, key="tax_sim_rows")
        for i in range(int(rows)):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(f"Scenario {i+1} Name", value=f"Scenario {i+1}", key=f"tax_sim_name_{i}")
            with col2:
                deductions = st.number_input(f"Total Deductions (R)", min_value=0.0, step=1000.0, key=f"tax_sim_deductions_{i}")
            scenarios.append({"name": name, "deductions": deductions})

        if st.button("Run Simulation", key="btn_run_tax_sim"):
            results = simulate_tax_scenarios(annual_income, int(dependants), scenarios)
            st.subheader("Simulation Results")
            for s in scenarios:
                res = results.get(s['name'])
                if res:
                    st.markdown(f"**{s['name']}**: Estimated Tax: R{res['estimated_tax']:,.2f} | Effective Tax Rate: {res['effective_rate']*100:.2f}% | Taxable Income: R{res['taxable_income']:,.2f}")
                    # Bar style visualization
                    st.progress(min(res['effective_rate'],1.0))
            st.markdown("Consult OptiFin to implement optimal tax strategies based on these scenarios.")

        if st.button("Back to Segment Hub", key="btn_back_tax_sim"):
            st.session_state.page = "segment_hub"
            st.experimental_rerun()

    except Exception as e:
        st.error(f"Error during simulation: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# Add to PAGE_FUNCTIONS dict
PAGE_FUNCTIONS.update({
    ("individual", "tax_simulator"): page_tax_scenario_simulator,
    ("household", "tax_simulator"): page_tax_scenario_simulator,
    ("business", "tax_simulator"): page_tax_scenario_simulator,
})
# Append to your app.py

def simulate_tax_scenarios(annual_income, dependants, scenarios):
    """
    Simulates multiple tax optimization scenarios.
    scenarios: list of dicts with keys:
        - 'name': str scenario name
        - 'deductions': float total deductions for scenario
    Returns dict mapping scenario name to estimated tax and effective rate.
    """
    results = {}
    for s in scenarios:
        deductions = s.get('deductions', 0.0)
        taxable_income = max(0.0, annual_income - deductions - dependants * 3500)
        # Simple progressive tax, SA rules demo
        if taxable_income < 50000:
            rate = 0.18
        elif taxable_income < 150000:
            rate = 0.26
        else:
            rate = 0.39
        est_tax = taxable_income * rate
        eff_rate = est_tax / annual_income if annual_income > 0 else 0
        results[s['name']] = {"estimated_tax": est_tax, "effective_rate": eff_rate, "taxable_income": taxable_income}
    return results

def page_tax_scenario_simulator():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Tax Optimization Scenario Simulator")

    try:
        annual_income = st.number_input("Annual Income (R)", min_value=0.0, step=1000.0, key="tax_sim_income")
        dependants = st.number_input("Number of Dependants", min_value=0, step=1, key="tax_sim_dependants")

        st.markdown("### Define your tax scenarios (compare deductions)")

        scenarios = []
        rows = st.number_input("Number of scenarios to simulate", min_value=1, max_value=5, value=2, key="tax_sim_rows")
        for i in range(int(rows)):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(f"Scenario {i+1} Name", value=f"Scenario {i+1}", key=f"tax_sim_name_{i}")
            with col2:
                deductions = st.number_input(f"Total Deductions (R)", min_value=0.0, step=1000.0, key=f"tax_sim_deductions_{i}")
            scenarios.append({"name": name, "deductions": deductions})

        if st.button("Run Simulation", key="btn_run_tax_sim"):
            results = simulate_tax_scenarios(annual_income, int(dependants), scenarios)
            st.subheader("Simulation Results")
            for s in scenarios:
                res = results.get(s['name'])
                if res:
                    st.markdown(f"**{s['name']}**: Estimated Tax: R{res['estimated_tax']:,.2f} | Effective Tax Rate: {res['effective_rate']*100:.2f}% | Taxable Income: R{res['taxable_income']:,.2f}")
                    # Bar style visualization
                    st.progress(min(res['effective_rate'],1.0))
            st.markdown("Consult OptiFin to implement optimal tax strategies based on these scenarios.")

        if st.button("Back to Segment Hub", key="btn_back_tax_sim"):
            st.session_state.page = "segment_hub"
            st.experimental_rerun()

    except Exception as e:
        st.error(f"Error during simulation: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# Add to PAGE_FUNCTIONS dict
PAGE_FUNCTIONS.update({
    ("individual", "tax_simulator"): page_tax_scenario_simulator,
    ("household", "tax_simulator"): page_tax_scenario_simulator,
    ("business", "tax_simulator"): page_tax_scenario_simulator,
})
# Append below in your app.py

import textblob

def fetch_sample_financial_news():
    """
    Placeholder: fetches recent financial news headlines related to user investments.
    Replace with live API calls (e.g. NewsAPI, Bloomberg API).
    """
    return [
        "Stock markets rally amid easing inflation concerns",
        "Tech sector reports mixed earnings for Q3",
        "South African Rand strengthens against US dollar",
        "New government tax incentives announced for retirement savings"
    ]

def analyze_sentiment(text):
    blob = textblob.TextBlob(text)
    return blob.sentiment.polarity  # -1 (negative) to 1 (positive)

def page_sentiment_insights():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Market Sentiment & Portfolio Insights")

    # Fetch news
    news = fetch_sample_financial_news()
    st.subheader("Recent Financial News")
    for idx, headline in enumerate(news, 1):
        polarity = analyze_sentiment(headline)
        sentiment_label = "Positive" if polarity > 0.1 else "Neutral" if -0.1 <= polarity <= 0.1 else "Negative"
        color = "#22c55e" if sentiment_label=="Positive" else "#facc15" if sentiment_label=="Neutral" else "#ef4444"
        st.markdown(f"{idx}. <span style='color:{color}'><b>[{sentiment_label}]</b></span> {headline}", unsafe_allow_html=True)

    # Aggregate sentiment
    avg_sentiment = sum(analyze_sentiment(n) for n in news) / len(news)
    st.markdown(f"**Average market sentiment score:** {avg_sentiment:.2f}")

    # Simple advice based on sentiment
    if avg_sentiment > 0.2:
        advice = "Market sentiment is positive. Consider cautiously increasing growth allocations."
    elif avg_sentiment < -0.2:
        advice = "Market sentiment is negative. Defensive positioning and cash buffers may be advisable."
    else:
        advice = "Market sentiment neutral; maintain current portfolio balance and monitor news."

    st.markdown(f"<div class='ai-insight-card'>{advice}</div>", unsafe_allow_html=True)

    if st.button("Back to Segment Hub", key="btn_back_sentiment"):
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

PAGE_FUNCTIONS.update({
    ("individual", "sentiment_insights"): page_sentiment_insights,
    ("household", "sentiment_insights"): page_sentiment_insights,
    ("business", "sentiment_insights"): page_sentiment_insights,
})
# Append to your app.py

# Simple in-memory user achievement tracking (persist to DB/file in production)
if "achievements" not in st.session_state:
    st.session_state.achievements = set()

def award_achievement(name: str):
    if name not in st.session_state.achievements:
        st.session_state.achievements.add(name)
        st.success(f"🎉 Achievement Unlocked: {name}!")

def page_achievements():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Achievements & Rewards")

    # Sample achievements checks (extend with real logic)
    profile = st.session_state.auth_profile or {}
    goals = profile.get("goals", [])
    if goals and "Goal Setter" not in st.session_state.achievements:
        award_achievement("Goal Setter")
    if len(goals) >= 3 and "Multi-Goal Planner" not in st.session_state.achievements:
        award_achievement("Multi-Goal Planner")

    st.markdown("Your Achievements:")
    if not st.session_state.achievements:
        st.info("No achievements yet. Keep progressing!")
    else:
        for ach in st.session_state.achievements:
            st.markdown(f"- ✅ {ach}")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# -------- Community Forum Placeholder --------

def page_community_forum():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Community Forum")

    st.info("The forum is coming soon! Meanwhile, join our mailing list or social media for updates.")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# -------- Educational Resources --------

def page_educational_resources():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Financial Education & Tutorials")

    tutorials = [
        {"title": "Basics of Investing", "link": "https://www.investopedia.com/articles/basics/06/invest1000.asp"},
        {"title": "Tax Savings Strategies", "link": "https://www.sars.gov.za/"},
        {"title": "Retirement Planning 101", "link": "https://www.a retirement site.com"},
        {"title": "Understanding Credit & Debt", "link": "https://www.consumerfinance.gov/"},
    ]

    for tut in tutorials:
        st.markdown(f"- [{tut['title']}]({tut['link']})")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# -------- Referral Program Placeholder --------

def page_referral_program():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Referral Program")

    st.info("""
    Invite your friends to OptiFin and earn credits towards premium reports and advice.
    Share your unique referral code:
    """)
    if st.session_state.auth_logged_in:
        referral_code = hashlib.sha256(st.session_state.auth_username.encode()).hexdigest()[:8].upper()
        st.code(referral_code)
    else:
        st.warning("Please log in to see your referral code.")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# -------- New Pages Mapping --------

PAGE_FUNCTIONS.update({
    ("individual", "achievements"): page_achievements,
    ("household", "achievements"): page_achievements,
    ("business", "achievements"): page_achievements,

    ("individual", "community"): page_community_forum,
    ("household", "community"): page_community_forum,
    ("business", "community"): page_community_forum,

    ("individual", "education"): page_educational_resources,
    ("household", "education"): page_educational_resources,
    ("business", "education"): page_educational_resources,

    ("individual", "referral"): page_referral_program,
    ("household", "referral"): page_referral_program,
    ("business", "referral"): page_referral_program,
})

# -------- Enhance Sidebar --------

def extend_sidebar():
    if st.session_state.auth_logged_in:
        st.markdown("---")
        st.markdown("### Community")
        if st.button("Achievements", key="sidebar_achievements"):
            st.session_state.page = "achievements"
            st.experimental_rerun()
        if st.button("Community Forum", key="sidebar_community"):
            st.session_state.page = "community"
            st.experimental_rerun()
        if st.button("Educational Resources", key="sidebar_education"):
            st.session_state.page = "education"
            st.experimental_rerun()
        if st.button("Referral Program", key="sidebar_referral"):
            st.session_state.page = "referral"
            st.experimental_rerun()

# -------- Modify main router to call extend_sidebar --------

_old_main_router_part5 = main_router_part5  # save old router as _old_main_router_part5

def main_router_part7():
    apply_styles()

    with st.sidebar:
        st.title(APP_NAME)

        if st.session_state.auth_logged_in:
            st.markdown(f"Signed in as **{st.session_state.auth_username}**")
            if st.button("Logout", key="btn_logout7"):
                auth_logout()
                st.experimental_rerun()
            if st.button("Edit Profile", key="btn_edit_profile7"):
                st.session_state.page = "auth_profile_edit"
                st.experimental_rerun()
            if st.button("Manage Goals", key="btn_manage_goals7"):
                st.session_state.page = "goals_manager"
                st.experimental_rerun()
            if st.button("Chat with Advisor", key="btn_chat_advisor7"):
                st.session_state.page = "chatbot"
                st.experimental_rerun()
            if st.button("Upload Bank Transactions", key="btn_bank_upload7"):
                st.session_state.page = "bank_upload"
                st.experimental_rerun()
            if st.button("Upload Documents", key="btn_doc_upload7"):
                st.session_state.page = "doc_upload"
                st.experimental_rerun()
            if st.button("Regulatory Updates", key="btn_reg_updates7"):
                st.session_state.page = "reg_updates"
                st.experimental_rerun()
            if st.button("PWA Info", key="btn_pwa_info7"):
                st.session_state.page = "pwa_info"
                st.experimental_rerun()
        else:
            if st.button("Login", key="btn_show_login7"):
                st.session_state.page = "auth_login"
                st.experimental_rerun()
            if st.button("Register", key="btn_show_register7"):
                st.session_state.page = "auth_register"
                st.experimental_rerun()

        extend_sidebar()

        st.markdown("---")
        theme_selection = st.radio("Theme", options=['dark', 'light'], index=0 if st.session_state.theme == 'dark' else 1, key="theme_radio_sidebar7")
        if theme_selection != st.session_state.theme:
            st.session_state.theme = theme_selection
            st.experimental_rerun()

        bg_choice = st.selectbox("Background Image", options=list(BACKGROUND_IMAGES.keys()), key="background_select_sidebar7")
        new_background = BACKGROUND_IMAGES[bg_choice]
        if st.session_state.background != new_background:
            st.session_state.background = new_background
            st.experimental_rerun()

        st.markdown("---")
        st.markdown(f"© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.")

    page = st.session_state.page

    if page == "bank_upload":
        bank_transaction_import_demo()
    elif page == "doc_upload":
        document_upload_and_processing()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "pwa_info":
        pwa_installation_notice()
    else:
        # Route using all prior pages
        if page in ["auth_login", "auth_register", "auth_profile_edit", "goals_manager", "chatbot", "privacy_gate",
                    "home", "segment_hub", "module_form"]:
            _old_main_router_part5()
        elif page in ["achievements", "community", "education", "referral"]:
            fn = PAGE_FUNCTIONS.get((st.session_state.user_segment, page), None)
            if fn:
                fn()
            else:
                st.error(f"Page not implemented: {page}")
        else:
            st.error(f"Unknown page: {page}. Redirecting home...")
            st.session_state.page = "home"
            st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    main_router_part7()
# Continue Part 7 - Community, Achievements, Education, Referral, Sidebar and Routing enhancements

# Simple in-memory user achievement tracking (persist to DB/file in production)
if "achievements" not in st.session_state:
    st.session_state.achievements = set()

def award_achievement(name: str):
    if name not in st.session_state.achievements:
        st.session_state.achievements.add(name)
        st.success(f"🎉 Achievement Unlocked: {name}!")

def page_achievements():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Achievements & Rewards")

    # Sample achievements checks (extend with real logic)
    profile = st.session_state.auth_profile or {}
    goals = profile.get("goals", [])
    if goals and "Goal Setter" not in st.session_state.achievements:
        award_achievement("Goal Setter")
    if len(goals) >= 3 and "Multi-Goal Planner" not in st.session_state.achievements:
        award_achievement("Multi-Goal Planner")

    st.markdown("Your Achievements:")
    if not st.session_state.achievements:
        st.info("No achievements yet. Keep progressing!")
    else:
        for ach in st.session_state.achievements:
            st.markdown(f"- ✅ {ach}")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def page_community_forum():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Community Forum")

    st.info("The forum is coming soon! Meanwhile, join our mailing list or social media for updates.")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def page_educational_resources():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Financial Education & Tutorials")

    tutorials = [
        {"title": "Basics of Investing", "link": "https://www.investopedia.com/articles/basics/06/invest1000.asp"},
        {"title": "Tax Savings Strategies", "link": "https://www.sars.gov.za/"},
        {"title": "Retirement Planning 101", "link": "https://www.example.com/retirement-planning"},
        {"title": "Understanding Credit & Debt", "link": "https://www.consumerfinance.gov/"},
    ]

    for tut in tutorials:
        st.markdown(f"- [{tut['title']}]({tut['link']})")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def page_referral_program():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Referral Program")

    st.info("""
    Invite your friends to OptiFin and earn credits towards premium reports and advice.
    Share your unique referral code:
    """)
    if st.session_state.auth_logged_in:
        referral_code = hashlib.sha256(st.session_state.auth_username.encode()).hexdigest()[:8].upper()
        st.code(referral_code)
    else:
        st.warning("Please log in to see your referral code.")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# Update PAGE_FUNCTIONS dictionary to include new pages
PAGE_FUNCTIONS.update({
    ("individual", "achievements"): page_achievements,
    ("household", "achievements"): page_achievements,
    ("business", "achievements"): page_achievements,

    ("individual", "community"): page_community_forum,
    ("household", "community"): page_community_forum,
    ("business", "community"): page_community_forum,

    ("individual", "education"): page_educational_resources,
    ("household", "education"): page_educational_resources,
    ("business", "education"): page_educational_resources,

    ("individual", "referral"): page_referral_program,
    ("household", "referral"): page_referral_program,
    ("business", "referral"): page_referral_program,
})

# Enhance sidebar to include community sections
def extend_sidebar():
    if st.session_state.auth_logged_in:
        st.markdown("---")
        st.markdown("### Community")
        if st.button("Achievements", key="sidebar_achievements"):
            st.session_state.page = "achievements"
            st.experimental_rerun()
        if st.button("Community Forum", key="sidebar_community"):
            st.session_state.page = "community"
            st.experimental_rerun()
        if st.button("Educational Resources", key="sidebar_education"):
            st.session_state.page = "education"
            st.experimental_rerun()
        if st.button("Referral Program", key="sidebar_referral"):
            st.session_state.page = "referral"
            st.experimental_rerun()

# Override main router portion to call extend_sidebar
_old_main_router_part5 = main_router_part5  # keep old main router

def main_router_part7():
    apply_styles()

    with st.sidebar:
        st.title(APP_NAME)

        if st.session_state.auth_logged_in:
            st.markdown(f"Signed in as **{st.session_state.auth_username}**")
            if st.button("Logout", key="btn_logout7"):
                auth_logout()
                st.experimental_rerun()
            if st.button("Edit Profile", key="btn_edit_profile7"):
                st.session_state.page = "auth_profile_edit"
                st.experimental_rerun()
            if st.button("Manage Goals", key="btn_manage_goals7"):
                st.session_state.page = "goals_manager"
                st.experimental_rerun()
            if st.button("Chat with Advisor", key="btn_chat_advisor7"):
                st.session_state.page = "chatbot"
                st.experimental_rerun()
            if st.button("Upload Bank Transactions", key="btn_bank_upload7"):
                st.session_state.page = "bank_upload"
                st.experimental_rerun()
            if st.button("Upload Documents", key="btn_doc_upload7"):
                st.session_state.page = "doc_upload"
                st.experimental_rerun()
            if st.button("Regulatory Updates", key="btn_reg_updates7"):
                st.session_state.page = "reg_updates"
                st.experimental_rerun()
            if st.button("PWA Info", key="btn_pwa_info7"):
                st.session_state.page = "pwa_info"
                st.experimental_rerun()
        else:
            if st.button("Login", key="btn_show_login7"):
                st.session_state.page = "auth_login"
                st.experimental_rerun()
            if st.button("Register", key="btn_show_register7"):
                st.session_state.page = "auth_register"
                st.experimental_rerun()

        extend_sidebar()

        st.markdown("---")
        theme_selection = st.radio("Theme", options=['dark', 'light'], index=0 if st.session_state.theme == 'dark' else 1, key="theme_radio_sidebar7")
        if theme_selection != st.session_state.theme:
            st.session_state.theme = theme_selection
            st.experimental_rerun()

        bg_choice = st.selectbox("Background Image", options=list(BACKGROUND_IMAGES.keys()), key="background_select_sidebar7")
        new_background = BACKGROUND_IMAGES[bg_choice]
        if st.session_state.background != new_background:
            st.session_state.background = new_background
            st.experimental_rerun()

        st.markdown("---")
        st.markdown(f"© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.")

    page = st.session_state.page

    # Route pages
    if page == "bank_upload":
        bank_transaction_import_demo()
    elif page == "doc_upload":
        document_upload_and_processing()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "pwa_info":
        pwa_installation_notice()
    else:
        if page in ["auth_login", "auth_register", "auth_profile_edit", "goals_manager", "chatbot",
                    "privacy_gate", "home", "segment_hub", "module_form"]:
            _old_main_router_part5()  # call old router for core pages
        elif page in ["achievements", "community", "education", "referral"]:
            fn = PAGE_FUNCTIONS.get((st.session_state.user_segment, page), None)
            if fn:
                fn()
            else:
                st.error(f"Page not implemented: {page}")
        else:
            st.error(f"Unknown page: {page}. Redirecting home...")
            st.session_state.page = "home"
            st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    main_router_part7()


