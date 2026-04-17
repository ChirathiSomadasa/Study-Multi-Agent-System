"""
tests/test_quiz_generator.py — Evaluation script for the Quiz Generator Agent (Member 3)

TODO (Member 3): Replace this stub with real tests.

Your test file must cover:
    1. Unit tests for save_quiz() tool:
       - Empty list raises ValueError
       - Writes quiz.json to outputs/
       - Returns correct MCQ/open counts
       - Malformed question dict raises ValueError

    2. Integration tests for quiz_generator_node() with mocked LLM:
       - Returns list of dicts in state["quiz"]
       - Each question has id, type, question, options, answer, topic_tag
       - MCQ questions have exactly 4 options
       - At least 1 MCQ and 1 open question present
       - Appends a log entry to state["log"]

    3. LLM-as-Judge test (real Ollama):
       - Judge checks questions are relevant to the topic
       - Judge checks MCQ options are plausible distractors
"""

import unittest


class TestQuizGeneratorStub(unittest.TestCase):
    def test_stub(self) -> None:
        self.skipTest("Member 3: replace this stub with real tests")


if __name__ == "__main__":
    unittest.main()
