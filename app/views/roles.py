"""Rollen & Ablauf – wer macht was, täglich und wöchentlich."""
from __future__ import annotations

import guide
from nicegui import ui

from components import avatar, frame, help_hint
from store import store


def _members_for(role: dict) -> list:
    out = []
    for m in store.active_members:
        r = (m.role or '').lower()
        if any(key in r for key in role['match']):
            out.append(m)
    return out


def _role_card(role: dict, people: list) -> None:
    with ui.card().classes('w-full gap-2'):
        with ui.row().classes('w-full items-center gap-2 no-wrap'):
            ui.icon('badge').classes('text-primary')
            ui.label(role['name']).classes('kontor-title text-lg grow')
            for m in people:
                avatar(m, '26px')
        ui.label(role['summary']).classes('text-sm text-grey-8')
        if people:
            ui.label('Im Team: ' + ', '.join(m.name for m in people)) \
                .classes('text-xs text-grey-6')
        else:
            ui.label('Aktuell niemandem zugeordnet (Rolle in der Crew setzen).') \
                .classes('text-xs text-grey-5')

        with ui.row().classes('w-full gap-4 flex-wrap items-start'):
            with ui.column().classes('grow min-w-[14rem] gap-1'):
                ui.label('Jeden Tag').classes('text-xs font-bold uppercase text-grey-6')
                for x in role['daily']:
                    with ui.row().classes('items-start gap-1 no-wrap'):
                        ui.icon('check', size='15px').classes('text-positive mt-0.5')
                        ui.label(x).classes('text-sm')
            with ui.column().classes('grow min-w-[14rem] gap-1'):
                ui.label('Jede Woche').classes('text-xs font-bold uppercase text-grey-6')
                for x in role['weekly']:
                    with ui.row().classes('items-start gap-1 no-wrap'):
                        ui.icon('event_repeat', size='15px').classes('text-primary mt-0.5')
                        ui.label(x).classes('text-sm')
            with ui.column().classes('grow min-w-[14rem] gap-1'):
                ui.label('Rote Flaggen').classes('text-xs font-bold uppercase text-grey-6')
                for x in role['flags']:
                    with ui.row().classes('items-start gap-1 no-wrap'):
                        ui.icon('flag', size='15px').classes('text-negative mt-0.5')
                        ui.label(x).classes('text-sm text-grey-7')


def _rhythm_table() -> None:
    with ui.card().classes('w-full gap-2'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('schedule').classes('text-primary')
            ui.label('Tagesrhythmus im Überblick').classes('kontor-title text-md')
        ui.label('Der grobe Ablauf über den Tag – wer wann was macht.') \
            .classes('text-xs text-grey-6')
        for slot, mapping in guide.DAY_RHYTHM:
            with ui.column().classes('w-full gap-0 p-2 rounded-lg bg-grey-1'):
                ui.label(slot).classes('text-xs font-bold uppercase tracking-widest text-primary mb-1')
                for who, task in mapping.items():
                    with ui.row().classes('w-full items-start gap-2 no-wrap py-0.5'):
                        ui.label(who).classes('text-xs font-semibold text-grey-7 w-24 shrink-0 mt-0.5')
                        ui.label(task).classes('text-sm text-grey-8 leading-snug')


def page() -> None:
    with frame('/roles'):
        ui.label('Rollen & Ablauf').classes('kontor-title text-xl')
        help_hint('Nicht jede Rolle braucht eine eigene Person. Im Klassenprojekt '
                  'übernimmt oft jemand mehrere Rollen – wichtig ist nur, dass für '
                  'jede Aufgabe klar ist, wer sie macht. Ordne Rollen in der Crew '
                  'zu, dann erscheinen hier die passenden Namen.',
                  title='Wie du diese Seite nutzt')

        for role in guide.ROLES:
            _role_card(role, _members_for(role))

        _rhythm_table()
