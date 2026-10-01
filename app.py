"""StudyBuddy AI — Streamlit front end.

Talks to the local backend package directly (backend/chains.py, quiz.py,
ingestion.py, memory.py) instead of a Langflow HTTP endpoint — see the README
for why. Layout + visual design follow Section 7 of StudyBuddy_Project_Plan.md
(design tokens in 7.5: accent #4F46E5/#818CF8, success/warning/danger, Inter
font, 12px card corners).
"""
import os
import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend import config, memory  # noqa: E402
from backend.chains import chat  # noqa: E402
from backend.ingestion import ingest  # noqa: E402
from backend.quiz import generate_quiz, grade_answer  # noqa: E402

st.set_page_config(page_title="StudyBuddy", page_icon="\U0001F393", layout="wide")

# ---------- styling (Section 7.5 design tokens) ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono&display=swap');

:root {
  --bg: #F8FAFC; --surface: #FFFFFF; --text: #0F172A; --muted: #64748B;
  --accent: #4F46E5; --accent-soft: rgba(79,70,229,.10); --accent-strong: #4338CA;
  --success: #16A34A; --success-soft: rgba(22,163,74,.12);
  --warning: #D97706; --warning-soft: rgba(217,119,6,.12);
  --danger: #DC2626; --danger-soft: rgba(220,38,38,.12);
  --border: rgba(100,116,139,.16);
  --shadow: 0 1px 3px rgba(15,23,42,.06), 0 1px 2px rgba(15,23,42,.04);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0F172A; --surface: #1E293B; --text: #E2E8F0; --muted: #94A3B8;
    --accent: #818CF8; --accent-soft: rgba(129,140,248,.14); --accent-strong: #A5B4FC;
    --success: #4ADE80; --success-soft: rgba(74,222,128,.14);
    --warning: #FBBF24; --warning-soft: rgba(251,191,36,.14);
    --danger: #F87171; --danger-soft: rgba(248,113,113,.14);
    --border: rgba(148,163,184,.16);
    --shadow: 0 1px 3px rgba(0,0,0,.3), 0 1px 2px rgba(0,0,0,.24);
  }
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
code, pre { font-family: 'JetBrains Mono', monospace; }

.block-container {max-width: 1080px; padding-top: 2rem; padding-bottom: 3rem;}

@keyframes sb-fade-in { from {opacity:0; transform: translateY(4px);} to {opacity:1; transform: translateY(0);} }

/* ---- page header with icon badge ---- */
.sb-header-wrap { display:flex; align-items:center; gap:.9rem; margin-bottom: 1.4rem;
  padding-bottom: 1.1rem; border-bottom: 1px solid var(--border); animation: sb-fade-in .25s ease; }
.icon-badge { width:46px; height:46px; min-width:46px; border-radius:13px; background: var(--accent-soft);
  display:flex; align-items:center; justify-content:center; font-size:1.5rem; }
.sb-header-wrap h2 { margin:0; font-weight:800; letter-spacing:-.01em; color: var(--text); }
.sb-subtitle { color: var(--muted); font-size:.92rem; margin-top:2px; }

/* ---- sidebar brand ---- */
.sb-brand { display:flex; align-items:center; gap:.55rem; font-size:1.3rem; font-weight:800;
  letter-spacing:-.01em; margin-bottom:.15rem; }
.sb-tagline { color: var(--muted); font-size:.78rem; margin-bottom:1.1rem; }

/* ---- status pill ---- */
.status-pill { display:flex; align-items:center; gap:.45rem; font-size:.78rem; color: var(--muted);
  padding: .4rem .1rem; }
.status-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.status-dot.ok { background: var(--success); box-shadow: 0 0 0 3px var(--success-soft); }
.status-dot.bad { background: var(--danger); box-shadow: 0 0 0 3px var(--danger-soft); }

/* ---- nav radio as pill tabs ---- */
div[role="radiogroup"] {gap: 3px;}
div[role="radiogroup"] label {
  border-radius: 10px; padding: 7px 10px; transition: background .15s ease, color .15s ease;
  font-weight: 500;
}
div[role="radiogroup"] label:hover { background: var(--accent-soft); }
div[role="radiogroup"] label:has(input:checked) { background: var(--accent-soft); color: var(--accent); font-weight:600; }

/* ---- weak topic buttons -> card rows ---- */
section[data-testid="stSidebar"] .stButton button {
  text-align:left; justify-content:flex-start; border-radius:10px;
  border:1px solid var(--border); background: var(--surface);
  font-weight:500; padding: .5rem .7rem; transition: all .15s ease;
}
section[data-testid="stSidebar"] .stButton button:hover {
  border-color: var(--accent); color: var(--accent); box-shadow: var(--shadow);
}

