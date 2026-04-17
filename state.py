"""
state.py — Global state schema for the Study MAS.

This TypedDict is the single source of truth passed between every agent node.
LangGraph serialises this as a dict at each graph step, ensuring no context is lost.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class StudyState(TypedDict):
    """
    Shared state object that flows through every agent node in the graph.

    Fields are populated progressively:
        Coordinator  → fills: syllabus
        Content Analyst → fills: notes
        Quiz Generator  → fills: quiz
        Evaluator       → fills: evaluation
    """

    # Input
    topic: str
    """The study topic provided by the user (e.g. 'Photosynthesis')."""

    grade_level: int
    """Target academic grade level (e.g. 10 for Grade 10)."""

    # Agent outputs 
    syllabus: Optional[dict[str, Any]]
    """
    Produced by Coordinator. Structure:
    {
        "topic": str,
        "subtopics": list[str],
        "learning_objectives": list[str],
        "validated": bool
    }
    """

    notes: Optional[str]
    """
    Produced by Content Analyst. Markdown-formatted study notes
    covering each subtopic from the syllabus.
    """

    quiz: Optional[list[dict[str, Any]]]
    """
    Produced by Quiz Generator. List of question objects:
    [
        {
            "id": int,
            "type": "mcq" | "open",
            "question": str,
            "options": list[str] | None,   # MCQ only
            "answer": str,
            "topic_tag": str
        },
        ...
    ]
    """

    evaluation: Optional[dict[str, Any]]
    """
    Produced by Evaluator. Structure:
    {
        "total_questions": int,
        "answered": int,
        "score": float,
        "per_question": list[dict],
        "summary": str
    }
    """

    # Observability 
    log: list[dict[str, Any]]
    """
    Append-only list of trace entries. Each agent node appends one entry:
    {
        "agent": str,
        "timestamp": str,
        "input_keys": list[str],
        "tool_calls": list[str],
        "output_keys": list[str],
        "latency_ms": float
    }
    """
