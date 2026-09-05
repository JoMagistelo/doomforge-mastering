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
        status_pill('RECOVERY', icon=ft.Icons.CLEANING_SERVICES),
        status_pill('TONE', icon=ft.Icons.EQUALIZER),
        status_pill('GLUE', icon=ft.Icons.COMPRESS),
        status_pill('LIMIT', icon=ft.Icons.SPEED),
    ], spacing=5, wrap=True)
    return ft.Container(
        height=116,
        border_radius=14,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(1, c.BORDER_STRONG),
        content=ft.Stack([
            ft.Image(src='doomforge_banner_clean.png', fit=ft.BoxFit.COVER, width=float('inf'), height=116),
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.CENTER_LEFT,
                    end=ft.Alignment.CENTER_RIGHT,
                    colors=['#E607060A', '#A80C0911', '#3517121F'],
                ),
                padding=ft.Padding.symmetric(horizontal=20, vertical=14),
                content=ft.Row([
                    ft.Image(src='doomforge_mark.svg', width=54, height=54, fit=ft.BoxFit.CONTAIN),
                    ft.Column([
                        ft.Text('DOOMFORGE', size=24, weight=ft.FontWeight.BOLD, color=c.WHITE),
                        ft.Text('FROM NOISE TO POWER', size=9, color=c.PURPLE_SOFT, weight=ft.FontWeight.W_600),
                        chain,
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text('LIVE RESCUE / MASTERING', size=10, color=c.WHITE, weight=ft.FontWeight.W_600),
                        ft.Text('Controla ruido, tono, dinámica y loudness sin destruir el carácter.', size=9.5, color=c.WHITE_SOFT, max_lines=2),
                    ], spacing=4, width=330),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        ]),
    )


def file_card(app, *, reference: bool = False) -> ft.Container:
    label = app.reference_label if reference else app.source_label
    button = action_button(
        'Cargar referencia' if reference else 'Cargar pista',
        icon=ft.Icons.LIBRARY_MUSIC if reference else ft.Icons.UPLOAD_FILE,
        on_click=app.choose_reference if reference else app.choose_source,
        primary=not reference,
        expand=True,
    )
    extra = [app.reference_summary] if reference else []
    return panel(ft.Column([
        section_title(
            'REFERENCE' if reference else 'SOURCE',
            'Referencia tonal opcional.' if reference else 'Archivo principal para analizar y masterizar.',
            icon=ft.Icons.LIBRARY_MUSIC if reference else ft.Icons.AUDIO_FILE,
        ),
        ft.Container(
            ft.Row([
                ft.Container(ft.Icon(ft.Icons.MUSIC_NOTE, size=18, color=c.PURPLE_SOFT), width=38, height=38, alignment=ft.Alignment.CENTER, bgcolor=c.SURFACE_3, border_radius=8),
                ft.Column([label, *extra], spacing=1, expand=True),
            ], spacing=8),
            padding=8,
            bgcolor=c.SURFACE_2,
            border=ft.Border.all(1, c.BORDER),
            border_radius=9,
        ),
        button,
    ], spacing=7), accent=not reference)


def recovery_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('01 · RECOVERY', 'Limpieza conservadora.', icon=ft.Icons.CLEANING_SERVICES),
        ft.Row([ft.Text('Denoise espectral', size=11, color=c.WHITE_SOFT, expand=True), app.denoise_switch]),
        *_params(app, [
            ('input_gain', 'Input gain', app.input_gain, 'Nivel antes del DSP. No empujes una fuente ya recortada.', '0 dB'),
            ('denoise', 'Denoise', app.denoise, 'Reduce ruido constante. Exceso puede volver metálicos platos y reverb.', '10–30%'),
            ('highpass', 'High-pass', app.highpass, 'Quita viento y subgrave inútil sin adelgazar el bajo.', '25–35 Hz'),
        ]),
    ], spacing=2))


def eq_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('02 · TONE', 'Cinco zonas musicales.', icon=ft.Icons.EQUALIZER),
        *_params(app, [
            ('low', 'Low · 110 Hz', app.low, 'Peso de bombo y bajo.', None),
            ('lowmid', 'Low-mid · 300 Hz', app.lowmid, 'Cuerpo frente a barro/caja.', None),
            ('mid', 'Mid · 1.2 kHz', app.mid, 'Centro de voz y guitarras.', None),
            ('presence', 'Presence · 3.8 kHz', app.presence, 'Ataque e inteligibilidad.', None),
            ('air', 'Air · 8.5 kHz', app.air, 'Brillo y aire; cuidado con fuentes ásperas.', None),
        ]),
    ], spacing=1))


def dynamics_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('03 · GLUE / DENSITY', 'Control sin aplastar.', icon=ft.Icons.COMPRESS),
        *_params(app, [
            ('threshold', 'Threshold', app.comp_threshold, 'Más negativo = más compresión.', None),
            ('ratio', 'Ratio', app.comp_ratio, '1.5–2.5:1 suele conservar naturalidad.', '1.5–2.5:1'),
            ('attack', 'Attack', app.attack, 'Más lento conserva transitorios.', None),
            ('release', 'Release', app.release, 'Muy corto bombea; muy largo hunde.', '120–250 ms'),
            ('saturation', 'Saturación', app.saturation, 'Añade densidad armónica moderada.', None),
            ('width', 'Stereo width', app.width, '1.00× conserva la imagen original.', '0.95–1.10×'),
        ]),
    ], spacing=1))


def reference_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('REFERENCE MATCH', 'Tendencia tonal con límites.', icon=ft.Icons.AUTO_FIX_HIGH),
        *_params(app, [('reference', 'Influencia', app.reference_strength, '0% ignora; 100% aplica la sugerencia máxima segura.', '55–75%')]),
        action_button('Aplicar sugerencia', icon=ft.Icons.TUNE, on_click=app.match_reference, expand=True),
    ], spacing=5))


