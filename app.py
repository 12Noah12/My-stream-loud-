# app.py - OptiFin (Production-ready, market-aware, PDF/Excel exports, unique keys)
# Requirements (at end). Add OPENAI_API_KEY to Streamlit secrets for full GPT features.

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import yfinance as yf
import io, math, datetime, textwrap, json, os, base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import xlsxwriter
import openai

# -----------------------
# App configuration
# -----------------------
APP_NAME = "OptiFin"
TAGLINE = "Actionable AI financial advice — investment & tax insights"
LOGO_TEXT = "OPTIFIN"
st.set_page_config(page_title=APP_NAME, page_icon="💼", layout="wide")

# -----------------------
# CSS and visual helpers
# -----------------------
BG_IMAGE_URL = "https://images.unsplash.com/photo-1496307042754-b4aa456c4a2d?auto=format&fit=crop&w=1470&q=80"

st.markdown(f"""
<style>
:root {{
  --panel-bg: rgba(255,255,255,0.95);
  --muted: #5b6b77;
  --accent: #0b5fff;
}}
body, .stApp {{
  background-image: url('{BG_IMAGE_URL}');
  background-size: cover;
  background-position: center;
}}

.translucent-card {{
  background: var(--panel-bg);
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(10,20,40,0.08);
}}

.header-left {{ font-weight:800; color:#0b2d4f; font-size:20px; }}
.header-sub {{ color:var(--muted); font-size:0.95rem; }}

.small-note {{ color:var(--muted); font-size:0.9rem; }}

.input-style input, .input-style textarea {{
  background: rgba(255,255,255,0.98) !important;
  color: #000 !important;
}}

.btn-primary > button {{
  background-color: #0b5fff !important;
  color: white !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
  font-weight:700 !important;
}}

.ai-insight {{
  background: linear-gradient(180deg,#ffffff,#f6fbff);
  border-left: 4px solid #0b5fff;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 6px 18px rgba(10,30,70,0.04);
}}

.kpi {{
  padding:10px; border-radius:10px; background:#f6f9ff; text-align:center;
}}
</style>
""", unsafe_allow_html=True)

# -----------------------
# Helpers
# -----------------------
def ensure_secret(key):
    v = st.secrets.get(key, None)
    return v

OPENAI_KEY = ensure_secret("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

def pretty_money(x):
    try:
        return f"R {float(x):,.0f}"
    except:
        return str(x)

def parse_num(x):
    if x is None: return 0.0
    if isinstance(x, (int,float)): return float(x)
    s = str(x).strip()
    if s == "": return 0.0
    s2 = s.replace(",", "").replace("R","").replace("$","")
    try:
        return float(s2)
    except:
        return 0.0

def call_gpt(prompt, max_tokens=400, temp=0.15):
    if not OPENAI_KEY:
        raise RuntimeError("OpenAI key not set")
    resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens, temperature=temp)
    return resp.choices[0].text.strip()

# -----------------------
# Prevent duplicate keys: central key helper
# -----------------------
def k(name):
    # central key generator to make unique keys predictable
    # include user id if available to avoid collisions across users in same session
    uid = st.session_state.get("user_id","")
    return f"{name}__{uid}"

# -----------------------
# Session defaults
# -----------------------
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False
if "page" not in st.session_state:
    st.session_state.page = "privacy"
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "inputs" not in st.session_state:
    st.session_state.inputs = {}
if "advice" not in st.session_state:
    st.session_state.advice = ""
if "market_snapshot" not in st.session_state:
    st.session_state.market_snapshot = ""
if "latest_etf_recs" not in st.session_state:
    st.session_state.latest_etf_recs = []
if "user_id" not in st.session_state:
    st.session_state.user_id = str(int(datetime.datetime.now().timestamp()))

