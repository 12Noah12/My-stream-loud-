# app.py - OptiFin (Integrated production-ready single-file Streamlit app)
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import yfinance as yf
import io, math, datetime, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import xlsxwriter
import openai
import base64

# -------------------------
# App meta and config
# -------------------------
APP_NAME = "OptiFin"
TAGLINE = "AI-driven investment, tax & retirement planning"
LOGO = "OPTIFIN"
st.set_page_config(page_title=APP_NAME, page_icon="💼", layout="wide")

# -------------------------
# Visual CSS – high contrast translucent panels
# -------------------------
BG = "https://images.unsplash.com/photo-1496307042754-b4aa456c4a2d?auto=format&fit=crop&w=1470&q=80"
st.markdown(f"""
<style>
:root {{--accent:#0b5fff; --muted:#6b7785; --panel: rgba(255,255,255,0.96); --darkpanel: rgba(12,20,36,0.85);}}
body, .stApp {{ background-image: url('{BG}'); background-size: cover; background-position: center; }}
.translucent {{ background: var(--panel); padding:20px; border-radius:12px; box-shadow: 0 12px 30px rgba(8,12,20,0.12); color: #071022; }}
.translucent-dark {{ background: var(--darkpanel); padding:18px; border-radius:12px; box-shadow: 0 12px 30px rgba(0,0,0,0.35); color: #fff; }}
.header {{ font-weight:800; color:#07213f; font-size:20px; }}
.sub {{ color:var(--muted); font-size:0.95rem; }}
.small {{ color:var(--muted); font-size:0.9rem; }}
.input-white input, .input-white textarea {{ background: #fff !important; color:#071022 !important; }}
.ai-box {{ background: linear-gradient(180deg,#ffffff,#f6fbff); border-left: 4px solid var(--accent); padding:12px; border-radius:8px; }}
.kpi {{ padding:10px; border-radius:10px; background:#f6f9ff; text-align:center; }}
.btn-primary > button {{ background-color: var(--accent) !important; color: white !important; font-weight:700 !important; border-radius:8px !important; padding:8px 12px !important; }}
.small-note {{ font-size:0.95rem; color:#13213a; }}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Stable key generator to avoid duplicate widget IDs
# -------------------------
def key(name: str):
    """Return a stable unique key per page + name to avoid duplicate element ids."""
    page = st.session_state.get("page", "main")
    return f"{page}__{name}"

# -------------------------
# Session defaults
# -------------------------
if "page" not in st.session_state: st.session_state.page = "privacy"
if "privacy_accepted" not in st.session_state: st.session_state.privacy_accepted = False
if "user_type" not in st.session_state: st.session_state.user_type = None
if "service_choice" not in st.session_state: st.session_state.service_choice = None
if "inputs" not in st.session_state: st.session_state.inputs = {}
if "advice" not in st.session_state: st.session_state.advice = ""
if "market_snapshot" not in st.session_state: st.session_state.market_snapshot = ""
if "latest_etf_recs" not in st.session_state: st.session_state.latest_etf_recs = []
if "user_id" not in st.session_state: st.session_state.user_id = str(int(datetime.datetime.now().timestamp()))

# -------------------------
# OpenAI (optional)
# -------------------------
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

def call_gpt(prompt: str, max_tokens=300, temp=0.15):
    if not OPENAI_KEY:
        raise RuntimeError("OpenAI key not set")
    resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=max_tokens, temperature=temp)
    return resp.choices[0].text.strip()

# -------------------------
# Utilities
# -------------------------
def parse_num(x):
    if x is None: return 0.0
    if isinstance(x, (int,float)): return float(x)
    s = str(x).replace(",", "").replace("R","").replace("$","").strip()
    if s == "": return 0.0
    try:
        return float(s)
    except:
        return 0.0

def pretty_money(x):
    try:
        return f"R {float(x):,.0f}"
    except:
        return str(x)

# -------------------------
# Market helpers (yfinance)
# -------------------------
ETF_UNIVERSE = ["VTI","SPY","ACWI","EEM","IEV","BND","AGG","TIP","VNQ","IAU"]
SAMPLE_STOCKS = ["AAPL","MSFT","NVDA","AMZN","TSLA","JPM"]

def get_market_snapshot():
    try:
        tickers = ["SPY","VTI","^GSPC"]
        df = yf.download(tickers, period="5d", progress=False, threads=False)
        parts = []
        for t in tickers:
            try:
                close = df[t]['Close'].iloc[-1]
                parts.append(f"{t} {close:,.0f}")
            except Exception:
                pass
        return " | ".join(parts) if parts else "Unavailable"
    except Exception:
        return "Unavailable"

def compute_ticker_metrics(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y", interval="1d", actions=False)
        if hist is None or hist.empty: return None
        latest = hist['Close'].iloc[-1]
        ret_3m = latest / hist['Close'].iloc[-63] - 1 if len(hist) >= 63 else 0.0
        ret_12m = latest / hist['Close'].iloc[0] - 1 if len(hist) > 0 else 0.0
        daily = hist['Close'].pct_change().dropna()
        vol = daily.std() * math.sqrt(252) if not daily.empty else 0.0
        ma50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None
        ma200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else None
        return {"ticker":ticker,"latest":latest,"ret_3m":ret_3m,"ret_12m":ret_12m,"vol":vol,"ma50":ma50,"ma200":ma200}
    except Exception:
        return None

def rank_etfs(profile="Moderate", limit=6):
    rows=[]
    for tk in ETF_UNIVERSE:
        m = compute_ticker_metrics(tk)
        if m: rows.append(m)
    if not rows: return []
    df = pd.DataFrame(rows)
    if profile.lower()=="low":
        df['score'] = -df['vol'] + df['ret_12m']*2
    elif profile.lower()=="high":
        df['score'] = df['ret_12m']*3 - df['vol']*0.5
    else:
        df['score'] = df['ret_12m']*2 - df['vol']*0.8
    df = df.sort_values('score', ascending=False)
    recs = df.head(limit).to_dict(orient='records')
    for r in recs:
        r['explain'] = f"{r['ticker']}: 12m {r['ret_12m']*100:.1f}% | vol {r['vol']*100:.1f}%"
    return recs

# -------------------------
# Deterministic fallback advice
# -------------------------
def deterministic_advice(user_type, inputs, market_snapshot):
    if user_type == "individual":
        return ("• Build a 3–6 month emergency fund before allocating to higher-risk investments.\n"
                "• Use a low-cost global ETF core and small satellite positions for higher returns.\n"
                "• Maximise local tax-advantaged retirement accounts where available.\n\nContact OptiFin for implementation and detailed modelling.")
    elif user_type == "household":
        return ("• Coordinate household tax allowances & family-oriented credits.\n"
                "• Automate household savings and prioritise high-interest debt repayment.\n"
                "• Consider splitting investments across tax-advantaged and taxable accounts.\n\nContact OptiFin for modelling & implementation.")
    else:
        return ("• Ensure strict bookkeeping and correct expense tagging; use company cards for eligible expenses.\n"
                "• Review owner remuneration strategy (salary vs dividends) to optimize tax.\n"
                "• Explore capital allowances and R&D credits if applicable.\n\nContact OptiFin to implement.")

# -------------------------
# GPT wrapper with fallback
# -------------------------
def generate_advice(user_type, inputs, market_snapshot):
    # Compose a high-quality prompt when OpenAI is available
    if OPENAI_KEY:
        prompt = f"Market snapshot: {market_snapshot}\nUser type: {user_type}\nInputs:\n"
        for k,v in inputs.items():
            prompt += f"- {k}: {v}\n"
        prompt += ("\nYou are a senior financial advisor. Provide 5 concise recommendations focusing on tax savings, "
                   "investment allocation, and a short prioritized action plan. Do not provide step-by-step actionable implementation that bypasses professional services. "
                   "End with a short estimate of potential annual savings (qualitative) and a single-line CTA to contact a professional.")
        try:
            text = call_gpt(prompt, max_tokens=450, temp=0.15)
            return text
        except Exception:
            return deterministic_advice(user_type, inputs, market_snapshot)
    else:
        return deterministic_advice(user_type, inputs, market_snapshot)

# -------------------------
# Projection helper
# -------------------------
def project_growth(initial, monthly, years, annual_return):
    r = annual_return / 12
    n = years * 12
    if r == 0:
        return initial + monthly * n
    fv_init = initial * ((1 + r) ** n)
    fv_monthly = monthly * (((1 + r) ** n - 1) / r)
    return fv_init + fv_monthly

# -------------------------
# PDF & Excel exports
# -------------------------
def build_branded_pdf(user_type, inputs, advice, etf_recs=None):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w,h = letter
    # Header band
    c.setFillColorRGB(0.06,0.20,0.38)
    c.rect(0,h-80,w,80, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, h-50, LOGO)
    c.setFont("Helvetica", 10)
    c.drawString(40, h-68, APP_NAME + " — " + TAGLINE)
    # Body
    y = h - 110
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"Client type: {user_type.capitalize()}")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Summary of Inputs:")
    y -= 14
    for k,v in inputs.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 12
        if y < 120:
            c.showPage(); y = h - 80
    y -= 6
    c.setFont("Helvetica-Bold", 11); c.drawString(40, y, "AI Advice (high-level)")
    y -= 14
    for line in textwrap.wrap(advice, width=90):
        c.setFont("Helvetica",10); c.drawString(45, y, line); y -= 12
        if y < 120:
            c.showPage(); y = h - 80
    if etf_recs:
        y -= 8
        c.setFont("Helvetica-Bold", 11); c.drawString(40, y, "ETF suggestions")
        y -= 14
        for r in etf_recs[:6]:
            row = f"{r.get('ticker')} — 12m {r.get('ret_12m',0)*100:.1f}% — vol {r.get('vol',0)*100:.1f}%"
            c.setFont("Helvetica",10); c.drawString(45, y, row)
            y -= 12
            if y < 120:
                c.showPage(); y = h - 80
    c.save()
    return buf.getvalue()

def build_styled_excel(user_type, inputs, advice, etf_recs=None):
    out = io.BytesIO()
    workbook = xlsxwriter.Workbook(out, {'in_memory': True})
    worksheet = workbook.add_worksheet("OptiFin Report")
    header_format = workbook.add_format({'bold': True, 'font_color': 'blue', 'font_size': 14})
    worksheet.write('A1', LOGO + " — " + APP_NAME, header_format)
    worksheet.write('A2', 'Client Type')
    worksheet.write('B2', user_type)
    row = 4
    worksheet.write(row,0, "Inputs", workbook.add_format({'bold':True}))
    worksheet.write(row,1, "Value", workbook.add_format({'bold':True}))
    row += 1
    for k,v in inputs.items():
        worksheet.write(row,0,k)
        try:
            num = parse_num(v) if isinstance(v,str) else v
            if isinstance(num, (int,float)) and not np.isnan(num):
                worksheet.write_number(row,1, float(num))
            else:
                worksheet.write(row,1, str(v))
        except:
            worksheet.write(row,1,str(v))
        row += 1
    row += 1
    worksheet.write(row,0,"AI Advice", workbook.add_format({'bold':True}))
    worksheet.write(row,1, advice)
    row += 2
    if etf_recs:
        worksheet.write(row,0,"ETF Suggestions", workbook.add_format({'bold':True}))
        row += 1
        for r in etf_recs:
            worksheet.write(row,0, r.get('ticker'))
            worksheet.write(row,1, r.get('explain',''))
            row += 1
    workbook.close()
    return out.getvalue()

# -------------------------
# UI Pages
# -------------------------
def page_privacy():
    st.markdown("<div class='translucent'>", unsafe_allow_html=True)
    st.markdown(f"<div class='header'>{LOGO} — {APP_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub'>{TAGLINE}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div class='small'>
    <p><b>Privacy summary:</b> Your information is securely stored. By accepting, you agree we may use your inputs to generate personalised financial advice and exports. Implementation of tax or investment actions requires professional engagement. If you do not accept, you will be redirected away and your data will not be stored.</p>
    </div>
    """, unsafe_allow_html=True)
    # Use form for one-click acceptance to avoid double-click issues
    with st.form(key=key("privacy_form")):
        accept = st.form_submit_button("Accept & Continue")
        if accept:
            st.session_state.privacy_accepted = True
            st.session_state.market_snapshot = get_market_snapshot()
            st.session_state.page = "home"
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_home():
    st.markdown("<div class='translucent'>", unsafe_allow_html=True)
    st.markdown(f"<div class='header'>{LOGO} — {APP_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub'>{TAGLINE}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.write("Market snapshot (quick):")
    ms = st.session_state.get("market_snapshot","")
    if not ms:
        ms = get_market_snapshot()
        st.session_state.market_snapshot = ms
    st.markdown(f"**{ms}**")
    st.markdown("---")
    st.write("Describe your need or pick a profile below.")
    cols = st.columns([4,1])
    with cols[0]:
        query = st.text_input("Tell OptiFin what you need (e.g., 'I need to lower tax and grow retirement', 'I run a small business...')", key=key("home_query"))
    with cols[1]:
        if st.button("Detect & Route", key=key("home_detect")):
            q = (query or "").lower()
            cat = "individual"
            if any(x in q for x in ["company","business","revenue","employees","invoice","profit","vat"]):
                cat = "business"
            elif any(x in q for x in ["family","household","children","kids","spouse","partner"]):
                cat = "household"
            st.session_state.user_type = cat
            st.session_state.page = "service"
            st.experimental_rerun()

    st.markdown("### Or select profile")
    c1,c2,c3 = st.columns(3)
    if c1.button("Individual", key=key("home_ind")):
        st.session_state.user_type = "individual"; st.session_state.page = "service"; st.experimental_rerun()
    if c2.button("Household", key=key("home_hh")):
        st.session_state.user_type = "household"; st.session_state.page = "service"; st.experimental_rerun()
    if c3.button("Business", key=key("home_bus")):
        st.session_state.user_type = "business"; st.session_state.page = "service"; st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_service():
    st.markdown("<div class='translucent'>", unsafe_allow_html=True)
    st.header(f"{st.session_state.user_type.capitalize()} — Choose Service")
    svc = st.selectbox("Which service do you want?", ["Invest","Tax Optimization","Retirement & Planner","Cashflow & Budget","Full Growth Plan"], key=key("service_select"))
    if st.button("Continue", key=key("service_continue")):
        st.session_state.service_choice = svc
        st.session_state.page = "questions"
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_questions():
    st.markdown("<div class='translucent input-white'>", unsafe_allow_html=True)
    st.header(f"{st.session_state.user_type.capitalize()} — Questions")
    # Contact
    st.subheader("Contact (optional)")
    name = st.text_input("Full name", key=key("q_name"))
    email = st.text_input("Email", key=key("q_email"))
    phone = st.text_input("Phone", key=key("q_phone"))

    inputs = {}
    ut = st.session_state.user_type
    st.markdown("---")
    if ut == "individual":
        st.subheader("Personal & Financial")
        inputs["Age"] = st.number_input("Age", min_value=16, max_value=100, key=key("ind_age"))
        inputs["Annual Income"] = st.text_input("Annual Gross Income (R)", key=key("ind_income"))
        inputs["Monthly Investable"] = st.text_input("Monthly Investable Amount (R)", key=key("ind_monthly"))
        inputs["Current Investable Assets"] = st.text_input("Current investable assets (R)", key=key("ind_assets"))
        inputs["Debt (high interest)"] = st.text_input("High-interest Debt (R)", key=key("ind_debt"))
        inputs["Risk Tolerance"] = st.selectbox("Risk Tolerance", ["Low","Moderate","High"], key=key("ind_risk"))
        inputs["Existing Deductions"] = st.text_area("Existing deductions (brief)", key=key("ind_deds"))
        inputs["Primary Goal"] = st.text_input("Primary goal (e.g., buy house in 5 years)", key=key("ind_goal"))
        inputs["Retirement Target Amount"] = st.text_input("Retirement goal amount (R)", key=key("ind_ret_goal"))
        inputs["Retirement Target Age"] = st.number_input("Retirement target age", min_value=30, max_value=100, value=65, key=key("ind_ret_age"))
    elif ut == "household":
        st.subheader("Household")
        inputs["Household Income"] = st.text_input("Household Annual Income (R)", key=key("hh_income"))
        inputs["Number of Children"] = st.number_input("Number of children", min_value=0, key=key("hh_children"))
        inputs["Monthly Investable"] = st.text_input("Monthly investable amount (R)", key=key("hh_monthly"))
        inputs["Existing Deductions"] = st.text_area("Existing household deductions", key=key("hh_deds"))
        inputs["Risk Tolerance"] = st.selectbox("Risk Tolerance", ["Low","Moderate","High"], key=key("hh_risk"))
        inputs["Retirement Target Amount"] = st.text_input("Household retirement target amount (R)", key=key("hh_ret_goal"))
        inputs["Retirement Target Age"] = st.number_input("Household retirement age target", min_value=30, max_value=100, value=65, key=key("hh_ret_age"))
    else:
        st.subheader("Business")
        inputs["Annual Revenue"] = st.text_input("Annual Revenue (R)", key=key("bus_rev"))
        inputs["Annual Expenses"] = st.text_input("Annual Expenses (R)", key=key("bus_exp"))
        inputs["Number of Employees"] = st.number_input("Number of employees", min_value=0, key=key("bus_emps"))
        inputs["Business Structure"] = st.selectbox("Business Structure", ["Sole Proprietor","Private Company","Partnership","Other"], key=key("bus_struct"))
        inputs["Owner Pay Last 12m"] = st.text_input("Owner pay last 12 months (R)", key=key("bus_ownerpay"))
        inputs["Tax Paid Last Year"] = st.text_input("Tax paid last year (R)", key=key("bus_taxpaid"))
        inputs["Existing Tax Strategies"] = st.text_area("Existing tax strategies (brief)", key=key("bus_taxes"))
    st.markdown("---")
    if st.button("Generate Advice & Results", key=key("q_submit")):
        st.session_state.inputs = inputs
        st.session_state.lead = {"name":name,"email":email,"phone":phone}
        st.session_state.market_snapshot = get_market_snapshot()
        st.session_state.page = "results"
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_results():
    st.markdown("<div class='translucent'>", unsafe_allow_html=True)
    ut = st.session_state.user_type
    inputs = st.session_state.get("inputs",{})
    market_ctx = st.session_state.get("market_snapshot","")
    st.header(f"{ut.capitalize()} — Results & Planner")
    if not st.session_state.advice:
        st.session_state.advice = generate_advice(ut, inputs, market_ctx)
    st.subheader("AI High-Level Advice")
    st.write(st.session_state.advice)

    # Retirement & Investment Planner (for individual & household)
    st.markdown("---")
    st.subheader("Retirement & Investment Planner")
    # default parse values
    if ut == "individual":
        current_assets = parse_num(inputs.get("Current Investable Assets", 0) or inputs.get("Current investable assets",0))
        monthly_invest = parse_num(inputs.get("Monthly Investable", 0) or inputs.get("Monthly Investable",0) or inputs.get("Monthly investable amount (R)",0))
        goal_amount = parse_num(inputs.get("Retirement Target Amount",0) or inputs.get("Retirement target amount (R)",0))
        target_age = int(inputs.get("Retirement Target Age", inputs.get("Retirement Target Age",65)))
        age = int(inputs.get("Age",30))
    elif ut == "household":
        current_assets = parse_num(inputs.get("Current Investments",0))
        monthly_invest = parse_num(inputs.get("Monthly Investable",0) or inputs.get("Monthly investable amount (R)",0))
        goal_amount = parse_num(inputs.get("Retirement Target Amount",0) or inputs.get("Household retirement target amount (R)",0))
        target_age = int(inputs.get("Retirement Target Age", inputs.get("Retirement Target Age",65)))
        age = 35
    else:
        current_assets = parse_num(inputs.get("Annual Revenue",0)) * 0.05
        monthly_invest = parse_num(inputs.get("Annual Revenue",0)) * 0.01
        goal_amount = 0
        target_age = 65
        age = 40

    # risk mapping
    rt = inputs.get("Risk Tolerance","Moderate") if inputs else "Moderate"
    rate_map = {"Low":0.04,"Moderate":0.07,"High":0.1}
    assumed_return = rate_map.get(rt, 0.07)
    years_to_go = max(1, target_age - age)
    # compute required monthly contribution to reach goal (if goal > 0), else show projection charts
    if goal_amount > 0:
        # formula to solve monthly contribution needed (approximate, using monthly compounding)
        initial = current_assets
        desired = goal_amount
        r = assumed_return / 12
        n = years_to_go * 12
        # monthly contribution c solving: desired = initial*(1+r)^n + c*(((1+r)^n - 1)/r)
        if r == 0:
            required_monthly = max(0.0, (desired - initial) / n)
        else:
            required_monthly = max(0.0, (desired - initial * ((1 + r) ** n)) * r / (((1 + r) ** n) - 1))
        st.markdown(f"**Assumed annual return:** {assumed_return*100:.1f}% based on risk tolerance ({rt})")
        st.markdown(f"**Years to target:** {years_to_go} years")
        st.markdown(f"**Required monthly contribution to reach R{goal_amount:,.0f} by age {target_age}:** **{pretty_money(required_monthly)}**")
        st.markdown(f"**Your current monthly contribution (entered):** {pretty_money(monthly_invest)}")
        gap = required_monthly - monthly_invest
        if gap > 0:
            st.warning(f"You are R{gap:,.0f} per month short of the target. FinAI suggests increasing monthly savings or adjusting the goal/timeframe.")
        else:
            st.success("You are on track for the stated retirement target (based on assumed returns).")

    # projection mini-charts and AI insight box
    st.markdown("---")
    col_left, col_right = st.columns([2,1])
    with col_left:
        st.subheader("Projection scenarios")
        scen_rates = {"Conservative": assumed_return-0.02, "Baseline": assumed_return, "Aggressive": assumed_return+0.03}
        scen_values = {k: project_growth(current_assets, monthly_invest, years_to_go, r) for k,r in scen_rates.items()}
        fig, ax = plt.subplots(figsize=(6,2.4))
        ax.plot(list(scen_values.keys()), [scen_values[k] for k in scen_values.keys()], marker='o', linewidth=1.6)
        ax.set_ylabel("Projected Value (R)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"R {v:,.0f}"))
        ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
        st.pyplot(fig, clear_figure=True)
    with col_right:
        st.subheader("AI Insight")
        insight_text = ""
        # Prepare input summary for AI/deterministic generator
        summary = {**inputs, "Assumed annual return": f"{assumed_return*100:.1f}%", "Years to target": years_to_go}
        if OPENAI_KEY:
            try:
                prompt = f"Market snapshot: {market_ctx}\nUser type: {ut}\nInputs:\n"
                for k,v in summary.items():
                    prompt += f"- {k}: {v}\n"
                prompt += ("\nYou are a senior financial advisor. Provide 4 concise recommendations focused on investments, "
                           "retirement contributions, and tax-efficient allocations. Offer a short prioritized action list and a qualitative estimate of potential savings or gains. Do not include full implementation details; encourage contacting OptiFin.")
                insight_text = call_gpt(prompt, max_tokens=300, temp=0.15)
            except Exception:
                insight_text = deterministic_advice(ut, inputs, market_ctx)
        else:
            insight_text = deterministic_advice(ut, inputs, market_ctx)
        st.markdown(f"<div class='ai-box'>{insight_text}</div>", unsafe_allow_html=True)

    # ETF recommendations
    st.markdown("---")
    st.subheader("ETF Suggestions (market-aware)")
    prof = st.selectbox("Risk profile for ETF suggestions", ["Low","Moderate","High"], index=1, key=key("etf_prof"))
    if st.button("Compute ETF shortlist", key=key("etf_compute")):
        with st.spinner("Computing ETF shortlist..."):
            recs = rank_etfs(prof, limit=6)
            st.session_state.latest_etf_recs = recs
    recs = st.session_state.get("latest_etf_recs", [])
    if recs:
        for r in recs:
            cols = st.columns([1,3,1])
            with cols[0]:
                # small sparkline
                try:
                    hist = yf.Ticker(r['ticker']).history(period="6mo", interval="1d", actions=False)
                    if hist is not None and not hist.empty:
                        fig, ax = plt.subplots(figsize=(2.4,1.4))
                        ax.plot(hist.index, hist['Close'], linewidth=1)
                        ax.set_xticks([]); ax.set_yticks([])
                        st.pyplot(fig, clear_figure=True)
                except Exception:
                    pass
            with cols[1]:
                st.markdown(f"**{r['ticker']}** — {r.get('explain')}")
            with cols[2]:
                st.write("")  # placeholder
    else:
        st.info("No ETF shortlist computed yet — click 'Compute ETF shortlist' to run it.")

    # Exports & CTA
    st.markdown("---")
    left, right = st.columns([2,1])
    with left:
        if st.button("Download Branded PDF", key=key("dl_pdf")):
            pdf = build_branded_pdf(ut, inputs, st.session_state.advice, st.session_state.get("latest_etf_recs",[]))
            st.download_button("Download PDF", data=pdf, file_name=f"OptiFin_{ut}_report.pdf", key=key("download_pdf"))
        if st.button("Download Branded Excel", key=key("dl_xlsx")):
            xlsx = build_styled_excel(ut, inputs, st.session_state.advice, st.session_state.get("latest_etf_recs",[]))
            st.download_button("Download Excel", data=xlsx, file_name=f"OptiFin_{ut}_report.xlsx", key=key("download_xlsx"))
    with right:
        st.markdown("<div class='ai-box'><b>Need implementation?</b><br>Contact OptiFin to implement the plan & capture the savings. We build the models and handle compliance.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Router / main app
# -------------------------
def main():
    # sidebar navigation
    st.sidebar.markdown(f"### {APP_NAME}")
    nav_choice = st.sidebar.radio("Navigate", ["Home","Service","Questions","Results"], index=0, key=key("nav"))
    # translate radio to page only when user chooses
    if nav_choice == "Home": st.session_state.page = "home"
    elif nav_choice == "Service": st.session_state.page = "service"
    elif nav_choice == "Questions": st.session_state.page = "questions"
    elif nav_choice == "Results": st.session_state.page = "results"

    # Ensure privacy accepted first
    if not st.session_state.privacy_accepted and st.session_state.page != "privacy":
        st.session_state.page = "privacy"

    if st.session_state.page == "privacy":
        page_privacy()
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

if __name__ == "__main__":
    main()
