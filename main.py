from src.tools.tools import web_search, scrape_url
from rich import print

# res = web_search("super cars", 2)
# print(res)

# print(scrape_url("https://www.langchain.com/langgraph"))

print(web_search.invoke("super cars"))