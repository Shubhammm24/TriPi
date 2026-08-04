"""Web search tool using DuckDuckGo (free, no key required)."""

from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for travel-related information.

    Uses DuckDuckGo search (completely free, no API key). Falls back
    gracefully if the library is unavailable.

    Args:
        query: Search query string (e.g. "best time to visit Paris 2025").

    Returns:
        Formatted search results summary.
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return f"No search results found for: {query}"

        lines = [f"🔍 Web Search Results for: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "No description")
            href = r.get("href", "")
            lines.append(f"  {i}. **{title}**")
            lines.append(f"     {body}")
            if href:
                lines.append(f"     Source: {href}")
            lines.append("")

        return "\n".join(lines)

    except ImportError:
        return (
            "Web search is unavailable. Install duckduckgo-search: "
            "pip install duckduckgo-search"
        )
    except Exception as e:
        return f"Web search failed: {str(e)}"
