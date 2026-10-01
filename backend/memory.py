"""Weak-topic memory (S1) + progress stats, persisted locally as JSON.

A real deployment would keep this in a database keyed by user/session; a flat
file is enough for a single-user local tutor and keeps the stretch goal simple.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from backend import config

STORE_PATH = config.DATA_DIR / "progress.json"

_DEFAULT = {"topics": {}, "quizzes": []}


def _load() -> dict:
    if not STORE_PATH.exists():
        return json.loads(json.dumps(_DEFAULT))
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_answer(topic: str, correct: bool) -> None:
    data = _load()
    t = data["topics"].setdefault(topic, {"correct": 0, "total": 0})
    t["total"] += 1
    if correct:
        t["correct"] += 1
    _save(data)


def record_quiz(topic: str, score_pct: float) -> None:
    data = _load()
    data["quizzes"].append(
        {"topic": topic, "score": score_pct, "date": date.today().isoformat()}
    )
    _save(data)


def weak_topics() -> dict[str, int]:
    """topic -> mastery % (rounded), lower is weaker."""
    data = _load()
    out = {}
    for topic, stats in data["topics"].items():
        total = stats.get("total", 0)
        pct = round(100 * stats.get("correct", 0) / total) if total else 0
        out[topic] = pct
    return out


def activity_last_n_days(n: int = 7) -> dict[str, int]:
    """date (M/D) -> number of quiz questions answered that day, oldest first."""
    data = _load()
    counts: dict[str, int] = {}
    for q in data["quizzes"]:
        counts[q["date"]] = counts.get(q["date"], 0) + 1

    out = {}
    cursor = date.today() - timedelta(days=n - 1)
    for _ in range(n):
        iso = cursor.isoformat()
        out[f"{cursor.month}/{cursor.day}"] = counts.get(iso, 0)
        cursor += timedelta(days=1)
    return out


def get_stats() -> dict:
    data = _load()
    quizzes = data["quizzes"]
    avg = round(sum(q["score"] for q in quizzes) / len(quizzes)) if quizzes else 0
    w = weak_topics()
    weak_count = sum(1 for pct in w.values() if pct < 70)

    quiz_dates = {q["date"] for q in quizzes}
    streak = 0
    cursor = date.today()
    while cursor.isoformat() in quiz_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "quizzes": len(quizzes),
        "avg_score": avg,
        "streak_days": streak,
        "weak_count": weak_count,
        "topic_mastery": w,
    }
