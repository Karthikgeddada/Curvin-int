import streamlit as st
import json
import os
from dotenv import load_dotenv
from ai_analyst import MarketAnalyst

load_dotenv(override=True)

st.set_page_config(page_title="AI Analyst Report", page_icon="📋", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif; -webkit-font-smoothing: antialiased; }
    .stApp { background-color: #FFFFFF; color: #1d1d1f; }
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.78);
        -webkit-backdrop-filter: saturate(180%) blur(20px);
        backdrop-filter: saturate(180%) blur(20px);
        border-right: 1px solid #d2d2d7;
    }
    .main .block-container { padding: 2rem 2.5rem; max-width: 1400px; }
    .stButton > button { background:#0071e3; color:#ffffff; border:none; border-radius:980px; padding:.5rem 1.6rem; font-weight:600; font-size:1rem; transition:background .18s ease; box-shadow:none; }
    .stButton > button:hover { background:#0077ed; color:#ffffff; }
    .stButton > button:disabled { background: #f5f5f7; color:#86868b; box-shadow:none; cursor:not-allowed; }
    h1 { color:#1d1d1f !important; font-weight:700 !important; letter-spacing:-0.025em !important; }
    h2, h3 { color:#1d1d1f !important; font-weight:600 !important; letter-spacing:-0.02em !important; }
    hr { border-color:#d2d2d7; }
    /* Card containers — soft gray tiles */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        background: #f5f5f7; border: none; border-radius: 18px; padding: 0.25rem;
    }
    /* Alerts — soft, borderless, rounded */
    .stSuccess { background: #f0f7f0; border: none; border-radius: 18px; color: #1d1d1f; }
    .stError { background: #fbf0f0; border: none; border-radius: 18px; color: #1d1d1f; }
    .stInfo { background: #f5f5f7; border: none; border-radius: 18px; color: #1d1d1f; }
    .stWarning { background: #fbf7ee; border: none; border-radius: 18px; color: #1d1d1f; }
    div[data-testid="stExpander"] { background: #f5f5f7; border: none; border-radius: 18px; }
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
st.caption("Powered by OpenRouter · LLaMA 3.3 70B · Grounded in Full Article Text")
st.markdown("---")

if has_data:
    df = st.session_state.dashboard_data
    industry = st.session_state.get("selected_industry", "Finance")
    # Prefer the deep-read full article text when available (snippet otherwise)
    top = df.head(15)
    articles = [
        {
            "title": row["title"],
            "description": row["deep_text"] if row.get("has_full_text") else row["description"],
        }
        for _, row in top.iterrows()
    ]

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
            banner_color = "#86868b"; icon_s = "➡️"

        st.markdown(f"""
        <div style="background:#f5f5f7;
            border: none; border-radius: 18px;
            padding:1.75rem 2rem; margin-bottom:2rem;">
            <p style="color:#86868b;font-size:0.8rem;text-transform:uppercase;font-weight:600;margin:0;letter-spacing:0.08em;">
                {icon_s} Overall Market Sentiment — {industry}
            </p>
            <h2 style="color:#1d1d1f;margin:0.4rem 0 0; font-size:1.9rem; font-weight:700; letter-spacing:-0.02em;">{sentiment_raw}</h2>
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
    <div style="background:#f5f5f7; border-radius:18px; padding:4.5rem 2rem; text-align:center; margin-top:2rem;">
        <div style="font-size:4rem; margin-bottom:1rem;">📋</div>
        <h2 style="color:#1d1d1f; margin:0 0 0.5rem; font-weight:700; letter-spacing:-0.02em;">Analyst Report Engine</h2>
        <p style="color:#86868b; font-size:1.1rem; max-width:520px; margin:0 auto;">
            Fetch market news first in the Dashboard, then return here to generate a full institutional-grade sector briefing.
        </p>
    </div>
    """, unsafe_allow_html=True)
