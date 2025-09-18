import os

from tavily import TavilyClient
import weave # (1) Import weave



weave.init(project="your-project-name")  # (2) connect to your Weave project


@weave.op()                              # (3) trace this function
def tavily_search(query: str) -> dict:    
    tv = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return tv.search(query)


# Example
if __name__ == "__main__":
    print(tavily_search("Who is Leo Messi?"))


def tavily_search(query: str) -> dict:
    """
    Search using Tavily API and return the response.
    """
    tv = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return tv.search(query)


# Example
if __name__ == "__main__":
    print(tavily_search("Who is Leo Messi?"))
