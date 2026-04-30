"""
tools/grade_answers.py — Custom tool for the Evaluator Agent.
This tool:
    - Accept a list of graded question dicts (with scores already assigned by LLM).
    - Compute aggregate statistics (mean, per-topic breakdown).
    - Write outputs/report.md with a human-readable summary.
    - Return an evaluation summary dict.
"""

from typing import Any, TypedDict
import os


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

    """

    if not graded_questions:
        raise ValueError("graded_questions list must not be empty")

    scores: list[float] = []
    per_topic_scores: dict[str, list[float]] = {}

    for q in graded_questions:
        score = q.get("score")
        if isinstance(score, (int, float)):
            scores.append(float(score))

        tag = q.get("topic_tag") or "general"
        if isinstance(score, (int, float)):
            per_topic_scores.setdefault(tag, []).append(float(score))

    total_questions = len(graded_questions)
    answered = len(scores)
    mean_score = round(sum(scores) / answered, 2) if answered else 0.0

    per_topic: dict[str, float] = {}
    for tag, vals in per_topic_scores.items():
        if vals:
            per_topic[tag] = round(sum(vals) / len(vals), 2)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "Final_Report.md")

    lines: list[str] = []
    lines.append("# Evaluation Report")
    lines.append("")
    lines.append(f"Topic: {topic}")
    lines.append(f"Total questions: {total_questions}")
    lines.append(f"Answered: {answered}")
    lines.append(f"Mean score: {mean_score}/10")
    lines.append("")
    lines.append("## Per-topic breakdown")
    if per_topic:
        for tag, avg in sorted(per_topic.items()):
            lines.append(f"- {tag}: {avg}/10")
    else:
        lines.append("- No topic tags found")
    lines.append("")
    lines.append("## Question feedback")
    for idx, q in enumerate(graded_questions, start=1):
        lines.append(f"{idx}. {q.get('question', '(missing question)')}")
        lines.append(f"   Type: {q.get('type', 'unknown')}")
        lines.append(f"   Student answer: {q.get('student_answer', '')}")
        lines.append(f"   Correct answer: {q.get('correct_answer', '')}")
        lines.append(f"   Score: {q.get('score', 0)}/10")
        lines.append(f"   Feedback: {q.get('feedback', '')}")
        lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return GradeResult(
        total_questions=total_questions,
        answered=answered,
        mean_score=mean_score,
        per_topic=per_topic,
        report_path=report_path,
        success=True,
    )
