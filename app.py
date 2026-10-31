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
    /* Apple-inspired: SF system font stack, antialiased */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
    }

    /* Canvas */
    .stApp { background-color: #FFFFFF; color: #1d1d1f; }

    /* Sidebar — frosted glass */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.78);
        -webkit-backdrop-filter: saturate(180%) blur(20px);
        backdrop-filter: saturate(180%) blur(20px);
        border-right: 1px solid #d2d2d7;
    }

    /* Main content */
    .main .block-container { padding: 2rem 2.5rem; max-width: 1400px; }
    
    /* Metric tiles — soft gray, borderless */
    [data-testid="stMetric"] {
        background: #f5f5f7;
        border: none;
        border-radius: 18px;
        padding: 1.5rem 1.25rem !important;
    }
    [data-testid="stMetricValue"] { color: #1d1d1f; font-weight: 600; letter-spacing: -0.02em; }
    [data-testid="stMetricLabel"] { color: #6e6e73; font-weight: 500; }

    /* Buttons — Apple pill */
    .stButton > button {
        background: #0071e3; color: #ffffff; border: none; border-radius: 980px;
        padding: 0.5rem 1.6rem; font-weight: 600; font-size: 1rem;
        transition: background 0.18s ease; box-shadow: none;
    }
    .stButton > button:hover { background: #0077ed; color: #ffffff; }

    /* Inputs */
    .stSelectbox > div > div, .stNumberInput > div > div {
        background-color: #f5f5f7; border: 1px solid #d2d2d7; border-radius: 12px; color: #1d1d1f;
    }

    /* Alerts */
    .stAlert { border-radius: 18px; }
    
    /* Headlines — large, tight Apple tracking */
    h1 { color: #1d1d1f !important; font-weight: 700 !important; letter-spacing: -0.025em !important; }
    h2, h3 { color: #1d1d1f !important; font-weight: 600 !important; letter-spacing: -0.02em !important; }
    p, div, span, li, label { color: #1d1d1f; }
    
    /* Spinner */
    .stSpinner { color: #0071e3; }

    /* Sidebar title */
    .sidebar-title {
        font-size: 1.4rem; font-weight: 700; color: #1d1d1f;
        letter-spacing: -0.02em; margin-bottom: 0.25rem;
    }
    .sidebar-subtitle { color: #86868b; font-size: 0.8rem; margin-bottom: 1.5rem; font-weight: 500; }

    /* Divider */
    hr { border-color: #d2d2d7; }

    /* Tabs — segmented control */
    .stTabs [data-baseweb="tab-list"] { background-color: #f5f5f7; border-radius: 12px; gap: 4px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: #6e6e73; border-radius: 9px; padding: 0.4rem 1rem; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: #FFFFFF; color: #1d1d1f !important; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

    /* Dataframe */
    [data-testid="stDataFrame"] { border-radius: 18px; overflow: hidden; border: 1px solid #e8e8ed; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🧠 Curvin Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">AI-Powered Market Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Navigation")
    st.page_link("app.py",             label="🏠  Home", icon=None)
    st.page_link("pages/1_Dashboard.py", label="📊  Dashboard")
    st.page_link("pages/2_AI_Report.py", label="📋  AI Analyst Report")
    st.page_link("pages/3_Chat.py",      label="💬  Chat with News")
    st.markdown("---")
    st.markdown(
        '<span style="color:#86868b;font-size:0.75rem;">Powered by FinBERT · OpenRouter LLaMA 3.3 70B<br>Data: Google News RSS</span>',
        unsafe_allow_html=True,
    )

# ── Home / Hero Section ───────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 3rem 1rem 2rem;">
    <h1 style="font-size: 3.5rem; font-weight: 700; color: #1d1d1f; letter-spacing: -0.03em; margin-bottom: 0.6rem;">
        Curvin Intelligence
    </h1>
    <p style="color:#86868b; font-size: 1.15rem; max-width: 620px; margin: 0 auto 2.5rem;">
        Institutional-grade market intelligence powered by FinBERT sentiment analysis 
        and OpenRouter LLaMA 3.3 70B. Monitor 30+ industries in real time.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Feature Cards ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="background: #f5f5f7; border-radius: 18px; padding: 2rem 1.5rem; height: 210px;">
        <div style="font-size:2rem">📊</div>
        <h3 style="color:#1d1d1f; margin:0.5rem 0 0.25rem; letter-spacing:-0.02em;">Live Dashboard</h3>
        <p style="color:#6e6e73; font-size:0.95rem;margin:0;">Real-time sentiment charts, trend analysis, 
        and sector heatmaps across all industries.</p>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="background: #f5f5f7; border-radius: 18px; padding: 2rem 1.5rem; height: 210px;">
        <div style="font-size:2rem">🤖</div>
        <h3 style="color:#1d1d1f; margin:0.5rem 0 0.25rem; letter-spacing:-0.02em;">AI Analyst Report</h3>
        <p style="color:#6e6e73; font-size:0.95rem;margin:0;">LLM-generated institutional reports with 
        risk, opportunity, and market driver analysis.</p>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="background: #f5f5f7; border-radius: 18px; padding: 2rem 1.5rem; height: 210px;">
        <div style="font-size:2rem">💬</div>
        <h3 style="color:#1d1d1f; margin:0.5rem 0 0.25rem; letter-spacing:-0.02em;">Chat with News</h3>
        <p style="color:#6e6e73; font-size:0.95rem;margin:0;">Context-aware RAG-lite chat grounded in 
        live news — no hallucinations, pure market intelligence.</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 **Select a page from the sidebar** to begin your market intelligence session.", icon="🚀")