/* ---- buttons ---- */
.stButton > button { border-radius: 10px; transition: all .15s ease; }
.stButton > button[kind="primary"] {
  background: var(--accent); border-color: var(--accent); font-weight:600; box-shadow: var(--shadow);
}
.stButton > button[kind="primary"]:hover { background: var(--accent-strong); border-color: var(--accent-strong); transform: translateY(-1px); }

/* ---- chat bubbles, alternating tint (strictly user -> assistant order) ---- */
[data-testid="stChatMessage"] {
  border-radius: 16px; border: 1px solid var(--border); padding: .5rem .3rem;
  margin-bottom: .6rem; animation: sb-fade-in .2s ease;
}
[data-testid="stChatMessage"]:nth-of-type(odd) { background: var(--accent-soft); }
[data-testid="stChatMessage"]:nth-of-type(even) { background: var(--surface); box-shadow: var(--shadow); }

/* ---- source citation chips ---- */
.src-chip {
  display:inline-block; padding:3px 12px; margin:6px 6px 0 0;
  border-radius:999px; background: var(--accent-soft);
  color: var(--accent); font-size:.78rem; font-weight:500;
  border: 1px solid var(--border);
}

/* ---- KPI / metric cards ---- */
div[data-testid="stMetric"] {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 1rem 1.1rem; box-shadow: var(--shadow);
  transition: transform .15s ease;
}
div[data-testid="stMetric"]:hover { transform: translateY(-2px); }
div[data-testid="stMetricLabel"] { color: var(--muted); }

/* ---- bordered containers (question cards etc.) ---- */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px !important; border-color: var(--border) !important;
  box-shadow: var(--shadow); animation: sb-fade-in .2s ease;
}

/* ---- quiz stepper ---- */
.stepper { display:flex; gap:8px; margin: .3rem 0 1rem; }
.stepper .dot { width:28px; height:6px; border-radius:999px; background: var(--border); transition: background .2s ease; }
.stepper .dot.done { background: var(--success); }
.stepper .dot.current { background: var(--accent); }

/* ---- custom mastery bars ---- */
.mastery-row { margin-bottom: 14px; }
.mastery-label { display:flex; justify-content:space-between; font-size:.85rem;
  margin-bottom: 4px; color: var(--text); font-weight:500; }
.mastery-track { background: var(--border); border-radius: 999px; height: 10px; overflow:hidden; }
.mastery-fill { height: 100%; border-radius: 999px; transition: width .4s ease; }

/* ---- badges ---- */
.badge { display:inline-block; padding:3px 11px; border-radius:999px; font-size:.75rem; font-weight:700; }
.badge-ok { background: var(--success-soft); color: var(--success); }
.badge-warn { background: var(--warning-soft); color: var(--warning); }

/* ---- empty state ---- */
.empty-state { text-align:center; padding: 2.6rem 1rem; color: var(--muted); }
.empty-state .big { font-size: 2.4rem; margin-bottom: .5rem; }

/* ---- section label ---- */
.section-label { font-size:.78rem; font-weight:700; letter-spacing:.04em; color: var(--muted);
  text-transform: uppercase; margin: 1.4rem 0 .6rem; }

