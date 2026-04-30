"""
tools/load_answers.py — Load student answers from outputs/answer.json.

Enforces a deadline relative to outputs/quiz.json so answers must be updated
within a fixed window after quiz generation.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict
from datetime import datetime, timezone
import json
import os
import time


class LoadAnswersResult(TypedDict):
	answers: list[dict[str, Any]]
	answer_map: dict[int, str]
	missing_ids: list[int]
	answer_path: str
	deadline_iso: str
	updated_after_quiz: bool
	success: bool


def load_student_answers(
	quiz: list[dict[str, Any]],
	deadline_minutes: int = 60,
	answer_path: Optional[str] = None,
	quiz_path: Optional[str] = None,
	wait_for_update: bool = True,
	poll_interval_seconds: int = 5,
) -> LoadAnswersResult:
	
	"""
	Load student answers and validate update timing.

	Args:
		quiz: List of quiz questions (used to align answers).
		deadline_minutes: Time window after quiz generation to accept answers.
		answer_path: Optional path to answer.json.
		quiz_path: Optional path to quiz.json.
		wait_for_update: If True, poll until answers are updated or deadline hits.
		poll_interval_seconds: Sleep between polls when waiting.

	Raises:
		FileNotFoundError: If quiz.json or answer.json is missing.
		ValueError: If answer.json is not updated after quiz.json.
		TimeoutError: If the update deadline has passed.
	"""
	
	if not quiz:
		raise ValueError("quiz list must not be empty")
	if deadline_minutes <= 0:
		raise ValueError("deadline_minutes must be greater than 0")
	if poll_interval_seconds <= 0:
		raise ValueError("poll_interval_seconds must be greater than 0")

	out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
	resolved_answer_path = answer_path or os.path.join(out_dir, "answer.json")
	resolved_quiz_path = quiz_path or os.path.join(out_dir, "quiz.json")

	if not os.path.exists(resolved_quiz_path):
		raise FileNotFoundError(f"quiz.json not found at {resolved_quiz_path}")

	quiz_mtime = os.path.getmtime(resolved_quiz_path)
	deadline_ts = quiz_mtime + (deadline_minutes * 60)
	deadline_iso = datetime.fromtimestamp(deadline_ts, tz=timezone.utc).isoformat()

	updated_after_quiz = False
	while True:
		if os.path.exists(resolved_answer_path):
			answer_mtime = os.path.getmtime(resolved_answer_path)
			updated_after_quiz = answer_mtime > quiz_mtime
			if updated_after_quiz:
				break
		if time.time() > deadline_ts:
			raise TimeoutError(
				"Answer deadline exceeded. Regenerate the quiz and submit answers "
				"within 60 minutes."
			)
		if not wait_for_update:
			if not os.path.exists(resolved_answer_path):
				raise FileNotFoundError(
					"answer.json not found. Update it before the deadline: "
					f"{deadline_iso}"
				)
			raise ValueError(
				"answer.json has not been updated after quiz generation. "
				f"Please update it before the deadline: {deadline_iso}"
			)
		time.sleep(poll_interval_seconds)

	with open(resolved_answer_path, "r", encoding="utf-8") as f:
		raw = json.load(f)

	if isinstance(raw, dict):
		raw_list = [raw]
	elif isinstance(raw, list):
		raw_list = raw
	else:
		raise ValueError("answer.json must be a JSON array or object")

	answer_map: dict[int, str] = {}
	for item in raw_list:
		if not isinstance(item, dict):
			continue
		if "id" not in item:
			continue
		raw_id = item.get("id")
		if isinstance(raw_id, bool):
			continue
		try:
			qid = int(raw_id)
		except (TypeError, ValueError):
			continue
		answer_val = item.get("answer", "")
		answer_map[qid] = "" if answer_val is None else str(answer_val)

	answers: list[dict[str, Any]] = []
	missing_ids: list[int] = []
	for idx, q in enumerate(quiz, start=1):
		raw_id = q.get("id", idx)
		if isinstance(raw_id, bool):
			qid = idx
		else:
			try:
				qid = int(raw_id)
			except (TypeError, ValueError):
				qid = idx
		if qid not in answer_map:
			missing_ids.append(qid)
		answers.append({"id": qid, "answer": answer_map.get(qid, "")})

	return LoadAnswersResult(
		answers=answers,
		answer_map=answer_map,
		missing_ids=missing_ids,
		answer_path=resolved_answer_path,
		deadline_iso=deadline_iso,
		updated_after_quiz=updated_after_quiz,
		success=True,
	)
