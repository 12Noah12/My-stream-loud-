import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# --- NAVIGATION OPTIONS ---
PAGES = {
    "home": "Home",
    "tax": "Tax Optimization",
    "investments": "Investments",
    "sme": "SME Dashboard",
    "premium": "Premium Modules"
}

# --- BACKGROUND STYLES ---
BG_STYLES = {
    "home": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
    "tax": "linear-gradient(135deg, #00c6ff 0%, #0072ff 100%)",
    "investments": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
    "sme": "linear-gradient(135deg, #485563 0%, #29323c 100%)",
    "premium": "linear-gradient(135deg, #f7971e 0%, #ffd200 100%)"
}

# --- FRIENDLY TEXT ---
SECTION_TEXT = {
    "home": "👋 Welcome to FinAI! Ask me anything below.",
    "tax": "💸 Optimize your taxes with smart strategies.",
    "investments": "📈 Grow your wealth with AI-guided investments.",
    "sme": "🏢 Manage your business efficiently with our SME tools.",
    "premium": "🌟 Unlock powerful premium features here."
}

# --- CUSTOM CSS ---
st.markdown("""
<style>
/* Reset padding */
.block-container {
    padding-top: 4rem;
}

/* Navbar */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  padding: 0.7rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1000;
}

/* Logo */
.navbar .logo {
  font-weight: 700;
  font-size: 1.2rem;
  color: #2563eb;
}

/* Nav links */
.nav-links {
  display: flex;
  gap: 1.5rem;
}
.nav-links a {
  font-weight: 600;
  color: #333;
  text-decoration: none;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  transition: background 0.2s;
}
.nav-links a:hover {
  background: #f0f0f0;
}

/* Menu dots */
.menu-dots {
  cursor: pointer;
  font-size: 22px;
  padding: 0.4rem 0.6rem;
  border-radius: 50%;
  transition: background 0.2s;
}
.menu-dots:hover {
  background: #eee;
}

/* Dropdown menu */
.dropdown {
  display: none;
  position: absolute;
  top: 60px;
  right: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 6px 15px rgba(0,0,0,0.1);
  overflow: hidden;
}
.dropdown a {
  display: block;
  padding: 0.8rem 1rem;
  color: #333;
  text-decoration: none;
}
.dropdown a:hover {
  background: #f9f9f9;
}

/* AI Search Bar */
.ai-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 70vh;
  flex-direction: column;
  text-align: center;
}

.ai-search-bar {
  font-weight: 700;
  font-size: 1.2rem;
  border: 2px solid #2563eb;
  border-radius: 12px;
  padding: 0.8rem 1.2rem;
  width: 60%;
  max-width: 600px;
  box-shadow: 0 0 12px rgba(37,99,235,0.3);
  transition: all 0.3s ease;
  animation: pulse 2s infinite;
}

.ai-search-bar:focus {
  outline: none;
  box-shadow: 0 0 20px rgba(37,99,235,0.6);
}

@keyframes pulse {
  0% { box-shadow: 0 0 10px rgba(37,99,235,0.5); }
  50% { box-shadow: 0 0 20px rgba(37,99,235,0.9); }
  100% { box-shadow: 0 0 10px rgba(37,99,235,0.5); }
}

/* Section box */
.section {
  text-align: center;
  padding: 3rem 2rem;
  border-radius: 12px;
  margin: 2rem auto;
  max-width: 900px;
  color: white;
  font-size: 1.1rem;
}
</style>

<!-- NAVBAR -->
<div class="navbar">
  <div class="logo">FinAI 💡</div>
  
  <div class="nav-links">
    <a href="?page=home">Home</a>
    <a href="?page=tax">Tax Optimization</a>
    <a href="?page=investments">Investments</a>
    <a href="?page=sme">SME Dashboard</a>
    <a href="?page=premium">Premium Modules</a>
  </div>
  
  <div class="menu-dots" onclick="toggleMenu()">⋮</div>
</div>

<!-- DROPDOWN -->
<div id="menu" class="dropdown">
  <a href="#">Login</a>
  <a href="#">Settings</a>
  <a href="#">Help</a>
</div>

<script>
function toggleMenu() {
  var menu = document.getElementById("menu");
  if (menu.style.display === "block") {
    menu.style.display = "none";
  } else {
    menu.style.display = "block";
  }
}
</script>
""", unsafe_allow_html=True)

# --- ROUTING ---
query_params = st.experimental_get_query_params()
page = query_params.get("page", ["home"])[0]

# --- BACKGROUND ---
bg_style = BG_STYLES.get(page, BG_STYLES["home"])
st.markdown(f"""
    <style>
    .stApp {{
        background: {bg_style};
        background-attachment: fixed;
        background-size: cover;
    }}
    </style>
""", unsafe_allow_html=True)

# --- PAGE CONTENT ---
if page == "home":
    st.markdown(
        "<div class='ai-wrapper'>"
        "<input class='ai-search-bar' placeholder='🔍 Ask AI anything...'>"
        "</div>", unsafe_allow_html=True
    )
    st.markdown(f"<div class='section'>{SECTION_TEXT[page]}</div>", unsafe_allow_html=True)

elif page == "tax":
    st.markdown(f"<div class='section'>{SECTION_TEXT[page]}</div>", unsafe_allow_html=True)
    st.subheader("Tax Calculator")
    income = st.number_input("Enter your income:", min_value=0, step=1000)
    expenses = st.number_input("Enter deductible expenses:", min_value=0, step=100)
    if income:
        taxable_income = max(0, income - expenses)
        st.write(f"**Taxable Income:** R{taxable_income:,.2f}")
        st.write("📊 (Here you could add your tax tables or API call.)")

elif page == "investments":
    st.markdown(f"<div class='section'>{SECTION_TEXT[page]}</div>", unsafe_allow_html=True)
    st.subheader("Investment Growth Simulator")
    principal = st.number_input("Initial Investment", min_value=0.0, step=100.0)
    rate = st.slider("Annual Growth Rate (%)", 1, 20, 5)
    years = st.slider("Years", 1, 40, 10)
    if principal:
        final_amount = principal * ((1 + rate/100) ** years)
        st.success(f"Projected Value: R{final_amount:,.2f}")

elif page == "sme":
    st.markdown(f"<div class='section'>{SECTION_TEXT[page]}</div>", unsafe_allow_html=True)
    st.subheader("SME Dashboard")
    st.write("📊 (Placeholder for SME tools: revenue, expenses, trends.)")

elif page == "premium":
    st.markdown(f"<div class='section'>{SECTION_TEXT[page]}</div>", unsafe_allow_html=True)
    st.subheader("Premium Modules")
    st.write("🌟 (Placeholder for exclusive premium features.)")
