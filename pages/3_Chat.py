import streamlit as st
import os
from dotenv import load_dotenv
from chat_with_news import NewsChat

load_dotenv(override=True)

st.set_page_config(page_title="Chat with Market News", page_icon="💬", layout="wide")

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
    h1 { color:#1d1d1f !important; font-weight:700 !important; letter-spacing:-0.025em !important; }
    h2, h3 { color:#1d1d1f !important; font-weight:600 !important; letter-spacing:-0.02em !important; }
    hr { border-color:#d2d2d7; }
    /* Chat — Apple Messages look */
    [data-testid="chatAvatarIcon-user"] { background: #0071e3 !important; }
    [data-testid="chatAvatarIcon-assistant"] { background: #1d1d1f !important; }
    [data-testid="stChatMessage"] { background-color: #f5f5f7; border: none; border-radius: 18px; padding: 1.25rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Configuration ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Intelligence Controls")
    
    st.markdown("---")
    # Load API keys from environment variables (.env for local) or st.secrets (Streamlit Cloud)
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not env_key:
        try:
            env_key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            pass
    OPENROUTER_API_KEYS = [env_key] if env_key else []
    
    clear_chat = st.button("🗑 Clear Chat History")

# ── Chat Logic Initialization ────────────────────────────────────────────────
if "chat_history" not in st.session_state or clear_chat:
    st.session_state.chat_history = []

chat_module = NewsChat(OPENROUTER_API_KEYS) if OPENROUTER_API_KEYS else None

# ── Main Chat UI ─────────────────────────────────────────────────────────────
st.title("💬 Chat with News Intelligence")

if "dashboard_data" in st.session_state:
    df = st.session_state.dashboard_data
    selected_industry = st.session_state.get('selected_industry', 'Finance')
    
    st.info(f"💡 You are currently chatting with the AI about recent news in the **{selected_industry}** sector ({len(df)} articles ingested).")
    
    # ── RENDER CHAT HISTORY ──────────────────────────────────────────────────
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # ── INPUT LOGIC ─────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask a question about the current market data..."):
        # Add user message to state
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Generate AI response
        with st.chat_message("assistant"):
            if not OPENROUTER_API_KEYS:
                response = "⚠️ **OpenRouter API Key not found.** Please set `OPENROUTER_API_KEY` in your `.env` file in the project background."
                st.markdown(response)
            else:
                with st.spinner("🧠 Querying intelligence context..."):
                    # Pass the top 20 articles as the grounded context
                    # (full deep-read text when available, snippet otherwise)
                    articles = [
                        {
                            "title": row["title"],
                            "description": row["deep_text"] if row.get("has_full_text") else row["description"],
                        }
                        for _, row in df.head(20).iterrows()
                    ]
                    response = chat_module.handle_query(prompt, articles)
                    st.markdown(response)
                
        # Add assistant message to state
        st.session_state.chat_history.append({"role": "assistant", "content": response})
else:
    st.warning("⚠️ No news context available. Please go to the **Dashboard** page and fetch data first.")
    st.markdown("""
    <div style="background:#f5f5f7; border-radius:18px; padding:4.5rem 2rem; text-align:center; margin-top:2rem;">
        <div style="font-size:4rem; margin-bottom:1rem;">💬</div>
        <h2 style="color:#1d1d1f; margin:0 0 0.5rem; font-weight:700; letter-spacing:-0.02em;">Context-Aware Chat</h2>
        <p style="color:#86868b; font-size:1.1rem; max-width:520px; margin:0 auto;">
            After fetching news data in the Dashboard, return here to
            ask questions grounded in real market intelligence — no hallucinations.
        </p>
    </div>
    """, unsafe_allow_html=True)
