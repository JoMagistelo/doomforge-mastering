from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Callable

import flet as ft
import flet_audio as fta

from doomforge.audio.engine import MasteringEngine
from doomforge.audio.io import SUPPORTED_EXPORT, SUPPORTED_IMPORT
from doomforge.audio.reference import suggest_from_reference
from doomforge.models import AudioMetrics, MasteringSettings
from doomforge.presets import PRESETS, get_preset
from doomforge.ui import theme as c
from doomforge.ui.components import (
    action_button,
    metric_chip,
    panel,
    parameter_row,
    section_title,
    status_pill,
)

Formatter = Callable[[float], str]
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


class DoomForgeApp:
    """Flet desktop shell around the testable mastering engine."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.engine = MasteringEngine()
        self.settings = get_preset("Phone Rescue / Live")
        self.source_path: str | None = None
        self.reference_path: str | None = None
        self.source_metrics: AudioMetrics | None = None
        self.reference_metrics: AudioMetrics | None = None
        self.preview_original: Path | None = None
        self.preview_mastered: Path | None = None

        self.value_texts: dict[str, ft.Text] = {}
        self.value_formatters: dict[str, Formatter] = {}
        self.spectrum_bars: list[ft.Container] = []

        self.file_picker = ft.FilePicker()
        self.reference_picker = ft.FilePicker()
        page.services.extend([self.file_picker, self.reference_picker])
        self.player = fta.Audio(autoplay=False, volume=1.0, release_mode=fta.ReleaseMode.STOP)
        page.services.append(self.player)

        self.status = ft.Text("Carga una pista para comenzar.", color=c.MUTED, size=10.5, max_lines=2)
        self.progress = ft.ProgressBar(
            value=0,
            visible=False,
            color=c.PURPLE_HOT,
            bgcolor=c.SURFACE_3,
            height=2,
        )
        self.source_label = ft.Text("Sin pista", color=c.MUTED, size=10.5, max_lines=1)
        self.reference_label = ft.Text("Sin referencia", color=c.MUTED, size=10.5, max_lines=1)
        self.reference_summary = ft.Text("", color=c.MUTED, size=9.5, max_lines=2)
        self.preview_metrics = ft.Text("Aún no hay preview.", color=c.MUTED, size=9.5)
        self.metrics_row = ft.Row(wrap=True, spacing=6, run_spacing=6)
        self.spectrum = self._build_spectrum()

        self._configure_page()
        self._build_controls()
        self._render()

    def _configure_page(self) -> None:
        self.page.title = "DoomForge Mastering Studio"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = c.BLACK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme = ft.Theme(
            color_scheme_seed=c.PURPLE,
            use_material3=True,
            font_family="Segoe UI",
            visual_density=ft.VisualDensity.COMPACT,
        )
        self.page.window.width = 1320
        self.page.window.height = 820
        self.page.window.min_width = 1024
        self.page.window.min_height = 680

    def _slider(
        self,
        key: str,
        value: float,
        min_v: float,
        max_v: float,
        divisions: int,
        formatter: Formatter,
    ) -> ft.Slider:
        value_text = ft.Text(
            formatter(float(value)), size=10, color=c.PURPLE_SOFT, weight=ft.FontWeight.W_600
        )
        self.value_texts[key] = value_text
        self.value_formatters[key] = formatter

        def on_change(event) -> None:
            value_text.value = formatter(float(event.control.value))
            self._sync_settings()
            value_text.update()

        return ft.Slider(
            value=value,
            min=min_v,
            max=max_v,
            divisions=divisions,
            active_color=c.PURPLE_HOT,
            inactive_color=c.SURFACE_3,
            on_change=on_change,
            height=27,
        )

    def _build_controls(self) -> None:
        s = self.settings
        self.preset = ft.Dropdown(
            value=s.preset_name,
            options=[ft.DropdownOption(key=k, text=k) for k in PRESETS],
            on_select=self.on_preset,
            dense=True,
            width=220,
            text_size=11,
        )
        self.export_format = ft.Dropdown(
            value=".wav",
            options=[ft.DropdownOption(key=e, text=e.upper().lstrip(".")) for e in SUPPORTED_EXPORT],
            dense=True,
            width=104,
            text_size=11,
        )

        self.input_gain = self._slider("input_gain", s.input_gain_db, -12, 12, 96, lambda v: f"{v:+.1f} dB")
        self.denoise_switch = ft.Switch(value=s.denoise_enabled, active_color=c.PURPLE_HOT, on_change=self._sync_settings, scale=0.8)
        self.denoise = self._slider("denoise", s.denoise_amount, 0, 0.8, 80, lambda v: f"{v * 100:.0f}%")
        self.highpass = self._slider("highpass", s.highpass_hz, 20, 80, 120, lambda v: f"{v:.0f} Hz")
        self.low = self._slider("low", s.low_shelf_db, -6, 6, 120, lambda v: f"{v:+.1f} dB")
        self.lowmid = self._slider("lowmid", s.low_mid_db, -6, 6, 120, lambda v: f"{v:+.1f} dB")
        self.mid = self._slider("mid", s.mid_db, -6, 6, 120, lambda v: f"{v:+.1f} dB")
        self.presence = self._slider("presence", s.presence_db, -6, 6, 120, lambda v: f"{v:+.1f} dB")
        self.air = self._slider("air", s.air_shelf_db, -6, 6, 120, lambda v: f"{v:+.1f} dB")
        self.comp_threshold = self._slider("threshold", s.compressor_threshold_db, -40, -6, 136, lambda v: f"{v:.1f} dB")
        self.comp_ratio = self._slider("ratio", s.compressor_ratio, 1, 6, 100, lambda v: f"{v:.1f}:1")
        self.attack = self._slider("attack", s.compressor_attack_ms, 1, 100, 99, lambda v: f"{v:.0f} ms")
        self.release = self._slider("release", s.compressor_release_ms, 40, 500, 92, lambda v: f"{v:.0f} ms")
        self.saturation = self._slider("saturation", s.saturation_drive_db, 0, 6, 120, lambda v: f"{v:.1f} dB")
        self.width = self._slider("width", s.stereo_width, 0.5, 1.5, 100, lambda v: f"{v:.2f}×")
        self.normalize_switch = ft.Switch(value=s.normalize_loudness, active_color=c.PURPLE_HOT, on_change=self._sync_settings, scale=0.8)
        self.target_lufs = self._slider("lufs", s.target_lufs, -18, -8, 100, lambda v: f"{v:.1f} LUFS")
        self.true_peak = self._slider("true_peak", s.true_peak_ceiling_dbtp, -3, -0.3, 54, lambda v: f"{v:.1f} dBTP")
        self.reference_strength = self._slider("reference", s.reference_match_strength, 0, 1, 100, lambda v: f"{v * 100:.0f}%")
        self.preview_start = ft.TextField(
            value=str(s.preview_start_s), width=82, height=36, dense=True, suffix="s", text_size=11,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        )
        self.preview_duration = ft.TextField(
            value=str(s.preview_duration_s), width=82, height=36, dense=True, suffix="s", text_size=11,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        )

    def _sync_settings(self, _=None) -> None:
        s = self.settings
        s.input_gain_db = float(self.input_gain.value)
        s.denoise_enabled = bool(self.denoise_switch.value)
        s.denoise_amount = float(self.denoise.value)
        s.highpass_hz = float(self.highpass.value)
        s.low_shelf_db = float(self.low.value)
        s.low_mid_db = float(self.lowmid.value)
        s.mid_db = float(self.mid.value)
        s.presence_db = float(self.presence.value)
        s.air_shelf_db = float(self.air.value)
        s.compressor_threshold_db = float(self.comp_threshold.value)
        s.compressor_ratio = float(self.comp_ratio.value)
        s.compressor_attack_ms = float(self.attack.value)
        s.compressor_release_ms = float(self.release.value)
        s.saturation_drive_db = float(self.saturation.value)
        s.stereo_width = float(self.width.value)
        s.normalize_loudness = bool(self.normalize_switch.value)
        s.target_lufs = float(self.target_lufs.value)
        s.true_peak_ceiling_dbtp = float(self.true_peak.value)
        s.reference_match_strength = float(self.reference_strength.value)
        try:
            s.preview_start_s = max(0.0, float(self.preview_start.value or 0))
            s.preview_duration_s = min(60.0, max(3.0, float(self.preview_duration.value or 20)))
        except ValueError:
            pass

    def _apply_settings_to_ui(self) -> None:
        s = self.settings
        values = {
            "input_gain": (self.input_gain, s.input_gain_db), "denoise": (self.denoise, s.denoise_amount),
            "highpass": (self.highpass, s.highpass_hz), "low": (self.low, s.low_shelf_db),
            "lowmid": (self.lowmid, s.low_mid_db), "mid": (self.mid, s.mid_db),
            "presence": (self.presence, s.presence_db), "air": (self.air, s.air_shelf_db),
            "threshold": (self.comp_threshold, s.compressor_threshold_db), "ratio": (self.comp_ratio, s.compressor_ratio),
            "attack": (self.attack, s.compressor_attack_ms), "release": (self.release, s.compressor_release_ms),
            "saturation": (self.saturation, s.saturation_drive_db), "width": (self.width, s.stereo_width),
            "lufs": (self.target_lufs, s.target_lufs), "true_peak": (self.true_peak, s.true_peak_ceiling_dbtp),
            "reference": (self.reference_strength, s.reference_match_strength),
        }
        for key, (control, value) in values.items():
            control.value = value
            self.value_texts[key].value = self.value_formatters[key](float(value))
        self.denoise_switch.value = s.denoise_enabled
        self.normalize_switch.value = s.normalize_loudness
        self.preview_start.value = str(s.preview_start_s)
        self.preview_duration.value = str(s.preview_duration_s)
        self.preset.value = s.preset_name
        self.page.update()

    def _set_busy(self, message: str) -> None:
        self.status.value = message
        self.status.color = c.PURPLE_SOFT
        self.progress.visible = True
        self.progress.value = None
        self.page.update()

    def _build_spectrum(self) -> ft.Column:
        cells: list[ft.Control] = []
        for label in ("SUB", "BODY", "MID", "PRES", "AIR"):
            bar = ft.Container(
                width=24,
                height=10,
                border_radius=4,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.BOTTOM_CENTER,
                    end=ft.Alignment.TOP_CENTER,
                    colors=[c.PURPLE_DARK, c.PURPLE_HOT, c.PURPLE_SOFT],
                ),
            )
            self.spectrum_bars.append(bar)
            cells.append(ft.Column([
                ft.Container(content=bar, height=58, alignment=ft.Alignment.BOTTOM_CENTER),
                ft.Text(label, size=7.5, color=c.MUTED_2),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        return ft.Column([
            ft.Text("ENERGÍA ESPECTRAL", size=8.5, color=c.MUTED_2),
            ft.Row(cells, spacing=12, alignment=ft.MainAxisAlignment.SPACE_AROUND, vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=4)

    def _show_metrics(self, m: AudioMetrics) -> None:
        self.metrics_row.controls = [
            metric_chip("LUFS-I", f"{m.integrated_lufs:.1f}", -16.5 <= m.integrated_lufs <= -8.5),
            metric_chip("True Peak", f"{m.true_peak_dbtp:.2f} dBTP", m.true_peak_dbtp <= -0.8),
            metric_chip("Crest", f"{m.crest_factor_db:.1f} dB", m.crest_factor_db >= 6),
            metric_chip("Clipping", f"{m.clipping_percent:.3f}%", m.clipping_percent < 0.01),
        ]
        values = [m.spectral_bands_db.get(k, -120.0) for k in ("low", "low_mid", "mid", "presence", "air")]
        ceiling = max(values) if values else -30.0
        floor = ceiling - 36.0
        for bar, value in zip(self.spectrum_bars, values):
            norm = min(1.0, max(0.08, (value - floor) / max(1.0, ceiling - floor)))
            bar.height = 8 + 46 * norm
        self.page.update()

    async def choose_source(self, _):
        files = await self.file_picker.pick_files(
            allow_multiple=False, file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[x.lstrip(".") for x in SUPPORTED_IMPORT],
        )
        if not files or not files[0].path:
            return
        self.source_path = files[0].path
        self.source_label.value = files[0].name
        self._set_busy("Analizando pista: loudness, true-peak, crest y espectro…")
        try:
            self.source_metrics = await asyncio.to_thread(self.engine.analyze, self.source_path)
            self._show_metrics(self.source_metrics)
            self.status.value = "Pista analizada. Ajusta la cadena o genera un preview A/B."
            self.status.color = c.GREEN
        except Exception as exc:
            self.status.value = f"Error al analizar: {exc}"
            self.status.color = c.RED
        finally:
            self.progress.visible = False
            self.page.update()

    async def choose_reference(self, _):
        files = await self.reference_picker.pick_files(
            allow_multiple=False, file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[x.lstrip(".") for x in SUPPORTED_IMPORT],
        )
        if not files or not files[0].path:
            return
        self.reference_path = files[0].path
        self.reference_label.value = files[0].name
        self._set_busy("Analizando referencia…")
        try:
            self.reference_metrics = await asyncio.to_thread(self.engine.analyze, self.reference_path)
            self.reference_summary.value = f"{self.reference_metrics.integrated_lufs:.1f} LUFS-I · {self.reference_metrics.true_peak_dbtp:.2f} dBTP"
            self.status.value = "Referencia lista. Puedes aplicar su tendencia tonal de forma segura."
            self.status.color = c.GREEN
        except Exception as exc:
            self.status.value = f"Error en referencia: {exc}"
            self.status.color = c.RED
        finally:
            self.progress.visible = False
            self.page.update()

    def on_preset(self, _):
        self.settings = get_preset(self.preset.value or "Phone Rescue / Live")
        self._apply_settings_to_ui()
        self.status.value = f"Preset cargado: {self.settings.preset_name}."
        self.status.color = c.PURPLE_SOFT
        self.page.update()

    def match_reference(self, _):
        self._sync_settings()
        if not self.source_metrics or not self.reference_metrics:
            self.status.value = "Carga primero la pista y una referencia."
            self.status.color = c.AMBER
            self.page.update()
            return
        suggestion = suggest_from_reference(self.source_metrics, self.reference_metrics, strength=self.settings.reference_match_strength)
        self.settings.target_lufs = suggestion.target_lufs
        self.settings.low_shelf_db = suggestion.eq_db["low"]
        self.settings.low_mid_db = suggestion.eq_db["low_mid"]
        self.settings.mid_db = suggestion.eq_db["mid"]
        self.settings.presence_db = suggestion.eq_db["presence"]
        self.settings.air_shelf_db = suggestion.eq_db["air"]
        self._apply_settings_to_ui()
        self.status.value = f"Reference Match aplicado con límites seguros · objetivo {suggestion.target_lufs:.1f} LUFS."
        self.status.color = c.PURPLE_SOFT
        self.page.update()

    async def make_preview(self, _):
        if not self.source_path:
            self.status.value = "Primero carga una pista."
            self.status.color = c.AMBER
            self.page.update()
            return
        self._sync_settings()
        self._set_busy("Forjando preview A/B…")
        try:
            original, mastered, metrics = await asyncio.to_thread(self.engine.preview, self.source_path, self.settings.copy())
            self.preview_original, self.preview_mastered = original, mastered
            self.preview_metrics.value = (
                f"MASTER PREVIEW · {metrics.integrated_lufs:.1f} LUFS-I · "
                f"{metrics.true_peak_dbtp:.2f} dBTP · crest {metrics.crest_factor_db:.1f} dB"
            )
            self.status.value = "Preview listo. Compara Original / Master al mismo fragmento."
            self.status.color = c.GREEN
        except Exception as exc:
            self.status.value = f"Error en preview: {exc}"
            self.status.color = c.RED
        finally:
            self.progress.visible = False
            self.page.update()

    async def _play_path(self, path: Path | None):
        if not path or not path.exists():
            self.status.value = "Primero genera el preview."
            self.status.color = c.AMBER
            self.page.update()
            return
        await self.player.release()
        self.player.src = path.read_bytes()
        self.page.update()
        await self.player.play()

    async def play_original(self, _):
        await self._play_path(self.preview_original)

    async def play_mastered(self, _):
        await self._play_path(self.preview_mastered)

    async def play_reference(self, _):
        if not self.reference_path:
            self.status.value = "Carga una referencia."
            self.status.color = c.AMBER
            self.page.update()
            return
        from doomforge.audio.io import read_audio, write_preview_wav
        try:
            self._sync_settings()
            audio, sr = await asyncio.to_thread(
                read_audio, self.reference_path,
                start_s=self.settings.preview_start_s,
                duration_s=self.settings.preview_duration_s,
            )
            path = Path(tempfile.mkdtemp(prefix="doomforge_ref_")) / "reference.wav"
            await asyncio.to_thread(write_preview_wav, path, audio, sr)
            await self._play_path(path)
        except Exception as exc:
            self.status.value = f"No se pudo reproducir la referencia: {exc}"
            self.status.color = c.RED
            self.page.update()

    async def pause(self, _):
        await self.player.pause()

    async def render_master(self, _):
        if not self.source_path:
            self.status.value = "Primero carga una pista."
            self.status.color = c.AMBER
            self.page.update()
            return
        self._sync_settings()
        ext = self.export_format.value or ".wav"
        output = await self.file_picker.save_file(
            dialog_title="Guardar master",
            file_name=f"{Path(self.source_path).stem}_MASTER{ext}",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[ext.lstrip(".")],
        )
        if not output:
            return
        output_path = str(Path(output).with_suffix(ext))
        self._set_busy("Renderizando master completo…")
        try:
            report = await asyncio.to_thread(self.engine.render, self.source_path, output_path, self.settings.copy())
            self.status.value = (
                f"Master listo · {Path(report.output_path).name} · "
                f"{report.output.integrated_lufs:.1f} LUFS-I · {report.output.true_peak_dbtp:.2f} dBTP"
            )
            self.status.color = c.GREEN
            if report.warnings:
                self.status.value += " · " + " ".join(report.warnings)
        except Exception as exc:
            self.status.value = f"Error al renderizar: {exc}"
            self.status.color = c.RED
        finally:
            self.progress.visible = False
            self.page.update()

    def _render(self) -> None:
        from doomforge.ui.workspace import build_shell

        build_shell(self)


def main(page: ft.Page):
    DoomForgeApp(page)


def run():
    ft.run(main, assets_dir=str(ASSETS_DIR))
