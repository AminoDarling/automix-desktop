from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.audio import LiveMixer
from app.config import APP_NAME
from app.models import MixerStatus
from app.youtube_loader import download_youtube_audio


class WaveformWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.data: list[float] = [0.0] * 96
        self._set_dark_style()

    def set_data(self, values: list[float]) -> None:
        self.data = values
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#12161d"))
        pen = QPen(QColor("#5eead4"))
        pen.setWidth(2)
        painter.setPen(pen)

        width = self.width()
        height = self.height()
        midpoint = height / 2
        for idx in range(len(self.data) - 1):
            left_x = idx / (len(self.data) - 1) * width
            right_x = (idx + 1) / (len(self.data) - 1) * width
            left_y = midpoint - self.data[idx] * (height * 0.4)
            right_y = midpoint - self.data[idx + 1] * (height * 0.4)
            painter.drawLine(int(left_x), int(left_y), int(right_x), int(right_y))

    def _set_dark_style(self) -> None:
        self.setMinimumHeight(80)
        self.setStyleSheet("background: #12161d; border: 1px solid #1f2937;")


class DeckPanel(QWidget):
    def __init__(self, deck_name: str, mixer: LiveMixer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.deck_name = deck_name
        self.mixer = mixer
        self.waveform = WaveformWidget(self)
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Paste YouTube URL")
        self.url_input.setStyleSheet("background: #111827; color: white; border: 1px solid #374151; padding: 8px;")

        self.load_button = QPushButton("Load YouTube")
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.skip_button = QPushButton("Skip")

        self.label = QLabel(f"{deck_name}")
        self.label.setStyleSheet("color: #f9fafb; font-size: 18px; font-weight: 600;")

        self.bpm_label = QLabel("BPM: --")
        self.status_label = QLabel("Status: Idle")
        self.progress_label = QLabel("00:00")

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)

        buttons = QHBoxLayout()
        buttons.addWidget(self.load_button)
        buttons.addWidget(self.play_button)
        buttons.addWidget(self.pause_button)
        buttons.addWidget(self.skip_button)

        meta = QHBoxLayout()
        meta.addWidget(self.bpm_label)
        meta.addWidget(self.status_label)
        meta.addWidget(self.progress_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.url_input)
        layout.addLayout(buttons)
        layout.addWidget(self.waveform)
        layout.addLayout(meta)
        layout.addWidget(QLabel("Deck volume"))
        layout.addWidget(self.volume_slider)

        self.load_button.clicked.connect(self.on_load_clicked)
        self.play_button.clicked.connect(self.on_play_clicked)
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.skip_button.clicked.connect(self.on_skip_clicked)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

    def on_load_clicked(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Paste a YouTube URL first.")
            return

        try:
            path = download_youtube_audio(url)
            deck = self.mixer.deck_a if self.deck_name == "Deck A" else self.mixer.deck_b
            deck.load(path)
            self.waveform.set_data(deck.waveform())
            self.status_label.setText("Status: Loaded")
            self.bpm_label.setText(f"BPM: {120.0:.1f}")
            self.progress_label.setText("00:00")
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Load failed", str(exc))

    def on_play_clicked(self) -> None:
        deck = self.mixer.deck_a if self.deck_name == "Deck A" else self.mixer.deck_b
        deck.playing = True
        self.status_label.setText("Status: Playing")

    def on_pause_clicked(self) -> None:
        deck = self.mixer.deck_a if self.deck_name == "Deck A" else self.mixer.deck_b
        deck.playing = False
        self.status_label.setText("Status: Paused")

    def on_skip_clicked(self) -> None:
        deck = self.mixer.deck_a if self.deck_name == "Deck A" else self.mixer.deck_b
        deck.seek(deck.position + 10.0)

    def on_volume_changed(self, value: int) -> None:
        deck = self.mixer.deck_a if self.deck_name == "Deck A" else self.mixer.deck_b
        deck.set_volume(value / 100.0)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 780)
        self.setStyleSheet("background: #0b1020; color: #f3f4f6; font-family: 'Segoe UI';")

        self.mixer = LiveMixer()
        self.deck_a = DeckPanel("Deck A", self.mixer)
        self.deck_b = DeckPanel("Deck B", self.mixer)

        top = QWidget(self)
        root = QHBoxLayout(top)
        root.addWidget(self.deck_a)
        root.addWidget(self.deck_b)
        self.setCentralWidget(top)

        self._build_transport()

    def _build_transport(self) -> None:
        transport = QWidget(self)
        transport_layout = QHBoxLayout(transport)

        self.crossfader = QSlider(Qt.Horizontal)
        self.crossfader.setRange(0, 100)
        self.crossfader.setValue(50)
        self.crossfader.valueChanged.connect(self.on_crossfader_changed)

        self.master_slider = QSlider(Qt.Horizontal)
        self.master_slider.setRange(0, 100)
        self.master_slider.setValue(80)
        self.master_slider.valueChanged.connect(self.on_master_changed)

        self.automix_toggle = QPushButton("AutoMix OFF")
        self.automix_toggle.setCheckable(True)
        self.automix_toggle.clicked.connect(self.on_automix_toggle)

        self.play_all = QPushButton("Play")
        self.pause_all = QPushButton("Pause")
        self.quit_button = QPushButton("Quit")

        self.play_all.clicked.connect(lambda: self._set_all_play(True))
        self.pause_all.clicked.connect(lambda: self._set_all_play(False))
        self.quit_button.clicked.connect(self.close)

        labels = QLabel("Crossfader")
        labels2 = QLabel("Master")
        transport_layout.addWidget(labels)
        transport_layout.addWidget(self.crossfader)
        transport_layout.addWidget(labels2)
        transport_layout.addWidget(self.master_slider)
        transport_layout.addWidget(self.automix_toggle)
        transport_layout.addWidget(self.play_all)
        transport_layout.addWidget(self.pause_all)
        transport_layout.addWidget(self.quit_button)

        self.addToolBar(Qt.TopToolBarArea, self._build_toolbar(transport))

    def _build_toolbar(self, widget: QWidget):
        from PySide6.QtWidgets import QToolBar

        bar = QToolBar("Transport")
        bar.addWidget(widget)
        return bar

    def on_crossfader_changed(self, value: int) -> None:
        self.mixer.set_crossfader(value / 100.0)

    def on_master_changed(self, value: int) -> None:
        self.mixer.set_master_gain(value / 100.0)

    def on_automix_toggle(self) -> None:
        enabled = self.automix_toggle.isChecked()
        self.mixer.toggle_auto_mix(enabled)
        self.automix_toggle.setText("AutoMix ON" if enabled else "AutoMix OFF")

    def _set_all_play(self, playing: bool) -> None:
        self.mixer.deck_a.playing = playing
        self.mixer.deck_b.playing = playing


def main() -> None:
    app = QApplication([])
    window = MainWindow()
    window.show()
    window.mixer.start()
    app.exec()
