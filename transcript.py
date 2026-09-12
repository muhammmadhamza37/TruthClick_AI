from typing import List, Dict, Optional
import json
import re

from youtube_transcript_api import YouTubeTranscriptApi


def _fmt(seconds: float) -> str:
    total = max(0, int(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _normalise_items(items) -> List[Dict]:
    segments = []
    for item in items:
        if hasattr(item, "text"):
            text = item.text
            start = float(item.start)
            duration = float(item.duration)
        else:
            text = item.get("text", "")
            start = float(item.get("start", 0))
            duration = float(item.get("duration", 0))

        text = " ".join(str(text).split())
        if not text:
            continue

        segments.append({
            "start": start,
            "end": start + duration,
            "start_display": _fmt(start),
            "end_display": _fmt(start + duration),
            "text": text,
        })
    return segments


def _fetch_with_youtube_transcript_api(video_id: str) -> List[Dict]:
    api = YouTubeTranscriptApi()

    # First inspect available tracks instead of assuming English.
    transcript_list = api.list(video_id)

    # Prefer manually created tracks, then generated tracks.
    candidates = []
    for transcript in transcript_list:
        candidates.append(transcript)

    if not candidates:
        raise RuntimeError("YouTube reports that no caption tracks are available.")

    preferred_languages = ("en", "ur", "hi", "ar")
    candidates.sort(
        key=lambda t: (
            not getattr(t, "language_code", "").lower().startswith(preferred_languages),
            getattr(t, "is_generated", False),
        )
    )

    last_error = None
    for transcript in candidates:
        try:
            fetched = transcript.fetch()
            items = fetched.to_raw_data() if hasattr(fetched, "to_raw_data") else fetched
            result = _normalise_items(items)
            if result:
                return result
        except Exception as exc:
            last_error = exc

    raise RuntimeError("Caption tracks were found, but none could be fetched.") from last_error


def _parse_vtt(text: str) -> List[Dict]:
    """Parse basic WebVTT subtitle text returned by yt-dlp."""
    blocks = re.split(r"\n\s*\n", text.strip())
    segments = []

    for block in blocks:
        lines = [line.strip("\ufeff ") for line in block.splitlines() if line.strip()]
        if not lines or lines[0].upper() == "WEBVTT":
            continue

        timing_index = next((i for i, line in enumerate(lines) if " --> " in line), None)
        if timing_index is None:
            continue

        timing = lines[timing_index]
        start_s, end_s = timing.split(" --> ", 1)
        end_s = end_s.split(" ", 1)[0]

        def parse_time(value: str) -> float:
            parts = value.replace(",", ".").split(":")
            if len(parts) == 3:
                h, m, s = parts
                return float(h) * 3600 + float(m) * 60 + float(s)
            m, s = parts
            return float(m) * 60 + float(s)

        try:
            start = parse_time(start_s)
            end = parse_time(end_s)
        except ValueError:
            continue

        caption = " ".join(lines[timing_index + 1:]).strip()
        caption = re.sub(r"<[^>]+>", "", caption)
        caption = " ".join(caption.split())

        if caption:
            segments.append({
                "start": start,
                "end": end,
                "start_display": _fmt(start),
                "end_display": _fmt(end),
                "text": caption,
            })

    return segments


def _fetch_with_ytdlp(video_id: str) -> List[Dict]:
    """
    Fallback for environments where youtube-transcript-api is blocked.
    yt-dlp can often read public manual/automatic subtitle tracks without
    needing a YouTube Data API key.
    """
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp is not installed.") from exc

    url = f"https://www.youtube.com/watch?v={video_id}"

    options = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en.*", "ur.*", "hi.*", "ar.*", ".*"],
        "subtitlesformat": "vtt",
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise RuntimeError("yt-dlp could not access the YouTube video.") from exc

    # Prefer manual subtitles, then automatic subtitles.
    subtitle_sets = [
        info.get("subtitles") or {},
        info.get("automatic_captions") or {},
    ]

    for subtitle_dict in subtitle_sets:
        if not subtitle_dict:
            continue

        language_codes = list(subtitle_dict.keys())
        preferred = sorted(
            language_codes,
            key=lambda x: (
                not x.lower().startswith(("en", "ur", "hi", "ar")),
                len(x),
            ),
        )

        for lang in preferred:
            formats = subtitle_dict.get(lang, [])
            vtt_url = next(
                (item.get("url") for item in formats if item.get("ext") == "vtt"),
                None,
            )
            if not vtt_url:
                continue

            import requests
            response = requests.get(
                vtt_url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()

            segments = _parse_vtt(response.text)
            if segments:
                return segments

    raise RuntimeError("No usable manual or automatic subtitle track was found.")


def get_transcript(video_id: str) -> List[Dict]:
    """
    Retrieve timestamped captions using two independent public-caption
    methods. The first method is preferred; yt-dlp is the fallback.
    """
    errors = []

    try:
        result = _fetch_with_youtube_transcript_api(video_id)
        if result:
            return result
    except Exception as exc:
        errors.append(f"youtube-transcript-api: {exc}")

    try:
        result = _fetch_with_ytdlp(video_id)
        if result:
            return result
    except Exception as exc:
        errors.append(f"yt-dlp: {exc}")

    raise ValueError(
        "Transcript could not be retrieved. "
        "The video may have captions disabled, may be restricted, "
        "or YouTube may be blocking transcript requests from this server. "
        "Try another public video with visible captions."
    )


def group_segments(segments: List[Dict], max_chars: int = 5000) -> List[Dict]:
    groups, current, chars = [], [], 0

    for seg in segments:
        if current and chars + len(seg["text"]) > max_chars:
            groups.append(_merge(current))
            current, chars = [], 0

        current.append(seg)
        chars += len(seg["text"])

    if current:
        groups.append(_merge(current))

    return groups


def _merge(items: List[Dict]) -> Dict:
    return {
        "start": items[0]["start"],
        "end": items[-1]["end"],
        "start_display": items[0]["start_display"],
        "end_display": items[-1]["end_display"],
        "text": " ".join(x["text"] for x in items),
        "segments": items,
    }
