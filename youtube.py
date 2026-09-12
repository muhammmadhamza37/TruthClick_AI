import re
from dataclasses import dataclass
from typing import Optional
import requests

VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})")

@dataclass
class VideoInfo:
    video_id: str
    title: str
    thumbnail: str
    channel: str
    duration: str
    url: str

def extract_video_id(url: str) -> str:
    match = VIDEO_ID_RE.search(url.strip())
    if not match:
        raise ValueError("Please enter a valid YouTube video URL.")
    return match.group(1)

def _duration(seconds: int) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def get_video_info(url: str) -> dict:
    video_id = extract_video_id(url)
    # Public oEmbed is intentionally used so an API key is not required for basic metadata.
    endpoint = "https://www.youtube.com/oembed"
    response = requests.get(endpoint, params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"}, timeout=15)
    if response.status_code != 200:
        raise ValueError("The YouTube video could not be accessed. It may be private or unavailable.")
    data = response.json()
    return {
        "video_id": video_id,
        "title": data.get("title", ""),
        "thumbnail": data.get("thumbnail_url", f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"),
        "channel": data.get("author_name", "Unknown"),
        "duration": "Unknown",
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }
