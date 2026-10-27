import json
from openrouter_client import MultiKeyOpenRouterClient

class MarketAnalyst:
    """Uses OpenRouter LLaMA 3.3 70B for generating analyst-level reports based on aggregated industry news."""
    def __init__(self, api_keys: list[str]):
        if not api_keys:
            raise ValueError("No OpenRouter API keys provided. Set OPENROUTER_API_KEY in .env")
        self.client = MultiKeyOpenRouterClient(api_keys)

    def generate_sector_report(self, sector: str, articles: list[dict]) -> dict:
        """Crafts a comprehensive analyst report from a list of market articles."""
        context = "\n".join([f"Title: {a['title']}\nSummary: {a['description']}" for a in articles[:15]])
        
        system_prompt = (
            "You are a Senior Market Analyst specializing in institutional intelligence. "
            "Your task is to analyze raw news articles and provide a structured JSON report. "
            "You must follow this exact JSON schema: "
            "{"
            "  'sector': str,"
            "  'overall_sentiment': str,"
            "  'key_drivers': list[str],"
            "  'risks': list[str],"
            "  'opportunities': list[str],"
            "  'companies_to_watch': list[str]"
            "}"
        )
        
        user_prompt = f"Sector: {sector}\n\nContext Articles:\n{context}"
        
        try:
            report_str = self.client.generate_report(
                system_prompt, 
                user_prompt, 
                response_format={"type": "json_object"}
            )
            return json.loads(report_str)
        except Exception as e:
            return {
                "sector": sector,
                "overall_sentiment": "Error generating report",
                "key_drivers": [str(e)],
                "risks": [],
                "opportunities": [],
                "companies_to_watch": []
            }
