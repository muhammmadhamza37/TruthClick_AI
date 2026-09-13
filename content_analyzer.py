import json
import os
from groq import Groq
from prompts import CONTENT_PROMPT
from transcript import group_segments


# Keep each request comfortably below Groq's 8K TPM limit.
MAX_TRANSCRIPT_CHARS = 9000
MAX_OUTPUT_TOKENS = 1000

def _client():
    key = os.getenv("GROQ_API_KEY")

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    return Groq(api_key=key)


def _model():
    # Use the model from .env if provided.
    # Otherwise use this default.
    return os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )


def _parse(text):
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end < start:
        raise ValueError("AI returned invalid JSON.")

    return json.loads(text[start:end + 1])


def _prepare_transcript(segments):
    """
    Convert transcript segments into a compact timestamped format.
    Stops before the request becomes too large.
    """

    selected = []
    total_chars = 0

    for segment in segments:

        item = {
            "start": round(float(segment.get("start", 0)), 2),
            "end": round(float(segment.get("end", 0)), 2),
            "text": str(segment.get("text", "")).strip()
        }

        item_text = json.dumps(
            item,
            ensure_ascii=False
        )

        if selected and (
            total_chars + len(item_text)
            > MAX_TRANSCRIPT_CHARS
        ):
            break

        selected.append(item)
        total_chars += len(item_text)

    return selected


def analyze_content(
    claim: dict,
    transcript: list[dict]
) -> dict:

    if not transcript:
        raise ValueError(
            "No transcript content was available for analysis."
        )

    client = _client()
    model = _model()

    # ---------------------------------------------------------
    # IMPORTANT:
    # Instead of sending every transcript group to Groq,
    # combine the transcript and send only ONE compact request.
    # ---------------------------------------------------------

    compact_transcript = _prepare_transcript(transcript)

    if not compact_transcript:
        raise ValueError(
            "Transcript was empty after size reduction."
        )

    claim_json = json.dumps(
        claim,
        ensure_ascii=False,
        separators=(",", ":")
    )

    transcript_json = json.dumps(
        compact_transcript,
        ensure_ascii=False,
        separators=(",", ":")
    )

    prompt = CONTENT_PROMPT.format(
        claim_json=claim_json,
        transcript=transcript_json
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=MAX_OUTPUT_TOKENS,
        response_format={
            "type": "json_object"
        }
    )

    result = _parse(
        response.choices[0].message.content
    )

    # ---------------------------------------------------------
    # Format timestamps
    # ---------------------------------------------------------

    segments = result.get(
        "relevant_segments",
        []
    )

    for segment in segments:

        start = float(
            segment.get("start", 0)
        )

        end = float(
            segment.get("end", 0)
        )

        segment["start_display"] = _fmt(start)
        segment["end_display"] = _fmt(end)

    return {
        "support_level": result.get(
            "support_level",
            "no_support"
        ),

        "evidence_found": bool(
            result.get(
                "evidence_found",
                False
            )
        ),

        "relevant_segments": segments[:5],

        "reason": result.get(
            "reason",
            ""
        )
    }


def _fmt(seconds: float) -> str:

    total = max(
        0,
        int(seconds)
    )

    hours, remainder = divmod(
        total,
        3600
    )

    minutes, seconds = divmod(
        remainder,
        60
    )

    if hours:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )
