from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
from scipy.signal import resample_poly, welch

from doomforge.audio.io import audio_info, read_audio
from doomforge.models import AudioMetrics

EPS = 1e-12
BANDS = {
    "low": (20.0, 120.0),
    "low_mid": (120.0, 500.0),
    "mid": (500.0, 2000.0),
    "presence": (2000.0, 6000.0),
    "air": (6000.0, 18000.0),
}


def amp_to_db(value: float) -> float:
    return 20.0 * math.log10(max(float(value), EPS))


def _samples_first(audio: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(audio.T)


def integrated_lufs(audio: np.ndarray, sr: int) -> float:
    if audio.size == 0:
        return -120.0
    data = _samples_first(audio)
    min_samples = int(sr * 0.45)
    if data.shape[0] < min_samples:
        pad = np.zeros((min_samples - data.shape[0], data.shape[1]), dtype=np.float32)
        data = np.vstack([data, pad])
    try:
        value = float(pyln.Meter(sr).integrated_loudness(data))
        return value if np.isfinite(value) else -120.0
    except Exception:
        return -120.0


def true_peak_dbtp(audio: np.ndarray, oversample: int = 4) -> float:
    if audio.size == 0:
        return -120.0
    # ITU-style meters use oversampling/reconstruction. This is a conservative 4x approximation.
    max_peak = 0.0
    for channel in audio:
        up = resample_poly(channel.astype(np.float64), oversample, 1)
        max_peak = max(max_peak, float(np.max(np.abs(up), initial=0.0)))
    return amp_to_db(max_peak)


def spectral_bands_db(audio: np.ndarray, sr: int) -> dict[str, float]:
    if audio.size == 0:
        return {name: -120.0 for name in BANDS}
    mono = np.mean(audio, axis=0, dtype=np.float64)
    nperseg = min(len(mono), 8192)
    if nperseg < 256:
        return {name: -120.0 for name in BANDS}
    freqs, power = welch(mono, fs=sr, nperseg=nperseg, noverlap=nperseg // 2)
    result: dict[str, float] = {}
    nyquist = sr / 2
    for name, (lo, hi) in BANDS.items():
        hi = min(hi, nyquist)
        mask = (freqs >= lo) & (freqs < hi)
        energy = float(np.mean(power[mask])) if np.any(mask) else EPS
        result[name] = 10.0 * math.log10(max(energy, EPS))
    return result


def analyze_buffer(audio: np.ndarray, sr: int, *, path: str = "") -> AudioMetrics:
    if audio.ndim == 1:
        audio = audio[np.newaxis, :]
    audio = np.asarray(audio, dtype=np.float32)
    abs_audio = np.abs(audio)
    sample_peak = float(np.max(abs_audio, initial=0.0))
    rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64)))) if audio.size else 0.0
    sample_peak_db = amp_to_db(sample_peak)
    rms_db = amp_to_db(rms)
    clip_pct = float(np.mean(abs_audio >= 0.999) * 100.0) if audio.size else 0.0
    corr = None
    if audio.shape[0] >= 2 and audio.shape[1] > 32:
        left = audio[0].astype(np.float64)
        right = audio[1].astype(np.float64)
        if np.std(left) > EPS and np.std(right) > EPS:
            corr = float(np.corrcoef(left, right)[0, 1])
    return AudioMetrics(
        path=path,
        duration_s=audio.shape[1] / sr if sr else 0.0,
        sample_rate=sr,
        channels=audio.shape[0],
        integrated_lufs=integrated_lufs(audio, sr),
        sample_peak_dbfs=sample_peak_db,
        true_peak_dbtp=true_peak_dbtp(audio),
        rms_dbfs=rms_db,
        crest_factor_db=max(0.0, sample_peak_db - rms_db),
        clipping_percent=clip_pct,
        stereo_correlation=corr,
        spectral_bands_db=spectral_bands_db(audio, sr),
    )


def analyze_file(path: str | Path, *, analysis_limit_s: float = 300.0) -> AudioMetrics:
    sr, channels, duration = audio_info(path)
    # Long concert recordings are sampled from the first 5 minutes for responsive UI analysis.
    # Full output is measured after render.
    audio, read_sr = read_audio(path, start_s=0.0, duration_s=min(duration, analysis_limit_s))
    metrics = analyze_buffer(audio, read_sr, path=str(path))
    metrics.duration_s = duration
    metrics.sample_rate = sr
    metrics.channels = channels
    return metrics
