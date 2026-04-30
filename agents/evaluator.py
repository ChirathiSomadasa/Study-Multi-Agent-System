"""
agents/evaluator.py — Evaluator Agent

Responsibilities:
    1. Read the quiz produced by the Quiz Generator.
    2. Use LLM-as-a-Judge: for each question, score a student answer 0-10.
    3. Call the grade_answers tool to compute aggregate scores.
    4. Write a final evaluation report to outputs/report.md.
    5. Append a trace entry to the shared log.

Notes:
    - Uses answer.json for student input (see tools/load_answers.py).
    - The evaluation output becomes the final state.
    - code for evaluation:
        python -c "import json; from agents.evaluator import evaluator_node; from logger import AgentLogger; quiz=json.load(open('outputs/quiz.json','r',encoding='utf-8')); syllabus=json.load(open('outputs/syllabus.json','r',encoding='utf-8')); state={'topic': syllabus.get('topic','Unknown'), 'grade_level':10, 'syllabus': syllabus, 'notes': None, 'quiz': quiz, 'evaluation': None, 'log': []}; out=evaluator_node(state, model='gemma3:1b', logger=AgentLogger()); print(out['evaluation']['summary'])"

"""


from typing import Any, Optional
import json
import re

from state import StudyState
from logger import AgentLogger
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from tools.grade_answers import grade_answers
from tools.load_answers import load_student_answers


SYSTEM_PROMPT = """You are an impartial academic evaluator.
Grade one answer strictly but fairly.

Rules:
- For MCQ: score 10 if the letter matches exactly, otherwise 0.
- For open questions: score 0-10 based on accuracy, completeness, and clarity.
- Feedback must be one short sentence.
- Respond ONLY with valid JSON.

Return a JSON object in this schema:
{
    "score": <0-10>,
    "feedback": "<one sentence>"
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

    """

    timer = logger.start_timer() if logger else None
    quiz = state["quiz"] or []
    if not quiz:
        raise ValueError("[Evaluator] quiz is empty")

    print(f"\n[Evaluator] Evaluating {len(quiz)} questions")

    topic = "Unknown"
    if state.get("syllabus") and isinstance(state["syllabus"], dict):
        topic = state["syllabus"].get("topic", "Unknown")

    # llm = ChatOllama(model=model, temperature=0.2)
    llm = ChatOllama(model=model, temperature=0.2, format="json")


    # 1) Load student answers from answer.json (deadline enforced)
    answers_result = load_student_answers(quiz)
    student_answers = answers_result["answers"]
    student_map = answers_result["answer_map"]


    # 2) Judge answers one-by-one using LLM-as-Judge
    graded_enriched: list[dict[str, Any]] = []
    for idx, q in enumerate(quiz, start=1):
        qid = _coerce_id(q.get("id", idx), idx)
        qtype = str(q.get("type", "open")).lower()
        correct_answer = str(q.get("answer", ""))
        student_answer = student_map.get(qid, "")
        has_answer = bool(str(student_answer).strip())

        if not has_answer:
            score = 0
            feedback = "No answer provided."
        else:
            judged = _judge_one(llm, q, student_answer)
            if judged is None:
                score = 0
                feedback = "No grade returned by judge."
            else:
                score = _normalize_score(
                    judged.get("score", 0),
                    qtype=qtype,
                    student_answer=student_answer,
                    correct_answer=correct_answer,
                )
                feedback = judged.get("feedback", "") or "Graded by judge."

        graded_enriched.append(
            {
                "id": qid,
                "type": q.get("type"),
                "question": q.get("question"),
                "student_answer": student_answer,
                "correct_answer": q.get("answer"),
                "score": score,
                "feedback": feedback,
                "topic_tag": q.get("topic_tag", "general"),
            }
        )


    # 4) Aggregate + report
    result = grade_answers(graded_enriched, topic=topic)


    # 5) Build evaluation state
    per_topic = result.get("per_topic", {})
    summary = (
        f"Mean score {result['mean_score']}/10 across {result['total_questions']} questions."
    )
    if per_topic:
        best = max(per_topic.items(), key=lambda kv: kv[1])[0]
        worst = min(per_topic.items(), key=lambda kv: kv[1])[0]
        summary += f" Strongest topic: {best}. Weakest topic: {worst}."

    evaluation = {
        "total_questions": result["total_questions"],
        "answered": result["answered"],
        "score": result["mean_score"],
        "per_question": graded_enriched,
        "summary": summary,
        "report_path": result["report_path"],
    }


    # 6) Log trace
    entry = None
    if logger:
        latency = logger.elapsed_ms(timer)
        entry = logger.log_entry(
            agent="evaluator",
            input_keys=["quiz"],
            tool_calls=["load_student_answers", "grade_answers"],
            output_keys=["evaluation"],
            latency_ms=latency,
            extra={"questions": len(quiz)},
        )

    new_log = list(state.get("log", []))
    if entry:
        new_log.append(entry)

    return {"evaluation": evaluation, "log": new_log}


def _parse_json_obj(raw: str) -> Optional[dict[str, Any]]:
    raw = raw.strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def _judge_one(
    llm: ChatOllama,
    question: dict[str, Any],
    student_answer: str,
) -> Optional[dict[str, Any]]:
    qtype = str(question.get("type", "open")).lower()
    judge_user = (
        "Grade this single answer. Return ONLY the JSON object schema.\n\n"
        f"Type: {qtype}\n"
        f"Question: {question.get('question', '')}\n"
        f"Options: {json.dumps(question.get('options', None))}\n"
        f"Correct answer: {question.get('answer', '')}\n"
        f"Student answer: {student_answer}"
    )
    try:
        judge_raw = llm.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=judge_user)]
        ).content
    except Exception:
        return None
    return _parse_json_obj(judge_raw)


def _normalize_score(
    score: Any,
    qtype: str,
    student_answer: str,
    correct_answer: str,
) -> int:
    if qtype == "mcq":
        student = str(student_answer).strip().upper()
        correct = str(correct_answer).strip().upper()
        return 10 if student == correct else 0

    try:
        score_val = float(score)
    except (TypeError, ValueError):
        return 0
    if score_val < 0:
        return 0
    if score_val > 10:
        return 10
    return int(round(score_val))


def _coerce_id(raw_id: Any, fallback: int) -> int:
    if isinstance(raw_id, bool):
        return fallback
    try:
        return int(raw_id)
    except (TypeError, ValueError):
        return fallback
