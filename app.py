import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime, timedelta
from io import BytesIO

# Optional: install yfinance if live market data is needed
try:
    import yfinance as yf
    YF_AVAILABLE = True
except:
    YF_AVAILABLE = False

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="OptiFin",
    page_icon="💹",
    layout="wide"
)

# ---------------- Custom CSS ----------------
st.markdown("""
<style>
.stApp {
  background-image: url('https://images.unsplash.com/photo-1567427013953-2451a0c35ef7?q=80&w=1950&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
}
.optifin-overlay {
  background: rgba(255,255,255,0.92);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
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
</style>
""", unsafe_allow_html=True)

# ---------------- Session State ----------------
if "page" not in st.session_state: st.session_state.page = "privacy"
if "user_type" not in st.session_state: st.session_state.user_type = None
if "accepted_privacy" not in st.session_state: st.session_state.accepted_privacy = False

# ---------------- Navigation ----------------
def go(page):
    st.session_state.page = page

# ---------------- Helper Functions ----------------
def branded_pdf_bytes(title, lines, advice):
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
    pdf.cell(0,8,f"Generated on {datetime.today().date()}",align="C")
    return pdf.output(dest="S").encode("utf-8")

def compact_line_chart(values, title="Projection"):
    fig, ax = plt.subplots(figsize=(5,2.5))
    ax.plot(range(1,len(values)+1),values, marker='o')
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.2)
    st.pyplot(fig, use_container_width=True)

def get_market_snapshot(tickers, days=7):
    snapshot=[]
    if not YF_AVAILABLE:
        return [(t,None,None) for t in tickers]
    end=datetime.utcnow()
    start=end-timedelta(days=days*2)
    try:
        data=yf.download(tickers,start=start,end=end,progress=False,auto_adjust=True)
        closes=data["Close"].dropna()
        for t in tickers:
            try:
                last=float(closes[t].iloc[-1])
                pct=(closes[t].iloc[-1]-closes[t].iloc[0])/closes[t].iloc[0]*100
            except:
                last=None
                pct=None
            snapshot.append((t,last,pct))
    except:
        snapshot=[(t,None,None) for t in tickers]
    return snapshot

def ai_investment_advice(user):
    risk=user.get("risk","Medium")
    goal=user.get("goal_amount",0.0)
    monthly=user.get("monthly_contribution",0.0)
    tickers=("VOO","VXUS","AAPL","MSFT")
    growth=1.06
    if risk=="Low": tickers=("VTI","BND","VXUS"); growth=1.03
    if risk=="High": tickers=("QQQ","NVDA","SMH","TSLA"); growth=1.1
    bal=0.0;series=[]
    for _ in range(12):
        bal=(bal+monthly)*growth
        series.append(bal)
    lines=[f"Risk profile: {risk}. Suggested tickers: {', '.join(tickers)}."]
    snaps=get_market_snapshot(tickers[:3])
    markets=[f"{t}: ${last:,.2f} ({pct:+.1f}%)" if last is not None else f"{t}: data N/A" for t,last,pct in snaps]
    lines.append("Market snapshot (7d): "+" | ".join(markets)+".")
    if goal and series[-1]<goal:
        gap=goal-series[-1]
        lines.append(f"Projected ${series[-1]:,.0f} vs goal ${goal:,.0f}. Consider increasing contributions or adjusting risk.")
    else:
        lines.append(f"Projected ${series[-1]:,.0f} in 12 months. Maintain current strategy.")
    return "\n".join(lines), series

def ai_tax_advice(user):
    income=user.get("annual_income",0.0)
    deductions=user.get("deductions",0.0)
    dependants=user.get("dependants",0)
    est_taxable=max(income-deductions-dependants*3500,0)
    rate=0.18 if est_taxable<50000 else 0.26 if est_taxable<150000 else 0.39
    est_tax=est_taxable*rate
    tips=["Max retirement contributions.",
          "Aggregate work costs with receipts.",
          "Use family allowances if applicable.",
          "Harvest capital losses prudently."]
    return est_tax, tips

# ---------------- Pages ----------------
def page_privacy():
    st.markdown("<div class='optifin-overlay'>",unsafe_allow_html=True)
    st.markdown("## Privacy & Consent Agreement")
    st.markdown("By clicking **I Agree**, you consent to data processing for AI advisory only.")
    c1,c2=st.columns([1,1])
    with c1:
        if st.button("I Decline",key="decline"): st.stop()
    with c2:
        if st.button("I Agree",key="agree"):
            st.session_state.accepted_privacy=True
            go("home")
    st.markdown("</div>",unsafe_allow_html=True)

def page_home():
    st.markdown("<div class='optifin-overlay'>",unsafe_allow_html=True)
    st.markdown("### Welcome to OptiFin")
    cA,cB,cC=st.columns(3)
    with cA:
        if st.button("Individual",key="indiv"):
            st.session_state.user_type="Individual";go("advisor")
    with cB:
        if st.button("Household",key="house"):
            st.session_state.user_type="Household";go("advisor")
    with cC:
        if st.button("Business",key="business"):
            st.session_state.user_type="Business";go("advisor")
    st.markdown("</div>",unsafe_allow_html=True)

def page_advisor():
    st.markdown("<div class='optifin-overlay'>",unsafe_allow_html=True)
    st.markdown(f"## {st.session_state.user_type} Advisory")
    
    user_data={}
    user_data['annual_income']=st.number_input("Annual Income ($)",min_value=0,step=1000)
    user_data['monthly_contribution']=st.number_input("Monthly Contribution ($)",min_value=0,step=100)
    user_data['goal_amount']=st.number_input("Goal Amount ($)",min_value=0,step=1000)
    user_data['risk']=st.selectbox("Risk Tolerance",["Low","Medium","High"])
    user_data['dependants']=st.number_input("Dependants",min_value=0,step=1)
    
    advice_text, projection = ai_investment_advice(user_data)
    est_tax, tips = ai_tax_advice(user_data)
    
    c1,c2 = st.columns([2,1])
    with c1:
        st.markdown("### Projection Chart")
        compact_line_chart(projection)
    with c2:
        st.markdown("<div class='ai-box'>### AI Insights</div>",unsafe_allow_html=True)
        st.markdown(advice_text)
        st.markdown(f"Estimated Tax: ${est_tax:,.2f}")
        st.markdown("Tips: " + " | ".join(tips))
    
    if st.button("Download PDF"):
        pdf_bytes = branded_pdf_bytes("Investment Overview", [f"User Type: {st.session_state.user_type}"], advice_text)
        st.download_button("Download PDF", pdf_bytes, file_name="OptiFin_Advisory.pdf")
    
    st.markdown("</div>",unsafe_allow_html=True)

# ---------------- Main ----------------
def main():
    if not st.session_state.accepted_privacy:
        page_privacy()
    elif st.session_state.page=="home":
        page_home()
    elif st.session_state.page=="advisor":
        page_advisor()

main()
