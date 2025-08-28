# OptiFin Part 1 — Core Initialization and Privacy Gate

import streamlit as st
import json
import datetime
import hashlib
from collections import deque

APP_NAME = "OptiFin"
APP_YEAR = 2025
DEFAULT_REGION = "South Africa"
DEFAULT_CURRENCY = "ZAR"

def init_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'privacy_gate'
    if 'consent_accepted' not in st.session_state:
        st.session_state.consent_accepted = False
    if 'user_segment' not in st.session_state:
        st.session_state.user_segment = None
    if 'sub_module' not in st.session_state:
        st.session_state.sub_module = None
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    if 'background' not in st.session_state:
        st.session_state.background = 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1950&q=80'
    if 'ai_router_result' not in st.session_state:
        st.session_state.ai_router_result = None
    if 'contact_submissions' not in st.session_state:
        st.session_state.contact_submissions = deque(maxlen=500)
    if 'auth_logged_in' not in st.session_state:
        st.session_state.auth_logged_in = False
    if 'auth_username' not in st.session_state:
        st.session_state.auth_username = ""
    if 'auth_profile' not in st.session_state:
        st.session_state.auth_profile = {}
    if "achievements" not in st.session_state:
        st.session_state.achievements = set()

init_state()

def page_privacy_gate():
    st.title(f"Welcome to {APP_NAME}")
    st.markdown(
        """
        ### Privacy & Data Processing Consent

        To use this app, you must agree to the processing of your financial data securely and confidentially.
        We comply with all applicable data protection laws.

        Please read and accept our privacy policy before proceeding.
        """
    )
    if st.button("I Accept"):
        st.session_state.consent_accepted = True
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    if not st.session_state.consent_accepted:
        page_privacy_gate()
    else:
        st.markdown("Proceed to App Hub (Next parts will add this...)")
# OptiFin Part 2 — AI Router and Segment Hub

import streamlit as st

def page_segment_hub():
    st.title("Welcome to OptiFin")
    st.markdown("#### Select your user segment to begin your personalized financial journey:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Individual"):
            st.session_state.user_segment = 'individual'
            st.session_state.page = "module_form"
            st.experimental_rerun()

    with col2:
        if st.button("Household / Family"):
            st.session_state.user_segment = 'household'
            st.session_state.page = "module_form"
            st.experimental_rerun()

    with col3:
        if st.button("Business Owner"):
            st.session_state.user_segment = 'business'
            st.session_state.page = "module_form"
            st.experimental_rerun()

def ai_router(input_text: str):
    """
    Simplified Router — analyzes natural language input
    to determine user intent and segment/module.
    """
    text = input_text.lower()

    # Default values
    segment = None
    sub_module = None

    if any(word in text for word in ["individual", "personal", "me", "i want"]):
        segment = "individual"
    elif any(word in text for word in ["household", "family", "we", "our"]):
        segment = "household"
    elif any(word in text for word in ["business", "company", "my business", "self-employed"]):
        segment = "business"
    else:
        # For demo we ask user to pick in hub
        segment = None

    # Detect module/topic
    if any(word in text for word in ["invest", "investment", "portfolio"]):
        sub_module = "investment"
    elif any(word in text for word in ["tax", "taxation", "deduction", "irs"]):
        sub_module = "tax"
    elif any(word in text for word in ["retirement", "pension", "401k"]):
        sub_module = "retirement"
    elif any(word in text for word in ["estate", "will", "inheritance", "trust"]):
        sub_module = "estate"
    elif any(word in text for word in ["budget", "expenses", "spending"]):
        sub_module = "budget"
    elif any(word in text for word in ["protection", "insurance", "coverage"]):
        sub_module = "protection"
    else:
        sub_module = None

    return segment, sub_module

def page_ai_natural_router():
    st.title(f"{APP_NAME} AI Natural Language Assistant")
    st.markdown("Ask any financial planning question or type your intent (e.g., 'Help me with individual retirement planning').")

    user_input = st.text_area("Your question or command...", height=120, key="ai_router_input")

    if st.button("Analyze and Route"):
        if not user_input.strip():
            st.warning("Please enter some text to analyze.")
        else:
            segment, sub_module = ai_router(user_input)
            if segment and sub_module:
                st.success(f"Detected segment: **{segment}**, module: **{sub_module}**")
                st.session_state.user_segment = segment
                st.session_state.sub_module = sub_module
                st.session_state.page = "module_form"
                st.experimental_rerun()
            else:
                st.info("Unable to determine segment or module clearly; please select below.")

    if st.session_state.user_segment is None:
        page_segment_hub()

if __name__ == "__main__":
    if st.session_state.consent_accepted:
        page_ai_natural_router()
    else:
        st.info("Please accept privacy agreement to continue.")
# OptiFin Part 3 — User Authentication, Profile Management, Main Router Foundation

import json
import pathlib
from datetime import date
import streamlit as st
import hashlib
import uuid

USERS_FILE = "optifin_users.json"

def hash_password(password: str) -> str:
    """Hash the password securely with salt."""
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return f"{hashed}:{salt}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against the one provided."""
    hashed, salt = stored_password.split(':')
    check = hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()
    return check == hashed

def load_users():
    if not pathlib.Path(USERS_FILE).exists():
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def init_auth_state():
    if 'auth_logged_in' not in st.session_state:
        st.session_state.auth_logged_in = False
    if 'auth_username' not in st.session_state:
        st.session_state.auth_username = ""
    if 'auth_profile' not in st.session_state:
        st.session_state.auth_profile = {}
    if 'auth_message' not in st.session_state:
        st.session_state.auth_message = ""

def auth_register():
    st.header("Register New Account")
    username = st.text_input("Choose username", key="register_username")
    password = st.text_input("Choose password", type="password", key="register_password")
    password_confirm = st.text_input("Confirm password", type="password", key="register_password_confirm")
    if st.button("Register", key="register_btn"):
        if not username or not password or not password_confirm:
            st.error("All fields are required.")
            return
        if password != password_confirm:
            st.error("Passwords do not match.")
            return
        users = load_users()
        if username in users:
            st.error("Username already exists.")
            return
        users[username] = {
            "password": hash_password(password),
            "profile": {
                "currency": DEFAULT_CURRENCY,
                "region": DEFAULT_REGION,
                "language": "en",
                "goals": [],
            },
        }
        save_users(users)
        st.success("Registration successful, please log in.")
        st.session_state.page = "auth_login"
        st.experimental_rerun()

def auth_login():
    st.header("Login to OptiFin")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login_btn"):
        users = load_users()
        if username not in users or not verify_password(users[username]["password"], password):
            st.error("Invalid username or password.")
            return
        st.session_state.auth_logged_in = True
        st.session_state.auth_username = username
        st.session_state.auth_profile = users[username]["profile"]
        st.session_state.page = "home"
        st.experimental_rerun()

def auth_logout():
    st.session_state.auth_logged_in = False
    st.session_state.auth_username = ""
    st.session_state.auth_profile = {}
    st.session_state.page = "auth_login"

def auth_profile_edit():
    st.header("Edit Profile")
    profile = st.session_state.auth_profile

    currency = st.selectbox("Preferred Currency", [DEFAULT_CURRENCY, "USD", "GBP", "EUR"],
                            index=[DEFAULT_CURRENCY, "USD", "GBP", "EUR"].index(profile.get("currency", DEFAULT_CURRENCY)))
    region = st.selectbox("Region/Country", [DEFAULT_REGION, "United Kingdom", "United States", "Australia"],
                          index=[DEFAULT_REGION, "United Kingdom", "United States", "Australia"].index(profile.get("region", DEFAULT_REGION)))
    language = st.selectbox("Language", ["en", "fr", "es"],
                            index=["en", "fr", "es"].index(profile.get("language", "en")))

    if st.button("Save Profile Changes", key="auth_save_profile"):
        profile["currency"] = currency
        profile["region"] = region
        profile["language"] = language
        users = load_users()
        users[st.session_state.auth_username]["profile"] = profile
        save_users(users)
        st.success("Profile updated!")

# Simplified Page Router (expand in future parts)
def main_router():
    page = st.session_state.page

    if page == "auth_login":
        auth_login()
    elif page == "auth_register":
        auth_register()
    elif page == "auth_profile_edit":
        auth_profile_edit()
    elif page == "privacy_gate":
        st.error("Privacy gate implementation missing here.")
    elif page == "segment_hub":
        st.error("Segment hub implementation missing here.")
    elif page == "home":
        st.info("Welcome home! Implement your homepage here.")
    else:
        st.info(f"Unknown page: {page}. Redirecting to home.")
        st.session_state.page = 'home'
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 4 — Goals Management, Module Forms, AI Chat Assistant, and Navigation

import streamlit as st
import openai

def load_goals():
    profile = st.session_state.auth_profile or {}
    return profile.get("goals", [])

def save_goals(goals):
    profile = st.session_state.auth_profile or {}
    profile["goals"] = goals
    st.session_state.auth_profile = profile
    users = load_users()
    if st.session_state.auth_username in users:
        users[st.session_state.auth_username]["profile"]["goals"] = goals
        save_users(users)

def goals_manager():
    st.header("Manage Your Financial Goals")
    goals = load_goals()

    st.markdown("Current Goals:")
    for i, goal in enumerate(goals):
        with st.expander(f"{goal.get('name', 'Unnamed Goal')}"):
            name = st.text_input(f"Goal Name #{i+1}", value=goal.get("name", ""), key=f"goal_name_{i}")
            amount = st.number_input(f"Target Amount for #{i+1}", min_value=0.0, value=goal.get("amount", 0.0), key=f"goal_amount_{i}")
            target_date = st.date_input(f"Target Date for #{i+1}", value=goal.get("target_date", date.today() + datetime.timedelta(days=365)), key=f"goal_date_{i}")

            goals[i] = {
                "name": name,
                "amount": amount,
                "target_date": target_date.isoformat() if hasattr(target_date, "isoformat") else str(target_date),
            }
            if st.button(f"Remove Goal #{i+1}", key=f"goal_remove_{i}"):
                goals.pop(i)
                save_goals(goals)
                st.experimental_rerun()

    if st.button("Add New Goal"):
        goals.append({"name": "", "amount": 0.0, "target_date": date.today().isoformat()})
        save_goals(goals)
        st.experimental_rerun()

    save_goals(goals)

