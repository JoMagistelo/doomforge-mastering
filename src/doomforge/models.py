from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AudioMetrics:
    path: str = ""
    duration_s: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    integrated_lufs: float = -120.0
    sample_peak_dbfs: float = -120.0
    true_peak_dbtp: float = -120.0
    rms_dbfs: float = -120.0
    crest_factor_db: float = 0.0
    clipping_percent: float = 0.0
    stereo_correlation: float | None = None
    spectral_bands_db: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MasteringSettings:
    preset_name: str = "Phone Rescue / Live"
    input_gain_db: float = 0.0
    denoise_enabled: bool = True
    denoise_amount: float = 0.22
    highpass_hz: float = 32.0

    low_shelf_db: float = -0.8
    low_mid_db: float = -1.5
    mid_db: float = 0.0
    presence_db: float = 0.8
    air_shelf_db: float = 0.5

    compressor_threshold_db: float = -20.0
    compressor_ratio: float = 2.2
    compressor_attack_ms: float = 22.0
    compressor_release_ms: float = 180.0

    saturation_drive_db: float = 0.7
    stereo_width: float = 1.05

    normalize_loudness: bool = True
    target_lufs: float = -12.0
    true_peak_ceiling_dbtp: float = -1.0
    limiter_release_ms: float = 100.0

    reference_match_strength: float = 0.65

    preview_start_s: float = 30.0
    preview_duration_s: float = 20.0

    def copy(self) -> "MasteringSettings":
        return MasteringSettings(**asdict(self))


@dataclass(slots=True)
class ReferenceSuggestion:
    target_lufs: float
    eq_db: dict[str, float]
    explanation: str


@dataclass(slots=True)
class RenderReport:
    source: AudioMetrics
    output: AudioMetrics
    output_path: str
    warnings: list[str] = field(default_factory=list)
