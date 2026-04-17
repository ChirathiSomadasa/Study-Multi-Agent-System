"""
tests/test_evaluator.py — Evaluation script for the Evaluator Agent (Member 4)

TODO (Member 4): Replace this stub with real tests.

Your test file must cover:
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

import unittest


class TestEvaluatorStub(unittest.TestCase):
    def test_stub(self) -> None:
        self.skipTest("Member 4: replace this stub with real tests")


if __name__ == "__main__":
    unittest.main()
