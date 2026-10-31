import os
import pandas as pd
import streamlit as st
import logging

logger = logging.getLogger("sentiment_analysis")

# ── Module-level cached model loader ──────────────────────────────────────────
# @st.cache_resource ensures the model is loaded only ONCE across all sessions,
# preventing repeated 500MB+ downloads and ensuring fast inference.
@st.cache_resource(show_spinner="⚙️ Loading FinBERT model (first run only)...")
def _load_finbert():
    """Loads and caches ProsusAI/finbert tokenizer and model weights."""
    # Lazy import: torch/transformers stay out of the process entirely when the
    # Gemini provider is active (light deployments skip the ~500MB model).
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    model_name = "ProsusAI/finbert"
    logger.info(f"Loading FinBERT from HuggingFace: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()  # Set to inference mode
    return tokenizer, model


class SentimentAnalyzer:
    """
    Enterprise-grade FinBERT sentiment engine.
    Processes financial text with 512-token truncation and returns
    sentiment label + confidence score per article.
    Uses batched inference for improved throughput on large article sets.
    """

    # FinBERT label mapping: 0 → Positive, 1 → Negative, 2 → Neutral
    LABELS = {0: "Positive", 1: "Negative", 2: "Neutral"}
    MAX_TOKENS = 512
    BATCH_SIZE = 16

    def __init__(self):
        self.tokenizer, self.model = _load_finbert()

    def _predict_batch(self, texts: list[str]) -> list[dict]:
        """Runs a batched inference pass and returns label + confidence per text."""
        # Truncate input texts to a safe char cap before tokenization
        truncated = [str(t)[:2000] for t in texts]

        inputs = self.tokenizer(
            truncated,
            return_tensors="pt",
            truncation=True,
            max_length=self.MAX_TOKENS,
            padding=True,
        )
        # Lazy import: only needed when the FinBERT engine actually runs
        import torch

        with torch.no_grad():
            logits = self.model(**inputs).logits
            scores = torch.softmax(logits, dim=1)

        results = []
        for i in range(len(truncated)):
            label_id = int(torch.argmax(scores[i]).item())
            results.append({
                "sentiment": self.LABELS[label_id],
                "confidence": round(float(scores[i][label_id].item()), 4),
            })
        return results

    def analyze(self, texts: list) -> pd.DataFrame:
        """
        Processes a list of article strings through FinBERT in batches.
        Returns a DataFrame with 'sentiment' and 'confidence' columns.
        """
        if not texts:
            return pd.DataFrame(columns=["sentiment", "confidence"])

        results = []
        str_texts = [str(t) for t in texts]

        for i in range(0, len(str_texts), self.BATCH_SIZE):
            batch = str_texts[i : i + self.BATCH_SIZE]
            try:
                results.extend(self._predict_batch(batch))
            except Exception as e:
                logger.warning(f"Batch prediction failed (batch {i//self.BATCH_SIZE}): {e}")
                results.extend([{"sentiment": "Neutral", "confidence": 0.0}] * len(batch))

        return pd.DataFrame(results)


def resolve_sentiment_provider() -> str:
    """
    Picks the sentiment engine:
    - SENTIMENT_PROVIDER env var wins if set to 'gemini' or 'finbert'
    - Otherwise: Gemini when a real GEMINI_API_KEY is configured, else FinBERT
    """
    explicit = os.getenv("SENTIMENT_PROVIDER", "").strip().lower()
    if explicit in ("gemini", "finbert"):
        return explicit
    try:
        from sentiment_gemini import gemini_available
        if gemini_available():
            return "gemini"
    except Exception:
        pass
    return "finbert"


def apply_sentiment_to_news(news_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches the news DataFrame with sentiment scores.
    Provider: Gemini API (LLM) when configured, FinBERT (local) otherwise.
    Uses the 'full_text' column (title + description) for analysis.
    """
    if resolve_sentiment_provider() == "gemini":
        from sentiment_gemini import apply_gemini_sentiment_to_news  # lazy
        return apply_gemini_sentiment_to_news(news_df)

    analyzer = SentimentAnalyzer()
    sentiment_df = analyzer.analyze(news_df["full_text"].tolist())
    return pd.concat([news_df.reset_index(drop=True), sentiment_df], axis=1)
