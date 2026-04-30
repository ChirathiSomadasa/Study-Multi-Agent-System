"""
tools/save_quiz.py — Custom tool for the Quiz Generator Agent (Member 3).
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
    """
    if not questions:
        raise ValueError("questions list must not be empty")

    mcq_count = 0
    open_count = 0
    required_keys = {"id", "type", "question", "answer", "topic_tag"}

    # Validate the schema of each question
    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValueError(f"Item at index {idx} is not a dictionary.")
        
        missing_keys = required_keys - set(q.keys())
        if missing_keys:
            raise ValueError(f"Question at index {idx} is missing required keys: {missing_keys}")

        q_type = q.get("type")
        if q_type == "mcq":
            mcq_count += 1
            options = q.get("options")
            if not isinstance(options, list) or len(options) != 4:
                raise ValueError(f"MCQ question (id: {q['id']}) must have exactly 4 items in 'options'.")
        elif q_type == "open":
            open_count += 1
        else:
            raise ValueError(f"Invalid question type '{q_type}' at index {idx}.")

    # Write the list to outputs/quiz.json
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "quiz.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)

    return SaveQuizResult(
        path=out_path,
        question_count=len(questions),
        mcq_count=mcq_count,
        open_count=open_count,
        success=True
    )