"""
agents/quiz_generator.py — Quiz Generator Agent (Member 3)

Responsibilities:
    1. Read the study notes produced by the Content Analyst.
    2. Generate a mixed quiz: MCQ + open-ended questions.
    3. Call the save_quiz tool to persist quiz to outputs/quiz.json.
    4. Append a trace entry to the shared log.

TODO (Member 3):
    - Write the SYSTEM_PROMPT for this agent.
    - Implement the quiz generation loop (aim for 5 MCQ + 3 open questions).
    - Ensure each question has a correct answer and topic_tag.
    - Implement tools/save_quiz.py (see stub there).
"""

from typing import Any, Optional, Dict

from state import StudyState
from logger import AgentLogger


SYSTEM_PROMPT = """TODO (Member 3): Write the system prompt for the Quiz Generator agent.

Guidelines:
- Produce a JSON array of question objects.
- MCQ: include 4 options labelled A-D, specify the correct letter in "answer".
- Open: "options" key should be null, "answer" should be a model answer string.
- Each question must have a "topic_tag" matching one of the syllabus subtopics.
- Respond ONLY with valid JSON — no preamble, no markdown fences.

Output schema per question:
{
  "id": <int>,
  "type": "mcq" | "open",
  "question": "<question text>",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."] | null,
  "answer": "<correct letter or model answer>",
  "topic_tag": "<subtopic>"
}
"""


def quiz_generator_node(
    state: StudyState,
    model: str = "gemma3:1b",
    logger: Optional[AgentLogger] = None,
) -> dict[str, Any]:
    """
    Quiz Generator agent node. Produces quiz questions from the study notes.

    Reads from state:  notes, syllabus
    Writes to state:   quiz, log (appended)

    Args:
        state:  Current LangGraph shared state.
        model:  Ollama model name.
        logger: Shared AgentLogger instance.

    Returns:
        Partial state dict with updated 'quiz' and 'log' keys.

    TODO (Member 3): Full implementation below.
    """
    timer = logger.start_timer() if logger else None
    notes = state["notes"]

    print(f"\n[QuizGenerator] Generating quiz from notes ({len(notes)} chars)")

    # ── TODO: Implement this node ──────────────────────────────────────────
    # Suggested steps:
    # 1. Build a prompt using notes + syllabus subtopics
    # 2. Call the LLM to generate question JSON
    # 3. Parse and validate the JSON list
    # 4. Call save_quiz(questions) tool
    # 5. Log the trace entry

    raise NotImplementedError("Member 3: implement quiz_generator_node()")
