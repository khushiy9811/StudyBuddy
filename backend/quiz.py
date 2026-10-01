"""Quiz generation + grading (F4). JSON output with a retry-on-invalid-JSON
guard, per the Risks & Mitigations table ("Quiz JSON breaks -> output parser
plus a retry").
"""
from __future__ import annotations

import json
import re

from langchain_core.prompts import PromptTemplate

from backend import config
from backend.chains import format_context, retrieve
from backend.prompts import GRADING_PROMPT, QUIZ_PROMPT
from backend.router import get_llm

_JSON_ARRAY = re.compile(r"\[.*\]", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str, pattern: re.Pattern):
    match = pattern.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def generate_quiz(topic: str, retries: int = 1) -> list[dict]:
    docs = retrieve(topic, config.TOP_K["quiz"])
    if not docs:
        return []
    context = format_context(docs)
    prompt = PromptTemplate.from_template(QUIZ_PROMPT).format(topic=topic, context=context)
    llm = get_llm(temperature=config.TEMPERATURE["quiz"])

    for attempt in range(retries + 1):
        raw = str(llm.invoke(prompt))
        parsed = _extract_json(raw, _JSON_ARRAY)
        if isinstance(parsed, list):
            return [q for q in parsed if isinstance(q, dict) and "q" in q]
        # Retry once with a stricter nudge if parsing failed.
        prompt = prompt + "\n\nReturn ONLY the JSON array, nothing else."
    return []


def grade_answer(question: dict, student_answer: str, retries: int = 1) -> dict:
    topic = question.get("source") or question.get("topic") or ""
    prompt = PromptTemplate.from_template(GRADING_PROMPT).format(
        q=question.get("q", ""),
        answer=question.get("answer", ""),
        student_answer=student_answer,
        topic=topic,
    )
    llm = get_llm(temperature=0.0)

    for attempt in range(retries + 1):
        raw = str(llm.invoke(prompt))
        parsed = _extract_json(raw, _JSON_OBJECT)
        if isinstance(parsed, dict) and "correct" in parsed:
            parsed.setdefault("topic", topic)
            return parsed
        prompt = prompt + "\n\nReturn ONLY the JSON object, nothing else."

    # Fallback: exact-match heuristic so grading never hard-fails.
    fallback_correct = student_answer.strip().lower() == str(question.get("answer", "")).strip().lower()
    return {"correct": fallback_correct, "feedback": "Auto-graded by exact match (LLM grading failed).", "topic": topic}
