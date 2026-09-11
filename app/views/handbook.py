"""Anleitung – wo finde ich was, wofür ist das gut, wie fange ich an."""
from __future__ import annotations

import guide
from nicegui import ui

from components import NAV_GROUPS, frame
from i18n import t

_flt = {'q': ''}


def _match(text: str, needle: str) -> bool:
    return needle in text.lower()


def _first_steps() -> None:
    with ui.card().classes('w-full gap-2 bg-teal-1 border border-teal-2'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('flag').classes('text-primary')
            ui.label('Erste Schritte – wenn das Projekt neu ist').classes('kontor-title text-md')
        for i, (title, desc, path) in enumerate(guide.FIRST_STEPS, 1):
            with ui.row().classes('w-full items-center gap-2 no-wrap'):
                ui.label(str(i)).classes(
                    'text-xs font-bold text-white bg-primary rounded-full '
                    'w-5 h-5 flex items-center justify-center shrink-0')
                with ui.column().classes('gap-0 grow'):
                    ui.label(title).classes('text-sm font-medium')
                    ui.label(desc).classes('text-xs text-grey-7')
                ui.button('Öffnen', on_click=lambda p=path: ui.navigate.to(p)) \
                    .props('flat dense no-caps size=sm')


@ui.refreshable
def results() -> None:
    q = _flt['q'].strip().lower()

    if not q:
        _first_steps()

    ui.label('Alle Bereiche').classes('kontor-title text-md mt-2')
    hits = 0
    for group, items in NAV_GROUPS:
        rows = []
        for label, icon, path in items:
            h = guide.PAGES.get(path)
            hay = f'{t(label)} {t(group)} {h["what"] if h else ""}'.lower()
            if q and not _match(hay, q):
                continue
            rows.append((label, icon, path, h))
        if not rows:
            continue
        hits += len(rows)
        with ui.card().classes('w-full gap-1'):
            ui.label(t(group)).classes('text-xs font-bold uppercase tracking-widest text-grey-6')
            for label, icon, path, h in rows:
                with ui.expansion(t(label), icon=icon).props('dense').classes('w-full text-sm'):
                    if h:
                        ui.label(h['what']).classes('text-sm text-grey-8')
                        if h.get('steps'):
                            ui.label('So gehst du vor').classes(
                                'text-xs font-bold uppercase text-grey-6 mt-1')
                            for i, s in enumerate(h['steps'], 1):
                                ui.label(f'{i}. {s}').classes('text-sm')
                        if h.get('tips'):
                            for tip in h['tips']:
                                with ui.row().classes('items-start gap-1 no-wrap mt-1'):
                                    ui.icon('lightbulb', size='15px').classes('text-accent mt-0.5')
                                    ui.label(tip).classes('text-sm text-grey-7')
                    else:
                        ui.label('Noch keine Beschreibung.').classes('text-sm text-grey-5')
                    ui.button('Bereich öffnen', icon='open_in_new',
                              on_click=lambda p=path: ui.navigate.to(p)) \
                        .props('flat dense no-caps size=sm').classes('mt-1')

    if q and not hits:
        ui.label('Nichts gefunden. Versuch es mit einem anderen Wort.').classes('text-grey-6')

    gloss = [(term, expl) for term, expl in guide.GLOSSARY
             if not q or _match(f'{term} {expl}', q)]
    if gloss:
        with ui.card().classes('w-full gap-1'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('school').classes('text-primary')
                ui.label('Begriffe kurz erklärt').classes('kontor-title text-md')
            for term, expl in gloss:
                with ui.row().classes('w-full items-baseline gap-2 no-wrap border-t border-grey-2 py-1'):
                    ui.label(term).classes('text-sm font-semibold w-44 shrink-0')
                    ui.label(expl).classes('text-sm text-grey-8')


def page() -> None:
    with frame('/handbook'):
        ui.label('Anleitung').classes('kontor-title text-xl')
        ui.label('Dein Nachschlagewerk: wo finde ich was – und wie fange ich an.') \
            .classes('text-sm text-grey-6')
        with ui.row().classes('w-full items-center gap-2'):
            ui.input(placeholder='Bereich oder Begriff suchen …', value=_flt['q'],
                     on_change=lambda e: (_flt.update(q=e.value or ''), results.refresh())) \
                .props('outlined dense clearable debounce=200').classes('grow max-w-md')
            ui.icon('search').classes('text-grey-6')
        results()