def diagnostics_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('ANÁLISIS', 'Loudness y salud de la señal.', icon=ft.Icons.MONITOR_HEART),
        app.metrics_row,
        app.spectrum,
    ], spacing=7), accent=True)


def loudness_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('04 · LOUDNESS / SAFETY', 'Nivel final y true-peak.', icon=ft.Icons.SPEED),
        ft.Row([ft.Text('Normalizar a LUFS', size=11, color=c.WHITE_SOFT, expand=True), app.normalize_switch]),
        *_params(app, [
            ('lufs', 'Target LUFS-I', app.target_lufs, '-14 es cómodo; -12 a -10 puede funcionar en rock pesado.', '-14…-10'),
            ('true_peak', 'True-peak ceiling', app.true_peak, '-1 dBTP deja margen para codecs.', '≤ -1.0 dBTP'),
        ]),
    ], spacing=2))


def preview_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('A/B MONITOR', 'Escucha antes de imprimir.', icon=ft.Icons.HEADPHONES),
        ft.Container(ft.Image(src='doomforge_wave.svg', height=34, fit=ft.BoxFit.COVER), border_radius=8, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
        ft.Row([ft.Text('Desde', size=9.5, color=c.MUTED), app.preview_start, ft.Text('Duración', size=9.5, color=c.MUTED), app.preview_duration], spacing=5),
        action_button('Generar preview', icon=ft.Icons.AUTO_AWESOME, on_click=app.make_preview, primary=True, expand=True),
        ft.Row([
            action_button('Original', icon=ft.Icons.PLAY_ARROW, on_click=app.play_original, expand=True),
            action_button('Master', icon=ft.Icons.GRAPHIC_EQ, on_click=app.play_mastered, expand=True),
            action_button('Ref', icon=ft.Icons.LIBRARY_MUSIC, on_click=app.play_reference, expand=True),
            action_button('Pausa', icon=ft.Icons.PAUSE, on_click=app.pause, expand=True),
        ], spacing=5),
        ft.Container(app.preview_metrics, padding=7, bgcolor=c.SURFACE_2, border_radius=8),
    ], spacing=5))


def render_panel(app) -> ft.Container:
    return panel(ft.Column([
        section_title('PRINT MASTER', 'Exporta sólo cuando el A/B te convenza.', icon=ft.Icons.DOWNLOAD),
        ft.Row([ft.Text('Formato', size=10, color=c.MUTED), app.export_format, ft.Container(expand=True)]),
        action_button('RENDER MASTER', icon=ft.Icons.LOCAL_FIRE_DEPARTMENT, on_click=app.render_master, primary=True, expand=True),
        ft.Text('WAV/FLAC para archivo; MP3/AAC para entrega.', size=9, color=c.MUTED),
    ], spacing=6), accent=True)


def header(app) -> ft.Container:
    return ft.Container(
        height=54,
        padding=ft.Padding.symmetric(horizontal=16, vertical=6),
        bgcolor=c.BLACK_2,
        border=ft.Border(bottom=ft.BorderSide(1, c.BORDER)),
        content=ft.Row([
            ft.Image(src='doomforge_mark.svg', width=32, height=32),
            ft.Column([
                ft.Text('DOOMFORGE', size=15, weight=ft.FontWeight.BOLD, color=c.WHITE),
                ft.Text('MASTERING STUDIO · OPEN SOURCE', size=7.5, color=c.PURPLE_SOFT),
            ], spacing=0),
            ft.Container(expand=True),
            ft.Text('PRESET', size=8, color=c.MUTED_2),
            app.preset,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


def build_shell(app) -> None:
    top_files = ft.Row([
        ft.Container(content=file_card(app, reference=False), expand=1),
        ft.Container(content=file_card(app, reference=True), expand=1),
    ], spacing=10)

    processing = ft.Column([
        ft.ResponsiveRow([
            ft.Container(content=recovery_panel(app), col={'sm': 12, 'md': 6, 'xl': 4}),
            ft.Container(content=eq_panel(app), col={'sm': 12, 'md': 6, 'xl': 4}),
            ft.Container(content=dynamics_panel(app), col={'sm': 12, 'md': 12, 'xl': 4}),
        ], spacing=10, run_spacing=10),
        ft.ResponsiveRow([
            ft.Container(content=reference_panel(app), col={'sm': 12, 'md': 6}),
            ft.Container(content=loudness_panel(app), col={'sm': 12, 'md': 6}),
        ], spacing=10, run_spacing=10),
    ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    monitor = ft.Container(
        width=360,
        content=ft.Column([diagnostics_panel(app), preview_panel(app), render_panel(app)], spacing=10, scroll=ft.ScrollMode.AUTO),
    )

    workspace = ft.Row([
        processing,
        ft.Container(width=1, bgcolor=c.BORDER),
        monitor,
    ], spacing=10, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

    footer = ft.Container(
        height=46,
        padding=ft.Padding.symmetric(horizontal=16, vertical=6),
        bgcolor=c.BLACK_2,
        border=ft.Border(top=ft.BorderSide(1, c.BORDER)),
        content=ft.Column([app.progress, app.status], spacing=3),
    )
    body = ft.Column([
        ft.Container(content=hero(app), padding=ft.Padding.only(left=12, top=9, right=12, bottom=8)),
        ft.Container(content=top_files, padding=ft.Padding.only(left=12, right=12, bottom=8)),
        ft.Container(content=workspace, padding=ft.Padding.only(left=12, right=12, bottom=8), expand=True),
    ], spacing=0, expand=True)
    app.page.add(header(app), body, footer)
