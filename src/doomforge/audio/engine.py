from __future__ import annotations

import tempfile
from pathlib import Path

from doomforge.audio.analysis import analyze_buffer, analyze_file
from doomforge.audio.dsp import process_buffer
from doomforge.audio.io import read_audio, write_audio, write_preview_wav
from doomforge.models import AudioMetrics, MasteringSettings, RenderReport


class MasteringEngine:
    def analyze(self, path: str) -> AudioMetrics:
        return analyze_file(path)

    def preview(self, path: str, settings: MasteringSettings) -> tuple[Path, Path, AudioMetrics]:
        audio, sr = read_audio(
            path,
            start_s=max(0.0, settings.preview_start_s),
            duration_s=max(3.0, settings.preview_duration_s),
        )
        processed = process_buffer(audio, sr, settings)
        directory = Path(tempfile.mkdtemp(prefix="doomforge_preview_"))
        original_path = write_preview_wav(directory / "original.wav", audio, sr)
        processed_path = write_preview_wav(directory / "mastered.wav", processed, sr)
        metrics = analyze_buffer(processed, sr, path=str(processed_path))
        return original_path, processed_path, metrics

    def render(self, source_path: str, output_path: str, settings: MasteringSettings) -> RenderReport:
        source_metrics = analyze_file(source_path)
        audio, sr = read_audio(source_path)
        processed = process_buffer(audio, sr, settings)
        out = write_audio(output_path, processed, sr)
        output_metrics = analyze_buffer(processed, sr, path=str(out))
        warnings: list[str] = []
        if source_metrics.clipping_percent > 0.01:
            warnings.append(
                "La fuente ya contiene muestras cerca de 0 dBFS; el mastering evita nuevos clips, "
                "pero no puede reconstruir perfectamente una onda recortada por el micrófono."
            )
        if output_metrics.true_peak_dbtp > settings.true_peak_ceiling_dbtp + 0.1:
            warnings.append("El true-peak final quedó por encima del techo solicitado; revisa el archivo.")
        return RenderReport(source_metrics, output_metrics, str(out), warnings)
