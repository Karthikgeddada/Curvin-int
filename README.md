https://curvin-intelligence.streamlit.app/
# Corvin Intelligence — AI Market Intelligence Platform

A production-grade, multi-industry AI system that analyzes real-time financial and sector-based news using **FinBERT** for sentiment analysis and **OpenRouter (LLaMA 3.3 70B)** for analyst-level insights.

---

## Architecture

```
User Input (Industry + Article Count)
        ↓
  Query Expansion Engine  (5 variations per industry)
        ↓
  Google News RSS Scraper
        ↓
  Deduplication + Cleaning
        ↓
  FinBERT Sentiment Engine
        ↓
  Structured Dataset
        ↓
  ├── Dashboard  (Visual Analytics — Plotly)
  ├── LLM (OpenRouter) → Analyst Report
  └── Chat Module (RAG-lite)
        ↓
  Streamlit Multi-Page UI
```

## Industry Coverage (31 sectors)

Finance · Banking · Insurance · Healthcare · Pharmaceuticals · Biotechnology · Agriculture · Food Industry · Energy · Oil & Gas · Renewable Energy · Technology · Artificial Intelligence · Cybersecurity · Semiconductors · Aviation · Space Industry · Automotive · Electric Vehicles · Logistics · Retail · E-commerce · Real Estate · Construction · Telecommunications · Media · Entertainment · Sports Industry · Defense · Geopolitics · Cryptocurrency

## Stack

| Layer | Technology |
|---|---|
| Sentiment | ProsusAI/FinBERT (HuggingFace Transformers) |
| LLM | OpenRouter API — LLaMA 3.3 70B Instruct |
| News | Google News RSS (feedparser) |
| Visualisation | Plotly |
| UI | Streamlit (multi-page) |
| Rate Limiting | Sliding-window + key rotation |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the platform
streamlit run app.py
```

## Project Structure

```
ai-market-intelligence/
├── app.py                   # Main entry / home page
├── pipeline.py              # Orchestration (fetch → dedupe → sentiment)
├── fetch_news.py            # Google News RSS ingestion
├── sentiment_analysis.py    # FinBERT engine
├── ai_analyst.py            # OpenRouter LLM analyst report generator
├── chat_with_news.py        # RAG-lite chat module
├── groq_client.py           # Multi-key OpenRouter client with rotation
├── pages/
│   ├── 1_Dashboard.py       # Visual analytics dashboard
│   ├── 2_AI_Report.py       # LLM-generated analyst report
│   └── 3_Chat.py            # Conversational market intelligence
├── utils/
│   ├── rate_limiter.py      # Sliding-window limiter + key rotator
│   ├── query_builder.py     # Multi-query expansion for 31 industries
│   └── deduplicator.py      # URL + title deduplication
├── requirements.txt
└── README.md
```

## API Key Configuration

The platform supports **multi-key rotation** for OpenRouter. Set your `OPENROUTER_API_KEY` in a `.env` file in the project root. For production deployment, use `st.secrets` or environment variables.

## License

MIT
