# Multi-Agent Research System

An LLM-based research pipeline that turns a topic into a source-grounded research
report. It combines specialized LangChain agents and chains:

```text
Research topic
    |
Search Agent -- Tavily web search --> search results
    |
Reader Agent -- URL scraping ------> scraped summaries
    |
Writer chain ----------------------> structured report
    |
Critic chain ----------------------> score, feedback, and verdict
```

The Streamlit interface displays the pipeline stages, generated report, sources,
scraped summaries, and critic review. The same pipeline can also be run from the
command line.

## Requirements

- Python 3.12 or newer
- A [Groq](https://console.groq.com/) API key
- A [Tavily](https://tavily.com/) API key

## Setup

Clone the repository and create a virtual environment:

```bash
git clone <repository-url>
cd multi-agent-research-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
TAVILY_API_KEY=your_tavily_api_key
```

Do not commit `.env` or expose API keys in source control.

## Run the web app

Start the Streamlit research lab:

```bash
source venv/bin/activate
streamlit run app.py
```

Open the local URL printed by Streamlit, enter a research topic, and select
**Run research**.

## Run from the command line

The CLI entry point runs the example topic configured in `main.py`:

```bash
source venv/bin/activate
python main.py
```

To use the pipeline from another Python script:

```python
from src.pipelines.pipelines import run_multi_agent_research_system

result = run_multi_agent_research_system("LLM-based multi-agent systems")
print(result["report"])
print(result["feedback"])
```

## Project structure

```text
app.py                  Streamlit interface
main.py                 CLI example
src/agents/agents.py    Search/reader agents, writer, and critic chains
src/tools/tools.py      Tavily search and webpage scraping tools
src/pipelines/          End-to-end orchestration
src/config.py           Environment and API-key configuration
slides.md               Two-slide system overview
```