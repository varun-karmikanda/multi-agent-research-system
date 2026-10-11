from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

def run_multi_agent_research_system(topic: str) -> dict:
    """
    Run the multi-agent research system for a given topic.
    
    Args:
        topic (str): The research topic.
        
    Returns:
        dict: A dictionary containing the research report and any additional information.
    """
    state = {}
    
    # Search Agent: Gather information from the web
    print("\n" + "="*50)
    print(f"Running Search Agent for topic: {topic}")
    print("="*50 + "\n")
    
    search_agent = build_search_agent()
    search_results = search_agent.invoke({
        "messages": [(
            "user",
            f"Search for information on the topic: {topic}. "
            "Provide titles, URLs, and short snippets of relevant content.",
        )]
    })
    
    state['search_results'] = search_results['messages'][-1].content
    
    print(f"\nSearch Results: {state['search_results']}\n")
    
    
    # Reader Agent: Scrape and summarize content from URLs
    print("\n" + "="*50)
    print(f"Running Reader Agent for topic: {topic}")
    print("="*50 + "\n")
    
    reader_agent = build_reader_agent()
    reader_results = reader_agent.invoke({
        'messages': [("user",
            f"Based on the following search result about topic '{topic}', "
            "pick the most relevant URLs and scrape their content. "
            "For every scrape call, pass the complete URL as the tool's 'url' argument. "
            "Do not pass search parameters. Summarize the scraped content concisely."
            f"\n\nSearch Results:\n{state['search_results']}"
        )]
    })
    
    state['scraped_content'] = reader_results['messages'][-1].content
    
    print(f"\nReader Results: {state['scraped_content']}\n")
    
    # Writer Chain: Synthesize the gathered information into a research report
    print("\n" + "="*50)
    print(f"Running Writer Chain for topic: {topic}")
    print("="*50 + "\n")
    
    research_combined = (
        f"Search Results:\n{state['search_results']}\n\n"
        f"Detailed Scraped Content:\n{state['scraped_content']}\n\n"
    )
    
    state['report'] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })
    
    print(f"\nFinal Research Report:\n{state['report']}\n")
    
    # Critic Chain: Review and critique the research report
    print("\n" + "="*50)
    print(f"Running Critic Chain for topic: {topic}")
    print("="*50 + "\n")
    
    state['feedback'] = critic_chain.invoke({
        "topic": topic,
        "report": state['report']
    })
    
    print(f"\nCritic Feedback:\n{state['feedback']}\n")
    
    return state