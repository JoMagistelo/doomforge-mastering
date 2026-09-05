from __future__ import annotations

import flet as ft

from doomforge.ui import theme as c
from doomforge.ui.components import action_button, panel, parameter_row, section_title, status_pill


def _params(app, specs: list[tuple]) -> list[ft.Control]:
    return [
        parameter_row(label, control, tip, value_text=app.value_texts[key], recommendation=rec)
        for key, label, control, tip, rec in specs
    ]


def hero(app) -> ft.Container:
    chain = ft.Row([
        status_pill("RECOVERY", icon=ft.Icons.CLEANING_SERVICES), ft.Icon(ft.Icons.CHEVRON_RIGHT, size=13, color=c.MUTED_2),
        status_pill("TONE", icon=ft.Icons.EQUALIZER), ft.Icon(ft.Icons.CHEVRON_RIGHT, size=13, color=c.MUTED_2),
        status_pill("GLUE", icon=ft.Icons.COMPRESS), ft.Icon(ft.Icons.CHEVRON_RIGHT, size=13, color=c.MUTED_2),
        status_pill("LIMIT", icon=ft.Icons.SPEED),
    ], spacing=4, wrap=True)
    return ft.Container(
        height=132,
        padding=ft.Padding.symmetric(horizontal=20, vertical=15),
        border_radius=16,
        border=ft.Border.all(1, c.BORDER_STRONG),
        image=ft.DecorationImage(src="doomforge_hero.svg", fit=ft.BoxFit.COVER, alignment=ft.Alignment.CENTER, opacity=0.86),
        content=ft.Row([
            ft.Column([
                ft.Text("LIVE RESCUE / MASTERING", size=10, color=c.PURPLE_SOFT, weight=ft.FontWeight.W_600),
                ft.Text("Turn field recordings into controlled, release-ready masters.", size=19, color=c.WHITE, weight=ft.FontWeight.BOLD, max_lines=1),
                ft.Text("Conserva el peso, controla picos y compara antes de imprimir.", size=10.5, color=c.WHITE_SOFT),
                chain,
            ], spacing=4, expand=True),
            ft.Image(src="doomforge_mark.svg", width=68, height=68, fit=ft.BoxFit.CONTAIN),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


def source_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title("SOURCE", "Pista principal y referencia de carácter.", icon=ft.Icons.AUDIO_FILE),
        action_button("Cargar pista", icon=ft.Icons.UPLOAD_FILE, on_click=app.choose_source, primary=True, expand=True),
        ft.Container(ft.Row([ft.Icon(ft.Icons.MUSIC_NOTE, size=14, color=c.PURPLE_SOFT), app.source_label], spacing=6), padding=8, bgcolor=c.SURFACE_2, border_radius=8),
        ft.Divider(height=8, color=c.BORDER),
        action_button("Cargar referencia", icon=ft.Icons.LIBRARY_MUSIC, on_click=app.choose_reference, expand=True),
        ft.Container(ft.Column([app.reference_label, app.reference_summary], spacing=2), padding=8, bgcolor=c.SURFACE_2, border_radius=8),
    ], spacing=7), accent=True)


def reference_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title("REFERENCE MATCH", "Tendencia, no defectos ni loudness extremo.", icon=ft.Icons.AUTO_FIX_HIGH),
        *_params(app, [("reference", "Influencia", app.reference_strength, "0% ignora la referencia. 100% aplica la sugerencia máxima dentro de límites seguros.", "55–75%")]),
        action_button("Aplicar sugerencia", icon=ft.Icons.TUNE, on_click=app.match_reference, expand=True),
        ft.Text("Usa una referencia cercana en género, instrumentación y densidad.", size=9.2, color=c.MUTED),
    ], spacing=6))


