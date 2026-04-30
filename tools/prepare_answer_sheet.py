"""
tools/prepare_answer_sheet.py — Create a student answer template.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict
import json
import os


class PrepareAnswerSheetResult(TypedDict):
	path: str
	question_count: int
	created: bool
	success: bool


def prepare_answer_sheet(
	questions: list[dict[str, Any]],
	quiz_path: Optional[str] = None,
	answer_path: Optional[str] = None,
) -> PrepareAnswerSheetResult:
	
	"""
	Create an answer.json template for students to fill in.

	The file is only overwritten when it is older than quiz.json or missing.
	"""
	
	if not questions:
		raise ValueError("questions list must not be empty")

	out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
	resolved_answer_path = answer_path or os.path.join(out_dir, "answer.json")
	resolved_quiz_path = quiz_path or os.path.join(out_dir, "quiz.json")

	quiz_mtime = os.path.getmtime(resolved_quiz_path) if os.path.exists(resolved_quiz_path) else None
	if quiz_mtime is not None and os.path.exists(resolved_answer_path):
		if os.path.getmtime(resolved_answer_path) >= quiz_mtime:
			return PrepareAnswerSheetResult(
				path=resolved_answer_path,
				question_count=len(questions),
				created=False,
				success=True,
			)

	answer_rows: list[dict[str, Any]] = []
	for idx, q in enumerate(questions, start=1):
		qid = q.get("id", idx)
		answer_rows.append(
			{
				"id": qid,
				"question": q.get("question", ""),
				"answer": "",
			}
		)

	os.makedirs(out_dir, exist_ok=True)
	with open(resolved_answer_path, "w", encoding="utf-8") as f:
		json.dump(answer_rows, f, indent=2)
	if quiz_mtime is not None:
		os.utime(resolved_answer_path, (quiz_mtime, quiz_mtime))

	return PrepareAnswerSheetResult(
		path=resolved_answer_path,
		question_count=len(questions),
		created=True,
		success=True,
	)
