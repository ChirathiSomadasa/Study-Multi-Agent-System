"""
tools/save_quiz.py — Custom tool for the Quiz Generator Agent (Member 3).

TODO (Member 3): Implement this tool.

This tool should:
    - Accept a list of question dicts.
    - Validate the schema of each question.
    - Write the list to outputs/quiz.json.
    - Return a summary dict.
"""

import json
import os
from typing import Any, TypedDict


class SaveQuizResult(TypedDict):
    path: str
    question_count: int
    mcq_count: int
    open_count: int
    success: bool


def save_quiz(questions: list[dict[str, Any]]) -> SaveQuizResult:
    """
    Persist a list of quiz questions to outputs/quiz.json.

    Args:
        questions: List of question dicts. Each must have keys:
                   id, type, question, options, answer, topic_tag.

    Returns:
        SaveQuizResult with path and counts.

    Raises:
        ValueError: If questions list is empty or any question is malformed.

    TODO (Member 3): Implement the body of this function.
    """
    if not questions:
        raise ValueError("questions list must not be empty")

    raise NotImplementedError("Member 3: implement save_quiz()")