# -----------------------
# Privacy page — one-click accept
# -----------------------
def privacy_page():
    st.markdown("<div class='translucent-card'>", unsafe_allow_html=True)
    cols = st.columns([3,1])
    with cols[0]:
        st.markdown(f"<div class='header-left'>{LOGO_TEXT} — {APP_NAME}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='header-sub'>{TAGLINE}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
        <div class="small-note">
        <p><b>Privacy & Legal (summary)</b></p>
        <p>All information you provide is stored securely and is used to generate personalised financial advice and exports.
        By clicking <b>Accept & Continue</b> you consent to the use of your data for these purposes. OptiFin provides
        informational guidance — concrete implementation requires engagement with our professional services. We do not
        sell your personal data.</p>
        <p>If you do not accept, you will be redirected away and your data will not be stored.</p>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        # show a clear Accept button — one-click should suffice
        st.write("")
        st.write("")
        if st.button("Accept & Continue", key=k("privacy_accept_btn")):
            st.session_state.privacy_accepted = True
            # pre-fetch market snapshot
            try:
                st.session_state.market_snapshot = get_market_snapshot()
            except:
                st.session_state.market_snapshot = "Market snapshot unavailable."
            st.session_state.page = "home"
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Market Data helpers (yfinance)
# -----------------------
ETF_UNIVERSE = {
    "VTI":"VTI", "SPY":"SPY", "ACWI":"ACWI", "IEV":"IEV", "EEM":"EEM",
    "BND":"BND", "AGG":"AGG", "TIP":"TIP", "VNQ":"VNQ", "IAU":"IAU"
}
STOCK_SAMPLE = ["AAPL","MSFT","TSLA","AMZN","NVDA","JPM","BHP.AX"]  # includes a foreign ticker (BHP.AX) as example

def get_market_snapshot():
    # quick snapshot for home page: SPY 1d, VTI 1d
    try:
        tickers = ["SPY","VTI","^GSPC"]
        df = yf.download(tickers, period="5d", threads=False, progress=False)
        parts = []
        for t in tickers:
            try:
                latest = df[t]['Close'].iloc[-1]
                parts.append(f"{t} {latest:,.0f}")
            except Exception:
                pass
        return " | ".join(parts) if parts else "Market snapshot unavailable."
    except Exception:
        return "Market snapshot unavailable."

def compute_ticker_metrics(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y", interval="1d", actions=False)
        if hist is None or hist.empty:
            return None
        latest = hist['Close'].iloc[-1]
        # returns
        start_3m = hist['Close'].iloc[-63] if len(hist)>=63 else hist['Close'].iloc[0]
        ret_3m = latest / start_3m - 1
        start_12m = hist['Close'].iloc[0]
        ret_12m = latest / start_12m - 1
        daily = hist['Close'].pct_change().dropna()
        vol = daily.std() * math.sqrt(252) if not daily.empty else 0.0
        ma50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist)>=50 else None
        ma200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist)>=200 else None
        return {
            "ticker": ticker,
            "latest": latest,
            "ret_3m": ret_3m,
            "ret_12m": ret_12m,
            "vol": vol,
            "ma50": ma50,
            "ma200": ma200
        }
    except Exception:
        return None

def rank_etfs(profile="moderate", limit=6):
    rows = []
    for name,ticker in ETF_UNIVERSE.items():
        metrics = compute_ticker_metrics(ticker)
        if metrics:
            metrics['name'] = name
            rows.append(metrics)
    if not rows:
        return []
    df = pd.DataFrame(rows)
    if profile.lower()=="low":
        df['score'] = (-df['vol']) + df['ret_12m']*2
    elif profile.lower()=="high":
        df['score'] = df['ret_12m']*3 - df['vol']*0.5
    else:
        df['score'] = df['ret_12m']*2 - df['vol']*0.8
    df = df.sort_values('score', ascending=False)
    recs = df.head(limit).to_dict(orient='records')
    return recs

