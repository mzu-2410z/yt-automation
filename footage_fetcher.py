"""
footage_fetcher.py
Downloads stock video clips from Pexels and/or Pixabay.
Falls back to the secondary source if the primary fails or returns nothing.
"""

import requests
import urllib.request
from pathlib import Path
from typing import Optional

import config


# ── Pexels ────────────────────────────────────────────────────────────────────

def _search_pexels(query: str) -> Optional[str]:
    """Return a download URL for the best matching Pexels video clip."""
    key = config.PEXELS_API_KEY
    if not key:
        raise ValueError(
            "\n[!] PEXELS_API_KEY not set in config.py\n"
            "    Get a free key at: https://www.pexels.com/api/"
        )

    url = "https://api.pexels.com/videos/search"
    params = {
        "query": query,
        "orientation": config.FOOTAGE_ORIENTATION,
        "size": "medium",
        "per_page": 5,
        "page": 1,
    }
    headers = {"Authorization": key}

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    videos = data.get("videos", [])
    if not videos:
        return None

    for video in videos:
        duration = video.get("duration", 0)
        if duration < config.FOOTAGE_MIN_DURATION:
            continue
        # Pick the HD or SD video file
        files = video.get("video_files", [])
        for quality in ["hd", "sd"]:
            for f in files:
                if f.get("quality") == quality and f.get("link"):
                    return f["link"]

    # Fallback: just return first available file
    try:
        return videos[0]["video_files"][0]["link"]
    except (IndexError, KeyError):
        return None


# ── Pixabay ───────────────────────────────────────────────────────────────────

def _search_pixabay(query: str) -> Optional[str]:
    """Return a download URL for the best matching Pixabay video clip."""
    key = config.PIXABAY_API_KEY
    if not key:
        raise ValueError(
            "\n[!] PIXABAY_API_KEY not set in config.py\n"
            "    Get a free key at: https://pixabay.com/api/docs/"
        )

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": key,
        "q": query,
        "video_type": "film",
        "orientation": config.FOOTAGE_ORIENTATION,
        "per_page": 5,
        "safesearch": "true",
        "min_duration": config.FOOTAGE_MIN_DURATION,
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    hits = data.get("hits", [])
    if not hits:
        return None

    for hit in hits:
        videos = hit.get("videos", {})
        # Prefer large > medium > small > tiny
        for size in ["large", "medium", "small", "tiny"]:
            v = videos.get(size, {})
            if v.get("url"):
                return v["url"]

    return None


# ── Downloader ────────────────────────────────────────────────────────────────

def _download(url: str, out_path: Path) -> Path:
    """Download a video URL to disk with a progress indicator."""
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=60) as response:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 256  # 256 KB

        with open(out_path, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(downloaded / total * 100)
                    print(f"\r        Downloading... {pct}%", end="", flush=True)

    print()
    return out_path


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_clip(query: str, out_path: Path) -> Optional[Path]:
    """
    Fetch one stock video clip for the given query.
    Tries FOOTAGE_PREFER source first, falls back to FOOTAGE_FALLBACK.
    Returns None if both fail (caller should use a static slide instead).
    """
    prefer  = config.FOOTAGE_PREFER.lower()
    fallback = config.FOOTAGE_FALLBACK.lower()

    sources = {
        "pexels":  _search_pexels,
        "pixabay": _search_pixabay,
    }

    for source_name in [prefer, fallback]:
        if source_name not in sources:
            continue
        try:
            print(f"      Searching {source_name}: '{query}'")
            video_url = sources[source_name](query)
            if video_url:
                print(f"        Found clip. Downloading...")
                return _download(video_url, out_path)
            else:
                print(f"        No results on {source_name}, trying fallback...")
        except Exception as e:
            print(f"        {source_name} error: {e} — trying fallback...")

    print(f"        [Warning] No footage found for '{query}'. Will use static slide.")
    return None


def fetch_all_clips(script: dict, job_dir: Path) -> list[Optional[Path]]:
    """
    Download one clip per script point + one for the intro.
    Returns a list aligned with the slide order:
      [intro_clip, point_1_clip, ..., point_5_clip, outro_clip]
    None entries mean no footage was found — video_assembler will use static slides.
    """
    footage_dir = job_dir / "footage"
    footage_dir.mkdir(exist_ok=True)

    clips = []

    # Intro: use first point's query as the intro backdrop
    intro_query = script["points"][0]["footage_query"]
    intro_path = footage_dir / "intro.mp4"
    clips.append(fetch_clip(intro_query, intro_path))

    # One clip per point
    for i, point in enumerate(script["points"]):
        query = point.get("footage_query", point["heading"])
        out_path = footage_dir / f"point_{i+1}.mp4"
        clips.append(fetch_clip(query, out_path))

    # Outro: reuse a generic "subscribe" type backdrop
    outro_path = footage_dir / "outro.mp4"
    clips.append(fetch_clip("cinematic sky timelapse", outro_path))

    return clips
