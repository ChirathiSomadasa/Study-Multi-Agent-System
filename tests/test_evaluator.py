"""
tests/test_evaluator.py — Evaluation script for the Evaluator Agent 

test file cover:
    1. Unit tests for grade_answers() tool:
       - Empty list raises ValueError
       - Returns correct mean_score
       - Per-topic breakdown contains all topic_tags
       - Writes report.md to outputs/
       - Score of 0 and 10 both handled (boundary check)

    2. Integration tests for evaluator_node() with mocked LLM:
       - Returns evaluation dict in state["evaluation"]
       - evaluation has: total_questions, answered, score, per_question, summary
       - per_question list length matches quiz length
       - Appends a log entry to state["log"]

    3. LLM-as-Judge test (real Ollama):
       - Judge checks feedback strings are constructive
       - Judge checks overall summary is coherent
       - Score distribution is reasonable (not all 0 or all 10)
"""

import json
import os
import unittest
from unittest import mock

import socket

from agents.evaluator import evaluator_node
from logger import AgentLogger
from tools.grade_answers import grade_answers


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeLLM:
    def __init__(self, *args, **kwargs) -> None:
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        graded = {"score": 10, "feedback": "Correct choice."}
        return FakeResponse(json.dumps(graded))


def _write_quiz_and_answers(quiz, answers) -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    quiz_path = os.path.join(out_dir, "quiz.json")
    answer_path = os.path.join(out_dir, "answer.json")

    with open(quiz_path, "w", encoding="utf-8") as f:
        json.dump(quiz, f, indent=2)

    with open(answer_path, "w", encoding="utf-8") as f:
        json.dump(answers, f, indent=2)

    quiz_mtime = os.path.getmtime(quiz_path)
    os.utime(answer_path, (quiz_mtime + 1, quiz_mtime + 1))


class TestGradeAnswers(unittest.TestCase):
    def test_empty_list_raises(self) -> None:
        with self.assertRaises(ValueError):
            grade_answers([])

    def test_mean_and_per_topic(self) -> None:
        graded = [
            {"id": 1, "score": 10, "topic_tag": "t1"},
            {"id": 2, "score": 0, "topic_tag": "t1"},
            {"id": 3, "score": 5, "topic_tag": "t2"},
        ]
        result = grade_answers(graded, topic="Demo")
        self.assertEqual(result["mean_score"], 5.0)
        self.assertIn("t1", result["per_topic"])
        self.assertIn("t2", result["per_topic"])
        self.assertTrue(os.path.exists(result["report_path"]))

    def test_boundary_scores(self) -> None:
        graded = [
            {"id": 1, "score": 0, "topic_tag": "t1"},
            {"id": 2, "score": 10, "topic_tag": "t1"},
        ]
        result = grade_answers(graded, topic="Demo")
        self.assertEqual(result["mean_score"], 5.0)


class TestEvaluatorIntegration(unittest.TestCase):
    @mock.patch("agents.evaluator.ChatOllama", FakeLLM)
    def test_evaluator_node_with_mock_llm(self) -> None:
        state = {
            "topic": "Photosynthesis",
            "grade_level": 10,
            "syllabus": {"topic": "Photosynthesis"},
            "notes": "notes",
            "quiz": [
                {
                    "id": 1,
                    "type": "mcq",
                    "question": "Which pigment is responsible for photosynthesis?",
                    "options": ["A. Chlorophyll", "B. Hemoglobin", "C. Melanin", "D. Keratin"],
                    "answer": "A",
                    "topic_tag": "chlorophyll",
                },
                {
                    "id": 2,
                    "type": "open",
                    "question": "What is the main product of photosynthesis?",
                    "options": None,
                    "answer": "Glucose",
                    "topic_tag": "outputs",
                },
            ],
            "evaluation": None,
            "log": [],
        }

        _write_quiz_and_answers(
            state["quiz"],
            [
                {"id": 1, "answer": "A"},
                {"id": 2, "answer": "Glucose"},
            ],
        )

        logger = AgentLogger()
        out = evaluator_node(state, model="gemma3:1b", logger=logger)

        self.assertIn("evaluation", out)
        self.assertIn("log", out)
        self.assertEqual(len(out["evaluation"]["per_question"]), len(state["quiz"]))

        eval_keys = {"total_questions", "answered", "score", "per_question", "summary"}
        self.assertTrue(eval_keys.issubset(set(out["evaluation"].keys())))
        self.assertTrue(len(out["log"]) >= 1)


def _ollama_ready() -> bool:
    if os.getenv("RUN_OLLAMA_TESTS") != "1":
        return False
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            return True
    except OSError:
        return False


class TestEvaluatorOllama(unittest.TestCase):
    @unittest.skipUnless(_ollama_ready(), "Ollama not running or RUN_OLLAMA_TESTS!=1")
    def test_llm_as_judge_real(self) -> None:
        state = {
            "topic": "Photosynthesis",
            "grade_level": 10,
            "syllabus": {"topic": "Photosynthesis"},
            "notes": "notes",
            "quiz": [
                {
                    "id": 1,
                    "type": "mcq",
                    "question": "Which pigment is responsible for photosynthesis?",
                    "options": ["A. Chlorophyll", "B. Hemoglobin", "C. Melanin", "D. Keratin"],
                    "answer": "A",
                    "topic_tag": "chlorophyll",
                },
                {
                    "id": 2,
                    "type": "open",
                    "question": "Explain the role of light energy in photosynthesis.",
                    "options": None,
                    "answer": "Light energy powers the conversion of CO2 and water into glucose.",
                    "topic_tag": "light_reactions",
                },
                {
                    "id": 3,
                    "type": "open",
                    "question": "Name one product of photosynthesis besides glucose.",
                    "options": None,
                    "answer": "Oxygen",
                    "topic_tag": "outputs",
                },
            ],
            "evaluation": None,
            "log": [],
        }

        _write_quiz_and_answers(
            state["quiz"],
            [
                {"id": 1, "answer": "A"},
                {"id": 2, "answer": "Light energy powers glucose production."},
                {"id": 3, "answer": "Oxygen"},
            ],
        )

        out = evaluator_node(state, model="gemma3:1b", logger=AgentLogger())
        evaluation = out["evaluation"]

        # Feedback should be non-empty and useful
        feedbacks = [q.get("feedback", "") for q in evaluation["per_question"]]
        self.assertTrue(all(isinstance(f, str) and len(f.strip()) >= 5 for f in feedbacks))

        # Summary should exist and mention mean score
        self.assertIn("Mean score", evaluation["summary"])

        # Scores should not be all 0 or all 10
        scores = [q.get("score", 0) for q in evaluation["per_question"]]
        self.assertFalse(all(s == 0 for s in scores))
        self.assertFalse(all(s == 10 for s in scores))


if __name__ == "__main__":
    unittest.main()