# -----------------------
# AI / advice generation
# -----------------------
def deterministic_advice(user_type, inputs, market_context):
    adv = []
    if user_type=="individual":
        adv.append("Build a 3–6 month emergency cash reserve before allocating to higher-risk investments.")
        adv.append("Prefer low-cost global ETFs as a core; use small satellite positions for higher return targets.")
        adv.append("Consider tax-advantaged retirement vehicles where available and maximise contributions.")
        adv.append("We can conduct a tax review and model specific savings for you — contact OptiFin to proceed.")
    elif user_type=="household":
        adv.append("Coordinate claimable deductions and education/child credits; check spouse income splitting where legal.")
        adv.append("Automate household savings and prioritise debt repayment on high-interest loans.")
        adv.append("Optimize asset allocation across accounts (tax-advantaged + taxable). Contact us for a household model.")
    else:
        adv.append("Ensure strict bookkeeping and expense tagging; route eligible expenses through the company where appropriate.")
        adv.append("Review owner remuneration strategy (salary vs dividends) to reduce combined tax burden.")
        adv.append("Investigate capital allowances or R&D credits if applicable.")
    return "\n\n".join(adv)

def generate_advice(user_type, inputs, market_context):
    # Build prompt with market context and user inputs
    prompt = f"Market snapshot: {market_context}\nUser type: {user_type}\nInputs:\n"
    for k,v in inputs.items():
        prompt += f"- {k}: {v}\n"
    prompt += ("\nYou are a senior financial advisor. Provide 5 concise, high-quality recommendations focusing on taxes, "
               "investments, and practical next steps. Avoid providing detailed, legal or step-by-step instructions; instead "
               "encourage the user to contact OptiFin for implementation. Include a short prioritized action list and an "
               "estimated potential annual saving (qualitative, not guaranteed).")
    if OPENAI_KEY:
        try:
            text = call_gpt(prompt, max_tokens=500, temp=0.2)
            return text
        except Exception:
            pass
    # fallback
    return deterministic_advice(user_type, inputs, market_context)

# -----------------------
# Projection & visualization helpers
# -----------------------
def project_growth(initial, monthly, years, annual_return):
    # monthly contributions, annual compounding approximated monthly
    r = annual_return/12
    n = years*12
    if r == 0:
        return initial + monthly*n
    fv_init = initial * ((1 + r)**n)
    fv_monthly = monthly * (((1 + r)**n - 1) / r)
    return fv_init + fv_monthly

def small_line_chart_for_ticker(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="1y", interval="1d", actions=False)
        if hist is None or hist.empty:
            return None
        fig, ax = plt.subplots(figsize=(3.2,2.0))
        ax.plot(hist.index, hist['Close'], linewidth=1.2)
        ma50 = hist['Close'].rolling(50).mean()
        ma200 = hist['Close'].rolling(200).mean()
        if len(hist)>=50:
            ax.plot(hist.index, ma50, linewidth=0.9, linestyle='--')
        if len(hist)>=200:
            ax.plot(hist.index, ma200, linewidth=0.9, linestyle=':')
        ax.set_xticks([])
        ax.set_yticks([])
        plt.tight_layout()
        return fig
    except Exception:
        return None

# -----------------------
# Exports: PDF + Excel (branded)
# -----------------------
def build_branded_pdf(user_type, inputs, advice, etf_recs=None):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w,h = letter
    # Header band
    c.setFillColorRGB(0.06,0.20,0.38)
    c.rect(0,h-80,w,80, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, h-50, LOGO_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(40, h-68, APP_NAME + " — " + TAGLINE)
    # body
    y = h - 110
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40,y, f"Client type: {user_type.capitalize()}")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(40,y, "Summary of Inputs:")
    y -= 14
    for k,v in inputs.items():
        text = f"{k}: {v}"
        c.drawString(50,y, text)
        y -= 12
        if y < 140:
            c.showPage()
            y = h - 80
    y -= 6
    c.setFont("Helvetica-Bold", 11); c.drawString(40,y, "AI Advice (high-level)")
    y -= 14
    for line in textwrap.wrap(advice, width=90):
        c.setFont("Helvetica",10); c.drawString(45,y,line)
        y -= 12
        if y < 120:
            c.showPage(); y = h - 80
    if etf_recs:
        y -= 8
        c.setFont("Helvetica-Bold", 11); c.drawString(40,y, "Selected ETF suggestions")
        y -= 14
        for r in etf_recs[:6]:
            row = f"{r.get('ticker')} — 12m {r.get('ret_12m',0)*100:.1f}% — vol {r.get('vol',0)*100:.1f}%"
            c.setFont("Helvetica",10); c.drawString(45,y,row)
            y -= 12
            if y < 120:
                c.showPage(); y = h - 80
    c.save()
    return buf.getvalue()

