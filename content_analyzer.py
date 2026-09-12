import json
import os
from groq import Groq
from prompts import CONTENT_PROMPT
from transcript import group_segments

def _client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
    return Groq(api_key=key)

def _model():
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def _parse(text):
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI returned invalid JSON.")
    return json.loads(text[start:end + 1])

def analyze_content(claim: dict, transcript: list[dict]) -> dict:
    # For long videos, analyze transcript chunks and ask a final synthesis pass.
    groups = group_segments(transcript)
    analyses = []
    for group in groups:
        response = _client().chat.completions.create(
            model=_model(),
            messages=[{"role": "user", "content": CONTENT_PROMPT.format(
                claim_json=json.dumps(claim, ensure_ascii=False),
                transcript=json.dumps(group["segments"], ensure_ascii=False)
            )}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        analyses.append(_parse(response.choices[0].message.content))

    if not analyses:
        raise ValueError("No transcript content was available for analysis.")

    # Select the strongest evidence rather than sending all raw text through another call.
    rank = {"strong_support": 5, "partial_support": 4, "contradiction": 4, "weak_relevance": 2, "no_support": 1}
    best = max(analyses, key=lambda x: rank.get(x.get("support_level"), 0))
    segments = best.get("relevant_segments", [])
    for seg in segments:
        start, end = float(seg.get("start", 0)), float(seg.get("end", 0))
        # Filled later by the UI layer's known video ID is not available here; keep data modular.
        seg["start_display"] = _fmt(start)
        seg["end_display"] = _fmt(end)
    return {
        "support_level": best.get("support_level", "no_support"),
        "evidence_found": bool(best.get("evidence_found", False)),
        "relevant_segments": segments[:5],
        "reason": best.get("reason", ""),
    }

def _fmt(seconds: float) -> str:
    total = max(0, int(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
