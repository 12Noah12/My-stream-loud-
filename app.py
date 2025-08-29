import streamlit as st
import datetime
from collections import deque

# --- App Config ---
APP_NAME = "OptiFin"
APP_YEAR = 2025
DEFAULT_REGION = "South Africa"
DEFAULT_CURRENCY = "ZAR"

# --- State Initialization ---
def init_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'privacy_gate'
    if 'consent_accepted' not in st.session_state:
        st.session_state.consent_accepted = False
    if 'user_segment' not in st.session_state:
        st.session_state.user_segment = None
    if 'sub_module' not in st.session_state:
        st.session_state.sub_module = None
    if 'ai_router_result' not in st.session_state:
        st.session_state.ai_router_result = None
    if "background" not in st.session_state:
        # DEFAULT BACKGROUND IMAGE URL from Unsplash
        st.session_state.background = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1950&q=80"

init_state()

# --- Safe safe rerun function ---
def safe_rerun():
    if not st.session_state.get("_rerun_done", False):
        st.session_state["_rerun_done"] = True
        st.experimental_rerun()

# --- Widget wrapper to assign unique keys ---
_widget_key_counters = {}

def safe_button(label, **kwargs):
    if 'key' not in kwargs:
        count = _widget_key_counters.get(label, 0)
        kwargs['key'] = f"{label}_{count}"
        _widget_key_counters[label] = count + 1
    return st.button(label, **kwargs)

def safe_text_area(label, **kwargs):
    if 'key' not in kwargs:
        count = _widget_key_counters.get(label, 0)
        kwargs['key'] = f"{label}_{count}"
        _widget_key_counters[label] = count + 1
    return st.text_area(label, **kwargs)

