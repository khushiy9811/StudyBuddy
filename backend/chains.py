"""Flow B — Chat: retriever -> mode prompt -> LLM -> answer with citations (F3/F5).

`chat()` is the single entry point the Streamlit UI (and the eval harness) call,
mirroring what a Langflow "Chat" flow would expose over its /run API.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.prompts import PromptTemplate

from backend import config
from backend.ingestion import get_vectorstore
from backend.prompts import DIRECT_PROMPT, PLAN_PROMPT, SUMMARY_PROMPT, TUTOR_PROMPT
from backend.router import classify_intent, get_llm

NOT_IN_NOTES = "This isn't covered in your notes."


@dataclass
class ChatResult:
    text: str
    intent: str
    sources: list[str] = field(default_factory=list)


def format_context(docs) -> str:
    parts = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page", "?")
        parts.append(f"[{src} p.{page}] {d.page_content}")
    return "\n\n".join(parts)


def format_sources(docs) -> list[str]:
    seen, out = set(), []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page", "?")
        key = (src, page)
        if key in seen:
            continue
        seen.add(key)
        out.append(f"\U0001F4C4 {src}, p.{page}")
    return out


def retrieve(topic_or_query: str, k: int):
    vs = get_vectorstore()
    return vs.similarity_search(topic_or_query, k=k)


def explain(query: str, history: str = "", tutor_mode: bool = True, k: int | None = None) -> ChatResult:
    docs = retrieve(query, k or config.TOP_K["explain"])
    if not docs:
        return ChatResult(text=NOT_IN_NOTES, intent="explain")
    context = format_context(docs)
    template = TUTOR_PROMPT if tutor_mode else DIRECT_PROMPT
    prompt = PromptTemplate.from_template(template).format(
        context=context, history=history, input=query
    )
    llm = get_llm(temperature=config.TEMPERATURE["answer"])
    answer = llm.invoke(prompt)
    return ChatResult(text=str(answer), intent="explain", sources=format_sources(docs))


def _summarize(query: str) -> ChatResult:
    docs = retrieve(query, config.TOP_K["summarize"])
    if not docs:
        return ChatResult(text=NOT_IN_NOTES, intent="summarize")
    context = format_context(docs)
    prompt = PromptTemplate.from_template(SUMMARY_PROMPT).format(context=context, input=query)
    llm = get_llm(temperature=config.TEMPERATURE["answer"])
    answer = llm.invoke(prompt)
    return ChatResult(text=str(answer), intent="summarize", sources=format_sources(docs))


def _plan(query: str, history: str, weak_topics: dict) -> ChatResult:
    weak_str = ", ".join(f"{t} ({s}%)" for t, s in sorted(weak_topics.items(), key=lambda x: x[1])) or "none yet"
    prompt = PromptTemplate.from_template(PLAN_PROMPT).format(
        weak_topics=weak_str, history=history, input=query
    )
    llm = get_llm(temperature=config.TEMPERATURE["answer"])
    answer = llm.invoke(prompt)
    return ChatResult(text=str(answer), intent="plan")


def chat(
    text: str,
    tutor_mode: bool = True,
    history: str = "",
    weak_topics: dict | None = None,
    force_intent: str | None = None,
) -> ChatResult:
    """Classify intent, dispatch to the right sub-flow, return the answer.

    `force_intent` skips the router (used by the Quiz page and the eval harness
    so they don't depend on the classifier guessing right).
    """
    weak_topics = weak_topics or {}
    if force_intent:
        intent = force_intent
    else:
        router_llm = get_llm(temperature=0.0)
        intent = classify_intent(router_llm, text)

    if intent == "quiz":
        # Quiz generation/grading has its own JSON contract — see backend/quiz.py.
        from backend.quiz import generate_quiz

        topic = text
        questions = generate_quiz(topic)
        if not questions:
            return ChatResult(text=NOT_IN_NOTES, intent="quiz")
        lines = [f"**Quiz: {topic}**\n"]
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q['q']}")
            if q.get("type") == "mcq":
                for j, opt in enumerate(q.get("options", [])):
                    lines.append(f"   {chr(65+j)}. {opt}")
        return ChatResult(text="\n".join(lines), intent="quiz")

    if intent == "summarize":
        return _summarize(text)
    if intent == "plan":
        return _plan(text, history, weak_topics)
    return explain(text, history, tutor_mode)