def recovery_panel(app) -> ft.Container:
    specs = [
        ("input_gain", "Input gain", app.input_gain, "Nivel antes del DSP. No empujes una fuente ya recortada.", "0 dB"),
        ("denoise", "Denoise", app.denoise, "Reduce ruido constante. Exceso vuelve metálicos platos, fuzz y reverb.", "10–30%"),
        ("highpass", "High-pass", app.highpass, "Quita viento y subgrave inútil; conserva el peso real.", "25–35 Hz"),
    ]
    return panel(ft.Column([
        section_title("01 · RECOVERY", "Limpieza conservadora antes de alterar el carácter.", icon=ft.Icons.CLEANING_SERVICES),
        ft.Row([ft.Text("Denoise espectral", size=11.5, color=c.WHITE_SOFT, expand=True), app.denoise_switch]),
        *_params(app, specs),
    ], spacing=3))


def eq_panel(app) -> ft.Container:
    specs = [
        ("low", "Low · 110 Hz", app.low, "Peso de bombo/bajo. Boost grande roba headroom.", None),
        ("lowmid", "Low-mid · 300 Hz", app.lowmid, "Cuerpo contra barro/caja; suele admitir un recorte leve.", None),
        ("mid", "Mid · 1.2 kHz", app.mid, "Presencia de guitarras y voz; demasiado boost suena nasal.", None),
        ("presence", "Presence · 3.8 kHz", app.presence, "Ataque e inteligibilidad; vigila platos y distorsión.", None),
        ("air", "Air · 8.5 kHz", app.air, "Aire y brillo. En fuentes ásperas, un pequeño corte puede ganar.", None),
    ]
    return panel(ft.Column([
        section_title("02 · TONE SHAPER", "Cinco zonas musicales; movimientos pequeños suelen ganar.", icon=ft.Icons.EQUALIZER),
        *_params(app, specs),
    ], spacing=2))


def dynamics_panel(app) -> ft.Container:
    specs = [
        ("threshold", "Threshold", app.comp_threshold, "Más negativo = más tiempo comprimiendo.", None),
        ("ratio", "Ratio", app.comp_ratio, "1.5–2.5:1 conserva naturalidad; ratios altos endurecen ambiente.", "1.5–2.5:1"),
        ("attack", "Attack", app.attack, "Más lento deja respirar bombo/caja; demasiado rápido mata pegada.", None),
        ("release", "Release", app.release, "Muy corto bombea; muy largo hunde la mezcla.", "120–250 ms"),
        ("saturation", "Saturación", app.saturation, "Densidad armónica moderada; no repara clipping impreso.", None),
        ("width", "Stereo width", app.width, "1.00× conserva imagen; más ancho aumenta riesgo mono.", "0.95–1.10×"),
    ]
    return panel(ft.Column([
        section_title("03 · GLUE / DENSITY", "Control de macro-dinámica sin aplastar el concierto.", icon=ft.Icons.COMPRESS),
        *_params(app, specs),
    ], spacing=2))


def diagnostics_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title("DIAGNOSTICS", "Salud de la fuente antes de masterizar.", icon=ft.Icons.MONITOR_HEART),
        app.metrics_row,
        app.spectrum,
        ft.Text("Clipping de origen no puede recuperarse perfectamente; DoomForge evita añadir más daño.", size=9, color=c.MUTED),
    ], spacing=8))


def loudness_panel(app) -> ft.Container:
    specs = [
        ("lufs", "Target LUFS-I", app.target_lufs, "-14 es cómodo; -12 a -10 puede servir en rock/doom si la mezcla aguanta.", "-14…-10"),
        ("true_peak", "True-peak ceiling", app.true_peak, "Techo inter-sample; -1 dBTP deja margen para codecs.", "≤ -1.0 dBTP"),
    ]
    return panel(ft.Column([
        section_title("04 · LOUDNESS / SAFETY", "Nivel final con techo true-peak.", icon=ft.Icons.SPEED),
        ft.Row([ft.Text("Normalizar a LUFS", size=11.5, color=c.WHITE_SOFT, expand=True), app.normalize_switch]),
        *_params(app, specs),
    ], spacing=3), accent=True)


