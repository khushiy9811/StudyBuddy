"""Evaluation harness — Section 9 of the project plan.

Runs eval/testset.json against several (chunk size / top-k) configurations,
re-ingesting data/notes for each one, and reports:
  - retrieval hit rate   (expected source in the retrieved top-k?)
  - answer correctness   (LLM-judge, 0/1/2)
  - faithfulness         (LLM self-check: is every claim grounded in context?)
  - refusal accuracy     (trick questions correctly say "not in your notes")
  - latency              (seconds per answer)

Usage:
    python eval/run_eval.py
    python eval/run_eval.py --configs baseline tuned1   # run a subset

Requires Ollama running locally with the configured LLM/embedding models
pulled (see README.md).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import config  # noqa: E402
from backend.chains import explain, retrieve  # noqa: E402
from backend.ingestion import ingest, reset_collection  # noqa: E402
from backend.router import get_llm  # noqa: E402

TESTSET_PATH = Path(__file__).parent / "testset.json"
RESULTS_DIR = Path(__file__).parent / "results"

CONFIGS = [
    {"name": "Baseline", "chunk": 1200, "overlap": 150, "k": 3},
    {"name": "Tuned 1", "chunk": 800, "overlap": 150, "k": 4},
    {"name": "Tuned 2", "chunk": 800, "overlap": 150, "k": 4},  # same retrieval, tutor+grounding prompt (default)
    {"name": "Final", "chunk": 800, "overlap": 150, "k": 6},
]

JUDGE_PROMPT = """You are grading a student-tutor's answer against a reference answer.
Score 0, 1, or 2:
  0 = wrong or missing the key point
  1 = partially correct
  2 = correct and matches the key point of the reference

Reference answer: {reference}
Model's answer: {answer}

Reply with only the number."""

FAITHFUL_PROMPT = """Context:
{context}

Answer:
{answer}

Is every factual claim in the Answer supported by the Context above? Reply with
only "yes" or "no"."""

def judge_correctness(llm, reference: str, answer: str) -> int:
    raw = str(llm.invoke(JUDGE_PROMPT.format(reference=reference, answer=answer)))
    m = re.search(r"[0-2]", raw)
    return int(m.group(0)) if m else 0


def judge_faithfulness(llm, context: str, answer: str) -> bool:
    raw = str(llm.invoke(FAITHFUL_PROMPT.format(context=context, answer=answer))).lower()
    return "yes" in raw


def run_config(cfg: dict, testset: list[dict], judge_llm) -> dict:
    print(f"\n=== {cfg['name']} (chunk={cfg['chunk']} overlap={cfg['overlap']} k={cfg['k']}) ===")
    reset_collection()
    n_chunks = ingest(chunk_size=cfg["chunk"], chunk_overlap=cfg["overlap"])
    print(f"Indexed {n_chunks} chunks.")

    hits, correctness_scores, faithful_flags, refusals, latencies = [], [], [], [], []

    for item in testset:
        t0 = time.time()
        docs = retrieve(item["question"], cfg["k"])
        result = explain(item["question"], history="", tutor_mode=False, k=cfg["k"])
        latency = time.time() - t0
        latencies.append(latency)

        if item["trick"]:
            said_no = "not in your notes" in result.text.lower()
            refusals.append(said_no)
            continue

        got_sources = {d.metadata.get("source") for d in docs}
        hit = item["source"] in got_sources
        hits.append(hit)

        score = judge_correctness(judge_llm, item["expected_answer"], result.text)
        correctness_scores.append(score)

        context = "\n".join(d.page_content for d in docs)
        faithful_flags.append(judge_faithfulness(judge_llm, context, result.text))

    def pct(vals):
        return round(100 * sum(vals) / len(vals)) if vals else None

    def avg(vals):
        return round(sum(vals) / len(vals), 2) if vals else None

    return {
        "config": cfg["name"],
        "chunk": cfg["chunk"],
        "k": cfg["k"],
        "hit_rate": pct(hits),
        "correctness_avg_0_2": avg(correctness_scores),
        "faithful_pct": pct(faithful_flags),
        "refusal_pct": pct(refusals),
        "avg_latency_s": avg(latencies),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", nargs="*", help="Subset of config names to run (default: all)")
    args = parser.parse_args()

    testset = json.loads(TESTSET_PATH.read_text(encoding="utf-8"))
    configs = CONFIGS
    if args.configs:
        wanted = {c.lower() for c in args.configs}
        configs = [c for c in CONFIGS if c["name"].lower() in wanted]

    judge_llm = get_llm(temperature=0.0)
    rows = [run_config(cfg, testset, judge_llm) for cfg in configs]

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"results_{int(time.time())}.md"
    header = "| Config | Chunk | k | Hit rate | Correct (avg /2) | Faithful | Refusal |\n"
    header += "|---|---|---|---|---|---|---|\n"
    lines = [header]
    for r in rows:
        lines.append(
            f"| {r['config']} | {r['chunk']} | {r['k']} | {r['hit_rate']}% | "
            f"{r['correctness_avg_0_2']} | {r['faithful_pct']}% | {r['refusal_pct']}% |\n"
        )
    table = "".join(lines)
    out_path.write_text(table, encoding="utf-8")
    print("\n" + table)
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
