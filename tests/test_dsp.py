import numpy as np

from doomforge.audio.analysis import integrated_lufs, true_peak_dbtp
from doomforge.audio.dsp import process_buffer
from doomforge.models import MasteringSettings


def test_mastering_respects_true_peak_ceiling():
    sr = 48000
    rng = np.random.default_rng(7)
    x = (rng.normal(0, 0.2, size=(2, sr * 2))).astype(np.float32)
    settings = MasteringSettings(denoise_enabled=False, target_lufs=-10, true_peak_ceiling_dbtp=-1.0)
    y = process_buffer(x, sr, settings)
    assert y.shape == x.shape
    assert np.isfinite(y).all()
    assert true_peak_dbtp(y) <= -0.90


def test_loudness_normalization_does_not_overshoot_target():
    sr = 48000
    t = np.arange(sr * 3, dtype=np.float32) / sr
    tone = (0.12 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    x = np.vstack([tone, tone])
    settings = MasteringSettings(denoise_enabled=False, target_lufs=-12.0, true_peak_ceiling_dbtp=-1.0)
    y = process_buffer(x, sr, settings)
    assert integrated_lufs(y, sr) <= -11.7
    assert integrated_lufs(y, sr) >= -12.4
