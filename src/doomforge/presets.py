from __future__ import annotations

from doomforge.models import MasteringSettings


PRESETS: dict[str, MasteringSettings] = {
    "Phone Rescue / Live": MasteringSettings(),
    "Streaming Balanced": MasteringSettings(
        preset_name="Streaming Balanced",
        denoise_amount=0.12,
        highpass_hz=28,
        low_shelf_db=-0.4,
        low_mid_db=-0.8,
        presence_db=0.4,
        air_shelf_db=0.4,
        compressor_threshold_db=-18,
        compressor_ratio=1.8,
        compressor_attack_ms=28,
        compressor_release_ms=220,
        saturation_drive_db=0.3,
        stereo_width=1.02,
        target_lufs=-14,
        true_peak_ceiling_dbtp=-1.0,
    ),
    "Doom / Heavy": MasteringSettings(
        preset_name="Doom / Heavy",
        denoise_amount=0.10,
        highpass_hz=25,
        low_shelf_db=0.7,
        low_mid_db=-1.0,
        mid_db=0.3,
        presence_db=0.2,
        air_shelf_db=-0.2,
        compressor_threshold_db=-19,
        compressor_ratio=2.4,
        compressor_attack_ms=30,
        compressor_release_ms=240,
        saturation_drive_db=1.1,
        stereo_width=1.04,
        target_lufs=-10.5,
        true_peak_ceiling_dbtp=-1.0,
    ),
    "Dynamic Archive": MasteringSettings(
        preset_name="Dynamic Archive",
        denoise_amount=0.08,
        highpass_hz=25,
        low_shelf_db=0.0,
        low_mid_db=-0.5,
        presence_db=0.0,
        air_shelf_db=0.0,
        compressor_threshold_db=-16,
        compressor_ratio=1.5,
        compressor_attack_ms=35,
        compressor_release_ms=280,
        saturation_drive_db=0.0,
        stereo_width=1.0,
        target_lufs=-16,
        true_peak_ceiling_dbtp=-1.5,
    ),
}


def get_preset(name: str) -> MasteringSettings:
    return PRESETS.get(name, PRESETS["Phone Rescue / Live"]).copy()
