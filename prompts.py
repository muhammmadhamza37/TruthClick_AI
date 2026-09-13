CLAIM_PROMPT = """You analyze a YouTube video's title for clickbait detection.
Return ONLY valid JSON. Do not use markdown.

Extract the promise/claim made by the title. Do not assume facts not present.
A person's name appearing in a title is not itself a claim.

Required JSON:
{{
  "main_topic": "string",
  "claim": "string",
  "claim_type": "factual|opinion|question|entertainment|other",
  "key_entities": ["string"],
  "expected_content": "string"
}}

Title:
{title}
"""

CONTENT_PROMPT = """You are an evidence-focused video content analyst.
Compare the supplied title claim with timestamped transcript segments.

Return ONLY valid JSON. Never invent evidence or timestamps.
Mentioning the same person/topic is NOT sufficient support.
Evaluate semantic meaning and context.

Use one support_level:
strong_support, partial_support, weak_relevance, no_support, contradiction

Return:
{{
  "support_level": "string",
  "evidence_found": true,
  "relevant_segments": [
    {{
      "start": 0,
      "end": 0,
      "topic": "string",
      "evidence": "short exact/paraphrased evidence from supplied text"
   } }
  ],
  "reason": "string"
}}

Claim:
{claim_json}

Transcript:
{transcript}
"""

VERDICT_PROMPT = """You are the final clickbait classifier.
Use ONLY the supplied claim analysis and content analysis.
Do not claim objective truth. Judge whether the video content sufficiently delivers the promise made by the title.

Return ONLY valid JSON:
{{
  "verdict": "CLICKBAIT|NON_CLICKBAIT|INCONCLUSIVE",
  "confidence": 0.0,
  "reason": "short explanation"
}}

Guidance:
- Strong support normally indicates NON_CLICKBAIT.
- No support or contradiction normally indicates CLICKBAIT.
- Weak relevance often indicates CLICKBAIT when the title makes a factual promise.
- Partial support requires context; do not automatically label it either way.
- If evidence is insufficient or transcript quality is inadequate, use INCONCLUSIVE.
- Confidence must be between 0 and 1.

Claim analysis:
{claim_json}

Content analysis:
{content_json}
"""
