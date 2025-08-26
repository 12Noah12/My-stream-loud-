# app.py - OptiFin (Stable, unique-keys, readable overlay, one-click privacy, market snapshot)
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
import os

# ---------------- App meta ----------------
APP_NAME = "OptiFin"
TAGLINE = "Smart, market-aware financial advice"
LOGO = "OPTIFIN"
st.set_page_config(page_title=APP_NAME, page_icon="💼", layout="wide")

# ---------------- Visual CSS (high contrast translucent panels) ----------------
BG = "https://images.unsplash.com/photo-1496307042754-b4aa456c4a2d?auto=format&fit=crop&w=1470&q=80"
st.markdown(f"""
<style>
:root{{--accent:#0b5fff; --muted:#6b7785; --panel: rgba(255,255,255,0.95);}}
body, .stApp {{ background-image: url('{BG}'); background-size: cover; background-position: center; }}
.translucent {{ background: var(--panel); padding:18px; border-radius:12px; box-shadow:0 12px 30px rgba(8,12,20,0.12); }}
.header {{ font-weight:800; color:#0b2d4f; font-size:20px; }}
.sub {{ color:var(--muted); font-size:0.95rem; }}
.small {{ color:var(--muted); font-size:0.9rem; }}
.input-box input, .input-box textarea {{ background: #fff !important; color:#000 !important; }}
.ai-box {{ background: linear-gradient(180deg,#ffffff,#f6fbff); border-left:4px solid var(--accent); padding:12px; border-radius:8px; }}
.btn-primary > button {{ background-color: var(--accent) !important; color: white !important; font-weight:700 !important; border-radius:8px !important; }}
</style>
""", unsafe_allow_html=True)

# ---------------- Key helper ----------------
def key(name: str):
    """Return a stable unique key per page + name to avoid duplicate element ids."""
    page = st.session_state.get("page", "main")
    return f"{page}__{name}"

# ---------------- Session defaults ----------------
if "page" not in st.session_state: st.session_state.page = "privacy"
if "privacy_accepted" not in st.session_state: st.session_state.privacy_accepted = False
if "user_type" not in st.session_state: st.session_state.user_type = None
if "inputs" not in st.session_state: st.session_state.inputs = {}
if "advice" not in st.session_state: st.session_state.advice = ""
if "market_snapshot" not in st.session_state: st.session_state.market_snapshot = ""

# ---------------- OpenAI availability ----------------
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

# ---------------- Utility functions ----------------
def parse_num(x):
    try:
        if x is None: return 0.0
        if isinstance(x, (int,float)): return float(x)
        s = str(x).replace(",", "").replace("R","").replace("$","").strip()
        return float(s) if s != "" else 0.0
    except:
        return 0.0

def pretty(x):
    try:
        return f"R {float(x):,.0f}"
    except:
        return str(x)

# ---------------- Market data helpers ----------------
ETF_UNIVERSE = ["VTI","SPY","ACWI","EEM","IEV","BND","AGG","TIP","VNQ","IAU"]
SAMPLE_STOCKS = ["AAPL","MSFT","NVDA","AMZN","TSLA","JPM"]

def get_market_snapshot():
    try:
        tickers = ["SPY","VTI","^GSPC"]
        df = yf.download(tickers, period="5d", progress=False, threads=False)
        parts = []
        for t in tickers:
            try:
                close = df[t]["Close"].iloc[-1]
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
        ret_3m = latest / hist['Close'].iloc[-63] - 1 if len(hist)>=63 else 0.0
        ret_12m = latest / hist['Close'].iloc[0] - 1 if len(hist)>0 else 0.0
        vol = hist['Close'].pct_change().dropna().std() * math.sqrt(252)
        ma50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist)>=50 else None
        ma200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist)>=200 else None
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
    return df.head(limit).to_dict(orient='records')

