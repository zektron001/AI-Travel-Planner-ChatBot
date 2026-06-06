import os
from langchain.tools import tool
from tavily import TavilyClient


def _tavily_search(query: str, max_results: int = 3) -> list:
    """Raw Tavily search returning list of results."""
    api_key = os.getenv("TAVILY_API_KEY")
    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=True
    )
    return response


@tool
def search_attractions(query: str) -> str:
    """
    Search for tourist attractions, restaurants, activities, and travel tips.
    Use for finding things to do, places to eat, local experiences.
    Example: 'top attractions in Tokyo' or 'best street food in Bangkok'
    """
    try:
        response = _tavily_search(query, max_results=3)
        result = f"Search results for: {query}\n\n"
        if response.get("answer"):
            result += f"Summary: {response['answer']}\n\n"
        for i, r in enumerate(response.get("results", [])[:3], 1):
            result += f"{i}. {r['title']}: {r['content'][:200]}...\n\n"
        return result
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def multi_hop_search(destination: str) -> str:
    """
    Perform multi-hop RAG search for a destination.
    This does 3 chained searches:
    1. Overview of the destination
    2. Top neighbourhoods/districts to visit
    3. Specific attractions in those neighbourhoods
    Use this for building a detailed, rich itinerary.
    """
    try:
        results = []

        # ── Hop 1: City overview ───────────────────────────────────────────
        hop1 = _tavily_search(f"{destination} travel guide overview highlights", max_results=2)
        overview = hop1.get("answer", "")
        hop1_text = " ".join([r["content"] for r in hop1.get("results", [])[:2]])
        results.append(f"📍 OVERVIEW OF {destination.upper()}:\n{overview}\n{hop1_text[:400]}")

        # ── Hop 2: Extract districts from hop 1, search each ──────────────
        hop2 = _tavily_search(f"best neighbourhoods districts areas to visit in {destination}", max_results=2)
        hop2_answer = hop2.get("answer", "")
        hop2_text = " ".join([r["content"] for r in hop2.get("results", [])[:2]])
        results.append(f"\n🗺️ TOP AREAS IN {destination.upper()}:\n{hop2_answer}\n{hop2_text[:400]}")

        # ── Hop 3: Deep dive into specific things based on hop 2 ───────────
        hop3 = _tavily_search(f"must visit attractions food experiences {destination} 2 days itinerary", max_results=3)
        hop3_answer = hop3.get("answer", "")
        hop3_items = "\n".join([f"- {r['title']}: {r['content'][:150]}" for r in hop3.get("results", [])[:3]])
        results.append(f"\n🎯 SPECIFIC EXPERIENCES IN {destination.upper()}:\n{hop3_answer}\n{hop3_items}")

        return "\n".join(results)

    except Exception as e:
        return f"Multi-hop search error: {str(e)}"
