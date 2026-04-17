"""
agents/coordinator.py — Coordinator Agent (Member 1)
"""

import json
import os
from typing import Any, Optional, Dict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from state import StudyState
from logger import AgentLogger
from tools.validate_topic import validate_topic

# System prompt
SYSTEM_PROMPT = """You are a strictly JSON-only API. 
Create a study syllabus. Do not write any other text.
Respond ONLY with this exact JSON format:

{
  "topic": "topic name",
  "validated": true,
  "subtopics": ["subtopic 1", "subtopic 2", "subtopic 3", "subtopic 4"],
  "learning_objectives": ["objective 1", "objective 2", "objective 3"]
}"""

def coordinator_node(
    state: StudyState,
    model: str = "gemma3:1b",
    logger: Optional[AgentLogger] = None,
) -> Dict[str, Any]:
    """
    Coordinator agent node. Validates the topic and generates a syllabus.
    """
    timer = logger.start_timer() if logger else None
    topic: str = state["topic"]
    grade: int = state.get("grade_level", 10)

    print(f"\n[Coordinator] Validating topic: '{topic}' for Grade {grade}")

    # Step 1: Run the validate_topic tool 
    validation_result = validate_topic(topic=topic, grade_level=grade)

    if not validation_result["is_valid"]:
        raise ValueError(
            f"[Coordinator] Topic rejected by validate_topic tool: "
            f"{validation_result['reason']}"
        )

    # Step 2: Call Ollama LLM to generate syllabus 
    llm = ChatOllama(model=model, temperature=0.2)

    user_prompt = (
        f"Generate a syllabus outline for the topic: '{topic}'\n"
        f"Target grade level: {grade}\n"
        "Respond with valid JSON only."
    )

    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )

    raw = response.content.strip()

    # Step 3: Parse and validate JSON output 
    try:
        syllabus: Dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            syllabus = json.loads(match.group())
        else:
            raise ValueError(f"[Coordinator] LLM returned non-JSON output: {raw[:200]}")

    # Forgiveness Logic for Small Models
    if not syllabus.get("validated", False):
        # If the small model forgot "validated: true" but STILL gave us subtopics, we accept it!
        if "subtopics" in syllabus and isinstance(syllabus["subtopics"], list) and len(syllabus["subtopics"]) > 0:
            print("[Coordinator] Note: Forgiving small model for missing validation key.")
            syllabus["validated"] = True
        else:
            raise ValueError(
                f"[Coordinator] LLM rejected topic or gave bad JSON: {syllabus.get('error', 'unknown reason')}"
            )

    # Step 4: Persist to disk 
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "syllabus.json")

    with open(out_path, "w") as f:
        json.dump(syllabus, f, indent=2)

    print(f"[Coordinator] Syllabus saved → {out_path}")
    print(f"[Coordinator] Subtopics: {syllabus.get('subtopics', [])}")

    # Step 5: Log trace 
    entry = None
    if logger:
        latency = logger.elapsed_ms(timer)
        entry = logger.log_entry(
            agent="coordinator",
            input_keys=["topic", "grade_level"],
            tool_calls=["validate_topic"],
            output_keys=["syllabus"],
            latency_ms=latency,
            extra={"subtopics_count": len(syllabus.get("subtopics", []))},
        )

    new_log = list(state.get("log", []))
    if entry:
        new_log.append(entry)

    return {"syllabus": syllabus, "log": new_log}