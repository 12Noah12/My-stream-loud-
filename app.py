import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# =============================
# NAVIGATION
# =============================
PAGES = {
    "home": "Home",
    "tax": "Tax Optimization",
    "investments": "Investments",
    "sme": "SME Dashboard",
    "premium": "Premium Modules",
}

if "page" not in st.session_state:
    st.session_state.page = "home"

# =============================
# GLOBAL STYLES (single injected block)
# =============================
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

st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 6rem; }}

    /* Navbar */
    .navbar {{
      position: fixed; top: 0; left: 0; width: 100%;
      background: rgba(255,255,255,0.9);
      backdrop-filter: blur(10px);
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      padding: 0.7rem 1.5rem; display: flex; justify-content: space-between; align-items: center; z-index: 1000;
    }}
    .navbar .logo {{ font-weight: 800; font-size: 1.1rem; color: #2563eb; letter-spacing: .3px; }}
    .nav-links {{ display: flex; gap: .5rem; }}
    .nav-button button {{
      background: none; border: none; font-weight: 700; font-size: .95rem;
      padding: .35rem .8rem; border-radius: 10px; cursor: pointer; transition: background .25s;
    }}
    .nav-button button:hover {{ background: rgba(37,99,235,.12); }}

    /* Background gradient per page */
    body {{ background: {BG_STYLES[st.session_state.page]}; color: white; }}

    /* Card layout: single big rectangle cut into sections */
    .mega-rect {{
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 20px; padding: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }}
    .grid {{ display: grid; gap: 1rem; }}
    @media(min-width: 1200px) {{
      .grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
      .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
    }}

    .card {{
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px; padding: 1rem; transition: transform .15s, box-shadow .15s;
    }}
    .card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.2); }}

    .kpi {{
      display:flex; align-items:center; gap:.75rem; font-weight:700; font-size:1.1rem;
      background: rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
      padding:.8rem 1rem; border-radius:12px;
    }}

    input, select, textarea {{ color: #111; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# NAVBAR (uses native Streamlit buttons for state changes)
# =============================
with st.container():
    st.markdown(
        """
        <div class="navbar">
            <div class="logo">💡 FinAI</div>
            <div class="nav-links">
                <!-- Buttons rendered by Streamlit below -->
            </div>
            <div class="dots">⋮</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

cols = st.columns(len(PAGES))
for i, (key, label) in enumerate(PAGES.items()):
    with cols[i]:
        if st.button(label, key=f"btn-{key}"):
            st.session_state.page = key

# Re-apply background per current page state
st.markdown(
    f"""
    <style>
    body {{ background: {BG_STYLES[st.session_state.page]}; color: white; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# UTILITIES
# =============================
@st.cache_data(show_spinner=False)
def future_value(P: float, r: float, n_years: int, m: int = 12) -> float:
    """FV of monthly contributions P at nominal annual rate r (as decimal), comp m times."""
    if r == 0:
        return P * m * n_years
    i = r / m
    N = m * n_years
    return P * ((1 + i) ** N - 1) / i

@st.cache_data(show_spinner=False)
def compound_growth_once(principal: float, r: float, years: float) -> float:
    return principal * ((1 + r) ** years)

def format_money(x: float) -> str:
    return f"R{x:,.2f}"

# =============================
# TAX SECTION HELPERS (SA defaults but editable)
# =============================
@dataclass
class TaxBracket:
    up_to: float
    rate: float  # decimal

SA_DEFAULT_2025 = [
    TaxBracket(237100, 0.18),
    TaxBracket(370500, 0.26),
    TaxBracket(512800, 0.31),
    TaxBracket(673000, 0.36),
    TaxBracket(857900, 0.39),
    TaxBracket(1817000, 0.41),
    TaxBracket(float("inf"), 0.45),
]

PRIMARY_REBATE = 17835  # editable by user

def calc_tax(income: float, brackets: List[TaxBracket]) -> float:
    tax = 0.0
    prev = 0.0
    for b in brackets:
        slab = min(income, b.up_to) - prev
        if slab > 0:
            tax += slab * b.rate
            prev = b.up_to
        if income <= b.up_to:
            break
    return max(0.0, tax)

# =============================
# PAGES
# =============================

def page_home():
    st.title(PAGES["home"])
    st.write(SECTION_TEXT["home"])

    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)
    st.text_input("🔍 Ask FinAI anything...", key="ai_query", placeholder="e.g., How can I reduce my tax legally?")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Active Users", "4,218", "+12%")
    with c2:
        st.metric("Avg Session", "06:14", "+8%")
    with c3:
        st.metric("Conversion", "3.9%", "+0.3%")

    st.markdown("</div>", unsafe_allow_html=True)


def page_tax():
    st.title(PAGES["tax"])
    st.write(SECTION_TEXT["tax"])

    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)
    tabs = st.tabs(["Income Tax", "VAT", "Capital Gains", "Allowances & Deductions"])

    # ----------------- Income Tax -----------------
    with tabs[0]:
        colL, colR = st.columns([1, 1])
        with colL:
            st.subheader("Income Tax Estimator 🇿🇦 (Editable Brackets)")
            income = st.number_input("Annual taxable income (R)", min_value=0.0, value=650000.0, step=1000.0)
            rebate = st.number_input("Primary rebate (R)", min_value=0.0, value=float(PRIMARY_REBATE), step=100.0)

            st.caption("Tax brackets (upper bound & rate). Edit as needed.")
            df_br = pd.DataFrame(
                {
                    "up_to": [b.up_to if math.isfinite(b.up_to) else 9_999_999_999 for b in SA_DEFAULT_2025],
                    "rate_%": [b.rate * 100 for b in SA_DEFAULT_2025],
                }
            )
            edited = st.data_editor(df_br, num_rows="dynamic", use_container_width=True)
            brackets = [TaxBracket(float(row["up_to"]), float(row["rate_%"]) / 100) for _, row in edited.iterrows()]

            gross_tax = calc_tax(income, brackets)
            net_tax = max(0.0, gross_tax - rebate)
            eff_rate = (net_tax / income * 100) if income > 0 else 0.0

            st.markdown("---")
            st.write("**Results**")
            k1, k2, k3 = st.columns(3)
            k1.metric("Gross tax", format_money(gross_tax))
            k2.metric("Net tax (after rebate)", format_money(net_tax))
            k3.metric("Effective rate", f"{eff_rate:.2f}%")

        with colR:
            st.subheader("PAYE / Monthly View")
            months = st.slider("Months employed this year", 1, 12, 12)
            paye = net_tax * months / 12
            monthly_eff = paye / months if months else 0
            st.metric("Estimated PAYE (YTD)", format_money(paye))
            st.metric("Avg tax / month", format_money(monthly_eff))

            # Simple bar visual
            fig, ax = plt.subplots()
            ax.bar(["Income", "Net Tax"], [income, net_tax])
            ax.set_title("Income vs Tax")
            st.pyplot(fig)

    # ----------------- VAT -----------------
    with tabs[1]:
        st.subheader("VAT Calculator")
        c1, c2, c3 = st.columns(3)
        with c1:
            base = st.number_input("Amount (ex VAT)", min_value=0.0, value=1000.0, step=10.0)
        with c2:
            vat_rate = st.number_input("VAT %", min_value=0.0, value=15.0, step=0.5)
        with c3:
            include = st.toggle("Input is VAT-inclusive?", value=False)

        r = vat_rate / 100
        if include:
            ex = base / (1 + r)
            vat = base - ex
            inc = base
        else:
            ex = base
            vat = base * r
            inc = base * (1 + r)

        k1, k2, k3 = st.columns(3)
        k1.metric("Excl. VAT", format_money(ex))
        k2.metric("VAT", format_money(vat))
        k3.metric("Incl. VAT", format_money(inc))

    # ----------------- Capital Gains -----------------
    with tabs[2]:
        st.subheader("Capital Gains Tax Estimator")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            proceeds = st.number_input("Proceeds", min_value=0.0, value=250000.0, step=1000.0)
        with c2:
            base_cost = st.number_input("Base cost", min_value=0.0, value=120000.0, step=1000.0)
        with c3:
            inclusion_rate = st.slider("Inclusion rate % (Individuals ~40, Co ~80)", 0, 100, 40)
        with c4:
            marginal_tax = st.slider("Marginal income tax %", 0, 55, 36)

        gain = max(0.0, proceeds - base_cost)
        inc_portion = gain * (inclusion_rate / 100)
        cgt = inc_portion * (marginal_tax / 100)

        k1, k2, k3 = st.columns(3)
        k1.metric("Capital gain", format_money(gain))
        k2.metric("Taxable portion", format_money(inc_portion))
        k3.metric("Estimated CGT", format_money(cgt))

    # ----------------- Deductions -----------------
    with tabs[3]:
        st.subheader("Allowances & Deductions")
        st.caption("Quick estimate of taxable income after common deductions.")
        col1, col2 = st.columns(2)
        with col1:
            gross = st.number_input("Gross salary (R)", min_value=0.0, value=700000.0, step=1000.0)
            ra = st.number_input("Retirement annuity contributions (R)", min_value=0.0, value=30000.0, step=500.0)
            med_aid = st.number_input("Medical credits (R)", min_value=0.0, value=12000.0, step=100.0)
        with col2:
            travel_allow = st.number_input("Travel allowance (taxable portion R)", min_value=0.0, value=20000.0, step=500.0)
            other_ded = st.number_input("Other deductible (R)", min_value=0.0, value=5000.0, step=100.0)

        taxable = max(0.0, gross - ra - other_ded - med_aid + travel_allow)
        st.metric("Estimated taxable income", format_money(taxable))

    st.markdown("</div>", unsafe_allow_html=True)


def page_investments():
    st.title(PAGES["investments"])
    st.write(SECTION_TEXT["investments"])

    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)
    tabs = st.tabs(["Compound Growth", "Retirement Planner", "DCA Simulator"]) 

    # ------------- Compound Growth -------------
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Compound Growth Calculator")
            principal = st.number_input("Starting amount (R)", min_value=0.0, value=50000.0, step=1000.0)
            monthly = st.number_input("Monthly contribution (R)", min_value=0.0, value=3000.0, step=100.0)
            years = st.slider("Years", 1, 50, 20)
            rate = st.slider("Expected annual return %", 0, 25, 10)

            fv_principal = compound_growth_once(principal, rate / 100, years)
            fv_contrib = future_value(monthly, rate / 100, years, 12)
            total = fv_principal + fv_contrib

            k1, k2, k3 = st.columns(3)
            k1.metric("Future value (principal)", format_money(fv_principal))
            k2.metric("Future value (contrib)", format_money(fv_contrib))
            k3.metric("Total future value", format_money(total))

        with col2:
            # Growth curve
            balances = []
            bal = principal
            m_rate = (rate / 100) / 12
            months = years * 12
            for m in range(months + 1):
                balances.append(bal)
                bal = bal * (1 + m_rate) + monthly
            fig, ax = plt.subplots()
            ax.plot([i / 12 for i in range(len(balances))], balances)
            ax.set_title("Projected Balance Over Time")
            ax.set_xlabel("Years")
            ax.set_ylabel("Balance (R)")
            st.pyplot(fig)

    # ------------- Retirement Planner -------------
    with tabs[1]:
        st.subheader("Retirement Planner")
        c1, c2 = st.columns(2)
        with c1:
            age_now = st.slider("Current age", 16, 70, 18)
            age_ret = st.slider("Retirement age", 45, 75, 60)
            monthly = st.number_input("Monthly contribution (R)", min_value=0.0, value=2800.0, step=100.0)
            current = st.number_input("Current savings (R)", min_value=0.0, value=556780.0, step=1000.0)
            exp_return = st.slider("Expected return %", 0, 20, 10)
            exp_infl = st.slider("Inflation %", 0, 12, 5)
        with c2:
            years = max(0, age_ret - age_now)
            fv_cur = compound_growth_once(current, exp_return / 100, years)
            fv_contrib = future_value(monthly, exp_return / 100, years, 12)
            nominal_total = fv_cur + fv_contrib
            real_total = nominal_total / ((1 + exp_infl / 100) ** years)

            st.metric("Nominal nest egg", format_money(nominal_total))
            st.metric("Real (today R)", format_money(real_total))

            # Simple drawdown estimate
            swr = st.slider("Safe withdrawal rate %", 2, 6, 4)
            real_income_year = real_total * (swr / 100)
            st.metric("Est. annual retirement income (today R)", format_money(real_income_year))

    # ------------- DCA Simulator -------------
    with tabs[2]:
        st.subheader("DCA (Dollar-Cost Averaging) Simulator")
        c1, c2 = st.columns(2)
        with c1:
            months = st.slider("Months", 12, 360, 120)
            monthly = st.number_input("Monthly buy (R)", min_value=0.0, value=2000.0, step=100.0)
            mu = st.slider("Avg annual return %", -10, 20, 8)
            sigma = st.slider("Volatility % (annualized)", 5, 60, 20)
        with c2:
            # Simulate a random walk price series
            np.random.seed(42)
            dt = 1 / 12
            mu_m = mu / 100
            sigma_m = sigma / 100
            prices = [100.0]
            for _ in range(months):
                drift = (mu_m - 0.5 * sigma_m ** 2) * dt
                shock = sigma_m * np.sqrt(dt) * np.random.randn()
                prices.append(prices[-1] * np.exp(drift + shock))

            units = 0.0
            for p in prices[1:]:
                if p > 0:
                    units += monthly / p
            final_value = units * prices[-1]
            invested = monthly * months

            k1, k2, k3 = st.columns(3)
            k1.metric("Total invested", format_money(invested))
            k2.metric("Portfolio value", format_money(final_value))
            k3.metric("Gain", format_money(final_value - invested))

            fig, ax = plt.subplots()
            ax.plot(prices)
            ax.set_title("Simulated Price (Geometric Brownian Motion)")
            ax.set_xlabel("Months")
            ax.set_ylabel("Price")
            st.pyplot(fig)

    st.markdown("</div>", unsafe_allow_html=True)


def page_sme():
    st.title(PAGES["sme"])
    st.write(SECTION_TEXT["sme"])

    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)
    tabs = st.tabs(["KPIs", "Cash Flow", "Breakeven", "Pricing Helper"]) 

    # ------------- KPIs -------------
    with tabs[0]:
        st.subheader("Business KPIs")
        c1, c2, c3, c4 = st.columns(4)
        rev = c1.number_input("Monthly revenue (R)", 0.0, value=120000.0, step=1000.0)
        cogs = c2.number_input("COGS (R)", 0.0, value=50000.0, step=500.0)
        opex = c3.number_input("Operating expenses (R)", 0.0, value=30000.0, step=500.0)
        tax_rate = c4.slider("Tax %", 0, 55, 28)

        gross_profit = max(0.0, rev - cogs)
        ebit = max(0.0, gross_profit - opex)
        tax = ebit * (tax_rate / 100)
        net = max(0.0, ebit - tax)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Gross Profit", format_money(gross_profit))
        k2.metric("EBIT", format_money(ebit))
        k3.metric("Tax", format_money(tax))
        k4.metric("Net Profit", format_money(net))

    # ------------- Cash Flow -------------
    with tabs[1]:
        st.subheader("Cash Flow Builder")
        st.caption("Enter line items for one month. Export to CSV below.")
        default_cf = pd.DataFrame(
            {
                "Type": ["Inflow", "Outflow"],
                "Item": ["Sales", "Rent"],
                "Amount": [120000, 15000],
            }
        )
        cf = st.data_editor(default_cf, num_rows="dynamic", use_container_width=True, key="cf_tbl")
        inflow = cf.loc[cf["Type"].str.lower().eq("inflow"), "Amount"].sum()
        outflow = cf.loc[cf["Type"].str.lower().eq("outflow"), "Amount"].sum()
        net = inflow - outflow
        k1, k2, k3 = st.columns(3)
        k1.metric("Total inflows", format_money(inflow))
        k2.metric("Total outflows", format_money(outflow))
        k3.metric("Net cash flow", format_money(net))

        st.download_button(
            "⬇️ Export Cash Flow CSV",
            data=cf.to_csv(index=False).encode("utf-8"),
            file_name="cash_flow.csv",
            mime="text/csv",
        )

    # ------------- Breakeven -------------
    with tabs[2]:
        st.subheader("Breakeven Analysis")
        c1, c2, c3 = st.columns(3)
        fixed = c1.number_input("Fixed costs (R)", min_value=0.0, value=40000.0, step=500.0)
        price = c2.number_input("Unit price (R)", min_value=0.0, value=250.0, step=10.0)
        var = c3.number_input("Variable cost / unit (R)", min_value=0.0, value=120.0, step=5.0)

        cm = max(0.0, price - var)
        be_units = (fixed / cm) if cm > 0 else float("inf")
        st.metric("Break-even units", f"{be_units:,.1f}")

        # Visualize profit vs units
        units = np.arange(0, max(1, int(be_units * 2) if math.isfinite(be_units) else 1000))
        profit = units * (price - var) - fixed
        fig, ax = plt.subplots()
        ax.plot(units, profit)
        ax.axhline(0, linestyle="--")
        ax.set_title("Profit vs Units Sold")
        ax.set_xlabel("Units")
        ax.set_ylabel("Profit (R)")
        st.pyplot(fig)

    # ------------- Pricing Helper -------------
    with tabs[3]:
        st.subheader("Pricing Helper")
        c1, c2, c3 = st.columns(3)
        target_margin = c1.slider("Target margin %", 0, 90, 40)
        cost = c2.number_input("Total unit cost (R)", min_value=0.0, value=150.0, step=5.0)
        vat_rate = c3.slider("VAT %", 0, 25, 15)

        price_ex = cost / (1 - target_margin / 100) if target_margin < 100 else float("inf")
        price_inc = price_ex * (1 + vat_rate / 100)

        k1, k2 = st.columns(2)
        k1.metric("Recommended price (ex VAT)", format_money(price_ex))
        k2.metric("Recommended price (inc VAT)", format_money(price_inc))

    st.markdown("</div>", unsafe_allow_html=True)


def page_premium():
    st.title(PAGES["premium"])
    st.write(SECTION_TEXT["premium"])

    st.markdown("<div class='mega-rect'>", unsafe_allow_html=True)

    tabs = st.tabs(["Monte Carlo Portfolio", "Tax Optimizer (Ideas)"])

    # ------------- Monte Carlo -------------
    with tabs[0]:
        st.subheader("Monte Carlo Portfolio Simulator")
        c1, c2 = st.columns(2)
        with c1:
            start = st.number_input("Starting balance (R)", min_value=0.0, value=100000.0, step=1000.0)
            contrib = st.number_input("Monthly contribution (R)", min_value=0.0, value=3000.0, step=100.0)
            years = st.slider("Years", 1, 50, 20)
            mu = st.slider("Avg annual return %", -5, 20, 9)
            vol = st.slider("Volatility % (annual)", 5, 50, 18)
            trials = st.slider("Simulations", 100, 5000, 1000, step=100)
        with c2:
            results = []
            m_mu = mu / 100 / 12
            m_vol = vol / 100 / math.sqrt(12)
            months = years * 12
            np.random.seed(123)
            for _ in range(trials):
                bal = start
                for _ in range(months):
                    r = np.random.normal(m_mu, m_vol)
                    bal = bal * (1 + r) + contrib
                results.append(bal)
            results = np.array(results)
            p5, p50, p95 = np.percentile(results, [5, 50, 95])
            st.metric("5th percentile", format_money(p5))
            st.metric("Median", format_money(p50))
            st.metric("95th percentile", format_money(p95))

            fig, ax = plt.subplots()
            ax.hist(results, bins=40)
            ax.set_title("Ending Balance Distribution")
            ax.set_xlabel("Balance (R)")
            ax.set_ylabel("Frequency")
            st.pyplot(fig)

    # ------------- Tax Optimizer Ideas -------------
    with tabs[1]:
        st.subheader("Tax Optimizer – Strategy Ideas")
        st.caption("Toggle strategies to see estimated savings. Values are illustrative.")
        salary = st.number_input("Annual salary (R)", min_value=0.0, value=700000.0, step=1000.0)
        base_tax = salary * 0.24  # simple baseline for illustration
        st.metric("Baseline tax (illustrative)", format_money(base_tax))

        col1, col2, col3 = st.columns(3)
        ra = col1.toggle("Max RA contribution")
        tfsa = col2.toggle("Max TFSA, shift taxable interest")
        med = col3.toggle("Medical credits / Gap cover")
        travel = col1.toggle("Optimized travel allowance")
        solar = col2.toggle("Solar upgrade incentive")
        learn = col3.toggle("Learnership allowance (SME)")

        savings = 0.0
        if ra:
            savings += 25000
        if tfsa:
            savings += 6000
        if med:
            savings += 4000
        if travel:
            savings += 8000
        if solar:
            savings += 15000
        if learn:
            savings += 10000

        st.metric("Estimated savings (illustrative)", format_money(savings))
        st.metric("Post-strategy tax (illustrative)", format_money(max(0.0, base_tax - savings)))

    st.markdown("</div>", unsafe_allow_html=True)

# =============================
# ROUTER
# =============================

if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "tax":
    page_tax()
elif st.session_state.page == "investments":
    page_investments()
elif st.session_state.page == "sme":
    page_sme()
elif st.session_state.page == "premium":
    page_premium()
else:
    page_home()

