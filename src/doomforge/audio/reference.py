from __future__ import annotations

from doomforge.models import AudioMetrics, ReferenceSuggestion


def suggest_from_reference(
    source: AudioMetrics,
    reference: AudioMetrics,
    *,
    strength: float = 0.65,
) -> ReferenceSuggestion:
    strength = min(1.0, max(0.0, strength))
    eq: dict[str, float] = {}
    for band in ("low", "low_mid", "mid", "presence", "air"):
        src = source.spectral_bands_db.get(band, -120.0)
        ref = reference.spectral_bands_db.get(band, -120.0)
        # Half the raw spectral difference prevents overfitting different arrangements.
        adjustment = (ref - src) * 0.5 * strength
        eq[band] = round(min(3.0, max(-3.0, adjustment)), 2)

    # A reference louder than -9 LUFS is deliberately not copied literally.
    ref_target = min(-9.0, max(-16.0, reference.integrated_lufs))
    target = source.integrated_lufs + (ref_target - source.integrated_lufs) * strength
    target = round(min(-9.0, max(-16.0, target)), 1)

    return ReferenceSuggestion(
        target_lufs=target,
        eq_db=eq,
        explanation=(
            "La referencia se usa como brújula tonal, no como molde absoluto. "
            "Los cambios se limitan a ±3 dB por banda y el objetivo de loudness a -16…-9 LUFS."
        ),
    )
