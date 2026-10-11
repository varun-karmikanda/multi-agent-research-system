from langchain.tools import tool
import requests
from src.config import settings
import os
from tavily import TavilyClient

tavily = TavilyClient(api_key=settings.tavily_api_key.get_secret_value())

def web_search(query: str, max_results: int = 5) -> str:
    results = tavily.search(query=query, max_results=max_results)
        
    out = [
        f"Title: {res.get('title', 'N/A')}\n"
        f"URL: {res.get('url', 'N/A')}\n"
        f"Snippet: {res.get('content', '')[:300]}"
        for res in results.get('results', [])
    ]
    
    return "\n---\n".join(out)

