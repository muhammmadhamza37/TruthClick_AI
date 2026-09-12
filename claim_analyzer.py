import json
import os
from groq import Groq
from prompts import CLAIM_PROMPT

def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
    return Groq(api_key=key)

def _model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def _json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI returned invalid JSON.")
    return json.loads(text[start:end + 1])

def analyze_claim(title: str, thumbnail_url: str | None = None) -> dict:
    # The current MVP uses title text. Thumbnail OCR/vision can be added later without changing the UI contract.
    prompt = CLAIM_PROMPT.format(title=title)
    response = _client().chat.completions.create(
        model=_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    data = _json_response(response.choices[0].message.content)
    required = ["main_topic", "claim", "claim_type", "key_entities", "expected_content"]
    if not all(k in data for k in required):
        raise ValueError("AI claim analysis is missing required fields.")
    return data
