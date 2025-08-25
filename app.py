# app.py
# FinAI — Full integrated Streamlit app (advanced, single-file)
# - Robust matplotlib fallback so the app won't crash if matplotlib is missing.
# - Pages: Home, Tax, Investments, SME, Premium
# - Modular functions and caching
# - Exports, charts (if matplotlib installed), downloadable CSVs
# - Designed for Streamlit Cloud (include requirements.txt)

import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any, Dict

import numpy as np
import pandas as pd

import streamlit as st

# ----------------------------
# Robust matplotlib import
# ----------------------------
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

    # create a dummy object so later code using plt won't crash
    class _DummyPLT:
        def __getattr__(self, _):
            def _no_op(*args, **kwargs):
                st.warning(
                    "Matplotlib is not installed. Add `matplotlib` to requirements.txt to enable charts."
                )

            return _no_op

    plt = _DummyPLT()

# ----------------------------
# Page config + global settings
# ----------------------------
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide", initial_sidebar_state="expanded")

APP_TITLE = "FinAI"
PAGES = {
    "home": "Home",
    "tax": "Tax Optimization",
    "investments": "Investments",
    "sme": "SME Dashboard",
    "premium": "Premium Modules",
}

BG_STYLES = {
    "home": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
    "tax": "linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)",
    "investments": "linear-gradient(135deg, #0ea5a0 0%, #34d399 100%)",
    "sme": "linear-gradient(135deg, #334155 0%, #111827 100%)",
    "premium": "linear-gradient(135deg, #f59e0b 0%, #fde047 100%)",
}

SECTION_TEXT = {
    "home": "👋 Welcome to FinAI! Ask me anything below.",
    "tax": "💸 Optimize your taxes with smart strategies.",
    "investments": "📈 Grow your wealth with AI-guided investments.",
    "sme": "🏢 Manage your business efficiently with our SME tools.",
    "premium": "🌟 Unlock powerful premium features here.",
}

