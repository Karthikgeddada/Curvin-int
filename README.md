https://curvin-intelligence.streamlit.app/
# Curvin Intelligence — AI Market Intelligence Platform

A production-grade, multi-industry AI system that analyzes real-time financial and sector-based news using **FinBERT** for sentiment analysis and **OpenRouter (LLaMA 3.3 70B)** for analyst-level insights.

---

## Architecture

```
User Input (Industry + Article Count + Region)
        ↓
  Google News RSS Scraper (multi-query with dynamic suffixes)
        ↓
  Deduplication + Text Cleaning
        ↓
  FinBERT Sentiment Engine (batched inference)
        ↓
  Structured Dataset (title, source, sentiment, confidence)
        ↓
  ├── Dashboard  (Visual Analytics — Plotly charts)
  ├── LLM (OpenRouter) → Institutional Analyst Report (JSON)
  └── Chat Module (RAG-lite, grounded in live news context)
        ↓
  Streamlit Multi-Page UI
```

## Industry Coverage (31 sectors)

Finance · Banking · Insurance · Healthcare · Pharmaceuticals · Biotechnology · Agriculture · Food Industry · Energy · Oil & Gas · Renewable Energy · Technology · Artificial Intelligence · Cybersecurity · Semiconductors · Aviation · Space Industry · Automotive · Electric Vehicles · Logistics · Retail · E-commerce · Real Estate · Construction · Telecommunications · Media · Entertainment · Sports Industry · Defense · Geopolitics · Cryptocurrency

## Tech Stack

| Layer | Technology |
|---|---|
| Sentiment | Gemini API (default when a key is configured) or ProsusAI/FinBERT locally (batched inference) |
| LLM | OpenRouter API — LLaMA 3.3 70B Instruct |
| News | Google News RSS (feedparser + BeautifulSoup) |
| Visualisation | Plotly |
| UI | Streamlit (multi-page app) |
| Rate Limiting | Sliding-window limiter + multi-key rotation |

## Quick Start

### Prerequisites

- Python 3.10+
- An [OpenRouter](https://openrouter.ai/) API key (free tier available)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Karthikgeddada/Curvin-intelligence.git
cd Curvin-intelligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Edit .env and paste your OpenRouter API key

# 4. Run the platform
streamlit run app.py
```

## API Key Configuration

Create a `.env` file in the project root (see `.env.example` for a template):

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
GEMINI_API_KEY=your-key-here
```

The platform supports **multi-key rotation** for higher throughput. For production deployment on Streamlit Cloud, use `st.secrets` or environment variables.

**Sentiment engine selection**: when a real `GEMINI_API_KEY` is configured, sentiment runs on the Gemini API (`gemini-flash-lite-latest` by default) instead of downloading the ~500MB FinBERT model. Set `SENTIMENT_PROVIDER=finbert` to force the local FinBERT engine.

## Project Structure

```
Curvin-intelligence/
├── app.py                   # Main entry / home page
├── pipeline.py              # Orchestration (fetch → dedupe → sentiment)
├── fetch_news.py            # Google News RSS ingestion + text cleaning
├── sentiment_analysis.py    # FinBERT engine (batched inference)
├── ai_analyst.py            # OpenRouter LLM analyst report generator
├── chat_with_news.py        # RAG-lite chat module
├── openrouter_client.py     # Multi-key OpenRouter client with rotation + caching
├── sentiment_gemini.py      # Gemini sentiment analyzer (auto-dispatch with FinBERT fallback)
├── article_scraper.py       # Deep-read: resolves Google News redirects, scrapes full article text
├── news_store.py            # Postgres/Supabase persistence + history search (RAG history)
├── pages/
│   ├── 1_Dashboard.py       # Visual analytics dashboard
│   ├── 2_AI_Report.py       # LLM-generated analyst report
│   └── 3_Chat.py            # Conversational market intelligence
├── utils/
│   ├── __init__.py          # Package init
│   ├── rate_limiter.py      # Sliding-window limiter + key rotator
│   ├── deduplicator.py      # URL + title deduplication
│   └── query_builder.py      # Industry/region query construction
├── .streamlit/
│   └── config.toml          # Streamlit theme config
├── .devcontainer/
│   └── devcontainer.json    # VS Code Dev Container config
├── requirements.txt
├── .env.example             # API key template (safe to commit)
├── .env                     # Your actual API key (gitignored, do NOT commit)
├── .gitignore
└── README.md
```

## Key Features

- **Live Dashboard**: Real-time sentiment charts, confidence distributions, and raw intelligence feed across 31 industries
- **AI Analyst Report**: LLM-generated institutional reports with key drivers, risks, opportunities, and entities to watch (structured JSON)
- **Chat with News**: Context-aware RAG-lite chat grounded in live news — no hallucinations
- **Batched FinBERT Inference**: Articles processed in batches of 16 for faster throughput
- **Multi-Key Rotation**: OpenRouter client with sliding-window rate limiting and automatic key fallback
- **Multi-Region Support**: Fetch news from US, UK, India, Canada, Australia, or Global

## Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Curvin Intelligence - production ready"
git branch -M main
git remote add origin https://github.com/<your-username>/Curvin-intelligence.git
git push -u origin main
```

The .env file is gitignored, so your API key will NOT be pushed to GitHub.
The .env.example template IS included so others know what to set up.

### 2. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click New app and connect your GitHub account
3. Select your repository: Curvin-intelligence
4. Set the main file path to app.py
5. Click Advanced Settings, then Secrets, and paste:
   OPENROUTER_API_KEY = "sk-or-v1-your-new-key-here"
6. Click Deploy. The app goes live at https://your-app-name.streamlit.app

The app checks st.secrets (Streamlit Cloud) first, then falls back to .env (local).
FinBERT model weights (~500MB) download automatically on first run and are cached.

### 3. Local Development

```bash
cp .env.example .env
# Edit .env and paste your OpenRouter API key
streamlit run app.py
```

The app opens at http://localhost:8501

## How It Works

1. **News Ingestion**: Google News RSS feeds are fetched using dynamic query suffixes ("news", "market updates", "analysis", etc.) with a 14-day recency filter. Articles are deduplicated by URL and title.
2. **Sentiment Analysis**: FinBERT (ProsusAI/finbert) classifies each article as Positive, Negative, or Neutral with a confidence score. Batched inference processes 16 articles per forward pass.
3. **AI Analyst Report**: The top 15 articles are sent to LLaMA 3.3 70B via OpenRouter with a structured JSON prompt, producing a report with overall sentiment, key drivers, risks, opportunities, and companies to watch.
4. **Chat Module**: Users can ask questions about the fetched news. The LLM is instructed to answer only from the provided article context — if it can't derive an answer, it says so explicitly.

## Disclaimer

This platform is for informational purposes only. AI-generated reports are not financial advice. Always verify with primary sources.

## License

MIT