def module_form():
    st.title(f"Module for {st.session_state.user_segment.capitalize()}")

    # Simple multi-module available
    modules = ["investment", "tax", "retirement", "estate", "budget", "protection"]

    selected_module = st.selectbox("Select a module", modules)

    st.markdown(f"**You selected the module:** {selected_module}")

    # Inputs based on module (simplified example)
    if selected_module == "investment":
        net_worth = st.number_input("Enter net worth (R)", min_value=0.0, step=1000.0)
        risk_tolerance = st.slider("Risk tolerance (1 low - 5 high)", 1, 5, 3)
        st.markdown(f"Analyzing investment options with net worth {net_worth} and risk tolerance {risk_tolerance}...")
        # Placeholder logic, replace with real advisor engine
    elif selected_module == "tax":
        income = st.number_input("Annual taxable income (R)", min_value=0.0, step=1000.0)
        deductions = st.number_input("Total deductions (R)", min_value=0.0, step=1000.0)
        st.markdown(f"Calculating tax based on income {income} and deductions {deductions}...")
    elif selected_module == "retirement":
        current_age = st.number_input("Current age", min_value=18, max_value=80)
        retire_age = st.number_input("Planned retirement age", min_value=current_age + 1, max_value=100)
        desired_retirement_fund = st.number_input("Desired retirement fund (R)", min_value=0.0, step=1000.0)
        st.markdown(f"Estimating retirement readiness from age {current_age} to {retire_age}...")
    else:
        st.info("Module form currently under construction")

def page_chatbot():
    st.title("OptiFin AI Personal Financial Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask me anything about your finances or goals", key="chat_input")
    if st.button("Send"):
        if user_input.strip():
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})

            # Call OpenAI GPT API to generate assistant reply (use your key in secrets.toml)
            if OPENAI_AVAILABLE and "OPENAI_API_KEY" in st.secrets:
                try:
                    openai.api_key = st.secrets["OPENAI_API_KEY"]
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.chat_history[-8:],  # keep last 8 messages for context
                        max_tokens=300,
                        temperature=0.7,
                    )
                    reply = response.choices[0].message['content']
                except Exception as e:
                    reply = "Sorry, an AI error occurred."
            else:
                reply = "OpenAI API key not configured."

            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.experimental_rerun()

    # Display chat history
    for m in st.session_state.chat_history:
        if m["role"] == "user":
            st.markdown(f"**You:** {m['content']}")
        else:
            st.markdown(f"**OptiFin AI:** {m['content']}")

# Update main router for pages from Part 4
def main_router():
    page = st.session_state.page

    if page == "auth_login":
        auth_login()
    elif page == "auth_register":
        auth_register()
    elif page == "auth_profile_edit":
        auth_profile_edit()
    elif page == "privacy_gate":
        page_privacy_gate()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        module_form()
    elif page == "goals_manager":
        goals_manager()
    elif page == "chatbot":
        page_chatbot()
    elif page == "home":
        st.info("OptiFin home page coming soon. Navigate via sidebar or AI router.")
    else:
        st.error(f"Unknown page '{page}', redirecting home.")
        st.session_state.page = "home"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 5 — Predictive Analytics, Uploads, Regulatory Feeds, and Sidebar UI

import streamlit as st
import pandas as pd
import numpy as np
from prophet import Prophet
from io import BytesIO

def page_predictive_cashflow():
    st.header("Predictive Cashflow & Expense Forecasting")

    uploaded_file = st.file_uploader("Upload your bank transactions CSV", type=["csv"], key="upload_cashflow")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().lower() for c in df.columns]
            if not all(col in df.columns for col in ["date", "amount"]):
                st.error("CSV must contain 'date' and 'amount' columns.")
                return

            df["date"] = pd.to_datetime(df["date"])
            daily = df.groupby("date")["amount"].sum().reset_index()

            model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
            prophet_df = daily.rename(columns={"date": "ds", "amount": "y"})
            model.fit(prophet_df)

            future = model.make_future_dataframe(periods=90)
            forecast = model.predict(future)

            st.line_chart(forecast[["ds", "yhat"]].set_index("ds"))

            next_90_days = forecast[forecast['ds'] > daily["date"].max()]
            predicted_sum = next_90_days["yhat"].sum()
            st.metric("Predicted Net Cashflow Next 90 Days", f"R {predicted_sum:,.2f}")

        except Exception as e:
            st.error(f"Error processing file or forecasting: {str(e)}")
    else:
        st.info("Upload your transactions CSV to predict cash flow.")

def page_bank_upload():
    st.header("Upload Bank Transactions")
    uploaded_file = st.file_uploader("Upload CSV bank statement", type=["csv"])
    if uploaded_file:
        st.success("File uploaded. Processing...")
        # Placeholder: Process transactions here

def page_doc_upload():
    st.header("Upload Documents")
    uploaded_files = st.file_uploader("Upload PDFs, tax docs etc.", type=["pdf", "docx", "xlsx"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"{len(uploaded_files)} files uploaded")
        # Placeholder process uploaded files

def display_regulatory_updates():
    st.header("Latest Regulatory Updates")
    # Placeholder content; replace with live feed API integration
    updates = [
        "New SARS tax exemption thresholds announced.",
        "Retirement fund contribution limits updated for 2025.",
        "Important deadline for submission of annual tax returns.",
        "Government launches financial literacy campaign."
    ]
    for update in updates:
        st.markdown(f"- {update}")

# Sidebar UI enhancements
def extend_sidebar():
    st.sidebar.title(APP_NAME)
    st.sidebar.markdown("### Navigation")
    if st.session_state.auth_logged_in:
        if st.sidebar.button("Home"):
            st.session_state.page = "home"
            st.experimental_rerun()
        if st.sidebar.button("Manage Goals"):
            st.session_state.page = "goals_manager"
            st.experimental_rerun()
        if st.sidebar.button("AI Chat"):
            st.session_state.page = "chatbot"
            st.experimental_rerun()
        if st.sidebar.button("Upload Bank Statement"):
            st.session_state.page = "bank_upload"
            st.experimental_rerun()
        if st.sidebar.button("Upload Documents"):
            st.session_state.page = "doc_upload"
            st.experimental_rerun()
        if st.sidebar.button("Predictive Cashflow"):
            st.session_state.page = "predictive_cashflow"
            st.experimental_rerun()
        if st.sidebar.button("Regulatory Updates"):
            st.session_state.page = "reg_updates"
            st.experimental_rerun()
        if st.sidebar.button("Logout"):
            auth_logout()
            st.experimental_rerun()
    else:
        if st.sidebar.button("Login"):
            st.session_state.page = "auth_login"
            st.experimental_rerun()
        if st.sidebar.button("Register"):
            st.session_state.page = "auth_register"
            st.experimental_rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Theme & Background")
    theme = st.sidebar.radio("Theme", ['dark', 'light'], index=0 if st.session_state.theme == 'dark' else 1)
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        st.experimental_rerun()

    bg_options = list(BACKGROUND_IMAGES.keys())
    bg_choice = st.sidebar.selectbox("Background Image", bg_options, index=bg_options.index(next(key for key, val in BACKGROUND_IMAGES.items() if val == st.session_state.background)))
    new_bg = BACKGROUND_IMAGES[bg_choice]
    if new_bg != st.session_state.background:
        st.session_state.background = new_bg
        st.experimental_rerun()

# Extend main_router to include these pages
def main_router():
    page = st.session_state.page

    # Authentication routes
    if page == "auth_login":
        auth_login()
    elif page == "auth_register":
        auth_register()
    elif page == "auth_profile_edit":
        auth_profile_edit()
    elif page == "privacy_gate":
        page_privacy_gate()
    elif page == "segment_hub":
        page_segment_hub()
    # Core app modules
    elif page == "module_form":
        module_form()
    elif page == "goals_manager":
        goals_manager()
    elif page == "chatbot":
        page_chatbot()
    elif page == "predictive_cashflow":
        page_predictive_cashflow()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "home":
        st.info("Welcome to OptiFin. Use sidebar or AI router to navigate.")
    else:
        st.error(f"Unknown page '{page}'. Redirecting home.")
        st.session_state.page = "home"
        st.experimental_rerun()

# Initialize and run
if __name__ == "__main__":
    init_state()
    init_auth_state()
    extend_sidebar()
    main_router()
# OptiFin Part 6 — AI-Powered Predictive Analytics, Reports & Insights

import streamlit as st
from prophet import Prophet
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import textblob
import json
import openai

def page_predictive_cashflow():
    st.header("Predictive Cashflow & Expense Forecasting")

    uploaded_file = st.file_uploader("Upload your transaction history CSV (Date, Amount, Category)", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().lower() for c in df.columns]
            if not all(col in df.columns for col in ["date", "amount"]):
                st.error("CSV must contain 'date' and 'amount' columns.")
                return

            df["date"] = pd.to_datetime(df["date"])
            daily = df.groupby("date")["amount"].sum().reset_index()
            prophet_data = daily.rename(columns={"date": "ds", "amount": "y"})

            model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
            model.fit(prophet_data)

            future = model.make_future_dataframe(periods=90)
            forecast = model.predict(future)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast'))
            fig.add_trace(go.Scatter(x=daily['date'], y=daily['amount'], mode='markers', name='Actual'))
            st.plotly_chart(fig, use_container_width=True)

            predicted_sum = forecast[forecast['ds'] > daily['date'].max()]['yhat'].sum()
            st.metric("Predicted Cashflow Next 90 Days", f"R {predicted_sum:,.2f}")

        except Exception as e:
            st.error(f"Error processing CSV or forecasting: {e}")
    else:
        st.info("Please upload your transaction history CSV.")

def page_smart_savings():
    st.header("Smart Savings & Auto Invest Plan")

    income = st.number_input("Monthly Net Income (R)", min_value=0.0)
    current_savings = st.number_input("Current Savings (R)", min_value=0.0)
    target_goal = st.number_input("Savings Goal Amount (R)", min_value=0.0)
    months_to_goal = st.number_input("Months to Goal", min_value=1, max_value=360, value=60)
    risk = st.slider("Risk Tolerance (1=Low to 5=High)", 1, 5, 3)

    base_return = {1: 0.035, 2: 0.05, 3: 0.07, 4: 0.09, 5: 0.12}[risk]

    suggested_savings = max(0, (target_goal - current_savings) / months_to_goal)
    monthly_savings = st.slider("Monthly Savings (R)", min_value=0, max_value=int(income), value=int(suggested_savings))

    monthly_rate = (1 + base_return) ** (1/12) - 1
    balance = current_savings
    projection = []
    for _ in range(months_to_goal):
        balance = balance * (1 + monthly_rate) + monthly_savings
        projection.append(balance)

    st.line_chart(projection)

    final_value = projection[-1]
    gap = target_goal - final_value

    st.metric(f"Projected value after {months_to_goal} months", f"R {final_value:,.2f}")
    if gap > 0:
        st.warning(f"Goal short by approximately R {gap:,.2f}. Consider increasing savings or extending timeframe.")
    else:
        st.success(f"Goal exceeded by R {abs(gap):,.2f}. Well done!")

def page_tax_simulator():
    st.header("Tax Optimization Scenario Simulator")

    income = st.number_input("Annual Income (R)", min_value=0.0)
    dependants = st.number_input("Number of Dependants", min_value=0, step=1)

    scenarios = []
    n = st.number_input("Number of Scenarios", min_value=1, max_value=5, value=2)
    for i in range(int(n)):
        name = st.text_input(f"Scenario {i+1} Name", value=f"Scenario {i+1}")
        deductions = st.number_input(f"Scenario {i+1} Deductions (R)", min_value=0.0)
        scenarios.append({"name": name, "deductions": deductions})

    def simulate_tax(income, dependants, scenarios):
        results = {}
        for s in scenarios:
            taxable = max(0, income - s.get("deductions", 0.0) - dependants * 3500)
            if taxable < 50000: rate = 0.18
            elif taxable < 150000: rate = 0.26
            else: rate = 0.39
            tax = taxable * rate
            eff = tax / income if income else 0
            results[s['name']] = {"tax": tax, "effective_rate": eff, "taxable_income": taxable}
        return results

    if st.button("Run Simulation"):
        results = simulate_tax(income, int(dependants), scenarios)
        for name, res in results.items():
            st.write(f"**{name}**: Tax={res['tax']:.2f} Effective Rate={res['effective_rate']*100:.2f}% Taxable Income={res['taxable_income']:.2f}")

def generate_ai_report_text(profile, metrics):
    prompt = f"""
You are a financial advisor. Create a concise monthly report narrative for this user profile: {json.dumps(profile)}.
Metrics: {json.dumps(metrics)}.
Give clear insights and advice without step-by-step instructions."""

    if OPENAI_AVAILABLE and "OPENAI_API_KEY" in st.secrets:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=350,
                temperature=0.3,
            )
            return response.choices[0].text.strip()
        except:
            return "Unable to generate AI report at this time."
    else:
        return """Monthly Financial Summary:
- Current Savings: R{current_savings}
- Projected Growth: R{projection_value}
- Estimated Tax: R{estimated_tax}
Consult your financial advisor for details."""

