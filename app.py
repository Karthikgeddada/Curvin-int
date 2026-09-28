import streamlit as st

# ── Page Config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Curvin Intelligence | Market AI Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS (Bloomberg-inspired dark theme) ────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Light background */
    .stApp { background-color: #FAFAFA; color: #111827; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E5E7EB;
    }

    /* Main content */
    .main .block-container { padding: 2rem 2.5rem; max-width: 1400px; }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 1.25rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stMetricValue"] { color: #111827; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #6B7280; font-weight: 500; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #3B82F6, #6366F1);
        color: white; border: none; border-radius: 8px;
        padding: 0.6rem 1.5rem; font-weight: 600; font-size: 0.9rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.25);
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 10px -1px rgba(59, 130, 246, 0.4); color: white; }

    /* Selectbox and number input */
    .stSelectbox > div > div, .stNumberInput > div > div {
        background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 8px; color: #111827;
    }

    /* Alerts */
    .stAlert { border-radius: 12px; }
    
    /* Headlines */
    h1 { color: #111827 !important; font-weight: 800 !important; }
    h2, h3 { color: #1F2937 !important; font-weight: 600 !important; }
    
    /* Spinner text */
    .stSpinner { color: #3B82F6; }

    /* Sidebar title */
    .sidebar-title {
        font-size: 1.5rem; font-weight: 700;
        background: linear-gradient(90deg, #3B82F6, #6366F1);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .sidebar-subtitle { color: #6B7280; font-size: 0.78rem; margin-bottom: 1.5rem; font-weight: 500; }

    /* Divider */
    hr { border-color: #E5E7EB; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: #F3F4F6; border-radius: 8px; gap: 4px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: #6B7280; border-radius: 6px; padding: 0.4rem 1rem; font-weight: 500; }
    .stTabs [aria-selected="true"] { background: #FFFFFF; color: #3B82F6 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }

    /* Dataframe */
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid #E5E7EB; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🧠 Corvin Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">AI-Powered Market Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Navigation")
    st.page_link("app.py",             label="🏠  Home", icon=None)
    st.page_link("pages/1_Dashboard.py", label="📊  Dashboard")
    st.page_link("pages/2_AI_Report.py", label="📋  AI Analyst Report")
    st.page_link("pages/3_Chat.py",      label="💬  Chat with News")
    st.markdown("---")
    st.markdown(
        '<span style="color:#475569;font-size:0.75rem;">Powered by FinBERT · OpenRouter LLaMA 3.3 70B<br>Data: Google News RSS</span>',
        unsafe_allow_html=True,
    )

# ── Home / Hero Section ───────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 3rem 1rem 2rem;">
    <h1 style="font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #3B82F6, #6366F1, #8B5CF6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">
        Corvin Intelligence
    </h1>
    <p style="color:#4B5563; font-size: 1.15rem; max-width: 600px; margin: 0 auto 2rem;">
        Institutional-grade market intelligence powered by FinBERT sentiment analysis 
        and OpenRouter LLaMA 3.3 70B. Monitor 30+ industries in real time.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Feature Cards ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="background: #FFFFFF; border:1px solid #E5E7EB; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-radius:16px; padding:1.5rem; height:180px;">
        <div style="font-size:2rem">📊</div>
        <h3 style="color:#111827; margin:0.5rem 0 0.25rem;">Live Dashboard</h3>
        <p style="color:#6B7280; font-size:0.85rem;margin:0;">Real-time sentiment charts, trend analysis, 
        and sector heatmaps across all industries.</p>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="background: #FFFFFF; border:1px solid #E5E7EB; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-radius:16px; padding:1.5rem; height:180px;">
        <div style="font-size:2rem">🤖</div>
        <h3 style="color:#111827; margin:0.5rem 0 0.25rem;">AI Analyst Report</h3>
        <p style="color:#6B7280; font-size:0.85rem;margin:0;">LLM-generated institutional reports with 
        risk, opportunity, and market driver analysis.</p>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="background: #FFFFFF; border:1px solid #E5E7EB; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-radius:16px; padding:1.5rem; height:180px;">
        <div style="font-size:2rem">💬</div>
        <h3 style="color:#111827; margin:0.5rem 0 0.25rem;">Chat with News</h3>
        <p style="color:#6B7280; font-size:0.85rem;margin:0;">Context-aware RAG-lite chat grounded in 
        live news — no hallucinations, pure market intelligence.</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 **Select a page from the sidebar** to begin your market intelligence session.", icon="🚀")
