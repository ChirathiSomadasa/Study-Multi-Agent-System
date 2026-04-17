"""
logger.py — AgentOps/LLMOps trace logger for the Study MAS.

Every agent node calls logger.log_entry() to record:
    - which agent ran
    - what keys it read from state
    - which tools it called
    - what keys it wrote to state
    - wall-clock latency in milliseconds

Entries are written to logs/trace.jsonl (one JSON object per line).
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional


LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trace.jsonl")


class AgentLogger:
    """Append-only JSONL trace logger. Thread-safe for single-process use."""

    def __init__(self) -> None:
        os.makedirs(LOG_DIR, exist_ok=True)
        # Truncate log file at the start of each run
        open(LOG_FILE, "w").close()

    def log_entry(
        self,
        agent: str,
        input_keys: list[str],
        tool_calls: list[str],
        output_keys: list[str],
        latency_ms: float,
        extra: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Record one trace entry and append it to logs/trace.jsonl.

        Args:
            agent:       Name of the agent node (e.g. "coordinator").
            input_keys:  State keys this agent READ from state.
            tool_calls:  Names of tools invoked (e.g. ["validate_topic"]).
            output_keys: State keys this agent WROTE to state.
            latency_ms:  Wall-clock time for this node in milliseconds.
            extra:       Any additional metadata (token counts, etc.).

        Returns:
            The trace entry dict (also appended to the shared state log[]).
        """
        entry: dict[str, Any] = {
            "agent": agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_keys": input_keys,
            "tool_calls": tool_calls,
            "output_keys": output_keys,
            "latency_ms": round(latency_ms, 2),
        }
        if extra:
            entry["extra"] = extra

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

        print(
            f"  [LOG] {agent:20s} | tools={tool_calls} | "
            f"out={output_keys} | {latency_ms:.0f}ms"
        )
        return entry

    @staticmethod
    def start_timer() -> float:
        """Return current time in seconds (use with elapsed_ms)."""
        return time.perf_counter()

    @staticmethod
    def elapsed_ms(start: float) -> float:
        """Compute elapsed milliseconds since start."""
        return (time.perf_counter() - start) * 1000
