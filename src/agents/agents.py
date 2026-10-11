from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools.tools import web_search, scrape_url
from src.config import settings

llm = ChatGroq(
    api_key=settings.groq_api_key.get_secret_value(),
    model=settings.groq_model.get_secret_value(),
    temperature=0.0,
    max_output_tokens=1024,
)

# Agent1: Web Search and Scraping Agent
def build_search_agent():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant that can search the web and scrape content from URLs."),
            ("human", "{input}"),
        ]
    )
    
    agent = create_agent(
        llm=llm,
        tools=[web_search, scrape_url],
        prompt=prompt,
        output_parser=StrOutputParser(),
    )
    
    return agent

#2 Agent 2: Reader Agent
def build_reader_agent():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant that can read and summarize content from URLs."),
            ("human", "{input}"),
        ]
    )
    
    agent = create_agent(
        llm=llm,
        tools=[scrape_url],
        prompt=prompt,
        output_parser=StrOutputParser(),
    )
    
    return agent

# Writer chain
writer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert research writer. You will receive information from multiple sources and your task is to synthesize it into a coherent, well-structured research report."),
        ("human", """Write a detailed research report on the topic below.
         
Topic: {topic}

Research Gathered:
{research}

Structure the report as follows:
1. Introduction: Provide an overview of the topic and its significance.
2. Background: Present relevant background information and context.
3. Methodology: Describe the methods used to gather and analyze information.
4. Findings: Summarize the key findings from the research.
5. Discussion: Interpret the findings and discuss their implications.
6. Conclusion: Provide a concise summary of the report and its main takeaways.
7. References: List all sources used in the research, formatted in APA style.

Be detailed and professional in your writing. Ensure that the report is well-organized, clear, and free of grammatical errors. Use appropriate headings and subheadings to enhance readability. Avoid plagiarism by properly citing all sources used in the research."""),
        
    ]
)

writer_chain = writer_prompt | llm | StrOutputParser()


# Critic chain
critic_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a critical reviewer of research reports. Your task is to evaluate the quality, coherence, and accuracy of the report provided to you."),
        ("human", """You will receive a research report on the topic below. Your task is to critically evaluate the report and provide constructive feedback.
Topic: {topic}
Research Report:
{report}
Respond with exact format:

Score: X/10

Strengths:
- ...
-...

Areas for Improvement:
- ...
- ...

One line verdict: [Acceptable/Needs Improvement/Unacceptable]"""),
    ]
)

critic_chain = critic_prompt | llm | StrOutputParser()