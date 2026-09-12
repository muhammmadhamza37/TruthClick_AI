# TruthClick AI

**Does the video deliver what the title promises?**

TruthClick AI is a modular Streamlit application that compares a YouTube video's title claim with its timestamped transcript and uses a Groq LLM to classify the video as **CLICKBAIT**, **NON_CLICKBAIT**, or **INCONCLUSIVE**.

## Features

- YouTube URL validation
- Public YouTube metadata via oEmbed
- Timestamped transcript extraction
- AI claim extraction
- Semantic claim-vs-content analysis
- Evidence and timestamp display
- Structured JSON from the AI
- Graceful error handling
- Long-transcript chunking
- Configurable Groq model

## Architecture

- `app.py` — Streamlit interface and orchestration only.
- `youtube.py` — YouTube URL parsing and metadata.
- `transcript.py` — Transcript retrieval, cleaning and segmentation.
- `claim_analyzer.py` — Extracts the promise/claim from the title.
- `content_analyzer.py` — Compares the claim with timestamped transcript evidence.
- `verdict.py` — Produces the final classification.
- `prompts.py` — Central home for all LLM prompts.
- `requirements.txt` — Python dependencies.
- `.env` — Local configuration/secrets placeholder.

## Requirements

Python 3.10+ is recommended.

A public YouTube video with an available transcript/captions is required for the MVP.

A Groq API key is required.

## Installation

### 1. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Groq

Edit `.env`:

```env
GROQ_API_KEY=your_real_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Never commit a real API key to GitHub.

### 4. Run

```bash
streamlit run app.py
```

## How it works

```text
YouTube URL
    ↓
Video metadata
    ↓
Timestamped transcript
    ↓
Title claim extraction
    ↓
Claim vs transcript analysis
    ↓
Evidence + timestamps
    ↓
Final verdict
```

The system does not treat keyword mentions as proof. For example, mentioning “Babar Azam” is not enough to prove a title claiming that he was insulted.

## Example

Title:

> Babar Azam Ki Beizzati Ho Gayi 😱

If the transcript only discusses Babar Azam's performance, without supporting the claim of an insult, the system can classify it as clickbait or inconclusive depending on evidence quality.

If the transcript contains a meaningful discussion of the claimed incident, the system can return non-clickbait with the relevant timestamp.

## Important limitation

TruthClick AI does not establish objective truth. It evaluates whether the available video transcript sufficiently supports the promise made by the title.

Transcript-only analysis also means that the current MVP cannot reliably detect claims conveyed only through visual information in the thumbnail/video. Thumbnail vision analysis and direct audio transcription can be added later.

If transcript data is unavailable or insufficient, the application should not invent evidence; it should report the limitation.

## GitHub

Create a repository, then:

```bash
git init
git add .
git commit -m "Initial TruthClick AI project"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Before pushing, add `.env` to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

## Streamlit deployment

For Streamlit deployment, add your secret values in the platform's Secrets settings rather than committing `.env`.

At minimum:

```toml
GROQ_API_KEY = "your_real_key"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

## Development roadmap

Future improvements can include:

- Thumbnail OCR/vision analysis
- Direct audio-to-text fallback
- Better multilingual transcript handling
- YouTube timestamp deep links
- Evidence ranking across all transcript chunks
- Batch video analysis
- Research dataset export


## Transcript retrieval

TruthClick AI first tries `youtube-transcript-api` and then falls back to `yt-dlp`
for public manual or automatically generated captions. A transcript is required
for timestamp-based clickbait analysis.

If both methods fail, the video may have captions disabled, may be restricted, or
YouTube may be blocking requests from the server running Streamlit. This is a
YouTube access limitation rather than a Groq/AI problem.

For testing, use a public video that visibly has captions/subtitles on YouTube.

After updating the project, reinstall dependencies:

```bash
pip install -r requirements.txt --upgrade
```
