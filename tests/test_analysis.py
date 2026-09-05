import numpy as np

from doomforge.audio.analysis import analyze_buffer, true_peak_dbtp


def test_analysis_sine_has_expected_peak():
    sr = 48000
    t = np.arange(sr, dtype=np.float32) / sr
    x = (0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)[None, :]
    m = analyze_buffer(x, sr)
    assert -6.2 < m.sample_peak_dbfs < -5.8
    assert -6.2 < true_peak_dbtp(x) < -5.7
    assert m.clipping_percent == 0