def build_styled_excel(user_type, inputs, advice, etf_recs=None):
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory': True})
    ws = wb.add_worksheet("OptiFin Report")
    title_fmt = wb.add_format({'bold': True, 'font_size': 16})
    hdr_fmt = wb.add_format({'bold': True, 'bg_color':'#E8EEF8'})
    money_fmt = wb.add_format({'num_format':'#,##0.00'})
    ws.set_column('A:A',35)
    ws.set_column('B:B',30)
    ws.write('A1', LOGO_TEXT + " — " + APP_NAME, title_fmt)
    ws.write('A2', 'Client type', hdr_fmt); ws.write('B2', user_type)
    row = 4
    ws.write(row,0,"Inputs", hdr_fmt); ws.write(row,1,"Value", hdr_fmt); row+=1
    for k,v in inputs.items():
        ws.write(row,0,k)
        val = parse_num(v) if isinstance(v,str) else v
        if isinstance(val,(int,float)) and not math.isnan(val):
            ws.write_number(row,1,val,money_fmt)
        else:
            ws.write(row,1,str(v))
        row += 1
    row += 1
    ws.write(row,0,"AI Advice", hdr_fmt); ws.write(row,1, advice); row += 2
    if etf_recs:
        ws.write(row,0,"ETF Suggestions", hdr_fmt); row+=1
        for r in etf_recs:
            ws.write(row,0, r.get('ticker')); ws.write(row,1, r.get('explain','')); row+=1
    wb.close()
    return out.getvalue()