hr, [data-testid="stDivider"] { border-color: var(--border) !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- state ----------
st.session_state.setdefault("messages", [])
st.session_state.setdefault("session_id", os.urandom(4).hex())
st.session_state.setdefault("quiz", None)  # {"topic", "questions", "idx", "score", "answers"}


def page_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="sb-header-wrap">
          <div class="icon-badge">{icon}</div>
          <div><h2>{title}</h2><div class="sb-subtitle">{subtitle}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def source_chips(sources: list[str]) -> str:
    if not sources:
        return ""
    chips = "".join(f'<span class="src-chip">{s}</span>' for s in sources)
    return f'<div style="margin-top:.4rem">{chips}</div>'


def mastery_bar(label: str, score: int):
    color = "var(--danger)" if score < 40 else "var(--warning)" if score < 70 else "var(--success)"
    st.markdown(
        f"""
        <div class="mastery-row">
          <div class="mastery-label"><span>{label}</span><span>{score}%</span></div>
          <div class="mastery-track"><div class="mastery-fill" style="width:{score}%;background:{color};"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, text: str):
    st.markdown(f'<div class="empty-state"><div class="big">{icon}</div>{text}</div>', unsafe_allow_html=True)


def stepper(total: int, current: int):
    dots = "".join(
        f'<div class="dot {"done" if i < current else "current" if i == current else ""}"></div>'
        for i in range(total)
    )
    st.markdown(f'<div class="stepper">{dots}</div>', unsafe_allow_html=True)


@st.cache_data(ttl=15)
def ollama_status() -> bool:
    try:
        r = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=2)
        return r.ok
    except Exception:
        return False


def history_text(n: int = 6) -> str:
    recent = st.session_state.messages[-n:]
    return "\n".join(f"{m['role']}: {m['content']}" for m in recent)


def ask(text: str, tutor_mode: bool, force_intent: str | None = None):
    try:
        result = chat(
            text,
            tutor_mode=tutor_mode,
            history=history_text(),
            weak_topics=memory.weak_topics(),
            force_intent=force_intent,
        )
        return result.text, result.sources
    except Exception as e:  # connection errors, model not pulled, etc.
        return (
            "⚠️ The tutor model isn't reachable right now. Make sure Ollama is running "
            f"and the model is pulled (`ollama pull {config.LLM_MODEL}`).\n\n*Details: {e}*",
            [],
        )


# ---------- sidebar ----------
with st.sidebar:
    st.markdown('<div class="sb-brand">\U0001F393 StudyBuddy</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-tagline">A tutor built on your own notes</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["\U0001F4AC Learn", "\U0001F4DD Quiz", "\U0001F4DA Library", "\U0001F4CA Progress"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown('<div class="section-label" style="margin-top:0">Weak topics</div>', unsafe_allow_html=True)
    weak = memory.weak_topics()
    if not weak:
        st.caption("Take a quiz to see weak topics here.")
    for topic, score in sorted(weak.items(), key=lambda x: x[1]):
        dot = "\U0001F534" if score < 40 else "\U0001F7E0" if score < 70 else "\U0001F7E2"
        if st.button(f"{dot}  {topic}  ·  {score}%", key=f"wt_{topic}", use_container_width=True):
            st.session_state.prefill = f"Explain {topic}"
            st.session_state.force_page = "\U0001F4AC Learn"

    n_docs = sum(1 for p in config.NOTES_DIR.glob("**/*") if p.suffix.lower() in {".pdf", ".txt", ".md"})
    st.divider()
    online = ollama_status()
    dot_cls = "ok" if online else "bad"
    status_text = f"Ollama connected · {config.LLM_MODEL}" if online else "Ollama unreachable"
    st.markdown(
        f'<div class="status-pill"><span class="status-dot {dot_cls}"></span>{status_text}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"\U0001F4DA {n_docs} document(s) in library")

if st.session_state.pop("force_page", None):
    page = "\U0001F4AC Learn"

# ---------- pages ----------
if page == "\U0001F4AC Learn":
    c1, c2 = st.columns([4, 1])
    with c1:
        page_header("\U0001F4AC", "Learn", "Ask about your notes, get a hint before the answer.")
    with c2:
        mode = st.segmented_control("Mode", ["Tutor", "Direct"], default="Tutor", label_visibility="collapsed")
    tutor_mode = (mode or "Tutor") == "Tutor"

    if not st.session_state.messages:
        empty_state("\U0001F44B", "Ask anything about your notes. Try one of these:")
        cols = st.columns(3)
        for col, s in zip(
            cols,
            ["Explain normalization", "Quiz me on SQL joins", "Make a 5-day study plan"],
        ):
            if col.button(s, use_container_width=True):
                st.session_state.prefill = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="\U0001F9D1" if m["role"] == "user" else "\U0001F393"):
            st.markdown(m["content"], unsafe_allow_html=True)

    prompt = st.chat_input("Ask about your notes…") or st.session_state.pop("prefill", None)
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="\U0001F9D1"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="\U0001F393"):
            with st.spinner("Thinking…"):
                answer, sources = ask(prompt, tutor_mode)
            rendered = answer + source_chips(sources)
            st.markdown(rendered, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": rendered})

    st.caption("↵ Enter to send · ⇧+↵ new line")

elif page == "\U0001F4DD Quiz":
    page_header("\U0001F4DD", "Quiz", "Five questions, written straight from your notes.")
    q = st.session_state.quiz

    if q is None:
        c1, c2 = st.columns([4, 1])
        topic = c1.text_input("Topic", placeholder="e.g. SQL Joins", label_visibility="collapsed")
        generate = c2.button("Generate", type="primary", use_container_width=True, disabled=not topic)
        if generate:
            with st.spinner("Writing questions from your notes…"):
                try:
                    questions = generate_quiz(topic)
                except Exception as e:
                    questions = []
                    st.error(f"Couldn't reach the tutor model: {e}")
            if not questions:
                st.warning("This isn't covered in your notes (or no notes are indexed yet).")
            else:
                st.session_state.quiz = {
                    "topic": topic,
                    "questions": questions,
                    "idx": 0,
                    "correct": 0,
                    "answers": [],
                }
                st.rerun()
        else:
            empty_state("\U0001F4DD", "Pick a topic from your notes to generate a 5-question quiz.")

    elif q["idx"] >= len(q["questions"]):
        total = len(q["questions"])
        score_pct = round(100 * q["correct"] / total) if total else 0
        memory.record_quiz(q["topic"], score_pct)
        badge = "badge-ok" if score_pct >= 70 else "badge-warn"
        with st.container(border=True):
            stepper(total, total)
            st.markdown(
                f"### Quiz complete — {q['correct']}/{total} "
                f'<span class="badge {badge}">{score_pct}%</span>',
                unsafe_allow_html=True,
            )
            for a in q["answers"]:
                icon = "✅" if a["correct"] else "❌"
                st.markdown(f"{icon} **{a['q']}**  \n{a['feedback']}")
        if st.button("New quiz", type="primary"):
            st.session_state.quiz = None
            st.rerun()

    else:
        i, total = q["idx"], len(q["questions"])
        question = q["questions"][i]
        with st.container(border=True):
            st.caption(f"Topic: {q['topic']} · Question {i + 1} of {total}")
            stepper(total, i)
            st.markdown(f"#### {question['q']}")

            if question.get("type") == "mcq" and question.get("options"):
                choice = st.radio("Choose one", question["options"], key=f"q{i}", label_visibility="collapsed")
            else:
                choice = st.text_input("Your answer", key=f"q{i}", label_visibility="collapsed", placeholder="Type your answer…")

            if st.button("Submit ▶", type="primary"):
                with st.spinner("Grading…"):
                    try:
                        result = grade_answer(question, choice or "")
                    except Exception as e:
                        result = {"correct": False, "feedback": f"Grading failed: {e}", "topic": q["topic"]}
                memory.record_answer(q["topic"], bool(result.get("correct")))
                q["correct"] += 1 if result.get("correct") else 0
                q["answers"].append(
                    {"q": question["q"], "correct": bool(result.get("correct")), "feedback": result.get("feedback", "")}
                )
                q["idx"] += 1
                st.rerun()

elif page == "\U0001F4DA Library":
    page_header("\U0001F4DA", "Library", "Upload PDFs or notes, then index them so StudyBuddy can cite them.")

    existing = sorted(p.name for p in config.NOTES_DIR.glob("**/*") if p.suffix.lower() in {".pdf", ".txt", ".md"})
    if existing:
        with st.container(border=True):
            st.caption(f"{len(existing)} document(s) in the library")
            chips = "".join(f'<span class="src-chip">\U0001F4C4 {name}</span>' for name in existing)
            st.markdown(chips, unsafe_allow_html=True)
    else:
        empty_state("\U0001F4C2", "No documents yet — upload your notes below to get started.")

    st.write("")
    files = st.file_uploader(
        "Upload PDFs or notes", type=["pdf", "txt", "md"], accept_multiple_files=True
    )
    if files:
        for f in files:
            (config.NOTES_DIR / f.name).write_bytes(f.getbuffer())
        st.toast(f"{len(files)} file(s) saved to the library.", icon="✅")

    if st.button("⚡ Index documents", type="primary"):
        with st.spinner("Reading and embedding your notes…"):
            try:
                n = ingest()
            except Exception as e:
                st.error(f"Indexing failed — is Ollama running? Details: {e}")
            else:
                if n == 0:
                    st.warning("No documents found in the library to index.")
                else:
                    st.toast(f"Indexed {n} chunks. Ready!", icon="⚡")

elif page == "\U0001F4CA Progress":
    page_header("\U0001F4CA", "Your Progress", "Track quiz history and weak spots over time.")
    stats = memory.get_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Quizzes", stats["quizzes"])
    m2.metric("Avg score", f"{stats['avg_score']}%")
    m3.metric("Streak", f"{stats['streak_days']} days")
    m4.metric("Weak topics", stats["weak_count"])

    st.markdown('<div class="section-label">Last 7 days</div>', unsafe_allow_html=True)
    activity = memory.activity_last_n_days(7)
    if any(activity.values()):
        st.bar_chart(activity, height=180, color="#4F46E5")
    else:
        st.caption("No activity yet this week — take a quiz to see it show up here.")

    st.markdown('<div class="section-label">Topic mastery</div>', unsafe_allow_html=True)
    if not stats["topic_mastery"]:
        empty_state("\U0001F4CA", "No quiz history yet — take a quiz to populate this.")
    else:
        with st.container(border=True):
            for topic, score in sorted(stats["topic_mastery"].items(), key=lambda x: x[1]):
                mastery_bar(topic, score)
