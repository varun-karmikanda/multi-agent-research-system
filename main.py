from src.tools.tools import web_search, scrape_url
from rich import print
from src.pipelines.pipelines import run_multi_agent_research_system

topic = "LLM based multi-agent systems"
results = run_multi_agent_research_system(topic=topic)
print(f"\nFinal Research Report for topic '{topic}':\n{results['report']}\n")