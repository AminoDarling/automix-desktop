from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yt_dlp

from app.config import APP_NAME


def ensure_cache_dir() -> Path:
    cache_dir = Path("cache") / "youtube"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_youtube_audio(url: str, target_dir: Path | None = None) -> str:
    """Download a YouTube audio file to a local cache directory.

    This app intentionally uses user-authorized sources and does not bypass
    paywalls or credentialed subscription restrictions.
    """
    output_dir = target_dir or ensure_cache_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    options: dict[str, Any] = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        ],
        "paths": {"home": str(output_dir)},
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        title = info.get("title", "track") if isinstance(info, dict) else "track"

    candidates = sorted(output_dir.glob(f"{title}.*"))
    if not candidates:
        raise FileNotFoundError(f"No downloaded audio found for title: {title}")

    audio_path = sorted(candidates, key=lambda item: item.stat().st_size)[-1]
    return str(audio_path)