# ---------------- Advice functions ----------------
def deterministic_advice(user_type, inputs, market_snapshot):
    if user_type=="individual":
        return ("1) Build a 3-6 month emergency fund before high-risk investing.\n"
                "2) Use a low-cost global ETF core and small satellite positions for higher returns.\n"
                "3) Maximise local tax-advantaged accounts (pension/retirement) if available.\n"
                "Contact OptiFin to run numbers and implement.")
    if user_type=="household":
        return ("1) Coordinate household tax allowances & claimable credits.\n"
                "2) Automate savings and prioritise high-interest debt repayment.\n"
                "3) Use education savings vehicles where beneficial. Contact OptiFin for modelling.")
    return ("1) Strengthen bookkeeping and capture expenses on company cards.\n"
            "2) Review owner remuneration (salary vs dividends) for tax efficiency.\n"
            "3) Investigate capital allowances or R&D incentives. Contact OptiFin to implement.")

def generate_advice(user_type, inputs, market_snapshot):
    # assemble prompt for GPT when available
    if OPENAI_KEY:
        prompt = f"Market snapshot: {market_snapshot}\nUser type: {user_type}\nInputs:\n"
        for k,v in inputs.items(): prompt += f"- {k}: {v}\n"
        prompt += ("\nYou are a seasoned financial advisor. Produce 5 concise recommendations for tax savings, "
                   "investment allocation suggestions based on risk, and 3 prioritized next steps. Do not provide "
                   "implementation steps; encourage contacting the advisory firm for execution.")
        try:
            resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=400, temperature=0.15)
            return resp.choices[0].text.strip()
        except Exception:
            return deterministic_advice(user_type, inputs, market_snapshot)
    else:
        return deterministic_advice(user_type, inputs, market_snapshot)

# ---------------- Exports ----------------
def build_pdf(user_type, inputs, advice, etf_recs=None):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w,h = letter
    # header band
    c.setFillColorRGB(0.06,0.20,0.38)
    c.rect(0,h-80,w,80,fill=1,stroke=0)
    c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",18); c.drawString(40,h-50, LOGO)
    c.setFont("Helvetica",10); c.drawString(40,h-68, APP_NAME + " — " + TAGLINE)
    y = h-110; c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold",12); c.drawString(40,y,f"Client type: {user_type}"); y-=18
    c.setFont("Helvetica",10); c.drawString(40,y,"Inputs:"); y-=14
    for k,v in inputs.items():
        c.drawString(50,y,f"{k}: {v}"); y-=12
        if y<120: c.showPage(); y=h-80
    y-=6; c.setFont("Helvetica-Bold",11); c.drawString(40,y,"AI Advice"); y-=14
    for line in textwrap.wrap(advice, width=90):
        c.setFont("Helvetica",10); c.drawString(45,y,line); y-=12
        if y<120: c.showPage(); y=h-80
    if etf_recs:
        y-=8; c.setFont("Helvetica-Bold",11); c.drawString(40,y,"ETF Picks"); y-=14
        for r in etf_recs:
            row = f"{r['ticker']} — 12m {r['ret_12m']*100:.1f}% | vol {r['vol']*100:.1f}%"
            c.setFont("Helvetica",10); c.drawString(45,y,row); y-=12
            if y<120: c.showPage(); y=h-80
    c.save(); pdf = buf.getvalue(); buf.close()
    return pdf

def build_xlsx(user_type, inputs, advice, etf_recs=None):
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {'in_memory':True})
    ws = wb.add_worksheet("OptiFin Report")
    title = wb.add_format({'bold':True,'font_size':14})
    hdr = wb.add_format({'bold':True,'bg_color':'#E8EEF8'})
    money = wb.add_format({'num_format':'#,##0.00'})
    ws.set_column('A:A',35); ws.set_column('B:B',30)
    ws.write('A1', LOGO + " — " + APP_NAME, title)
    ws.write('A2', 'Client type', hdr); ws.write('B2', user_type)
    r=4; ws.write(r,0,"Inputs",hdr); ws.write(r,1,"Value",hdr); r+=1
    for k,v in inputs.items():
        ws.write(r,0,k)
        try:
            num = parse_num(v) if isinstance(v,str) else v
            if isinstance(num,(int,float)): ws.write_number(r,1,num,money)
            else: ws.write(r,1,str(v))
        except:
            ws.write(r,1,str(v))
        r+=1
    r+=1; ws.write(r,0,"AI Advice",hdr); ws.write(r,1,advice); r+=2
    if etf_recs:
        ws.write(r,0,"ETF Picks",hdr); r+=1
        for rec in etf_recs:
            ws.write(r,0,rec['ticker']); ws.write(r,1,rec.get('explain','')); r+=1
    wb.close(); return out.getvalue()