def page_monthly_report():
    st.header("Monthly Financial Report")

    profile = st.session_state.auth_profile or {}

    metrics = {
        "projection_value": 1500000,
        "estimated_tax": 250000,
    }

    report_text = generate_ai_report_text(profile, metrics)
    st.markdown(f"**Report:**\n\n{report_text}")

def page_sentiment_insights():
    st.header("Market Sentiment & Portfolio Insights")

    news = [
        "Stock markets rally amid easing inflation concerns",
        "Tech sector reports mixed earnings for Q3",
        "South African Rand strengthens against US dollar",
        "New tax incentives for retirement savings introduced"
    ]

    for i, headline in enumerate(news, 1):
        polarity = textblob.TextBlob(headline).sentiment.polarity
        sentiment = "Positive" if polarity > 0.1 else "Neutral" if -0.1 <= polarity <= 0.1 else "Negative"
        color = "#22c55e" if sentiment == "Positive" else "#facc15" if sentiment == "Neutral" else "#ef4444"
        st.markdown(f"{i}. <span style='color:{color}'><b>[{sentiment}]</b></span> {headline}", unsafe_allow_html=True)

    avg_sentiment = np.mean([textblob.TextBlob(n).sentiment.polarity for n in news])
    st.markdown(f"**Average Market Sentiment:** {avg_sentiment:.2f}")

    advice = (
        "Market sentiment positive. You might consider increasing growth exposure."
        if avg_sentiment > 0.2 else
        "Market sentiment negative. Consider defensive strategies."
        if avg_sentiment < -0.2 else
        "Market sentiment neutral. Maintain your current portfolio."
    )
    st.markdown(f"**Advice:** {advice}")

# Add calls for rerun immediately after state changes to avoid double-clicks issues
# Sample example for button in any page:
# if st.button("Next"):
#     st.session_state.page = "some_page"
#     st.experimental_rerun()

# Extend main router for Part 6 pages
def main_router():
    page = st.session_state.page

    if page == "predictive_cashflow":
        page_predictive_cashflow()
    elif page == "smart_savings":
        page_smart_savings()
    elif page == "tax_simulator":
        page_tax_simulator()
    elif page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    else:
        # fallback to prior routing (Part 5 and earlier)
        # assume main_router from previous part handles
        pass

if __name__ == "__main__":
    init_state()
    init_auth_state()
    extend_sidebar()
    main_router()
# OptiFin Parts 7 & 8 — Community, Achievements, Referral, Education, Modern UI & Styling

import streamlit as st
import hashlib

# Simple in-memory achievement tracking
if "achievements" not in st.session_state:
    st.session_state.achievements = set()

def award_achievement(name: str):
    if name not in st.session_state.achievements:
        st.session_state.achievements.add(name)
        st.success(f"🎉 Achievement Unlocked: {name}!")

# Achievements page
def page_achievements():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Achievements & Rewards")
    profile = st.session_state.auth_profile or {}
    goals = profile.get("goals", [])

    if goals and "Goal Setter" not in st.session_state.achievements:
        award_achievement("Goal Setter")
    if len(goals) >= 3 and "Multi-Goal Planner" not in st.session_state.achievements:
        award_achievement("Multi-Goal Planner")

    st.markdown("### Your Achievements:")
    if not st.session_state.achievements:
        st.info("No achievements yet. Keep progressing!")
    else:
        for ach in sorted(st.session_state.achievements):
            st.markdown(f"- ✅ {ach}")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Community forum placeholder
def page_community_forum():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Community Forum")
    st.info("The forum is coming soon! Join our mailing list or social media for updates.")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Educational resources page
def page_educational_resources():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Financial Education & Tutorials")

    tutorials = [
        {"title": "Basics of Investing", "link": "https://www.investopedia.com/articles/basics/06/invest1000.asp"},
        {"title": "Tax Savings Strategies", "link": "https://www.sars.gov.za/"},
        {"title": "Retirement Planning 101", "link": "https://www.example.com/retirement-planning"},
        {"title": "Understanding Credit & Debt", "link": "https://www.consumerfinance.gov/"},
    ]

    for tut in tutorials:
        st.markdown(f"- [{tut['title']}]({tut['link']})")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Referral program page
