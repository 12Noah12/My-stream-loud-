# ----------------------- OptiFin - Full Launch App -----------------------
# Streamlit single-file app with privacy gating, legible UI, live insights,
# compact charts + AI Insight panel, branded PDF/Excel exports, and robust
# navigation without experimental_rerun.

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
from datetime import date, datetime, timedelta

# yfinance is optional (we degrade gracefully)
try:
    import yfinance as yf
    YF_AVAILABLE = True
except Exception:
    YF_AVAILABLE = False

# ----------------------- PAGE CONFIG -----------------------
st.set_page_config(page_title="OptiFin", page_icon="💹", layout="wide")

# ----------------------- GLOBAL STYLES -----------------------
st.markdown("""
<style>
/* Base */
html, body, [class*="css"]  {
  font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif;
  color: #101418;
}

/* App background image + overlay for legibility */
.stApp {
  background-image: url('https://images.unsplash.com/photo-1567427013953-2451a0c35ef7?q=80&w=1950&auto=format&fit=crop');
  background-size: cover;
  background-position: center;
}
.optifin-overlay {
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 16px;
  padding: 18px 22px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

/* Titles readable on all backgrounds */
h1, h2, h3, h4 { color: #0b1320 !important; }

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, #1f7a8c, #2a9d8f);
  color: #fff;
  border: 0;
  padding: 0.6rem 1rem;
  border-radius: 10px;
  font-weight: 600;
  letter-spacing: .2px;
}
.stButton > button:hover {
  filter: brightness(1.05);
}

/* Primary CTA */
.optifin-cta button {
  background: linear-gradient(135deg, #5a189a, #7b2cbf) !important;
}

/* Inputs: remove +/- steppers while allowing free typing */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0;}
input[type=number] { -moz-appearance:textfield; }

/* Compact chart container */
.chart-box {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 14px;
  padding: 12px;
}

/* AI Insight panel */
.ai-box {
  background: #0b1320;
  color: #eff4ff;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(255,255,255,0.08);
}

/* Info cards */
.info-card {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 14px;
  padding: 14px;
}

/* Tooltips (help text) */
label p, .stMarkdown p { color: #101418; }
.small-muted { color: #5b6573; font-size: 0.9rem; }

/* Privacy page readability */
.privacy-wrapper {
  background: rgba(17, 24, 39, 0.86);
  color: #f1f5f9;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px;
  padding: 18px;
}
.privacy-wrapper h2, .privacy-wrapper h3, .privacy-wrapper h4 { color: #ffffff !important; }

/* Form label color contrast */
.css-10trblm, .css-5rimss { color: #0b1320 !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------- NAV & STATE -----------------------
PAGES = ["privacy", "home", "advisor"]
if "page" not in st.session_state:
    st.session_state.page = "privacy"
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "action" not in st.session_state:
    st.session_state.action = None
if "accepted_privacy" not in st.session_state:
    st.session_state.accepted_privacy = False

def go(page: str):
    st.session_state.page = page

# ----------------------- HELPERS -----------------------
def parse_money(text: str) -> float:
    if text is None:
        return 0.0
    try:
        clean = str(text).replace(" ", "").replace(",", "").replace("$", "")
        return float(clean) if clean else 0.0
    except Exception:
        return 0.0

def branded_pdf_bytes(report_title: str, header_lines: list[str], ai_advice: str) -> bytes:
    """Create a branded PDF with FPDF and return bytes (fixing prior TypeError)."""
    pdf = FPDF()
    pdf.add_page()

    # Header/letterhead
    pdf.set_fill_color(11,19,32)   # dark navy
    pdf.rect(0, 0, 210, 28, 'F')   # top band
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 18)
    pdf.ln(8)
    pdf.cell(0, 10, "OptiFin Advisory", ln=1, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "Confidential Financial Summary", ln=1, align="C")
    pdf.ln(4)

    # Title
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, report_title, ln=1)

    # Lines
    pdf.set_font("Arial", "", 12)
    for line in header_lines:
        pdf.cell(0, 8, line, ln=1)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "AI Insights (Overview)", ln=1)
    pdf.set_font("Arial", "", 12)
    # Wrap advice across lines
    for para in ai_advice.split("\n"):
        pdf.multi_cell(0, 6, para)

    # Footer
    pdf.set_y(-28)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 8, f"Generated on {date.today().strftime('%Y-%m-%d')} | OptiFin ©", align="C")

    # Return bytes safely
    raw = pdf.output(dest="S").encode("latin-1")
    return raw

def branded_excel_bytes(rows: list[tuple]):
    """Create a simple branded Excel with header formatting."""
    from xlsxwriter import Workbook
    output = BytesIO()
    wb = Workbook(output, {'in_memory': True})
    ws = wb.add_worksheet("OptiFin Report")
    header_fmt = wb.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#0b1320', 'border':1})
    cell_fmt = wb.add_format({'border':1})
    # Headers
    ws.write(0, 0, "Field", header_fmt)
    ws.write(0, 1, "Value", header_fmt)
    # Rows
    r = 1
    for k, v in rows:
        ws.write(r, 0, str(k), cell_fmt)
        ws.write(r, 1, str(v), cell_fmt)
        r += 1
    ws.set_column(0, 0, 28)
    ws.set_column(1, 1, 36)
    wb.close()
    return output.getvalue()

def compact_line_chart(months, values, title="Projection"):
    fig, ax = plt.subplots(figsize=(5,2.4))
    ax.plot(range(1, months+1), values, marker='o')
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Balance")
    ax.grid(True, alpha=0.2)
    st.pyplot(fig, use_container_width=True)

def get_market_snapshot(tickers: list[str], lookback_days: int = 7):
    """Return recent close and pct change for tickers. Graceful fallback if yfinance not available."""
    snapshot = []
    if not YF_AVAILABLE:
        # Fallback dummy
        for t in tickers:
            snapshot.append((t, None, None))
        return snapshot

    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days*2)  # cushion for weekends/holidays
    try:
        data = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
        # Structure varies if single vs multi ticker
        if len(tickers) == 1:
            last = float(data["Close"].dropna().iloc[-1]) if not data["Close"].dropna().empty else None
            first = float(data["Close"].dropna().iloc[0]) if not data["Close"].dropna().empty else None
            pct = ((last-first)/first*100) if (last and first and first != 0) else None
            snapshot.append((tickers[0], last, pct))
        else:
            closes = data["Close"].dropna()
            if closes.empty:
                for t in tickers:
                    snapshot.append((t, None, None))
            else:
                last_row = closes.iloc[-1]
                first_row = closes.iloc[0]
                for t in tickers:
                    try:
                        last = float(last_row.get(t, np.nan))
                        first = float(first_row.get(t, np.nan))
                        pct = ((last-first)/first*100) if (not np.isnan(last) and not np.isnan(first) and first != 0) else None
                    except Exception:
                        last, pct = None, None
                    snapshot.append((t, None if np.isnan(last) else last, pct))
    except Exception:
        for t in tickers:
            snapshot.append((t, None, None))
    return snapshot

# ----------------------- AI ADVICE -----------------------
def ai_investment_advice(user, market):
    """Heuristic (non-OpenAI) advice so it runs anywhere."""
    risk = user.get("risk", "Medium")
    goal = user.get("goal_amount", 0.0)
    monthly = user.get("monthly_contribution", 0.0)

    # Map risk to a model portfolio (broad ideas only)
    if risk == "Low":
        tickers = ["VTI", "BND", "VXUS"]
        growth = 1.03
    elif risk == "High":
        tickers = ["QQQ", "NVDA", "SMH", "TSLA"]
        growth = 1.10
    else: # Medium
        tickers = ["VOO", "VXUS", "AAPL", "MSFT"]
        growth = 1.06

    # Project 12 months
    bal = 0.0
    series = []
    for _ in range(12):
        bal = (bal + monthly) * growth
        series.append(bal)

    # Build insight text
    lines = []
    lines.append(f"Risk profile detected: **{risk}**. Suggested focus: {', '.join(tickers)}.")
    # Market snapshot
    snaps = get_market_snapshot(tickers[:3], 7)
    markets = []
    for t, last, pct in snaps:
        if last is not None and pct is not None:
            markets.append(f"{t}: ${last:,.2f} ({pct:+.1f}%)")
        else:
            markets.append(f"{t}: data unavailable")
    lines.append("Market snapshot (7d): " + " | ".join(markets) + ".")

    if goal and series[-1] < goal:
        gap = goal - series[-1]
        uplift = 1.15 if risk == "Low" else 1.08
        lines.append(
            f"At current monthly contribution **${monthly:,.0f}**, 12-month projection is **${series[-1]:,.0f}** "
            f"— below your goal **${goal:,.0f}** by **${gap:,.0f}**. Consider either increasing monthly savings "
            f"or a slightly higher risk mix. A tactical sleeve (≈10-20%) toward momentum or value using "
            f"disciplined rules (e.g., quarterly rebalance) can target uplift of ~{int((uplift-1)*100)}%."
        )
    else:
        lines.append(
            f"Your current pace aims at **${series[-1]:,.0f}** in 12 months. Maintain disciplined contributions, "
            f"automate transfers on payday, and rebalance semi-annually."
        )

    # Nudge to contact
    lines.append(
        "For an exact allocation, tax wrappers (e.g., TFSA/ISA/retirement accounts), and order routing, "
        "contact OptiFin to implement a managed plan."
    )
    return "\n".join(lines), series, tickers

def ai_tax_advice(user):
    """Heuristic tax guidance (non-jurisdictional; educational)."""
    income = user.get("annual_income", 0.0)
    deductions = user.get("deductions", 0.0)
    dependants = user.get("dependants", 0)
    filing = user.get("filing_status", "Single")

    est_taxable = max(income - deductions - dependants*3500, 0)  # simple proxy
    # crude bracket for demo
    if est_taxable < 50000: rate = 0.18
    elif est_taxable < 150000: rate = 0.26
    else: rate = 0.39
    est_tax = est_taxable * rate

    tips = [
        "Maximize retirement account contributions before year-end; pretax deferrals reduce taxable income immediately.",
        "Aggregate legitimate work-related costs (home office per sqm, device depreciation) with receipts.",
        "Use family allowances where applicable (education, medical) and capture dependent credits properly.",
        "Harvest capital losses against gains; reinstate exposure via similar but not substantially identical assets."
    ]
    return est_tax, tips

# ----------------------- PAGES -----------------------
def page_privacy():
    st.markdown("<div class='privacy-wrapper'>", unsafe_allow_html=True)
    st.markdown("## Privacy & Data Processing Agreement")
    st.markdown("""
**Purpose.** OptiFin collects the information you enter to generate tailored financial analysis and projections.
We process data solely to provide advisory insights and to prepare reports you explicitly request (PDF/Excel).

**Security.** Data is transmitted via TLS and stored on secure infrastructure. We restrict access and apply least-privilege controls.
You may request deletion of stored data at any time.

**Consent.** By selecting **I Agree**, you acknowledge and consent to: (i) processing of your data to generate financial insights; (ii)
limited retention for report generation; and (iii) our contacting you if you request implementation. This is a binding agreement.

**Disclaimer.** Results are for educational purposes and are not financial, legal, or tax advice. Consult a licensed professional
before taking action. You are responsible for the accuracy of data you provide.

**Opt-out.** If you do not agree, select **I Decline** and you will leave this application.
    """)

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("I Decline", key="btn_decline"):
            st.stop()  # Ends execution; Streamlit shows nothing else (effectively kicks user)
    with c2:
        if st.button("I Agree", key="btn_agree"):
            st.session_state.accepted_privacy = True
            go("home")
    st.markdown("</div>", unsafe_allow_html=True)

def page_home():
    st.markdown("<div class='optifin-overlay'>", unsafe_allow_html=True)
    st.markdown("### Welcome to OptiFin")
    st.markdown(
        "Your streamlined, AI-assisted hub for **Investment Planning**, **Tax Optimization**, and **Retirement**."
    )

    cA, cB, cC = st.columns(3)
    with cA:
        if st.button("Individual", key="nav_individual"):
            st.session_state.user_type = "Individual"
    with cB:
        if st.button("Household", key="nav_household"):
            st.session_state.user_type = "Household"
    with cC:
        if st.button("Business", key="nav_business"):
            st.session_state.user_type = "Business"

    st.markdown("---")
    st.markdown("#### What would you like to do?")
    st.session_state.action = st.selectbox(
        "Pick a focus area",
        ["Investment Planning", "Tax Optimization", "Retirement Planning"],
        key="select_action"
    )

    if st.session_state.user_type and st.session_state.action:
        if st.button("Continue", key="btn_continue", help="Proceed to the tailored advisor form"):
            go("advisor")
    st.markdown("</div>", unsafe_allow_html=True)

def page_advisor():
    st.markdown("<div class='optifin-overlay'>", unsafe_allow_html=True)
    ut = st.session_state.user_type or "Individual"
    act = st.session_state.action or "Investment Planning"
    st.markdown(f"### {ut} — {act}")

    # ---- Collect inputs (text fields to avoid +/-; validate) ----
    if act == "Investment Planning":
        with st.expander("Your Investment Profile", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                income_txt = st.text_input("Monthly income", "35000", key="ip_income",
                                           help="Enter your approximate monthly net income.")
                monthly_income = parse_money(income_txt)
            with col2:
                contrib_txt = st.text_input("Monthly contribution towards investments", "5000", key="ip_contrib",
                                            help="How much you plan to invest monthly.")
                monthly_contrib = parse_money(contrib_txt)
            with col3:
                goal_txt = st.text_input("Target goal (12 months)", "120000", key="ip_goal",
                                         help="What portfolio value would you like to reach in ±12 months?")
                goal_amount = parse_money(goal_txt)

            risk = st.selectbox("Risk tolerance", ["Low", "Medium", "High"],
                                index=1, key="ip_risk",
                                help="Low = conservative; High = aggressive growth preference.")
            horizon = st.selectbox("Time horizon", ["<1y", "1–3y", "3–5y", "5y+"], index=1, key="ip_horizon",
                                   help="How long do you plan to invest this money before major withdrawals?")

        # Build user dict and generate advice
        user = {
            "risk": risk,
            "goal_amount": goal_amount,
            "monthly_contribution": monthly_contrib,
            "monthly_income": monthly_income,
            "horizon": horizon,
            "user_type": ut
        }

        advice_text, series, tickers = ai_investment_advice(user, market=None)

        # Layout: small chart + AI insight side by side
        left, right = st.columns([1,1])
        with left:
            st.markdown("##### 12-Month Projection")
            st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
            compact_line_chart(12, series, "Projected Portfolio (12m)")
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown("##### AI Insight")
            st.markdown(f"<div class='ai-box'><div>{advice_text.replace('\n','<br>')}</div></div>", unsafe_allow_html=True)

        # Export buttons
        export_cols = st.columns(2)
        with export_cols[0]:
            rows = [
                ("User Type", ut),
                ("Focus", act),
                ("Monthly Income", f"{monthly_income:,.2f}"),
                ("Monthly Contribution", f"{monthly_contrib:,.2f}"),
                ("Goal (12m)", f"{goal_amount:,.2f}"),
                ("Risk", risk),
                ("Horizon", horizon),
                ("Tickers (indicative)", ", ".join(tickers))
            ]
            excel_bytes = branded_excel_bytes(rows + [("AI Insight", advice_text)])
            st.download_button("Download Excel", data=excel_bytes, file_name="OptiFin_Report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_excel_invest")
        with export_cols[1]:
            header_lines = [f"{k}: {v}" for k, v in rows]
            pdf_bytes = branded_pdf_bytes("Investment Overview", header_lines, advice_text)
            st.download_button("Download PDF", data=pdf_bytes, file_name="OptiFin_Report.pdf",
                               mime="application/pdf", key="dl_pdf_invest")

    elif act == "Tax Optimization":
        with st.expander("Your Tax Profile", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                inc_txt = st.text_input("Annual income", "720000", key="tx_income",
                                        help="Gross annual income (before tax).")
                annual_income = parse_money(inc_txt)
            with c2:
                ded_txt = st.text_input("Deductions (annual)", "45000", key="tx_deductions",
                                        help="Known deductions you already claim.")
                deductions = parse_money(ded_txt)
            with c3:
                deps = st.text_input("Dependants (number)", "1", key="tx_deps",
                                     help="Count of qualified dependants.")
                dependants = int(parse_money(deps)) if deps.strip() else 0

            filing_status = st.selectbox("Filing status", ["Single", "Married/Joint", "Head of Household"],
                                         key="tx_filing",
                                         help="Pick the category that fits your circumstances best.")

        est_tax, tips = ai_tax_advice({
            "annual_income": annual_income,
            "deductions": deductions,
            "dependants": dependants,
            "filing_status": filing_status
        })

        left, right = st.columns([1,1])
        with left:
            st.markdown("##### Estimated Liability (Demo)")
            st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
            months = 12
            # Simple monthly visualization of liability/accrual as a proportion
            liability_series = [est_tax/12.0 for _ in range(months)]
            compact_line_chart(months, liability_series, "Monthly Tax Accrual (est.)")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown("##### AI Insight")
            summary = (
                f"Estimated taxable income proxy suggests a liability around **${est_tax:,.0f}** under demo brackets. "
                "Potential actions:\n"
                f"- {tips[0]}\n- {tips[1]}\n- {tips[2]}\n- {tips[3]}\n\n"
                "We’ll tailor deductions/credits to your jurisdiction, optimize retirement wrappers, and structure "
                "allowable expense categories. Contact OptiFin to implement."
            )
            st.markdown(f"<div class='ai-box'><div>{summary.replace('\n','<br>')}</div></div>", unsafe_allow_html=True)

        # Export
        rows = [
            ("User Type", ut),
            ("Focus", act),
            ("Annual Income", f"{annual_income:,.2f}"),
            ("Deductions", f"{deductions:,.2f}"),
            ("Dependants", dependants),
            ("Filing", filing_status),
            ("Est. Annual Tax (demo)", f"{est_tax:,.0f}")
        ]
        colx, coly = st.columns(2)
        with colx:
            excel_bytes = branded_excel_bytes(rows + [("AI Insight", summary)])
            st.download_button("Download Excel", data=excel_bytes, file_name="OptiFin_Tax_Report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_excel_tax")
        with coly:
            header_lines = [f"{k}: {v}" for k, v in rows]
            pdf_bytes = branded_pdf_bytes("Tax Optimization Overview", header_lines, summary)
            st.download_button("Download PDF", data=pdf_bytes, file_name="OptiFin_Tax_Report.pdf",
                               mime="application/pdf", key="dl_pdf_tax")

    else:  # Retirement Planning (simple)
        with st.expander("Your Retirement Inputs", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                age_txt = st.text_input("Current age", "34", key="rt_age", help="Your current age.")
                age = int(parse_money(age_txt)) if age_txt.strip() else 30
            with c2:
                retire_txt = st.text_input("Target retirement age", "65", key="rt_target",
                                           help="At what age would you like to retire?")
                retire_age = int(parse_money(retire_txt)) if retire_txt.strip() else 65
            with c3:
                contrib_txt = st.text_input("Monthly contribution", "6000", key="rt_contrib",
                                            help="What you can commit monthly.")
                monthly_contrib = parse_money(contrib_txt)

            nest_txt = st.text_input("Current investable assets", "250000", key="rt_nest",
                                     help="Total current portfolio value earmarked for retirement.")
            nest_egg = parse_money(nest_txt)

            risk = st.selectbox("Risk tolerance", ["Low", "Medium", "High"], index=1, key="rt_risk",
                                help="Higher risk seeks higher expected long-term returns with higher volatility.")

        # Simple compounding to retirement
        years = max(retire_age - age, 1)
        if risk == "Low": annual_factor = 1.04
        elif risk == "High": annual_factor = 1.09
        else: annual_factor = 1.06

        months = years * 12
        monthly_factor = annual_factor ** (1/12)
        bal = nest_egg
        series = []
        for _ in range(months):
            bal = (bal + monthly_contrib) * monthly_factor
            series.append(bal)

        left, right = st.columns([1,1])
        with left:
            st.markdown("##### Retirement Projection")
            st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
            # sample last 24 months to keep chart compact if very long
            display_months = min(24, months)
            compact_line_chart(display_months, series[-display_months:], f"Next {display_months} Months")
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            final_val = series[-1]
            line = (
                f"Projected nest egg at age **{retire_age}** is **${final_val:,.0f}** under a {risk.lower()} profile. "
                "To enhance confidence, front-load contributions, exploit tax-advantaged wrappers, and maintain a "
                "globally diversified core with a disciplined glidepath."
            )
            st.markdown(f"<div class='ai-box'><div>{line}</div></div>", unsafe_allow_html=True)

        rows = [
            ("User Type", ut),
            ("Focus", act),
            ("Age / Target", f"{age} / {retire_age}"),
            ("Monthly Contribution", f"{monthly_contrib:,.2f}"),
            ("Current Assets", f"{nest_egg:,.2f}"),
            ("Risk", risk),
            ("Projected Value @ Retirement", f"{final_val:,.0f}")
        ]
        colx, coly = st.columns(2)
        with colx:
            excel_bytes = branded_excel_bytes(rows + [("AI Insight", line)])
            st.download_button("Download Excel", data=excel_bytes, file_name="OptiFin_Retirement_Report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_excel_retire")
        with coly:
            header_lines = [f"{k}: {v}" for k, v in rows]
            pdf_bytes = branded_pdf_bytes("Retirement Overview", header_lines, line)
            st.download_button("Download PDF", data=pdf_bytes, file_name="OptiFin_Retirement_Report.pdf",
                               mime="application/pdf", key="dl_pdf_retire")

    # Back nav
    st.markdown("---")
    if st.button("← Back", key="btn_back"):
        go("home")

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------- MAIN ROUTER -----------------------
def main():
    if not st.session_state.accepted_privacy:
        page_privacy()
        return
    if st.session_state.page == "home":
        page_home()
    elif st.session_state.page == "advisor":
        page_advisor()
    else:
        # default
        page_home()

if __name__ == "__main__":
    main()
# ----------------------- End of file -----------------------
