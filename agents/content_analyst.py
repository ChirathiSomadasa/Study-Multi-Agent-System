
import os
from typing import Any, Optional, Dict
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from state import StudyState
from logger import AgentLogger

from tools.fetch_resource import fetch_resource

SYSTEM_PROMPT = """You are an expert Educational Content Analyst. 
Your task is to take raw study material and convert it into high-quality, structured Markdown study notes.

Rules:
1. Use Grade {grade} level vocabulary.
2. Structure: Use # for the Main Topic and ## for Subtopics.
3. Content: For each subtopic, provide a clear definition and bullet points for key concepts.
4. Output: Respond ONLY with Markdown text. Do not include any preamble, greetings, or JSON.
"""


def content_analyst_node(
    state: StudyState,
    model: str = "gemma3:1b",
    logger: Optional[AgentLogger] = None,
) -> dict[str, Any]:
    """
    Content Analyst agent node. Generates study notes from the syllabus.
    Utilizes state management to pass data between agents.

    Reads from state:  syllabus, grade_level
    Writes to state:   notes, log (appended)

    Args:
        state:  Current LangGraph shared state.
        model:  Ollama model name.
        logger: Shared AgentLogger instance.

    Returns:
        Partial state dict with updated 'notes' and 'log' keys.

    """
    timer = logger.start_timer() if logger else None
    syllabus = state["syllabus"]
    grade = state.get("grade_level", 10)
    subtopics = syllabus.get("subtopics", [])

    print(f"\n[ContentAnalyst] Generating notes for: {syllabus['topic']}")

    all_fetched_text = ""

    for sub in subtopics:
        print(f"[ContentAnalyst] Fetching content for: {sub}")
        resource = fetch_resource(query=sub)
        if resource["success"]:
            all_fetched_text += f"\n\nSource Material for {sub}:\n{resource['content']}"

    llm = ChatOllama(model=model, temperature=0.3)

    user_prompt = (
        f"Topic: {syllabus['topic']}\n"
        f"Subtopics to cover: {', '.join(subtopics)}\n"
        f"Raw Material: {all_fetched_text}\n\n"
        "Please generate the Markdown study notes now."
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT.format(grade=grade)),
        HumanMessage(content=user_prompt),
    ])

    notes_markdown = response.content.strip()

    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "notes.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(notes_markdown)

    print(f"[ContentAnalyst] Notes saved → {out_path}")

    entry = None
    if logger:
        latency = logger.elapsed_ms(timer)
        entry = logger.log_entry(
            agent="content_analyst",
            input_keys=["syllabus"],
            tool_calls=["fetch_resource"],
            output_keys=["notes"],
            latency_ms=latency,
            extra={"subtopics_processed": len(subtopics)},
        )

    new_log = list(state.get("log", []))
    if entry:
        new_log.append(entry)
    else:
        new_log.append({"agent": "content_analyst", "status": "success"})

    return {"notes": notes_markdown, "log": new_log}