# -----------------------
# UI Pages
# -----------------------
def page_home():
    st.markdown("<div class='translucent-card'>", unsafe_allow_html=True)
    top_cols = st.columns([3,1])
    with top_cols[0]:
        st.markdown(f"<div class='header-left'>{LOGO_TEXT} — {APP_NAME}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='header-sub'>{TAGLINE}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.write("Quick market snapshot:")
        ms = st.session_state.get("market_snapshot","")
        if not ms:
            ms = get_market_snapshot()
            st.session_state.market_snapshot = ms
        st.markdown(f"**{ms}**")
    with top_cols[1]:
        if st.button("Refresh Market Snapshot", key=k("home_refresh_mkt_btn")):
            st.session_state.market_snapshot = get_market_snapshot()
            st.success("Market snapshot refreshed.")
    st.markdown("---")
    st.write("Describe your need in plain English or choose a category below.")
    qcol = st.columns([4,1])
    with qcol[0]:
        query = st.text_input("Tell OptiFin what you need (e.g., 'I run a cafe, R2M revenue, want to lower tax and expand')", key=k("home_query"))
    with qcol[1]:
        if st.button("Detect & Route", key=k("home_detect_btn")):
            # decide category
            cat = "individual"
            q = str(query or "").lower()
            if any(x in q for x in ["company","business","revenue","employees","profit","invoice"]):
                cat = "business"
            elif any(x in q for x in ["household","family","children","kids","spouse","partner"]):
                cat = "household"
            st.session_state.user_type = cat
            st.session_state.page = "service"
            st.experimental_rerun()

    st.markdown("### Or pick a profile")
    c1,c2,c3 = st.columns(3)
    if c1.button("Individual", key=k("home_ind_btn")):
        st.session_state.user_type = "individual"; st.session_state.page = "service"; st.experimental_rerun()
    if c2.button("Household", key=k("home_hh_btn")):
        st.session_state.user_type = "household"; st.session_state.page = "service"; st.experimental_rerun()
    if c3.button("Business", key=k("home_bus_btn")):
        st.session_state.user_type = "business"; st.session_state.page = "service"; st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def page_service():
    st.markdown("<div class='translucent-card'>", unsafe_allow_html=True)
    st.header(f"{st.session_state.user_type.capitalize()} — Choose Service")
    svc = st.selectbox("Which service do you want?", ["Invest","Tax Optimization","Cashflow & Budget","Full Growth Plan"], key=k("service_select"))
    if st.button("Continue", key=k("service_continue_btn")):
        st.session_state.service_choice = svc
        st.session_state.page = "questions"
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_questions():
    st.markdown("<div class='translucent-card input-style'>", unsafe_allow_html=True)
    st.header(f"{st.session_state.user_type.capitalize()} — Questions")
    # contact details
    st.subheader("Contact (optional for now)")
    name = st.text_input("Full name", key=k("q_name"))
    email = st.text_input("Email", key=k("q_email"))
    phone = st.text_input("Phone", key=k("q_phone"))

    ut = st.session_state.user_type
    inputs = {}
    st.markdown("---")
    if ut == "individual":
        st.subheader("Personal & Financial")
        inputs['Age'] = st.number_input("Age", min_value=16, max_value=120, value=30, key=k("ind_age"))
        inputs['Country'] = st.text_input("Country", key=k("ind_country"))
        inputs['Annual Income'] = st.text_input("Annual Gross Income (R)", key=k("ind_income_q"))
        inputs['Monthly Investable'] = st.text_input("Monthly Investable Amount (R)", key=k("ind_monthly_q"))
        inputs['Current Investable Assets'] = st.text_input("Current investable assets (R)", key=k("ind_assets_q"))
        inputs['Debt (high interest)'] = st.text_input("High-interest Debt (R)", key=k("ind_debt_q"))
        inputs['Risk Tolerance'] = st.selectbox("Risk Tolerance", ["Low","Moderate","High"], key=k("ind_risk_q"))
        inputs['Existing Deductions'] = st.text_area("Existing deductions/reliefs", key=k("ind_deds_q"))
        inputs['Primary Goal'] = st.text_input("Primary financial goal", key=k("ind_goal_q"))
        inputs['Timeframe (years)'] = st.number_input("Timeframe to goal (years)", min_value=1, max_value=60, value=10, key=k("ind_time_q"))
    elif ut == "household":
        st.subheader("Household Details")
        inputs['Household Income'] = st.text_input("Household Annual Income (R)", key=k("hh_income_q"))
        inputs['Children'] = st.number_input("Number of children", min_value=0, key=k("hh_children_q"))
        inputs['Education Costs'] = st.text_input("Annual education/childcare costs (R)", key=k("hh_edu_q"))
        inputs['Household Deductions'] = st.text_input("Total household deductions (R)", key=k("hh_deds_q"))
        inputs['Monthly Investable'] = st.text_input("Monthly investable amount (R)", key=k("hh_monthly_q"))
        inputs['Risk Tolerance'] = st.selectbox("Risk Tolerance", ["Low","Moderate","High"], key=k("hh_risk_q"))
        inputs['Goal & Timeframe'] = st.text_input("Goal & timeframe (years)", key=k("hh_goal_time_q"))
    else:
        st.subheader("Business Details")
        inputs['Revenue'] = st.text_input("Annual Revenue (R)", key=k("bus_revenue_q"))
        inputs['Expenses'] = st.text_input("Annual Expenses (R)", key=k("bus_expenses_q"))
        inputs['Employees'] = st.number_input("Number of Employees", min_value=0, key=k("bus_employees_q"))
        inputs['Business Type'] = st.selectbox("Business Structure", ["Sole Proprietor","Private Company","Partnership","Other"], key=k("bus_type_q"))
        inputs['Owner Pay (12m)'] = st.text_input("Owner pay / draw last 12 months (R)", key=k("bus_ownerpay_q"))
        inputs['Tax Paid (last yr)'] = st.text_input("Tax paid last year (R)", key=k("bus_taxpaid_q"))
        inputs['Monthly CapEx'] = st.text_input("Average monthly capex (R)", key=k("bus_capex_q"))
        inputs['Tax Strategies'] = st.text_area("Existing tax strategies used", key=k("bus_taxes_q"))

    st.markdown("---")
    st.write("By default we show high-level actionable recommendations; to implement them, contact OptiFin.")
    if st.button("Generate Advice & Results", key=k("q_gen_btn")):
        # save inputs to session and route to results
        st.session_state.inputs = inputs
        st.session_state.lead = {"name":name,"email":email,"phone":phone}
        # compute market snapshot fresh
        st.session_state.market_snapshot = get_market_snapshot()
        st.session_state.page = "results"
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def page_results():
    st.markdown("<div class='translucent-card'>", unsafe_allow_html=True)
    ut = st.session_state.user_type
    inputs = st.session_state.get("inputs", {})
    market_ctx = st.session_state.get("market_snapshot","")
    st.header(f"{ut.capitalize()} — Results")
    # Generate advice
    if not st.session_state.advice:
        st.session_state.advice = generate_advice(ut, inputs, market_ctx)
    st.subheader("AI High-Level Advice")
    st.write(st.session_state.advice)

    # Small projection box + scenario
    st.markdown("---")
    st.subheader("Projection scenarios (illustrative)")
    # attempt to parse some inputs for projection; best-effort
    try:
        if ut == "individual":
            initial = parse_num(inputs.get("Current investable assets",0) or inputs.get("Current Investable Assets",0))
            monthly = parse_num(inputs.get("Monthly Investable",0) or inputs.get("Monthly Investable",0))
            years = int(inputs.get("Timeframe (years)",10))
            risk = inputs.get("Risk Tolerance","Moderate")
        elif ut == "household":
            initial = parse_num(inputs.get("Monthly Investable",0))*6
            monthly = parse_num(inputs.get("Monthly Investable",0))
            years = 10
            risk = inputs.get("Risk Tolerance","Moderate")
        else:
            initial = max(0.0, parse_num(inputs.get("Revenue",0)) - parse_num(inputs.get("Expenses",0))) * 0.05
            monthly = parse_num(inputs.get("Monthly CapEx",0))*0.05 if inputs.get("Monthly CapEx",None) is not None else 0.0
            years = 7
            risk = "Moderate"
    except Exception:
        initial = 0; monthly = 0; years = 7; risk = "Moderate"

    rate_map = {"Low":0.04,"Moderate":0.07,"High":0.1}
    base = rate_map.get(str(risk),"0.07")
    scenarios = {
        "Conservative": base-0.02,
        "Baseline": base,
        "Aggressive": base+0.03
    }
    scen_results = {name: project_growth(initial, monthly, years, r) for name,r in scenarios.items()}

    left, right = st.columns([2,1])
    with left:
        fig, ax = plt.subplots(figsize=(5.5,2.4))
        names = list(scen_results.keys())
        vals = [scen_results[n] for n in names]
        ax.plot(names, vals, marker='o', linewidth=1.6)
        ax.set_ylabel("Projected Value (R)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"R {v:,.0f}"))
        ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.6)
        st.pyplot(fig, clear_figure=True)
    with right:
        st.markdown("<div class='ai-insight'><b>Projection Insight</b><br>")
        st.write(f"Baseline ({base*100:.1f}%) projected value in {years} years: **{pretty_money(scen_results['Baseline'])}**")
        st.write("These are illustrative projections. Contact OptiFin for legally compliant, personalised modelling.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ETF recommendations
    st.markdown("---")
    st.subheader("Market-aware ETF suggestions")
    profile = st.selectbox("Risk profile for ETF suggestions", ["Low","Moderate","High"], index=1, key=k("etf_profile"))
    if st.button("Refresh ETF Recommendations", key=k("refresh_etf_btn")):
        with st.spinner("Fetching ETF metrics..."):
            recs = rank_etfs(profile.lower())
            # attach explanation
            formatted = []
            for r in recs:
                r['explain'] = f"{r['ticker']}: 12m {r['ret_12m']*100:.1f}% | 3m {r['ret_3m']*100:.1f}% | vol {r['vol']*100:.1f}%"
                formatted.append(r)
            st.session_state.latest_etf_recs = formatted
            st.success("ETF recommendations updated.")
    recs = st.session_state.get("latest_etf_recs", [])
    if recs:
        for r in recs:
            cols = st.columns([1,3,1])
            with cols[0]:
                fig = small_line_chart_for_ticker(r['ticker'])
                if fig:
                    st.pyplot(fig, clear_figure=True)
            with cols[1]:
                st.markdown(f"**{r['ticker']}** — {r.get('explain')}")
            with cols[2]:
                st.write("")  # placeholder for small CTA/icon
    else:
        st.info("No ETF recommendations yet — click 'Refresh ETF Recommendations'.")

    # quick stock suggestions based on sample
    st.markdown("---")
    st.subheader("Top current stock movers (sample quick view)")
    if st.button("Fetch stock sample metrics", key=k("fetch_stock_sample_btn")):
        with st.spinner("Fetching sample stock metrics..."):
            rows = []
            for tk in STOCK_SAMPLE:
                m = compute_ticker_metrics(tk)
                if m:
                    rows.append({"ticker":m['ticker'], "12m":f"{m['ret_12m']*100:.1f}%", "vol":f"{m['vol']*100:.1f}%"})
            st.table(pd.DataFrame(rows))
    # CTA & exports
    st.markdown("---")
    st.subheader("Branded Exports & Contact")
    left, right = st.columns([2,1])
    with left:
        if st.button("Download Branded PDF", key=k("dl_pdf_btn")):
            pdf = build_branded_pdf(ut, inputs, st.session_state.advice, st.session_state.get("latest_etf_recs",[]))
            st.download_button("Download PDF", data=pdf, file_name=f"OptiFin_Report_{ut}.pdf", key=k("download_pdf"))
        if st.button("Download Branded Excel", key=k("dl_xlsx_btn")):
            xlsx = build_styled_excel(ut, inputs, st.session_state.advice, st.session_state.get("latest_etf_recs",[]))
            st.download_button("Download Excel", data=xlsx, file_name=f"OptiFin_Report_{ut}.xlsx", key=k("download_xlsx"))
    with right:
        st.markdown("<div class='ai-insight'><b>Want Implementation?</b><br>Contact OptiFin for full model building & tax implementation. We charge for implementation but provide the quantified savings and action plan.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Top-level app router
# -----------------------
def app():
    # top nav
    st.sidebar.markdown(f"### {APP_NAME}")
    st.sidebar.write(TAGLINE)
    page = st.sidebar.radio("Navigate", options=["Home","Service","Questions","Results"], index=0, key=k("sidebar_nav"))
    # map radio selection to pages
    if page == "Home":
        st.session_state.page = "home"
    elif page == "Service":
        st.session_state.page = "service"
    elif page == "Questions":
        st.session_state.page = "questions"
    elif page == "Results":
        st.session_state.page = "results"

    if not st.session_state.privacy_accepted and st.session_state.page!="privacy":
        # show the privacy page first (force)
        st.session_state.page = "privacy"

    # Route
    if st.session_state.page == "privacy":
        privacy_page()
    elif st.session_state.page == "home":
        page_home()
    elif st.session_state.page == "service":
        page_service()
    elif st.session_state.page == "questions":
        page_questions()
    elif st.session_state.page == "results":
        page_results()
    else:
        page_home()

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app()

# -----------------------
# Requirements (to add to requirements.txt)
# -----------------------
# streamlit
# pandas
# numpy
# matplotlib
# yfinance
# xlsxwriter
# reportlab
# openai
