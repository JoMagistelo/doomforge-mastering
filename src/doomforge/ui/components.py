from __future__ import annotations

import flet as ft

from doomforge.ui import theme as c


def info_icon(text: str) -> ft.IconButton:
    """A deliberately quiet help affordance for parameter explanations."""
    return ft.IconButton(
        icon=ft.Icons.HELP_OUTLINE,
        icon_size=15,
        icon_color=c.MUTED_2,
        tooltip=text,
        width=26,
        height=26,
        visual_density=ft.VisualDensity.COMPACT,
    )


def section_title(title: str, subtitle: str = "", *, icon=None) -> ft.Column:
    head: list[ft.Control] = []
    if icon is not None:
        head.append(ft.Icon(icon, size=16, color=c.PURPLE_SOFT))
    head.append(ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=c.WHITE))
    controls: list[ft.Control] = [ft.Row(head, spacing=7)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=10.5, color=c.MUTED, max_lines=2))
    return ft.Column(controls=controls, spacing=2)


def panel(
    content: ft.Control,
    *,
    padding: int = 13,
    accent: bool = False,
    image: ft.DecorationImage | None = None,
) -> ft.Container:
    border_color = c.BORDER_STRONG if accent else c.BORDER
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=c.SURFACE,
        border=ft.Border.all(1, border_color),
        border_radius=14,
        image=image,
        shadow=[
            ft.BoxShadow(
                blur_radius=18,
                spread_radius=-8,
                color=ft.Colors.with_opacity(0.25 if accent else 0.12, c.PURPLE),
            )
        ],
    )


def parameter_row(
    label: str,
    control: ft.Control,
    tip: str,
    *,
    value_text: ft.Text | None = None,
    recommendation: str | None = None,
) -> ft.Column:
    badge = value_text or ft.Text("", size=10.5, color=c.PURPLE_SOFT)
    header_controls: list[ft.Control] = [
        ft.Text(label, size=11.5, color=c.WHITE_SOFT, expand=True),
    ]
    if recommendation:
        header_controls.append(
            ft.Container(
                content=ft.Text(recommendation, size=8.5, color=c.MUTED),
                padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                bgcolor=c.SURFACE_3,
                border_radius=20,
            )
        )
    header_controls.extend([badge, info_icon(tip)])
    return ft.Column(
        controls=[
            ft.Row(
                controls=header_controls,
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            control,
        ],
        spacing=0,
    )


def metric_chip(label: str, value: str, good: bool | None = None) -> ft.Container:
    color = c.PURPLE_SOFT if good is None else (c.GREEN if good else c.AMBER)
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(label.upper(), size=8.5, color=c.MUTED_2),
                ft.Text(value, size=13.5, weight=ft.FontWeight.W_600, color=color),
            ],
            spacing=0,
        ),
        padding=ft.Padding.symmetric(horizontal=10, vertical=7),
        bgcolor=c.SURFACE_2,
        border=ft.Border.all(1, c.BORDER),
        border_radius=10,
    )


def status_pill(text: str, *, icon=ft.Icons.BOLT, color: str = c.PURPLE_SOFT) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [ft.Icon(icon, size=12, color=color), ft.Text(text, size=9.5, color=color)],
            spacing=5,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=9, vertical=5),
        bgcolor=c.SURFACE_2,
        border=ft.Border.all(1, c.BORDER),
        border_radius=30,
    )


def action_button(
    text: str,
    *,
    icon=None,
    on_click=None,
    primary: bool = False,
    expand: bool = False,
) -> ft.Button:
    return ft.Button(
        content=text,
        icon=icon,
        on_click=on_click,
        expand=expand,
        height=38,
        color=c.WHITE if primary else c.WHITE_SOFT,
        bgcolor=c.PURPLE_DARK if primary else c.SURFACE_3,
        elevation=0,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=9),
            side=ft.BorderSide(1, c.PURPLE if primary else c.BORDER_STRONG),
            overlay_color=ft.Colors.with_opacity(0.12, c.WHITE),
            icon_size=17,
        ),
    )
