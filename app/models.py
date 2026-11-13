from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TrackInfo:
    deck: str
    title: str = "Unknown track"
    artist: str = "Unknown artist"
    url: str = ""
    path: Optional[Path] = None
    duration_seconds: float = 0.0
    bpm: float = 120.0
    sample_rate: int = 44_100
    channels: int = 2
    is_loaded: bool = False


@dataclass
class MixerStatus:
    crossfader: float = 0.5
    master_gain: float = 1.0
    auto_mix: bool = False
    transition_status: str = "Idle"
    bpm_sync: float = 0.0
    is_playing: bool = False
    a_volume: float = 0.8
    b_volume: float = 0.8
    deck_a_state: str = "Stopped"
    deck_b_state: str = "Stopped"
    transition_confidence: float = 0.0
    waveform_a: list[float] = field(default_factory=list)
    waveform_b: list[float] = field(default_factory=list)
