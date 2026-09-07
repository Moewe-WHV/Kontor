"""Asynchrones Daily-Standup: gestern / heute / Blocker pro Person."""
from __future__ import annotations

from datetime import date, timedelta

from nicegui import ui

from components import avatar, frame
from store import store, today_iso

_sel = {'date': today_iso()}


@ui.refreshable
def content() -> None:
    day = _sel['date']
    with ui.row().classes('w-full items-center gap-2'):
        ui.button(icon='chevron_left',
                  on_click=lambda: (_sel.update(date=(date.fromisoformat(day) - timedelta(days=1)).isoformat()),
                                    content.refresh())).props('flat dense')
        ui.input(value=day, on_change=lambda e: (_sel.update(date=e.value), content.refresh())) \
            .props('outlined dense type=date').classes('w-44')
        ui.button(icon='chevron_right',
                  on_click=lambda: (_sel.update(date=(date.fromisoformat(day) + timedelta(days=1)).isoformat()),
                                    content.refresh())).props('flat dense')
        if day != today_iso():
            ui.button('heute', on_click=lambda: (_sel.update(date=today_iso()), content.refresh())) \
                .props('flat dense no-caps')
        ui.space()
        blockers = [s for s in store.standups if s.date == day and s.blocker.strip()]
        ui.badge(f'{len(blockers)} Blocker').props('color=negative' if blockers else 'color=grey-5')

    for m in store.active_members:
        su = store.standup_for(day, m.id)
        with ui.card().classes('w-full gap-2'):
            with ui.row().classes('items-center gap-2'):
                avatar(m, '30px')
                ui.label(m.name).classes('font-medium')
                ui.label(m.role).classes('text-xs text-grey-5')
            with ui.row().classes('w-full gap-2 no-wrap flex-wrap'):
                y = ui.textarea('Gestern', value=su.yesterday if su else '') \
                    .props('outlined dense autogrow').classes('grow min-w-[14rem]')
                t = ui.textarea('Heute', value=su.today if su else '') \
                    .props('outlined dense autogrow').classes('grow min-w-[14rem]')
                b = ui.textarea('Blocker', value=su.blocker if su else '') \
                    .props('outlined dense autogrow').classes('grow min-w-[14rem]')
            for widget, fld in ((y, 'yesterday'), (t, 'today'), (b, 'blocker')):
                widget.on('blur', lambda w=widget, f=fld, mid=m.id:
                          store.upsert_standup(day, mid, **{f: w.value or ''}))

    ui.label('Felder speichern beim Verlassen automatisch.').classes('text-xs text-grey-5')


def page() -> None:
    with frame('/standup'):
        ui.label('Daily-Standup').classes('kontor-title text-xl')
        content()
