# app.py
import datetime as dt
import io
import math
import textwrap
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# Optional libs (graceful fallback)
try:
    import yfinance as yf
except Exception:
    yf = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import cm
except Exception:
    canvas = None

try:
    import xlsxwriter
except Exception:
    xlsxwriter = None

# ----------------------------------
# App Config
# ----------------------------------
st.set_page_config(page_title="OptiFin", page_icon="💡", layout="wide")

# ----------------------------------
# Theme / Global CSS (Legibility)
# ----------------------------------
BG_IMAGE_URL = "https://images.unsplash.com/photo-1454165205744-3b78555e5572?q=80&w=1920&auto=format&fit=crop"

st.markdown(
    f"""
    <style>
      /* Page background */
      .stApp {{
        background: url('{BG_IMAGE_URL}') no-repeat center center fixed;
        background-size: cover;
      }}
      /* High-contrast text defaults */
      html, body, [class*="css"] {{
        color: #111 !important;
        font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji" !important;
      }}
      /* Glass panels for legibility */
      .glass {{
        background: rgba(255,255,255,0.85);
        -webkit-backdrop-filter: blur(8px);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(0,0,0,0.05);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
      }}
      .glass-dark {{
        background: rgba(0,0,0,0.55);
        -webkit-backdrop-filter: blur(8px);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 18px 20px;
        color:#fff !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
      }}
      .brand-title {{
        font-weight: 800; 
        letter-spacing: 0.3px;
        color:#0f172a;
        text-shadow: 0 2px 12px rgba(255,255,255,0.6);
      }}
      .muted {{
        color:#334155 !important;
      }}
      .cta {{
        background:#0ea5e9; 
        color:#fff;
        padding:10px 16px;
        border-radius:12px;
        text-decoration:none;
        font-weight:600;
        display:inline-block;
      }}
      /* Buttons & widgets contrast */
      .stButton>button {{
        border-radius: 12px;
        border: 1px solid rgba(0,0,0,0.08);
        font-weight: 700;
      }}
      .primary>button {{
        background:#0ea5e9 !important;
        color:#fff !important;
        border: none !important;
      }}
      /* Smaller, tidy charts */
      .chart-card {{
        padding:12px 14px; 
        border-radius:14px; 
        background:#fff; 
        border:1px solid rgba(0,0,0,0.06);
      }}
      /* Tooltip help icons */
      .help {{
        display:inline-block;
        margin-left:8px;
        color:#64748b;
        cursor: help;
        border-bottom: 1px dotted #64748b;
      }}
      /* Input label contrast */
      label p {{
        color:#0f172a !important; 
        font-weight:600 !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------
# Session State (single-click flows)
# ----------------------------------
def init_state():
    defaults = dict(
        privacy_accepted=False,
        page="home",  # "home" | "household" | "business"
        subtool=None,  # tool chosen within a section
        route_hint=None,  # AI router hint
        last_advice=None,
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ----------------------------------
# Helpers
# ----------------------------------
def h2(text: str):
    st.markdown(f"<h2 class='brand-title'>{text}</h2>", unsafe_allow_html=True)

def pill(text: str):
    st.markdown(
        f"<span style='background:#e2e8f0;padding:6px 10px;border-radius:999px;font-weight:700;color:#0f172a'>{text}</span>",
        unsafe_allow_html=True,
    )

def money(x: float) -> str:
    try:
        return f"R{float(x):,.0f}"
    except Exception:
        return "—"

def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except Exception:
        return default

# ----------------------------------
# Router (AI-ish: robust keyword mapper)
# ----------------------------------
def route_from_query(q: str) -> Tuple[str, str]:
    ql = q.lower()
    # Naive but resilient mapping
    household_keywords = ["family", "household", "budget", "kids", "spouse", "home", "mortgage", "rent", "retirement", "pension", "ra", "tfsa", "medical"]
    business_keywords = ["business", "company", "corp", "corporate", "sme", "employees", "payroll", "vat", "provisional", "sars", "invoice", "revenue", "cashflow"]
    invest_keywords = ["invest", "stocks", "shares", "etf", "index", "portfolio", "market", "trading", "bitcoin", "crypto"]

    if any(k in ql for k in business_keywords):
        return "business", "business"
    if any(k in ql for k in household_keywords):
        return "household", "household"
    if any(k in ql for k in invest_keywords):
        # Default invest goes to household unless they said business
        return "household", "invest"
    # Default to household
    return "household", "household"

# ----------------------------------
# Privacy Page
# ----------------------------------
def page_privacy():
    st.markdown("<div class='glass-dark'>", unsafe_allow_html=True)
    h2("Privacy, Data Use & Consent")
    st.markdown(
        """
        <div style="font-size:1.05rem; line-height:1.7">
        This Agreement explains how OptiFin collects, uses, stores, and safeguards the information you provide in this app.  
        By selecting <strong>Accept</strong>, you confirm that:
        <ul>
          <li>All information you enter may be stored on secure servers for analysis and service delivery.</li>
          <li>We will use your data to personalize financial insights, forecasts, and documents (e.g., reports, spreadsheets).</li>
          <li>You consent to automated processing and modeling to produce tailored advice.</li>
          <li>We do not sell your personal information. Access is restricted to authorized staff for service provision.</li>
          <li>Outputs are educational and do not constitute legal, tax, or financial advice. Decisions remain your responsibility.</li>
          <li>You may request data deletion at any time by contacting support.</li>
        </ul>
        If you do not accept, you will be redirected away from the app.
        </div>
        """,
        unsafe_allow_html=True,
    )
    colA, colB = st.columns([1, 1])
    with colA:
        accept = st.button("Accept", key="btn_accept_privacy", use_container_width=True)
    with colB:
        decline = st.button("Decline", key="btn_decline_privacy", use_container_width=True)

    if accept:
        st.session_state.privacy_accepted = True
        st.session_state.page = "home"
        st.success("Thanks. Your preferences are saved.")
        st.rerun()
    if decline:
        # Show a blocking message + stop
        st.error("Access denied. You chose not to accept the Privacy Agreement.")
        st.markdown(
            "<div class='glass' style='margin-top:12px'><strong>Close this tab</strong> to exit.</div>",
            unsafe_allow_html=True,
        )
        st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------
# PDF / Excel builders
# ----------------------------------
def build_pdf_report(title: str, inputs: Dict[str, Any], insights: str, chart_png: bytes | None) -> bytes | None:
    if canvas is None:
        return None
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Letterhead
    c.setFillColorRGB(0.06, 0.65, 0.91)
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, height - 50, "OptiFin — Personalised Financial Report")

    # Title
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, height - 110, title)

    # Inputs block
    y = height - 140
    c.setFont("Helvetica", 11)
    for k, v in inputs.items():
        c.drawString(2 * cm, y, f"{k}: {v}")
        y -= 16
        if y < 4 * cm:
            c.showPage()
            y = height - 100

    # Insights
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2 * cm, y - 10, "AI Insights")
    y -= 30
    c.setFont("Helvetica", 11)
    for line in textwrap.wrap(insights, width=100):
        c.drawString(2 * cm, y, line)
        y -= 16
        if y < 4 * cm:
            c.showPage()
            y = height - 100

    # Chart image if present
    if chart_png:
        try:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(io.BytesIO(chart_png))
            c.drawImage(img, width - 10*cm, 3*cm, 8*cm, 5*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Footer
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawRightString(width - 1.5*cm, 1.5*cm, "© OptiFin — Confidential • For client preview only")

    c.showPage()
    c.save()
    return buf.getvalue()

def build_excel_report(title: str, inputs: Dict[str, Any], insights: str) -> bytes | None:
    if xlsxwriter is None:
        return None
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    # Branding
    cover = wb.add_worksheet("Cover")
    h = wb.add_format({"bold": True, "font_size": 20, "font_color": "#0EA5E9"})
    small = wb.add_format({"font_size": 10, "font_color": "#475569"})
    cover.write("A1", "OptiFin — Strategy Pack", h)
    cover.write("A3", title, wb.add_format({"bold": True, "font_size": 14}))
    cover.write("A5", f"Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", small)

    ws = wb.add_worksheet("Inputs & Notes")
    bold = wb.add_format({"bold": True, "bg_color": "#E2E8F0"})
    ws.write("A1", "Field", bold)
    ws.write("B1", "Value", bold)
    r = 1
    for k, v in inputs.items():
        ws.write(r, 0, k)
        ws.write(r, 1, str(v))
        r += 1

    ws2 = wb.add_worksheet("Insights")
    ws2.write("A1", "AI Insights", bold)
    rows = textwrap.wrap(insights, width=90)
    rr = 1
    for line in rows:
        ws2.write(rr, 0, line)
        rr += 1

    wb.close()
    return output.getvalue()

# ----------------------------------
# Chart helper (small & neat)
# ----------------------------------
def small_line_chart(df: pd.DataFrame, y: str, height_px: int = 180):
    # Use Streamlit's native chart for speed and minimalism
    _ = st.line_chart(df[y], height=height_px)

# ----------------------------------
# AI-ish insights (no external keys required)
# ----------------------------------
def household_ai_insights(inputs: Dict[str, Any]) -> str:
    inc = safe_float(inputs.get("Monthly Income (R)"))
    exp = safe_float(inputs.get("Monthly Expenses (R)"))
    kids = int(safe_float(inputs.get("Dependants (#)"), 0))
    risk = inputs.get("Risk Tolerance", "Moderate")
    invest_goal = safe_float(inputs.get("Retirement Goal (R)"))
    invest_years = int(safe_float(inputs.get("Years to Retirement"), 25))
    contributions = safe_float(inputs.get("Monthly Contribution (R)"))

    saved = max(0.0, inc - exp)
    suggested = max(0.0, saved * 0.3)
    rate = 0.06 if risk == "Conservative" else (0.08 if risk == "Moderate" else 0.11)
    months = max(1, invest_years * 12)
    projected = contributions * (((1 + rate/12) ** months - 1) / (rate/12))

    lines = []
    lines.append(f"Based on your budget, a suggested monthly investment is around {money(suggested)} (≈30% of surplus).")
    lines.append(f"Given '{risk}' risk, a long-run annual return of ~{int(rate*100)}% is assumed for projections.")
    if invest_goal > 0:
        if projected >= invest_goal:
            lines.append(f"At your current contributions ({money(contributions)}/mo), you are on track to meet your goal of {money(invest_goal)} in ~{invest_years} years.")
        else:
            gap = invest_goal - projected
            lines.append(f"Your current trajectory could miss the target by ~{money(gap)}. Increasing monthly contributions or extending the horizon improves odds materially.")
    if kids > 0:
        lines.append("Consider using eligible dependants and education-related deductions/credits where lawful to reduce household tax burden.")
    if suggested <= 0:
        lines.append("Your expenses currently match or exceed income. Focus on trimming top 2–3 variable line items to unlock investable surplus.")
    lines.append("Prefer low-cost diversified index funds/ETFs for core holdings; layer satellite positions (5–20%) for thematic growth aligned to your risk.")
    lines.append("For implementation details and tailored vehicles (e.g., retirement annuities, tax-free accounts), please contact our team.")
    return " • " + "\n • ".join(lines)

def business_ai_insights(inputs: Dict[str, Any]) -> str:
    rev = safe_float(inputs.get("Annual Revenue (R)"))
    exp = safe_float(inputs.get("Annual Operating Expenses (R)"))
    emp = int(safe_float(inputs.get("Employees (#)"), 0))
    structure = inputs.get("Business Structure", "Company")
    capex = safe_float(inputs.get("Capex (R)"))
    vat = inputs.get("VAT Registered", "No")

    profit = max(0.0, rev - exp)
    margin = (profit / rev * 100) if rev > 0 else 0.0

    lines = []
    lines.append(f"Operating margin approximates {margin:.1f}%. Benchmark peers to set a 12-month margin target.")
    if capex > 0:
        lines.append("Model accelerated allowances for qualifying capital assets to optimize taxable income timing.")
    if emp > 0:
        lines.append("Review payroll structuring: split taxable cash, compliant allowances, and employer benefits to reduce total tax drag while preserving net pay.")
    if vat.lower().startswith("y"):
        lines.append("Ensure rigorous input VAT capture across all expense lines; consider apportionment optimization where partially exempt.")
    lines.append(f"For {structure.lower()} structures, ensure remuneration mix for owners balances dividends vs salary with relevant tax outcomes.")
    lines.append("Consider company card spend policies for ordinary & necessary expenses—tighten policy to maximize deductibility and audit trail quality.")
    lines.append("For implementation (entity restructure, payroll policy, capex schedules), please contact our team.")
    return " • " + "\n • ".join(lines)

# ----------------------------------
# Market data (if yfinance available)
# ----------------------------------
def get_price_history(ticker: str, months: int = 6) -> pd.DataFrame | None:
    if yf is None:
        return None
    try:
        period = f"{months}mo"
        hist = yf.Ticker(ticker).history(period=period)
        if hist is None or hist.empty:
            return None
        hist = hist.rename(columns={"Close": "Price"})
        return hist[["Price"]]
    except Exception:
        return None

# ----------------------------------
# Home (AI Search + Section pick)
# ----------------------------------
def show_home():
    st.markdown("<div class='glass' style='margin-bottom:16px'>", unsafe_allow_html=True)
    h2("OptiFin")
    st.markdown("<p class='muted'>AI-assisted personal, household & corporate finance—clarity without the clutter.</p>", unsafe_allow_html=True)

    q = st.text_input(
        "Describe what you need (we'll route you):",
        placeholder="e.g. 'Help me lower my business tax and invest excess cash' or 'Plan retirement with RA + ETF blend'",
        key="ai_router_query",
    )
    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        if st.button("Route Me", key="btn_route", use_container_width=True):
            if q.strip():
                section, hint = route_from_query(q)
                st.session_state.page = section
                st.session_state.route_hint = hint
                st.rerun()
    with colB:
        if st.button("Household & Individual", key="btn_household", use_container_width=True):
            st.session_state.page = "household"
            st.session_state.route_hint = None
            st.rerun()
    with colC:
        if st.button("Business & Corporate", key="btn_business", use_container_width=True):
            st.session_state.page = "business"
            st.session_state.route_hint = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------
# Household Section
# ----------------------------------
def page_household():
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    h2("Household & Individual")
    st.markdown("<p class='muted'>Answer a few questions and get a compact projection + actionable insights.</p>", unsafe_allow_html=True)

    # Tool choice
    tool = st.radio(
        "Choose a tool",
        ["Retirement & Investment Planner", "Tax Optimization"],
        key="hh_tool",
        horizontal=True,
    )

    if tool == "Retirement & Investment Planner":
        cols = st.columns([1.2, 1])
        with cols[0]:
            st.subheader("Inputs")
            c1, c2 = st.columns(2)
            with c1:
                income = st.number_input("Monthly Income (R)", min_value=0.0, step=100.0, key="hh_income")
                expenses = st.number_input("Monthly Expenses (R)", min_value=0.0, step=100.0, key="hh_expenses")
                kids = st.number_input("Dependants (#)", min_value=0, step=1, key="hh_kids")
            with c2:
                risk = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], key="hh_risk")
                years = st.slider("Years to Retirement", min_value=5, max_value=50, value=25, key="hh_years")
                goal = st.number_input("Retirement Goal (R)", min_value=0.0, step=10000.0, key="hh_goal")

            contrib = st.number_input("Monthly Contribution (R)", min_value=0.0, step=100.0, key="hh_contrib")

            inputs = {
                "Monthly Income (R)": income,
                "Monthly Expenses (R)": expenses,
                "Dependants (#)": kids,
                "Risk Tolerance": risk,
                "Years to Retirement": years,
                "Retirement Goal (R)": goal,
                "Monthly Contribution (R)": contrib,
            }

            # Projection chart (small)
            st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
            # Simulate growth series
            rate = 0.06 if risk == "Conservative" else (0.08 if risk == "Moderate" else 0.11)
            months = max(1, years * 12)
            values = []
            running = 0.0
            for m in range(months):
                running = running * (1 + rate/12) + contrib
                if m % 3 == 0:
                    values.append(running)
            df = pd.DataFrame({"Projected Value": values})
            df.index = pd.date_range(end=dt.date.today() + dt.timedelta(days=months*30), periods=len(values), freq="Q")
            st.caption("Projected Portfolio (quarterly points)")
            small_line_chart(df.rename(columns={"Projected Value": "Projected"}), "Projected", height_px=160)
            st.markdown("</div>", unsafe_allow_html=True)

            # Buttons
            colx, coly = st.columns(2)
            with colx:
                run = st.button("Generate Insights", key="hh_generate", use_container_width=True)
            with coly:
                export = st.button("Export PDF & Excel", key="hh_export", use_container_width=True)

        with cols[1]:
            st.subheader("AI Insights")
            insights = household_ai_insights(inputs)
            st.info(insights)
            st.caption("These insights are educational—contact us for implementation details & specific instruments.")

        # Exports
        if export:
            # Chart image (optional)
            chart_png = None
            try:
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(4, 2.2))
                ax.plot(df.index, df["Projected"])
                ax.set_title("Projected Portfolio")
                ax.set_xlabel("")
                ax.set_ylabel("Rands")
                fig.tight_layout()
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=200)
                chart_png = buf.getvalue()
                plt.close(fig)
            except Exception:
                pass

            pdf_bytes = build_pdf_report("Household Retirement & Investment", inputs, insights, chart_png)
            excel_bytes = build_excel_report("Household Retirement & Investment", inputs, insights)

            c1, c2 = st.columns(2)
            with c1:
                if pdf_bytes:
                    st.download_button("Download PDF", data=pdf_bytes, file_name="OptiFin_Household_Report.pdf", mime="application/pdf", key="dl_hh_pdf")
                else:
                    st.warning("PDF generator not available (install reportlab).")
            with c2:
                if excel_bytes:
                    st.download_button("Download Excel", data=excel_bytes, file_name="OptiFin_Household_Report.xlsx", key="dl_hh_xlsx")
                else:
                    st.warning("Excel generator not available (install xlsxwriter).")

    elif tool == "Tax Optimization":
        st.subheader("Household Tax Review")
        c1, c2 = st.columns(2)
        with c1:
            annual_income = st.number_input("Annual Taxable Income (R)", min_value=0.0, step=1000.0, key="ht_income")
            deductions = st.number_input("Known Deductions (R)", min_value=0.0, step=1000.0, key="ht_deductions")
            dependants = st.number_input("Dependants (#)", min_value=0, step
