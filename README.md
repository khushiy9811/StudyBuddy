# StudyBuddy AI

Implementation of `StudyBuddy_Project_Plan.md`: a grounded, local AI tutor over
your own notes (F1–F6): upload → ask/explain (Socratic tutor) → quiz →
citations & "not in your notes" refusal → evaluation harness.

## A note on Langflow

The plan calls for building the flow visually in Langflow. Langflow is a GUI
tool with no scriptable way to click through its canvas, so this repo
implements the **same flow graph, in code**, with LangChain (the library
Langflow itself is built on):

```
Flow A (ingestion):  backend/ingestion.py
Flow B (chat/router): backend/router.py + backend/chains.py
Quiz + grading:        backend/quiz.py
Weak-topic memory (S1): backend/memory.py
```

This keeps every prompt, chunk size, and top-k value from Sections 5–6 of the
plan intact and testable end-to-end without a GUI. If you want the literal
Langflow canvas too, you can rebuild the same graph visually and point
`app.py` at its `/api/v1/run/<flow_id>` endpoint instead — this was the
original starter code in Section 8, kept as `app.py`'s design reference.

## Prerequisites (manual — not automatable from here)

1. **Ollama** — install from https://ollama.com, then:
   ```bash
   ollama pull phi3:mini
   ollama pull nomic-embed-text
   ollama serve   # if it isn't already running as a service
   ```
2. **Python 3.10+**

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # optional, defaults already match the plan
```

## Run

```bash
streamlit run app.py
```

Open the **Library** page first, upload PDFs/`.txt`/`.md` notes (five sample
DBMS notes files — Normalization, ER Model, SQL Basics, Joins, Indexing — are
already in `data/notes/` so you can try it immediately), then click
**Index documents**. Then use **Learn** to chat, **Quiz** to test yourself,
and **Progress** to see weak topics.

Or index from the CLI:

```bash
python scripts/ingest.py
```

## Evaluation

```bash
python eval/run_eval.py
```

Runs `eval/testset.json` (25 grounded questions + 5 "trick" questions with no
answer in the notes) against the four configs from Section 9 of the plan
(Baseline / Tuned 1 / Tuned 2 / Final), re-ingesting `data/notes` for each
chunk size. Writes a results table to `eval/results/results_<timestamp>.md`
— paste it into Section 9 of your write-up.

Metrics: retrieval hit rate, LLM-judged correctness (0–2), a lightweight
LLM self-check faithfulness proxy (swap in RAGAS for something more rigorous),
and refusal accuracy on the trick questions.

## Project layout

```
app.py                  Streamlit UI (Section 7/8)
backend/
  config.py              env-driven settings (chunk size, top-k, temperature, models)
  prompts.py              Section 6 prompt templates
  ingestion.py             Flow A
  router.py                intent classifier (F2)
  chains.py                Flow B dispatch: explain / summarize / plan
  quiz.py                   quiz generation + grading, JSON parse-with-retry (F4)
  memory.py                 weak-topic tracking + progress stats (S1)
data/notes/               drop PDFs/txt/md here (sample DBMS notes included)
data/chroma/               persisted vector store (created at runtime)
data/progress.json         quiz history / weak topics (created at runtime)
eval/
  testset.json              20–30 question test set incl. 5 trick questions
  run_eval.py                Section 9 evaluation harness
scripts/ingest.py           CLI ingestion
```

## What's not built (stretch / out of scope here)

- **S2 study planner** persistence beyond a single generated table (the
  `plan` intent generates one; there's no exam-date/calendar storage).
- **S4 MCP/API export** — not implemented.
- Faithfulness uses a simple LLM self-check, not full RAGAS (heavy extra
  dependency); see `eval/run_eval.py` if you want to swap it in.
