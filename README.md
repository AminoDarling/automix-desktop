# Automix Desktop

Modern desktop DJ application for streaming, remixing, and automixing YouTube-sourced audio with the `automix-engine` transition backend.

## What this app does

- Two virtual decks (Deck A / Deck B)
- Load audio via YouTube URLs
- Real-time crossfader and volume controls
- Dark DJ-style desktop UI
- BPM display and waveform rendering
- AutoMix with `automix-engine` transition analysis
- Real-time audio mixing in Python using `sounddevice`
- Seamless loading and processing pipeline for track transitions

## Architecture

The app is split into a clean backend + UI boundary:

- `app/automix_adapter.py` integrates with the external `VertexSelection/automix-engine` repo and reuses the existing beat analysis + transition logic.
- `app/audio.py` handles real-time playback, crossfading, latency-safe buffering, and mixer logic.
- `app/ui_main.py` provides the desktop interface and controls.

## Requirements

- Python 3.11+
- FFmpeg
- Git
- A desktop environment with audio output

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app
```

## Usage

1. Copy a YouTube URL into either deck.
2. Click `Load YouTube`.
3. Click `Play` to start playback.
4. Use the crossfader to blend decks in real time.
5. Toggle `AutoMix` to generate or preview a transition using `automix-engine`.

## YouTube / legal note

This app is designed to work with audio files the user explicitly loads from YouTube URLs. It does not bypass paywalls or disable content protections. Use only content you are authorized to use and comply with YouTube’s terms and local copyright rules.

## Project layout

```text
app/
  __init__.py
  __main__.py
  config.py
  models.py
  youtube_loader.py
  automix_adapter.py
  audio.py
  ui_main.py
requirements.txt
README.md
```

## Backend integration

`automix-engine` is treated as the mixing backend. The app will clone or reuse a local `third_party/automix-engine` checkout and call the existing `cue_analysis.py` and `stem_transition.py` scripts. The UI talks to the backend over Python interfaces rather than rewriting the transition logic.
