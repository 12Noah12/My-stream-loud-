# app.py
# FinAI — Complete advanced Streamlit app (650+ lines)
# - Pages: Home (big AI search), Tax, Investments, SME, Premium
# - Tooltips/help on nearly all inputs (hover the ? on inputs)
# - Robust matplotlib fallback so the app does not crash if matplotlib is missing
# - Charts render if matplotlib is installed
# - CSV export, caching, modular structure
# - Paste into app.py and add requirements.txt (provided at the bottom)

import math
import io
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any, Dict

import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------
# Robust matplotlib import (non-crashing)
# ---------------------------
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

    # create a dummy object so later code using plt won't crash
    class _DummyPlt:
        def __getattr__(self, _):
            def _no_op(*args, **kwargs):
                # Defer the warning until a chart function is actually called
                st.warning(
                    "Matplotlib is not installed. Charts are disabled. Add `matplotlib` to requirements.txt."
                )

            return _no_op

    plt = _DummyPlt()

# ---------------------------
# Page config + global constants
# ---------------------------
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
    "home": "linear-gradient(135deg, #081124 0%, #07213a 100%)",
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

# ---------------------------
# Global CSS (single injected block)
# ---------------------------
st.markdown(
    """
    <style>
    /* Top padding to make room for the navbar */
    .block-container { padding-top: 5.5rem; }

    /* Navbar */
    .navbar {
      position: fixed; top: 0; left: 0; width: 100%;
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(8px);
      box-shadow: 0 2px 10px rgba(0,0,0,0.12);
      padding: 0.6rem 1.25rem;
      display: flex; justify-content: space-between; align-items: center; z-index: 1000;
    }
    .navbar .logo { font-weight: 800; font-size: 1.05rem; color: #2563eb; letter-spacing: .3px; }
    .nav-links { display: flex; gap: .5rem; }
    .nav-button button {
      background: none; border: none; font-weight: 700; font-size: .95rem;
      padding: .35rem .75rem; border-radius: 10px; cursor: pointer; transition: background .2s;
    }
    .nav-button button:hover { background: rgba(37,99,235,.12); }

    /* Big AI Search styling */
    .ai-wrap { display:flex; justify-content:center; align-items:center; margin-top:1.5rem; margin-bottom:1rem; }
    .ai-search {
        width: 80%;
        max-width: 1000px;
        display:flex;
        gap:.6rem;
        align-items:center;
    }
    .ai-input {
        flex:1;
    }
    .ai-input input {
        width:100% !important;
        padding: 16px 20px !important;
        font-size: 18px !important;
        border-radius: 14px !important;
        border: 2px solid rgba(37,99,235,0.15) !important;
        box-shadow: 0 8px 30px rgba(37,99,235,0.08);
        transition: box-shadow .2s, transform .08s;
    }
    .ai-input input:focus {
        outline: none;
        box-shadow: 0 0 28px rgba(37,99,235,0.35);
        transform: translateY(-2px);
    }
    .ai-btn button {
        padding: 12px 20px !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg,#2563eb,#4f46e5) !important;
        color: white !important;
        font-weight: 800;
        font-size: 15px;
        border: none;
        box-shadow: 0 8px 28px rgba(79,70,229,0.18);
    }
    .ai-btn button:hover { transform: translateY(-2px); box-shadow: 0 12px 34px rgba(79,70,229,0.22); }

    /* Mega card */
    .mega-rect {
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 18px; padding: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    }
    .card {
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.04);
      border-radius: 12px; padding: 0.85rem; transition: transform .12s, box-shadow .12s;
    }
    .card:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,.15); }

    .kpi { display:flex; align-items:center; gap:.75rem; font-weight:700; font-size:1rem;
      background: rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.04); padding:.55rem .8rem; border-radius:10px; }

    /* smaller responsive tweaks */
    @media (max-width: 900px) {
      .ai-search { width: 96%; flex-direction: column; gap: .5rem; }
      .ai-btn button { width:100% !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Session state defaults
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "authed" not in st.session_state:
    st.session_state.authed = False  # placeholder for Premium gating

# ---------------------------
# Utilities
# ---------------------------
def format_money(x: float) -> str:
    try:
        return f"R{x:,.2f}"
    except Exception:
        return str(x)


@st.cache_data(show_spinner=False)
def future_value_monthly(monthly: float, annual_rate: float, years: int) -> float:
    """Future value of monthly contributions (nominal annual rate)."""
    if monthly <= 0 or years <= 0:
        return 0.0
    r = annual_rate / 100.0
    i = r / 12.0
    n = years * 12
    if i == 0:
        return monthly * n
    return monthly * ((1 + i) ** n - 1) / i


@st.cache_data(show_spinner=False)
def compound_once(principal: float, annual_rate: float, years: float) -> float:
    r = annual_rate / 100.0
    return principal * ((1 + r) ** years)


# ---------------------------
# Tax helpers & defaults
# ---------------------------
@dataclass
class TaxBracket:
    up_to: float
    rate: float  # decimal


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
    prev = 0.0
    for b in brackets:
        top = b.up_to
        slab = min(income, top) - prev
        if slab > 0:
            tax += slab * b.rate
            prev = top
        if income <= top:
            break
    return max(0.0, tax)


# ---------------------------
# Navbar (rendered via HTML + Streamlit buttons)
# ---------------------------
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

# Render nav buttons with columns to align horizontally
nav_cols = st.columns(len(PAGES))
for i, (k, label) in enumerate(PAGES.items()):
    with nav_cols[i]:
        if st.button(label, key=f"nav-{k}"):
            st.session_state.page = k

# Re-apply page-specific background
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

# ---------------------------
# PAGE: Home (big AI search)
# ---------------------------
def page_home():
    st.title(PAGES["home"])
    st.write(SECTION_TEXT["home"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    # Big center AI search
    st.markdown("<div class='ai-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='ai-search'>", unsafe_allow_html=True)
    # left: input
    st.markdown("<div class='ai-input'>", unsafe_allow_html=True)
    ai_query = st.text_input(
        "🔎 Ask FinAI anything",
        key="ai_query",
        placeholder="e.g., \"How can I reduce my 2025 tax liability legally?\"",
        help="Type a question for FinAI. Examples: tax, investments, SME questions. Press the Search button or Enter."
    )
    st.markdown("</div>", unsafe_allow_html=True)
    # right: button
    st.markdown("<div class='ai-btn'>", unsafe_allow_html=True)
    run_search = st.button("Search with AI", key="ai_search_btn", help="Run the AI query. Requires an API integration to return real answers.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Quick demo: prefill examples for users to try
    col_ex1, col_ex2, col_ex3 = st.columns([1, 1, 1])
    with col_ex1:
        if st.button("Example: Reduce tax legally"):
            st.session_state.ai_query = "What are legal tax reduction strategies in South Africa for a salaried individual?"
    with col_ex2:
        if st.button("Example: Compound returns"):
            st.session_state.ai_query = "How much will R50,000 grow to in 20 years at a 10% annual return with R3,000 monthly contributions?"
    with col_ex3:
        if st.button("Example: SME cashflow"):
            st.session_state.ai_query = "How do I structure a monthly cash flow forecast for a small retail business?"

    # Process AI query (placeholder; replace with real LLM integration as needed)
    if run_search and ai_query:
        st.info("Processing your query with FinAI (demo)...")
        # Demo response (replace this with a real API call if desired)
        st.success("Sample response (demo):")
        st.write(
            "This demo response is generated locally. Connect your OpenAI or other LLM API in Settings to return live answers."
        )
        st.markdown("---")

    # Small dashboard cards beneath
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Quick analytics")
    k1, k2, k3 = st.columns(3)
    k1.metric("Active Users", "4,218", "+12%", help="Active users on the platform this hour.")
    k2.metric("Avg Session", "06:14", "+8%", help="Average session length.")
    k3.metric("Conversion", "3.9%", "+0.3%", help="Conversion rate for premium features.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# PAGE: Tax Optimization
# ---------------------------
def page_tax():
    st.title(PAGES["tax"])
    st.write(SECTION_TEXT["tax"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    tabs = st.tabs(["Income Tax", "VAT", "Capital Gains", "Deductions & RA"])

    # Income Tax tab
    with tabs[0]:
        st.subheader("Income Tax Estimator (editable brackets)")
        col_left, col_right = st.columns([1, 1])
        with col_left:
            income = st.number_input(
                "Annual taxable income (R)",
                min_value=0.0,
                value=650000.0,
                step=1000.0,
                help="Enter the total taxable income for the tax year (after employer deductions)."
            )
            rebate = st.number_input(
                "Primary rebate (R)",
                min_value=0.0,
                value=DEFAULT_PRIMARY_REBATE,
                step=100.0,
                help="Primary rebate reduces tax payable for individuals. Use SA values or your country values."
            )

            # Editable brackets table
            st.caption("Edit tax brackets (upper bound & rate %) — use a very large number for 'infinity'.")
            df_br = pd.DataFrame({
                "up_to": [b.up_to if math.isfinite(b.up_to) else 9999999999 for b in SA_DEFAULT_BRACKETS],
                "rate_%": [b.rate * 100 for b in SA_DEFAULT_BRACKETS],
            })
            edited = st.data_editor(df_br, num_rows="dynamic", use_container_width=True, key="tax_brackets_editor")

            brackets: List[TaxBracket] = []
            for _, r in edited.iterrows():
                try:
                    up = float(r["up_to"])
                    rt = float(r["rate_%"]) / 100.0
                    brackets.append(TaxBracket(up, rt))
                except Exception:
                    continue

            gross_tax = calc_income_tax(income, brackets)
            net_tax = max(0.0, gross_tax - rebate)
            eff_rate = (net_tax / income * 100) if income > 0 else 0.0

            st.markdown("---")
            k1, k2, k3 = st.columns(3)
            k1.metric("Gross tax", format_money(gross_tax))
            k2.metric("Net tax (after rebate)", format_money(net_tax))
            k3.metric("Effective rate", f"{eff_rate:.2f}%")

        with col_right:
            st.subheader("PAYE / Monthly View")
            months = st.slider(
                "Months employed this year",
                min_value=1,
                max_value=12,
                value=12,
                help="Number of months you were employed during the tax year (useful for pro-rating)."
            )
            paye = net_tax * months / 12.0
            avg_month = paye / months if months else 0.0
            st.metric("Estimated PAYE (YTD)", format_money(paye))
            st.metric("Average tax / month", format_money(avg_month))

            if HAS_MPL:
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.bar(["Income", "Net tax"], [income, net_tax], color=["#4f46e5", "#2563eb"])
                ax.set_title("Income vs Tax")
                st.pyplot(fig)
            else:
                st.info("Charts disabled: install `matplotlib` in requirements.txt to enable charts.")

    # VAT tab
    with tabs[1]:
        st.subheader("VAT Calculator")
        c1, c2, c3 = st.columns(3)
        with c1:
            base_amount = st.number_input(
                "Amount (ex VAT if not inclusive) (R)",
                min_value=0.0,
                value=1000.0,
                step=10.0,
                help="Enter the base amount (either VAT exclusive or inclusive depending on the checkbox)."
            )
        with c2:
            vat_rate = st.number_input(
                "VAT %", min_value=0.0, value=15.0, step=0.5,
                help="Enter the VAT percentage applicable in your country."
            )
        with c3:
            vat_incl = st.checkbox(
                "Input amount is VAT-inclusive",
                value=False,
                help="Toggle if the base amount already contains VAT."
            )

        r = vat_rate / 100.0
        if vat_incl:
            excl = base_amount / (1 + r)
            vat_val = base_amount - excl
            incl = base_amount
        else:
            excl = base_amount
            vat_val = base_amount * r
            incl = base_amount * (1 + r)

        k1, k2, k3 = st.columns(3)
        k1.metric("Excl. VAT", format_money(excl), help="Amount excluding VAT.")
        k2.metric("VAT", format_money(vat_val), help="VAT amount.")
        k3.metric("Incl. VAT", format_money(incl), help="Amount including VAT.")

    # Capital Gains tab
    with tabs[2]:
        st.subheader("Capital Gains Tax (CGT) Estimator")
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            proceeds = st.number_input(
                "Proceeds (R)",
                min_value=0.0,
                value=250000.0,
                step=1000.0,
                help="The sale proceeds received for the asset."
            )
        with col_b:
            base_cost = st.number_input(
                "Base cost (R)",
                min_value=0.0,
                value=120000.0,
                step=1000.0,
                help="The original cost of the asset (including improvements)."
            )
        with col_c:
            inclusion_rate = st.slider(
                "Inclusion rate % (Individuals ~40, Companies ~80)",
                0, 100, 40,
                help="Percentage of the capital gain that is included in taxable income."
            )
        with col_d:
            marginal_tax_pct = st.slider(
                "Marginal income tax %",
                0, 55, 36,
                help="Your marginal income tax rate to estimate CGT payable on the taxable portion."
            )

        gain = max(0.0, proceeds - base_cost)
        taxable_portion = gain * inclusion_rate / 100.0
        estimated_cgt = taxable_portion * (marginal_tax_pct / 100.0)

        k1, k2, k3 = st.columns(3)
        k1.metric("Capital gain", format_money(gain))
        k2.metric("Taxable portion", format_money(taxable_portion))
        k3.metric("Estimated CGT", format_money(estimated_cgt))

    # Deductions & RA tab
    with tabs[3]:
        st.subheader("Allowances, Deductions & Retirement Annuity (RA)")
        col1, col2 = st.columns(2)
        with col1:
            gross_salary = st.number_input(
                "Gross salary (R)",
                min_value=0.0,
                value=700000.0,
                step=1000.0,
                help="Enter your gross salary before deductions."
            )
            ra_contrib = st.number_input(
                "Retirement annuity contributions (R)",
                min_value=0.0,
                value=30000.0,
                step=500.0,
                help="Your annual retirement annuity contributions — these may be deductible within limits."
            )
            med_credit = st.number_input(
                "Medical credits (R)",
                min_value=0.0,
                value=12000.0,
                step=100.0,
                help="Medical credits or tax-deductible medical expenses."
            )
        with col2:
            travel_allow = st.number_input(
                "Travel allowance - taxable portion (R)",
                min_value=0.0,
                value=20000.0,
                step=500.0,
                help="Taxable portion of any travel allowance you received."
            )
            other_ded = st.number_input(
                "Other deductible amount (R)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                help="Other deductions (e.g., work-related expenses) that reduce taxable income."
            )

        est_taxable_income = max(0.0, gross_salary - ra_contrib - other_ded - med_credit + travel_allow)
        st.metric("Estimated taxable income", format_money(est_taxable_income),
                  help="Approximate taxable income after the deductions entered above.")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# PAGE: Investments
# ---------------------------
def page_investments():
    st.title(PAGES["investments"])
    st.write(SECTION_TEXT["investments"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    tabs = st.tabs(["Compound Growth", "Retirement Planner", "DCA Simulator", "Portfolio Analyzer"])

    # Compound Growth
    with tabs[0]:
        st.subheader("Compound Growth Calculator")
        left, right = st.columns(2)
        with left:
            principal = st.number_input(
                "Starting amount (R)",
                min_value=0.0,
                value=50000.0,
                step=1000.0,
                help="Your starting capital (lump sum) invested today."
            )
            monthly = st.number_input(
                "Monthly contribution (R)",
                min_value=0.0,
                value=3000.0,
                step=100.0,
                help="Amount you will add every month to the investment."
            )
            years = st.slider("Years", 1, 60, 20, help="Investment horizon in years.")
            ann_return = st.slider(
                "Expected annual return %",
                0, 25, 10,
                help="Nominal expected annual return (before inflation)."
            )
        with right:
            fv_principal = compound_once(principal, ann_return, years)
            fv_contrib = future_value_monthly(monthly, ann_return, years)
            total = fv_principal + fv_contrib

            k1, k2, k3 = st.columns(3)
            k1.metric("Future value (principal)", format_money(fv_principal))
            k2.metric("Future value (contrib)", format_money(fv_contrib))
            k3.metric("Total future value", format_money(total))

            # Growth chart
            months = years * 12
            bal = principal
            balances = [bal]
            monthly_rate = (ann_return / 100.0) / 12.0
            for _ in range(months):
                bal = bal * (1 + monthly_rate) + monthly
                balances.append(bal)
            if HAS_MPL:
                fig, ax = plt.subplots(figsize=(8, 3.5))
                ax.plot(np.arange(len(balances)) / 12.0, balances, linewidth=2, color="#2563eb")
                ax.set_title("Projected Balance Over Time")
                ax.set_xlabel("Years")
                ax.set_ylabel("Balance (R)")
                st.pyplot(fig)
            else:
                st.info("Charts disabled: install matplotlib to see the growth chart.")

    # Retirement Planner
    with tabs[1]:
        st.subheader("Retirement Planner (Nominal vs Real)")
        c1, c2 = st.columns(2)
        with c1:
            age_now = st.slider("Current age", 16, 70, 18, help="Your present age.")
            age_ret = st.slider("Retirement age", age_now + 1, 75, 60, help="Age at which you plan to retire.")
            monthly_cont = st.number_input(
                "Monthly contribution (R)",
                min_value=0.0,
                value=2800.0,
                step=100.0,
                help="Monthly savings you will contribute until retirement."
            )
            curr_savings = st.number_input(
                "Current savings (R)",
                min_value=0.0,
                value=556780.0,
                step=1000.0,
                help="Amount already saved/invested for retirement."
            )
            exp_return = st.slider("Expected return %", 0, 20, 8, help="Expected nominal annual return.")
            exp_infl = st.slider("Inflation %", 0, 12, 5, help="Expected average annual inflation.")
        with c2:
            years = max(0, age_ret - age_now)
            fv_curr = compound_once(curr_savings, exp_return, years)
            fv_cont = future_value_monthly(monthly_cont, exp_return, years)
            nominal_total = fv_curr + fv_cont
            real_total = nominal_total / ((1 + exp_infl / 100.0) ** years) if years > 0 else nominal_total

            st.metric("Nominal nest egg", format_money(nominal_total), help="Nominal value at retirement.")
            st.metric("Real (today R)", format_money(real_total), help="Inflation-adjusted value in today's rand.")

            swr = st.slider("Safe withdrawal rate %", 1, 6, 4, help="Percent of portfolio you can safely withdraw annually.")
            est_income = real_total * (swr / 100.0)
            st.metric("Est. annual retirement income (today R)", format_money(est_income))

    # DCA Simulator
    with tabs[2]:
        st.subheader("DCA (Dollar-Cost Averaging) Simulator")
        a_col, b_col = st.columns(2)
        with a_col:
            months = st.slider("Months", 12, 360, 120, help="Number of months to simulate (investment horizon).")
            monthly_buy = st.number_input("Monthly buy (R)", min_value=0.0, value=2000.0, step=100.0, help="Amount invested every month.")
            mu = st.slider("Avg annual return %", -10, 20, 8, help="Average annual return (mean).")
            sigma = st.slider("Volatility % (annual)", 1, 80, 20, help="Annualized volatility of returns.")
            runs = st.number_input("Monte-Carlo runs", min_value=50, max_value=2000, value=200, step=50, help="Number of simulated runs.")
        with b_col:
            results = []
            dt = 1.0 / 12.0
            mu_m = mu / 100.0
            sigma_m = sigma / 100.0
            np.random.seed(123)
            for r in range(runs):
                price = 100.0
                units = 0.0
                for _ in range(months):
                    drift = (mu_m - 0.5 * sigma_m * sigma_m) * dt
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
            k3.metric("10th / 90th percentile", f"{format_money(p10)} / {format_money(p90)}")

            if HAS_MPL:
                fig, ax = plt.subplots(figsize=(8, 3.5))
                ax.hist(results, bins=30, color="#4f46e5")
                ax.set_title("Distribution of Ending Portfolio Values")
                st.pyplot(fig)

    # Portfolio Analyzer
    with tabs[3]:
        st.subheader("Simple Portfolio Analyzer (CSV upload)")
        uploaded = st.file_uploader("Upload holdings CSV (columns: symbol, units, price)", type=["csv"], help="CSV must include symbol, units, price columns.")
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                # normalize column names
                df_cols_lower = [c.lower().strip() for c in df.columns]
                df.columns = df_cols_lower
                if {"symbol", "units", "price"}.issubset(set(df.columns)):
                    df["market_value"] = df["units"].astype(float) * df["price"].astype(float)
                    total = df["market_value"].sum()
                    st.metric("Total portfolio value", format_money(total))
                    st.dataframe(df)
                    st.download_button("Download processed CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="portfolio_processed.csv")
                    if HAS_MPL:
                        fig, ax = plt.subplots(figsize=(6, 4))
                        ax.pie(df["market_value"], labels=df["symbol"], autopct="%1.1f%%")
                        ax.set_title("Portfolio Allocation")
                        st.pyplot(fig)
                else:
                    st.warning("CSV must contain 'symbol', 'units', and 'price' columns (case-insensitive).")
            except Exception as e:
                st.error(f"Failed to process CSV: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# PAGE: SME Dashboard
# ---------------------------
def page_sme():
    st.title(PAGES["sme"])
    st.write(SECTION_TEXT["sme"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    tabs = st.tabs(["KPIs", "Cash Flow", "Breakeven", "Pricing Helper", "Payroll Estimator"])

    # KPIs
    with tabs[0]:
        st.subheader("Business KPIs")
        c1, c2, c3, c4 = st.columns(4)
        revenue = c1.number_input("Monthly revenue (R)", min_value=0.0, value=120000.0, step=1000.0, help="Total sales or revenue for the month.")
        cogs = c2.number_input("COGS (R)", min_value=0.0, value=50000.0, step=500.0, help="Cost of goods sold.")
        opex = c3.number_input("Operating expenses (R)", min_value=0.0, value=30000.0, step=500.0, help="Recurring operating expenses (rent, utilities, etc.).")
        tax_rate = c4.slider("Estimated tax %", 0, 55, 28, help="Estimated corporate tax rate for the business.")

        gross_profit = max(0.0, revenue - cogs)
        ebit = max(0.0, gross_profit - opex)
        tax = ebit * (tax_rate / 100.0) if ebit > 0 else 0.0
        net_profit = ebit - tax

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Gross Profit", format_money(gross_profit))
        k2.metric("EBIT", format_money(ebit))
        k3.metric("Tax", format_money(tax))
        k4.metric("Net Profit", format_money(net_profit))

    # Cash Flow builder
    with tabs[1]:
        st.subheader("Cash Flow Builder")
        st.caption("Add inflow and outflow line items for one month. Export to CSV after editing.")
        default_cf = pd.DataFrame({"Type": ["Inflow", "Outflow"], "Item": ["Sales", "Rent"], "Amount": [revenue, 15000.0]})
        cf = st.data_editor(default_cf, num_rows="dynamic", use_container_width=True, key="cf_table", help="Edit or add rows: Type must be 'Inflow' or 'Outflow'.")
        try:
            inflows = cf.loc[cf["Type"].str.lower() == "inflow", "Amount"].astype(float).sum()
            outflows = cf.loc[cf["Type"].str.lower() == "outflow", "Amount"].astype(float).sum()
            net_cf = inflows - outflows
        except Exception:
            inflows = 0.0
            outflows = 0.0
            net_cf = 0.0

        k1, k2, k3 = st.columns(3)
        k1.metric("Total inflows", format_money(inflows))
        k2.metric("Total outflows", format_money(outflows))
        k3.metric("Net cash flow", format_money(net_cf))

        st.download_button("⬇️ Export Cash Flow CSV", data=cf.to_csv(index=False).encode("utf-8"), file_name="cash_flow.csv")

    # Breakeven
    with tabs[2]:
        st.subheader("Break-even Analysis")
        fixed = st.number_input("Fixed costs (monthly, R)", min_value=0.0, value=40000.0, step=500.0, help="Monthly fixed costs that do not vary with units sold.")
        unit_price = st.number_input("Unit price (R)", min_value=0.0, value=250.0, step=5.0, help="Selling price per unit.")
        var_cost = st.number_input("Variable cost per unit (R)", min_value=0.0, value=120.0, step=5.0, help="Variable cost incurred for each unit sold.")

        cont_margin = max(0.0, unit_price - var_cost)
        be_units = (fixed / cont_margin) if cont_margin > 0 else float("inf")
        st.metric("Break-even units", f"{be_units:,.1f}", help="Number of units you must sell to cover fixed costs.")

        # Profit vs units chart
        max_units = int(be_units * 2) if math.isfinite(be_units) and be_units > 0 else 1000
        units = np.arange(0, max(10, max_units + 1))
        profit = units * cont_margin - fixed
        if HAS_MPL:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.plot(units, profit, color="#2563eb")
            ax.axhline(0, linestyle="--", color="gray")
            ax.set_title("Profit vs Units")
            ax.set_xlabel("Units")
            ax.set_ylabel("Profit (R)")
            st.pyplot(fig)

    # Pricing helper
    with tabs[3]:
        st.subheader("Pricing Helper")
        target_margin = st.slider("Target margin %", 0, 90, 40, help="Desired gross margin percentage.")
        total_unit_cost = st.number_input("Total unit cost (R)", min_value=0.0, value=150.0, step=5.0, help="Total cost per unit including variable costs and allocated fixed costs.")
        vat_pct = st.slider("VAT %", 0, 25, 15, help="VAT percentage to include in the final price.")

        price_excl = total_unit_cost / (1 - target_margin / 100.0) if target_margin < 100 else float("inf")
        price_incl = price_excl * (1 + vat_pct / 100.0)
        k1, k2 = st.columns(2)
        k1.metric("Recommended price (ex VAT)", format_money(price_excl))
        k2.metric("Recommended price (inc VAT)", format_money(price_incl))

    # Payroll estimator
    with tabs[4]:
        st.subheader("Payroll Estimator")
        num_employees = st.number_input("Number of employees", min_value=0, value=5, step=1, help="Total full-time equivalent employees.")
        avg_salary = st.number_input("Average monthly salary (R)", min_value=0.0, value=12000.0, step=100.0, help="Average gross monthly salary per employee.")
        employer_contrib_pct = st.slider("Employer contributions % (benefits)", 0, 30, 10, help="Additional employer costs as a percentage of salary (pension, benefits).")
        total_payroll = num_employees * avg_salary * (1 + employer_contrib_pct / 100.0)
        st.metric("Estimated monthly payroll cost", format_money(total_payroll))

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# PAGE: Premium Modules
# ---------------------------
def page_premium():
    st.title(PAGES["premium"])
    st.write(SECTION_TEXT["premium"])
    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    # Placeholder gating
    if not st.session_state.authed:
        st.info("Premium modules are gated. This demo allows toggling to simulate unlocking.")
        if st.button("Unlock premium (demo)"):
            st.session_state.authed = True
        st.markdown("</div>", unsafe_allow_html=True)
        return

    tabs = st.tabs(["Monte Carlo Portfolio", "Tax Optimizer Ideas", "Advanced Exports"])

    # Monte Carlo Portfolio simulator
    with tabs[0]:
        st.subheader("Monte Carlo Portfolio Simulator")
        start_bal = st.number_input("Starting balance (R)", min_value=0.0, value=100000.0, step=1000.0, help="Initial portfolio balance.")
        monthly_add = st.number_input("Monthly contribution (R)", min_value=0.0, value=3000.0, step=100.0, help="Monthly additions to portfolio.")
        years = st.slider("Years", 1, 50, 20, help="Simulation horizon in years.")
        avg_ret = st.slider("Avg annual return %", -5, 20, 9, help="Expected average return (nominal).")
        vol = st.slider("Annual volatility %", 1, 50, 18, help="Expected annual volatility (standard deviation).")
        sims = st.number_input("Simulations", min_value=100, max_value=5000, value=1000, step=100, help="Number of Monte Carlo simulation runs.")

        np.random.seed(1234)
        months = years * 12
        m_mu = avg_ret / 100.0 / 12.0
        m_sigma = vol / 100.0 / math.sqrt(12.0)
        results = np.zeros(sims)
        for s in range(sims):
            bal = start_bal
            for _ in range(months):
                r = np.random.normal(m_mu, m_sigma)
                bal = bal * (1 + r) + monthly_add
            results[s] = bal

        p5, p50, p95 = np.percentile(results, [5, 50, 95])
        st.metric("5th percentile", format_money(p5))
        st.metric("Median", format_money(p50))
        st.metric("95th percentile", format_money(p95))

        if HAS_MPL:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.hist(results, bins=60, color="#2563eb")
            ax.set_title("Ending Balance Distribution")
            st.pyplot(fig)

    # Tax optimizer ideas
    with tabs[1]:
        st.subheader("Tax Optimizer — Illustrative Strategies")
        salary = st.number_input("Annual salary (R)", min_value=0.0, value=700000.0, step=1000.0, help="Baseline salary used for illustrative savings calculations.")
        base_tax = salary * 0.24  # illustrative baseline
        st.metric("Baseline tax (illustrative)", format_money(base_tax))
        st.caption("These toggles are illustrative. Consult a tax advisor before applying any strategy.")

        c1, c2, c3 = st.columns(3)
        with c1:
            opt_ra = st.checkbox("Max RA contribution", help="Increase RA contributions to reduce taxable income within allowable limits.")
            opt_travel = st.checkbox("Optimized travel allowance", help="Re-structure travel allowance to reduce taxable portion where legal.")
        with c2:
            opt_tfsa = st.checkbox("Max TFSA", help="Shift taxable interest/income into tax-efficient wrappers like TFSA.")
            opt_med = st.checkbox("Medical credits", help="Identify medical expenses or credits that may reduce tax.")
        with c3:
            opt_solar = st.checkbox("Solar incentive", help="Capex incentives for solar installations (check local rules).")
            opt_learn = st.checkbox("Learnership allowance", help="SME learnership incentives and allowances.")

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

        st.metric("Estimated savings (illustrative)", format_money(savings))
        st.metric("Post-strategy tax (illustrative)", format_money(max(0.0, base_tax - savings)))

    # Advanced exports
    with tabs[2]:
        st.subheader("Advanced Exports & Reports")
        st.write("Bundle multiple snapshots into a single export for offline review or sharing.")
        df = pd.DataFrame({
            "module": ["tax", "investments", "sme"],
            "snapshot": ["Tax calc snapshot", "Future value snapshot", "KPI snapshot"],
            "value_R": [12345.0, 67890.0, 23456.0],
        })
        st.dataframe(df)
        st.download_button("Download report CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="finai_report.csv")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# Router
# ---------------------------
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


# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    router()


# ---------------------------
# Recommended requirements.txt
# ---------------------------
# Create a requirements.txt file with:
# streamlit
# matplotlib
# pandas
# numpy
# (optional extras: scikit-learn, altair, plotly)
