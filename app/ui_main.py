from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf

from app.config import BUFFER_SIZE, CHANNELS, SAMPLE_RATE


@dataclass
class DeckPlayback:
    name: str
    path: Optional[Path] = None
    samples: np.ndarray | None = None
    sample_rate: int = SAMPLE_RATE
    channels: int = CHANNELS
    volume: float = 1.0
    playing: bool = False
    position: float = 0.0
    duration: float = 0.0

    def load(self, track_path: str | Path) -> None:
        audio, sr = sf.read(str(track_path), always_2d=True, dtype="float32")
        if audio.ndim == 1:
            audio = np.column_stack([audio, audio])
        self.path = Path(track_path)
        self.samples = np.ascontiguousarray(audio, dtype=np.float32)
        self.sample_rate = sr
        self.channels = 2
        self.duration = len(self.samples) / sr
        self.position = 0.0

    def seek(self, seconds: float) -> None:
        if self.samples is None:
            return
        self.position = max(0.0, min(self.duration, seconds))

    def set_volume(self, gain: float) -> None:
        self.volume = max(0.0, min(1.5, gain))

    def waveform(self, points: int = 128) -> list[float]:
        if self.samples is None:
            return [0.0] * points
        mono = np.sqrt(np.mean(np.square(self.samples), axis=1))
        if mono.size == 0:
            return [0.0] * points
        reduced = mono.reshape(-1)
        step = max(1, len(reduced) // points)
        window = reduced[::step][:points]
        if len(window) < points:
            window = np.pad(window, (0, points - len(window)))
        return np.clip(window, 0.0, 1.0).astype(float).tolist()

    def render_block(self, frames: int, crossfade: float = 0.0) -> np.ndarray:
        if self.samples is None:
            return np.zeros((frames, 2), dtype=np.float32)
        start = int(round(self.position * self.sample_rate))
        end = start + frames
        chunk = self.samples[start:end]
        if chunk.shape[0] < frames:
            pad = np.zeros((frames - chunk.shape[0], 2), dtype=np.float32)
            chunk = np.concatenate([chunk, pad], axis=0)
        chunk = chunk[:frames]
        chunk = chunk * self.volume
        self.position += frames / self.sample_rate
        if self.position >= self.duration:
            self.position = 0.0
        return chunk


class LiveMixer:
    def __init__(self) -> None:
        self.deck_a = DeckPlayback("A")
        self.deck_b = DeckPlayback("B")
        self.crossfader = 0.5
        self.master_gain = 1.0
        self.auto_mix = False
        self.transition_status = "Idle"
        self.output_stream = None
        self._sample_queue = 0

    def start(self) -> None:
        if self.output_stream is not None:
            return
        self.output_stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=2,
            blocksize=BUFFER_SIZE,
            callback=self._audio_callback,
        )
        self.output_stream.start()

    def stop(self) -> None:
        if self.output_stream is not None:
            self.output_stream.stop()
            self.output_stream.close()
            self.output_stream = None

    def _audio_callback(self, outdata, frames, timeinfo, status) -> None:
        if status:
            print(status)

        delta_a = self.deck_a.render_block(frames)
        delta_b = self.deck_b.render_block(frames)

        if self.auto_mix:
            fade = float(self.crossfader)
            a_gain = 1.0 - fade
            b_gain = fade
            out = delta_a * a_gain + delta_b * b_gain
        else:
            fade = float(self.crossfader)
            a_gain = math.cos(fade * 0.5 * math.pi)
            b_gain = math.sin(fade * 0.5 * math.pi)
            out = delta_a * a_gain + delta_b * b_gain

        out = np.clip(out * self.master_gain, -1.0, 1.0)
        outdata[:, :] = out

    def set_crossfader(self, value: float) -> None:
        self.crossfader = max(0.0, min(1.0, value))

    def set_master_gain(self, value: float) -> None:
        self.master_gain = max(0.0, min(2.0, value))

    def toggle_auto_mix(self, enabled: bool) -> None:
        self.auto_mix = enabled
        self.transition_status = "AutoMix ON" if enabled else "Manual mix"

    def deck_state(self, name: str) -> str:
        deck = self.deck_a if name == "A" else self.deck_b
        if deck.playing:
            return "Playing"
        return "Paused"