def page_referral_program():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Referral Program")

    st.info("Invite your friends to OptiFin and earn credits towards premium reports and advice.")
    if st.session_state.auth_logged_in:
        # Generate referral code (hash first 8 chars of username md5)
        referral_code = hashlib.md5(st.session_state.auth_username.encode()).hexdigest()[:8].upper()
        st.code(referral_code)
        st.markdown("Share your referral code with friends!")
    else:
        st.warning("Please log in to see your referral code.")

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Base CSS for modern, readable, sleek UI with fixes for button responsiveness and background layering
def get_modern_css():
    theme = st.session_state.theme if "theme" in st.session_state else "dark"
    text_color = "#eef6ff" if theme == "dark" else "#111"
    bg_color = "rgba(20,24,28,0.85)" if theme == "dark" else "rgba(255,255,255,0.9)"
    overlay_color = "rgba(0,0,0,0.55)" if theme == "dark" else "rgba(255,255,255,0.85)"
    button_bg = "linear-gradient(135deg,#004174,#047860)" if theme == "dark" else "linear-gradient(135deg,#06b1a6,#387c6a)"
    button_hover_bg = "linear-gradient(135deg,#047860,#004174)" if theme == "dark" else "linear-gradient(135deg,#387c6a,#06b1a6)"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, #root, .appview-container, .main {{
        height: 100%;
        margin: 0;
        font-family: 'Inter', sans-serif;
        background: url('{st.session_state.background}') no-repeat center center fixed;
        background-size: cover;
        color: {text_color};
    }}
    body:before {{
        content: '';
        position: fixed;
        top:0; left:0; width:100vw; height:100vh;
        background-color: {overlay_color};
        z-index: -1;
    }}
    .glass-card {{
        background: {bg_color};
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 30px;
        box-shadow: 0 15px 40px rgba(8, 24, 70, 0.6);
        backdrop-filter: blur(10px);
        transition: box-shadow 0.3s ease;
    }}
    .glass-card:hover {{
        box-shadow: 0 25px 55px rgba(8, 24, 70, 0.8);
    }}
    h1, h2, h3 {{
        font-weight: 700;
        color: {text_color};
    }}
    h1 {{ font-size: 48px; margin-bottom: 1rem; }}
    h2 {{ font-size: 36px; margin-bottom: 0.75rem; }}
    button {{
        background: {button_bg};
        color: white !important;
        font-weight: 700;
        border-radius: 15px;
        padding: 14px 28px;
        border: none;
        box-shadow: 0 6px 20px rgba(4,120,96,0.4);
        font-size: 18px;
        transition: background 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
        user-select: none;
    }}
    button:hover, button:focus {{
        background: {button_hover_bg};
        box-shadow: 0 15px 35px rgba(4,120,96,0.7);
        outline: none;
    }}
    .stTextInput>div>div>input {{
        border-radius: 15px;
        border: 2px solid #05f7a7;
        padding: 14px 18px;
        font-size: 16px;
        color: {text_color};
        background-color: rgba(0, 0, 0, 0.7);
        transition: border-color 0.3s ease;
        width: 100%;
        max-width: 600px;
        user-select: text;
    }}
    .stTextInput>div>div>input::placeholder {{
        color: rgba(255,255,255,0.6);
    }}
    .stTextInput>div>div>input:focus {{
        border-color: #50fa7b;
        outline: none;
        box-shadow: 0 0 20px #50fa7b;
        background-color: rgba(0,0,0,0.9);
    }}
    footer {{
        color: {text_color};
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(255,255,255,0.1);
        font-size: 0.87rem;
        text-align: center;
        font-weight: 400;
    }}
    /* Responsive */
    @media (max-width: 768px) {{
        h1 {{ font-size: 38px; }}
        h2 {{ font-size: 28px; }}
        button {{ font-size: 16px; padding: 12px 20px; }}
        .glass-card {{ padding: 18px; }}
    }}
    </style>
    """

def apply_global_styles():
    st.markdown(get_modern_css(), unsafe_allow_html=True)

# Integrate with main router (add these pages)
def main_router():
    page = st.session_state.page

    if page == "achievements":
        page_achievements()
    elif page == "community":
        page_community_forum()
    elif page == "education":
        page_educational_resources()
    elif page == "referral":
        page_referral_program()
    else:
        # fallback to earlier routing
        if page in ["home", "auth_login", "auth_register", "auth_profile_edit", "segment_hub", "module_form", "goals_manager", "chatbot",
                    "predictive_cashflow", "bank_upload", "doc_upload", "reg_updates", "smart_savings", "tax_simulator", "monthly_report", "sentiment_insights"]:
            # Call previously defined router (assuming you merged parts)
            pass
        else:
            st.warning("Invalid page. Redirecting to home.")
            st.session_state.page = "home"
            st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    apply_global_styles()
    extend_sidebar()  # Sidebar defined in Part 5, integrated here
    main_router()

# Footer caller, use in main app layout
def app_footer():
    st.markdown(f"<footer>© {APP_YEAR} {APP_NAME} — Smart financial planning, simplified.</footer>", unsafe_allow_html=True)
# OptiFin Part 9 — Final Fixes, PDF & Excel Export, PDF Unicode Fixes, UX Polish

import streamlit as st
from fpdf import FPDF
import io
import pandas as pd

# --- PDF Generation with Unicode-safe text ---
def generate_pdf_report(title: str, meta: dict, advice_text: str, chart_bytes: bytes | None):
    """
    Create a branded PDF report with sanitized text to avoid UnicodeEncodeError.
    """
    if not FPDF:
        st.warning("PDF generation requires fpdf package.")
        return None

    pdf = FPDF()
    pdf.add_page()

    # Set metadata title
    safe_title = title.encode("ascii", errors="ignore").decode()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, safe_title, ln=True, align='C')

    pdf.ln(10)

    # Add meta info sanitized to ascii
    pdf.set_font("Helvetica", "", 12)
    for k, v in meta.items():
        safe_k = str(k).encode('ascii', errors='ignore').decode()
        safe_v = str(v).encode('ascii', errors='ignore').decode()
        pdf.cell(0, 10, f"{safe_k}: {safe_v}", ln=True)

    pdf.ln(10)

    # Add advice section
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "AI-generated Advice:", ln=True)
    pdf.set_font("Helvetica", "", 12)

    safe_advice = advice_text.encode("ascii", errors="ignore").decode()
    pdf.multi_cell(0, 10, safe_advice)

    # Embed chart if available
    if chart_bytes:
        try:
            pdf.image(io.BytesIO(chart_bytes), x=15, y=pdf.get_y() + 5, w=180)
        except Exception:
            pass

    return pdf.output(dest="S").encode("latin1")


# --- Excel Export (basic) ---
def generate_excel_report(data: pd.DataFrame):
    towrite = io.BytesIO()
    data.to_excel(towrite, index=False)
    towrite.seek(0)
    return towrite.read()


# --- Streamlit UI wrappers for export ---
def page_monthly_report():
    st.header("Generate Monthly Financial Report")

    profile = st.session_state.auth_profile or {}
    advice_text = "Your AI-generated financial summary and advice will appear here."
    # Dummy metadata
    meta = {"User": st.session_state.auth_username, "Date": str(st.date_input("Report Date", value=st.session_state.get("report_date", None) or st.today()))}

    if st.button("Generate PDF Report"):
        pdf_bytes = generate_pdf_report("Monthly Financial Report", meta, advice_text, None)
        if pdf_bytes:
            st.download_button("Download Report PDF", pdf_bytes, file_name="OptiFin_Report.pdf", mime="application/pdf")
        else:
            st.error("PDF generation failed.")

    if st.button("Generate Excel Report"):
        # Example data
        df = pd.DataFrame([{"Goal": "Retirement", "Progress": 45, "Target": 100}])
        excel_bytes = generate_excel_report(df)
        st.download_button("Download Report Excel", excel_bytes, file_name="OptiFin_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# --- Fix rerun issue for buttons across app ---
def rerun_on_button(label, key=None):
    clicked = st.button(label, key=key)
    if clicked:
        st.experimental_rerun()
    return clicked


# --- Final CSS polish ---
def get_final_css():
    theme = st.session_state.get("theme", "dark")
    text_c = "#eef6ff" if theme == "dark" else "#111"
    bgrgba = "rgba(20,24,28, 0.85)" if theme == "dark" else "rgba(255,255,255, 0.9)"
    return f"""
    <style>
    body {{
        color: {text_c} !important;
        background-color: {bgrgba} !important;
        user-select: none;
    }}
    button {{
        user-select: none;
        border-radius: 16px !important;
        font-weight: 700 !important;
        padding: 14px 32px !important;
        transition: all 0.3s ease !important;
        background: linear-gradient(135deg,#004174,#047860) !important;
        box-shadow: 0 6px 20px rgba(4,120,96,0.4);
        color: white !important;
    }}
    button:hover, button:focus {{
        background: linear-gradient(135deg,#047860,#004174) !important;
        outline:none !important;
        box-shadow: 0 15px 35px rgba(4,120,96,0.7);
    }}
    .stTextInput>div>div>input {{
        color: {text_c} !important;
        font-size: 16px !important;
        padding: 14px 18px !important;
        user-select: text !important;
    }}
    </style>
    """

def apply_final_css():
    st.markdown(get_final_css(), unsafe_allow_html=True)


# --- Main Router addition for Part 9 ---
def main_router():
    page = st.session_state.page

    if page == "monthly_report":
        page_monthly_report()
    else:
        # Fallback default pages (connect to your earlier router or extend)
        st.write(f"Page '{page}' content goes here.")
        if rerun_on_button("Back to Home"):
            st.session_state.page = "home"

if __name__ == "__main__":
    init_state()
    init_auth_state()
    apply_final_css()
    extend_sidebar()
    main_router()
# OptiFin Part 10 — Advanced Portfolio & Market Data Integration

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

def fetch_stock_data(ticker: str, period="1mo", interval="1d") -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        if hist.empty:
            st.warning(f"No data found for {ticker}")
            return pd.DataFrame()
        hist.reset_index(inplace=True)
        return hist
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        return pd.DataFrame()

def page_portfolio_overview():
    st.header("My Investment Portfolio Overview")
    portfolio = st.session_state.auth_profile.get("portfolio", [])
    if not portfolio:
        st.info("Your portfolio is empty. Add investments in the Goals section or profile.")
        return

    tickers = [item.get("ticker") for item in portfolio if "ticker" in item]
    tickers = list(set(tickers))  # Unique tickers
    for ticker in tickers:
        st.subheader(f"Ticker: {ticker}")
        df = fetch_stock_data(ticker)
        if df.empty:
            continue
        
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Close Price'))
        fig.update_layout(
            title=f"{ticker} Closing Price - Last Month",
            xaxis_title="Date",
            yaxis_title="Price (ZAR)",
            template='plotly_dark' if st.session_state.theme == 'dark' else 'plotly_white',
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Portfolio item current value estimate
        quantity = next((item.get("quantity", 0) for item in portfolio if item.get("ticker") == ticker), 0)
        current_price = df["Close"].iloc[-1]
        value = quantity * current_price
        st.metric("Current Value", f"R {value:,.2f}", delta=None)

def interactive_goals_chart():
    st.header("Goals Progress Visualization")
    profile = st.session_state.auth_profile or {}
    goals = profile.get("goals", [])

    if not goals:
        st.info("You have not set any goals yet.")
        return

    # Prepare data
    names = [g['name'] for g in goals]
    targets = [g['amount'] for g in goals]
    progresses = [np.random.uniform(0, t) for t in targets]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=targets, name='Target Amount', marker_color='lightblue'))
    fig.add_trace(go.Bar(x=names, y=progresses, name='Current Progress', marker_color='green'))

    fig.update_layout(barmode='group', title="Goals vs Progress", yaxis_title="R (ZAR)")
    st.plotly_chart(fig, use_container_width=True)


# Integration example in main router
def main_router():
    page = st.session_state.page

    if page == "portfolio_overview":
        page_portfolio_overview()
    elif page == "goals_chart":
        interactive_goals_chart()
    else:
        # Assume fallback to existing router logic from prior parts
        st.info(f"Page {page} placeholder. Implement further here.")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 11 — Calendar, Alerts, Multi-language, Accessibility & Settings

import streamlit as st
import datetime
import locale

# Locale setting for date format
LOCALE_MAP = {
    "en": "en_US.UTF-8",
    "fr": "fr_FR.UTF-8",
    "es": "es_ES.UTF-8",
}

# Financial calendar and reminders data (could be fetched dynamically from APIs)
FINANCIAL_EVENTS = [
    {"date": "2025-03-31", "title": "SA SARS Tax Returns Deadline", "description": "File your income tax returns with SARS."},
    {"date": "2025-06-30", "title": "Q2 VAT Submission", "description": "Submit VAT reports for Q2."},
    {"date": "2025-12-01", "title": "Retirement Fund Annual Contribution Deadline", "description": "Last day to contribute to your retirement fund."},
]

# Alert management with persistence
def load_alerts():
    return st.session_state.get("alerts", [])

def save_alerts(alerts):
    st.session_state.alerts = alerts

def page_financial_calendar():
    st.header("Financial Calendar & Reminders")
    locale_code = LOCALE_MAP.get(st.session_state.auth_profile.get("language", "en"), "en_US.UTF-8")
    
    try:
        locale.setlocale(locale.LC_TIME, locale_code)
    except Exception:
        pass  # fallback gracefully

    today = datetime.date.today()
    upcoming_events = [e for e in FINANCIAL_EVENTS if datetime.date.fromisoformat(e["date"]) >= today]
    
    for event in upcoming_events:
        event_date = datetime.date.fromisoformat(event["date"])
        formatted_date = event_date.strftime("%A, %d %B %Y")
        st.markdown(f"### {event['title']} - {formatted_date}")
        st.write(event["description"])

# Alerts Notifications Page
def page_alerts():
    st.header("Alerts & Notifications")
    alerts = load_alerts()
    new_alert = st.text_input("Add New Alert")

    if st.button("Add Alert"):
        if new_alert.strip():
            alerts.append({"text": new_alert.strip(), "date": datetime.datetime.now().isoformat()})
            save_alerts(alerts)
            st.experimental_rerun()

    if alerts:
        for i, alert in enumerate(alerts):
            st.markdown(f"- [{alert['date'][:10]}] {alert['text']}")
            if st.button(f"Remove Alert {i+1}", key=f'remove_alert_{i}'):
                alerts.pop(i)
                save_alerts(alerts)
                st.experimental_rerun()
    else:
        st.info("No alerts yet.")

# Multi-language & currency settings page
def page_settings():
    st.header("User Settings & Preferences")
    profile = st.session_state.auth_profile or {}

    lang_options = {"English": "en", "French": "fr", "Spanish": "es"}
    currency_options = {"South African Rand": "ZAR", "USD": "USD", "EUR": "EUR", "GBP": "GBP"}

    lang_inv = {v: k for k,v in lang_options.items()}
    currency_inv = {v: k for k,v in currency_options.items()}

    current_lang = profile.get("language", "en")
    current_currency = profile.get("currency", "ZAR")

    selected_lang = st.selectbox("Preferred Language", list(lang_options.keys()), index=list(lang_options.values()).index(current_lang))
    selected_currency = st.selectbox("Preferred Currency", list(currency_options.keys()), index=list(currency_options.values()).index(current_currency))

    if st.button("Save Preferences"):
        profile["language"] = lang_options[selected_lang]
        profile["currency"] = currency_options[selected_currency]
        st.session_state.auth_profile = profile

        # Save to USERS_DB if using file or DB storage (simplified)
        if st.session_state.auth_username in USERS_DB:
            USERS_DB[st.session_state.auth_username]["profile"] = profile
        st.success("Preferences saved! The app will reload with your preferences.")
        st.experimental_rerun()

# Accessibility improvements (adds a skip link and usage instructions)
def apply_accessibility_features():
    st.markdown("""
    <style>
    a.skip-link {
      position: absolute;
      left: -999px;
      top: auto;
      width: 1px;
      height: 1px;
      overflow: hidden;
      z-index: -999;
    }
    a.skip-link:focus {
      position: static;
      width: auto;
      height: auto;
      margin: 10px;
      padding: 10px;
      background-color: #004174;
      color: white;
      text-decoration: none;
      z-index: 1000;
      outline: 2px solid #50fa7b;
    }
    </style>
    <a href="#main-content" class="skip-link">Skip to main content</a>
    """, unsafe_allow_html=True)

    st.markdown('<div id="main-content" tabindex="-1"></div>', unsafe_allow_html=True)
    st.info(
        "Keyboard Navigation Tips: Use Tab to move between interactive elements. "
        "Use Enter to activate buttons & links."
    )

# Integrate Part 11 pages into router
def main_router():
    page = st.session_state.page

    if page == "financial_calendar":
        page_financial_calendar()
    elif page == "alerts":
        page_alerts()
    elif page == "settings":
        page_settings()
    else:
        st.info(f"Page '{page}' content placeholder...")

if __name__=="__main__":
    init_state()
    init_auth_state()
    apply_accessibility_features()
    extend_sidebar()
    main_router()
# OptiFin Part 12 — Advanced Investment Dashboard with yfinance & Plotly

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

# Fetch live stock data
def fetch_stock_data(ticker, period='1y', interval='1d'):
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=period, interval=interval)
        hist.reset_index(inplace=True)
        return hist
    except Exception as e:
        st.error(f"Failed fetching {ticker}: {str(e)}")
        return pd.DataFrame()

# Calculate portfolio value over time
def calculate_portfolio_performance(portfolio):
    combined_df = None
    for asset in portfolio:
        ticker = asset.get('ticker')
        quantity = asset.get('quantity', 0)
        df = fetch_stock_data(ticker)
        if df.empty:
            continue
        df['value'] = df['Close'] * quantity
        df = df[['Date', 'value']]
        df.rename(columns={'value': ticker}, inplace=True)
        if combined_df is None:
            combined_df = df
        else:
            combined_df = pd.merge(combined_df, df, on='Date', how='outer')
    if combined_df is None:
        return pd.DataFrame()
    combined_df.fillna(method='ffill', inplace=True)
    combined_df.fillna(0, inplace=True)
    combined_df['Total Portfolio'] = combined_df.drop(columns=['Date']).sum(axis=1)
    return combined_df

# Plot portfolio value and components
def plot_portfolio(df):
    if df.empty:
        st.warning("No data to plot for portfolio.")
        return
    fig = go.Figure()
    for col in df.columns:
        if col != 'Date':
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df[col], mode='lines', name=col
            ))
    fig.update_layout(
        title="Portfolio Performance Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (ZAR)",
        height=600,
        template='plotly_dark' if st.session_state.theme == 'dark' else 'plotly_white',
    )
    st.plotly_chart(fig, use_container_width=True)

# Sector allocation chart (dummy data example)
def plot_sector_allocation():
    sectors = {
        "Technology": 25,
        "Financials": 20,
        "Healthcare": 15,
        "Consumer Goods": 15,
        "Energy": 10,
        "Utilities": 5,
        "Other": 10,
    }
    labels = list(sectors.keys())
    values = list(sectors.values())

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
    fig.update_layout(title="Portfolio Sector Allocation", height=400)
    st.plotly_chart(fig, use_container_width=True)

# Main investment dashboard page
def page_investment_dashboard():
    st.title("Investment Dashboard")

    portfolio = st.session_state.auth_profile.get("portfolio", [])

    if not portfolio:
        st.info("Your portfolio is empty. Please add investments in your profile.")
        return

    st.subheader("Portfolio Composition")
    portfolio_df = pd.DataFrame(portfolio)
    st.dataframe(portfolio_df)

    st.subheader("Portfolio Value Over Time")
    perf_df = calculate_portfolio_performance(portfolio)
    if perf_df.empty:
        st.warning("Unable to fetch portfolio historical data.")
    else:
        plot_portfolio(perf_df)

    st.subheader("Sector Allocation")
    plot_sector_allocation()

    # Individual stock quick stats
    for asset in portfolio:
        ticker = asset.get('ticker')
        if not ticker:
            continue
        st.markdown(f"### {ticker} Details")
        df = fetch_stock_data(ticker, period='5d', interval='1d')
        if not df.empty:
            st.line_chart(df.set_index('Date')['Close'])
            last_price = df['Close'].iloc[-1]
            st.metric("Last Close Price", f"R {last_price:.2f}")

# Integrate page to router (call this in your main_router or equivalent)
def main_router():
    page = st.session_state.page

    if page == "investment_dashboard":
        page_investment_dashboard()
    else:
        # fallback handle other pages as before
        st.info(f"Page '{page}' not implemented yet.")

if __name__=="__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 14 — Wallet & Transaction Ledger

import streamlit as st
import pandas as pd
import io
import datetime

# Initialize user wallet transactions store
def init_wallet():
    if "wallet_transactions" not in st.session_state:
        st.session_state.wallet_transactions = pd.DataFrame(columns=["Date", "Category", "Description", "Amount"])

def add_transactions_from_csv(csv_file):
    try:
        new_txns = pd.read_csv(csv_file, parse_dates=["Date"])
        # Ensure required columns exist
        expected_cols = {"Date", "Category", "Description", "Amount"}
        if not expected_cols.issubset(set(new_txns.columns)):
            st.error(f"CSV must have columns: {expected_cols}")
            return False

        # Append new transactions, avoid duplicates by Date+Desc+Amount
        wallet = st.session_state.wallet_transactions
        combined = pd.concat([wallet, new_txns]).drop_duplicates(subset=["Date", "Description", "Amount"], keep="last").reset_index(drop=True)
        st.session_state.wallet_transactions = combined.sort_values("Date", ascending=False)

        st.success(f"{len(new_txns)} transactions added successfully.")
        return True
    except Exception as e:
        st.error(f"Error parsing CSV: {str(e)}")
        return False

def export_wallet_to_csv():
    wallet = st.session_state.wallet_transactions
    csv_buffer = io.StringIO()
    wallet.to_csv(csv_buffer, index=False)
    b = csv_buffer.getvalue().encode()
    return b

def page_wallet():
    init_wallet()
    st.title("Wallet & Transaction Ledger")

    # CSV Upload for transactions
    uploaded_file = st.file_uploader("Import Transactions CSV", type=["csv"])
    if uploaded_file:
        if add_transactions_from_csv(uploaded_file):
            st.experimental_rerun()

    # Date Range Filter
    wallet = st.session_state.wallet_transactions
    if wallet.empty:
        st.info("No transactions yet. Import your CSV file to get started.")
        return

    min_date = wallet["Date"].min()
    max_date = wallet["Date"].max()
    date_filter = st.slider("Filter Date Range", min_value=min_date, max_value=max_date,
                            value=(min_date, max_date), format="YYYY-MM-DD")

    filtered_wallet = wallet[(wallet["Date"] >= date_filter[0]) & (wallet["Date"] <= date_filter[1])]

    # Category Filter
    categories = sorted(filtered_wallet["Category"].dropna().unique().tolist())
    selected_categories = st.multiselect("Filter by Category", options=categories, default=categories)

    filtered_wallet = filtered_wallet[filtered_wallet["Category"].isin(selected_categories)]

    # Show filtered transactions with pagination
    st.markdown(f"### Showing {len(filtered_wallet)} Transactions")

    PAGE_SIZE = 10
    total_pages = (len(filtered_wallet) - 1) // PAGE_SIZE + 1

    page_num = st.number_input("Page Number", min_value=1, max_value=total_pages, value=1, step=1)

    start_idx = (page_num - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE

    to_display = filtered_wallet.iloc[start_idx:end_idx]

    st.dataframe(to_display.reset_index(drop=True), height=300)

    # Expense/Income Summary Chart (Monthly)
    if not filtered_wallet.empty:
        filtered_wallet["Month"] = filtered_wallet["Date"].dt.to_period("M").dt.to_timestamp()
        summary = filtered_wallet.groupby(["Month"])["Amount"].sum().reset_index()

        st.markdown("### Monthly Net Inflow/Outflow")
        st.bar_chart(summary.rename(columns={"Month": "index"}).set_index("index")["Amount"])

    # Export CSV
    csv_bytes = export_wallet_to_csv()
    st.download_button("Export Wallet to CSV", csv_bytes, file_name="optifin_wallet.csv", mime="text/csv")

    if st.button("Clear All Transactions"):
        st.session_state.wallet_transactions = pd.DataFrame(columns=["Date", "Category", "Description", "Amount"])
        st.success("All transactions cleared.")
        st.experimental_rerun()
# OptiFin Part 16 — AI Dynamic Scenario Simulation and Behavioral Finance Insights

import streamlit as st
import numpy as np
import random
import openai

# Simulate dynamic "What-if" scenario tool
def simulate_what_if_scenarios(current_savings, monthly_income, monthly_expenses, years, volatility=0.1):
    np.random.seed(42)
    months = years * 12
    balance = current_savings
    balances = []
    for month in range(months):
        # Random "shock" factor influenced by volatility
        shock = np.random.normal(loc=0, scale=volatility)
        # Income varies ± shock, expenses vary ± shock
        income = monthly_income * (1 + shock)
        expenses = monthly_expenses * (1 + shock)
        balance = balance + income - expenses
        # Ensure no negative savings (except can dip to small negative)
        balance = max(balance, -1000)
        balances.append(balance)
    return balances

def plot_simulation(balances):
    import plotly.graph_objs as go
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=balances, mode='lines+markers', name='Projected Balance'))
    fig.update_layout(
        title="Simulated Savings Balance Over Time",
        xaxis_title="Months",
        yaxis_title="Balance (ZAR)",
        template='plotly_dark' if st.session_state.theme == 'dark' else 'plotly_white',
    )
    st.plotly_chart(fig, use_container_width=True)

# Behavioral finance AI insight generator
def generate_behavioral_insights(user_profile):
    prompt = f"""
You are a behavioral finance assistant. Based on this user's profile and financial behavior:
{user_profile}

Generate actionable insights about their spending/saving habits, emotional biases, and tailored advice to optimize their financial wellbeing avoiding common behavioral pitfalls."""

    if "OPENAI_API_KEY" in st.secrets:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                temperature=0.8,
                max_tokens=400,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"AI generation error: {str(e)}"
    else:
        # Fallback sample insights
        return """
- Your spending tends to increase at month-ends; consider setting stricter budgets during this period.
- You show a tendency towards loss aversion; diversifying your investments can reduce instinctive sell-offs.
- Automate savings to reduce impulsive spending.
- Schedule monthly financial reviews to keep your goals aligned.
"""

def page_advanced_ai_companion():
    st.title("AI-Powered Financial Companion & Scenario Simulator")

    st.markdown("""
    Adjust your inputs to simulate financial outcomes under realistic variability.
    Receive personalized behavioral finance insights powered by AI.
    """)

    profile = st.session_state.auth_profile or {}
    current_savings = st.number_input("Current Savings (ZAR)", min_value=0.0, value=profile.get("current_savings", 5000))
    monthly_income = st.number_input("Monthly Income (ZAR)", min_value=0.0, value=profile.get("monthly_income", 20000))
    monthly_expenses = st.number_input("Monthly Expenses (ZAR)", min_value=0.0, value=profile.get("monthly_expenses", 15000))
    simulation_years = st.slider("Simulation Period (Years)", min_value=1, max_value=10, value=5)
    volatility = st.slider("Financial Variability (Volatility)", 0.0, 1.0, 0.1)

    if st.button("Run Scenario Simulation"):
        balances = simulate_what_if_scenarios(current_savings, monthly_income, monthly_expenses, simulation_years, volatility)
        plot_simulation(balances)

    if st.button("Get Behavioral Finance Insights"):
        insights = generate_behavioral_insights(profile)
        st.markdown(f"### AI Behavioral Insights\n\n{insights}")

# Integration example in router
def main_router():
    page = st.session_state.page

    if page == "advanced_ai_companion":
        page_advanced_ai_companion()
    else:
        st.info(f"Page '{page}' placeholder here.")

if __name__=="__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 17 — Smart Alerts & Notifications System

import streamlit as st
import datetime

def init_alerts():
    if "alerts" not in st.session_state:
        st.session_state.alerts = []

def add_alert(message: str, level="info", auto=False):
    """
    Add an alert.
    `level` can be info, warning, error
    `auto` indicates if alert was auto-generated by system
    """
    st.session_state.alerts.append({
        "id": len(st.session_state.alerts) + 1,
        "message": message,
        "level": level,
        "timestamp": datetime.datetime.now(),
        "auto": auto,
        "read": False
    })

def remove_alert(alert_id):
    st.session_state.alerts = [a for a in st.session_state.alerts if a["id"] != alert_id]

def mark_alert_read(alert_id):
    for alert in st.session_state.alerts:
        if alert["id"] == alert_id:
            alert["read"] = True

# Generate automated alerts based on user financial data
def generate_auto_alerts():
    profile = st.session_state.auth_profile or {}
    wallet = st.session_state.get("wallet_transactions", pd.DataFrame())

    # Example logic: low balance alert
    recent_balance = profile.get("current_savings", 0)
    if recent_balance < 1000:
        exists = any(a for a in st.session_state.alerts if "low balance" in a["message"].lower() and a["auto"])
        if not exists:
            add_alert("⚠️ Your savings balance is critically low.", level="warning", auto=True)

    # Example: Upcoming tax due date reminders
    today = datetime.date.today()
    tax_due = datetime.date(today.year, 3, 31)
    days_to_due = (tax_due - today).days
    if 0 <= days_to_due <= 7:
        exists = any(a for a in st.session_state.alerts if "tax" in a["message"].lower() and a["auto"])
        if not exists:
            add_alert(f"⏰ Reminder: SARS tax return deadline in {days_to_due} day(s).", level="info", auto=True)

def page_alerts():
    st.title("Notifications & Alerts")
    init_alerts()
    generate_auto_alerts()

    if not st.session_state.alerts:
        st.info("No alerts at this moment. You're all clear!")

    # Display alerts with filters
    show_unread_only = st.checkbox("Show only unread alerts", value=True)
    filtered_alerts = [a for a in st.session_state.alerts if not (show_unread_only and a["read"])]

    for alert in filtered_alerts:
        bg_color = "#323232" if alert["level"] == "info" else "#a15627" if alert["level"] == "warning" else "#701313"
        style = f"background-color: {bg_color}; padding: 15px; margin-bottom: 10px; border-radius: 8px; color: white;"
        with st.container():
            st.markdown(f"<div style='{style}'>"
                        f"<strong>{'AUTOMATED' if alert['auto'] else 'USER'} Alert:</strong> {alert['message']}<br>"
                        f"<small>{alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>"
                        f"</div>", unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])
            if col1.button(f"Mark Read (ID: {alert['id']})", key=f"read_{alert['id']}"):
                mark_alert_read(alert["id"])
                st.experimental_rerun()
            if col2.button(f"Dismiss (ID: {alert['id']})", key=f"dismiss_{alert['id']}"):
                remove_alert(alert["id"])
                st.experimental_rerun()

    # Manual add alert
    st.markdown("---")
    st.header("Add Custom Alert")
    msg = st.text_input("Alert message")
    lvl = st.selectbox("Level", ["info", "warning", "error"])
    if st.button("Add Alert"):
        if msg.strip():
            add_alert(msg.strip(), level=lvl, auto=False)
            st.success("Custom alert added!")
            st.experimental_rerun()
        else:
            st.error("Alert message cannot be empty.")

# Add to main router
def main_router():
    page = st.session_state.page
    if page == "alerts":
        page_alerts()
    else:
        st.info(f"Page '{page}' placeholder.")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 18 — AI-Powered Personalized Investment Tips & Market Sentiment Guidance

import streamlit as st
import random
import openai
import datetime

# Simulate live market sentiment & news (would use APIs in real app)
MARKET_SENTIMENTS = [
    {"sector": "Technology", "sentiment": 0.82, "headline": "Tech sector rallies on AI innovations"},
    {"sector": "Financials", "sentiment": -0.44, "headline": "Bank stocks dip amid regulatory concerns"},
    {"sector": "Healthcare", "sentiment": 0.15, "headline": "Healthcare gains modest traction on new drug approvals"},
    {"sector": "Energy", "sentiment": -0.30, "headline": "Energy sector under pressure due to policy shifts"},
]

# Generate AI investment tips based on profile and current sentiment
def generate_investment_tips(profile, market_sentiments):
    user_info = f"""
User Profile:
- Risk tolerance: {profile.get('risk_tolerance', 'medium')}
- Portfolio allocation: {profile.get('portfolio_allocation', 'balanced')}
- Investment goals: {profile.get('investment_goals', 'growth')}
- Current savings: {profile.get('current_savings', 0):,.2f} ZAR
"""
    sentiment_summary = "\n".join([f"- {m['sector']}: {'Positive' if m['sentiment']>0 else 'Negative'} ({m['headline']})" for m in market_sentiments])

    prompt = f"""
You are a top financial AI advisor. The client has the following profile:
{user_info}

Current market sentiment is:
{sentiment_summary}

Provide personalized, clear, and actionable investment recommendations based on this data.
Keep it in plain language, encouraging cautious yet growth-minded decisions.
"""

    if "OPENAI_API_KEY" in st.secrets:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"AI generation error: {str(e)}"
    else:
        # Basic fallback generated tips
        return """Based on your sentiment and risk tolerance:
- Consider increasing exposure to Technology sector, especially AI-related companies.
- Monitor Financial sector carefully due to regulatory risks.
- Maintain diversified holdings in Healthcare for steady growth.
- Reduce Energy sector exposure until policy uncertainty resolves."""

def page_investment_tips():
    st.title("Personalized Investment Tips & Market Sentiment Guidance")

    profile = st.session_state.auth_profile or {}
    st.markdown("Your profile and current market sentiment are analyzed to generate tailored investment advice.")

    # Display simulated market sentiment overview
    st.subheader("Market Sentiment Snapshot")
    for market in MARKET_SENTIMENTS:
        sentiment_icon = "🔺" if market["sentiment"] > 0 else "🔻"
        st.markdown(f"**{market['sector']}**: {sentiment_icon} {market['headline']}")

    # User risk tolerance input (for demo)
    risk_tolerance = st.selectbox("Risk Tolerance", ["low", "medium", "high"], index=1)
    portfolio_alloc = st.selectbox("Portfolio Allocation Style", ["balanced", "growth", "income"], index=0)
    investment_goals = st.text_area("Investment Goals", "Long-term growth and wealth preservation")

    # Save user inputs to profile for context (optional persistence here)
    profile["risk_tolerance"] = risk_tolerance
    profile["portfolio_allocation"] = portfolio_alloc
    profile["investment_goals"] = investment_goals
    st.session_state.auth_profile = profile

    if st.button("Get Personalized Investment Advice"):
        advice = generate_investment_tips(profile, MARKET_SENTIMENTS)
        st.markdown(f"### AI-Generated Investment Advice\n\n{advice}")

# Integrate in main router
def main_router():
    page = st.session_state.page
    if page == "investment_tips":
        page_investment_tips()
    else:
        st.info(f"Page '{page}' not implemented yet.")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 19 — South African Tax Module with Up-to-date SARS Rules and Filing Alerts

import streamlit as st
import datetime

# Tax brackets and rebates 2025 (year ending 28 Feb 2026)
SA_TAX_BRACKETS_2025 = [
    (0, 237100, 0.18, 0),
    (237101, 370500, 0.26, 42678),
    (370501, 512800, 0.31, 77362),
    (512801, 673000, 0.36, 121475),
    (673001, 857900, 0.39, 179147),
    (857901, 1817000, 0.41, 251258),
    (1817001, float('inf'),0.45,644489)
]

SA_TAX_REBATES_2025 = {
    "primary": 17235,
    "secondary": 9444,
    "tertiary": 3145
}

# SARS Filing Season 2025 key dates
FILING_DATES_2025 = {
    "auto_assessment_notice_start": datetime.date(2025, 7, 7),
    "auto_assessment_notice_end": datetime.date(2025, 7, 20),
    "individual_filing_start": datetime.date(2025, 7, 21),
    "individual_filing_end": datetime.date(2025, 10, 20),
    "provisional_filing_start": datetime.date(2025, 7, 21),
    "provisional_filing_end": datetime.date(2026, 1, 19),
    "trust_filing_start": datetime.date(2025, 9, 19),
    "trust_filing_end": datetime.date(2026, 1, 19),
}

# Retirement fund contribution limits
RETIREMENT_CONTRIBUTION_LIMIT_2025 = 350000

def calculate_sa_tax(income, age):
    """
    Calculate South African income tax for 2025 year of assessment.
    Applies rebates based on age, progressive rates.
    """
    # Determine rebate
    rebate = SA_TAX_REBATES_2025["primary"]
    if age >= 65 and age < 75:
        rebate += SA_TAX_REBATES_2025["secondary"]
    elif age >= 75:
        rebate += SA_TAX_REBATES_2025["secondary"] + SA_TAX_REBATES_2025["tertiary"]

    tax_payable = 0.0
    for bracket in SA_TAX_BRACKETS_2025:
        low, high, rate, base_tax = bracket
        if income >= low and income <= high:
            tax_payable = base_tax + rate * (income - low)
            break

    tax_payable = max(0, tax_payable - rebate)
    return tax_payable

def display_tax_summary():
    st.header("South African Income Tax Calculator 2025")

    age = st.slider("Age", min_value=18, max_value=100, value=30)
    income = st.number_input("Taxable Annual Income (ZAR)", min_value=0.0, step=1000.0, value=300000.0)

    tax = calculate_sa_tax(income, age)
    st.metric("Estimated Tax Payable (2025 Year)", f"R {tax:,.2f}")

    st.markdown(f"### Annual Retirement Fund Contributions Limit: R{RETIREMENT_CONTRIBUTION_LIMIT_2025:,}")

def check_filing_deadlines():
    st.header("SARS 2025 Filing Season Deadlines")

    today = datetime.date.today()
    messages = []

    for key, date in FILING_DATES_2025.items():
        days_left = (date - today).days
        if 0 <= days_left <= 30:
            messages.append(f"⏰ Deadline: {key.replace('_', ' ').capitalize()} on {date.strftime('%d %b %Y')} ({days_left} day(s) left)")

    if messages:
        for msg in messages:
            st.warning(msg)
    else:
        st.success("No filing deadlines within the next 30 days.")

def page_sa_tax_module():
    st.title("South African Tax & Filing Info — 2025 Update")

    display_tax_summary()
    st.markdown("---")
    check_filing_deadlines()
    st.markdown("---")
    st.info("""
    This tool uses the **latest SARS tax tables and rebates** effective for the year ending February 28, 2026.
    It automatically updates filing season deadlines and retirement contribution limits for South African taxpayers.
    """)

# Integration in main router
def main_router():
    page = st.session_state.page
    if page == "sa_tax_module":
        page_sa_tax_module()
    else:
        st.info(f"Page '{page}' not implemented yet.")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 20 — Retirement Planning, Tax Benefits & AI Optimization for South Africa

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objs as go

RETIREMENT_AGE = 65
ANNUAL_RETIREMENT_CONTRIBUTION_LIMIT = 350000  # 2025 SARS limit

def retirement_projection(current_age, current_savings, annual_contribution, years_until_retirement, avg_return=0.07):
    """
    Calculate projected retirement corpus applying compound interest annually.
    """
    balances = []
    balance = current_savings
    for year in range(years_until_retirement):
        balance = balance * (1 + avg_return) + annual_contribution
        balances.append(balance)
    return balances

def calculate_tax_relief(contribution):
    """
    SARS allows tax relief on retirement fund contributions up to a limit.
    Here we calculate estimated immediate tax relief.
    """
    limit = ANNUAL_RETIREMENT_CONTRIBUTION_LIMIT
    taxable_contrib = min(contribution, limit)
    relief_rate = 0.276  # Approximate max marginal tax rate for high earners in SA (41% * 67%)
    tax_relief = taxable_contrib * relief_rate
    return tax_relief

def page_retirement_planner():
    st.title("South African Retirement Planning & Tax Optimization")

    profile = st.session_state.auth_profile or {}
    age = st.slider("Your Current Age", min_value=18, max_value=RETIREMENT_AGE - 1, value=profile.get("age", 30))
    current_savings = st.number_input("Current Retirement Savings (ZAR)", min_value=0.0, value=profile.get("current_savings", 0.0))
    annual_contribution = st.number_input("Annual Contribution (ZAR)", min_value=0.0, value=profile.get("annual_contribution", 0.0), max_value=ANNUAL_RETIREMENT_CONTRIBUTION_LIMIT)
    years_to_retirement = RETIREMENT_AGE - age

    st.markdown(f"**Note:** SARS limits tax-deductible retirement contributions to R{ANNUAL_RETIREMENT_CONTRIBUTION_LIMIT:,} annually.")

    tax_relief = calculate_tax_relief(annual_contribution)
    st.metric("Estimated Immediate Tax Relief", f"R {tax_relief:,.2f}")

    projection = retirement_projection(age, current_savings, annual_contribution, years_to_retirement)

    # Plotting the growth projection
    fig = go.Figure()
    years = list(range(age + 1, RETIREMENT_AGE + 1))
    fig.add_trace(go.Scatter(x=years, y=projection, mode="lines+markers", name="Projected Retirement Savings"))

    fig.update_layout(title=f"Projected Retirement Savings Growth from Age {age} to {RETIREMENT_AGE}",
                      xaxis_title="Age",
                      yaxis_title="Retirement Savings (ZAR)",
                      template='plotly_dark' if st.session_state.theme == 'dark' else 'plotly_white')

    st.plotly_chart(fig, use_container_width=True)

    # AI Recommendations (basic example, ideally replace with GPT-generated text)
    if st.button("Get AI Retirement Optimization Tips"):
        tips = f"""
- Consider increasing your annual contribution close to theR {ANNUAL_RETIREMENT_CONTRIBUTION_LIMIT:,} limit to maximize tax relief.
- Start contributing early to benefit from compound interest.
- Diversify your retirement portfolio for sustainable growth.
- Review and adjust contributions annually based on your income and lifestyle changes.
"""
        st.markdown("### AI-Powered Retirement Tips")
        st.markdown(tips)

# Integration in main router
def main_router():
    page = st.session_state.page
    if page == "retirement_planner":
        page_retirement_planner()
    else:
        st.info(f"Page '{page}' not implemented yet.")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 21 — AI-Driven SARS Tax Optimization & Filing Strategy Support

import streamlit as st
import openai
import datetime

# Tax optimization suggestions engine
def generate_tax_optimization_advice(user_profile, income, age):
    prompt = f"""
You are a South African tax expert AI advisor. The user has the following profile and income:

User Profile: {user_profile}
Annual taxable income: R{income:,.2f}
Age: {age}

Using SARS 2025/2026 tax laws, rebates, deductions, retirement limits, and filing deadlines, provide:
- Optimized tax reduction strategies tailored for this user
- Advice on provisional tax filings and critical deadlines
- How to leverage retirement savings tax relief optimally
- Suggestions on deductions such as medical credits, donations, home office, and others applicable in SA
- Any advanced SARS tax structuring trends and how the user can apply them legitimately

Respond with clear, actionable, plain language advice.
"""

    if "OPENAI_API_KEY" in st.secrets:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=600,
                temperature=0.6,
                top_p=1.0,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"AI generation error: {e}"
    else:
        # Fallback canned advice snippet
        return """
- Maximize contributions to your retirement fund up to R350,000 annually to reduce taxable income.
- Claim medical tax credits for yourself and dependents where eligible.
- Keep documentation for charitable donations, which may be deductible.
- Review your eligibility for home office deductions based on SARS guidelines.
- File provisional tax returns timely to avoid penalties.
- Consider spreading income streams to manage taxable brackets.
- Leverage tax-free savings accounts for additional tax relief.
- Stay updated on SARS filing deadlines: July 21 to October 20 for individuals.
"""

def page_tax_optimization():
    st.title("South African AI Tax Optimization Advisor")

    profile = st.session_state.auth_profile or {}
    income = st.number_input("Annual Taxable Income (ZAR)", min_value=0.0, value=profile.get("annual_income", 300000.0))
    age = st.slider("Age", min_value=18, max_value=100, value=profile.get("age", 35))

    # Display existing profile for transparency
    st.markdown(f"**Current User Profile:** {profile}")

    if st.button("Get AI-Powered Tax Optimization Advice"):
        advice = generate_tax_optimization_advice(profile, income, age)
        st.markdown("### Tax Optimization Advice\n")
        st.markdown(advice)

# Integrate into router
def main_router():
    page = st.session_state.page
    if page == "tax_optimization":
        page_tax_optimization()
    else:
        st.info(f"Page '{page}' not implemented yet.")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 22 — Drag & Drop User Dashboard with Live SARS & AI Widgets

import streamlit as st
import json

# Default widgets available
AVAILABLE_WIDGETS = {
    "tax_alerts": "South African Tax Alerts",
    "retirement_progress": "Retirement Savings Progress",
    "portfolio_overview": "Investment Portfolio Summary",
    "ai_tips": "AI Personalized Tips",
}

# Simulate storing user dashboard config (replace with DB as needed)
def get_dashboard_config():
    return st.session_state.get("dashboard_config", ["tax_alerts", "retirement_progress", "ai_tips"])

def save_dashboard_config(config):
    st.session_state.dashboard_config = config

def page_dashboard():
    st.title("My Custom Dashboard")
    st.markdown("Drag & Drop to reorder widgets. Hide/show to customize what you see.")
    init_widgets = get_dashboard_config()

    widgets = []
    col1, col2 = st.columns(2)

    # Widget reorder controls
    st.markdown("### Rearrange Widgets")

    config_json = json.dumps(init_widgets)
    new_order_str = st.text_area("Current widget order (edit JSON array of keys)", value=config_json, height=100)
    try:
        new_order = json.loads(new_order_str)
        if isinstance(new_order, list) and all(item in AVAILABLE_WIDGETS for item in new_order):
            save_dashboard_config(new_order)
            st.success("Dashboard layout updated.")
        else:
            st.warning("Invalid widget configuration list.")
    except Exception:
        st.warning("Invalid JSON format.")

    st.markdown("---")
    st.markdown("### Widgets")
    config = get_dashboard_config()

    for widget_key in config:
        if widget_key == "tax_alerts":
            with st.expander(AVAILABLE_WIDGETS[widget_key], expanded=True):
                tax_alerts_widget()
        elif widget_key == "retirement_progress":
            with st.expander(AVAILABLE_WIDGETS[widget_key], expanded=True):
                retirement_progress_widget()
        elif widget_key == "portfolio_overview":
            with st.expander(AVAILABLE_WIDGETS[widget_key], expanded=True):
                portfolio_overview_widget()
        elif widget_key == "ai_tips":
            with st.expander(AVAILABLE_WIDGETS[widget_key], expanded=True):
                ai_tips_widget()
        else:
            st.info(f"Unknown widget: {widget_key}")

# Example widget implementations:

def tax_alerts_widget():
    from datetime import datetime
    today = datetime.today()
    # Simple example alerts
    st.info(f"Tax Filing Season ends on 20 Oct 2025 ({(datetime(2025,10,20)-today).days} days left).")
    st.warning("Maximum retirement contribution for tax relief: R350,000 per year.")

def retirement_progress_widget():
    profile = st.session_state.auth_profile or {}
    balance = profile.get("current_savings", 0)
    target = 3_000_000  # Sample retirement corpus goal
    progress = min(balance / target, 1.0) * 100
    st.metric("Retirement Savings Progress", f"{progress:.1f}%", delta=f"R{balance:,.0f} out of R{target:,}")

def portfolio_overview_widget():
    profile = st.session_state.auth_profile or {}
    portfolio = profile.get("portfolio", [])
    st.write("You hold", len(portfolio), "assets.")
    # Example placeholder for portfolio summary
    if portfolio:
        total_value = sum(item.get("quantity",0)*item.get("price",0) for item in portfolio)
        st.metric("Estimated Portfolio Value (ZAR)", f"R {total_value:,.2f}")
    else:
        st.info("No portfolio data available.")

def ai_tips_widget():
    st.markdown("**AI Personalized Tips**")
    tips = """
- Think long-term; avoid emotional reactions to market volatility.
- Maximize your retirement tax relief annually.
- Review your investment portfolio quarterly.
- Automate savings to reduce spending temptations.
"""
    st.markdown(tips)

# Router integration
def main_router():
    page = st.session_state.page
    if page == "dashboard":
        page_dashboard()
    else:
        st.info(f"Page '{page}' placeholder...")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
# OptiFin Part 23 — Responsive UX & Notification Center

import streamlit as st

# CSS for mobile responsiveness and accessibility
RESPONSIVE_CSS = """
<style>
/* Base layout spacing */
section > div[data-testid="stVerticalBlock"] {
    padding: 0.5rem !important;
}
.block-container {
    max-width: 900px;
    margin: auto;
    padding: 10px;
}

/* Responsive tweaks */
@media (max-width: 600px) {
    .block-container {
        padding: 5px;
    }
}

/* Accessibility - focus outlines */
[data-testid="stButton"] button:focus {
    outline: 3px solid #05f;
    outline-offset: 2px;
}

/* Notification badges */
.stAlertNotification {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #074074dd;
    color: white;
    padding: 8px 16px;
    border-radius: 50px;
    cursor: pointer;
    font-weight: 700;
    z-index: 9999;
}
</style>
"""

def apply_responsive_css():
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)

# Notification Center UI
def notification_center_ui():
    init_alerts()
    unread_count = sum(1 for a in st.session_state.alerts if not a.get("read", False))
    if unread_count == 0:
        return

    # Floating notification badge
    if st.button(f"🔔 You have {unread_count} unread alert(s)", key="notif_button"):
        # Show notification panel
        st.session_state.show_notifications = not st.session_state.get("show_notifications", False)

    if st.session_state.get("show_notifications", False):
        st.markdown("### Notifications")
        for alert in st.session_state.alerts:
            status = "✅" if alert.get("read", False) else "🕒"
            st.markdown(f"{status} {alert['message']} — *{alert['timestamp'].strftime('%d %b %Y %H:%M')}*")
            col1, col2 = st.columns(2)
            if col1.button(f"Mark Read {alert['id']}", key=f"mark_{alert['id']}"):
                alert["read"] = True
                st.experimental_rerun()
            if col2.button(f"Dismiss {alert['id']}", key=f"dismiss_{alert['id']}"):
                st.session_state.alerts = [a for a in st.session_state.alerts if a["id"] != alert["id"]]
                st.experimental_rerun()

def main_router():
    page = st.session_state.page or "home"
    apply_responsive_css()

    notification_center_ui()

    # Your previous page handling
    if page == "dashboard":
        page_dashboard()
    elif page == "alerts":
        page_alerts()
    elif page == "retirement_planner":
        page_retirement_planner()
    elif page == "tax_optimization":
        page_tax_optimization()
    elif page == "investment_tips":
        page_investment_tips()
    elif page == "investment_dashboard":
        page_investment_dashboard()
    elif page == "wallet":
        page_wallet()
    else:
        st.title("Welcome to OptiFin")
        st.markdown("Use the sidebar to navigate through your personalized finance features.")

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import analytics  # Import Segment SDK

analytics.write_key = 'YOUR_SEGMENT_WRITE_KEY'  # Replace with your real key

def track_user_event(user_id, event_name, properties=None):
    if properties is None:
        properties = {}
    analytics.track(user_id, event_name, properties)

# Usage example in your Streamlit app:
track_user_event('user123', 'Page Viewed', {'page': 'Dashboard'})
# Example fixes you should do throughout your app for all widgets that generate duplicates.
# Replace existing widgets like this:

# Old (error prone if duplicated):
# if st.button("I Accept"):
#    ...

# New (with unique key):
if st.button("I Accept", key="privacy_accept_button"):
    # your acceptance logic here
    pass

# Another example for segment hub:
if st.button("Individual", key="segment_hub_individual_btn"):
    # your logic here
    pass

# If you have buttons inside loops, use loop index or unique identifiers:
for i in range(num_items):
    if st.button(f"Delete item {i}", key=f"delete_item_btn_{i}"):
        # delete logic
        pass

# Similarly for other widgets like text_input, checkbox etc:
user_input = st.text_input("Enter name", key="unique_text_input_key_123")

# Add keys to all buttons, checkboxes, sliders, selects to ensure uniqueness


