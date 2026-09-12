import json
import os
from groq import Groq
from prompts import VERDICT_PROMPT

def _client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
    return Groq(api_key=key)

def _model():
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def generate_verdict(claim: dict, content: dict) -> dict:
    response = _client().chat.completions.create(
        model=_model(),
        messages=[{"role": "user", "content": VERDICT_PROMPT.format(
            claim_json=json.dumps(claim, ensure_ascii=False),
            content_json=json.dumps(content, ensure_ascii=False)
        )}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI returned invalid verdict JSON.")
    result = json.loads(text[start:end + 1])
    verdict = result.get("verdict")
    if verdict not in {"CLICKBAIT", "NON_CLICKBAIT", "INCONCLUSIVE"}:
        raise ValueError("AI returned an invalid verdict.")
    confidence = float(result.get("confidence", 0))
    result["confidence"] = max(0.0, min(1.0, confidence))
    return result
