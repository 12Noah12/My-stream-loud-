import streamlit as st
import datetime

# --- Page config and wide layout ---
st.set_page_config(
    page_title="OptiFin - Smart Financial Planning",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Global constants ---
APP_NAME = "OptiFin"
APP_YEAR = 2025
DEFAULT_REGION = "South Africa"
DEFAULT_CURRENCY = "ZAR"

# --- Background image and overlay style ---
BACKGROUND_IMAGE_URL = (
    "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1950&q=80"
)

def inject_background_and_css():
    css = f"""
    <style>
    /* Background image and dark overlay */
    .stApp {{
        background: 
            linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)),
            url("{BACKGROUND_IMAGE_URL}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #eef6ff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    /* Glass morphism effect for containers */
    .glass-card {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 30px;
        box-shadow: 0 15px 40px rgba(8, 24, 70, 0.6);
        backdrop-filter: blur(10px);
        transition: box-shadow 0.3s ease;
        color: #eef6ff;
    }}
    .glass-card:hover {{
        box-shadow: 0 25px 55px rgba(8, 24, 70, 0.8);
    }}
    h1, h2, h3, h4 {{
        font-weight: 700;
        color: #eef6ff;
    }}
    button {{
        background: linear-gradient(135deg, #004174, #047860);
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
        background: linear-gradient(135deg, #047860, #004174);
        box-shadow: 0 15px 35px rgba(4,120,96,0.7);
        outline: none;
    }}
    .stTextInput>div>div>input {{
        border-radius: 15px;
        border: 2px solid #05f7a7;
        padding: 14px 18px;
        font-size: 16px;
        color: #eef6ff;
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
    .question-mark {{
        color: #0a74da;
        cursor: help;
        font-weight: bold;
        margin-left: 6px;
        user-select: none;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_background_and_css()

# --- Tooltip utility for question marks ---
def tooltip(text):
    return f'<span class="question-mark" title="{text}">?</span>'

# --- Safe widget wrappers with unique keys ---
_key_counters = {}

def safe_key(label):
    count = _key_counters.get(label, 0)
    _key_counters[label] = count + 1
    return f"{label}_{count}"

def safe_button(label, **kwargs):
    if "key" not in kwargs:
        kwargs["key"] = safe_key(label)
    return st.button(label, **kwargs)

def safe_text_input(label, **kwargs):
    if "key" not in kwargs:
        kwargs["key"] = safe_key(label)
    return st.text_input(label, **kwargs)

# --- Session state initialization ---
def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "privacy_gate"
    if "consent_accepted" not in st.session_state:
        st.session_state.consent_accepted = False
    if "user_segment" not in st.session_state:
        st.session_state.user_segment = None
    if "sub_module" not in st.session_state:
        st.session_state.sub_module = None
    if "auth_logged_in" not in st.session_state:
        st.session_state.auth_logged_in = False
    if "auth_username" not in st.session_state:
        st.session_state.auth_username = ""
    if "auth_profile" not in st.session_state:
        st.session_state.auth_profile = {}
    if "ai_router_result" not in st.session_state:
        st.session_state.ai_router_result = None

init_state()

# --- Privacy gate page ---
def page_privacy_gate():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.title(f"Welcome to {APP_NAME}")
    st.markdown("""
    To use this app, please accept our
    [Privacy Policy](https://streamlit.io/privacy-policy) and consent to data processing.
    """)
    if safe_button("I Accept " + tooltip("Click here to accept privacy policy")):
        st.session_state.consent_accepted = True
        st.session_state.page = "segment_hub"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Segment hub page ---
def page_segment_hub():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.title("Select your user segment")
    st.markdown(
        f"Please select the segment that best describes you to begin your financial journey."
    )
    cols = st.columns(3)

    with cols[0]:
        st.markdown("Individual " + tooltip("Financial planning for an individual"))
        if safe_button("Select Individual", key="segment_individual_btn"):
            st.session_state.user_segment = "individual"
            st.session_state.page = "module_form"
            st.experimental_rerun()

    with cols[1]:
        st.markdown("Household " + tooltip("Planning for households/families"))
        if safe_button("Select Household", key="segment_household_btn"):
            st.session_state.user_segment = "household"
            st.session_state.page = "module_form"
            st.experimental_rerun()

    with cols[2]:
        st.markdown("Business Owner " + tooltip("Financial management for businesses"))
        if safe_button("Select Business", key="segment_business_btn"):
            st.session_state.user_segment = "business"
            st.session_state.page = "module_form"
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Main router ---
def main_router():
    if not st.session_state.consent_accepted:
        page_privacy_gate()
        return  # Avoid rendering other pages

    page = st.session_state.page

    if page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page to be implemented...")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to segment hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    main_router()
import streamlit as st
import hashlib
import uuid
import json
import pathlib

# --- Sidebar Navigation ---
def sidebar_navigation():
    st.sidebar.title("Navigation")
    
    if safe_button("Home", key="nav_home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    if safe_button("Goals Manager", key="nav_goals"):
        st.session_state.page = "goals_manager"
        st.experimental_rerun()
        
    if safe_button("AI Chat", key="nav_ai_chat"):
        st.session_state.page = "chatbot"
        st.experimental_rerun()

    if safe_button("Bank Upload", key="nav_bank_upload"):
        st.session_state.page = "bank_upload"
        st.experimental_rerun()

    if safe_button("Documents Upload", key="nav_doc_upload"):
        st.session_state.page = "doc_upload"
        st.experimental_rerun()

    if safe_button("Predictive Cashflow", key="nav_pred_cashflow"):
        st.session_state.page = "predictive_cashflow"
        st.experimental_rerun()

    if safe_button("Regulatory Updates", key="nav_reg_updates"):
        st.session_state.page = "reg_updates"
        st.experimental_rerun()

    if safe_button("Logout", key="nav_logout"):
        st.session_state.auth_logged_in = False
        st.session_state.page = "auth_login"
        st.experimental_rerun()

# --- Authentication utilities ---
USERS_FILE = "optifin_users.json"

def hash_password(password: str) -> str:
    salt = uuid.uuid4().hex
    hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    return f"{hashed}:{salt}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    try:
        hashed, salt = stored_password.split(':')
        check = hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()
        return check == hashed
    except Exception:
        return False

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

# --- Login page ---
def auth_login():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Login to OptiFin")

    username = safe_text_input("Username " + tooltip("Enter your login username"))
    password = safe_text_input("Password " + tooltip("Your password"), type="password")

    if safe_button("Login"):
        users = load_users()
        if username not in users or not verify_password(users[username]["password"], password):
            st.error("Invalid username or password.")
        else:
            st.session_state.auth_logged_in = True
            st.session_state.auth_username = username
            st.session_state.auth_profile = users[username]["profile"]
            st.session_state.page = "home"
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Registration page ---
def auth_register():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Register New Account")

    username = safe_text_input("Choose username " + tooltip("Enter desired username"))
    password = safe_text_input("Choose password " + tooltip("Password must be secure"), type="password")
    password_confirm = safe_text_input("Confirm password " + tooltip("Must match password"), type="password")

    if safe_button("Register"):
        if not username or not password or not password_confirm:
            st.error("All fields are required.")
        elif password != password_confirm:
            st.error("Passwords do not match.")
        else:
            users = load_users()
            if username in users:
                st.error("Username already exists.")
            else:
                users[username] = {
                    "password": hash_password(password),
                    "profile": {
                        "currency": DEFAULT_CURRENCY,
                        "region": DEFAULT_REGION,
                        "language": "en",
                        "goals": [],
                    }
                }
                save_users(users)
                st.success("Registration successful! Please log in.")
                st.session_state.page = "auth_login"
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- Update main_router to include sidebar and auth pages ---
def main_router():
    # Show sidebar nav if logged in
    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return  # avoid showing other pages
    
    page = st.session_state.page

    if page == "auth_login":
        auth_login()
    elif page == "auth_register":
        auth_register()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to segment hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    main_router()
import streamlit as st
import datetime

# --- Helper function to safely update page with on_click ---
def go_to_page(page_name):
    st.session_state.page = page_name

# --- AI Natural Language Router ---
def page_ai_natural_router():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.title("OptiFin AI Assistant")
    st.markdown("Ask any financial question or type your intent (e.g., 'Help me with retirement planning').")

    user_input = st.text_area("Your question " + tooltip("Type your question or command here"), height=120, key="ai_input")

    def analyze_and_route():
        text = st.session_state.ai_input.lower()
        # Simple keyword routing:
        if "individual" in text:
            st.session_state.user_segment = "individual"
        elif "household" in text:
            st.session_state.user_segment = "household"
        elif "business" in text:
            st.session_state.user_segment = "business"
        else:
            st.session_state.user_segment = None

        if "retirement" in text:
            st.session_state.sub_module = "retirement"
        elif "tax" in text:
            st.session_state.sub_module = "tax"
        else:
            st.session_state.sub_module = None

        if st.session_state.user_segment and st.session_state.sub_module:
            st.session_state.page = "module_form"
        else:
            st.session_state.page = "segment_hub"

    st.button("Analyze and Route", on_click=analyze_and_route)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Goals Manager with dynamic form rows and add/remove functionality ---
def goals_manager():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Manage Your Financial Goals")

    # Load goals from profile or create empty list
    profile = st.session_state.auth_profile or {}
    goals = profile.get("goals", [])

    if "temp_goals" not in st.session_state:
        st.session_state.temp_goals = goals.copy()

    for i, goal in enumerate(st.session_state.temp_goals):
        with st.expander(f"Goal #{i+1}: {goal.get('name', '')}"):
            name = st.text_input(f"Goal Name #{i+1} " + tooltip("Name for this financial goal"),
                                 value=goal.get("name", ""), key=f"goal_name_{i}")
            amount = st.number_input(f"Target Amount #{i+1} " + tooltip("Money you want to save"),
                                     value=goal.get("amount", 0.0), min_value=0.0, step=100.0, key=f"goal_amount_{i}")
            target_date = st.date_input(f"Target Date #{i+1} " + tooltip("By when to achieve this goal"),
                                        value=datetime.date.today() + datetime.timedelta(days=365),
                                        key=f"goal_date_{i}")

            st.session_state.temp_goals[i] = {
                "name": name,
                "amount": amount,
                "target_date": str(target_date),
            }
            remove_key = f"remove_goal_{i}"

            if st.button("Remove this Goal", key=remove_key):
                st.session_state.temp_goals.pop(i)
                st.experimental_rerun()
                break  # Important to break loop after mutation

    def add_goal():
        st.session_state.temp_goals.append({"name": "", "amount": 0.0, "target_date": datetime.date.today().isoformat()})

    st.button("Add New Goal", on_click=add_goal)

    def save_goals():
        # Save current temp_goals to profile and persist if desired
        profile["goals"] = st.session_state.temp_goals
        st.session_state.auth_profile = profile
        st.success("Goals saved!")

    st.button("Save Goals", on_click=save_goals)

    st.markdown('</div>', unsafe_allow_html=True)

# --- Update main_router ---
def main_router():
    if not st.session_state.consent_accepted:
        page_privacy_gate()
        return

    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "ai_natural_router":
        page_ai_natural_router()
    elif page == "goals_manager":
        goals_manager()
    elif page == "auth_login":
        auth_login()
    elif page == "auth_register":
        auth_register()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pathlib

# --- Load credential config ---
CONFIG_FILE = "credentials.yml"

def load_auth_config():
    if pathlib.Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r") as file:
            return yaml.load(file, Loader=SafeLoader)
    else:
        st.error("Auth config file missing!")
        return None

# --- Initialize and return the authenticator object ---
def init_authenticator():
    config = load_auth_config()
    if config:
        return stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
        )
    return None

# --- Authentication Page Using Streamlit-Authenticator ---
def auth_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.title("Login to OptiFin")

    authenticator = init_authenticator()
    if not authenticator:
        st.error("Authentication configuration error.")
        return

    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status:
        st.session_state.auth_logged_in = True
        st.session_state.auth_username = username
        st.session_state.auth_profile = {}  # Can be fetched or extended from DB
        st.success(f"Welcome, {name}!")
        if st.button("Logout"):
            authenticator.logout("Logout", "main")
            st.session_state.auth_logged_in = False
            st.session_state.auth_username = ""
            st.session_state.page = "auth_login"
            st.experimental_rerun()

    elif authentication_status == False:
        st.error("Username/password is incorrect")
    elif authentication_status == None:
        st.warning("Please enter your username and password")

    st.markdown('</div>', unsafe_allow_html=True)

# --- Update router ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return

    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import pandas as pd

# --- Page to upload bank csv statements ---
def page_bank_upload():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Upload Bank Transactions")
    uploaded_file = st.file_uploader(
        "Upload your bank transactions CSV " + tooltip("CSV must include Date, Amount columns"),
        type=["csv"],
        key="upload_bank_csv",
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().lower() for c in df.columns]
            if not {"date", "amount"}.issubset(df.columns):
                st.error("CSV must contain 'date' and 'amount' columns.")
            else:
                df["date"] = pd.to_datetime(df["date"])
                st.success(f"Successfully loaded {len(df)} transactions.")
                st.dataframe(df.head(10))
                # Placeholder: process transactions into profile or database
        except Exception as e:
            st.error(f"Error processing CSV: {e}")
    else:
        st.info("Please upload a CSV file with your transactions.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Page to upload supporting documents (PDF, DOCX, XLSX) ---
def page_doc_upload():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Upload Supporting Documents")
    uploaded_files = st.file_uploader(
        "Upload PDFs, tax docs etc. " + tooltip("Multiple files allowed"),
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        key="upload_docs",
    )
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded successfully.")
        # Placeholder: process files
    else:
        st.info("Upload supporting documents for your financial planning.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Display latest regulatory updates ---
def display_regulatory_updates():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Latest Regulatory Updates")
    updates = [
        "New SARS tax exemption thresholds announced.",
        "Retirement fund contribution limits updated for 2025.",
        "Important deadline for submission of annual tax returns approaching.",
        "Government launches financial literacy campaign.",
    ]
    for update in updates:
        st.markdown(f"- {update}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Extend main_router ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return
    
    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "goals_manager":
        goals_manager()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import plotly.express as px
import pandas as pd
import numpy as np

# --- Monthly Financial Report with charts and AI-generated summary ---
def page_monthly_report():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Monthly Financial Report")

    # Example simulated data for visualization
    dates = pd.date_range(end=pd.Timestamp.today(), periods=12, freq='M')
    savings = np.cumsum(np.random.uniform(1000, 5000, size=12))
    expenses = np.cumsum(np.random.uniform(500, 4000, size=12))

    df_report = pd.DataFrame({"Date": dates, "Savings": savings, "Expenses": expenses})

    st.subheader("Savings vs Expenses Over Last Year")
    fig = px.line(df_report, x="Date", y=["Savings", "Expenses"], 
                  title="Savings and Expenses Trend",
                  labels={"value": "Amount (ZAR)", "Date": "Month"})
    st.plotly_chart(fig, use_container_width=True)

    # AI generated summary (placeholder text)
    summary = f"""
    Your total savings have been steadily increasing over the past year, 
    with an average monthly savings of ZAR {savings.mean():.2f}.
    Monthly expenses have fluctuated but remain controlled on average.
    Consider reviewing any months with unusually high expenses.
    """
    st.markdown("### Summary")
    st.info(summary)

    st.markdown('</div>', unsafe_allow_html=True)

# --- Sentiment & Portfolio Insights page ---
def page_sentiment_insights():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Market Sentiment & Portfolio Insights")

    headlines = [
        "Stock markets rally amid easing inflation concerns",
        "Tech sector reports mixed earnings for Q3",
        "South African Rand strengthens against US dollar",
        "New government tax incentives announced",
    ]

    st.subheader("Latest Market Headlines")
    for h in headlines:
        st.markdown(f"- {h}")

    # Simple sentiment placeholder (could integrate with sentiment analysis APIs)
    st.markdown("### Market Sentiment: Positive")
    st.markdown("Overall sentiment is positive based on recent news headlines.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- Update main_router to include new pages ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return

    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "goals_manager":
        goals_manager()
    elif page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import streamlit as st

# --- Chatbot page with simple conversational interface ---
def page_chatbot():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("OptiFin AI Chat Assistant")
    st.markdown("Ask any question about your financial plans, goals, or general advice. Powered by AI.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    def submit_message():
        user_msg = st.session_state.user_input.strip()
        if user_msg:
            # Add user's message
            st.session_state.chat_history.append({"role": "user", "content": user_msg})

            # Simulate AI response - replace with real AI call
            ai_response = f"AI Response to: {user_msg}"
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

            st.session_state.user_input = ""

    st.text_input("Your message:", key="user_input", on_change=submit_message, placeholder="Ask me anything...")

    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"**You:** {chat['content']}")
        else:
            st.markdown(f"**OptiFin AI:** {chat['content']}")

    st.markdown('</div>', unsafe_allow_html=True)

# --- User Achievement tracking and display ---
def page_achievements():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Achievements & Rewards")
    if "achievements" not in st.session_state:
        st.session_state.achievements = set()

    # Example achievements
    if st.session_state.page == "goals_manager" and "Goal Setter" not in st.session_state.achievements:
        st.session_state.achievements.add("Goal Setter")

    st.markdown("### Your Achievements:")
    if not st.session_state.achievements:
        st.info("No achievements yet. Start working on your goals to unlock achievements!")
    else:
        for ach in sorted(st.session_state.achievements):
            st.markdown(f"- ✅ {ach}")

    if safe_button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Extend main_router ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return
    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "chatbot":
        page_chatbot()
    elif page == "achievements":
        page_achievements()
    elif page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "goals_manager":
        goals_manager()
    elif page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import hashlib

# --- Referral program page ---
def page_referral_program():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Referral Program")
    st.info("Invite your friends to OptiFin and earn rewards!")

    if st.session_state.auth_logged_in:
        # Generate referral code from username hash
        username = st.session_state.auth_username
        referral_code = hashlib.sha256(username.encode()).hexdigest()[:8].upper()
        st.markdown(f"Your referral code: **{referral_code}**")

        if safe_button("Copy referral code to clipboard"):
            # Clipboard copy not natively supported in Streamlit, just informational here
            st.success("Use your system clipboard to copy the code above.")
    else:
        st.warning("Please log in to view your referral code.")

    if safe_button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Educational resources page ---
def page_educational_resources():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Financial Education & Tutorials")

    tutorials = [
        {"title": "Basics of Investing", "link": "https://www.investopedia.com/articles/basics/06/invest1000.asp"},
        {"title": "Tax Planning Strategies", "link": "https://www.sars.gov.za/"},
        {"title": "Retirement Planning 101", "link": "https://www.aarp.org/retirement/planning-for-retirement/"},
        {"title": "Understanding Credit & Debt", "link": "https://www.consumerfinance.gov/"},
    ]

    for tutorial in tutorials:
        st.markdown(f"- [{tutorial['title']}]({tutorial['link']})")

    if safe_button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- Export Options Page ---
def page_export_data():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Export Your Financial Data")

    # Example placeholder - later connect to real financial data
    sample_data = pd.DataFrame({
        "Date": pd.date_range(datetime.date.today(), periods=5),
        "Category": ["Income", "Expense", "Savings", "Investment", "Expense"],
        "Amount": [5000, -1500, 2000, 1200, -500]
    })

    st.dataframe(sample_data)

    csv = sample_data.to_csv(index=False).encode('utf-8')
    excel = sample_data.to_excel(index=False, engine='openpyxl')

    st.download_button(label="Download CSV", data=csv, file_name="financial_data.csv", mime="text/csv")
    st.download_button(label="Download Excel", data=excel, file_name="financial_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if safe_button("Back to Home"):
        st.session_state.page = "home"
        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- Extend main_router ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return

    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "referral":
        page_referral_program()
    elif page == "education":
        page_educational_resources()
    elif page == "export":
        page_export_data()
    elif page == "chatbot":
        page_chatbot()
    elif page == "achievements":
        page_achievements()
    elif page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "goals_manager":
        goals_manager()
    elif page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import streamlit as st

# --- Financial Insights with LLM Placeholder ---
def page_financial_insights():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Financial Insights & Analysis Powered by AI")

    st.markdown("""
    This section provides intelligent insights from your financial data
    using AI and advanced large language models (LLMs). Features include:
    - Analysis of uploaded documents and bank transactions
    - AI-generated comments, trend predictions, and recommendations
    - Personalized financial tips based on your goals and profile
    """)

    user_question = st.text_input("Ask a financial question or request insights:")

    def generate_insights():
        query = st.session_state.get("insight_query", "")
        if query:
            # Placeholder: replace with actual LLM call
            response = f"AI-generated insight response to: '{query}'"
            st.session_state.insight_response = response
        else:
            st.session_state.insight_response = "Please enter a question."

    st.text_input("Input your query here", key="insight_query", on_change=generate_insights)

    if "insight_response" in st.session_state:
        st.markdown("### AI Insight Response")
        st.info(st.session_state.insight_response)

    st.markdown('</div>', unsafe_allow_html=True)

# --- Update main_router ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return

    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "financial_insights":
        page_financial_insights()
    elif page == "referral":
        page_referral_program()
    elif page == "education":
        page_educational_resources()
    elif page == "export":
        page_export_data()
    elif page == "chatbot":
        page_chatbot()
    elif page == "achievements":
        page_achievements()
    elif page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "goals_manager":
        goals_manager()
    elif page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()


if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import streamlit as st

# --- Modern AI Chat Assistant with Stateful Chat UI ---
def page_chatbot():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("OptiFin AI Chat Assistant")
    st.markdown("Ask any question about your finances, plans, or general advice. Powered by AI.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input area
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        # Simulate AI response (replace with real API call)
        response_placeholder = st.chat_message("assistant")
        response_placeholder.markdown("...")
        # Simulated response generation
        import time
        time.sleep(1)
        response_content = f"AI says: {prompt[::-1]}"  # Reverse string as dummy response
        response_placeholder.markdown(response_content)

        st.session_state.chat_messages.append({"role": "assistant", "content": response_content})

    st.markdown('</div>', unsafe_allow_html=True)


# --- Update main_router to include new enhanced chatbot ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return

    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "chatbot":
        page_chatbot()
    elif page == "financial_insights":
        page_financial_insights()
    elif page == "referral":
        page_referral_program()
    elif page == "education":
        page_educational_resources()
    elif page == "export":
        page_export_data()
    elif page == "achievements":
        page_achievements()
    elif page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "goals_manager":
        goals_manager()
    elif page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
import streamlit as st

# --- Dashboard KPIs & Financial Metrics ---
def page_dashboard_metrics():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("Dashboard: Key Financial Metrics")

    # Display cards in columns
    col1, col2, col3 = st.columns(3)

    # Example dummy metrics - replace with actual calculations
    total_savings = 150000.00
    monthly_expenses = 12000.00
    active_goals = len(st.session_state.auth_profile.get("goals", [])) if st.session_state.auth_profile else 0

    with col1:
        st.metric("Total Savings (ZAR)", f"{total_savings:,.2f}", delta="+5% from last month")
    with col2:
        st.metric("Monthly Expenses (ZAR)", f"{monthly_expenses:,.2f}", delta="-2% from last month")
    with col3:
        st.metric("Active Financial Goals", active_goals)

    st.markdown("</div>", unsafe_allow_html=True)

# --- User Input Validation Utility ---
def validate_positive_number(value, field_name):
    try:
        val = float(value)
        if val < 0:
            st.error(f"{field_name} cannot be negative.")
            return None
        return val
    except ValueError:
        st.error(f"{field_name} must be a valid number.")
        return None

# --- Loading Spinner Decorator (for slow functions) ---
from functools import wraps
import time

def loading_spinner(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with st.spinner("Processing..."):
            time.sleep(0.5)  # simulate delay, remove or tune as needed
            result = func(*args, **kwargs)
        return result
    return wrapper

# --- Example usage of loading_spinner decorator ---
@loading_spinner
def expensive_computation():
    # simulate complicated processing
    time.sleep(2)
    return "Done"

# --- Example button in any page ---
def example_expensive_action():
    if st.button("Run Expensive Computation"):
        result = expensive_computation()
        st.success(result)

# --- Update main_router with KPI dashboard and example ---
def main_router():
    if not st.session_state.get("consent_accepted", False):
        page_privacy_gate()
        return

    if st.session_state.get("auth_logged_in", False):
        sidebar_navigation()

    page = st.session_state.page

    if page == "dashboard_metrics":
        page_dashboard_metrics()
    elif page == "example_expensive_action":
        example_expensive_action()
    elif page == "chatbot":
        page_chatbot()
    elif page == "financial_insights":
        page_financial_insights()
    elif page == "referral":
        page_referral_program()
    elif page == "education":
        page_educational_resources()
    elif page == "export":
        page_export_data()
    elif page == "achievements":
        page_achievements()
    elif page == "monthly_report":
        page_monthly_report()
    elif page == "sentiment_insights":
        page_sentiment_insights()
    elif page == "bank_upload":
        page_bank_upload()
    elif page == "doc_upload":
        page_doc_upload()
    elif page == "reg_updates":
        display_regulatory_updates()
    elif page == "goals_manager":
        goals_manager()
    elif page == "auth_login":
        auth_page()
    elif page == "segment_hub":
        page_segment_hub()
    elif page == "module_form":
        st.info("Module form page coming soon...")
    elif page == "home":
        st.title(f"Welcome home, {st.session_state.auth_username}!")
    else:
        st.warning(f"Page '{page}' not found. Redirecting to Segment Hub.")
        st.session_state.page = "segment_hub"
        st.experimental_rerun()

if __name__ == "__main__":
    init_state()
    init_auth_state()
    main_router()
