from __future__ import annotations

import flet as ft

from doomforge.ui import theme as c


def info_icon(text: str) -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.INFO_OUTLINE,
        icon_size=16,
        icon_color=c.MUTED,
        tooltip=text,
        width=28,
        height=28,
    )


def section_title(title: str, subtitle: str = "") -> ft.Column:
    controls = [ft.Text(title, size=18, weight=ft.FontWeight.W_600, color=c.WHITE)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=12, color=c.MUTED))
    return ft.Column(controls=controls, spacing=2)


def parameter_row(
    label: str,
    control: ft.Control,
    tip: str,
    *,
    value_text: ft.Text | None = None,
) -> ft.Column:
    head = ft.Row(
        controls=[
            ft.Text(label, size=12, color=c.WHITE, expand=True),
            value_text or ft.Container(),
            info_icon(tip),
        ],
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Column(controls=[head, control], spacing=3)


def metric_chip(label: str, value: str, good: bool | None = None) -> ft.Container:
    color = c.PURPLE_SOFT if good is None else (c.GREEN if good else c.AMBER)
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(label, size=10, color=c.MUTED),
                ft.Text(value, size=15, weight=ft.FontWeight.W_600, color=color),
            ],
            spacing=1,
        ),
        padding=10,
        bgcolor=c.PANEL_2,
        border=ft.Border.all(1, c.BORDER),
        border_radius=10,
    )


def panel(content: ft.Control, *, padding: int = 16) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=c.PANEL,
        border=ft.Border.all(1, c.BORDER),
        border_radius=14,
    )