def preview_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title("A/B MONITOR", "Escucha antes de imprimir.", icon=ft.Icons.HEADPHONES),
        ft.Container(ft.Image(src="doomforge_wave.svg", height=40, fit=ft.BoxFit.COVER, border_radius=8), border_radius=8, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
        ft.Row([ft.Text("Desde", size=10, color=c.MUTED), app.preview_start, ft.Text("duración", size=10, color=c.MUTED), app.preview_duration], spacing=6),
        action_button("Generar preview", icon=ft.Icons.AUTO_AWESOME, on_click=app.make_preview, primary=True, expand=True),
        ft.Row([
            action_button("Original", icon=ft.Icons.PLAY_ARROW, on_click=app.play_original, expand=True),
            action_button("Master", icon=ft.Icons.GRAPHIC_EQ, on_click=app.play_mastered, expand=True),
        ], spacing=6),
        ft.Row([
            action_button("Ref", icon=ft.Icons.LIBRARY_MUSIC, on_click=app.play_reference, expand=True),
            action_button("Pausa", icon=ft.Icons.PAUSE, on_click=app.pause, expand=True),
        ], spacing=6),
        ft.Container(app.preview_metrics, padding=8, bgcolor=c.SURFACE_2, border=ft.Border.all(1, c.BORDER), border_radius=8),
    ], spacing=6))


def render_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title("PRINT MASTER", "Exporta cuando el A/B ya te convenza.", icon=ft.Icons.DOWNLOAD),
        ft.Row([ft.Text("Formato", size=10.5, color=c.MUTED), app.export_format, ft.Container(expand=True)]),
        action_button("RENDER MASTER", icon=ft.Icons.LOCAL_FIRE_DEPARTMENT, on_click=app.render_master, primary=True, expand=True),
        ft.Text("WAV/FLAC para archivo; MP3/AAC sólo como entrega final.", size=9.2, color=c.MUTED),
    ], spacing=7), accent=True)


def header(app) -> ft.Container:
    return ft.Container(
        height=62,
        padding=ft.Padding.symmetric(horizontal=18, vertical=8),
        bgcolor=c.BLACK_2,
        border=ft.Border(bottom=ft.BorderSide(1, c.BORDER)),
        content=ft.Row([
            ft.Image(src="doomforge_mark.svg", width=36, height=36, fit=ft.BoxFit.CONTAIN),
            ft.Column([
                ft.Text("DOOMFORGE", size=17, weight=ft.FontWeight.BOLD, color=c.WHITE),
                ft.Text("MASTERING STUDIO · OPEN SOURCE", size=8.5, color=c.PURPLE_SOFT),
            ], spacing=0),
            ft.Container(width=1, height=30, bgcolor=c.BORDER),
            ft.Text("FIELD AUDIO → CONTROLLED MASTER", size=9, color=c.MUTED_2),
            ft.Container(expand=True),
            ft.Text("PRESET", size=8.5, color=c.MUTED_2),
            app.preset,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


def build_shell(app) -> None:
    left = ft.Container(width=276, content=ft.Column([source_panel(app), reference_panel(app)], spacing=10, scroll=ft.ScrollMode.AUTO))
    center = ft.Column([recovery_panel(app), eq_panel(app), dynamics_panel(app)], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    right = ft.Container(width=326, content=ft.Column([
        diagnostics_panel(app), loudness_panel(app), preview_panel(app), render_panel(app)
    ], spacing=10, scroll=ft.ScrollMode.AUTO))
    workspace = ft.Row([
        left, ft.Container(width=1, bgcolor=c.BORDER), center,
        ft.Container(width=1, bgcolor=c.BORDER), right,
    ], spacing=10, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
    footer = ft.Container(
        padding=ft.Padding.symmetric(horizontal=16, vertical=7),
        bgcolor=c.BLACK_2,
        border=ft.Border(top=ft.BorderSide(1, c.BORDER)),
        content=ft.Column([app.progress, app.status], spacing=4),
    )
    body = ft.Column([
        ft.Container(content=hero(app), padding=ft.Padding.only(left=14, top=11, right=14, bottom=9)),
        ft.Container(content=workspace, padding=ft.Padding.only(left=14, right=14, bottom=9), expand=True),
    ], spacing=0, expand=True)
    app.page.add(header(app), body, footer)
