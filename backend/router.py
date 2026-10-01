"""Intent Router — classifies each message as explain / quiz / summarize / plan (F2)."""
from __future__ import annotations

from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

from backend import config
from backend.prompts import INTENT_CLASSIFIER

VALID_LABELS = {"explain", "quiz", "summarize", "plan"}

_prompt = PromptTemplate.from_template(INTENT_CLASSIFIER)


def classify_intent(llm: OllamaLLM, text: str) -> str:
    """Return one of explain/quiz/summarize/plan. Falls back to 'explain' on any
    unexpected output so the chat flow always has somewhere to go (see Risks table)."""
    raw = llm.invoke(_prompt.format(input=text))
    label = str(raw).strip().lower().splitlines()[0].strip(" .:`\"'")
    for candidate in VALID_LABELS:
        if candidate in label:
            return candidate
    return "explain"


def get_llm(temperature: float = 0.1) -> OllamaLLM:
    # Using the plain completion API (OllamaLLM / api/generate) rather than
    # ChatOllama (api/chat): with small quantized models like phi3:mini, the
    # chat endpoint's template wrapping around our long RAG prompts triggered
    # Ollama's "token repeat limit reached" abort. The completion API, which
    # is what `ollama run` uses under the hood, handles the same prompts fine.
    return OllamaLLM(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=temperature,
        # Small quantized models (e.g. phi3:mini) can fall into a repetition
        # loop at low/near-greedy temperature and hit Ollama's "token repeat
        # limit reached" abort. repeat_penalty makes recently-used tokens
        # less likely, which prevents that without needing higher temperature.
        repeat_penalty=1.3,
        repeat_last_n=256,
    )
