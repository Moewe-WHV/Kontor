"""Seekarte – Monatskalender mit Sprints, Abwesenheiten und Releases."""
from __future__ import annotations

import calendar as _cal
from datetime import date, timedelta

from nicegui import ui

from components import frame
from store import ABSENCE_KINDS, store

_sel: dict = {'ym': None}
WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
MONTHS = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']
KIND_BG = {'urlaub': '#1f4e5f', 'krank': '#a63a3a', 'fortbildung': '#b5533a', 'sonstiges': '#8ba1a8'}


def _current_ym() -> tuple[int, int]:
    if _sel['ym']:
        y, m = _sel['ym']
        return y, m
    t = date.today()
    return t.year, t.month


def _shift(delta: int) -> None:
    y, m = _current_ym()
    m += delta
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    _sel['ym'] = (y, m)
    content.refresh()


@ui.refreshable
def content() -> None:
    y, m = _current_ym()
    first = date(y, m, 1)
    last = date(y, m, _cal.monthrange(y, m)[1])
    grid_start = first - timedelta(days=first.weekday())
    grid_end = last + timedelta(days=6 - last.weekday())

    with ui.row().classes('w-full items-center gap-2'):
        ui.button(icon='chevron_left', on_click=lambda: _shift(-1)).props('flat dense')
        ui.label(f'{MONTHS[m]} {y}').classes('kontor-title text-lg w-48 text-center')
        ui.button(icon='chevron_right', on_click=lambda: _shift(1)).props('flat dense')
        ui.button('heute', on_click=lambda: (_sel.update(ym=None), content.refresh())).props('flat dense no-caps')

    # Events pro Tag sammeln
    events: dict[date, list[tuple[str, str]]] = {}

    def add(day: date, text: str, color: str) -> None:
        events.setdefault(day, []).append((text, color))

    for a in store.absences:
        s, e = a.start, a.end
        if not s or not e:
            continue
        d = date.fromisoformat(s)
        end = date.fromisoformat(e)
        mem = store.member(a.member_id)
        while d <= end:
            if grid_start <= d <= grid_end:
                add(d, f'{mem.initials if mem else "?"} {ABSENCE_KINDS.get(a.kind, a.kind)}',
                    KIND_BG.get(a.kind, '#8ba1a8'))
            d += timedelta(days=1)

    for sp in store.p_sprints():
        if sp.start_date and grid_start <= sp.start_date <= grid_end:
            add(sp.start_date, f'▶ {sp.name}', '#3d7a5d')
        if sp.end_date and grid_start <= sp.end_date <= grid_end:
            add(sp.end_date, f'⚑ {sp.name} Ende', '#cf8a2e')
    for rel in store.p_releases():
        if rel.date and grid_start <= date.fromisoformat(rel.date) <= grid_end:
            add(date.fromisoformat(rel.date), f'🚀 {rel.version}', '#b5533a')
    for ms in store.p_milestones():
        if ms.due and grid_start <= date.fromisoformat(ms.due) <= grid_end:
            add(date.fromisoformat(ms.due), f'🏁 {ms.title}', '#7a5c99')
    for mt in store.p_meetings():
        if mt.date and grid_start <= date.fromisoformat(mt.date) <= grid_end:
            add(date.fromisoformat(mt.date), f'📅 {mt.title}', '#3d7a5d')
    for v in store.p_vendors():
        if v.active and v.renewal and grid_start <= date.fromisoformat(v.renewal) <= grid_end:
            add(date.fromisoformat(v.renewal), f'⟳ {v.name}', '#cf8a2e')

    with ui.grid(columns=7).classes('w-full gap-1'):
        for wd in WEEKDAYS:
            ui.label(wd).classes('text-xs font-bold text-grey-6 text-center')
        d = grid_start
        while d <= grid_end:
            in_month = d.month == m
            is_today = d == date.today()
            cell = ui.column().classes(
                'gap-0 p-1 rounded min-h-[5.5rem] border ' +
                ('border-primary bg-blue-1' if is_today else 'border-grey-2') +
                ('' if in_month else ' opacity-40'))
            with cell:
                ui.label(str(d.day)).classes('text-xs ' + ('font-bold' if is_today else 'text-grey-7'))
                for text, color in events.get(d, [])[:4]:
                    ui.label(text).classes('text-[10px] leading-tight rounded px-1 mt-[1px] truncate w-full') \
                        .style(f'background:{color}22;color:{color}')
            d += timedelta(days=1)

    with ui.row().classes('gap-3 text-xs text-grey-6 flex-wrap'):
        for kind, lbl in ABSENCE_KINDS.items():
            ui.label(lbl).style(f'color:{KIND_BG[kind]}')
        ui.label('▶ Sprint-Start · ⚑ Sprint-Ende · 🚀 Release · 🏁 Meilenstein · 📅 Besprechung · ⟳ Vertrag')


def page() -> None:
    with frame('/calendar'):
        ui.label('Seekarte – Kalender').classes('kontor-title text-xl')
        content()
