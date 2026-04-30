"""
tests/test_quiz_generator.py — Evaluation script for the Quiz Generator Agent (Member 3)

Covers:
    1. Unit tests for save_quiz() tool schema validation and file creation.
    2. Integration tests for quiz_generator_node() using a mock LLM.
    3. An LLM-as-a-Judge test to evaluate generated quiz logic.

Run:
    pytest tests/test_quiz_generator.py -v
    pytest tests/test_quiz_generator.py -v -k "not llm_judge"  
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.save_quiz import save_quiz


class TestSaveQuizTool(unittest.TestCase):
    
    def setUp(self):
        self.valid_mcq = {
            "id": 1,
            "type": "mcq",
            "question": "What is the powerhouse of the cell?",
            "options": ["A. Nucleus", "B. Mitochondria", "C. Ribosome", "D. ER"],
            "answer": "B",
            "topic_tag": "Cellular Respiration"
        }
        self.valid_open = {
            "id": 2,
            "type": "open",
            "question": "Explain the role of chlorophyll.",
            "options": None,
            "answer": "Chlorophyll absorbs light energy...",
            "topic_tag": "Photosynthesis"
        }

    def test_save_quiz_happy_path(self):
        questions = [self.valid_mcq, self.valid_open]
        result = save_quiz(questions)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["question_count"], 2)
        self.assertEqual(result["mcq_count"], 1)
        self.assertEqual(result["open_count"], 1)
        self.assertTrue(os.path.exists(result["path"]))

    def test_empty_list_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            save_quiz([])

    def test_missing_keys_raises_value_error(self):
        invalid_q = self.valid_mcq.copy()
        del invalid_q["topic_tag"]
        
        with self.assertRaisesRegex(ValueError, "missing required keys"):
            save_quiz([invalid_q])

    def test_mcq_incorrect_options_count(self):
        invalid_q = self.valid_mcq.copy()
        invalid_q["options"] = ["A", "B", "C"]  # Only 3 options
        
        with self.assertRaisesRegex(ValueError, "exactly 4 items"):
            save_quiz([invalid_q])

class TestQuizGeneratorIntegration(unittest.TestCase):
    
    MOCK_QUIZ_JSON = [
        {
            "id": 1,
            "type": "mcq",
            "question": "Which cycle is light-independent?",
            "options": ["A. Krebs", "B. Calvin", "C. Citric Acid", "D. Water"],
            "answer": "B",
            "topic_tag": "Calvin cycle"
        },
        {
            "id": 2,
            "type": "open",
            "question": "Describe chloroplast structure.",
            "options": None,
            "answer": "It has an inner and outer membrane...",
            "topic_tag": "Chloroplast structure"
        }
    ]

    def _make_mock_llm_response(self):
        mock_response = MagicMock()
        mock_response.content = json.dumps(self.MOCK_QUIZ_JSON)
        return mock_response

    @patch("agents.quiz_generator.ChatOllama")
    def test_quiz_generator_state_updates(self, mock_ollama_class):
        from agents.quiz_generator import quiz_generator_node
        from logger import AgentLogger
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = self._make_mock_llm_response()
        mock_ollama_class.return_value = mock_instance

        logger = AgentLogger()
        initial_state = {
            "topic": "Photosynthesis",
            "grade_level": 10,
            "syllabus": {"subtopics": ["Calvin cycle", "Chloroplast structure"]},
            "notes": "Mocked study notes about photosynthesis...",
            "quiz": None,
            "evaluation": None,
            "log": [],
        }

        result = quiz_generator_node(initial_state, model="gemma3:1b", logger=logger)

        self.assertIn("quiz", result)
        self.assertEqual(len(result["quiz"]), 2)
        
        # Check logs
        self.assertEqual(len(result["log"]), 1)
        entry = result["log"][0]
        self.assertEqual(entry["agent"], "quiz_generator")
        self.assertIn("save_quiz", entry["tool_calls"])
        self.assertIn("prepare_answer_sheet", entry["tool_calls"])

class TestQuizGeneratorLLMJudge(unittest.TestCase):

    def _is_ollama_available(self) -> bool:
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def test_llm_judge_quiz_quality(self):
        if not self._is_ollama_available():
            self.skipTest("Ollama not running locally — skipping LLM-as-judge test")

        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        from agents.quiz_generator import quiz_generator_node

        # Run real quiz generator using dummy notes
        initial_state = {
            "topic": "Python Basics",
            "grade_level": 10,
            "syllabus": {"subtopics": ["Data Types"]},
            "notes": "Integers are whole numbers. Strings are text enclosed in quotes.",
            "quiz": None,
            "log": [],
        }
        
        result = quiz_generator_node(initial_state, model="gemma3:1b")
        quiz = result["quiz"]

        judge_system = (
            "You are an educational quality evaluator. Respond ONLY with valid JSON: "
            '{"verdict": "PASS" | "FAIL", "reason": "<short explanation>"}'
        )
        judge_user = (
            f"Evaluate this quiz generation based on the topic 'Python Basics'.\n"
            f"Quiz: {json.dumps(quiz)}\n\n"
            "PASS if: The questions are relevant to programming and the options are plausible distractors.\n"
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
        self.assertEqual(verdict.get("verdict"), "PASS", f"LLM judge FAILED the quiz: {verdict.get('reason')}")

if __name__ == "__main__":
    unittest.main(verbosity=2)