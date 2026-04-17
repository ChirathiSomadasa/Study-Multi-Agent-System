"""
agents/evaluator.py — Evaluator Agent (Member 4)

Responsibilities:
    1. Read the quiz produced by the Quiz Generator.
    2. Use LLM-as-a-Judge: for each question, score a student answer 0-10.
    3. Call the grade_answers tool to compute aggregate scores.
    4. Write a final evaluation report to outputs/report.md.
    5. Append a trace entry to the shared log.

TODO (Member 4):
    - Write the SYSTEM_PROMPT for this agent (LLM-as-Judge persona).
    - Decide how to source student answers (simulate them, or read from a file).
    - Implement tools/grade_answers.py (see stub there).
    - The evaluation output becomes the final state — make it informative.
"""

from typing import Any, Optional, Dict

from state import StudyState
from logger import AgentLogger


SYSTEM_PROMPT = """TODO (Member 4): Write the system prompt for the Evaluator agent.

Guidelines:
- You are an impartial academic evaluator. Grade each answer strictly but fairly.
- For MCQ: 10 if the letter matches, 0 otherwise.
- For open questions: score 0-10 based on accuracy, completeness, and clarity.
- Respond ONLY with valid JSON — one object per question.

Output schema per graded question:
{
  "id": <int>,
  "score": <0-10>,
  "feedback": "<one sentence of feedback>",
  "correct_answer": "<answer from quiz>"
}
"""


def evaluator_node(
    state: StudyState,
    model: str = "gemma3:1b",
    logger: Optional[AgentLogger] = None,
) -> dict[str, Any]:
    """
    Evaluator agent node. Grades answers and produces the final report.

    Reads from state:  quiz
    Writes to state:   evaluation, log (appended)

    Args:
        state:  Current LangGraph shared state.
        model:  Ollama model name.
        logger: Shared AgentLogger instance.

    Returns:
        Partial state dict with updated 'evaluation' and 'log' keys.

    TODO (Member 4): Full implementation below.
    """
    timer = logger.start_timer() if logger else None
    quiz = state["quiz"]

    print(f"\n[Evaluator] Evaluating {len(quiz)} questions")

    # ── TODO: Implement this node ──────────────────────────────────────────
    # Suggested steps:
    # 1. For demo purposes, you can auto-generate sample student answers
    #    using the LLM, then immediately grade them — shows the full loop.
    # 2. Call grade_answers(answers, rubric) tool
    # 3. Compute aggregate score and write outputs/report.md
    # 4. Log the trace entry

    raise NotImplementedError("Member 4: implement evaluator_node()")