# ----------------------------
# CSS / styling (single block)
# ----------------------------
st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 5.5rem; }}
    /* Navbar */
    .navbar {{
      position: fixed; top: 0; left: 0; width: 100%;
      background: rgba(255,255,255,0.9);
      backdrop-filter: blur(8px);
      box-shadow: 0 2px 8px rgba(0,0,0,0.12);
      padding: 0.65rem 1.25rem; display: flex; justify-content: space-between; align-items: center; z-index: 1000;
    }}
    .navbar .logo {{ font-weight: 800; font-size: 1.05rem; color: #2563eb; }}
    .nav-links {{ display: flex; gap: .5rem; }}
    .nav-button button {{
      background: none; border: none; font-weight: 700; font-size: .95rem;
      padding: .35rem .75rem; border-radius: 10px; cursor: pointer; transition: background .2s;
    }}
    .nav-button button:hover {{ background: rgba(37,99,235,.12); }}

    /* Layout */
    .mega-rect {{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 18px; padding: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    }}
    .card {{
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 12px; padding: 1rem; transition: transform .12s, box-shadow .12s;
    }}
    .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,.18); }}

    .kpi {{ display:flex; align-items:center; gap:.75rem; font-weight:700; font-size:1rem;
      background: rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.06); padding:.6rem .8rem; border-radius:10px; }}

    input, select, textarea {{ color: #111; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Session state defaults
# ----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "authed" not in st.session_state:
    st.session_state.authed = False  # placeholder for gating premium

# ----------------------------
# Utilities
# ----------------------------
def format_money(x: float) -> str:
    try:
        return f"R{x:,.2f}"
    except Exception:
        return str(x)


@st.cache_data(show_spinner=False)
def future_value_monthly(monthly: float, annual_rate: float, years: int) -> float:
    """Future value of a monthly contribution at nominal annual rate, compounded monthly."""
    if monthly <= 0 or years <= 0:
        return 0.0
    r = annual_rate / 100
    i = r / 12
    n = years * 12
    if i == 0:
        return monthly * n
    return monthly * ((1 + i) ** n - 1) / i


@st.cache_data(show_spinner=False)
def compound_once(principal: float, annual_rate: float, years: float) -> float:
    r = annual_rate / 100
    return principal * ((1 + r) ** years)


# ----------------------------
# Tax helpers & defaults (South Africa style sample)
# ----------------------------
@dataclass
class TaxBracket:
    up_to: float
    rate: float  # decimal, e.g., 0.18 for 18%


SA_DEFAULT_BRACKETS = [
    TaxBracket(237100, 0.18),
    TaxBracket(370500, 0.26),
    TaxBracket(512800, 0.31),
    TaxBracket(673000, 0.36),
    TaxBracket(857900, 0.39),
    TaxBracket(1817000, 0.41),
    TaxBracket(float("inf"), 0.45),
]

DEFAULT_PRIMARY_REBATE = 17835.0


def calc_income_tax(income: float, brackets: List[TaxBracket]) -> float:
    tax = 0.0
    prev_limit = 0.0
    for b in brackets:
        top = b.up_to
        slab = min(income, top) - prev_limit
        if slab > 0:
            tax += slab * b.rate
            prev_limit = top
        if income <= top:
            break
    return max(0.0, tax)


# ----------------------------
# Navbar rendering
# ----------------------------
with st.container():
    st.markdown(
        """
        <div class="navbar">
            <div class="logo">💡 FinAI</div>
            <div class="nav-links">
                <!-- Buttons rendered below -->
            </div>
            <div class="dots">⋮</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Render nav buttons horizontally using columns
nav_cols = st.columns(len(PAGES))
for i, (k, label) in enumerate(PAGES.items()):
    with nav_cols[i]:
        if st.button(label, key=f"nav-{k}"):
            st.session_state.page = k

# Apply body background style depending on page
st.markdown(
    f"""
    <style>
    body {{
        background: {BG_STYLES.get(st.session_state.page, BG_STYLES['home'])};
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------
# Page: Home
# ----------------------------
def page_home():
    st.title(PAGES["home"])
    st.write(SECTION_TEXT["home"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    # AI Query Card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Ask FinAI")
    query = st.text_input("🔍 Ask a question about taxes, investments, or running an SME", key="ai_query")
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt_btn = st.button("Send Query")
    with col2:
        clear_btn = st.button("Clear")

    if prompt_btn and query:
        # placeholder for real LLM integration
        st.info("Processing...")
        # Simulate a helpful response
        st.success(f"Sample answer for: {query}")
        st.write(
            "Note: This is a skeleton AI reply. Connect an LLM or backend to provide real responses. "
            "Use provider APIs and secure keys."
        )

    if clear_btn:
        st.session_state.ai_query = ""

    st.markdown("</div>", unsafe_allow_html=True)

    # Quick stats
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Quick snapshots")
    k1, k2, k3 = st.columns(3)
    k1.metric("Active users", "4,218", "+12%")
    k2.metric("Avg session", "06:14", "+8%")
    k3.metric("Conversion", "3.9%", "+0.3%")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Page: Tax
# ----------------------------
def page_tax():
    st.title(PAGES["tax"])
    st.write(SECTION_TEXT["tax"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    tabs = st.tabs(["Income Tax", "VAT", "Capital Gains", "Deductions & RA"])

    # --- Income Tax tab ---
    with tabs[0]:
        st.subheader("Income Tax Estimator (editable brackets)")
        colL, colR = st.columns([1, 1])
        with colL:
            income = st.number_input("Annual taxable income (R)", min_value=0.0, value=650000.0, step=1000.0)
            rebate = st.number_input("Primary rebate (R)", min_value=0.0, value=DEFAULT_PRIMARY_REBATE, step=100.0)

            # editable brackets via data_editor
            df_br = pd.DataFrame(
                {
                    "up_to": [b.up_to if math.isfinite(b.up_to) else 9_999_999_999 for b in SA_DEFAULT_BRACKETS],
                    "rate_%": [b.rate * 100 for b in SA_DEFAULT_BRACKETS],
                }
            )
            st.caption("Edit the upper bound (use a large number for 'infinity') and rates in %.")
            edited = st.data_editor(df_br, num_rows="dynamic", use_container_width=True, key="tax_br_edit")
            # sanitized parse
            brackets = []
            for _, r in edited.iterrows():
                try:
                    up = float(r["up_to"])
                    rt = float(r["rate_%"]) / 100.0
                    brackets.append(TaxBracket(up, rt))
                except Exception:
                    continue

            gross_tax = calc_income_tax(income, brackets)
            net_tax = max(0.0, gross_tax - rebate)
            effective_rate = (net_tax / income * 100) if income > 0 else 0.0

            st.markdown("---")
            k1, k2, k3 = st.columns(3)
            k1.metric("Gross tax", format_money(gross_tax))
            k2.metric("Net tax (after rebate)", format_money(net_tax))
            k3.metric("Effective rate", f"{effective_rate:.2f}%")

        with colR:
            st.subheader("Monthly / PAYE view")
            months = st.slider("Months employed this year", 1, 12, 12)
            paye = net_tax * months / 12.0
            avg_monthly = paye / months if months else 0.0
            st.metric("Estimated PAYE (YTD)", format_money(paye))
            st.metric("Average tax / month", format_money(avg_monthly))

            # small bar
            if HAS_MPL:
                fig, ax = plt.subplots(figsize=(4, 3))
                ax.bar(["Income", "Net tax"], [income, net_tax])
                ax.set_title("Income vs Tax")
                st.pyplot(fig)
            else:
                st.info("Charts disabled (matplotlib missing).")

    # --- VAT tab ---
    with tabs[1]:
        st.subheader("VAT Calculator")
        col1, col2, col3 = st.columns(3)
        with col1:
            vat_amount = st.number_input("Amount (ex VAT if not inclusive)", min_value=0.0, value=1000.0, step=10.0)
        with col2:
            vat_pct = st.number_input("VAT %", min_value=0.0, value=15.0, step=0.5)
        with col3:
            vat_inclusive = st.checkbox("Input amount is VAT-inclusive", value=False)

        r = vat_pct / 100.0
        if vat_inclusive:
            ex = vat_amount / (1 + r)
            vat_val = vat_amount - ex
            inc = vat_amount
        else:
            ex = vat_amount
            vat_val = vat_amount * r
            inc = vat_amount * (1 + r)

        c1, c2, c3 = st.columns(3)
        c1.metric("Excl. VAT", format_money(ex))
        c2.metric("VAT", format_money(vat_val))
        c3.metric("Incl. VAT", format_money(inc))

    # --- Capital Gains tab ---
    with tabs[2]:
        st.subheader("Capital Gains Tax Estimator")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            proceeds = st.number_input("Proceeds (R)", min_value=0.0, value=250000.0, step=1000.0)
        with c2:
            base_cost = st.number_input("Base cost (R)", min_value=0.0, value=120000.0, step=1000.0)
        with c3:
            inclusion_rate = st.slider("Inclusion rate % (Individuals ~40, Companies ~80)", 0, 100, 40)
        with c4:
            marginal_tax_pct = st.slider("Marginal income tax %", 0, 55, 36)

        gain = max(0.0, proceeds - base_cost)
        taxable_portion = gain * (inclusion_rate / 100.0)
        estimated_cgt = taxable_portion * (marginal_tax_pct / 100.0)

        k1, k2, k3 = st.columns(3)
        k1.metric("Capital gain", format_money(gain))
        k2.metric("Taxable portion", format_money(taxable_portion))
        k3.metric("Estimated CGT", format_money(estimated_cgt))

    # --- Deductions & RA tab ---
    with tabs[3]:
        st.subheader("Allowances, Deductions & Retirement Annuity (RA)")
        col1, col2 = st.columns(2)
        with col1:
            gross_salary = st.number_input("Gross salary (R)", min_value=0.0, value=700000.0, step=1000.0)
            ra_contrib = st.number_input("Retirement annuity contributions (R)", min_value=0.0, value=30000.0, step=500.0)
            med_credit = st.number_input("Medical credits (R)", min_value=0.0, value=12000.0, step=100.0)
        with col2:
            travel = st.number_input("Travel allowance taxable portion (R)", min_value=0.0, value=20000.0, step=500.0)
            other_ded = st.number_input("Other deductible amount (R)", min_value=0.0, value=5000.0, step=100.0)

        est_taxable_income = max(0.0, gross_salary - ra_contrib - other_ded - med_credit + travel)
        st.metric("Estimated taxable income", format_money(est_taxable_income))

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Page: Investments
# ----------------------------
def page_investments():
    st.title(PAGES["investments"])
    st.write(SECTION_TEXT["investments"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    tabs = st.tabs(["Compound Growth", "Retirement Planner", "DCA Simulator", "Portfolio Analyzer"])

    # Compound Growth tab
    with tabs[0]:
        st.subheader("Compound Growth Calculator")
        col1, col2 = st.columns(2)
        with col1:
            principal = st.number_input("Starting amount (R)", min_value=0.0, value=50000.0, step=1000.0)
            monthly = st.number_input("Monthly contribution (R)", min_value=0.0, value=3000.0, step=100.0)
            years = st.slider("Years", 1, 60, 20)
            ann_return = st.slider("Expected annual return %", 0, 25, 10)
        with col2:
            fv_principal = compound_once(principal, ann_return, years)
            fv_contrib = future_value_monthly(monthly, ann_return, years)
            total = fv_principal + fv_contrib

            k1, k2, k3 = st.columns(3)
            k1.metric("Future value (principal)", format_money(fv_principal))
            k2.metric("Future value (contrib)", format_money(fv_contrib))
            k3.metric("Total future value", format_money(total))

            # plot growth
            months = years * 12
            bal = principal
            balances = [bal]
            monthly_rate = (ann_return / 100.0) / 12.0
            for _ in range(months):
                bal = bal * (1 + monthly_rate) + monthly
                balances.append(bal)
            if HAS_MPL:
                fig, ax = plt.subplots(figsize=(8, 3.5))
                ax.plot(np.arange(len(balances)) / 12.0, balances, linewidth=2)
                ax.set_title("Projected Balance Over Time")
                ax.set_xlabel("Years")
                ax.set_ylabel("Balance (R)")
                st.pyplot(fig)
            else:
                st.info("Charts disabled (matplotlib missing).")

    # Retirement Planner tab
    with tabs[1]:
        st.subheader("Retirement Planner (Nominal vs Real)")
        c1, c2 = st.columns(2)
        with c1:
            age_now = st.slider("Current age", 16, 70, 18)
            age_ret = st.slider("Planned retirement age", age_now + 1, 75, 60)
            monthly_cont = st.number_input("Monthly contribution (R)", min_value=0.0, value=2800.0, step=100.0)
            curr_savings = st.number_input("Current savings (R)", min_value=0.0, value=556780.0, step=1000.0)
            exp_return = st.slider("Expected return %", 0, 20, 8)
            exp_inflation = st.slider("Inflation %", 0, 12, 5)
        with c2:
            years = max(0, age_ret - age_now)
            fv_curr = compound_once(curr_savings, exp_return, years)
            fv_cont = future_value_monthly(monthly_cont, exp_return, years)
            nominal_total = fv_curr + fv_cont
            real_total = nominal_total / ((1 + exp_inflation / 100.0) ** years) if years > 0 else nominal_total

            st.metric("Nominal nest egg", format_money(nominal_total))
            st.metric("Real (today R)", format_money(real_total))

            swr = st.slider("Safe withdrawal rate %", 1, 6, 4)
            est_annual_income_today = real_total * (swr / 100.0)
            st.metric("Estimated annual retirement income (today R)", format_money(est_annual_income_today))

    # DCA simulator tab
    with tabs[2]:
        st.subheader("DCA (Dollar-Cost Averaging) Simulator")
        c1, c2 = st.columns(2)
        with c1:
            months = st.slider("Months", 12, 360, 120)
            monthly_buy = st.number_input("Monthly buy (R)", min_value=0.0, value=2000.0, step=100.0)
            mu = st.slider("Avg annual return %", -10, 20, 8)
            sigma = st.slider("Volatility % (annualized)", 1, 80, 20)
            runs = st.number_input("Monte-Carlo runs", min_value=50, max_value=2000, value=200, step=50)
        with c2:
            # simulate GBM for each run and compute final portfolio
            results = []
            t_steps = months
            dt = 1 / 12.0
            mu_m = mu / 100.0
            sigma_m = sigma / 100.0
            np.random.seed(42)
            for r in range(runs):
                price = 100.0
                units = 0.0
                for _ in range(t_steps):
                    drift = (mu_m - 0.5 * sigma_m ** 2) * dt
                    shock = sigma_m * math.sqrt(dt) * np.random.randn()
                    price = price * math.exp(drift + shock)
                    if price > 0:
                        units += monthly_buy / price
                results.append(units * price)

            invested = monthly_buy * months
            median = np.median(results)
            p10, p90 = np.percentile(results, [10, 90])

            k1, k2, k3 = st.columns(3)
            k1.metric("Total invested", format_money(invested))
            k2.metric("Median portfolio value", format_money(median))
            k3.metric("10th/90th percentile", f"{format_money(p10)} / {format_money(p90)}")

            if HAS_MPL:
                fig, ax = plt.subplots(figsize=(8, 3.5))
                ax.hist(results, bins=30)
                ax.set_title("Distribution of Ending Portfolio Values")
                st.pyplot(fig)

    # Portfolio Analyzer (simple)
    with tabs[3]:
        st.subheader("Simple Portfolio Analyzer")
        uploaded = st.file_uploader("Upload holdings CSV (symbol, units, price)", type=["csv"])
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                st.dataframe(df)
                if {"symbol", "units", "price"}.issubset(set(df.columns.str.lower())):
                    # normalize columns
                    df.columns = [c.lower() for c in df.columns]
                    df["market_value"] = df["units"] * df["price"]
                    total = df["market_value"].sum()
                    st.metric("Total portfolio value", format_money(total))
                    st.download_button("Download processed CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="portfolio_processed.csv")
                    if HAS_MPL:
                        fig, ax = plt.subplots(figsize=(6, 4))
                        ax.pie(df["market_value"], labels=df["symbol"], autopct="%1.1f%%")
                        ax.set_title("Portfolio Allocation")
                        st.pyplot(fig)
                else:
                    st.warning("CSV missing required columns: symbol, units, price (case-insensitive).")
            except Exception as e:
                st.error(f"Failed to read CSV: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Page: SME Dashboard
# ----------------------------
def page_sme():
    st.title(PAGES["sme"])
    st.write(SECTION_TEXT["sme"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    tabs = st.tabs(["KPIs", "Cash Flow", "Breakeven", "Pricing", "Payroll Estimator"])

    # KPIs
    with tabs[0]:
        st.subheader("Business KPIs")
        c1, c2, c3, c4 = st.columns(4)
        revenue = c1.number_input("Monthly revenue (R)", min_value=0.0, value=120000.0, step=1000.0)
        cogs = c2.number_input("COGS (R)", min_value=0.0, value=50000.0, step=500.0)
        opex = c3.number_input("Operating expenses (R)", min_value=0.0, value=30000.0, step=500.0)
        tax_rate = c4.slider("Estimated tax %", 0, 55, 28)

        gross_profit = max(0.0, revenue - cogs)
        ebit = max(0.0, gross_profit - opex)
        tax = ebit * (tax_rate / 100.0) if ebit > 0 else 0.0
        net_profit = ebit - tax

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Gross profit", format_money(gross_profit))
        k2.metric("EBIT", format_money(ebit))
        k3.metric("Tax", format_money(tax))
        k4.metric("Net profit", format_money(net_profit))

    # Cash Flow builder
    with tabs[1]:
        st.subheader("Cash Flow Builder")
        st.caption("Provide inflows and outflows. Export CSV when done.")
        default = pd.DataFrame(
            {"Type": ["Inflow", "Outflow"], "Item": ["Sales", "Rent"], "Amount": [revenue, 15000.0]}
        )
        cf = st.data_editor(default, num_rows="dynamic", use_container_width=True, key="cf_editor")
        try:
            inflows = cf.loc[cf["Type"].str.lower() == "inflow", "Amount"].sum()
            outflows = cf.loc[cf["Type"].str.lower() == "outflow", "Amount"].sum()
            net_cf = inflows - outflows
        except Exception:
            inflows = 0.0
            outflows = 0.0
            net_cf = 0.0

        k1, k2, k3 = st.columns(3)
        k1.metric("Inflows", format_money(inflows))
        k2.metric("Outflows", format_money(outflows))
        k3.metric("Net cash flow", format_money(net_cf))

        st.download_button("Export cash flow CSV", data=cf.to_csv(index=False).encode("utf-8"), file_name="cash_flow.csv")

    # Breakeven
    with tabs[2]:
        st.subheader("Break-even Analysis")
        fixed = st.number_input("Fixed costs (monthly, R)", min_value=0.0, value=40000.0, step=500.0)
        unit_price = st.number_input("Unit price (R)", min_value=0.0, value=250.0, step=5.0)
        var_cost = st.number_input("Variable cost / unit (R)", min_value=0.0, value=120.0, step=5.0)

        cont_margin = max(0.0, unit_price - var_cost)
        be_units = (fixed / cont_margin) if cont_margin > 0 else float("inf")
        st.metric("Break-even units", f"{be_units:,.1f}")

        # Visualize profit vs units
        max_units = int(be_units * 2) if math.isfinite(be_units) and be_units > 0 else 1000
        units = np.arange(0, max(10, max_units + 1))
        profit = units * cont_margin - fixed

        if HAS_MPL:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.plot(units, profit)
            ax.axhline(0, color="gray", linestyle="--")
            ax.set_title("Profit vs Units")
            ax.set_xlabel("Units")
            ax.set_ylabel("Profit (R)")
            st.pyplot(fig)

    # Pricing helper
    with tabs[3]:
        st.subheader("Pricing Helper")
        target_margin = st.slider("Target margin %", 0, 90, 40)
        total_unit_cost = st.number_input("Total unit cost (R)", min_value=0.0, value=150.0, step=5.0)
        vat_pct = st.slider("VAT %", 0, 25, 15)

        price_excl = total_unit_cost / (1 - target_margin / 100.0) if target_margin < 100 else float("inf")
        price_incl = price_excl * (1 + vat_pct / 100.0)

        k1, k2 = st.columns(2)
        k1.metric("Recommended price (ex VAT)", format_money(price_excl))
        k2.metric("Recommended price (inc VAT)", format_money(price_incl))

    # Payroll estimator (extra)
    with tabs[4]:
        st.subheader("Payroll Estimator")
        num_employees = st.number_input("Number of employees", min_value=0, value=5, step=1)
        avg_salary = st.number_input("Average monthly salary (R)", min_value=0.0, value=12000.0, step=100.0)
        employer_contrib_pct = st.slider("Employer contributions % (pension/benefits)", 0, 30, 10)
        total_monthly_payroll = num_employees * avg_salary * (1 + employer_contrib_pct / 100.0)
        st.metric("Estimated monthly payroll cost", format_money(total_monthly_payroll))

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Page: Premium
# ----------------------------
def page_premium():
    st.title(PAGES["premium"])
    st.write(SECTION_TEXT["premium"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    # gating (placeholder)
    if not st.session_state.authed:
        st.info("Premium modules are gated. Toggle to simulate unlock (placeholder).")
        if st.button("Unlock premium (demo)"):
            st.session_state.authed = True
        st.stop()

    tabs = st.tabs(["Monte Carlo Portfolio", "Tax Optimizer (Ideas)", "Advanced Exports"])

    # Monte Carlo
    with tabs[0]:
        st.subheader("Monte Carlo Portfolio Simulator")
        start_bal = st.number_input("Starting balance (R)", min_value=0.0, value=100000.0, step=1000.0)
        monthly_add = st.number_input("Monthly contribution (R)", min_value=0.0, value=3000.0, step=100.0)
        years = st.slider("Years", 1, 50, 20)
        avg_ret = st.slider("Average annual return %", -5, 20, 9)
        vol = st.slider("Annual volatility %", 1, 50, 18)
        sims = st.number_input("Simulations", min_value=100, max_value=5000, value=1000, step=100)

        # run sim (optimized lightly)
        np.random.seed(1234)
        months = years * 12
        m_mu = avg_ret / 100.0 / 12.0
        m_sigma = vol / 100.0 / math.sqrt(12.0)
        results = np.zeros(sims)
        for s in range(sims):
            bal = start_bal
            shocks = np.random.normal(m_mu, m_sigma, months)
            for r in shocks:
                bal = bal * (1 + r) + monthly_add
            results[s] = bal

        p5, p50, p95 = np.percentile(results, [5, 50, 95])
        st.metric("5th percentile", format_money(p5))
        st.metric("Median", format_money(p50))
        st.metric("95th percentile", format_money(p95))

        if HAS_MPL:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.hist(results, bins=60)
            ax.set_title("Distribution of Ending Balances")
            st.pyplot(fig)

    # Tax optimizer (idea toggles)
    with tabs[1]:
        st.subheader("Tax Optimizer — Toggle strategies to see illustrative savings")
        salary = st.number_input("Annual salary (R)", min_value=0.0, value=700000.0, step=1000.0)
        base_tax_est = salary * 0.24  # illustrative baseline

        st.metric("Baseline tax (illustrative)", format_money(base_tax_est))

        st.caption("Note: These are illustrative strategy toggles (not binding tax advice).")
        col1, col2, col3 = st.columns(3)
        with col1:
            opt_ra = st.checkbox("Max RA contribution")
            opt_travel = st.checkbox("Optimize travel allowance")
        with col2:
            opt_tfsa = st.checkbox("Max TFSA / Shift taxable interest")
            opt_med = st.checkbox("Medical credits / gap cover optimization")
        with col3:
            opt_solar = st.checkbox("Solar upgrade incentive (capex)")
            opt_learn = st.checkbox("Learnership / SME allowances")

        savings = 0.0
        if opt_ra:
            savings += 25000
        if opt_tfsa:
            savings += 6000
        if opt_med:
            savings += 4000
        if opt_travel:
            savings += 8000
        if opt_solar:
            savings += 15000
        if opt_learn:
            savings += 10000

        st.metric("Estimated tax savings (illustrative)", format_money(savings))
        st.metric("Post-strategy tax (illustrative)", format_money(max(0.0, base_tax_est - savings)))

    # Advanced Exports
    with tabs[2]:
        st.subheader("Advanced Exports")
        st.write("Bundle and export reports or scenarios for offline review.")
        # Example: create an example report dataframe
        df = pd.DataFrame(
            {
                "module": ["tax", "investments", "sme"],
                "summary": ["Tax calc snapshot", "Future value snapshot", "KPI snapshot"],
                "value_R": [12345.0, 67890.0, 23456.0],
            }
        )
        st.dataframe(df)
        st.download_button("Download report CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="finai_report.csv")

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Router
# ----------------------------
def router():
    page = st.session_state.get("page", "home")
    if page == "home":
        page_home()
    elif page == "tax":
        page_tax()
    elif page == "investments":
        page_investments()
    elif page == "sme":
        page_sme()
    elif page == "premium":
        page_premium()
    else:
        page_home()


# ----------------------------
# Run app
# ----------------------------
if __name__ == "__main__":
    router()

# ----------------------------
# Recommended requirements.txt
# ----------------------------
# Create a requirements.txt file with:
# streamlit
# matplotlib
# pandas
# numpy
# (Optionally add: scikit-learn, altair, plotly if you extend the app)
