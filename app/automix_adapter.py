from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


AUTOMIX_REPO_URL = "https://github.com/VertexSelection/automix-engine.git"
AUTOMIX_REPO_DIR = Path("third_party") / "automix-engine"


def ensure_automix_repo(repo_dir: Path = AUTOMIX_REPO_DIR) -> Path:
    if repo_dir.exists():
        return repo_dir

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", AUTOMIX_REPO_URL, str(repo_dir)], check=True)
    return repo_dir


def copy_track_to_automix(track_path: str | Path, repo_dir: Path = AUTOMIX_REPO_DIR, role: str = "song1") -> Path:
    repo_dir = ensure_automix_repo(repo_dir)
    destination = repo_dir / f"{role}.mp3"
    shutil.copy2(str(track_path), destination)
    return destination


def build_transition_audio(outgoing_path: str | Path, incoming_path: str | Path, output_dir: Path | None = None) -> dict[str, Any]:
    repo_dir = ensure_automix_repo()
    outgoing = copy_track_to_automix(outgoing_path, repo_dir, role="song1")
    incoming = copy_track_to_automix(incoming_path, repo_dir, role="song2")

    process = subprocess.run(
        ["python", "stem_transition.py"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=False,
    )

    output_root = repo_dir / "output" / "beat_overlap"
    if not output_root.exists():
        raise FileNotFoundError(f"Automix output directory was not created: {output_root}")

    transition_file = output_root / "beat_overlap_transition.wav"
    report_file = output_root / "beat_overlap_transition_report.json"
    if not transition_file.exists():
        raise FileNotFoundError(f"Automix generated no transition WAV at {transition_file}")

    payload: dict[str, Any] = {
        "transition_file": str(transition_file),
        "report_file": str(report_file),
        "stdout": process.stdout,
        "stderr": process.stderr,
        "returncode": process.returncode,
    }

    if report_file.exists():
        try:
            payload["report"] = json.loads(report_file.read_text())
        except json.JSONDecodeError:
            payload["report"] = {}

    return payload
