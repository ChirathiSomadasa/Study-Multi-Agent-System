import json
import re
from typing import Any, Optional, Dict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from state import StudyState
from logger import AgentLogger
from tools.save_quiz import save_quiz

SYSTEM_PROMPT = """You are a highly analytical educational quiz generator. 
Your objective is to read the provided study notes and syllabus, then produce a JSON array of quiz questions.

Guidelines:
- Generate a mix of questions: approximately 5 Multiple Choice (MCQ) and 3 Open-Ended questions.
- MCQ questions MUST include exactly 4 options labelled A-D in the "options" array. Specify the correct letter in the "answer" field.
- Open questions MUST have "options": null. Provide a comprehensive model answer in the "answer" field.
- Each question must have a "topic_tag" that perfectly matches one of the subtopics in the provided syllabus.
- Respond ONLY with a valid JSON array. Do not include markdown fences, preambles, or explanations.

Output schema per question:
{
  "id": <int>,
  "type": "mcq" | "open",
  "question": "<question text>",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."] | null,
  "answer": "<correct letter or model answer>",
  "topic_tag": "<subtopic from syllabus>"
}
"""

def quiz_generator_node(
    state: StudyState,
    model: str = "gemma3:1b",
    logger: Optional[AgentLogger] = None,
) -> dict[str, Any]:
    timer = logger.start_timer() if logger else None
    notes = state.get("notes", "")
    syllabus = state.get("syllabus", {})

    print(f"\n[QuizGenerator] Generating quiz from notes ({len(notes)} chars)")

    llm = ChatOllama(model=model, temperature=0.3, num_ctx=4096)

    subtopics = syllabus.get("subtopics", [])
    user_prompt = (
        f"Target Syllabus Subtopics: {json.dumps(subtopics)}\n\n"
        f"Study Notes:\n{notes}\n\n"
        "Generate the structured JSON array of quiz questions based strictly on the notes above."
    )

    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )

    raw = response.content.strip()
    raw_questions = []

    try:
        parsed = json.loads(raw)
        raw_questions = parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                raw_questions = parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                pass 

    if not raw_questions:
        blocks = re.findall(r'\{.*?\}', raw, re.DOTALL)
        for block in blocks:
            try:
                raw_questions.append(json.loads(block))
            except json.JSONDecodeError:
                continue

    questions = []
    for q in raw_questions:
        if not isinstance(q, dict):
            continue
        
        if "question" not in q or "answer" not in q:
            continue

        valid_q = {
            "id": q.get("id", len(questions) + 1),
            "type": str(q.get("type", "open")).lower(),
            "question": str(q.get("question", "")),
            "options": q.get("options", None),
            "answer": str(q.get("answer", "")),
            "topic_tag": str(q.get("topic_tag", "General"))
        }

        if valid_q["type"] == "mcq":
            opts = valid_q["options"]
            if not isinstance(opts, list) or len(opts) != 4:
                valid_q["type"] = "open"
                valid_q["options"] = None
        else:
            valid_q["type"] = "open"
            valid_q["options"] = None

        questions.append(valid_q)

    if not questions:
        raise ValueError(f"[QuizGenerator] LLM failed to generate valid questions. Raw: {raw[:200]}")

    save_result = save_quiz(questions)
    print(f"[QuizGenerator] Quiz saved → {save_result['path']} ({save_result['mcq_count']} MCQ, {save_result['open_count']} Open)")

    entry = None
    if logger:
        latency = logger.elapsed_ms(timer)
        entry = logger.log_entry(
            agent="quiz_generator",
            input_keys=["notes", "syllabus"],
            tool_calls=["save_quiz"],
            output_keys=["quiz"],
            latency_ms=latency,
            extra={
                "total_questions": save_result["question_count"],
                "mcq_count": save_result["mcq_count"],
                "open_count": save_result["open_count"]
            },
        )

    new_log = list(state.get("log", []))
    if entry:
        new_log.append(entry)

    return {"quiz": questions, "log": new_log}