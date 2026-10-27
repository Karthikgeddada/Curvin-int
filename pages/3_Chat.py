import streamlit as st
import os
from dotenv import load_dotenv
from chat_with_news import NewsChat

load_dotenv(override=True)

st.set_page_config(page_title="Chat with Market News", page_icon="💬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #FAFAFA; color: #111827; }
    [data-testid="stSidebar"] { background-color: #F8FAFC; border-right:1px solid #E5E7EB; }
    .main .block-container { padding: 2rem 2.5rem; max-width: 1400px; }
    .stButton > button { background: linear-gradient(90deg,#3B82F6,#6366F1); color:white; border:none; border-radius:8px; padding:.6rem 1.5rem; font-weight:600; transition:all .2s ease; box-shadow:0 4px 6px -1px rgba(59,130,246,0.25); }
    .stButton > button:hover { transform:translateY(-2px); box-shadow:0 6px 10px -1px rgba(59,130,246,0.4); color: white; }
    h1 { color:#111827 !important; font-weight:800 !important; }
    h2, h3 { color:#1F2937 !important; font-weight:600 !important; }
    hr { border-color:#E5E7EB; }
    /* Chat bubbles */
    [data-testid="chatAvatarIcon-user"] { background: linear-gradient(135deg,#3B82F6,#6366F1) !important; }
    [data-testid="chatAvatarIcon-assistant"] { background: linear-gradient(135deg,#10B981,#059669) !important; }
    [data-testid="stChatMessage"] { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
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
                    articles = df[['title', 'description']].head(20).to_dict('records')
                    response = chat_module.handle_query(prompt, articles)
                    st.markdown(response)
                
        # Add assistant message to state
        st.session_state.chat_history.append({"role": "assistant", "content": response})
else:
    st.warning("⚠️ No news context available. Please go to the **Dashboard** page and fetch data first.")
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);
        border-radius:16px; padding:4rem 2rem; text-align:center; margin-top:2rem;">
        <div style="font-size:4rem; margin-bottom:1rem;">💬</div>
        <h2 style="color:#111827; margin:0 0 0.5rem; font-weight:700;">Context-Aware Chat</h2>
        <p style="color:#6B7280; font-size:1.1rem; max-width:500px; margin:0 auto;">
            After fetching news data in the Dashboard, return here to
            ask questions grounded in real market intelligence — no hallucinations.
        </p>
    </div>
    """, unsafe_allow_html=True)
