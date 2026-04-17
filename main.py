import argparse
import json
from graph import build_graph
from logger import AgentLogger


def main() -> None:
    parser = argparse.ArgumentParser(description="Study MAS — Agentic Education System")
    parser.add_argument("--topic", required=True, help="Study topic (e.g. 'Photosynthesis')")
    parser.add_argument("--grade", type=int, default=10, help="Target grade level (default: 10)")
    parser.add_argument("--model", default="gemma3:1b", help="Ollama model to use")
    args = parser.parse_args()

    logger = AgentLogger()
    graph = build_graph(model=args.model, logger=logger)

    print(f"\n[MAS] Starting pipeline for topic: '{args.topic}' | Grade: {args.grade}\n")

    initial_state = {
        "topic": args.topic,
        "grade_level": args.grade,
        "syllabus": None,
        "notes": None,
        "quiz": None,
        "evaluation": None,
        "log": [],
    }

    final_state = graph.invoke(initial_state)

    print("\n[MAS] Pipeline complete. Outputs written to /outputs/")
    print(f"  Trace log: logs/trace.jsonl ({len(final_state['log'])} entries)")
    print(json.dumps({k: str(v)[:80] + "..." if isinstance(v, str) and len(str(v)) > 80 else v
                      for k, v in final_state.items() if k != "log"}, indent=2))


if __name__ == "__main__":
    main()
