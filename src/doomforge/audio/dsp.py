from __future__ import annotations

import math

import noisereduce as nr
import numpy as np
from scipy.ndimage import minimum_filter1d
from pedalboard import (
    Compressor,
    Gain,
    HighShelfFilter,
    HighpassFilter,
    LowShelfFilter,
    PeakFilter,
    Pedalboard,
)

from doomforge.audio.analysis import integrated_lufs, true_peak_dbtp
from doomforge.models import MasteringSettings


def _db_to_gain(db: float) -> float:
    return 10.0 ** (db / 20.0)


def apply_denoise(audio: np.ndarray, sr: int, amount: float) -> np.ndarray:
    amount = float(min(0.8, max(0.0, amount)))
    if amount <= 0.001:
        return audio
    return np.asarray(
        nr.reduce_noise(
            y=audio,
            sr=sr,
            stationary=False,
            prop_decrease=amount,
            time_constant_s=1.5,
            freq_mask_smooth_hz=250,
            time_mask_smooth_ms=75,
            n_jobs=1,
        ),
        dtype=np.float32,
    )


def apply_soft_saturation(audio: np.ndarray, drive_db: float) -> np.ndarray:
    if abs(drive_db) < 0.01:
        return audio
    drive = _db_to_gain(max(0.0, drive_db))
    norm = math.tanh(drive)
    if norm == 0:
        return audio
    saturated = np.tanh(audio * drive) / norm
    mix = min(0.35, max(0.0, drive_db / 12.0))
    return ((1.0 - mix) * audio + mix * saturated).astype(np.float32)


def apply_stereo_width(audio: np.ndarray, width: float) -> np.ndarray:
    if audio.shape[0] < 2:
        return audio
    width = min(1.5, max(0.0, width))
    out = audio.copy()
    left, right = out[0], out[1]
    mid = (left + right) * 0.5
    side = (left - right) * 0.5 * width
    out[0] = mid + side
    out[1] = mid - side
    return out


def build_board(settings: MasteringSettings) -> Pedalboard:
    plugins = [
        Gain(gain_db=settings.input_gain_db),
        HighpassFilter(cutoff_frequency_hz=settings.highpass_hz),
        LowShelfFilter(cutoff_frequency_hz=110, gain_db=settings.low_shelf_db, q=0.707),
        PeakFilter(cutoff_frequency_hz=300, gain_db=settings.low_mid_db, q=0.85),
        PeakFilter(cutoff_frequency_hz=1200, gain_db=settings.mid_db, q=0.75),
        PeakFilter(cutoff_frequency_hz=3800, gain_db=settings.presence_db, q=0.8),
        HighShelfFilter(cutoff_frequency_hz=8500, gain_db=settings.air_shelf_db, q=0.707),
        Compressor(
            threshold_db=settings.compressor_threshold_db,
            ratio=settings.compressor_ratio,
            attack_ms=settings.compressor_attack_ms,
            release_ms=settings.compressor_release_ms,
        ),
    ]
    return Pedalboard(plugins)


def apply_peak_limiter(
    audio: np.ndarray,
    sr: int,
    ceiling_db: float,
    release_ms: float,
    lookahead_ms: float = 2.0,
) -> np.ndarray:
    """Offline linked-channel limiter that only attenuates.

    A short acausal lookahead window anticipates peaks. The final oversampled safety trim
    below handles inter-sample peaks, so this stage never needs makeup gain.
    """
    if audio.size == 0:
        return audio
    ceiling = _db_to_gain(ceiling_db)
    peak = np.max(np.abs(audio), axis=0)
    desired = np.minimum(1.0, ceiling / np.maximum(peak, 1e-12))
    lookahead = max(1, int(sr * max(0.0, lookahead_ms) / 1000.0))
    if lookahead > 1:
        desired = minimum_filter1d(desired, size=lookahead * 2 + 1, mode="nearest")

    release_s = max(0.005, release_ms / 1000.0)
    alpha = math.exp(-1.0 / (sr * release_s))
    gain = np.empty_like(desired, dtype=np.float64)
    gain[0] = desired[0]
    for i in range(1, len(desired)):
        if desired[i] < gain[i - 1]:
            gain[i] = desired[i]
        else:
            gain[i] = alpha * gain[i - 1] + (1.0 - alpha) * desired[i]
    return (audio * gain[np.newaxis, :]).astype(np.float32)


def process_buffer(audio: np.ndarray, sr: int, settings: MasteringSettings) -> np.ndarray:
    x = np.asarray(audio, dtype=np.float32)
    if x.ndim == 1:
        x = x[np.newaxis, :]
    if settings.denoise_enabled:
        x = apply_denoise(x, sr, settings.denoise_amount)

    x = build_board(settings)(x, sr).astype(np.float32)
    x = apply_soft_saturation(x, settings.saturation_drive_db)
    x = apply_stereo_width(x, settings.stereo_width)

    if settings.normalize_loudness:
        current = integrated_lufs(x, sr)
        if current > -100:
            gain_db = min(12.0, max(-12.0, settings.target_lufs - current))
            x = Gain(gain_db=gain_db)(x, sr).astype(np.float32)

    # Linked-channel limiter only attenuates; oversampled safety trim enforces dBTP ceiling.
    x = apply_peak_limiter(
        x,
        sr,
        ceiling_db=settings.true_peak_ceiling_dbtp,
        release_ms=settings.limiter_release_ms,
    )

    measured_tp = true_peak_dbtp(x)
    if measured_tp > settings.true_peak_ceiling_dbtp:
        trim_db = settings.true_peak_ceiling_dbtp - measured_tp - 0.05
        x *= _db_to_gain(trim_db)
    return np.nan_to_num(x, copy=False).astype(np.float32)
