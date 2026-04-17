"""
agents/content_analyst.py — Content Analyst Agent (Member 2)

Responsibilities:
    1. Read the syllabus produced by the Coordinator.
    2. For each subtopic, call the fetch_resource tool to gather study material.
    3. Synthesise all material into well-structured Markdown study notes.
    4. Write notes to outputs/notes.md.
    5. Append a trace entry to the shared log.

TODO (Member 2):
    - Write the SYSTEM_PROMPT for this agent.
    - Implement the loop that calls fetch_resource() for each subtopic.
    - Parse and combine the LLM's summarisation output into notes.
    - Implement tools/fetch_resource.py (see stub there).
"""

from typing import Any, Optional, Dict

from state import StudyState
from logger import AgentLogger


SYSTEM_PROMPT = """TODO (Member 2): Write the system prompt for the Content Analyst agent.

Guidelines:
- The agent receives a syllabus JSON and must produce cohesive Markdown notes.
- Notes must cover each subtopic with a heading, definition, and key points.
- Use simple language appropriate for the grade level.
- Respond ONLY with Markdown content — no JSON, no preamble.
"""


def content_analyst_node(
    state: StudyState,
    model: str = "gemma3:1b",
    logger: Optional[AgentLogger] = None,
) -> dict[str, Any]:
    """
    Content Analyst agent node. Generates study notes from the syllabus.

    Reads from state:  syllabus, grade_level
    Writes to state:   notes, log (appended)

    Args:
        state:  Current LangGraph shared state.
        model:  Ollama model name.
        logger: Shared AgentLogger instance.

    Returns:
        Partial state dict with updated 'notes' and 'log' keys.

    TODO (Member 2): Full implementation below.
    """
    timer = logger.start_timer() if logger else None
    syllabus = state["syllabus"]

    print(f"\n[ContentAnalyst] Generating notes for: {syllabus['topic']}")

    # ── TODO: Implement this node ──────────────────────────────────────────
    # Suggested steps:
    # 1. Import and call fetch_resource(query=subtopic) for each subtopic
    # 2. Build a prompt that asks the LLM to summarise the fetched resources
    # 3. Parse LLM output as Markdown
    # 4. Write to outputs/notes.md
    # 5. Log the trace entry

    raise NotImplementedError("Member 2: implement content_analyst_node()")