# --- Background Image CSS injection ---
def set_background(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{image_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

set_background(st.session_state.background)

# --- Tooltip utility for question marks ---
def tooltip(text):
    # Unicode question mark inside a span with a CSS tooltip on hover
    return f'<span style="color:#0a74da; cursor:help; font-weight:bold;" title="{text}">?</span>'

# --- Privacy Gate Page ---
def page_privacy_gate():
    st.title(f"Welcome to {APP_NAME}")
    st.markdown("""
    ### Privacy & Data Processing Consent
    To use this app, you must agree to the processing of your financial data securely and confidentially.
    We comply with all applicable data protection laws.
    Please read and accept our privacy policy before proceeding.
    """)

    if safe_button(f"I Accept {tooltip('Click to accept our Privacy Policy and continue')}"):
        st.session_state.consent_accepted = True
        st.session_state.page = "segment_hub"
        safe_rerun()

# --- Segment Hub Page ---
def page_segment_hub():
    st.title(f"Welcome to {APP_NAME}")
    st.markdown("#### Select your user segment to begin your personalized financial journey:")

    col1, col2, col3 = st.columns(3)
    with col1:
        if safe_button(f"Individual {tooltip('Financial planning for individuals')}"):
            st.session_state.user_segment = "individual"
            st.session_state.page = "module_form"
            safe_rerun()
    with col2:
        if safe_button(f"Household / Family {tooltip('Planning for households and families')}"):
            st.session_state.user_segment = "household"
            st.session_state.page = "module_form"
            safe_rerun()
    with col3:
        if safe_button(f"Business Owner {tooltip('Financial management for businesses')}"):
            st.session_state.user_segment = "business"
            st.session_state.page = "module_form"
            safe_rerun()

# --- Simplified AI Router ---
def ai_router(input_text: str):
    text = input_text.lower()
    segment = None
    sub_module = None

    if any(word in text for word in ["individual", "personal", "me", "i want"]):
        segment = "individual"
    elif any(word in text for word in ["household", "family", "we", "our"]):
        segment = "household"
    elif any(word in text for word in ["business", "company", "self-employed"]):
        segment = "business"

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

    return segment, sub_module

# --- AI Natural Language Router Page ---
def page_ai_natural_router():
    st.title(f"{APP_NAME} AI Natural Language Assistant")
    st.markdown("Ask any financial planning question or type your intent (e.g., 'Help me with individual retirement planning').")

    user_input = safe_text_area("Your question or command " + tooltip("Type your question or command here"), height=120)

    if safe_button("Analyze and Route"):
        if not user_input.strip():
            st.warning("Please enter some text to analyze.")
        else:
            segment, sub_module = ai_router(user_input)
            if segment and sub_module:
                st.success(f"Detected segment: **{segment}**, module: **{sub_module}**")
                st.session_state.user_segment = segment
                st.session_state.sub_module = sub_module
                st.session_state.page = "module_form"
                safe_rerun()
            else:
                st.info("Unable to determine segment or module clearly; please select from the segment hub.")
                st.session_state.page = "segment_hub"
                safe_rerun()

# --- Main Router ---
def main_router():
    if not st.session_state.consent_accepted:
        page_privacy_gate()
    else:
        page = st.session_state.page
        if page == "privacy_gate":
            page_privacy_gate()
        elif page == "segment_hub":
            page_segment_hub()
        elif page == "ai_natural_router":
            page_ai_natural_router()
        elif page == "module_form":
            st.info("Module Form page to be implemented...")  # Placeholder
        else:
            st.info(f"Unknown page: {page}. Redirecting to segment hub.")
            st.session_state.page = "segment_hub"
            safe_rerun()


if __name__ == "__main__":
    main_router()
import streamlit as st

# --- Widget key counters maintained from Part 1 ---
# (Include at top of your full app script!)
# _widget_key_counters = {}

# --- Reuse safe_button from Part 1 or define again if separate ---
# safe_button() is the same wrapper ensuring unique keys.

# --- CSS Styling for fonts, colors, buttons ---
def inject_css():
    css = f"""
    <style>
        body {{
            color: #eef6ff;
            background-color: rgba(20,24,28, 0.85);
            font-family: 'Inter', sans-serif;
        }}
        .stApp {{
            color: #eef6ff;
        }}
        button {{
            cursor: pointer;
            background: linear-gradient(135deg,#004174,#047860);
            color: white !important;
            font-weight: 700;
            border-radius: 15px;
            padding: 12px 24px;
            box-shadow: 0 6px 20px rgba(4,120,96,0.4);
            transition: background 0.3s ease, box-shadow 0.3s ease;
        }}
        button:hover, button:focus {{
            background: linear-gradient(135deg,#047860,#004174);
            box-shadow: 0 15px 35px rgba(4,120,96,0.7);
            outline: none;
        }}
        label[for] {{
            font-weight: 600;
        }}
        .question-mark {{
            color: #0a74da;
            cursor: help;
            font-weight: bold;
            margin-left: 6px;
            user-select: none;
        }}
    </style>"""
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# --- Helper to show question marks with tooltips ---
def tooltip_span(text):
    return f'<span class="question-mark" title="{text}">?</span>'

# --- Sidebar Navigation with tooltip markers ---
def sidebar_navigation():
    st.sidebar.title("Navigation")
    
    if safe_button(f"Home {tooltip_span('Return to home page')}", key="nav_home"):
        st.session_state.page = "home"
        safe_rerun()
    if safe_button(f"Goals Manager {tooltip_span('Manage your financial goals')}", key="nav_goals"):
        st.session_state.page = "goals_manager"
        safe_rerun()
    if safe_button(f"AI Chat {tooltip_span('Talk with AI Personal Assistant')}", key="nav_ai_chat"):
        st.session_state.page = "chatbot"
        safe_rerun()
    if safe_button(f"Bank Upload {tooltip_span('Upload your bank statements')}", key="nav_bank_upload"):
        st.session_state.page = "bank_upload"
        safe_rerun()
    if safe_button(f"Documents Upload {tooltip_span('Upload supporting documents')}", key="nav_doc_upload"):
        st.session_state.page = "doc_upload"
        safe_rerun()
    if safe_button(f"Predictive Cashflow {tooltip_span('Forecast your cashflow')}", key="nav_pred_cashflow"):
        st.session_state.page = "predictive_cashflow"
        safe_rerun()
    if safe_button(f"Regulatory Updates {tooltip_span('Stay updated on regulations')}", key="nav_reg_updates"):
        st.session_state.page = "reg_updates"
        safe_rerun()
    if safe_button(f"Logout {tooltip_span('Log out from the application')}", key="nav_logout"):
        st.session_state.auth_logged_in = False
        st.session_state.page = "auth_login"
        safe_rerun()


# --- Updated main router to include sidebar ---
def main_router():
    # Ensure sidebar navigation on every page if logged in
    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()
    
    page = st.session_state.page

    if page == "privacy_gate":
        page_privacy_gate()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "ai_natural_router":
        page_ai_natural_router()
    elif page == "home":
        st.title("Welcome Home to OptiFin")
        st.markdown("Use the sidebar or AI assistant to navigate.")
    elif page == "goals_manager":
        st.info("Goals Manager page to be implemented...")
    elif page == "chatbot":
        st.info("Chatbot AI assistant page to be implemented...")
    elif page == "bank_upload":
        st.info("Bank Upload page to be implemented...")
    elif page == "doc_upload":
        st.info("Documents Upload page to be implemented...")
    elif page == "predictive_cashflow":
        st.info("Predictive Cashflow page to be implemented...")
    elif page == "reg_updates":
        st.info("Regulatory Updates page to be implemented...")
    elif page == "auth_login":
        st.info("Login page to be implemented...")
    else:
        st.warning(f"Unknown page '{page}', redirecting to privacy gate.")
        st.session_state.page = "privacy_gate"
        safe_rerun()

if __name__ == "__main__":
    main_router()
import streamlit as st
import hashlib
import uuid
import json
import pathlib

USERS_FILE = "optifin_users.json"

# Password hashing utility
def hash_password(password: str) -> str:
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return f"{hashed}:{salt}"

def verify_password(stored_password: str, provided_password: str) -> bool:
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

# Initialize auth state
def init_auth_state():
    if 'auth_logged_in' not in st.session_state:
        st.session_state.auth_logged_in = False
    if 'auth_username' not in st.session_state:
        st.session_state.auth_username = ""
    if 'auth_profile' not in st.session_state:
        st.session_state.auth_profile = {}
    if 'auth_message' not in st.session_state:
        st.session_state.auth_message = ""

# Registration page
def auth_register():
    st.header("Register New Account")
    username = safe_text_input("Choose username " + tooltip_span("Enter desired login username"))
    password = safe_text_input("Choose password " + tooltip_span("Must be secure"), type="password")
    password_confirm = safe_text_input("Confirm password " + tooltip_span("Must match password"), type="password")

    if safe_button("Register"):
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
        safe_rerun()

# Login page
def auth_login():
    st.header("Login to OptiFin")
    username = safe_text_input("Username " + tooltip_span("Enter your login username"))
    password = safe_text_input("Password " + tooltip_span("Your password"), type="password")

    if safe_button("Login"):
        users = load_users()
        if username not in users or not verify_password(users[username]["password"], password):
            st.error("Invalid username or password.")
            return
        st.session_state.auth_logged_in = True
        st.session_state.auth_username = username
        st.session_state.auth_profile = users[username]["profile"]
        st.session_state.page = "home"
        safe_rerun()

# Logout helper
def auth_logout():
    st.session_state.auth_logged_in = False
    st.session_state.auth_username = ""
    st.session_state.auth_profile = {}
    st.session_state.page = "auth_login"
    safe_rerun()

# Profile editing page
def auth_profile_edit():
    st.header("Edit Profile")
    profile = st.session_state.auth_profile or {}
    currency = st.selectbox("Preferred Currency " + tooltip_span("Your currency for display"), [DEFAULT_CURRENCY, "USD", "GBP", "EUR"],
                            index=[DEFAULT_CURRENCY, "USD", "GBP", "EUR"].index(profile.get("currency", DEFAULT_CURRENCY)))
    region = st.selectbox("Region/Country " + tooltip_span("Your region for tax rules"), [DEFAULT_REGION, "United Kingdom", "United States", "Australia"],
                          index=[DEFAULT_REGION, "United Kingdom", "United States", "Australia"].index(profile.get("region", DEFAULT_REGION)))
    language = st.selectbox("Language " + tooltip_span("Your preferred language"), ["en", "fr", "es"],
                            index=["en", "fr", "es"].index(profile.get("language", "en")))

    if safe_button("Save Profile Changes"):
        profile["currency"] = currency
        profile["region"] = region
        profile["language"] = language
        users = load_users()
        users[st.session_state.auth_username]["profile"] = profile
        save_users(users)
        st.success("Profile updated!")

# Update main router to support auth
def main_router():
    # Show sidebar if logged in
    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()
        
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
    elif page == "ai_natural_router":
        page_ai_natural_router()
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
        st.markdown("Use the sidebar or AI assistant to navigate.")
    else:
        st.warning(f"Unknown page '{page}', redirecting to privacy_gate.")
        st.session_state.page = "privacy_gate"
        safe_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import streamlit as st
import datetime
from typing import List, Dict

# --- Safe wrappers from previous parts assumed imported ---

# Load and save goals from session state profile
def load_goals() -> List[Dict]:
    profile = st.session_state.auth_profile or {}
    return profile.get("goals", [])

def save_goals(goals: List[Dict]):
    profile = st.session_state.auth_profile or {}
    profile["goals"] = goals
    st.session_state.auth_profile = profile
    users = load_users()
    if st.session_state.auth_username in users:
        users[st.session_state.auth_username]["profile"]["goals"] = goals
        save_users(users)

# Goals management page
def goals_manager():
    st.header("Manage Your Financial Goals")
    goals = load_goals()
    for i, goal in enumerate(goals):
        with st.expander(f"Goal #{i+1}: {goal.get('name', 'Unnamed Goal')}"):
            name = safe_text_input(f"Goal Name #{i+1} " + tooltip_span("Name for this financial goal"),
                                   value=goal.get("name", ""), key=f"goal_name_{i}")
            amount = st.number_input(f"Target Amount #{i+1} " + tooltip_span("Money you want to save for this goal"),
                                     min_value=0.0, value=goal.get("amount", 0.0), key=f"goal_amount_{i}")
            target_date = st.date_input(f"Target Date #{i+1} " + tooltip_span("Date by which you want to reach this goal"),
                                        value=datetime.date.today() + datetime.timedelta(days=365),
                                        key=f"goal_date_{i}")

            goals[i] = {
                "name": name,
                "amount": amount,
                "target_date": target_date.isoformat() if hasattr(target_date, "isoformat") else str(target_date),
            }

            if safe_button(f"Remove Goal #{i+1}", key=f"goal_remove_{i}"):
                goals.pop(i)
                save_goals(goals)
                safe_rerun()

    if safe_button("Add New Goal"):
        goals.append({"name": "", "amount": 0.0, "target_date": datetime.date.today().isoformat()})
        save_goals(goals)
        safe_rerun()

    save_goals(goals)

# Module form (simplified)
def module_form():
    st.title(f"Module for {st.session_state.user_segment.capitalize()}")
    modules = ["investment", "tax", "retirement", "estate", "budget", "protection"]

    selected_module = st.selectbox("Select a module " + tooltip_span("Choose a financial planning area"),
                                   modules, key="module_select")

    st.markdown(f"**You selected the module:** {selected_module}")

    # Example inputs per module
    if selected_module == "investment":
        net_worth = st.number_input("Enter net worth (R) " + tooltip_span("Total value of your assets"),
                                    min_value=0.0, step=1000.0)
        risk_tolerance = st.slider("Risk tolerance (1 low - 5 high) " + tooltip_span("Your appetite for investment risk"),
                                   1, 5, 3)
        st.markdown(f"Analyzing investment options based on net worth {net_worth} and risk tolerance {risk_tolerance}...")
    elif selected_module == "tax":
        income = st.number_input("Annual taxable income (R) " + tooltip_span("Your yearly taxable earnings"),
                                min_value=0.0, step=1000.0)
        deductions = st.number_input("Total deductions (R) " + tooltip_span("Tax deductible expenses"),
                                     min_value=0.0, step=1000.0)
        st.markdown(f"Calculating tax based on income {income} and deductions {deductions}...")
    elif selected_module == "retirement":
        current_age = st.number_input("Current age " + tooltip_span("Your current age"),
                                      min_value=18, max_value=80)
        retire_age = st.number_input("Planned retirement age " + tooltip_span("Age you plan to retire"),
                                     min_value=current_age + 1, max_value=100)
        desired_fund = st.number_input("Desired retirement fund (R) " + tooltip_span("Amount you want at retirement"),
                                       min_value=0.0, step=1000.0)
        st.markdown(f"Estimating retirement readiness from age {current_age} to {retire_age}...")
    else:
        st.info("Module form under construction...")

# Simple chatbot starter page
def page_chatbot():
    st.title("OptiFin AI Personal Financial Assistant")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = safe_text_input("Ask me anything about your finances or goals " + tooltip_span("Type your financial question here"),
                                key="chat_input")
    if safe_button("Send"):
        if user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
            # Placeholder response, replace with AI logic
            st.session_state.chat_history.append({"role": "assistant", "content": "Sorry, AI integration pending."})
            safe_rerun()

    # Display chat so far
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**OptiFin AI:** {msg['content']}")
import streamlit as st
import pandas as pd

# --- Safe wrappers assumed available ---

# --- Upload Bank Transactions ---
def page_bank_upload():
    st.header("Upload Bank Transactions")
    uploaded_file = st.file_uploader("Upload your bank transactions CSV " + tooltip_span("CSV must include Date, Amount columns"),
                                     type=["csv"], key="upload_bank_csv")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().lower() for c in df.columns]

            if not all(col in df.columns for col in ["date", "amount"]):
                st.error("CSV must contain 'date' and 'amount' columns.")
                return

            df["date"] = pd.to_datetime(df["date"])
            st.success(f"Successfully uploaded {len(df)} transactions.")
            st.dataframe(df.head(10))

            # Placeholder: further processing for your app

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.info("Please upload your transactions CSV file.")

# --- Upload Supporting Documents ---
def page_doc_upload():
    st.header("Upload Supporting Documents")
    uploaded_files = st.file_uploader("Upload PDFs, tax docs etc. " + tooltip_span("Multiple files allowed"),
                                      type=["pdf", "docx", "xlsx"], accept_multiple_files=True, key="upload_docs")

    if uploaded_files:
        st.success(f"{len(uploaded_files)} files uploaded successfully.")
        # Placeholder: process uploaded files here
    else:
        st.info("Upload your supporting documents for processing.")

# --- Latest Regulatory Updates ---
def display_regulatory_updates():
    st.header("Latest Regulatory Updates")
    # Placeholder for live feed API. Here are static examples:
    updates = [
        "New SARS tax exemption thresholds announced.",
        "Retirement fund contribution limits updated for 2025.",
        "Important deadline for submission of annual tax returns approaching.",
        "Government launches financial literacy campaign."
    ]
    for update in updates:
        st.markdown(f"- {update}")

# --- Integrate these pages in main router ---
def main_router():
    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()  # Sidebar from Part 2

    page = st.session_state.page

    if page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    # Include routing previously defined...
    else:
        # Calling previous router pages (privacy, segment, auth etc.)
        if page == "privacy_gate":
            page_privacy_gate()
        elif page == "segment_hub":
            page_segment_hub()
        elif page == "ai_natural_router":
            page_ai_natural_router()
        elif page == "auth_login":
            auth_login()
        elif page == "auth_register":
            auth_register()
        elif page == "auth_profile_edit":
            auth_profile_edit()
        elif page == "goals_manager":
            goals_manager()
        elif page == "module_form":
            module_form()
        elif page == "chatbot":
            page_chatbot()
        elif page == "home":
            st.title(f"Welcome home, {st.session_state.auth_username}!")
            st.markdown("Use the sidebar or AI assistant to navigate.")
        else:
            st.warning(f"Unknown page '{page}', redirecting to privacy gate.")
            st.session_state.page = "privacy_gate"
            safe_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import streamlit as st
import numpy as np
import textblob
import pandas as pd
import json

# --- Report generation stub ---
def generate_ai_report_text(profile, metrics):
    # Placeholder for AI-generated report text; extend with OpenAI or similar
    return (
        "Monthly Financial Summary:\n"
        f"- Current Savings: R{metrics.get('current_savings', 0):,.2f}\n"
        f"- Projected Growth: R{metrics.get('projection_value', 0):,.2f}\n"
        f"- Estimated Tax: R{metrics.get('estimated_tax', 0):,.2f}\n"
        "Consult your financial advisor for details."
    )

def page_monthly_report():
    st.header("Monthly Financial Report")
    profile = st.session_state.auth_profile or {}
    metrics = {
        "current_savings": 250000,
        "projection_value": 1500000,
        "estimated_tax": 250000,
    }
    report_text = generate_ai_report_text(profile, metrics)
    st.markdown(f"**Report:**\n\n{report_text}")

    if safe_button("Generate PDF Report"):
        st.info("PDF generation coming soon...")

    if safe_button("Generate Excel Report"):
        st.info("Excel report generation coming soon...")

# --- Sentiment Insights page ---
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

# --- Final CSS polish ---
def final_css():
    theme = st.session_state.get("theme", "dark")
    text_c = "#eef6ff" if theme == "dark" else "#111"
    bgrgba = "rgba(20,24,28, 0.85)" if theme == "dark" else "rgba(255,255,255, 0.9)"
    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )

