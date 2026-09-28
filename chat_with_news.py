from groq_client import MultiKeyOpenRouterClient
import streamlit as st

class NewsChat:
    """Uses OpenRouter LLaMA 3.3 70B for RAG-lite chat with local news context."""
    def __init__(self, api_keys: list[str]):
        self.client = MultiKeyOpenRouterClient(api_keys)

    def handle_query(self, query: str, articles: list[dict], history: list[dict] = None) -> str:
        """Processes a chat query with grounded article context."""
        context = "\n".join([f"Title: {a['title']}\nSummary: {a['description']}" for a in articles[:15]])
        
        # In a real RAG system, we'd use vector search. 
        # Here, top 15 articles provide comprehensive enough coverage for an analyst-lite experience.
        try:
            answer = self.client.chat_query(context, query)
            return answer
        except Exception as e:
            return f"Error interacting with the AI client: {str(e)}"
