from doomforge.audio.reference import suggest_from_reference
from doomforge.models import AudioMetrics


def test_reference_limits_adjustments_and_loudness():
    src = AudioMetrics(integrated_lufs=-22, spectral_bands_db={k: -40 for k in ["low", "low_mid", "mid", "presence", "air"]})
    ref = AudioMetrics(integrated_lufs=-5, spectral_bands_db={k: -10 for k in ["low", "low_mid", "mid", "presence", "air"]})
    s = suggest_from_reference(src, ref, strength=1.0)
    assert s.target_lufs == -9.0
    assert all(v == 3.0 for v in s.eq_db.values())
