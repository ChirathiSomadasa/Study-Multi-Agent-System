"""
tools/grade_answers.py — Custom tool for the Evaluator Agent (Member 4).

TODO (Member 4): Implement this tool.

This tool should:
    - Accept a list of graded question dicts (with scores already assigned by LLM).
    - Compute aggregate statistics (mean, per-topic breakdown).
    - Write outputs/report.md with a human-readable summary.
    - Return an evaluation summary dict.
"""

from typing import Any, TypedDict


class GradeResult(TypedDict):
    total_questions: int
    answered: int
    mean_score: float
    per_topic: dict[str, float]
    report_path: str
    success: bool


def grade_answers(
    graded_questions: list[dict[str, Any]],
    topic: str = "Unknown",
) -> GradeResult:
    """
    Aggregate LLM-assigned scores and write a final report.

    Args:
        graded_questions: List of graded question dicts, each with keys:
                          id, score (0-10), feedback, correct_answer.
        topic:            Study topic (used in the report header).

    Returns:
        GradeResult with aggregate statistics and report path.

    Raises:
        ValueError: If graded_questions is empty.

    TODO (Member 4): Implement the body of this function.
    """
    if not graded_questions:
        raise ValueError("graded_questions list must not be empty")

    raise NotImplementedError("Member 4: implement grade_answers()")
