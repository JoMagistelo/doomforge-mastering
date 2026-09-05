from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import flet as ft
import flet_audio as fta

from doomforge.audio.engine import MasteringEngine
from doomforge.audio.io import SUPPORTED_EXPORT, SUPPORTED_IMPORT
from doomforge.audio.reference import suggest_from_reference
from doomforge.models import AudioMetrics, MasteringSettings
from doomforge.presets import PRESETS, get_preset
from doomforge.ui import theme as c
from doomforge.ui.components import metric_chip, panel, parameter_row, section_title


class DoomForgeApp:
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

        self.file_picker = ft.FilePicker()
        self.reference_picker = ft.FilePicker()
        page.services.extend([self.file_picker, self.reference_picker])

        self.player = fta.Audio(autoplay=False, volume=1.0, release_mode=fta.ReleaseMode.STOP)
        page.services.append(self.player)

        self.status = ft.Text("Carga una pista para comenzar.", color=c.MUTED, size=12)
        self.progress = ft.ProgressBar(value=0, visible=False, color=c.PURPLE, bgcolor=c.PANEL_2)
        self.source_label = ft.Text("Sin pista", color=c.MUTED, max_lines=1)
        self.reference_label = ft.Text("Sin referencia", color=c.MUTED, max_lines=1)
        self.metrics_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
        self.preview_metrics = ft.Text("", color=c.MUTED, size=11)

        self._build_controls()
        self._configure_page()
        self._render()

    def _configure_page(self):
        self.page.title = "DoomForge Mastering Studio"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = c.BLACK
        self.page.padding = 0
        self.page.window.width = 1320
        self.page.window.height = 860
        self.page.window.min_width = 980
        self.page.window.min_height = 700

    def _slider(self, value, min_v, max_v, divisions=100, on_change=None):
        return ft.Slider(
            value=value,
            min=min_v,
            max=max_v,
            divisions=divisions,
            active_color=c.PURPLE,
            inactive_color=c.BORDER,
            on_change=on_change,
        )

    def _build_controls(self):
        self.preset = ft.Dropdown(
            value=self.settings.preset_name,
            options=[ft.DropdownOption(key=k, text=k) for k in PRESETS],
            on_select=self.on_preset,
            dense=True,
            width=240,
        )
        self.export_format = ft.Dropdown(
            value=".wav",
            options=[ft.DropdownOption(key=e, text=e.upper().lstrip(".")) for e in SUPPORTED_EXPORT],
            dense=True,
            width=130,
        )

        self.input_gain = self._slider(self.settings.input_gain_db, -12, 12, 96, self._sync_settings)
        self.denoise_switch = ft.Switch(value=self.settings.denoise_enabled, active_color=c.PURPLE, on_change=self._sync_settings)
        self.denoise = self._slider(self.settings.denoise_amount, 0, 0.8, 80, self._sync_settings)
        self.highpass = self._slider(self.settings.highpass_hz, 20, 80, 120, self._sync_settings)

        self.low = self._slider(self.settings.low_shelf_db, -6, 6, 120, self._sync_settings)
        self.lowmid = self._slider(self.settings.low_mid_db, -6, 6, 120, self._sync_settings)
        self.mid = self._slider(self.settings.mid_db, -6, 6, 120, self._sync_settings)
        self.presence = self._slider(self.settings.presence_db, -6, 6, 120, self._sync_settings)
        self.air = self._slider(self.settings.air_shelf_db, -6, 6, 120, self._sync_settings)

        self.comp_threshold = self._slider(self.settings.compressor_threshold_db, -40, -6, 136, self._sync_settings)
        self.comp_ratio = self._slider(self.settings.compressor_ratio, 1, 6, 100, self._sync_settings)
        self.attack = self._slider(self.settings.compressor_attack_ms, 1, 100, 99, self._sync_settings)
        self.release = self._slider(self.settings.compressor_release_ms, 40, 500, 92, self._sync_settings)
        self.saturation = self._slider(self.settings.saturation_drive_db, 0, 6, 120, self._sync_settings)
        self.width = self._slider(self.settings.stereo_width, 0.5, 1.5, 100, self._sync_settings)

        self.normalize_switch = ft.Switch(value=self.settings.normalize_loudness, active_color=c.PURPLE, on_change=self._sync_settings)
        self.target_lufs = self._slider(self.settings.target_lufs, -18, -8, 100, self._sync_settings)
        self.true_peak = self._slider(self.settings.true_peak_ceiling_dbtp, -3, -0.3, 54, self._sync_settings)
        self.preview_start = ft.TextField(value=str(self.settings.preview_start_s), width=95, dense=True, suffix_text="s")
        self.preview_duration = ft.TextField(value=str(self.settings.preview_duration_s), width=95, dense=True, suffix_text="s")
        self.reference_strength = self._slider(self.settings.reference_match_strength, 0, 1, 100, self._sync_settings)

    def _sync_settings(self, _=None):
        self.settings.input_gain_db = float(self.input_gain.value)
        self.settings.denoise_enabled = bool(self.denoise_switch.value)
        self.settings.denoise_amount = float(self.denoise.value)
        self.settings.highpass_hz = float(self.highpass.value)
        self.settings.low_shelf_db = float(self.low.value)
        self.settings.low_mid_db = float(self.lowmid.value)
        self.settings.mid_db = float(self.mid.value)
        self.settings.presence_db = float(self.presence.value)
        self.settings.air_shelf_db = float(self.air.value)
        self.settings.compressor_threshold_db = float(self.comp_threshold.value)
        self.settings.compressor_ratio = float(self.comp_ratio.value)
        self.settings.compressor_attack_ms = float(self.attack.value)
        self.settings.compressor_release_ms = float(self.release.value)
        self.settings.saturation_drive_db = float(self.saturation.value)
        self.settings.stereo_width = float(self.width.value)
        self.settings.normalize_loudness = bool(self.normalize_switch.value)
        self.settings.target_lufs = float(self.target_lufs.value)
        self.settings.true_peak_ceiling_dbtp = float(self.true_peak.value)
        self.settings.reference_match_strength = float(self.reference_strength.value)
        try:
            self.settings.preview_start_s = max(0.0, float(self.preview_start.value or 0))
            self.settings.preview_duration_s = min(60.0, max(3.0, float(self.preview_duration.value or 20)))
        except ValueError:
            pass

    def _apply_settings_to_ui(self):
        s = self.settings
        self.input_gain.value = s.input_gain_db
        self.denoise_switch.value = s.denoise_enabled
        self.denoise.value = s.denoise_amount
        self.highpass.value = s.highpass_hz
        self.low.value = s.low_shelf_db
        self.lowmid.value = s.low_mid_db
        self.mid.value = s.mid_db
        self.presence.value = s.presence_db
        self.air.value = s.air_shelf_db
        self.comp_threshold.value = s.compressor_threshold_db
        self.comp_ratio.value = s.compressor_ratio
        self.attack.value = s.compressor_attack_ms
        self.release.value = s.compressor_release_ms
        self.saturation.value = s.saturation_drive_db
        self.width.value = s.stereo_width
        self.normalize_switch.value = s.normalize_loudness
        self.target_lufs.value = s.target_lufs
        self.true_peak.value = s.true_peak_ceiling_dbtp
        self.reference_strength.value = s.reference_match_strength
        self.page.update()

    def _set_busy(self, message: str, busy: bool = True):
        self.status.value = message
        self.status.color = c.PURPLE_SOFT if busy else c.MUTED
        self.progress.visible = busy
        self.progress.value = None if busy else 0
        self.page.update()

    def _show_metrics(self, m: AudioMetrics):
        self.metrics_row.controls = [
            metric_chip("LUFS-I", f"{m.integrated_lufs:.1f}", -16.5 <= m.integrated_lufs <= -8.5),
            metric_chip("True Peak", f"{m.true_peak_dbtp:.2f} dBTP", m.true_peak_dbtp <= -0.8),
            metric_chip("Sample Peak", f"{m.sample_peak_dbfs:.2f} dBFS", m.sample_peak_dbfs < -0.05),
            metric_chip("Crest", f"{m.crest_factor_db:.1f} dB", m.crest_factor_db >= 6),
            metric_chip("Clipping", f"{m.clipping_percent:.3f}%", m.clipping_percent < 0.01),
            metric_chip("Formato", f"{m.sample_rate/1000:.1f} kHz / {m.channels} ch"),
        ]
        self.page.update()

    async def choose_source(self, _):
        files = await self.file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[x.lstrip(".") for x in SUPPORTED_IMPORT],
        )
        if not files or not files[0].path:
            return
        self.source_path = files[0].path
        self.source_label.value = files[0].name
        self._set_busy("Analizando pista…")
        try:
            self.source_metrics = await asyncio.to_thread(self.engine.analyze, self.source_path)
            self._show_metrics(self.source_metrics)
            self.status.value = "Pista analizada. Ajusta la cadena o genera un preview."
        except Exception as exc:
            self.status.value = f"Error al analizar: {exc}"
            self.status.color = c.RED
        finally:
            self.progress.visible = False
            self.page.update()

    async def choose_reference(self, _):
        files = await self.reference_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[x.lstrip(".") for x in SUPPORTED_IMPORT],
        )
        if not files or not files[0].path:
            return
        self.reference_path = files[0].path
        self.reference_label.value = files[0].name
        self._set_busy("Analizando referencia…")
        try:
            self.reference_metrics = await asyncio.to_thread(self.engine.analyze, self.reference_path)
            self.status.value = f"Referencia lista: {self.reference_metrics.integrated_lufs:.1f} LUFS-I."
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
        self.page.update()

    def match_reference(self, _):
        self._sync_settings()
        if not self.source_metrics or not self.reference_metrics:
            self.status.value = "Carga primero la pista y la referencia."
            self.status.color = c.AMBER
            self.page.update()
            return
        suggestion = suggest_from_reference(
            self.source_metrics,
            self.reference_metrics,
            strength=self.settings.reference_match_strength,
        )
        self.settings.target_lufs = suggestion.target_lufs
        self.settings.low_shelf_db = suggestion.eq_db["low"]
        self.settings.low_mid_db = suggestion.eq_db["low_mid"]
        self.settings.mid_db = suggestion.eq_db["mid"]
        self.settings.presence_db = suggestion.eq_db["presence"]
        self.settings.air_shelf_db = suggestion.eq_db["air"]
        self._apply_settings_to_ui()
        self.status.value = f"Referencia aplicada con límites seguros. Objetivo: {suggestion.target_lufs:.1f} LUFS."
        self.status.color = c.PURPLE_SOFT
        self.page.update()

    async def make_preview(self, _):
        if not self.source_path:
            self.status.value = "Primero carga una pista."
            self.status.color = c.AMBER
            self.page.update()
            return
        self._sync_settings()
        self._set_busy("Renderizando preview A/B…")
        try:
            original, mastered, metrics = await asyncio.to_thread(
                self.engine.preview, self.source_path, self.settings.copy()
            )
            self.preview_original, self.preview_mastered = original, mastered
            self.preview_metrics.value = (
                f"Preview → {metrics.integrated_lufs:.1f} LUFS-I · "
                f"{metrics.true_peak_dbtp:.2f} dBTP · crest {metrics.crest_factor_db:.1f} dB"
            )
            self.status.value = "Preview listo. Compara Original / Master."
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
            self.page.update()
            return
        # Decode a short reference snippet through the same preview helper without processing.
        from doomforge.audio.io import read_audio, write_preview_wav
        try:
            self._sync_settings()
            audio, sr = await asyncio.to_thread(
                read_audio,
                self.reference_path,
                start_s=self.settings.preview_start_s,
                duration_s=self.settings.preview_duration_s,
            )
            p = Path(tempfile.mkdtemp(prefix="doomforge_ref_")) / "reference.wav"
            await asyncio.to_thread(write_preview_wav, p, audio, sr)
            await self._play_path(p)
        except Exception as exc:
            self.status.value = f"No se pudo reproducir la referencia: {exc}"
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
        default_name = f"{Path(self.source_path).stem}_MASTER{ext}"
        output = await self.file_picker.save_file(
            dialog_title="Guardar master",
            file_name=default_name,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[ext.lstrip(".")],
        )
        if not output:
            return
        output_path = str(Path(output).with_suffix(ext))
        self._set_busy("Renderizando master completo…")
        try:
            report = await asyncio.to_thread(
                self.engine.render, self.source_path, output_path, self.settings.copy()
            )
            self.status.value = (
                f"Master listo: {Path(report.output_path).name} · "
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

    def _source_panel(self):
        return panel(
            ft.Column(
                controls=[
                    section_title("01 · Fuente", "Importa la grabación y, opcionalmente, una referencia."),
                    ft.Row(
                        controls=[
                            ft.Button("Cargar pista", icon=ft.Icons.AUDIO_FILE, on_click=self.choose_source),
                            self.source_label,
                        ],
                    ),
                    ft.Row(
                        controls=[
                            ft.Button("Cargar referencia", icon=ft.Icons.LIBRARY_MUSIC, on_click=self.choose_reference),
                            self.reference_label,
                        ],
                    ),
                    self.metrics_row,
                ],
                spacing=12,
            )
        )

    def _recovery_panel(self):
        return panel(
            ft.Column(
                controls=[
                    section_title("02 · Recovery", "Limpieza conservadora antes del mastering."),
                    parameter_row(
                        "Input gain",
                        self.input_gain,
                        "Ajusta nivel antes de procesar. Evita empujar una grabación ya saturada; normalmente 0 dB es correcto.",
                    ),
                    ft.Row([ft.Text("Denoise espectral", expand=True), self.denoise_switch]),
                    parameter_row(
                        "Cantidad de denoise",
                        self.denoise,
                        "Reduce ruido constante/ambiente. Más no siempre es mejor: por encima de ~0.35 puede volver metálicos platos y reverberación.",
                    ),
                    parameter_row(
                        "High-pass",
                        self.highpass,
                        "Quita subgrave, viento y golpes de manejo. Para doom/stoner evita subir demasiado: 25–35 Hz suele preservar el peso.",
                    ),
                ],
                spacing=8,
            )
        )

    def _eq_panel(self):
        return panel(
            ft.Column(
                controls=[
                    section_title("03 · EQ tonal", "Cinco zonas musicales, cambios pequeños."),
                    parameter_row("Low shelf · 110 Hz", self.low, "Peso de bombo/bajo. Boost excesivo roba headroom y fuerza al limiter."),
                    parameter_row("Low-mid · 300 Hz", self.lowmid, "Cuerpo vs. caja/embarrado. En grabación de teléfono suele agradecer un recorte suave."),
                    parameter_row("Mid · 1.2 kHz", self.mid, "Presencia de guitarras y voz. Mucho boost puede volver nasal/agresivo."),
                    parameter_row("Presence · 3.8 kHz", self.presence, "Ataque, inteligibilidad y filo. Vigila platos y distorsión del micrófono."),
                    parameter_row("Air shelf · 8.5 kHz", self.air, "Aire/brillo. En fuentes con AAC o platos ásperos, incluso un pequeño corte puede sonar mejor."),
                ],
                spacing=7,
            )
        )

    def _dynamics_panel(self):
        return panel(
            ft.Column(
                controls=[
                    section_title("04 · Dinámica", "Glue, densidad y control sin aplastar."),
                    parameter_row("Threshold", self.comp_threshold, "Más negativo = el compresor trabaja más tiempo. Busca 1–4 dB de reducción, no una pared constante."),
                    parameter_row("Ratio", self.comp_ratio, "1.5–2.5:1 conserva naturalidad; ratios altos endurecen el concierto y suben el ruido ambiente."),
                    parameter_row("Attack", self.attack, "Ataque más lento deja pasar bombo/caja; muy rápido puede quitar pegada."),
                    parameter_row("Release", self.release, "Muy corto bombea; muy largo puede dejar todo hundido. 120–250 ms suele funcionar en rock pesado."),
                    parameter_row("Saturación", self.saturation, "Añade densidad armónica muy moderada. No repara clipping digital ya impreso."),
                    parameter_row("Stereo width", self.width, "1.0 = original. Más ancho aumenta ambiente y riesgo de problemas mono; usa cambios pequeños."),
                ],
                spacing=7,
            )
        )

    def _loudness_panel(self):
        return panel(
            ft.Column(
                controls=[
                    section_title("05 · Loudness & safety", "Nivel final con techo true-peak."),
                    ft.Row([ft.Text("Normalizar a LUFS", expand=True), self.normalize_switch]),
                    parameter_row("Target LUFS-I", self.target_lufs, "-14 es cómodo para streaming; -12 a -10 puede funcionar en rock/doom; por encima de -9 aumenta mucho el riesgo de aplastar dinámica."),
                    parameter_row("True-peak ceiling", self.true_peak, "Techo final inter-sample. -1.0 dBTP es una meta segura para distribución con compresión con pérdida."),
                    ft.Divider(color=c.BORDER),
                    ft.Row([ft.Text("Preview desde"), self.preview_start, ft.Text("duración"), self.preview_duration]),
                    ft.Row(
                        controls=[
                            ft.Button("Generar preview", icon=ft.Icons.AUTO_AWESOME, on_click=self.make_preview),
                            ft.Button("Original", icon=ft.Icons.PLAY_ARROW, on_click=self.play_original),
                            ft.Button("Master", icon=ft.Icons.GRAPHIC_EQ, on_click=self.play_mastered),
                            ft.Button("Ref", icon=ft.Icons.HEADPHONES, on_click=self.play_reference),
                            ft.IconButton(icon=ft.Icons.PAUSE, tooltip="Pausa", on_click=self.pause),
                        ],
                        wrap=True,
                    ),
                    self.preview_metrics,
                ],
                spacing=8,
            )
        )

    def _reference_panel(self):
        return panel(
            ft.Column(
                controls=[
                    section_title("Reference Match", "Aproxima el balance sin copiar defectos ni loudness extremo."),
                    parameter_row("Fuerza", self.reference_strength, "0 = sin influencia; 1 = máximo. Los cambios siguen limitados a ±3 dB por banda y -16…-9 LUFS."),
                    ft.Button("Aplicar sugerencia", icon=ft.Icons.TUNE, on_click=self.match_reference),
                    ft.Text(
                        "Consejo: usa una referencia parecida en género, instrumentación y tipo de mezcla. "
                        "Una producción de estudio no siempre es una buena referencia para una toma de público.",
                        size=11,
                        color=c.MUTED,
                    ),
                ],
                spacing=8,
            )
        )

    def _render_panel(self):
        return panel(
            ft.Column(
                controls=[
                    section_title("Render", "Exporta el master completo cuando el A/B te convenza."),
                    ft.Row([ft.Text("Formato"), self.export_format, ft.Container(expand=True), ft.Button("RENDER MASTER", icon=ft.Icons.DOWNLOAD, on_click=self.render_master)]),
                    ft.Text(
                        "Para archivo/edición posterior: WAV o FLAC. MP3/AAC son para distribución, no para seguir procesando.",
                        size=11,
                        color=c.MUTED,
                    ),
                ],
                spacing=9,
            )
        )

    def _render(self):
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("DOOMFORGE", size=28, weight=ft.FontWeight.BOLD, color=c.WHITE),
                            ft.Text("MASTERING STUDIO · open-source", size=11, color=c.PURPLE_SOFT),
                        ],
                        spacing=0,
                    ),
                    ft.Container(expand=True),
                    ft.Text("Preset", color=c.MUTED, size=11),
                    self.preset,
                ]
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            bgcolor=c.PANEL,
            border=ft.Border(bottom=ft.BorderSide(1, c.BORDER)),
        )

        left = ft.Column(
            controls=[self._source_panel(), self._recovery_panel(), self._reference_panel()],
            spacing=12,
            col={"sm": 12, "lg": 4},
        )
        middle = ft.Column(
            controls=[self._eq_panel(), self._dynamics_panel()],
            spacing=12,
            col={"sm": 12, "lg": 4},
        )
        right = ft.Column(
            controls=[self._loudness_panel(), self._render_panel()],
            spacing=12,
            col={"sm": 12, "lg": 4},
        )

        body = ft.Column(
            controls=[
                ft.ResponsiveRow(controls=[left, middle, right], spacing=12, run_spacing=12),
                self.progress,
                ft.Container(content=self.status, padding=ft.Padding.symmetric(horizontal=4, vertical=8)),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.page.add(header, ft.Container(content=body, padding=16, expand=True))


def main(page: ft.Page):
    DoomForgeApp(page)


def run():
    ft.run(main)