# Add final_css call in main, or near start
final_css()
import streamlit as st
import hashlib

# Initialize achievements set in session state
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

    if safe_button("Back to Home"):
        st.session_state.page = "home"
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Community forum placeholder
def page_community_forum():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Community Forum")
    st.info("The forum is coming soon! Join our mailing list or social media for updates.")
    if safe_button("Back to Home"):
        st.session_state.page = "home"
        safe_rerun()
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

    if safe_button("Back to Home"):
        st.session_state.page = "home"
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Referral program page
def page_referral_program():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Referral Program")
    st.info("Invite your friends to OptiFin and earn credits towards premium reports and advice.")
    if st.session_state.auth_logged_in:
        # Generate referral code (md5 first 8 chars of username hash)
        referral_code = hashlib.md5(st.session_state.auth_username.encode()).hexdigest()[:8].upper()
        st.code(referral_code)
        st.markdown("Share your referral code with friends!")
    else:
        st.warning("Please log in to see your referral code.")

    if safe_button("Back to Home"):
        st.session_state.page = "home"
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Final base CSS with background layering and font colors
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

# Call apply_global_styles() near app start or router...
apply_global_styles()

# Footer example for display in main layout
def app_footer():
    st.markdown(f"<footer>© {APP_YEAR} {APP_NAME} --- Smart financial planning, simplified.</footer>", unsafe_allow_html=True)
