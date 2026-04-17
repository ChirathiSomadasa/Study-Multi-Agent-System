"""
tests/test_coordinator.py — Evaluation script for the Coordinator Agent (Member 1)

Covers:
    1. Unit tests for validate_topic() tool (property-style, deterministic).
    2. Integration tests for coordinator_node() using a mock LLM.
    3. An LLM-as-a-Judge test that runs the REAL Ollama model and checks output quality.

Run:
    pytest tests/test_coordinator.py -v
    pytest tests/test_coordinator.py -v -k "not llm_judge"  # skip slow LLM tests
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.validate_topic import validate_topic, ValidationResult


# ═══════════════════════════════════════════════════════════════════════════
# 1. Unit tests — validate_topic() tool
# ═══════════════════════════════════════════════════════════════════════════

class TestValidateTopicHappyPath(unittest.TestCase):
    """Valid topics should be accepted and categorised correctly."""

    def test_biology_topic(self) -> None:
        result = validate_topic("Photosynthesis", grade_level=10)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["category"], "biology")
        self.assertEqual(result["normalised_topic"], "Photosynthesis")

    def test_physics_topic(self) -> None:
        result = validate_topic("force and motion", grade_level=9)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["category"], "physics")

    def test_chemistry_topic(self) -> None:
        result = validate_topic("Chemical bonding and molecular structure", grade_level=11)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["category"], "chemistry")

    def test_general_category_for_unrecognised(self) -> None:
        result = validate_topic("The French Revolution", grade_level=8)
        self.assertTrue(result["is_valid"])
        # May match "history" or "general" — either is acceptable
        self.assertIn(result["category"], ["history", "general"])

    def test_normalisation_strips_and_title_cases(self) -> None:
        result = validate_topic("  photosynthesis  ", grade_level=10)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["normalised_topic"], "Photosynthesis")

    def test_minimum_grade_boundary(self) -> None:
        result = validate_topic("Counting and Numbers", grade_level=1)
        self.assertTrue(result["is_valid"])

    def test_maximum_grade_boundary(self) -> None:
        result = validate_topic("Advanced Calculus", grade_level=13)
        self.assertTrue(result["is_valid"])


class TestValidateTopicRejections(unittest.TestCase):
    """Invalid topics should be rejected with helpful messages."""

    def test_empty_string_rejected(self) -> None:
        result = validate_topic("", grade_level=10)
        self.assertFalse(result["is_valid"])
        self.assertIn("empty", result["reason"].lower())

    def test_whitespace_only_rejected(self) -> None:
        result = validate_topic("   ", grade_level=10)
        self.assertFalse(result["is_valid"])

    def test_too_short_rejected(self) -> None:
        result = validate_topic("AB", grade_level=10)
        self.assertFalse(result["is_valid"])
        self.assertIn("short", result["reason"].lower())

    def test_punctuation_only_rejected(self) -> None:
        result = validate_topic("!!!???", grade_level=10)
        self.assertFalse(result["is_valid"])

    def test_topic_too_long_rejected(self) -> None:
        long_topic = "A" * 121
        result = validate_topic(long_topic, grade_level=10)
        self.assertFalse(result["is_valid"])
        self.assertIn("long", result["reason"].lower())


class TestValidateTopicTypeErrors(unittest.TestCase):
    """Invalid argument types should raise TypeError or ValueError."""

    def test_non_string_topic_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            validate_topic(123, grade_level=10)  # type: ignore[arg-type]

    def test_none_topic_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            validate_topic(None, grade_level=10)  # type: ignore[arg-type]

    def test_grade_below_range_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            validate_topic("Photosynthesis", grade_level=0)

    def test_grade_above_range_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            validate_topic("Photosynthesis", grade_level=14)

    def test_grade_float_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            validate_topic("Photosynthesis", grade_level=10.5)  # type: ignore[arg-type]


# ═══════════════════════════════════════════════════════════════════════════
# 2. Integration tests — coordinator_node() with mocked LLM
# ═══════════════════════════════════════════════════════════════════════════

class TestCoordinatorNodeIntegration(unittest.TestCase):
    """Test the coordinator node with a deterministic mock LLM."""

    MOCK_SYLLABUS = {
        "topic": "Photosynthesis",
        "validated": True,
        "error": None,
        "subtopics": [
            "Chloroplast structure",
            "Light-dependent reactions",
            "Calvin cycle",
            "Factors affecting photosynthesis",
        ],
        "learning_objectives": [
            "Explain the structure of a chloroplast",
            "Describe the light-dependent reactions",
            "Explain the Calvin cycle steps",
            "Identify factors that affect photosynthesis",
        ],
    }

    def _make_mock_llm_response(self) -> MagicMock:
        mock_response = MagicMock()
        mock_response.content = json.dumps(self.MOCK_SYLLABUS)
        return mock_response

    @patch("agents.coordinator.ChatOllama")
    def test_coordinator_returns_syllabus(self, mock_ollama_class: MagicMock) -> None:
        from agents.coordinator import coordinator_node

        mock_instance = MagicMock()
        mock_instance.invoke.return_value = self._make_mock_llm_response()
        mock_ollama_class.return_value = mock_instance

        initial_state = {
            "topic": "Photosynthesis",
            "grade_level": 10,
            "syllabus": None,
            "notes": None,
            "quiz": None,
            "evaluation": None,
            "log": [],
        }

        result = coordinator_node(initial_state, model="gemma3:1b")

        self.assertIn("syllabus", result)
        self.assertTrue(result["syllabus"]["validated"])
        self.assertEqual(len(result["syllabus"]["subtopics"]), 4)

    @patch("agents.coordinator.ChatOllama")
    def test_coordinator_writes_syllabus_file(self, mock_ollama_class: MagicMock) -> None:
        from agents.coordinator import coordinator_node

        mock_instance = MagicMock()
        mock_instance.invoke.return_value = self._make_mock_llm_response()
        mock_ollama_class.return_value = mock_instance

        initial_state = {
            "topic": "Photosynthesis",
            "grade_level": 10,
            "syllabus": None,
            "notes": None,
            "quiz": None,
            "evaluation": None,
            "log": [],
        }

        coordinator_node(initial_state, model="gemma3:1b")

        out_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "syllabus.json")
        self.assertTrue(os.path.exists(out_path), "syllabus.json should be written to outputs/")

        with open(out_path) as f:
            saved = json.load(f)
        self.assertEqual(saved["topic"], "Photosynthesis")

    @patch("agents.coordinator.ChatOllama")
    def test_coordinator_appends_log_entry(self, mock_ollama_class: MagicMock) -> None:
        from agents.coordinator import coordinator_node
        from logger import AgentLogger

        mock_instance = MagicMock()
        mock_instance.invoke.return_value = self._make_mock_llm_response()
        mock_ollama_class.return_value = mock_instance

        logger = AgentLogger()
        initial_state = {
            "topic": "Photosynthesis",
            "grade_level": 10,
            "syllabus": None,
            "notes": None,
            "quiz": None,
            "evaluation": None,
            "log": [],
        }

        result = coordinator_node(initial_state, model="gemma3:1b", logger=logger)

        self.assertEqual(len(result["log"]), 1)
        entry = result["log"][0]
        self.assertEqual(entry["agent"], "coordinator")
        self.assertIn("validate_topic", entry["tool_calls"])
        self.assertIn("syllabus", entry["output_keys"])
        self.assertGreater(entry["latency_ms"], 0)

    @patch("agents.coordinator.ChatOllama")
    def test_coordinator_raises_on_invalid_topic(self, mock_ollama_class: MagicMock) -> None:
        from agents.coordinator import coordinator_node

        initial_state = {
            "topic": "   ",   # empty whitespace — should fail validation
            "grade_level": 10,
            "syllabus": None,
            "notes": None,
            "quiz": None,
            "evaluation": None,
            "log": [],
        }

        with self.assertRaises(ValueError):
            coordinator_node(initial_state, model="gemma3:1b")


# ═══════════════════════════════════════════════════════════════════════════
# 3. LLM-as-a-Judge test (requires Ollama running locally)
# ═══════════════════════════════════════════════════════════════════════════

class TestCoordinatorLLMJudge(unittest.TestCase):
    """
    Slow integration test: runs the REAL Ollama model and uses a second LLM
    call to judge whether the output syllabus is academically appropriate.

    Skip with: pytest -k "not llm_judge"
    """

    def _is_ollama_available(self) -> bool:
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def test_llm_judge_syllabus_quality(self) -> None:
        """Judge that the syllabus is relevant, structured, and age-appropriate."""
        if not self._is_ollama_available():
            self.skipTest("Ollama not running locally — skipping LLM-as-judge test")

        from langchain_community.chat_models import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        from agents.coordinator import coordinator_node

        # Run the real coordinator
        initial_state = {
            "topic": "Photosynthesis",
            "grade_level": 10,
            "syllabus": None,
            "notes": None,
            "quiz": None,
            "evaluation": None,
            "log": [],
        }
        result = coordinator_node(initial_state, model="gemma3:1b")
        syllabus = result["syllabus"]

        # Build judge prompt
        judge_system = (
            "You are an educational quality evaluator. "
            "Respond ONLY with valid JSON: "
            '{"verdict": "PASS" | "FAIL", "reason": "<one sentence>"}'
        )
        judge_user = (
            f"Evaluate this syllabus for a Grade 10 class studying '{syllabus['topic']}'.\n"
            f"Subtopics: {syllabus['subtopics']}\n"
            f"Learning objectives: {syllabus['learning_objectives']}\n\n"
            "PASS if: subtopics are relevant, objectives use action verbs, "
            "content is appropriate for Grade 10.\n"
            "FAIL otherwise."
        )

        judge_llm = ChatOllama(model="gemma3:1b", temperature=0)
        response = judge_llm.invoke([
            SystemMessage(content=judge_system),
            HumanMessage(content=judge_user),
        ])

        import re
        raw = response.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        self.assertIsNotNone(match, f"Judge did not return JSON: {raw}")

        verdict = json.loads(match.group())
        self.assertEqual(
            verdict.get("verdict"),
            "PASS",
            f"LLM judge FAILED the syllabus: {verdict.get('reason')}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
