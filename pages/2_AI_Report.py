import streamlit as st
import json
import os
from dotenv import load_dotenv
from ai_analyst import MarketAnalyst

load_dotenv(override=True)

st.set_page_config(page_title="AI Analyst Report", page_icon="📋", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #FAFAFA; color: #111827; }
    [data-testid="stSidebar"] { background-color: #F8FAFC; border-right:1px solid #E5E7EB; }
    .main .block-container { padding: 2rem 2.5rem; max-width: 1400px; }
    .stButton > button { background: linear-gradient(90deg,#3B82F6,#6366F1); color:white; border:none; border-radius:8px; padding:.6rem 1.5rem; font-weight:600; transition:all .2s ease; box-shadow:0 4px 6px -1px rgba(59,130,246,0.25); }
    .stButton > button:hover { transform:translateY(-2px); box-shadow:0 6px 10px -1px rgba(59,130,246,0.4); color: white; }
    .stButton > button:disabled { background: #F3F4F6; color:#9CA3AF; box-shadow:none; cursor:not-allowed; }
    h1 { color:#111827 !important; font-weight:800 !important; }
    h2, h3 { color:#1F2937 !important; font-weight:600 !important; }
    hr { border-color:#E5E7EB; }
    /* Card containers */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);
    }
    /* Alert overrides */
    .stSuccess { background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; color: #166534; }
    .stError { background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; color: #991B1B; }
    .stInfo { background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; color: #1E3A8A; }
    .stWarning { background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; color: #92400E; }
    div[data-testid="stExpander"] { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Intelligence Controls")
    st.markdown("---")

    has_data = "dashboard_data" in st.session_state and st.session_state.dashboard_data is not None

    if has_data:
        industry = st.session_state.get("selected_industry", "Finance")
        article_count = len(st.session_state.dashboard_data)
        st.success(f"✅ **{industry}** — {article_count} articles loaded")
    else:
        st.warning("No data loaded yet. Go to the **Dashboard** first.")

    st.markdown("---")
    raw_keys = ""

    generate_btn = st.button("⚡ Generate Analyst Report", disabled=not has_data)
    if st.button("🗑 Clear Report"):
        st.session_state.pop("current_report", None)

# ── Parse API Keys ────────────────────────────────────────────────────────────
# Load API keys from environment variables (.env for local) or st.secrets (Streamlit Cloud)
env_key = os.environ.get("OPENROUTER_API_KEY", "")
if not env_key:
    try:
        env_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except Exception:
        pass
OPENROUTER_API_KEYS = [env_key] if env_key else []

analyst_engine = MarketAnalyst(OPENROUTER_API_KEYS) if OPENROUTER_API_KEYS else None

# ── Main Report UI ────────────────────────────────────────────────────────────
st.title("📋 AI Institutional Analyst Report")
st.caption("Powered by OpenRouter · LLaMA 3.3 70B · Grounded in Live News Context")
st.markdown("---")

if has_data:
    df = st.session_state.dashboard_data
    industry = st.session_state.get("selected_industry", "Finance")
    articles = df[["title", "description"]].head(15).to_dict("records")

    if generate_btn:
        if not OPENROUTER_API_KEYS:
            st.error("⚠️ **OpenRouter API Key not found.** Please set `OPENROUTER_API_KEY` in your `.env` file in the project background.")
        else:
            with st.spinner(f"🧠 Synthesizing institutional intelligence for **{industry}**..."):
                report = analyst_engine.generate_sector_report(industry, articles)
                st.session_state.current_report = report

    if "current_report" in st.session_state:
        report = st.session_state.current_report

        if report.get("overall_sentiment") == "Error generating report":
            error_msg = report.get("key_drivers", ["Unknown error"])[0]
            st.error(f"❌ **API Error:** {error_msg}")
            st.info("💡 **Tip:** It looks like there is an issue with your OpenRouter API account (e.g., rate limit, invalid key, or organization restriction). Please check your OpenRouter dashboard.")
            st.stop()

        # ── SENTIMENT BANNER ─────────────────────────────────────────────────
        sentiment_raw = report.get("overall_sentiment", "N/A")
        # Color code the banner based on sentiment
        if "positive" in sentiment_raw.lower():
            banner_color = "#10B981"; icon_s = "📈"
        elif "negative" in sentiment_raw.lower():
            banner_color = "#EF4444"; icon_s = "📉"
        else:
            banner_color = "#6366F1"; icon_s = "➡️"

        st.markdown(f"""
        <div style="background:#FFFFFF;
            border-left: 6px solid {banner_color}; border: 1px solid #E5E7EB; border-left-width: 6px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            border-radius:16px; padding:1.5rem 2rem; margin-bottom:2rem;">
            <p style="color:#6B7280;font-size:0.85rem;text-transform:uppercase;font-weight:700;margin:0;letter-spacing:1px;">
                {icon_s} Overall Market Sentiment — {industry}
            </p>
            <h2 style="color:#111827;margin:0.4rem 0 0; font-size:1.8rem; font-weight:800;">{sentiment_raw}</h2>
        </div>
        """, unsafe_allow_html=True)

        # ── FOUR QUADRANT CARDS ──────────────────────────────────────────────
        col1, col2 = st.columns(2, gap="large")

        with col1:
            with st.container(border=True):
                st.markdown("### 🚀 Key Market Drivers")
                drivers = report.get("key_drivers", [])
                if drivers:
                    for d in drivers:
                        st.markdown(f"- {d}")
                else:
                    st.caption("No key drivers identified.")

            st.markdown("<br>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("### 💡 Sector Opportunities")
                opps = report.get("opportunities", [])
                if opps:
                    for o in opps:
                        st.success(o, icon="✅")
                else:
                    st.caption("No opportunities identified.")

        with col2:
            with st.container(border=True):
                st.markdown("### ⚠️ Critical Risks")
                risks = report.get("risks", [])
                if risks:
                    for r in risks:
                        st.error(r, icon="⚠️")
                else:
                    st.caption("No critical risks identified.")

            st.markdown("<br>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("### 👀 Entities to Watch")
                entities = report.get("companies_to_watch", [])
                if entities:
                    for e in entities:
                        st.info(e, icon="🏢")
                else:
                    st.caption("No specific entities flagged.")

        st.markdown("---")
        st.caption(
            "⚠️ This report is AI-generated from real-time news data. "
            "It is not financial advice. Always verify with primary sources."
        )

        with st.expander("🔍 View Raw JSON Report"):
            st.json(report)

    else:
        st.info("👆 Click **⚡ Generate Analyst Report** in the sidebar to produce your institutional intelligence briefing.", icon="📋")

else:
    st.warning("⚠️ No data available. Please navigate to the **Dashboard** page and fetch industry news first.")
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);
        border-radius:16px; padding:4rem 2rem; text-align:center; margin-top:2rem;">
        <div style="font-size:4rem; margin-bottom:1rem;">📋</div>
        <h2 style="color:#111827; margin:0 0 0.5rem; font-weight:700;">Analyst Report Engine</h2>
        <p style="color:#6B7280; font-size:1.1rem; max-width:500px; margin:0 auto;">
            Fetch market news first in the Dashboard, then return here to generate a full institutional-grade sector briefing.
        </p>
    </div>
    """, unsafe_allow_html=True)