# --- Improved main router with exclusive privacy gate display ---
def main_router():
    # Show privacy gate ONLY if consent NOT given
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return  # Stop further rendering so no duplicates
    
    # Proceed only if consent accepted
    page = st.session_state.get("page", "privacy_gate")
    
    if page == "privacy_gate":
        # Safety fallback — should not happen if consent accepted
        page_privacy_gate()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "ai_natural_router":
        page_ai_natural_router()
    elif page == "auth_login":
        auth_login()
    elif page == "auth_register":
        auth_register()
    elif page == "auth_profile_edit":
        auth_profile_edit()
    elif page == "goals_manager":
        goals_manager()
    elif page == "module_form":
        module_form()
    elif page == "chatbot":
        page_chatbot()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "predictive_cashflow":
        page_predictive_cashflow()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    elif page == "achievements":
        page_achievements()
    elif page == "community":
        page_community_forum()
    elif page == "education":
        page_educational_resources()
    elif page == "referral":
        page_referral_program()
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Unknown page '{page}'. Redirecting to segment hub.")
        st.session_state.page = "segment_hub"
        safe_rerun()

# --- Fix button label tooltips --- 
# Instead of embed HTML in the button label, do this pattern:
# st.markdown(f"Question text {tooltip_span('Helpful explanation')}", unsafe_allow_html=True)
# Then, below or next to it, use:
# if safe_button("Button Text", key="your_button_key"):
#     action()
#
# For buttons in titles, segment hub etc., remove any embedded HTML or special chars in label.

# For example, in segment hub page replace:

# if safe_button("Individual " + tooltip_span("Financial planning for individuals")):

# with:

st.markdown("Individual " + tooltip_span("Financial planning for individuals"), unsafe_allow_html=True)
if safe_button("Select Individual", key="segment_individual_btn"):
    # your button action here

# This keeps the question mark tooltip visible as separate text, not inside button text, avoiding raw html issues.



