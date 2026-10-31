import os
import json
import logging
import pandas as pd

logger = logging.getLogger("sentiment_gemini")

VALID_LABELS = {"positive", "negative", "neutral"}
PLACEHOLDER_HINTS = ("your", "paste", "here", "placeholder", "xxx")


def _resolve_key_and_model():
    """Resolves GEMINI_API_KEY (Streamlit secrets → env) and GEMINI_MODEL (env)."""
    key = None
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass  # Not running inside Streamlit (e.g. FastAPI on Render) — fall back to env
    if not key:
        key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    return key, model


def _is_placeholder(key) -> bool:
    """True when the key is missing or still a template placeholder value."""
    if not key:
        return True
    k = key.strip().lower()
    return (not k) or any(hint in k for hint in PLACEHOLDER_HINTS)


def gemini_available() -> bool:
    """True when a real (non-placeholder) Gemini API key is configured."""
    key, _ = _resolve_key_and_model()
    return not _is_placeholder(key)


class GeminiSentimentAnalyzer:
    """
    Gemini-based sentiment engine — lightweight, API-only alternative to FinBERT.
    Same output contract as the FinBERT engine: a 'sentiment' label
    (Positive/Negative/Neutral) plus a 'confidence' score per article.
    Articles are scored in batches (one Gemini call per batch) as strict JSON.
    """

    BATCH_SIZE = 10
    MAX_CHARS = 4000  # deep-read articles are longer; Gemini handles it easily

    SYSTEM_PROMPT = (
        "You are a financial-news sentiment classifier. For each numbered article, "
        "classify the overall sentiment strictly as 'positive', 'negative', or 'neutral' "
        "and assign a confidence between 0 and 1. Judge each article independently. "
        "Respond ONLY with a JSON array — no markdown, no commentary — where each "
        "element has the shape: "
        '{"index": <article number>, "sentiment": "positive|negative|neutral", '
        '"confidence": <number between 0 and 1>}.'
    )

    def __init__(self, api_key=None, model=None):
        from google import genai  # lazy import keeps deployments light

        resolved_key, resolved_model = _resolve_key_and_model()
        self.api_key = api_key or resolved_key
        self.model = model or resolved_model
        if not self.api_key or _is_placeholder(self.api_key):
            raise ValueError(
                "GEMINI_API_KEY not configured. Set it in Streamlit Secrets, "
                "the .env file, or environment variables."
            )
        self.client = genai.Client(api_key=self.api_key)

    # ── Parsing helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _extract_json(raw: str) -> str:
        """Strips markdown fences and any text around the JSON array."""
        t = (raw or "").strip()
        if t.startswith("```"):
            t = "\n".join(l for l in t.splitlines() if not l.strip().startswith("```"))
        start, end = t.find("["), t.rfind("]")
        if start != -1 and end > start:
            t = t[start:end + 1]
        return t

    @classmethod
    def _parse_response(cls, raw: str, expected: int) -> list:
        """
        Parses the model's JSON into per-article dicts.
        Any article the model skipped or mangled falls back to Neutral / 0.0.
        """
        results = [{"sentiment": "Neutral", "confidence": 0.0} for _ in range(expected)]
        try:
            data = json.loads(cls._extract_json(raw))
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Gemini returned unparseable JSON: {e}")
            return results
        if not isinstance(data, list):
            logger.warning("Gemini JSON was not a list; defaulting batch to Neutral.")
            return results
        for item in data:
            try:
                idx = int(item.get("index", item.get("i", 0))) - 1
                if not 0 <= idx < expected:
                    continue
                label = str(item.get("sentiment", item.get("s", "neutral"))).strip().lower()
                conf = float(item.get("confidence", item.get("c", 0.0)))
                if label not in VALID_LABELS:
                    label = "neutral"
                results[idx] = {
                    "sentiment": label.title(),
                    "confidence": round(min(1.0, max(0.0, conf)), 4),
                }
            except (AttributeError, TypeError, ValueError):
                continue
        return results

    # ── Inference ──────────────────────────────────────────────────────────────
    def _score_batch(self, texts: list) -> list:
        numbered = "\n\n".join(
            f"[{i + 1}] {str(t)[:self.MAX_CHARS]}" for i, t in enumerate(texts)
        )
        prompt = (
            f"Classify the sentiment of each of these {len(texts)} financial-news "
            f"articles.\n\n{numbered}"
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "system_instruction": self.SYSTEM_PROMPT,
                "temperature": 0.0,
                "max_output_tokens": 4096,
                "response_mime_type": "application/json",
            },
        )
        return self._parse_response(response.text or "", len(texts))

    def analyze(self, texts: list) -> pd.DataFrame:
        """Scores articles in batches; failed batches fall back to Neutral / 0.0."""
        if not texts:
            return pd.DataFrame(columns=["sentiment", "confidence"])
        str_texts = [str(t) for t in texts]
        results = []
        for i in range(0, len(str_texts), self.BATCH_SIZE):
            batch = str_texts[i : i + self.BATCH_SIZE]
            try:
                results.extend(self._score_batch(batch))
            except Exception as e:
                logger.warning(
                    f"Gemini batch {i // self.BATCH_SIZE} failed ({e}); "
                    "defaulting to Neutral."
                )
                results.extend([{"sentiment": "Neutral", "confidence": 0.0}] * len(batch))
        return pd.DataFrame(results)


def apply_gemini_sentiment_to_news(news_df: pd.DataFrame) -> pd.DataFrame:
    """Drop-in replacement for apply_sentiment_to_news, powered by the Gemini API."""
    analyzer = GeminiSentimentAnalyzer()
    sentiment_df = analyzer.analyze(news_df["full_text"].tolist())
    return pd.concat([news_df.reset_index(drop=True), sentiment_df], axis=1)
