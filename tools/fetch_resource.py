"""
tools/fetch_resource.py — Custom tool for the Content Analyst Agent (Member 2).

TODO (Member 2): Implement this tool.

This tool should:
    - Accept a subtopic query string.
    - Return relevant study text WITHOUT calling a paid external API.

Suggested implementations (choose one):
    Option A — Wikipedia API (free, no key needed):
        Use the `wikipedia-api` package or requests to call
        https://en.wikipedia.org/api/rest_v1/page/summary/{topic}
        and return the extract field.

    Option B — Local file search:
        Search a /resources/ folder of pre-downloaded .txt files
        and return the best-matching chunk.

    Option C — DuckDuckGo Instant Answer API (free):
        GET https://api.duckduckgo.com/?q={query}&format=json
        and return the AbstractText field.
"""

from typing import TypedDict


class FetchResult(TypedDict):
    query: str
    source: str
    content: str
    success: bool


def fetch_resource(query: str, max_chars: int = 2000) -> FetchResult:
    """
    Fetch study content for a given subtopic query.

    Args:
        query:     The subtopic to search for (e.g. "Chloroplast structure").
        max_chars: Maximum characters to return (default: 2000).

    Returns:
        FetchResult with content and metadata.

    Raises:
        ValueError: If query is empty.

    TODO (Member 2): Implement the body of this function.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    raise NotImplementedError("Member 2: implement fetch_resource()")
