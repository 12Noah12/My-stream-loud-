import streamlit as st
import openai
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AI Knowledge Hub",
    page_icon="🤖",
    layout="wide"
)

# ============================================
# CUSTOM CSS
# ============================================

st.markdown("""
    <style>
    .big-search-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 50px;
    }
    .big-search-bar input {
        font-size: 20px !important;
        padding: 15px !important;
        border-radius: 15px !important;
        border: 2px solid #4CAF50 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        width: 80% !important;
    }
    .stButton>button {
        border-radius: 12px;
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# HELPER FUNCTIONS
# ============================================

def ai_response(query: str) -> str:
    """Generate AI response for a query."""
    if not query.strip():
        return "Please enter a valid query."
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query}],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# ============================================
# FRONT PAGE - AI SEARCH BAR
# ============================================

st.title("🤖 AI Knowledge Hub")
st.subheader("Your personal assistant for research, insights, and data exploration")

with st.container():
    st.markdown("<div class='big-search-container'>", unsafe_allow_html=True)
    query = st.text_input("", placeholder="Ask me anything...", key="main_search", help="Type your question for the AI here.")
    st.markdown("</div>", unsafe_allow_html=True)

    search_button = st.button("🔍 Search with AI")

if search_button and query:
    with st.spinner("Thinking..."):
        answer = ai_response(query)
    st.success("AI Response:")
    st.write(answer)

# ============================================
# SIDEBAR NAVIGATION
# ============================================

st.sidebar.title("📌 Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Dashboard", "Charts", "Upload & Analyze", "Settings"],
    help="Select a section to explore."
)

# ============================================
# DASHBOARD PAGE
# ============================================

if page == "Dashboard":
    st.header("📊 Dashboard Overview")
    st.info("This section shows quick statistics and AI insights.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Users Online", 1245, help="Current active users.")
    with col2:
        st.metric("Data Processed", "58 GB", help="Total data analyzed this week.")
    with col3:
        st.metric("AI Requests", 8732, help="Total AI queries processed.")

    st.subheader("📈 Weekly Activity")
    data = pd.DataFrame({
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Requests": [1200, 1400, 1800, 1600, 2000, 2200, 2500]
    })
    st.line_chart(data.set_index("Day"), use_container_width=True)

# ============================================
# CHARTS PAGE
# ============================================

elif page == "Charts":
    st.header("📊 Custom Charts")
    st.info("Visualize your data with dynamic charts.")

    chart_type = st.selectbox(
        "Select chart type",
        ["Line", "Bar", "Scatter"],
        help="Choose which type of chart to generate."
    )

    num_points = st.slider("Number of data points", 10, 100, 50, help="Adjust how many points are displayed.")

    x = np.arange(num_points)
    y = np.random.randint(10, 100, num_points)

    fig, ax = plt.subplots()
    if chart_type == "Line":
        ax.plot(x, y, marker="o")
    elif chart_type == "Bar":
        ax.bar(x, y)
    elif chart_type == "Scatter":
        ax.scatter(x, y)
    st.pyplot(fig)

# ============================================
# UPLOAD & ANALYZE PAGE
# ============================================

elif page == "Upload & Analyze":
    st.header("📂 Upload & Analyze Data")
    st.info("Upload your CSV/Excel file and let AI analyze it.")

    uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx"], help="Upload CSV or Excel data for analysis.")

    if uploaded_file:
        try:
            if uploaded_file.name.endswith("csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.write("### Preview of Uploaded Data:")
            st.dataframe(df.head())

            st.subheader("🔎 Quick Stats")
            st.write(df.describe())

            st.subheader("📊 Column Selector")
            column = st.selectbox("Choose column to analyze", df.columns, help="Pick a column for deeper analysis.")
            st.bar_chart(df[column].value_counts())

        except Exception as e:
            st.error(f"Error reading file: {e}")

# ============================================
# SETTINGS PAGE
# ============================================

elif page == "Settings":
    st.header("⚙️ Settings")
    st.info("Manage your preferences and API keys.")

    openai_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key to enable AI features.")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        st.success("API Key set successfully!")

    theme = st.selectbox("Theme", ["Light", "Dark"], help="Choose between light and dark mode.")
    notifications = st.checkbox("Enable Notifications", help="Turn on/off system notifications.")

    st.write("---")
    st.write("Last updated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
