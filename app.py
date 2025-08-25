import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinAI", page_icon="💡", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
/* Reset default padding */
.block-container {
    padding-top: 2rem;
}

/* Navbar */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: #ffffffcc;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 0.7rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1000;
}

/* Logo */
.navbar img {
  height: 36px;
  border-radius: 6px;
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

/* Dropdown for dots */
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

/* AI Search Bar Center */
.ai-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 75vh;
  text-align: center;
  flex-direction: column;
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

/* Section styling */
.section {
  text-align: center;
  padding: 4rem 2rem;
  border-radius: 12px;
  margin: 2rem auto;
  max-width: 900px;
  color: white;
  font-size: 1.1rem;
}
</style>

<div class="navbar">
  <img src="https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg" alt="Logo">
  
  <div class="nav-links">
    <a href="?page=home">Home</a>
    <a href="?page=tax">Tax Optimization</a>
    <a href="?page=investments">Investments</a>
    <a href="?page=sme">SME Dashboard</a>
    <a href="?page=premium">Premium Modules</a>
  </div>
  
  <div class="menu-dots" onclick="toggleMenu()">⋮</div>
</div>

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

# --- BACKGROUND COLORS ---
bg_colors = {
    "home": "#2563eb",          # Blue
    "tax": "#16a34a",           # Green
    "investments": "#9333ea",   # Purple
    "sme": "#ea580c",           # Orange
    "premium": "#b91c1c"        # Red
}

# --- QUERY PARAMS ---
query_params = st.experimental_get_query_params()
page = query_params.get("page", ["home"])[0]

# --- FRIENDLY SECTION TEXT ---
sections = {
    "home": "👋 Welcome to FinAI! Start your journey by asking me anything.",
    "tax": "💸 Smart tax strategies tailored for you. Let’s optimize together.",
    "investments": "📈 Plan, project and grow your investments with confidence.",
    "sme": "🏢 Your SME dashboard – insights to run your business smoothly.",
    "premium": "🌟 Premium modules – unlock exclusive financial tools."
}

# --- BACKGROUND CHANGE ---
color = bg_colors.get(page, "#2563eb")
st.markdown(
    f"""
    <style>
    .section {{
        background: {color};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- MAIN CONTENT ---
st.markdown(f"<div class='ai-wrapper'><input class='ai-search-bar' placeholder='🔍 Ask AI...'></div>", unsafe_allow_html=True)

st.markdown(f"<div class='section'>{sections[page]}</div>", unsafe_allow_html=True)
