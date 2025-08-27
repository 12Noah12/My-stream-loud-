# ----------------------- OptiFin Full App -----------------------
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
from datetime import date, datetime, timedelta

# yfinance optional
try:
    import yfinance as yf
    YF_AVAILABLE = True
except Exception:
    YF_AVAILABLE = False

st.set_page_config(page_title="OptiFin", page_icon="💹", layout="wide")

# ----------------------- STYLES -----------------------
st.markdown("""
<style>
.stApp {
  background-image: url('https://images.unsplash.com/photo-1567427013953-2451a0c35ef7?q=80&w=1950&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
}
.optifin-overlay {
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(6px);
  border-radius: 16px;
  padding: 20px;
}
.privacy-wrapper {
  background: rgba(17,24,39,0.9);
  color: #f1f5f9;
  border-radius: 14px;
  padding: 20px;
}
.ai-box {
  background: #0b1320;
  color: #eff4ff;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(255,255,255,0.08);
}
.chart-box {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 14px;
  padding: 12px;
}
.stButton>button {
  background: linear-gradient(135deg,#1f7a8c,#2a9d8f);
  color: #fff;
  border: 0;
  padding: 0.6rem 1rem;
  border-radius: 10px;
  font-weight: 600;
}
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button { -webkit-appearance:none; margin:0; }
input[type=number] { -moz-appearance:textfield; }
</style>
""", unsafe_allow_html=True)

# ----------------------- SESSION STATE -----------------------
if "page" not in st.session_state: st.session_state.page = "privacy"
if "user_type" not in st.session_state: st.session_state.user_type = None
if "action" not in st.session_state: st.session_state.action = None
if "accepted_privacy" not in st.session_state: st.session_state.accepted_privacy = False

def go(page): st.session_state.page = page

# ----------------------- HELPERS -----------------------
def parse_money(txt): 
    try: return float(str(txt).replace(",","").replace(" ","").replace("$",""))
    except: return 0.0

def branded_pdf_bytes(title, lines, advice):
    """UTF-8 safe PDF bytes"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",18)
    pdf.cell(0,10,"OptiFin Advisory",ln=1,align="C")
    pdf.set_font("Arial","",12)
    for line in lines: pdf.multi_cell(0,6,line)
    pdf.ln(4)
    pdf.set_font("Arial","B",14)
    pdf.cell(0,8,"AI Insights",ln=1)
    pdf.set_font("Arial","",12)
    for para in advice.split("\n"): pdf.multi_cell(0,6,para)
    pdf.set_y(-20)
    pdf.set_font("Arial","I",9)
    pdf.cell(0,8,f"Generated on {date.today()}",align="C")
    return pdf.output(dest="S").encode("utf-8")  # UTF-8 encoding fixes Unicode errors

def compact_line_chart(months, values,title="Projection"):
    fig,ax = plt.subplots(figsize=(5,2.5))
    ax.plot(range(1,months+1),values,marker='o')
    ax.set_title(title)
    ax.set_xlabel("Month");ax.set_ylabel("Value")
    ax.grid(True,alpha=0.2)
    st.pyplot(fig,use_container_width=True)

def get_market_snapshot(tickers,days=7):
    snapshot=[]
    if not YF_AVAILABLE: return [(t,None,None) for t in tickers]
    end=datetime.utcnow();start=end-timedelta(days=days*2)
    try:
        data=yf.download(tickers,start=start,end=end,progress=False,auto_adjust=True)
        if len(tickers)==1:
            last=float(data["Close"].dropna().iloc[-1])
            first=float(data["Close"].dropna().iloc[0])
            pct=(last-first)/first*100
            snapshot.append((tickers[0],last,pct))
        else:
            closes=data["Close"].dropna()
            if closes.empty: return [(t,None,None) for t in tickers]
            for t in tickers:
                try: last=float(closes[t].iloc[-1]);first=float(closes[t].iloc[0]);pct=(last-first)/first*100
                except: last,pct=None,None
                snapshot.append((t,last,pct))
    except: snapshot=[(t,None,None) for t in tickers]
    return snapshot

def ai_investment_advice(user,_):
    risk=user.get("risk","Medium");goal=user.get("goal_amount",0.0)
    monthly=user.get("monthly_contribution",0.0)
    tickers,growth=("VOO","VXUS","AAPL","MSFT"),1.06
    if risk=="Low": tickers=["VTI","BND","VXUS"];growth=1.03
    if risk=="High": tickers=["QQQ","NVDA","SMH","TSLA"];growth=1.1
    bal=0.0;series=[]
    for _ in range(12): bal=(bal+monthly)*growth;series.append(bal)
    lines=[f"Risk profile: {risk}. Suggested: {', '.join(tickers)}."]
    snaps=get_market_snapshot(tickers[:3])
    markets=[f"{t}: ${last:,.2f} ({pct:+.1f}%)" if last is not None else f"{t}: data N/A" for t,last,pct in snaps]
    lines.append("Market snapshot (7d): "+" | ".join(markets)+".")
    if goal and series[-1]<goal: gap=goal-series[-1];lines.append(
        f"Projected ${series[-1]:,.0f} vs goal ${goal:,.0f}. Consider increasing contributions or risk slightly.")
    else: lines.append(f"Projected ${series[-1]:,.0f} in 12 months. Maintain discipline.")
    return "\n".join(lines),series,tickers

def ai_tax_advice(user):
    income=user.get("annual_income",0.0);deductions=user.get("deductions",0.0)
    dependants=user.get("dependants",0);filing=user.get("filing_status","Single")
    est_taxable=max(income-deductions-dependants*3500,0)
    rate=0.18 if est_taxable<50000 else 0.26 if est_taxable<150000 else 0.39
    est_tax=est_taxable*rate
    tips=["Max retirement contributions.","Aggregate work costs with receipts.",
          "Use family allowances if applicable.","Harvest capital losses prudently."]
    return est_tax,tips

# ----------------------- PAGES -----------------------
def page_privacy():
    st.markdown("<div class='privacy-wrapper'>",unsafe_allow_html=True)
    st.markdown("## Privacy & Consent Agreement")
    st.markdown("By clicking **I Agree**, you consent to data processing for AI advisory only.")
    c1,c2=st.columns([1,1])
    with c1: 
        if st.button("I Decline",key="btn_decline"): st.stop()
    with c2: 
        if st.button("I Agree",key="btn_agree"): st.session_state.accepted_privacy=True;go("home")
    st.markdown("</div>",unsafe_allow_html=True)

def page_home():
    st.markdown("<div class='optifin-overlay'>",unsafe_allow_html=True)
    st.markdown("### Welcome to OptiFin")
    cA,cB,cC=st.columns(3)
    with cA: 
        if st.button("Individual",key="nav_individual"): st.session_state.user_type="Individual"
    with cB: 
        if st.button("Household",key="nav_household"): st.session_state.user_type="Household"
    with cC: 
        if st.button("Business",key="nav_business"): st.session_state.user_type="Business"
    st.markdown("---")
    st.session_state.action