# ---------------- Pages ----------------
def page_privacy():
    # one-click acceptance using form to avoid double click issues
    st.markdown("<div class='translucent'>", unsafe_allow_html=True)
    st.markdown(f"<div class='header'>{LOGO} — {APP_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub'>{TAGLINE}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div class='small'>
    <p><b>Privacy summary:</b> Your information is stored securely and used only to generate personalised advice and exports.
    By accepting you agree that OptiFin may use your inputs to provide insights, and that implementation requires direct engagement.
    If you do not accept you will be redirected away.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key=key("privacy_form")):
        st.write("")  # spacing
        accept = st.form_submit_button("Accept & Continue")
        if accept:
            st.session_state.privacy_accepted = True
            # prefetch market snapshot
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
    qcol = st.columns([4,1])
    with qcol[0]:
        query = st.text_input("Tell OptiFin what you need (free text)", key=key("home_query"))
    with qcol[1]:
        if st.button("Detect & Route", key=key("home_detect")):
            q = (query or "").lower()
            cat = "individual"
            if any(x in q for x in ["company","business","revenue","employees","invoice","profit"]): cat = "business"
            elif any(x in q for x in ["family","household","children","kids","spouse","partner"]): cat = "household"
            st.session_state.user_type = cat; st.session_state.page = "service"; st.experimental_rerun()

    st.markdown("### Or select profile")
    c1,c2,c3 = st.columns(3)
    if c1.button("Individual", key=key("home_ind")):
        st.session_state.user_type="individual"; st.session_state.page="service"; st.experimental_rerun()
    if c2.button("Household", key=key("home_hh")):
        st.session_state.user_type="household"; st.session_state.page="service"; st.experimental_rerun()
    if c3.button("Business", key=key("home_bus")):
        st.session_state.user_type="business"; st.session_state.page="service"; st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_service():
    st.markdown("<div class='translucent'>", unsafe_allow_html=True)
    st.header(f"{st.session_state.user_type.capitalize()} — Choose Service")
    svc = st.selectbox("Which service do you want?",["Invest","Tax Optimization","Cashflow & Budget","Full Growth Plan"], key=key("service_select"))
    if st.button("Continue", key=key("service_continue")):
        st.session_state.service_choice = svc
        st.session_state.page = "questions"
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_questions():
    st.markdown("<div class='translucent input-box'>", unsafe_allow_html=True)
    st.header(f"{st.session_state.user_type.capitalize()} — Tell us more")
    # contact
    st.subheader("Contact (optional)")
    name = st.text_input("Full name", key=key("q_name"))
    email = st.text_input("Email", key=key("q_email"))
    phone = st.text_input("Phone", key=key("q_phone"))

    inputs = {}
    if st.session_state.user_type == "individual":
        st.subheader("Personal & financial")
        inputs["Age"] = st.number_input("Age", min_value=16, max_value=100, key=key("ind_age"))
        inputs["Annual Income"] = st.text_input("Annual Gross Income (R)", key=key("ind_income"))
        inputs["Monthly Investable"] = st.text_input("Monthly investable (R)", key=key("ind_monthly"))
        inputs["Current Assets"] = st.text_input("Current investable assets (R)", key=key("ind_assets"))
        inputs["Risk Tolerance"] = st.selectbox("Risk Tolerance", ["Low","Moderate","High"], key=key("ind_risk"))
        inputs["Existing Deductions"] = st.text_area("Existing deductions (brief)", key=key("ind_deds"))
        inputs["Primary Goal"] = st.text_input("Primary goal (e.g., buy house in 5y)", key=key("ind_goal"))
        inputs["Timeframe"] = st.number_input("Timeframe (years)", min_value=1, value=10, key=key("ind_time"))
    elif st.session_state.user_type == "household":
        st.subheader("Household")
        inputs["Household Income"] = st.text_input("Household annual income (R)", key=key("hh_income"))
        inputs["Children"] = st.number_input("Number of children", min_value=0, key=key("hh_children"))
        inputs["Monthly Investable"] = st.text_input("Monthly investable (R)", key=key("hh_monthly"))
        inputs["Existing Deductions"] = st.text_area("Existing household deductions", key=key("hh_deds"))
        inputs["Risk Tolerance"] = st.selectbox("Risk Tolerance", ["Low","Moderate","High"], key=key("hh_risk"))
        inputs["Goal & Timeframe"] = st.text_input("Goal & timeframe", key=key("hh_goal"))
    else:
        st.subheader("Business")
        inputs["Annual Revenue"] = st.text_input("Annual revenue (R)", key=key("bus_rev"))
        inputs["Annual Expenses"] = st.text_input("Annual expenses (R)", key=key("bus_exp"))
        inputs["Employees"] = st.number_input("Employees", min_value=0, key=key("bus_emps"))
        inputs["Business Type"] = st.selectbox("Structure", ["Sole Proprietor","Private Company","Partnership","Other"], key=key("bus_type"))
        inputs["Owner Pay"] = st.text_input("Owner pay last 12 months (R)", key=key("bus_ownerpay"))
        inputs["Tax Paid Last Year"] = st.text_input("Tax paid last year (R)", key=key("bus_tax"))
        inputs["Monthly CapEx"] = st.text_input("Average monthly capex (R)", key=key("bus_capex"))
        inputs["Existing Tax Strategies"] = st.text_area("Existing tax strategies (brief)", key=key("bus_taxes"))

    # submit button (one-click)
    if st.button("Generate Advice & See Results", key=key("q_submit")):
        st.session_state.inputs = inputs
        st.session_state.lead = {"name":name,"email":email,"phone":phone}
        st.session_state.market_snapshot = get_market_snapshot()
        st.session_state.page = "results"
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def page_results():
    st.markdown("<div class='translucent'>", unsafe_allow_html=True)
    st.header("Results & Recommendations")
    ut = st.session_state.user_type
    inputs = st.session_state.get("inputs", {})
    market = st.session_state.get("market_snapshot","")
    # generate advice
    if not st.session_state.advice:
        st.session_state.advice = generate_advice(ut, inputs, market)
    st.subheader("High-level AI Advice")
    st.write(st.session_state.advice)
    # projection
    st.markdown("---")
    st.subheader("Illustrative projection")
    try:
        if ut=="individual":
            initial = parse_num(inputs.get("Current Assets",0) or inputs.get("Current investable assets",0))
            monthly = parse_num(inputs.get("Monthly Investable", inputs.get("Monthly investable",0) or inputs.get("Monthly investable",0)))
            years = int(inputs.get("Timeframe", 10))
            risk = inputs.get("Risk Tolerance","Moderate")
        elif ut=="household":
            initial = parse_num(inputs.get("Monthly Investable",0))*6
            monthly = parse_num(inputs.get("Monthly Investable",0))
            years = 10
            risk = inputs.get("Risk Tolerance","Moderate")
        else:
            initial = max(0.0, parse_num(inputs.get("Annual Revenue",0)) - parse_num(inputs.get("Annual Expenses",0))) * 0.05
            monthly = parse_num(inputs.get("Monthly CapEx",0))*0.05 if inputs.get("Monthly CapEx") else 0.0
            years = 7
            risk = "Moderate"
    except:
        initial, monthly, years, risk = 0,0,7,"Moderate"
    rate_map={"Low":0.04,"Moderate":0.07,"High":0.1}
    base = rate_map.get(risk,0.07)
    scenarios = {"Conservative": base-0.02, "Baseline": base, "Aggressive": base+0.03}
    proj = {n: project_growth(initial, monthly, years, r) for n,r in scenarios.items()}
    left,right = st.columns([2,1])
    with left:
        fig, ax = plt.subplots(figsize=(5,2.6))
        ax.plot(list(proj.keys()), [proj[k] for k in proj.keys()], marker='o', linewidth=1.6)
        ax.set_ylabel("Projected Value (R)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"R {v:,.0f}"))
        ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
        st.pyplot(fig, clear_figure=True)
    with right:
        st.markdown("<div class='ai-box'><b>Projection insight</b><br>")
        st.write(f"Baseline ({base*100:.1f}%) in {years} years: **{pretty(proj['Baseline'])}**")
        st.write("Illustrative only — contact for full model.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ETF recs
    st.markdown("---")
    st.subheader("Market-aware ETF shortlist")
    profile = st.selectbox("Risk profile", ["Low","Moderate","High"], index=1, key=key("etf_profile"))
    if st.button("Compute ETF shortlist", key=key("etf_compute")):
        recs = rank_etfs(profile, limit=6)
        formatted=[]
        for r in recs:
            r['explain'] = f"{r['ticker']}: 12m {r['ret_12m']*100:.1f}% | 3m {r['ret_3m']*100:.1f}% | vol {r['vol']*100:.1f}%"
            formatted.append(r)
        st.session_state.latest_etf_recs = formatted
    recs = st.session_state.get("latest_etf_recs",[])
    if recs:
        for r in recs:
            cols = st.columns([1,3,1])
            with cols[0]:
                fig = small_line_chart_for_ticker(r['ticker'])
                if fig: st.pyplot(fig, clear_figure=True)
            with cols[1]:
                st.markdown(f"**{r['ticker']}** — {r['explain']}")
            with cols[2]:
                st.write("")  # placeholder
    else:
        st.info("No ETF shortlist yet — click 'Compute ETF shortlist'")

    # Sample stocks quick table
    st.markdown("---")
    st.subheader("Market movers (sample)")
    if st.button("Fetch sample stocks", key=key("fetch_sample")):
        metrics=[]
        for tk in SAMPLE_STOCKS:
            m = compute_ticker_metrics(tk)
            if m:
                metrics.append({"ticker":m['ticker'], "12m":f"{m['ret_12m']*100:.1f}%", "vol":f"{m['vol']*100:.1f}%"})
        if metrics: st.table(pd.DataFrame(metrics))
        else: st.info("No stock data available")

    # Exports & CTA
    st.markdown("---")
    left,right = st.columns([2,1])
    with left:
        if st.button("Download Branded PDF", key=key("dl_pdf")):
            pdf = build_pdf(st.session_state.user_type, inputs, st.session_state.advice, st.session_state.get("latest_etf_recs",[]))
            st.download_button("Download PDF", data=pdf, file_name=f"OptiFin_{st.session_state.user_type}_report.pdf", key=key("dlpdf_btn"))
        if st.button("Download Branded Excel", key=key("dl_xlsx")):
            xlsx = build_xlsx(st.session_state.user_type, inputs, st.session_state.advice, st.session_state.get("latest_etf_recs",[]))
            st.download_button("Download Excel", data=xlsx, file_name=f"OptiFin_{st.session_state.user_type}_report.xlsx", key=key("dlxlsx_btn"))
    with right:
        st.markdown("<div class='ai-box'><b>Want implementation?</b><br>Schedule a call — we will build & implement the plan for a fee.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Navigation helpers ----------------
def project_growth(initial, monthly, years, annual_return):
    r = annual_return/12
    n = years*12
    if r == 0:
        return initial + monthly*n
    fv_init = initial * ((1+r)**n)
    fv_monthly = monthly * (((1+r)**n - 1) / r)
    return fv_init + fv_monthly

def small_line_chart_for_ticker(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="1y", interval="1d", actions=False)
        if hist is None or hist.empty: return None
        fig, ax = plt.subplots(figsize=(2.6,1.8))
        ax.plot(hist.index, hist['Close'], linewidth=1.1)
        ma50 = hist['Close'].rolling(50).mean()
        if len(hist)>=50: ax.plot(hist.index, ma50, linewidth=0.8, linestyle='--')
        ax.set_xticks([]); ax.set_yticks([])
        plt.tight_layout()
        return fig
    except Exception:
        return None

# ---------------- Router main ----------------
def main():
    # top-level sidebar nav (stable keys)
    st.sidebar.markdown(f"### {APP_NAME}")
    nav = st.sidebar.radio("Go to", ["Home","Service","Questions","Results"], index=["Home","Service","Questions","Results"].index("Home"), key=key("nav"))
    # map radio to page
    if not st.session_state.privacy_accepted and st.session_state.page!="privacy":
        st.session_state.page="privacy"

    if st.session_state.page=="privacy":
        page_privacy()
    elif st.session_state.page=="home":
        page_home()
    elif st.session_state.page=="service":
        page_service()
    elif st.session_state.page=="questions":
        page_questions()
    elif st.session_state.page=="results":
        page_results()
    else:
        page_home()

if __name__ == "__main__":
    main()
